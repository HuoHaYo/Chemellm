import io
import json
import zipfile
from pathlib import Path

import httpx
from reportlab.pdfgen import canvas

from app.config import ROOT
from app.db import one, execute
from app.fulltext import extract_jats
from app.evidence import quote_match
from scripts.check_evidence_bundle import check_bundle

JATS=b'''<?xml version="1.0"?><article><front><article-meta><article-id pub-id-type="doi">10.0000/test-fixture</article-id><title-group><article-title>Controlled test source</article-title></title-group><permissions><license>Creative Commons Attribution 4.0</license></permissions><abstract><p>Gas solubility depends on temperature and solvent.</p></abstract></article-meta></front><body><sec id="s1"><title>Methods</title><p id="p1">Henry constants must be compared using the same definition and temperature.</p><p id="p2">The measured pressure was 100 kPa in the controlled test.</p><disp-formula id="eq1"><tex-math><![CDATA[H = p/x]]></tex-math></disp-formula><table-wrap id="t1"><label>Table 1</label><table><tr><th>T / K</th><th>H / Pa</th></tr><tr><td>300</td><td>100000</td></tr></table></table-wrap></sec></body></article>'''


def call(client, project_id, name, args):
    return client.post(f"/api/projects/{project_id}/tools/{name}",json={"arguments":args})


def source(client, project_id):
    response=client.post(f"/api/projects/{project_id}/upload",files={"file":("source.xml",JATS)})
    assert response.status_code==200,response.text
    artifact=response.json()
    result=call(client,project_id,"document_extract",{"artifact_id":artifact["id"]})
    assert result.status_code==200,result.text
    snapshot=result.json()
    blocks=call(client,project_id,"document_read",{"snapshot_id":snapshot["snapshot_id"]}).json()["blocks"]
    block=next(b for b in blocks if b["text"].startswith("Henry constants"))
    return artifact,snapshot,block


def claim_and_quote(client, project_id):
    artifact,snapshot,block=source(client,project_id)
    claim=call(client,project_id,"claim_save",{"text":"亨利常数的比较需要统一定义和温度条件。"}).json()
    args={"claim_id":claim["id"],"expected_revision":1,"snapshot_id":snapshot["snapshot_id"],"block_id":block["id"],"quote":block["text"],"relation":"supports","conditions":"同一定义、同一温度；测试资料"}
    response=call(client,project_id,"evidence_add",args)
    assert response.status_code==200,response.text
    return artifact,snapshot,block,response.json(),args


def test_jats_tables_formulas_locators_and_no_fabricated_page(client,project_id):
    _,snapshot,block=source(client,project_id)
    result=call(client,project_id,"document_read",{"snapshot_id":snapshot["snapshot_id"]}).json()
    assert snapshot["kinds"]["table"]==1 and snapshot["kinds"]["equation"]==1
    table=next(b for b in result["blocks"] if b["kind"]=="table")
    assert table["cells"]==[["T / K","H / Pa"],["300","100000"]]
    assert all(b["locator"]["page"] is None for b in result["blocks"])
    assert block["locator"]["anchor"]=="p1"
    search=call(client,project_id,"project_search",{"query":"Henry constant definition"}).json()
    assert search["results"][0]["snapshot_id"]==snapshot["snapshot_id"]
    assert search["results"][0]["block_id"]==block["id"]


def test_reject_xml_entities_and_non_jats(client,project_id):
    attack=b'<!DOCTYPE article [<!ENTITY e SYSTEM "file:///etc/passwd">]><article><body><p>&e;</p></body></article>'
    response=client.post(f"/api/projects/{project_id}/upload",files={"file":("unsafe.xml",attack)})
    assert response.status_code==422
    assert not client.get(f"/api/projects/{project_id}/artifacts").json()


