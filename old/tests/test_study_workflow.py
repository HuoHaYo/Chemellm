"""Dependency versions, stale deliverables, checkpoints and execution limits."""
import io
import json
import zipfile

import pytest

from app import workflow
from app.db import connection, execute, now, one, rows, uid
from app.workflow import ParameterWrite, TaskWrite, WorkflowStart, AttemptResolution, save_parameter, save_task, start_execution, run_execution, execution, study_status, resume_execution, reconcile_attempt


def parameter(project_id,value=1,revision=None):
    return save_parameter(project_id,ParameterWrite(key="pressure",label="研究压力",value=value,unit="bar",
        provenance="assumption",conditions="数值工作流控制案例，非工艺设计依据",expected_revision=revision))


def task(project_id,key="pressure_pa",**kwargs):
    values=dict(key=key,title=key,tool="convert_units",arguments={"value":1,"from_unit":"bar","to_unit":"Pa"})
    values.update(kwargs)
    return save_task(project_id,TaskWrite(**values))


def make_chain(project_id):
    parameter(project_id)
    task(project_id,bindings=[{"target":"/value","kind":"parameter","key":"pressure","unit":"bar"}])
    task(project_id,"pressure_kpa",arguments={"value":1,"from_unit":"Pa","to_unit":"kPa"},
         bindings=[{"target":"/value","kind":"task","key":"pressure_pa","path":"/value","unit":"Pa"}])
    task(project_id,"report",tool="export_report",arguments={"title":"版本化数值控制案例","body":"待计算","formats":["md","pdf"]},
         bindings=[{"target":"/body","kind":"task","key":"pressure_kpa","path":"/value","render_as":"text","prefix":"控制案例压力：","suffix":" kPa；来源为假设，未经工程审核。"}])


def run(project_id,keys=["report"],**kwargs):
    item=start_execution(project_id,WorkflowStart(task_keys=keys,**kwargs))
    run_execution(item["id"])
    return execution(item["id"])


def test_dependency_binding_version_and_checkpoint_reuse(project_id):
    make_chain(project_id)
    result=run(project_id)
    assert result["status"]=="completed",result
    assert result["state"]["order"]==["pressure_pa","pressure_kpa","report"]
    status=study_status(project_id);tasks={t["key"]:t for t in status["tasks"]}
    assert tasks["pressure_kpa"]["latest_attempt"]["result"]["value"]==pytest.approx(100)
    assert tasks["pressure_pa"]["latest_attempt"]["sources"][0]["revision"]==1
    assert "100.0 kPa" in tasks["report"]["latest_attempt"]["input"]["body"]
    old_attempts=[t["latest_attempt_id"] for t in status["tasks"]]
    again=run(project_id)
    assert again["status"]=="completed" and again["state"]["tool_calls"]==0
    assert old_attempts==[t["latest_attempt_id"] for t in study_status(project_id)["tasks"]]


def test_parameter_change_invalidates_transitive_outputs_and_acceptance(client,project_id):
    make_chain(project_id);assert run(project_id)["status"]=="completed"
    report=next(t for t in study_status(project_id)["tasks"] if t["key"]=="report")
    artifact=report["latest_attempt"]["result"]["artifacts"][0]
    original=client.get(artifact["download_url"]).content
    from app.competition import seed_requirements
    seed_requirements(project_id)
    response=client.put(f"/api/projects/{project_id}/requirements/D01",json={"status":"verified","evidence":[artifact["id"]],"notes":"这是控制案例的人工接口验证记录，不作真实工程审核。"})
    assert response.status_code==200,response.text
    changed=parameter(project_id,2,1)
    assert set(changed["invalidated_tasks"])=={"pressure_pa","pressure_kpa","report"}
    assert all(t["status"]=="stale" for t in study_status(project_id)["tasks"])
    record=one("SELECT status FROM requirements WHERE project_id=? AND code='D01'",(project_id,))
    assert record["status"]=="draft"
    assert one("SELECT COUNT(*) AS n FROM study_review_invalidations WHERE project_id=?",(project_id,))["n"]==1
    assert client.get(artifact["download_url"]).content==original
    meta=json.loads(one("SELECT metadata FROM artifacts WHERE id=?",(artifact["id"],))["metadata"])
    assert meta["workflow_freshness"]=="stale"
    response=client.put(f"/api/projects/{project_id}/requirements/D01",json={"status":"verified","evidence":[artifact["id"]],"notes":"尝试使用旧版本重新审核，系统应拒绝。"})
    assert response.status_code==422
    assert run(project_id)["status"]=="completed"
    report=next(t for t in study_status(project_id)["tasks"] if t["key"]=="report")
    assert "200.0 kPa" in report["latest_attempt"]["input"]["body"]
    assert report["latest_attempt"]["result"]["artifacts"][0]["id"]!=artifact["id"]
    assert one("SELECT COUNT(*) AS n FROM study_attempts WHERE task_id=?",(report["id"],))["n"]==2


