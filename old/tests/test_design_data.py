import copy
import hashlib
from app.config import ROOT

def record():
    return {"tag":"E-101","name":"原料预热器","equipment_type":"exchanger","parameters":[
        {"name":"design_pressure","label":"设计压力","value":3,"unit":"bar","provenance":"assumption"},
        {"name":"design_temperature","label":"设计温度","value":120,"unit":"degC","provenance":"assumption"}
    ]}

def test_equipment_units_versions_and_stale_write(client,project_id):
    url=f"/api/projects/{project_id}/equipment"
    data=record()
    saved=client.post(url,json={"record":data})
    assert saved.status_code==200,saved.text
    r=saved.json()["record"]
    assert r["revision"]==1 and r["status"]=="draft"
    assert r["data"]["parameters"][0]["base_value"]==300000
    assert abs(r["data"]["parameters"][1]["base_value"]-393.15)<1e-9
    data["parameters"][0]["value"]=4
    assert client.post(url,json={"record":data}).status_code==422
    changed=client.post(url,json={"record":data,"expected_revision":1})
    assert changed.json()["record"]["revision"]==2
    stale=client.post(url,json={"record":data,"expected_revision":1})
    assert stale.status_code==422
    history=client.get(url+"/"+r["id"]+"/history").json()
    assert len(history)==2
    assert history[0]["data"]["parameters"][0]["value"]==4
    assert history[1]["data"]["parameters"][0]["value"]==3
    # Assumptions are visible and cannot pass source-backed review.
    review=client.post(url+"/"+r["id"]+"/review",json={"expected_revision":2,"status":"reviewed","notes":"已完成测试检查但参数仍然为假设数值"})
    assert review.status_code==422

def test_invalid_unit_and_source_rollback(client,project_id):
    url=f"/api/projects/{project_id}/equipment"
    data=record()
    data["parameters"][0]["unit"]="not_a_real_unit_zz"
    assert client.post(url,json={"record":data}).status_code==422
    assert client.get(url).json()==[]
    data=record()
    data["parameters"][0].update(provenance="datasheet")
    assert client.post(url,json={"record":data}).status_code==422
    source=client.post(f"/api/projects/{project_id}/import-competition").json()
    data["parameters"][0].update(artifact_id=source["id"],source_page=99)
    assert client.post(url,json={"record":data}).status_code==422
    data["parameters"][0]["source_page"]=4
    other=client.post("/api/projects",json={"name":"其他测试项目"}).json()["id"]
    assert client.post(f"/api/projects/{other}/equipment",json={"record":data}).status_code==422
    assert client.get(url).json()==[]

def test_source_hash_review_and_recalculated_revision(client,project_id):
    url=f"/api/projects/{project_id}/equipment"
    source=client.post(f"/api/projects/{project_id}/import-competition").json()
    actual_hash=hashlib.sha256((ROOT/"26化工设计大赛题目.pdf").read_bytes()).hexdigest()
    assert source["metadata"]["sha256"]==actual_hash
    result=client.post(f"/api/projects/{project_id}/tools/heat_exchanger",json={"arguments":{}}).json()
    data=record()
    data["parameters"]=[{"name":"area","label":"换热面积","value":result["area_m2"],"unit":"m^2","provenance":"calculated","calculation_id":result["calculation_id"],"artifact_id":source["id"],"source_page":4}]
    created=client.post(url,json={"record":data}).json()["record"]
    assert created["data"]["parameters"][0]["source_sha256"]==actual_hash
    # This test checks the manual review state machine, not source applicability.
    reviewed=client.post(url+"/"+created["id"]+"/review",json={"expected_revision":1,"status":"reviewed","notes":"测试审核状态持久化，尚不能代表实际设备工艺校核"})
    assert reviewed.status_code==200 and reviewed.json()["status"]=="reviewed"
    data["parameters"][0]["value"]+=1
    changed=client.post(url,json={"record":data,"expected_revision":1}).json()["record"]
    assert changed["status"]=="draft" and changed["review_notes"]==""
    history=client.get(url+"/"+created["id"]+"/history").json()
    assert history[1]["reviews"][0]["status"]=="reviewed"
    assert history[0]["reviews"]==[]
    model_query=client.post(f"/api/projects/{project_id}/tools/equipment_query",json={"arguments":{"query":"预热"}})
    assert model_query.json()["records"][0]["tag"]=="E-101"
