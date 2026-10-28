"""Create a source-linked public-data study through the running HTTP API."""
import argparse
import json
import os
import sys
from pathlib import Path

import httpx

ROOT=Path(__file__).resolve().parent.parent
sys.path.insert(0,str(ROOT))
from app.benchmarks import CASES, evaluate_regression


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--base-url",default="http://127.0.0.1:8000")
    args=parser.parse_args()
    headers={"Authorization":"Bearer "+os.environ["CHEMELLM_AUTH_TOKEN"]} if os.environ.get("CHEMELLM_AUTH_TOKEN") else {}
    with httpx.Client(base_url=args.base_url,headers=headers,timeout=120) as client:
        def post(path,body=None):
            response=client.post(path,json=body or {})
            response.raise_for_status()
            return response.json()
        project=post("/api/projects",{"name":"NIST公开数据 · 实验建模与数值验证"})
        prefix="/api/projects/"+project["id"]
        analyses=[]
        body=["研究范围：对公开观测数据进行回归与模型比较。认证结果验证数值算法，不验证化学机理或未知条件外推。", "三个案例均为开发期间可见的公开参考，不能作为LLM保留测试集成绩。", ""]
        for name,case in CASES.items():
            artifact=post(prefix+"/datasets/example",{"name":name})
            analysis=post(prefix+"/tools/analyze_dataset",{"arguments":{"artifact_id":artifact["id"],"x_column":case["x_name"],"y_column":case["y_name"],"x_unit":case["x_unit"],"y_unit":case["y_unit"],"models":["linear",case["model"]]}})
            analyses.append(analysis)
            body.extend([name+"："+case["topic"], "数据来源："+artifact["metadata"]["reference"]["source_url"], "数据原文件SHA256："+artifact["metadata"]["reference"]["source_sha256"], "导入CSV SHA256："+analysis["source"]["sha256"]])
            for fit in analysis["fits"]:
                body.append(fit["model"]+"；RMSE="+str(fit["metrics"]["RMSE"])+"；AICc="+str(fit["metrics"]["AICc"]))
                for parameter in fit["parameters"]:
                    body.append(parameter["name"]+" = "+str(parameter["value"])+" "+parameter["unit"]+"；95%局部区间="+str(parameter["confidence_interval"]))
            body.append("比较依据："+analysis["comparison"]["interpretation"])
            body.append("")
        benchmark=evaluate_regression()
        body.extend(["NIST认证数值比较："+("全部通过预定容差" if benchmark["passed"] else "存在未通过项"), "不确定度范围：独立观测、误差假设与局部线性传播；不包含模型结构偏差、自变量误差或未建模混杂因素。", "下一步：按研究问题设计新增实验，对机理、参数适用范围与独立数据上的预测进行验证。"])
        reports=post(prefix+"/tools/export_report",{"arguments":{"title":"NIST公开数据·实验建模与数值验证","body":"\n".join(body),"formats":["pdf","docx","md"]}})
        bundle=post(prefix+"/bundle")
        output={"project":project,"analyses":analyses,"benchmark":benchmark,"report":reports,"bundle":bundle,
                "status":"numerical_qualification_only; research and physical validation pending"}
        target=ROOT/"data"/"experimental-study-results.json"
        target.write_text(json.dumps(output,ensure_ascii=False,indent=2,allow_nan=False),encoding="utf-8")
        print(json.dumps({"project":project["id"],"cases":len(analyses),"benchmark_passed":benchmark["passed"],"results":str(target),"bundle":bundle["download_url"]},ensure_ascii=False))


if __name__=="__main__":
    main()
