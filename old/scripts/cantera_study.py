"""Run gas studies through HTTP; export source-linked reports and native models."""
import argparse
import json
import os
import sys
from pathlib import Path

import httpx

ROOT=Path(__file__).resolve().parent.parent
sys.path.insert(0,str(ROOT))
from scripts.cantera_benchmark import evaluate


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--base-url",default="http://127.0.0.1:8000")
    args=parser.parse_args()
    benchmark=evaluate()
    if not benchmark["passed"]:raise ValueError("Frozen benchmark failed")
    headers={"Authorization":"Bearer "+os.environ["CHEMELLM_AUTH_TOKEN"]} if os.environ.get("CHEMELLM_AUTH_TOKEN") else {}
    with httpx.Client(base_url=args.base_url,headers=headers,timeout=120) as client:
        def post(path,body=None):
            response=client.post(path,json=body or {});response.raise_for_status();return response.json()
        project=post("/api/projects",{"name":"Cantera气相研究 · WGS热力学与有限时间反应器"})
        prefix="/api/projects/"+project["id"]
        sources=[]
        files=[("Cantera-benchmark-protocol.json",(ROOT/"docs/CANTERA_BENCHMARK_PROTOCOL.json").read_bytes()),
               ("Cantera-benchmark-results.json",json.dumps(benchmark,ensure_ascii=False,indent=2).encode("utf-8"))]
        for species,source in benchmark["protocol"]["sources"].items():
            files.append(("NIST-"+species+".source.html.txt",(ROOT/source["source_file"]).read_bytes()))
        for filename,content in files:
            response=client.post(prefix+"/upload",files={"file":(filename,content,"application/octet-stream")})
            response.raise_for_status();sources.append(response.json())
        cases=[]
        composition={"CO":1,"H2O":1,"CO2":.1,"H2":.1}
        body=["研究范围：使用Cantera 3.2.0作指定物种集合内的理想气相平衡和均相闭式反应器研究。",
              "本研究由HTTP确定性工具执行，没有使用真实LLM规划，也不是保留测试或完整工程设计。",
              "四物种WGS仅允许CO/H2O/CO2/H2；未含甲烷、碳析出、液固相或催化机理。",
              "NIST Shomate与NASA关联式可能共享原始实验来源；对照不等于完全独立实验验证。",""]
        for reference in benchmark["thermodynamic_cases"]:
            T=reference["temperature_K"]
            parameters={"mechanism":"wgs4","constraint":"TP","temperature_K":T,"pressure_Pa":101325,"composition":composition}
            result=post(prefix+"/tools/cantera_equilibrium",{"arguments":parameters})
            if not result["validation"]["passed"]:raise ValueError("WGS validation failed")
            cases.append({"label":f"WGS-TP-{T:g}K","tool":"cantera_equilibrium","arguments":parameters,"result":result})
            x=result["final"]["mole_fractions"];kp=x["CO2"]*x["H2"]/(x["CO"]*x["H2O"])
            body.extend([f"WGS定温定压：T={T:g} K，P=101325 Pa；初始相对摩尔量CO/H2O/CO2/H2=1/1/0.1/0.1。",
                         f"平衡组成商={kp:.9g}；NIST参考Kp={reference['reference_Kp']:.9g}。",
                         "最终摩尔分数="+json.dumps(x),"计算记录="+result["calculation_id"],
                         "原生机理SHA256="+result["native_model_sha256"],""])
        parameters={"mechanism":"wgs4","constraint":"HP","temperature_K":1000,"pressure_Pa":101325,"composition":composition}
        hp=post(prefix+"/tools/cantera_equilibrium",{"arguments":parameters})
        if not hp["validation"]["passed"]:raise ValueError("HP validation failed")
        cases.append({"label":"WGS-HP-1000K","tool":"cantera_equilibrium","arguments":parameters,"result":hp})
        body.extend(["WGS定焓定压：初始1000 K、101325 Pa；这是不同能量约束的案例。",
                     f"最终温度={hp['final']['temperature_K']:.9g} K；初始/最终比焓={hp['initial']['enthalpy_J_kg']:.9g}/{hp['final']['enthalpy_J_kg']:.9g} J/kg。",
                     "计算记录="+hp["calculation_id"],""])
        parameters={"mechanism":"h2o2","constraint":"constant_pressure","energy":"adiabatic","temperature_K":1001,
                    "pressure_Pa":101325,"composition":{"H2":2,"O2":1,"N2":4},"end_time_s":.001,"samples":160}
        reactor=post(prefix+"/tools/cantera_reactor",{"arguments":parameters})
        if not reactor["validation"]["passed"]:raise ValueError("Reactor validation failed")
        cases.append({"label":"H2O2-closed-CP-adiabatic","tool":"cantera_reactor","arguments":parameters,"result":reactor})
        body.extend(["氢氧均相闭式反应器：初始1001 K、101325 Pa、H2/O2/N2=2/1/4；定压绝热，积分0.001 s。",
                     f"最终温度={reactor['final']['temperature_K']:.9g} K；输出{len(reactor['trajectory'])}个采样点。",
                     "有限时间轨迹不是平衡、稳态或点火延迟认证。没有用该机理替代乙苯催化脱氢。",
                     "计算记录="+reactor["calculation_id"],"",
                     "数值资格：3个WGS热力学对照、4个构造一级反应解析解对照通过预先登记容差。",
                     "构造A→B的解析解只验证积分实现，不验证真实反应机理。",
                     "每个工况的原生包含YAML、输入结果、许可证和独立运行脚本；反应器另有CSV/SVG/PDF轨迹。",
                     "复算比较证明可复现性；真实动力学、实验预测、催化/多相/设备与Linux平台仍需分别验证。",
                     "NIST来源及归档哈希："])
        for species,source in benchmark["protocol"]["sources"].items():
            body.extend([species+"："+source["url"],"SHA256="+source["sha256"]])
        reports=post(prefix+"/tools/export_report",{"arguments":{"title":"Cantera气相热力学与反应器研究","body":"\n".join(body),"formats":["docx","pdf","md","pptx"]}})
        bundle=post(prefix+"/bundle")
        output={"project":project,"cases":cases,"sources":sources,"benchmark":benchmark,"report":reports,"bundle":bundle,
                "status":"numerical_research_requires_review; no physical kinetics, LLM or Linux qualification"}
        target=ROOT/"data/cantera-study-results.json"
        target.write_text(json.dumps(output,ensure_ascii=False,indent=2,allow_nan=False),encoding="utf-8")
        print(json.dumps({"project":project["id"],"cases":len(cases),"benchmark_passed":benchmark["passed"],"results":str(target),"bundle":bundle["download_url"]},ensure_ascii=False))


if __name__=="__main__":main()
