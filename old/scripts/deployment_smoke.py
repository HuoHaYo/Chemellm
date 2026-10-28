"""Verify a running installation through its public HTTP API.

Creates a clearly labelled QA project. Never reads or prints model credentials.
Linux Office conversion can be required explicitly with --require-office.
"""
import argparse
import hashlib
import io
import json
import os
import sys
import time
import zipfile
from pathlib import Path
from urllib.parse import urlparse
import httpx

ROOT=Path(__file__).resolve().parent.parent

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--url",default="http://127.0.0.1:8000")
    parser.add_argument("--require-office",action="store_true")
    parser.add_argument("--output",type=Path,default=Path(os.getenv("CHEMELLM_DATA_DIR",str(ROOT/"data")))/"qa"/"deployment-results.json")
    args=parser.parse_args()
    target=urlparse(args.url)
    if target.scheme not in {"http","https"} or not target.netloc or target.username or target.password:
        parser.error("Use an http(s) origin without embedded credentials.")
    headers={}
    token=os.getenv("CHEMELLM_AUTH_TOKEN","")
    if token:headers["Authorization"]="Bearer "+token
    checks=[]
    with httpx.Client(base_url=args.url.rstrip("/"),headers=headers,timeout=120,follow_redirects=False) as client:
        def get(path):
            r=client.get(path)
            if r.status_code!=200:raise RuntimeError(f"GET {path}: HTTP {r.status_code}")
            return r
        def post(path,body=None):
            r=client.post(path,json=body or {})
            if r.status_code!=200:raise RuntimeError(f"POST {path}: HTTP {r.status_code}")
            return r.json()
        assert get("/api/health").json()["status"]=="ok"
        assert "ChemELLM" in get("/").text
        cfg=get("/api/config").json()
        if args.require_office and not cfg["office_preview"]:
            raise RuntimeError("LibreOffice is unavailable; --require-office cannot pass.")
        checks.append("health/static/config")
        project=post("/api/projects",{"name":"部署验收 QA · "+str(time.time_ns())})
        prefix="/api/projects/"+project["id"]
        original=post(prefix+"/import-competition")
        acceptance=get(prefix+"/acceptance").json()
        assert acceptance["total"]==35 and acceptance["mandatory"]==31
        raw=get(original["download_url"]).content
        assert hashlib.sha256(raw).hexdigest()==original["metadata"]["sha256"]
        assert get(original["preview_url"]).content.startswith(b"%PDF")
        checks.append("competition requirements/original hash/PDF preview")
        tool_cases=[(name,{}) for name in ("material_balance","flash","column_mesh","aqueous_flash","frontend_process")]
        tool_cases.extend([("wet_column",{"equilibrium_stages":6,"feed_stage":3}),
            ("wet_separation_train",{"column_stages":6,"column_feed_stage":3}),
            ("mixture_reaction",{}),("recycle_process",{})])
        for tool,arguments in tool_cases:
            result=post(prefix+"/tools/"+tool,{"arguments":arguments})
            assert result["validation"]["passed"],tool
            checks.append(tool)
        generated=post(prefix+"/tools/export_report",{"arguments":{"title":"部署验收QA文档","body":"这是部署测试文档，包含中文字符与温度 298.15 K。\n不代表工程设计已完成。","formats":["pdf","docx","pptx"]}})
        preview_modes={}
        for artifact in generated["artifacts"]:
            raw=get(artifact["download_url"]).content
            preview=get(artifact["preview_url"])
            if artifact["kind"]=="pdf":assert raw.startswith(b"%PDF")
            else:
                assert zipfile.is_zipfile(io.BytesIO(raw))
                if args.require_office:assert preview.content.startswith(b"%PDF"),artifact["kind"]
            preview_modes[artifact["kind"]]="pdf" if preview.content.startswith(b"%PDF") else "text"
        checks.append("Office/PDF generation/download/preview")
        exported=post(prefix+"/bundle")
        with zipfile.ZipFile(io.BytesIO(get(exported["download_url"]).content)) as archive:
            manifest=json.loads(archive.read("manifest.json"))
            assert len(manifest["calculations"])==len(tool_cases)+1
            assert "reproduce/app/aqueous.py" in archive.namelist()
            assert "reproduce/app/wet_column.py" in archive.namelist()
            assert "reproduce/app/separation_train.py" in archive.namelist()
            assert "reproduce/app/recycle_process.py" in archive.namelist()
        checks.append("project bundle with calculations and replay source")
    output={"passed":True,"target":args.url,"project_id":project["id"],"checks":checks,
        "preview_modes":preview_modes,"office_required":args.require_office,
        "note":"HTTP checks against the named target only; this does not verify a real model, container build, process restart or engineering design."}
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(output,ensure_ascii=False,indent=2),encoding="utf-8")
    print(json.dumps(output,ensure_ascii=False,indent=2))

if __name__=="__main__":
    try:main()
    except (httpx.HTTPError,AssertionError,RuntimeError) as exc:
        print("Deployment check failed: "+str(exc),file=sys.stderr)
        raise SystemExit(1)
