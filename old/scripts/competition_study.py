"""Build a source-backed, explicitly unfinished competition unit-model study.

No model account is required. This is a replayable study, not a replacement for
the linked flowsheet, design decisions, or independent engineering review.
"""
import json
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent.parent))
from app import config
from app.db import init_db, execute, uid, now, one
from app.documents import ingest
from app.toolbox import run_tool
from app.main import bundle

def main():
    init_db()
    project_id=uid()
    execute("INSERT INTO projects VALUES(?,?,?)",(project_id,"2026竞赛 · 单元模型与证据基础 · "+now(),now()))
    source=config.ROOT/"26化工设计大赛题目.pdf"
    original=ingest(project_id,source.name,source.read_bytes())
    cases={
        "material_balance":{"product_t_per_year":200000,"operating_hours":8000,"conversion":.6,"ethylbenzene_recovery":.99,"recycle_purge":.01},
        "reaction_thermo":{"ethylbenzene_kmol_h":400,"steam_to_ethylbenzene":8,"inlet_temperature_K":823.15,
            "reactor_temperature_K":873.15,"pressure_Pa":100000,"conversion":.6},
        "column_mesh":{"light_component":"ethylbenzene","heavy_component":"styrene","feed_kmol_h":100,
            "feed_light_fraction":.4,"equilibrium_stages":50,"feed_stage":25,"pressure_Pa":20000,
            "distillate_fraction":.4,"reflux_ratio":10},
        "aqueous_flash":{"feed_kmol_h":100,"mole_fractions":[.8,.08,.12],"temperature_K":310,"pressure_Pa":101325},
    }
    result={name:run_tool(project_id,name,args) for name,args in cases.items()}
    vll=run_tool(project_id,"aqueous_flash",{**cases["aqueous_flash"],"temperature_K":360,"pressure_Pa":80000})
    thermo=result["reaction_thermo"]
    tower=result["column_mesh"]
    separation=result["aqueous_flash"]
    body=[
        "研究目标与状态",
        "本文件对应原赛题第3页流程仿真、物热衡算与设备设计的前置模型工作。下列工况是独立的示例假设，尚未组成同一条闭合流程。",
        "20万吨/年、8000小时/年及乙苯路线都不是已完成市场/资源调查后确认的设计决策。未确定厂址、原料规格和产品指标。",
        "原任务书：文件 "+original["id"]+"；SHA256 "+original["metadata"]["sha256"],
        "一、物料计量与循环示例",
        "计算记录 "+result["material_balance"]["calculation_id"],
        "输入假设："+json.dumps(cases["material_balance"],ensure_ascii=False),
        "输出 kg/h："+json.dumps(result["material_balance"]["streams"],ensure_ascii=False),
        "这是指定转化率和回收率的理想计量循环；回收率未由分离设备计算，也不含蒸汽和副反应。",
        "二、反应热力学",
        "计算记录 "+thermo["calculation_id"],
        "输入假设："+json.dumps(cases["reaction_thermo"],ensure_ascii=False),
        f"873.15 K理想气体标准反应焓 {thermo['thermodynamics']['delta_H_J_mol']/1000:.6f} kJ/mol；Kp={thermo['thermodynamics']['Kp_dimensionless']:.9f}；标准压力1 bar。",
        f"给定条件平衡转化率 {thermo['equilibrium_conversion']:.6f}；指定转化率0.6的供热量 {thermo['heat_duty_kW']:.3f} kW。供热量只覆盖气相进料显热与反应热。",
        "乙苯/苯乙烯的标准气相生成焓、熵和高温Cp取自NIST WebBook原表，选用条目和出处保存在计算记录。氢气用WebBook Shomate热容。未建立催化动力学、失活、选择性及副反应。",
        "https://webbook.nist.gov/cgi/cbook.cgi?ID=C100414&Units=SI&Mask=1",
        "https://webbook.nist.gov/cgi/cbook.cgi?ID=C100425&Units=SI&Mask=1",
        "三、二元真空精馏单元",
        "计算记录 "+tower["calculation_id"],
        "输入假设："+json.dumps(cases["column_mesh"],ensure_ascii=False),
        f"塔顶乙苯摩尔分数 {tower['distillate_light_fraction']:.9f}；塔底乙苯摩尔分数 {tower['bottoms_light_fraction']:.9f}。",
        f"再沸器 {tower['reboiler_duty_kW']:.3f} kW；冷凝器移热 {tower['condenser_duty_removed_kW']:.3f} kW；全塔能量残差 {tower['validation']['global_energy_residual_kW']:.3g} kW。",
        "50级包含部分再沸器、不含全凝器；第25级饱和液进料；等压20 kPa。Raoult理想液/理想气，未以实测VLE或独立模拟器验证。塔径、内件、压降、停留时间和阻聚设计均未完成。",
        "逐级结果（级数；温度K；液相乙苯摩尔分数；气相乙苯摩尔分数；L kmol/h；V kmol/h）",
    ]
    body.extend(f"{s['stage']}; {s['temperature_K']:.4f}; {s['liquid_light_fraction']:.8f}; {s['vapor_light_fraction']:.8f}; {s['liquid_kmol_h']:.4f}; {s['vapor_kmol_h']:.4f}" for s in tower["stages"])
    body.extend([
        "四、水与有机物分相单元",
        "液液记录 "+separation["calculation_id"]+"；气液液记录 "+vll["calculation_id"],
        "输入顺序为水/乙苯/苯乙烯；摩尔分数0.8/0.08/0.12；进料100 kmol/h。310 K、101325 Pa得到两液相；360 K、80000 Pa得到气液液三相。",
        "模型：Dortmund UNIFAC version 1/DOUFIP2016液相，理想气相，忽略Poynting修正。用组分闭合、共存相逸度及231点液相稳定性筛查校验。预测尚无本项目实验基准。",
    ])
    for phase in separation["phases"]:
        body.append(f"{phase['phase']}: {phase['flow_kmol_h']:.6f} kmol/h；组成 "+json.dumps(phase["mole_fractions"]))
    body.extend([
        "模型保留水相有机物溶解损失和有机相含水，不是完全分割。当前不支持氢气，不能把完整反应器出口直接送入此工具。",
        "https://thermo.readthedocs.io/thermo.unifac.html",
        "五、流程连接前必须解决的缺项",
        "建立氢气/水/芳烃冷凝与气液分配模型，包括可靠的Henry常数或经验证逸度模型；以实验/文献数据验证水与有机物相平衡。",
        "建立含水有机物的脱水和多组分精馏，或提供经验证的独立脱水单元；不得直接删去有机相中的水后送入二元塔。",
        "引入催化剂动力学、副反应及压降，再计算反应器体积。联立循环后重新核对各组分、原子、温压与统一焓基准，计算真实产品纯度、收率和公用工程。",
        "市场、资源、厂址、政策、工艺比选、HAZOP、P&ID、设备工艺/机械设计、配管/三维布置、经济评价和规范图集仍需完成。",
        "数学残差合格和文件生成不构成工程验收；验收状态由使用者关联证据并逐项校核。",
    ])
    report=run_tool(project_id,"export_report",{"title":"2026赛题·单元模型研究草稿","body":"\n".join(body),"formats":["docx","pdf","md"]})
    presentation=run_tool(project_id,"export_report",{"title":"2026赛题·研究进展与缺项","body":"\n".join([
        "独立单元研究，尚未形成闭合流程；所有操作参数均为待确认假设。",
        f"反应热力学：873.15 K，ΔH={thermo['thermodynamics']['delta_H_J_mol']/1000:.3f} kJ/mol，理想平衡转化率{thermo['equilibrium_conversion']:.4f}。",
        f"二元塔：50级、20 kPa、回流比10；xD={tower['distillate_light_fraction']:.6f}，xB={tower['bottoms_light_fraction']:.6f}。",
        f"二元塔供热{tower['reboiler_duty_kW']:.1f} kW；移热{tower['condenser_duty_removed_kW']:.1f} kW。",
        "水/乙苯/苯乙烯UNIFAC模型可得到两液相和气液液三相，保留互溶损失。",
        "优先缺项：氢气分配、多组分分离、VLE/LLE与催化动力学基准、循环与全流程物热衡算。",
        "后续交付：厂址与市场依据、P&ID、设备与布置、HAZOP、经济评价及规范图集。",
        "所有计算记录、原始任务书和复算源码均在项目成果包中；草稿不能自动通过验收。",
    ]),"formats":["pptx"]})
    evidence=[a["id"] for a in report["artifacts"]]
    for code in ("E02","P06"):
        execute("UPDATE requirements SET status='draft',evidence=?,notes=? WHERE project_id=? AND code=? AND status='missing'",
            (json.dumps(evidence),"仅完成独立单元研究草稿。各工况未连接成闭合流程；不代表完整物热衡算或塔器工程设计已完成。",project_id,code))
    archive=bundle(project_id)
    records={name:{"input":cases[name],"calculation_id":r["calculation_id"],"validation":r.get("validation")} for name,r in result.items()}
    records["aqueous_vll"]={"calculation_id":vll["calculation_id"],"validation":vll["validation"]}
    output={"project_id":project_id,"status":"draft","calculations":records,
        "reports":[{"name":a["name"],"path":one("SELECT path FROM artifacts WHERE id=?",(a["id"],))["path"]} for a in report["artifacts"]+presentation["artifacts"]],
        "bundle":one("SELECT path FROM artifacts WHERE id=?",(archive["id"],))["path"]}
    destination=config.DATA/"competition-study-results.json"
    destination.write_text(json.dumps(output,ensure_ascii=False,indent=2),encoding="utf-8")
    print(json.dumps(output,ensure_ascii=False,indent=2))

if __name__=="__main__":
    main()
