import json
import pytest
from app import agent
from app.agent import RunInput, create_run, execute_run, resume_run
from app.db import one, rows, execute

def tool_call(name,args,ident="call-1"):
    return {"role":"assistant","content":None,"tool_calls":[{"id":ident,"type":"function","function":{"name":name,"arguments":json.dumps(args)}}]}

def test_error_feedback_correction_and_trace(project_id,monkeypatch):
    monkeypatch.setenv("MODEL_BALANCED","test-model")
    responses=[tool_call("heat_exchanger",{"cold_out_C":250,"_execution":{"task_key":"area"}}),None,{"role":"assistant","content":"面积已计算；U 为假设值，待工程校核。"}]
    def completion(cfg,p,messages):
        if len(responses)==2:
            failure=json.loads(messages[-1]["content"])
            assert failure["error"] and failure["task_key"]=="area"
            responses[0]=tool_call("heat_exchanger",{"_execution":{"task_key":"area","repairs":[failure["execution_failure_id"]]}},"call-2")
        return responses.pop(0),{}
    monkeypatch.setattr(agent,"completion",completion)
    ident=create_run(project_id,RunInput(message="计算面积"))
    execute_run(ident)
    row=one("SELECT * FROM runs WHERE id=?",(ident,))
    assert row["status"]=="completed"
    state=json.loads(row["result"])
    assert state["unresolved_tools"]==[]
    records=rows("SELECT payload FROM events WHERE run_id=? AND type='tool_result'",(ident,))
    assert json.loads(records[0]["payload"])["failed"]
    assert not json.loads(records[1]["payload"])["failed"]
    failure=state["failures"][0]
    assert failure["resolved_by"]["call_id"]=="call-2"
    assert failure["resolved_by"]["calculation_id"]
    assert json.loads(records[1]["payload"])["repairs"]==[failure["id"]]


@pytest.mark.parametrize("mode",["unlinked","other_task","other_tool","unknown_id"])
def test_unrelated_success_never_closes_failure(project_id,monkeypatch,mode):
    monkeypatch.setenv("MODEL_BALANCED","test-model")
    calls=[0]
    def completion(cfg,p,messages):
        calls[0]+=1
        if calls[0]==1:
            return tool_call("heat_exchanger",{"cold_out_C":250,"_execution":{"task_key":"bad-area"}}),{}
        if calls[0]==2:
            failure=json.loads(messages[-1]["content"])["execution_failure_id"]
            metadata={"task_key":"bad-area"}
            name="heat_exchanger"
            if mode=="other_task":metadata.update(task_key="another-area",repairs=[failure])
            if mode=="other_tool":name="material_balance";metadata["repairs"]=[failure]
            if mode=="unknown_id":metadata["repairs"]=["not-an-existing-failure"]
            return tool_call(name,{"_execution":metadata},"call-2"),{}
        return {"role":"assistant","content":"保留原换热器参数错误，未完成工程校核。"},{}
    monkeypatch.setattr(agent,"completion",completion)
    ident=create_run(project_id,RunInput(message="故意错误和无关联成功的隔离测试"))
    execute_run(ident)
    record=one("SELECT * FROM runs WHERE id=?",(ident,))
    assert record["status"]=="needs_review"
    state=json.loads(record["result"])
    assert state["failures"][0]["resolved_by"] is None
    assert "heat_exchanger" in state["unresolved_tools"]


def test_question_schema_failure_can_be_explicitly_repaired(project_id,monkeypatch):
    monkeypatch.setenv("MODEL_BALANCED","test-model")
    calls=[0]
    def completion(cfg,p,messages):
        calls[0]+=1
        if calls[0]==1:return tool_call("ask_user",{"question":"确认热负荷","task_key":"misplaced"}),{}
        failed=json.loads(messages[-1]["content"])
        return tool_call("ask_user",{"question":"请确认热负荷 / kW","_execution":{"task_key":failed["task_key"],"repairs":[failed["execution_failure_id"]]}},"fixed-question"),{}
    monkeypatch.setattr(agent,"completion",completion)
    ident=create_run(project_id,RunInput(message="追问参数结构修复"))
    execute_run(ident)
    record=one("SELECT * FROM runs WHERE id=?",(ident,))
    state=json.loads(record["result"])
    assert record["status"]=="awaiting_user"
    assert state["unresolved_tools"]==[]
    assert state["failures"][0]["resolved_by"]["call_id"]=="fixed-question"
    resume_run(ident,"Q=1000 kW")
    monkeypatch.setattr(agent,"completion",lambda *args:({"role":"assistant","content":"已收到确认，追问记录完整。"},{}))
    execute_run(ident)
    assert one("SELECT status FROM runs WHERE id=?",(ident,))["status"]=="completed"

def test_question_resume_preserves_context(project_id,monkeypatch):
    monkeypatch.setenv("MODEL_BALANCED","test-model")
    monkeypatch.setattr(agent,"completion",lambda *a:(tool_call("ask_user",{"question":"请确认年产量与年操作小时。"}),{}))
    ident=create_run(project_id,RunInput(message="设计乙苯脱氢单元"))
    execute_run(ident)
    assert one("SELECT status FROM runs WHERE id=?",(ident,))["status"]=="awaiting_user"
    resume_run(ident,"产量20万吨/年，8000小时。")
    def completed(cfg,p,messages):
        assert messages[-1]["content"]=="产量20万吨/年，8000小时。"
        assert any(m.get("tool_calls") for m in messages)
        return {"role":"assistant","content":"已记录设计依据；下一步进行计算。"},{}
    monkeypatch.setattr(agent,"completion",completed)
    execute_run(ident)
    assert one("SELECT status FROM runs WHERE id=?",(ident,))["status"]=="completed"

def test_iteration_limit_and_cancellation(project_id,monkeypatch):
    monkeypatch.setenv("MODEL_BALANCED","test-model")
    monkeypatch.setenv("MAX_AGENT_ITERATIONS","1")
    monkeypatch.setattr(agent,"completion",lambda *a:(tool_call("material_balance",{}),{}))
    ident=create_run(project_id,RunInput(message="计算"))
    execute_run(ident)
    assert one("SELECT status FROM runs WHERE id=?",(ident,))["status"]=="iteration_limit"
    resume_run(ident,"继续并说明假设")
    execute("UPDATE runs SET status='cancelled' WHERE id=?",(ident,))
    execute_run(ident)
    assert one("SELECT status FROM runs WHERE id=?",(ident,))["status"]=="cancelled"
