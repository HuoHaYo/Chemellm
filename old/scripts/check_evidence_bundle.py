"""Offline verification of source bytes, full-text snapshots and literal quotes."""
import argparse
import hashlib
import json
from pathlib import Path
import sys

sys.path.insert(0,str(Path(__file__).resolve().parent))
from app.evidence import quote_match


def check_lineage(snapshot_id, snapshots, visited=None):
    """Validate recorded edits against immutable ancestors; not their accuracy."""
    visited=set() if visited is None else visited
    if snapshot_id in visited or len(visited)>100:
        return False
    visited.add(snapshot_id)
    row=snapshots[snapshot_id]
    if hashlib.sha256(row["content"].encode()).hexdigest()!=row["content_sha256"]:
        return False
    content=json.loads(row["content"])
    parent_id=content.get("derived_from")
    if not parent_id:
        return not content.get("transcription_corrections")
    parent=snapshots[parent_id]
    if parent["artifact_id"]!=row["artifact_id"] or parent["source_sha256"]!=row["source_sha256"]:
        return False
    original=json.loads(parent["content"])
    before={b["id"]:b for b in original["blocks"]}
    after={b["id"]:b for b in content["blocks"]}
    changes=[c for c in content["transcription_corrections"] if c["previous_snapshot_id"]==parent_id]
    if set(before)!=set(after) or not changes or len({c["block_id"] for c in changes})!=len(changes):
        return False
    expected=json.loads(json.dumps(before))
    for change in changes:
        block=expected[change["block_id"]]
        if not block.get("ocr") or block["text"]!=change["previous_text"]:
            return False
        if not change.get("reviewer") or not change.get("notes"):
            return False
        block["text"]=change["text"]
        block.setdefault("transcription_history",[]).append(change)
    if expected!=after:
        return False
    if content["transcription_corrections"]!=original.get("transcription_corrections",[])+changes:
        return False
    excluded={"blocks","derived_from","transcription_corrections","warnings"}
    if {k:v for k,v in content.items() if k not in excluded}!={k:v for k,v in original.items() if k not in excluded}:
        return False
    return check_lineage(parent_id,snapshots,visited)


def check_bundle(manifest_path):
    manifest_path=Path(manifest_path).resolve()
    manifest=json.loads(manifest_path.read_text(encoding="utf-8"))
    snapshots={s["id"]:s for s in manifest.get("document_snapshots",[])}
    artifacts={a["id"]:a for a in manifest["artifacts"]}
    results=[]
    for claim in manifest.get("research_evidence",{}).get("claims",[]):
        for evidence in claim["evidence"]:
            try:
                snapshot=snapshots[evidence["snapshot_id"]]
                artifact=artifacts[snapshot["artifact_id"]]
                source=(manifest_path.parent/"files"/artifact["id"]/artifact["name"]).resolve()
                if not source.is_relative_to(manifest_path.parent/"files"):
                    raise ValueError("invalid source path")
                digest=hashlib.sha256(source.read_bytes()).hexdigest()
                content=json.loads(snapshot["content"])
                block=next(b for b in content["blocks"] if b["id"]==evidence["block_id"])
                checks={"source_bytes":digest==snapshot["source_sha256"]==evidence["data"]["source_sha256"]==artifact["metadata"]["sha256"],
                        "snapshot":hashlib.sha256(snapshot["content"].encode()).hexdigest()==snapshot["content_sha256"]==evidence["data"]["content_sha256"],
                        "quote":quote_match(block["text"],evidence["data"]["quote"])["matched"],
                        "transcription_lineage":check_lineage(snapshot["id"],snapshots)}
                results.append({"claim_id":claim["id"],"evidence_id":evidence["id"],"checks":checks,"passed":all(checks.values()),
                                "transcription_corrected":bool(block.get("transcription_history"))})
            except (KeyError,ValueError,TypeError,StopIteration,OSError) as exc:
                results.append({"claim_id":claim["id"],"evidence_id":evidence["id"],"passed":False,"error":type(exc).__name__})
    return {"results":results,"passed":all(r["passed"] for r in results),"applicable":bool(results),
            "scope":"source bytes, snapshot integrity, literal quote occurrence and recorded transcription lineage only; transcription accuracy and scientific support are not adjudicated"}


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--manifest",type=Path,default=Path(__file__).resolve().parent.parent/"manifest.json")
    args=parser.parse_args()
    output=check_bundle(args.manifest)
    Path("evidence-integrity.json").write_text(json.dumps(output,ensure_ascii=False,indent=2),encoding="utf-8")
    print(json.dumps(output,ensure_ascii=False))
    return 0 if output["passed"] else 1


if __name__=="__main__":raise SystemExit(main())