def test_pdf_real_page_and_controlled_table_extraction(client,project_id):
    stream=io.BytesIO();pdf=canvas.Canvas(stream)
    pdf.drawString(60,780,"Controlled source. Q = m Cp dT")
    for y in [740,710,680]:pdf.line(60,y,300,y)
    for x in [60,180,300]:pdf.line(x,680,x,740)
    pdf.drawString(70,720,"Temperature K");pdf.drawString(190,720,"Pressure Pa")
    pdf.drawString(70,690,"300");pdf.drawString(190,690,"100000")
    pdf.save()
    artifact=client.post(f"/api/projects/{project_id}/upload",files={"file":("grid.pdf",stream.getvalue())}).json()
    response=call(client,project_id,"document_extract",{"artifact_id":artifact["id"]})
    assert response.status_code==200,response.text
    assert response.json()["kinds"]["table"]==1 and response.json()["kinds"]["equation_candidate"]>=1
    blocks=call(client,project_id,"document_read",{"snapshot_id":response.json()["snapshot_id"]}).json()["blocks"]
    assert all(b["locator"]["page"]==1 for b in blocks)
    assert next(b for b in blocks if b["kind"]=="table")["cells"][1]==["300","100000"]


def test_real_iapws_source_quote_with_page(client,project_id):
    content=(ROOT/"docs/sources/IAPWS-G7-04-HenGuide.pdf").read_bytes()
    artifact=client.post(f"/api/projects/{project_id}/upload",files={"file":("IAPWS.pdf",content)}).json()
    result=call(client,project_id,"document_extract",{"artifact_id":artifact["id"],"first_page":1,"last_page":1})
    assert result.status_code==200,result.text
    blocks=call(client,project_id,"document_read",{"snapshot_id":result.json()["snapshot_id"],"page":1}).json()["blocks"]
    assert any(quote_match(b["text"],"Publication in whole or in part is allowed in all countries")["matched"] for b in blocks)
    assert result.json()["total_pages"]==9


def test_quote_integrity_not_semantic_approval_and_misquote_rejected(client,project_id):
    artifact,snapshot,block,claim,args=claim_and_quote(client,project_id)
    assert claim["revision"]==2 and claim["review_status"]=="needs_review"
    assert claim["integrity_passed"] is True
    bad={**args,"expected_revision":2,"quote":"Henry constants are independent of temperature."}
    assert call(client,project_id,"evidence_add",bad).status_code==422
    assert quote_match("Pressure\nwas 100 kPa.","Pressure was 100 kPa.")["matched"]
    assert not quote_match("Pressure was 100 kPa.","Pressure was 900 kPa.")["matched"]


def test_review_invalidated_by_new_revision_and_source_change(client,project_id):
    artifact,_,_,claim,_=claim_and_quote(client,project_id)
    review={"expected_revision":2,"reviewer":"测试审核者","decision":"supported","notes":"仅用于验证审核版本失效的自动化测试记录。"}
    response=client.post(f'/api/projects/{project_id}/claims/{claim["id"]}/review',json=review)
    assert response.status_code==200,response.text
    assert response.json()["review_status"]=="supported"
    edited=call(client,project_id,"claim_save",{"text":"修改后的论断也需要重新审核其原文支持程度。","claim_id":claim["id"],"expected_revision":2}).json()
    assert edited["revision"]==3 and edited["review_status"]=="needs_review"
    assert client.post(f'/api/projects/{project_id}/claims/{claim["id"]}/review',json=review).status_code==422
    path=Path(one("SELECT path FROM artifacts WHERE id=?",(artifact["id"],))["path"])
    path.write_bytes(path.read_bytes()+b" ")
    checked=call(client,project_id,"evidence_check",{"claim_id":claim["id"]}).json()["claims"][0]
    assert not checked["integrity_passed"] and checked["review_status"]=="needs_review"


def test_opposing_annotations_are_reported_without_automatic_contradiction(client,project_id):
    _,_,_,claim,args=claim_and_quote(client,project_id)
    opposite={**args,"expected_revision":2,"relation":"refutes","conditions":"不同条件的录入者标注，不能自动判定物理矛盾"}
    response=call(client,project_id,"evidence_add",opposite)
    assert response.status_code==200,response.text
    assert response.json()["conflict"]["opposing_annotations"]
    assert response.json()["review_status"]=="needs_review"