def test_parameter_unit_conversion_and_versions(project_id):
    parameter(project_id)
    task(project_id,bindings=[{"target":"/value","kind":"parameter","key":"pressure","unit":"Pa"}],
         arguments={"value":1,"from_unit":"Pa","to_unit":"kPa"})
    assert run(project_id,["pressure_pa"])["status"]=="completed"
    assert study_status(project_id)["tasks"][0]["latest_attempt"]["input"]["value"]==100000
    with pytest.raises(ValueError,match="版本"):parameter(project_id,2)
    with pytest.raises(ValueError):save_parameter(project_id,ParameterWrite(key="bad",label="bad",value=1,unit="invalid_unit_xyz",conditions="test"))
    with pytest.raises(ValueError):save_parameter(project_id,ParameterWrite(key="bad",label="bad",value=1,unit="Pa",conditions="test",provenance="experimental"))


def test_cycles_missing_dependency_and_cross_project_rejected(project_id):
    task(project_id,"a")
    task(project_id,"b",depends_on=["a"])
    with pytest.raises(ValueError,match="环"):task(project_id,"a",depends_on=["b"],expected_revision=1)
    with pytest.raises(ValueError,match="不存在"):task(project_id,"c",depends_on=["unknown"])
    another=uid();execute("INSERT INTO projects VALUES(?,?,?)",(another,"another",now()))
    parameter(another)
    with pytest.raises(ValueError,match="参数不存在"):
        task(project_id,"c",bindings=[{"target":"/value","kind":"parameter","key":"pressure"}])
    assert one("SELECT revision FROM study_tasks WHERE project_id=? AND key='a'",(project_id,))["revision"]==1


def test_changed_during_execution_is_not_current(project_id,monkeypatch):
    parameter(project_id)
    task(project_id,bindings=[{"target":"/value","kind":"parameter","key":"pressure"}])
    from app import toolbox
    original=toolbox.run_tool
    def changing(*args):
        parameter(project_id,2,1)
        return original(*args)
    monkeypatch.setattr(toolbox,"run_tool",changing)
    result=run(project_id,["pressure_pa"])
    assert result["status"]=="blocked"
    status=study_status(project_id)["tasks"][0]
    assert status["status"]=="stale" and status["latest_attempt"]["status"]=="stale"


def test_tool_budget_is_cumulative_and_requires_new_run(project_id):
    make_chain(project_id)
    result=run(project_id,max_tools=1)
    assert result["status"]=="budget_exhausted" and result["state"]["tool_calls"]==1
    assert study_status(project_id)["tasks"][0]["status"]=="succeeded"
    with pytest.raises(ValueError,match="预算"):resume_execution(result["id"])
    next_run=run(project_id)
    assert next_run["status"]=="completed" and next_run["state"]["tool_calls"]==2


def test_time_budget_prevents_another_tool(project_id,monkeypatch):
    task(project_id,"a");task(project_id,"b",depends_on=["a"])
    from app import toolbox
    original=toolbox.run_tool;clock=[0.]
    monkeypatch.setattr(workflow.time,"monotonic",lambda:clock[0])
    def slow(*args):
        result=original(*args);clock[0]+=2;return result
    monkeypatch.setattr(toolbox,"run_tool",slow)
    result=run(project_id,["b"],max_seconds=1)
    assert result["status"]=="budget_exhausted" and result["state"]["tool_calls"]==1


def test_cancel_inflight_keeps_unapproved_result_and_blocks_overlap(project_id,monkeypatch):
    task(project_id,"a")
    item=start_execution(project_id,WorkflowStart(task_keys=["a"]))
    from app import toolbox
    original=toolbox.run_tool
    def cancel(*args):
        workflow.cancel_execution(item["id"])
        with pytest.raises(ValueError,match="取消"):start_execution(project_id,WorkflowStart(task_keys=["a"]))
        with pytest.raises(ValueError,match="取消"):resume_execution(item["id"])
        return original(*args)
    monkeypatch.setattr(toolbox,"run_tool",cancel)
    run_execution(item["id"])
    assert execution(item["id"])["status"]=="cancelled"
    assert study_status(project_id)["tasks"][0]["latest_attempt"]["calculation_id"]
    assert study_status(project_id)["tasks"][0]["status"]=="cancelled"


