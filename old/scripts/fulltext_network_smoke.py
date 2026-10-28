"""Real Europe PMC calls, no mocks; preserve failures and source provenance."""
import json
import sys
from pathlib import Path

sys.path.insert(0,str(Path(__file__).resolve().parent.parent))
from app import config
from app.db import init_db, execute, uid, now
from app.fulltext import FulltextImportInput, import_open_fulltext
from app.research import SearchInput, open_literature_search


def main():
    init_db()
    project_id=uid()
    execute("INSERT INTO projects VALUES(?,?,?)",(project_id,"真实开放全文联网QA",now()))
    report={"created_at":now(),"project_id":project_id,"scope":"real network in this execution environment; no model or scientific approval"}
    report["search"]=open_literature_search(SearchInput(query="PMCID:PMC10110988",limit=1))
    try:
        report["import"]=import_open_fulltext(project_id,FulltextImportInput(pmcid="PMC10110988"))
    except ValueError as exc:
        report["import"]={"error":str(exc)}
    report["passed"]=bool(report["search"]["results"]) and "extraction" in report["import"]
    folder=config.DATA/"qa";folder.mkdir(exist_ok=True)
    path=folder/"fulltext-network-results.json"
    path.write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding="utf-8")
    print(json.dumps({"passed":report["passed"],"project_id":project_id,"search_results":len(report["search"]["results"]),
                      "import_error":report["import"].get("error"),"evidence":str(path)},ensure_ascii=False))
    return 0 if report["passed"] else 1


if __name__=="__main__":raise SystemExit(main())