def test_cross_project_snapshot_and_claim_rejected(client,project_id):
    _,snapshot,block,claim,args=claim_and_quote(client,project_id)
    other=client.post('/api/projects',json={"name":"另一个项目"}).json()["id"]
    assert call(client,other,"document_read",{"snapshot_id":snapshot["snapshot_id"]}).status_code==422
    assert call(client,other,"evidence_add",args).status_code==422


def test_open_fulltext_requires_open_access_metadata(client,project_id,monkeypatch):
    original=httpx.Client
    def handler(request):
        if request.url.path.endswith('search'):
            return httpx.Response(200,json={"resultList":{"result":[{"pmcid":"PMC123456","isOpenAccess":"Y","doi":"10.0000/fixture"}]}})
        return httpx.Response(200,content=JATS)
    monkeypatch.setattr(httpx,"Client",lambda **kwargs:original(transport=httpx.MockTransport(handler),**kwargs))
    response=call(client,project_id,"fulltext_import",{"pmcid":"PMC123456"})
    assert response.status_code==200,response.text
    assert response.json()["artifact"]["metadata"]["fulltext_source"]["open_access_metadata"]=="Y"
    assert call(client,project_id,"fulltext_import",{"pmcid":"http://127.0.0.1/private"}).status_code==422


def test_nonopen_fulltext_not_fabricated(client,project_id,monkeypatch):
    original=httpx.Client
    monkeypatch.setattr(httpx,"Client",lambda **kwargs:original(transport=httpx.MockTransport(lambda r:httpx.Response(200,json={"resultList":{"result":[{"pmcid":"PMC123456","isOpenAccess":"N"}]}})),**kwargs))
    response=call(client,project_id,"fulltext_import",{"pmcid":"PMC123456"})
    assert response.status_code==422 and "开放获取" in response.text
    assert client.get(f"/api/projects/{project_id}/artifacts").json()==[]


def test_export_and_offline_bundle_verification_detect_tampering(client,project_id,tmp_path):
    artifact,_,_,claim,_=claim_and_quote(client,project_id)
    exported=call(client,project_id,"evidence_export",{})
    assert exported.status_code==200,exported.text
    assert {a["kind"] for a in exported.json()["artifacts"]}=={"json","md","docx","pdf"}
    bundle=client.post(f"/api/projects/{project_id}/bundle").json()
    with zipfile.ZipFile(io.BytesIO(client.get(bundle["download_url"]).content)) as archive:
        archive.extractall(tmp_path)
    checked=check_bundle(tmp_path/"manifest.json")
    assert checked["applicable"] and checked["passed"]
    raw=tmp_path/"files"/artifact["id"]/artifact["name"]
    raw.write_bytes(raw.read_bytes()+b"tampered")
    assert check_bundle(tmp_path/"manifest.json")["passed"] is False