def test_restart_recovery_preserves_completed_checkpoint(project_id):
    task(project_id,"a");task(project_id,"b",depends_on=["a"])
    assert run(project_id,["a"])["status"]=="completed"
    old=study_status(project_id)["tasks"][0]["latest_attempt_id"]
    item=start_execution(project_id,WorkflowStart(task_keys=["b"]))
    execute("UPDATE study_executions SET status='running' WHERE id=?",(item["id"],))
    workflow.recover_interrupted()
    assert execution(item["id"])["status"]=="interrupted"
    resume_execution(item["id"]);run_execution(item["id"])
    assert execution(item["id"])["status"]=="completed"
    assert study_status(project_id)["tasks"][0]["latest_attempt_id"]==old


def test_failure_is_task_specific_and_export_keeps_history(client,project_id):
    task(project_id,"bad",tool="heat_exchanger",arguments={"cold_out_C":250})
    task(project_id,"good",tool="heat_exchanger",arguments={})
    assert run(project_id,["bad"])["status"]=="failed"
    assert run(project_id,["good"])["status"]=="completed"
    records={t["key"]:t for t in study_status(project_id)["tasks"]}
    assert records["bad"]["status"]=="failed" and records["good"]["status"]=="succeeded"
    bundle=client.post(f"/api/projects/{project_id}/bundle").json()
    with zipfile.ZipFile(io.BytesIO(client.get(bundle["download_url"]).content)) as archive:
        manifest=json.loads(archive.read("manifest.json"))
    study=manifest["study_workflow"]
    assert len(study["study_attempts"])==2 and study["events"]
    assert {r["status"] for r in study["study_attempts"]}=={"failed","succeeded"}


def test_http_registration_dispatch_and_details(client,project_id,monkeypatch):
    import app.main as main
    monkeypatch.setattr(main,"dispatch_execution",run_execution)
    response=client.post(f"/api/projects/{project_id}/study/tasks",json={"key":"a","title":"压力换算","tool":"convert_units","arguments":{"value":2,"from_unit":"bar","to_unit":"Pa"}})
    assert response.status_code==200,response.text
    result=client.post(f"/api/projects/{project_id}/study/executions",json={"task_keys":["a"]})
    assert result.status_code==200,result.text
    ident=result.json()["id"]
    details=client.get("/api/study-executions/"+ident).json()
    assert details["status"]=="completed" and details["events"]
    assert client.get(f"/api/projects/{project_id}/study").json()["tasks"][0]["latest_attempt"]["result"]["value"]==200000


def interrupted_call(project_id,key,produce_result=False):
    """Persist the actual pre-call checkpoint, then emulate loss of the worker."""
    from app.toolbox import run_tool
    item=start_execution(project_id,WorkflowStart(task_keys=[key]))
    with connection() as db:
        record=db.execute("SELECT * FROM study_tasks WHERE project_id=? AND key=?",(project_id,key)).fetchone()
        arguments,sources=workflow.resolve(db,project_id,record)
        attempt_id=uid()
        db.execute("INSERT INTO study_attempts VALUES(?,?,?,?,?,?,?,?,?,?,?,?)",(attempt_id,record["id"],item["id"],record["revision"],workflow.encoded(arguments),workflow.encoded(sources),"running",None,"{}","",now(),None))
        db.execute("UPDATE study_tasks SET status='running',latest_attempt_id=? WHERE id=?",(attempt_id,record["id"]))
        state={**item["state"],"tool_calls":1}
        db.execute("UPDATE study_executions SET status='running',state=? WHERE id=?",(workflow.encoded(state),item["id"]))
    result=run_tool(project_id,json.loads(record["config"])["tool"],arguments) if produce_result else None
    workflow.recover_interrupted()
    return item["id"],attempt_id,result


