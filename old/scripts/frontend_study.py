"""Create a replayable reactor/condenser study and source-linked deliverables."""
import json
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent.parent))
from app import config
from app.db import init_db,execute,uid,now,one
from app.documents import ingest
from app.toolbox import run_tool
from app.main import bundle

def main():
    init_db()
    project_id=uid()
    execute("INSERT INTO projects VALUES(?,?,?)",(project_id,"2026竞赛 · 反应与含氢冷凝联立 · "+now(),now()))
    task=config.ROOT/"26化工设计大赛题目.pdf"
    ingest(project_id,task.name,task.read_bytes())
    source=config.ROOT/"docs"/"HYDROGEN_MODEL.md"
    reference=ingest(project_id,source.name,source.read_bytes())
    cases={factor:run_tool(project_id,"frontend_process",{"organic_henry_multiplier":factor}) for factor in (.5,1.,2.)}
    result=cases[1.]
    body=["范围与状态",
        "本研究将乙苯脱氢与低压含氢冷凝分相实际连接。四种组分均传递，采用共同气相生成焓参考。尚未连接精馏、循环与全厂公用工程；不是完成全部赛题的设计报告。",
        "输入均为研究假设：乙苯400 kmol/h；蒸汽/乙苯8；气相进料823.15 K；反应873.15 K；指定转化率0.6；全段100 kPa；冷凝310 K。未用市场与资源调查确认产能和工艺路线。",
        "数值计算记录："+result["calculation_id"],
        "数据与模型说明文件："+reference["id"]+"；SHA256 "+reference["metadata"]["sha256"],
        "反应与相平衡模型",
        "反应为理想气体单反应。检查指定转化率不超过理想平衡上限；没有催化动力学、副反应、失活或设备尺寸。",
        "冷凝模型采用Dortmund UNIFAC溶剂、稀溶H2亨利模型与理想气体；水中H2参数来自Sander 2023汇编。有机溶剂H2亨利常数由PR/kij=0无限稀释预测，未由实验拟合。",
        "水中Hscp(298.15 K)=7.8e-6 mol/(m3 Pa)，dlnHscp/d(1/T)=530 K；Hpx=溶剂摩尔密度/Hscp。原始汇编：https://henrys-law.org/henry/casrn/1333-74-0；DOI 10.5194/acp-23-10901-2023。",
        "亨利混合常数使用溶剂组成的对数平均，溶剂逸度修正与焓从同一Gibbs模型导出；数学一致性测试不替代实验验证。303–313.15 K、50–200 kPa是实现限制。",
        "物流表：流量顺序为水/乙苯/苯乙烯/H2，单位kmol/h；焓流单位kW（含生成焓参考）。",
    ]
    for stream in result["streams"]:
        flows=" / ".join(f"{v:.6f}" for v in stream["component_flows_kmol_h"].values())
        body.append(f"{stream['id']} {stream['name']}；{stream['temperature_K']:.2f} K；{stream['pressure_Pa']:.0f} Pa；{flows}；焓流 {stream['enthalpy_flow_kW']:.6f}")
    body.extend([f"反应器供热 {result['reactor_heat_input_kW']:.6f} kW；冷凝器移热 {result['condenser_heat_removed_kW']:.6f} kW。",
        "物热检查："+json.dumps(result["validation"],ensure_ascii=False),
        "敏感性：改变有机H2亨利预测倍率；水中数据保持不变。倍率不是实验不确定度区间，也不代表参数校准。"])
    sensitivity=[]
    for factor,case in cases.items():
        vapor=next(s for s in case["streams"] if s["name"]=="含氢尾气")
        organic=next(s for s in case["streams"] if s["phase"]=="organic_liquid")
        row={"organic_henry_multiplier":factor,"calculation_id":case["calculation_id"],
            "hydrogen_in_organic_kmol_h":organic["component_flows_kmol_h"]["hydrogen"],
            "ethylbenzene_in_tailgas_kmol_h":vapor["component_flows_kmol_h"]["ethylbenzene"],
            "styrene_in_tailgas_kmol_h":vapor["component_flows_kmol_h"]["styrene"],
            "condenser_heat_removed_kW":case["condenser_heat_removed_kW"]}
        sensitivity.append(row)
        body.append(json.dumps(row,ensure_ascii=False))
    body.extend(["下一步与未完成项",
        "有机相仍含水与氢气，不能直接删除后送进二元塔；应建立实际脱气/脱水与多组分分离。尾气和水相含芳烃，需要回收及废水处理设计。",
        "需要实测H2有机溶剂溶解度、混合溶剂数据、VLE/LLE与独立模拟软件基准。热负荷尚未用于换热器选型、面积、压降或安全联锁设计。",
        "仍需联立多组分塔和循环、确认产品纯度/收率、催化反应器工艺与机械设计、热集成、P&ID/HAZOP、三维布置、调研与经济评价。",
        "本草稿只关联P06为部分研究；任何数值收敛和文件生成都不会自动标记工程验收通过。"])
    report=run_tool(project_id,"export_report",{"title":"2026赛题·反应与含氢冷凝联立研究","body":"\n".join(body),"formats":["pdf","docx","md"]})
    nodes=[{"id":"R-101","label":"脱氢反应器","kind":"reactor","x":150,"y":230},
        {"id":"E-102","label":"冷凝与分相计算边界","kind":"exchanger","x":440,"y":230},
        {"id":"V-101","label":"含水和芳烃的氢气尾气","kind":"tank","x":850,"y":130},
        {"id":"TK-101","label":"含有机物和氢气的水相","kind":"tank","x":850,"y":350},
        {"id":"TK-102","label":"含水和氢气的有机相","kind":"tank","x":850,"y":570}]
    drawing=run_tool(project_id,"pfd",{"title":"反应与含氢冷凝·研究计算边界","drawing_type":"PFD","nodes":nodes,
        "edges":[{"source":"R-101","target":"E-102","label":"S02 水/乙苯/苯乙烯/H2"},
            {"source":"E-102","target":"V-101","label":"S03 尾气","route":[[440,190],[440,130],[802,130]]},
            {"source":"E-102","target":"TK-101","label":"S04 水相","route":[[480,230],[640,230],[640,350],[802,350]]},
            {"source":"E-102","target":"TK-102","label":"S05 湿有机相","route":[[440,270],[440,570],[802,570]]}]})
    evidence=[a["id"] for a in report["artifacts"]]
    execute("UPDATE requirements SET status='draft',evidence=?,notes=? WHERE project_id=? AND code='P06'",
        (json.dumps(evidence),"仅完成反应-冷凝前端研究，尚缺精馏、循环和全厂物热衡算；模型缺少实验与独立软件基准。",project_id))
    archive=bundle(project_id)
    output={"project_id":project_id,"status":"draft","sensitivity":sensitivity,
        "reports":[{"name":a["name"],"path":one("SELECT path FROM artifacts WHERE id=?",(a["id"],))["path"]} for a in report["artifacts"]],
        "drawings":[{"name":a["name"],"path":one("SELECT path FROM artifacts WHERE id=?",(a["id"],))["path"]} for a in drawing["artifacts"]],
        "bundle":one("SELECT path FROM artifacts WHERE id=?",(archive["id"],))["path"]}
    destination=config.DATA/"frontend-study-results.json"
    destination.write_text(json.dumps(output,ensure_ascii=False,indent=2),encoding="utf-8")
    print(json.dumps(output,ensure_ascii=False,indent=2))

if __name__=="__main__":main()