def test_transcription_history_invalidation_replacement_and_bundle(client,project_id,monkeypatch,tmp_path):
    from PIL import Image
    from app import vision
    # State-machine fixture only; no model accuracy or live visual capability claim.
    monkeypatch.setattr(vision,"transcribe_image",lambda image,**kwargs:{
        "status":"transcribed_not_verified","request_made":True,"model":"test-vision",
        "text":"Pressure = 1o0 kPa","image_sha256":"a"*64,"response_sha256":"b"*64,
        "prompt_version":"test-v1","usage":{}})
    stream=io.BytesIO();Image.new("RGB",(220,50),"white").save(stream,format="PNG")
    artifact=client.post(f"/api/projects/{project_id}/upload",files={"file":("numeric.png",stream.getvalue())}).json()
    snapshot=call(client,project_id,"document_extract",{"artifact_id":artifact["id"],"image_mode":"ai"}).json()["snapshot_id"]
    block=call(client,project_id,"document_read",{"snapshot_id":snapshot}).json()["blocks"][0]
    claim=call(client,project_id,"claim_save",{"text":"控制图片记录的压力需要原图转录复核。"}).json()
    quote={"claim_id":claim["id"],"expected_revision":1,"snapshot_id":snapshot,"block_id":block["id"],"quote":block["text"]}
    old=call(client,project_id,"evidence_add",quote).json()["evidence"][0]["id"]
    review={"expected_revision":2,"decision":"insufficient","reviewer":"自动状态测试","notes":"测试审核保存和失效；不代表专家判断。","ocr_transcription_checked":True}
    endpoint=f"/api/projects/{project_id}/claims/{claim['id']}/review"
    assert client.post(endpoint,json=review).json()["review_status"]=="insufficient"
    correction={"reviewer":"自动状态测试","notes":"测试数字1o0改为100；该例不验证OCR准确性。","corrections":[{"block_id":block["id"],"text":"Pressure = 100 kPa"}]}
    response=client.post(f"/api/projects/{project_id}/documents/{snapshot}/transcription",json=correction)
    assert response.status_code==200,response.text
    corrected=response.json()["snapshot_id"]
    assert corrected!=snapshot
    original=call(client,project_id,"document_read",{"snapshot_id":snapshot}).json()
    assert original["blocks"][0]["text"]=="Pressure = 1o0 kPa"
    current=call(client,project_id,"document_read",{"snapshot_id":corrected}).json()
    assert current["blocks"][0]["text"]=="Pressure = 100 kPa"
    assert current["derived_from"]==snapshot and current["transcription_corrections"][0]["previous_text"]==block["text"]
    checked=call(client,project_id,"evidence_check",{"claim_id":claim["id"]}).json()["claims"][0]
    assert checked["integrity_passed"] and checked["transcription_recheck_required"] and checked["review_status"]=="needs_review"
    assert client.post(endpoint,json=review).status_code==422
    other=client.post('/api/projects',json={"name":"隔离测试"}).json()["id"]
    assert client.post(f"/api/projects/{other}/documents/{snapshot}/transcription",json=correction).status_code==422
    wrong=call(client,project_id,"evidence_add",{**quote,"expected_revision":2,"snapshot_id":corrected,"quote":"Pressure = 100 kPa","supersedes_evidence_id":"foreign"})
    assert wrong.status_code==422
    updated=call(client,project_id,"evidence_add",{**quote,"expected_revision":2,"snapshot_id":corrected,"quote":"Pressure = 100 kPa","supersedes_evidence_id":old}).json()
    assert len(updated["evidence"])==2 and updated["evidence"][0]["superseded"]
    assert not updated["transcription_recheck_required"] and updated["review_status"]=="needs_review"
    assert updated["evidence"][1]["data"]["transcription_history"][0]["previous_text"]==block["text"]
    review["expected_revision"]=3
    assert client.post(endpoint,json=review).json()["review_status"]=="insufficient"
    bundle=client.post(f"/api/projects/{project_id}/bundle").json()
    with zipfile.ZipFile(io.BytesIO(client.get(bundle["download_url"]).content)) as archive:archive.extractall(tmp_path)
    assert check_bundle(tmp_path/"manifest.json")["passed"]
    manifest_path=tmp_path/"manifest.json"
    manifest=json.loads(manifest_path.read_text(encoding="utf-8"))
    edited=next(s for s in manifest["document_snapshots"] if s["id"]==corrected)
    content=json.loads(edited["content"])
    content["transcription_corrections"][0]["previous_text"]="invented prior transcription"
    edited["content"]=json.dumps(content,ensure_ascii=False,sort_keys=True)
    import hashlib
    edited["content_sha256"]=hashlib.sha256(edited["content"].encode()).hexdigest()
    for c in manifest["research_evidence"]["claims"]:
        for e in c["evidence"]:
            if e["snapshot_id"]==corrected:e["data"]["content_sha256"]=edited["content_sha256"]
    manifest_path.write_text(json.dumps(manifest),encoding="utf-8")
    assert not check_bundle(manifest_path)["passed"]


def test_transcription_cannot_edit_nonocr_or_reuse_duplicate_blocks(client,project_id):
    _,snapshot,block=source(client,project_id)
    payload={"reviewer":"转录测试","notes":"不允许将人工修改的普通原文冒充OCR纠错。","corrections":[{"block_id":block["id"],"text":"Changed source text"}]}
    endpoint=f"/api/projects/{project_id}/documents/{snapshot['snapshot_id']}/transcription"
    assert client.post(endpoint,json=payload).status_code==422
    payload["corrections"]*=2
    assert client.post(endpoint,json=payload).status_code==422