def test_unknown_outcome_blocks_replay_until_explicit_retry(project_id):
    task(project_id,"a")
    ident,attempt_id,_=interrupted_call(project_id,"a")
    with pytest.raises(ValueError,match="未知"):resume_execution(ident)
    with pytest.raises(ValueError,match="未知"):start_execution(project_id,WorkflowStart(task_keys=["a"]))
    # Changing the definition does not erase the uncertain side effect.
    task(project_id,"a",expected_revision=1)
    with pytest.raises(ValueError,match="未知"):start_execution(project_id,WorkflowStart(task_keys=["a"]))
    assert not rows("SELECT id FROM calculations WHERE project_id=?",(project_id,))
    reconcile_attempt(attempt_id,AttemptResolution(decision="retry",reviewer="自动测试",notes="模拟核对后明确允许重试，非真实工程审核。"))
    resume_execution(ident);run_execution(ident)
    assert execution(ident)["status"]=="completed"
    assert execution(ident)["state"]["tool_calls"]==2
    assert one("SELECT status FROM study_attempts WHERE id=?",(attempt_id,))["status"]=="retry_approved"
    assert len(rows("SELECT id FROM calculations WHERE project_id=?",(project_id,)))==1
    assert not study_status(project_id)["uncertain_attempts"]


def test_adopt_existing_return_without_repeating_report(client,project_id):
    task(project_id,"report",tool="export_report",arguments={"title":"中断成果核对测试","body":"仅检查中断后的文件关联和重放规则。","formats":["md"]})
    ident,attempt_id,result=interrupted_call(project_id,"report",produce_result=True)
    calculation_id=result["calculation_id"];artifact=result["artifacts"][0]
    content=client.get(artifact["download_url"]).content
    response=client.post(f"/api/study-attempts/{attempt_id}/reconcile",json={"decision":"adopt","calculation_id":calculation_id,"reviewer":"自动测试","notes":"核对测试生成文件与实际调用输入，采用已有记录以避免重复生成。"})
    assert response.status_code==200,response.text
    resume_execution(ident);run_execution(ident)
    assert execution(ident)["status"]=="completed"
    assert execution(ident)["state"]["tool_calls"]==1
    assert len(rows("SELECT id FROM calculations WHERE project_id=?",(project_id,)))==1
    current=study_status(project_id)["tasks"][0]
    assert current["latest_attempt_id"]==attempt_id and current["latest_attempt"]["calculation_id"]==calculation_id
    assert client.get(artifact["download_url"]).content==content
    meta=json.loads(one("SELECT metadata FROM artifacts WHERE id=?",(artifact["id"],))["metadata"])
    assert meta["workflow_freshness"]=="current" and meta["workflow_attempt_id"]==attempt_id
    assert client.post(f"/api/study-attempts/{attempt_id}/reconcile",json={"decision":"retry","reviewer":"自动测试","notes":"重复处置必须被拒绝，保留原始确认记录。"}).status_code==422
    events=execution(ident)["events"]
    assert [e["type"] for e in events].count("attempt_reconciled")==1
    assert any(e["type"]=="task_interrupted" for e in events)


@pytest.mark.parametrize("mode",["changed_inputs","changed_source","foreign_project","wrong_tool","wrong_input"])
def test_adoption_rejects_unrelated_or_stale_record(project_id,mode):
    from app.toolbox import run_tool
    parameter(project_id)
    task(project_id,"a",bindings=[{"target":"/value","kind":"parameter","key":"pressure"}])
    _,attempt_id,result=interrupted_call(project_id,"a",produce_result=True)
    if mode=="changed_inputs":task(project_id,"a",expected_revision=1)
    if mode=="changed_source":parameter(project_id,2,1)
    if mode=="foreign_project":
        other=uid();execute("INSERT INTO projects VALUES(?,?,?)",(other,"其他项目",now()))
        result=run_tool(other,"convert_units",{"value":1,"from_unit":"bar","to_unit":"Pa"})
    if mode=="wrong_tool":result=run_tool(project_id,"material_balance",{})
    if mode=="wrong_input":result=run_tool(project_id,"convert_units",{"value":3,"from_unit":"bar","to_unit":"Pa"})
    with pytest.raises(ValueError):
        reconcile_attempt(attempt_id,AttemptResolution(decision="adopt",calculation_id=result["calculation_id"],reviewer="自动测试",notes="不匹配或过期结果不能变为当前结果。"))
    assert one("SELECT status FROM study_attempts WHERE id=?",(attempt_id,))["status"]=="interrupted"
    assert not rows("SELECT id FROM study_events WHERE project_id=? AND type='attempt_reconciled'",(project_id,))
