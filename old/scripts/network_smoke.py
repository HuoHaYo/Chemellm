"""Live public API verification; records actual responses, no generated substitutes."""
import json
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent.parent))
from app.research import literature_search, pubchem, SearchInput, PubChemInput
from app.db import now

def main():
    result={"checked_at":now(),
            "literature":literature_search(SearchInput(query="ethylbenzene dehydrogenation styrene energy integration",limit=5)),
            "pubchem":pubchem(PubChemInput(compound="styrene"))}
    destination=Path(__file__).resolve().parent.parent/"data"/"qa"
    destination.mkdir(parents=True,exist_ok=True)
    (destination/"network-results.json").write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding="utf-8")
    print(json.dumps({"literature_status":result["literature"]["status"],"papers":len(result["literature"]["results"]),
                      "pubchem_status":result["pubchem"]["status"],"errors":result["literature"]["errors"]},ensure_ascii=False))
    return 0 if result["literature"]["status"]==result["pubchem"]["status"]=="ok" else 1

if __name__=="__main__":
    raise SystemExit(main())
