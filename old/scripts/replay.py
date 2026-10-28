"""Run from an extracted bundle's reproduce/ directory."""
import argparse
import json
import math
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
from app.db import init_db
from app.calculations import REGISTRY, calculate

def equivalent(a,b):
    if isinstance(a,dict) and isinstance(b,dict):
        return a.keys()==b.keys() and all(equivalent(a[k],b[k]) for k in a)
    if isinstance(a,list) and isinstance(b,list):
        return len(a)==len(b) and all(equivalent(x,y) for x,y in zip(a,b))
    if isinstance(a,(int,float)) and isinstance(b,(int,float)):
        return math.isclose(a,b,rel_tol=1e-8,abs_tol=1e-8)
    return a==b

def compare_result(tool,actual,expected):
    """Compare physical results; independently accepted residuals are diagnostics.

    MESH iteration counts and near-zero residuals vary with BLAS/SciPy. They
    remain in the manifest, but neither is a physical prediction. Both recorded
    and recomputed validation must pass before this exception can apply.
    """
    # JSON object keys are strings (for example UNIFAC subgroup IDs). Apply
    # the same wire format to both sides before comparing scientific values.
    actual=json.loads(json.dumps(actual,allow_nan=False))
    expected=json.loads(json.dumps(expected,allow_nan=False))
    if tool in {"cantera_equilibrium","cantera_reactor"}:
        if any(r.get("validation",{}).get("passed") is not True for r in (actual,expected)):return False
        def physical(result):
            result=json.loads(json.dumps(result))
            for k in ["artifacts","plot_artifact_id","native_archive_id","native_model_yaml"]:result.pop(k,None)
            result['solver'].pop('stats',None)
            result['validation']={'passed':True}
            return result
        def same(a,b):
            if isinstance(a,dict) and isinstance(b,dict):return a.keys()==b.keys() and all(same(a[k],b[k]) for k in a)
            if isinstance(a,list) and isinstance(b,list):return len(a)==len(b) and all(same(x,y) for x,y in zip(a,b))
            if isinstance(a,(int,float)) and isinstance(b,(int,float)):return math.isclose(a,b,rel_tol=1e-6,abs_tol=1e-8)
            return a==b
        return same(physical(actual),physical(expected))
    if tool=="fit_data":
        # Numerical regression diagnostics need not be bit-identical across BLAS.
        # Compare the full scientific output at a declared regression tolerance.
        def regression_equal(a,b):
            if isinstance(a,dict) and isinstance(b,dict):
                return a.keys()==b.keys() and all(regression_equal(a[k],b[k]) for k in a)
            if isinstance(a,list) and isinstance(b,list):
                return len(a)==len(b) and all(regression_equal(x,y) for x,y in zip(a,b))
            if isinstance(a,(int,float)) and isinstance(b,(int,float)):
                return math.isclose(a,b,rel_tol=1e-6,abs_tol=1e-8)
            return a==b
        return regression_equal(actual,expected)
    if tool=="recycle_process":
        if any(r.get("validation",{}).get("passed") is not True for r in (actual,expected)):return False
        if not compare_result("wet_column",actual["column"],expected["column"]):return False
        for r in (actual,expected):
            r.pop("column");r["validation"]={"passed":True}
            r["recycle_solver"]={"method":r["recycle_solver"]["method"]}
        return equivalent(actual,expected)
    if tool=="wet_separation_train":
        if any(r.get("validation",{}).get("passed") is not True for r in (actual,expected)):return False
        if not compare_result("frontend_process",actual["frontend"],expected["frontend"]):return False
        if not compare_result("wet_column",actual["column"],expected["column"]):return False
        for r in (actual,expected):
            r.pop("frontend");r.pop("column");r["validation"]={"passed":True}
        return equivalent(actual,expected)
    if tool in {"condenser_flash","frontend_process"}:
        if actual.get("validation",{}).get("passed") is not True or expected.get("validation",{}).get("passed") is not True:
            return False
        if tool=="frontend_process":
            if not compare_result("condenser_flash",actual["condenser"],expected["condenser"]):return False
            actual.pop("condenser");expected.pop("condenser")
        else:
            for result in (actual,expected):
                result["solver"]={"method":result["solver"]["method"]}
        for result in (actual,expected):result["validation"]={"passed":True}
        return equivalent(actual,expected)
    if tool in {"column_mesh","wet_column"}:
        if actual.get("validation",{}).get("passed") is not True or expected.get("validation",{}).get("passed") is not True:
            return False
        def physical(result):
            result=json.loads(json.dumps(result))
            result["solver"]={k:v for k,v in result.get("solver",{}).items() if k not in {"residual_evaluations","success","elapsed_seconds"}}
            result["validation"]={"passed":True}
            for stage in result["stages"]:
                for key in ("total_residual_kmol_h","light_residual_kmol_h","energy_residual_kW","component_residuals_kmol_h","minimum_searched_liquid_TPD"):
                    stage.pop(key,None)
            return result
        return equivalent(physical(actual),physical(expected))
    return equivalent(actual,expected)

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--manifest",type=Path,default=Path(__file__).resolve().parent.parent/"manifest.json")
    args=parser.parse_args()
    manifest=json.loads(args.manifest.read_text(encoding="utf-8"))
    init_db()
    results=[]
    skipped=[]
    non_replayable={"literature_search","open_literature_search","pubchem","project_search","pfd","export_report","acceptance","equipment_save","equipment_query","drawing_read","dataset_inspect","analyze_dataset","document_extract","document_read","fulltext_import","claim_save","evidence_add","evidence_check","evidence_export"}
    non_replayable.update({'project_context','engineering_object','engineering_deliverable','engineering_status','engineering_bundle',
                           'engineering_plan','engineering_requirements','calculation_read','source_fetch'})
    for record in manifest["calculations"]:
        if record["tool"] not in REGISTRY:
            if record["tool"] in non_replayable:
                skipped.append({"id":record["id"],"tool":record["tool"],"reason":"External lookup, document generation or project-state tool; original record retained, not re-executed."})
            else:
                results.append({"id":record["id"],"tool":record["tool"],"reproduced":False,"error":"Recorded tool is unavailable in this replay source."})
            continue
        try:
            actual=calculate(record["tool"],record["input"])
            results.append({"id":record["id"],"tool":record["tool"],"reproduced":compare_result(record["tool"],actual,record["result"])})
        except Exception as exc:
            results.append({"id":record["id"],"tool":record["tool"],"reproduced":False,"error":str(exc)})
    output={"results":results,"skipped":skipped,"comparison_policy":"Physical results: rel_tol=1e-8, abs_tol=1e-8; fit_data and Cantera output: rel_tol=1e-6, abs_tol=1e-8. Cantera compares all sampled states and native model hash, requires both numerical validations, and ignores artifact links, accepted residual diagnostics and CVODES statistics. MESH and H2 condenser/connected front-end require both validations to pass; iteration/branch-search diagnostics and accepted equation/stability residuals are not compared for equality. Dataset orchestration is skipped; its separately recorded fit_data inputs/results are replayed.","note":"复算一致不代表工程模型适用或设计通过审核。"}
    Path("replay-results.json").write_text(json.dumps(output,ensure_ascii=False,indent=2),encoding="utf-8")
    print(json.dumps(output,ensure_ascii=False,indent=2))
    return 0 if results and all(r["reproduced"] for r in results) else 1

if __name__=="__main__":
    raise SystemExit(main())
