"""Replayable once-through reaction/condenser/wet-distillation study."""
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
    execute("INSERT INTO projects VALUES(?,?,?)",(project_id,"2026竞赛 · 四元湿塔联立研究 · "+now(),now()))
    for path in (config.ROOT/"26化工设计大赛题目.pdf",config.ROOT/"docs/WET_COLUMN_MODEL.md",
        config.ROOT/"docs/HYDROGEN_MODEL.md",config.ROOT/"docs/sources/IAPWS-G7-04-HenGuide.pdf"):
        ingest(project_id,path.name,path.read_bytes())
    cases={n:run_tool(project_id,"wet_separation_train",{"column_stages":n,"column_feed_stage":n//2}) for n in (6,12)}
    result=cases[12]
    body=["范围与数据等级",
        "四组分一次通过研究：反应器→100 kPa冷凝分相→湿有机相绝热降压→20 kPa精馏塔→气液液塔顶分相。没有乙苯循环，不是全厂设计或合格产品报告。所有操作条件为研究假设。",
        "反应进料乙苯400 kmol/h、蒸汽比8，823.15→873.15 K，指定转化率0.6；前端与塔顶冷凝310 K。湿塔12个平衡级，含部分再沸器、不含塔顶分相器，进料第6级，回流比3，有机馏出/F=0.4。",
        "原始赛题、IAPWS原指南及两套模型说明均已导入本项目。IAPWS G7-04(2004)公式对照原表6四个温度点；原件版权归IAPWS，按注明归属条件保留。",
        "水中H2：前端为Sander2023低温参数，湿塔为IAPWS宽温式；有机H2为PR/kij=0预测。溶剂Dortmund UNIFAC、气相理想；不存在该体系实测或独立流程模拟软件验证。",
        "上游湿有机相的全部组分流量与实际焓直接传入塔进料；降压按绝热无轴功近似保持焓，不重置为塔压下饱和液。进料温度保留为上游描述，不声称降压后仍为同温单液相。",
        "全流程物流：水/乙苯/苯乙烯/H2，单位kmol/h；焓流kW，含生成焓参考。内部流股不重复计入全流程出口。"]
    for s in result["streams"]:
        flows=" / ".join(f"{v:.7g}" for v in s["component_flows_kmol_h"].values())
        body.append(f"{s['id']} {s['name']}（{s['boundary']}）；T={s['temperature_K']:.3f} K，P={s['pressure_Pa']:.0f} Pa；{flows}；H={s['enthalpy_flow_kW']:.6f}")
    body.extend(["热负荷与数学检查",
        f"反应供热 {result['reactor_heat_input_kW']:.6f} kW；前端冷凝移热 {result['condenser_heat_removed_kW']:.6f} kW；湿塔再沸供热 {result['column_reboiler_duty_kW']:.6f} kW；湿塔冷凝移热 {result['column_condenser_duty_removed_kW']:.6f} kW。",
        json.dumps(result["validation"],ensure_ascii=False),"湿塔检查："+json.dumps(result["column"]["validation"],ensure_ascii=False),
        "6级和12级比较：相同回流/馏出比例，进料置于中间级。级数变化同时改变进料级；不是独立实验对照或最优参数搜索。"])
    comparison=[]
    for n,case in cases.items():
        bottom=next(s for s in case["column"]["outlets"] if s["outlet"]=="bottoms")
        row={"stages":n,"feed_stage":n//2,"calculation_id":case["calculation_id"],
            "bottom_styrene_mole_fraction":bottom["mole_fractions"][2],
            "bottom_styrene_kmol_h":bottom["component_flows_kmol_h"]["styrene"],
            "reboiler_kW":case["column_reboiler_duty_kW"],"condenser_removed_kW":case["column_condenser_duty_removed_kW"]}
        comparison.append(row);body.append(json.dumps(row,ensure_ascii=False))
    body.extend(["未完成的工程工作",
        "12级默认塔底苯乙烯摩尔分数约0.799，不能标记合格产品；塔顶有机液仍含苯乙烯、水和H2，后续循环必须保留这些杂质。尾气和两股水相仍含芳烃，需要资源回收、废水和真空系统设计。",
        "每个热级只允许一个液相。有限TPD搜索检查没有发现不稳定，不能证明全局稳定；未来工况如出现两液相必须换用三相塔模型。极微量尾数不代表可测精度或可靠脱除率。",
        "仍缺产品规格驱动优化与完整循环、催化动力学/副反应、设备内件/水力学/机械、热集成、阻聚/安全、P&ID、三维布置、市场/现场调研及完整经济分析。",
        "数学收敛、复算一致、文件生成与工程验收不同。本报告仅关联P06为部分研究草稿，不自动标记任何验收通过。"])
    report=run_tool(project_id,"export_report",{"title":"2026赛题·四元湿精馏联立研究","body":"\n".join(body),"formats":["pdf","docx","md"]})
    drawing=run_tool(project_id,"pfd",{"title":"反应冷凝与四元湿塔·研究边界","drawing_type":"PFD",
        "nodes":[{"id":"R-101","label":"脱氢反应计算","kind":"reactor","x":110,"y":450},
            {"id":"E-102","label":"前端冷凝分相","kind":"exchanger","x":370,"y":450},
            {"id":"V-101","label":"前端含氢尾气","kind":"tank","x":370,"y":170},
            {"id":"TK-101","label":"前端水相","kind":"tank","x":370,"y":800},
            {"id":"T-101","label":"四元湿塔","kind":"column","x":720,"y":450},
            {"id":"V-102","label":"塔顶VLL分相","kind":"tank","x":1030,"y":250},
            {"id":"V-103","label":"塔顶尾气","kind":"tank","x":1430,"y":130},
            {"id":"TK-102","label":"塔顶水相","kind":"tank","x":1430,"y":400},
            {"id":"TK-103","label":"有机馏出待回收","kind":"tank","x":1430,"y":650},
            {"id":"TK-104","label":"塔底非合格产品","kind":"tank","x":1030,"y":800}],
        "edges":[{"source":"R-101","target":"E-102","label":"S02 反应出口"},
            {"source":"E-102","target":"V-101","label":"S03 尾气","route":[[370,410],[370,230]]},
            {"source":"E-102","target":"TK-101","label":"S04 水相","route":[[370,490],[370,740]]},
            {"source":"E-102","target":"T-101","label":"S05 湿液 / 等焓降压","route":[[410,450],[672,450]]},
            {"source":"T-101","target":"V-102","label":"塔顶蒸汽","route":[[720,390],[720,250],[982,250]]},
            {"source":"V-102","target":"T-101","label":"有机液回流","route":[[982,280],[860,280],[860,450],[768,450]]},
            {"source":"V-102","target":"V-103","label":"S08 塔顶尾气","route":[[1030,190],[1030,130],[1382,130]]},
            {"source":"V-102","target":"TK-102","label":"S07 水相","route":[[1078,250],[1250,250],[1250,400],[1382,400]]},
            {"source":"V-102","target":"TK-103","label":"S06 有机馏出","route":[[1030,310],[1030,650],[1382,650]]},
            {"source":"T-101","target":"TK-104","label":"S09 富苯乙烯塔底","route":[[720,510],[720,800],[982,800]]}]})
    evidence=[a["id"] for a in report["artifacts"]]
    execute("UPDATE requirements SET status='draft',evidence=?,notes=? WHERE project_id=? AND code='P06'",
        (json.dumps(evidence),"一次通过反应-冷凝-湿塔研究；尚缺循环、规格优化、全厂物热衡算和独立模型基准。",project_id))
    archive=bundle(project_id)
    output={"project_id":project_id,"status":"draft","comparison":comparison,
        "reports":[{"name":a["name"],"path":one("SELECT path FROM artifacts WHERE id=?",(a["id"],))["path"]} for a in report["artifacts"]],
        "drawings":[{"name":a["name"],"path":one("SELECT path FROM artifacts WHERE id=?",(a["id"],))["path"]} for a in drawing["artifacts"]],
        "bundle":one("SELECT path FROM artifacts WHERE id=?",(archive["id"],))["path"]}
    (config.DATA/"wet-train-study-results.json").write_text(json.dumps(output,ensure_ascii=False,indent=2),encoding="utf-8")
    print(json.dumps(output,ensure_ascii=False,indent=2))


if __name__=="__main__":main()
