"""Source-linked literature workflow; no invented expert or model approval."""
import argparse
import hashlib
import json
import os
from pathlib import Path

import httpx

ROOT=Path(__file__).resolve().parent.parent


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--base-url",default="http://127.0.0.1:8000")
    args=parser.parse_args()
    headers={"Authorization":"Bearer "+os.environ["CHEMELLM_AUTH_TOKEN"]} if os.environ.get("CHEMELLM_AUTH_TOKEN") else {}
    with httpx.Client(base_url=args.base_url,headers=headers,timeout=100) as client:
        def post(path,body=None):
            response=client.post(path,json=body or {})
            response.raise_for_status()
            return response.json()
        project=post("/api/projects",{"name":"全文证据研究 · 亨利常数定义与储氢传质"})
        prefix="/api/projects/"+project["id"]
        def tool(name,arguments):return post(prefix+"/tools/"+name,{"arguments":arguments})
        response=client.post(prefix+"/tools/fulltext_import",json={"arguments":{"pmcid":"PMC10110988"}})
        import_record={"actual_status_code":response.status_code,"provider":"Europe PMC","pmcid":"PMC10110988"}
        if response.status_code==200:
            imported=response.json();article=imported["artifact"];snapshot=imported["extraction"]
            import_record["mode"]="live_open_fulltext"
        else:
            import_record["error"]=response.text[:1500]
            raw=ROOT/"docs/sources/fulltext/PMC10110988.xml"
            response=client.post(prefix+"/upload",files={"file":(raw.name,raw.read_bytes())})
            response.raise_for_status();article=response.json()
            snapshot=tool("document_extract",{"artifact_id":article["id"]})
            import_record["mode"]="archived_real_open_fulltext"
            import_record["archive_sha256"]=hashlib.sha256(raw.read_bytes()).hexdigest()
        original=ROOT/"docs/sources/IAPWS-G7-04-HenGuide.pdf"
        response=client.post(prefix+"/upload",files={"file":(original.name,original.read_bytes())})
        response.raise_for_status();guide=response.json()
        guide_snapshot=tool("document_extract",{"artifact_id":guide["id"],"last_page":9})
        article_blocks=tool("document_read",{"snapshot_id":snapshot["snapshot_id"],"limit":100})["blocks"]
        guide_blocks=tool("document_read",{"snapshot_id":guide_snapshot["snapshot_id"],"limit":100})["blocks"]
        equilibrium=next(b for b in article_blocks if "An essential assumption in Henrys law" in b["text"])
        temperature=next(b for b in article_blocks if "Henry solubility constant" in b["text"])
        definition=next(b for b in guide_blocks if b["kind"]=="page_text" and b["locator"]["page"]==2)
        table=next(b for b in article_blocks if b["kind"]=="table" and "Henry constant for hydrogen" in b["text"])
        claims=[]
        def create(text):return tool("claim_save",{"text":text})
        def attach(claim,snap,block,quote,relation,conditions):
            return tool("evidence_add",{"claim_id":claim["id"],"expected_revision":claim["revision"],"snapshot_id":snap["snapshot_id"],"block_id":block["id"],"quote":quote,"relation":relation,"conditions":conditions})
        claim=create("地下储氢反应器在微生物生长全过程中均可直接使用气液平衡浓度，无需传质模型。")
        claim=attach(claim,snapshot,equilibrium,equilibrium["text"],"refutes","Strobel等2023：有微生物消耗的加压间歇反应器；作者区分初始状态与生长过程。")
        claims.append(claim)
        claim=create("氢气亨利常数的比较必须核对常数定义、浓度基准、温度与体系，不能直接比较不同定义的数字。")
        quote="liquid-phase fugacity and mole fraction of the solute."
        claim=attach(claim,guide_snapshot,definition,quote,"context","IAPWS2004第2页式(1)：kH以逸度/液相摩尔分数定义；指南仅考虑溶剂饱和边界。")
        quote="To account for the higher temperature inside the reactor, the Henry constant can be corrected with the following approach:"
        claim=attach(claim,snapshot,temperature,quote,"context","Strobel等2023：亨利溶解度系数和温度修正；需与IAPWS的kH定义区分。")
        row=next(row for row in table["cells"] if any("Henry constant for hydrogen" in cell for cell in row))
        claim=attach(claim,snapshot,table,"\t".join(row),"context","论文表2的氢气系数、单位与37/63摄氏度工况；提取转录须对照源表，不把不同定义当作数据矛盾。")
        claims.append(claim)
        retrieval=tool("project_search",{"query":"Henry equilibrium temperature","limit":6})
        evidence=tool("evidence_export",{})
        body=["研究问题：如何使用文献中的亨利常数，何时需要显式传质模型？", "来源一：Gion Strobel、Birger Hagemann、Christian Truitt Lüddeke、Leonhard Ganzer (2023). Coupled model for microbial growth and phase mass transfer in pressurized batch reactors in the context of underground hydrogen storage. DOI:10.3389/fmicb.2023.1150102。CC BY，原文归原作者及出版方。", "来源二：IAPWS (2004), Guideline on the Henry’s Constant and Vapor-Liquid Distribution Constant for Gases in H2O and D2O at High Temperatures。原文许可在注明IAPWS归属时转载。", "工作方式：归档真实全文、提取段落/表格/公式候选、保存源哈希；程序验证逐条引句存在。没有执行LLM对照或代替专家审核。", ""]
        for claim in claims:
            body.extend([claim["text"],"当前状态："+claim["review_status"]])
            for e in claim["evidence"]:
                body.extend(["原文："+e["data"]["quote"],"位置："+json.dumps(e["data"]["locator"],ensure_ascii=False),"条件标注："+e["data"]["conditions"],"关系标注："+e["data"]["relation"],"原件SHA256："+e["data"]["source_sha256"]])
            body.append("")
        body.extend(["工作解释：原论文明确区分初始平衡与微生物生长中的传质。IAPWS与论文使用的亨利常数基准不同，须先统一定义、浓度与温度；此处没有宣称两源数值相互矛盾。", "剩余核查：公式及表格需对照出版版、专家审核科学判断，并用独立实验验证具体过程模型；本文不宣布阶段B全部通过。"])
        report=tool("export_report",{"title":"亨利常数与储氢传质·全文证据研究","body":"\n".join(body),"formats":["pdf","docx","md"]})
        bundle=post(prefix+"/bundle")
        output={"project":project,"open_import":import_record,"article":article,"guide":guide,"snapshots":[snapshot,guide_snapshot],"claims":claims,"retrieval":retrieval,"evidence_export":evidence,"report":report,"bundle":bundle,"status":"quote_integrity_checked; scientific_review_and_model_comparison_pending"}
        target=ROOT/"data/literature-study-results.json"
        target.write_text(json.dumps(output,ensure_ascii=False,indent=2),encoding="utf-8")
        print(json.dumps({"project":project["id"],"claims":len(claims),"quotes":sum(len(c["evidence"]) for c in claims),"import_mode":import_record["mode"],"results":str(target)},ensure_ascii=False))


if __name__=="__main__":main()
