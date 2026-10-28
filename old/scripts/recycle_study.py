"""Create source-linked, reproducible four-component recycle deliverables."""
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
    init_db();project_id=uid()
    execute("INSERT INTO projects VALUES(?,?,?)",(project_id,"2026竞赛 · 四元循环与纯度研究 · "+now(),now()))
    for path in (config.ROOT/"26化工设计大赛题目.pdf",*(config.ROOT/"docs"/name for name in
        ("RECYCLE_MODEL.md","WET_COLUMN_MODEL.md","HYDROGEN_MODEL.md","sources/IAPWS-G7-04-HenGuide.pdf"))):
        ingest(project_id,path.name,path.read_bytes())
    result=run_tool(project_id,"recycle_process",{})
    if not result["validation"]["passed"]:raise RuntimeError("研究案例没有通过数学检查")
    spec=result["product_specification"]
    body=["范围与研究假设",
        "本研究实际连接四组分反应、前端冷凝、湿塔和有机馏出循环。水/乙苯/苯乙烯/H2全部保留，循环液经泵升压及汽化预热后入反应器。不是全厂工程设计或全部赛题交付。",
        "新鲜液态乙苯400 kmol/h、310 K；反应入口总水/总乙苯=8；外部水蒸汽以823.15 K气相供应，未包括锅炉产汽。反应入口823.15 K、出口873.15 K、100 kPa、指定单程转化率0.6。",
        "前端与塔顶冷凝均310 K；湿塔20 kPa、50个平衡级、进料25级、回流比10、有机馏出/F=0.4。馏出1%排放，其余四组分均循环。泵效率0.7、平均摩尔体积0.12 m3/kmol为待验证假设。",
        "纯度目标0.998质量分数是用户可改的研究假设，不是已确认的完整产品标准；没有真实副产物、阻聚剂、聚合、催化动力学或机械/水力学设计。",
        "数据与求解：NIST高温热容与生成焓，Dortmund UNIFAC溶剂，Sander低温水中H2/IAPWS宽温水中H2，有机H2为PR/kij=0无限稀释预测。IAPWS G7-04原件归IAPWS，已附于项目；暂无该体系实验或独立模拟器基准。",
        "逐级MESH与VLL塔顶采用对数流量残差、稀疏Newton及原关联式精修，外层四组分循环用Anderson加速。初始化的理想二元分布仅为初猜，不代替最终四元方程。",
        "计算记录："+result["calculation_id"],
        "结果与检查",
        f"塔底预测苯乙烯质量分数 {spec['predicted_styrene_mass_fraction']:.10f}；指定目标 {spec['target_styrene_mass_fraction']:.6f}；数值目标比较 {spec['meets_assumed_purity_target']}。苯乙烯塔底量 {spec['styrene_product_kmol_h']:.6f} kmol/h，净反应生成量的塔底回收率 {spec['styrene_recovery_of_net_reaction']:.8f}。",
        "循环实际组分kmol/h："+json.dumps(result["recycle_component_kmol_h"],ensure_ascii=False),
        f"补充水蒸汽 {result['makeup_steam_kmol_h']:.6f} kmol/h。反应器混合进料理想平衡转化率 {result['reactor']['equilibrium_conversion']:.8f}；指定0.6已检查可行。",
        "全边界数学检查："+json.dumps(result["validation"],ensure_ascii=False),
        "物流顺序为水/乙苯/苯乙烯/H2，单位kmol/h。焓流kW，含生成焓参考。只把外部进料/出口计入整体衡算，内部流股不重复计入。"]
    for s in result["streams"]:
        flow=" / ".join(f"{v:.8g}" for v in s["component_flows_kmol_h"].values())
        body.append(f"{s['id']} {s['name']}（{s['boundary']}），{s['temperature_K']:.3f} K，{s['pressure_Pa']:.0f} Pa；{flow}；H={s['enthalpy_flow_kW']:.6f}")
    body.append("热负荷与轴功，kW")
    for label,key in [("冷料汽化/预热","feed_conditioning_heat_kW"),("反应供热","reactor_heat_input_kW"),
        ("前端冷凝移热","condenser_heat_removed_kW"),("塔再沸供热","column_reboiler_duty_kW"),
        ("塔冷凝移热","column_condenser_duty_removed_kW"),("循环泵轴功","recycle_pump_work_kW")]:
        body.append(f"{label}：{result[key]:.6f}")
    body.append("循环残差，max |rout-rin|/max(1,|rout|)")
    for row in result["recycle_solver"]["history"]:body.append(f"第{row['iteration']}轮：{row['max_relative_or_absolute_residual']:.8g}")
    body.extend(["未完成的验证和交付",
        "单液热级及有限TPD搜索不是全局稳定性证明；极微量水/H2预测不代表实测脱除精度。不同温区水中H2模型的差异仍待实验或独立模拟器验证。",
        "未包括催化动力学、副反应、阻聚剂和聚合安全、塔压降/效率/内件/水力学/机械、换热网络、锅炉产汽、真空与尾气回收、废水处理、现场/市场调研和完整经济分析。",
        "默认研究边界只有当前四组分，达到指定纯度数值目标不代表产品标准全部满足或工程验收。31项必需赛题交付仍未完成；本草稿只关联P06为部分研究，不自动审核通过。"])
    report=run_tool(project_id,"export_report",{"title":"2026赛题·四元循环与纯度研究","body":"\n".join(body),"formats":["pdf","docx","md"]})
    slides=run_tool(project_id,"export_report",{"title":"四元循环研究·计算进展",
        "body":"\n".join(["研究范围：反应、冷凝、湿塔、四组分循环与排放，尚非全厂设计。",
            "输入为假设：新鲜EB400 kmol/h、蒸汽比8、873.15 K、X=0.6，50级/20 kPa/R=10，1%排放。",
            f"塔底预测苯乙烯质量分数 {spec['predicted_styrene_mass_fraction']:.8f}，与指定0.998数值目标比较；未按完整产品标准验收。",
            "循环杂质保留："+json.dumps(result["recycle_component_kmol_h"],ensure_ascii=False),
            "预热/汽化、泵功及混合进料反应平衡均计入。",
            "物料、原子和共同参考能量闭合；可独立解压复算，尚无实验/独立模拟器基准。",
            "待完成：动力学/副反应、阻聚/安全、设备、热集成、真空/回收/废水、调研与经济设计。"]),"formats":["pptx"]})
    nodes=[("F-101","新鲜液态乙苯","tank",110,350),("F-102","补充水蒸汽","tank",110,150),
        ("E-101","混合汽化预热","exchanger",350,350),("R-101","脱氢反应计算","reactor",600,350),
        ("E-102","前端冷凝分相","exchanger",850,350),("V-101","前端尾气","tank",850,130),
        ("TK-101","前端水相","tank",850,650),("T-101","四元湿塔","column",1150,350),
        ("V-102","塔顶VLL分相","tank",1400,150),("V-103","塔顶尾气","tank",1400,430),
        ("TK-102","塔顶水相","tank",1400,650),("TK-103","塔底待工程验收","tank",1150,600),
        ("V-104","有机馏出分流","tank",1150,800),("TK-104","循环排放待回收","tank",1450,900),
        ("P-101","循环泵计算边界","pump",600,800)]
    edges=[("F-101","E-101","F01 新鲜乙苯",[[158,350],[310,350]]),
        ("F-102","E-101","F02 补充蒸汽",[[158,150],[350,150],[350,310]]),
        ("E-101","R-101","S01 实际气相进料",[[390,350],[552,350]]),
        ("R-101","E-102","S02 反应出口",[[648,350],[810,350]]),
        ("E-102","V-101","S03 前端尾气",[[850,310],[850,190]]),
        ("E-102","TK-101","S04 前端水相",[[850,390],[850,590]]),
        ("E-102","T-101","S05 湿液 / 等焓降压",[[890,350],[1102,350]]),
        ("T-101","V-102","塔顶蒸汽",[[1150,290],[1150,150],[1352,150]]),
        ("V-102","T-101","有机液内回流",[[1352,180],[1280,180],[1280,350],[1198,350]]),
        ("V-102","V-103","S08 塔顶尾气",[[1448,130],[1550,130],[1550,430],[1448,430]]),
        ("V-102","TK-102","S07 塔顶水相",[[1448,170],[1600,170],[1600,650],[1448,650]]),
        ("V-102","V-104","S06 有机馏出",[[1400,210],[1400,270],[1300,270],[1300,710],[1150,710],[1150,740]]),
        ("T-101","TK-103","S09 塔底",[[1150,410],[1150,540]]),
        ("V-104","TK-104","P01 1%排放",[[1198,800],[1450,800],[1450,840]]),
        ("V-104","P-101","R01 四组分循环",[[1102,800],[640,800]]),
        ("P-101","E-101","循环升压 / 计入轴功",[[600,840],[600,980],[350,980],[350,390]])]
    drawing=run_tool(project_id,"pfd",{"title":"四元循环流程·研究计算边界","drawing_type":"PFD",
        "nodes":[dict(zip(["id","label","kind","x","y"],n)) for n in nodes],
        "edges":[dict(zip(["source","target","label","route"],e)) for e in edges]})
    evidence=[a["id"] for a in report["artifacts"]]
    execute("UPDATE requirements SET status='draft',evidence=?,notes=? WHERE project_id=? AND code='P06'",
        (json.dumps(evidence),"四元反应/冷凝/湿塔循环及进料调温已作研究闭合，未完成全厂工程、动力学及独立模拟器/实验基准。",project_id))
    archive=bundle(project_id)
    def paths(items):return [{"name":a["name"],"path":one("SELECT path FROM artifacts WHERE id=?",(a["id"],))["path"]} for a in items]
    output={"project_id":project_id,"status":"draft","calculation_id":result["calculation_id"],"product_specification":spec,
        "validation":result["validation"],"reports":paths(report["artifacts"]+slides["artifacts"]),"drawings":paths(drawing["artifacts"]),
        "bundle":one("SELECT path FROM artifacts WHERE id=?",(archive["id"],))["path"]}
    (config.DATA/"recycle-study-results.json").write_text(json.dumps(output,ensure_ascii=False,indent=2),encoding="utf-8")
    print(json.dumps(output,ensure_ascii=False,indent=2))


if __name__=="__main__":main()
