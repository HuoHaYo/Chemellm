"""Create a source deployment bundle with an explicit file allowlist."""
import hashlib
import json
from pathlib import Path
import zipfile

ROOT=Path(__file__).resolve().parent.parent
def main():
    destination=ROOT/"dist"
    destination.mkdir(exist_ok=True)
    files=[]
    for folder in ("app","web","scripts","docs","tests"):
        files.extend(p for p in (ROOT/folder).rglob("*") if p.is_file() and "__pycache__" not in p.parts and p.suffix not in {".pyc",".log"})
    files.extend(ROOT/name for name in ("Dockerfile","compose.yaml",".dockerignore",".env.example","pyproject.toml","README.md","26化工设计大赛题目.pdf"))
    path=destination/"chemellm-linux-source-0.1.0.zip"
    manifest={}
    with zipfile.ZipFile(path,"w",zipfile.ZIP_DEFLATED) as archive:
        for source in sorted(files):
            relative=source.relative_to(ROOT).as_posix()
            content=source.read_bytes()
            manifest[relative]=hashlib.sha256(content).hexdigest()
            archive.writestr("chemellm/"+relative,content)
        archive.writestr("chemellm/SHA256SUMS.json",json.dumps(manifest,indent=2,ensure_ascii=False))
    digest=hashlib.sha256(path.read_bytes()).hexdigest()
    # Keep LF on Windows so Linux sha256sum does not treat CR as filename text.
    path.with_suffix(".zip.sha256").write_bytes((digest+"  "+path.name+"\n").encode("utf-8"))
    print(json.dumps({"path":str(path),"files":len(files),"bytes":path.stat().st_size,"sha256":digest}))

if __name__=="__main__":
    main()
