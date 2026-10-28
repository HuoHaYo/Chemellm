"""Crash-window controls, preserving real calculation/artifact effects and batches."""
import json
from pathlib import Path
import pytest
from app import agent, toolbox
from app.agent import RunInput, create_run, execute_run, resume_run
from app.db import execute, one, rows, uid, now
from app.run_recovery import CallResolution, recover_runs, reconcile_call, unknown_calls


class ProcessLoss(BaseException):
    pass


def state(ident):
    return json.loads(one('SELECT result FROM runs WHERE id=?',(ident,))['result'])


def test_long_tool_message_is_valid_compact_json_without_value_truncation():
    from app.run_recovery import tool_message
    long_result={'calculation_id':'calc-large','tool':'material_balance','status':'computed',
                 'streams':[{'name':'S'+str(i),'components':{'A':i,'B':i+1}} for i in range(5000)],
                 'warnings':['check mass closure']}
    state_data={'messages':[],'pending_calls':[{'id':'c-large'}]}
    tool_message(state_data,'c-large',long_result)
    message=state_data['messages'][0]
    payload=json.loads(message['content'])
    assert payload['calculation_id']=='calc-large' and payload['tool']=='material_balance'
    assert payload['result_outline']['streams']=={'type':'list','items':5000}
    assert payload['warnings']==['check mass closure']
    assert 'excerpt' not in payload and 'streams' not in payload
    assert not state_data['pending_calls']


def response():
    calls=[]
    for call_id,name,args in [
        ('checkpoint','convert_units',{'value':1,'from_unit':'bar','to_unit':'Pa'}),
        ('report','export_report',{'title':'Crash QA report','body':'100 kPa, numerical control only','formats':['md']}),
        ('sibling','convert_units',{'value':100000,'from_unit':'Pa','to_unit':'kPa'})]:
        calls.append({'id':call_id,'type':'function','function':{'name':name,'arguments':json.dumps(args)}})
    return {'role':'assistant','content':None,'tool_calls':calls}


def crash(project_id,monkeypatch,phase='after',max_tools=10,cancel=False):
    monkeypatch.setenv('MODEL_BALANCED','test-model')
    monkeypatch.setattr(agent,'completion',lambda *args:(response(),{}))
    ident=create_run(project_id,RunInput(message='crash-window QA',max_tools=max_tools))
    def gated(project,name,args):
        saved=state(ident)
        current=saved['tool_attempts'][-1]
        assert current['status']=='running' and current['tool']==name
        assert any(m.get('tool_calls') for m in saved['messages'])
        if name=='export_report':
            assert saved['tool_calls']==2
            assert [c['id'] for c in saved['pending_calls']]==['report','sibling']
            assert saved['tool_attempts'][0]['status']=='succeeded'
            if cancel:execute("UPDATE runs SET status='cancelled' WHERE id=?",(ident,))
            if phase=='after':toolbox.run_tool(project,name,args)
            raise ProcessLoss()
        return toolbox.run_tool(project,name,args)
    monkeypatch.setattr(agent,'run_tool',gated)
    with pytest.raises(ProcessLoss):execute_run(ident)
    recover_runs()
    return ident


@pytest.mark.parametrize('phase',['before','after'])
def test_unknown_blocks_new_run_and_resume_then_keeps_batch(project_id,monkeypatch,phase):
    ident=crash(project_id,monkeypatch,phase)
    pending=unknown_calls(ident)
    assert len(pending)==1 and pending[0]['call_id']=='report'
    with pytest.raises(ValueError,match='未知'):resume_run(ident,'')
    with pytest.raises(ValueError,match='未知'):create_run(project_id,RunInput(message='cannot bypass'))
    attempt=pending[0]
    if phase=='after':
        record=next(c for c in attempt['candidate_calculations'] if c['tool']=='export_report')
        artifact=record['result']['artifacts'][0]
        original=Path(one('SELECT path FROM artifacts WHERE id=?',(artifact['id'],))['path']).read_bytes()
        decision=CallResolution(decision='adopt',calculation_id=record['id'],reviewer='QA operator',notes='Checked real persisted report bytes and input. Execution disposition only.')
    else:decision=CallResolution(decision='retry',reviewer='QA operator',notes='Confirmed gated backend had not run; explicitly allow another attempt.')
    reconcile_call(ident,attempt['id'],decision)
    with pytest.raises(ValueError,match='已处理'):reconcile_call(ident,attempt['id'],decision)
    resume_run(ident,'继续保留已完成的换算')
    called=[]
    def backend(project,name,args):
        called.append(name)
        return toolbox.run_tool(project,name,args)
    monkeypatch.setattr(agent,'run_tool',backend)
    def done(cfg,p,messages):
        assert messages[-1]['role']=='user'
        assert '执行恢复记录' in messages[0]['content']
        assert '"decision": "'+decision.decision+'"' in messages[0]['content']
        assert '"cumulative_tool_calls": '+str(3 if phase=='after' else 4) in messages[0]['content']
        ids=[m['tool_call_id'] for m in messages if m['role']=='tool']
        assert ids==['checkpoint','report','sibling']
        assert all(json.loads(m['content']).get('status')!='not_executed' for m in messages if m['role']=='tool')
        report=next(json.loads(m['content']) for m in messages if m.get('tool_call_id')=='report')
        assert report['execution_reconciliation']['decision']==decision.decision
        return {'role':'assistant','content':'控制任务结束；未进行工程审核。'},{}
    monkeypatch.setattr(agent,'completion',done)
    execute_run(ident)
    final=state(ident)
    assert one('SELECT status FROM runs WHERE id=?',(ident,))['status']=='completed'
    assert called==(['convert_units'] if phase=='after' else ['export_report','convert_units'])
    assert final['tool_calls']==(3 if phase=='after' else 4)
    assert not final['pending_calls'] and not unknown_calls(ident)
    assert final['tool_attempts'][1]['resolution']['decision']==decision.decision
    if phase=='after':
        assert Path(one('SELECT path FROM artifacts WHERE id=?',(artifact['id'],))['path']).read_bytes()==original
        assert len(rows("SELECT id FROM calculations WHERE project_id=? AND tool='export_report'",(project_id,)))==1
    before=state(ident)
    execute_run(ident)  # Terminal runs cannot be dispatched a second time.
    assert state(ident)==before


@pytest.mark.parametrize('mode',['wrong_input','wrong_tool','foreign_project','before_attempt','failed_result','missing_file'])
def test_adoption_rejects_unrelated_or_missing_record(project_id,monkeypatch,mode):
    ident=crash(project_id,monkeypatch)
    attempt=unknown_calls(ident)[0]
    candidate=attempt['candidate_calculations'][0]
    name='export_report';args=attempt['input'];project=project_id
    if mode=='wrong_input':args={**args,'body':'different report'}
    if mode=='wrong_tool':name='convert_units';args={'value':1,'from_unit':'bar','to_unit':'Pa'}
    if mode=='foreign_project':
        project=uid();execute('INSERT INTO projects VALUES(?,?,?)',(project,'other',now()))
    if mode in {'wrong_input','wrong_tool','foreign_project'}:
        candidate=toolbox.run_tool(project,name,args)
        candidate['id']=candidate['calculation_id']
    if mode=='before_attempt':execute('UPDATE calculations SET created_at=? WHERE id=?',('2000-01-01T00:00:00+00:00',candidate['id']))
    if mode=='failed_result':execute('UPDATE calculations SET result=? WHERE id=?',(json.dumps({'status':'unavailable'}),candidate['id']))
    if mode=='missing_file':
        artifact=candidate['result']['artifacts'][0]
        Path(one('SELECT path FROM artifacts WHERE id=?',(artifact['id'],))['path']).unlink()
    with pytest.raises(ValueError):
        reconcile_call(ident,attempt['id'],CallResolution(decision='adopt',calculation_id=candidate['id'],reviewer='QA operator',notes='Negative adoption case, must be rejected.'))
    assert unknown_calls(ident)[0]['status']=='unknown'


def test_retry_keeps_spent_budget_and_cancelled_inflight_is_unknown(project_id,monkeypatch):
    ident=crash(project_id,monkeypatch,'before',max_tools=2,cancel=True)
    assert one('SELECT status FROM runs WHERE id=?',(ident,))['status']=='interrupted'
    attempt=unknown_calls(ident)[0]
    reconcile_call(ident,attempt['id'],CallResolution(decision='retry',reviewer='QA operator',notes='Explicitly authorize retry while retaining previously spent budget.'))
    resume_run(ident,'')
    monkeypatch.setattr(agent,'run_tool',lambda *a:pytest.fail('Budget must stop retry'))
    monkeypatch.setattr(agent,'completion',lambda *a:pytest.fail('Budget must stop model'))
    execute_run(ident)
    assert one('SELECT status FROM runs WHERE id=?',(ident,))['status']=='budget_exhausted'
    assert state(ident)['tool_calls']==2
    assert all(json.loads(m['content'])['status']=='not_executed' for m in state(ident)['messages'] if m.get('tool_call_id') in {'report','sibling'})


def test_mutating_tool_exception_requires_disposition(project_id,monkeypatch):
    monkeypatch.setenv('MODEL_BALANCED','test-model')
    batch=response();batch['tool_calls']=batch['tool_calls'][1:2]
    monkeypatch.setattr(agent,'completion',lambda *a:(batch,{}))
    def partial(*args):raise OSError('disk write acknowledgement lost')
    monkeypatch.setattr(toolbox,'export_report',partial)
    ident=create_run(project_id,RunInput(message='partial write QA'))
    execute_run(ident)
    assert one('SELECT status FROM runs WHERE id=?',(ident,))['status']=='interrupted'
    assert unknown_calls(ident)[0]['call_id']=='report'
    with pytest.raises(ValueError,match='未知'):resume_run(ident,'')


def test_legacy_lost_response_is_recovered_conservatively(project_id,monkeypatch):
    monkeypatch.setenv('MODEL_BALANCED','test-model')
    ident=create_run(project_id,RunInput(message='legacy control'))
    old={'messages':[{'role':'system','content':agent.SYSTEM},{'role':'user','content':'legacy control'}],
         'failures':[],'unresolved_tools':[],'tool_calls':1,'iterations':1,'active_seconds':1.}
    execute("UPDATE runs SET status='running',result=? WHERE id=?",(json.dumps(old),ident))
    execute('INSERT INTO events(run_id,type,payload,created_at) VALUES(?,?,?,?)',
            (ident,'tool_start',json.dumps({'name':'convert_units','arguments':{'value':1,'from_unit':'bar','to_unit':'Pa'}}),now()))
    recover_runs()
    attempt=unknown_calls(ident)[0]
    assert attempt['legacy'] and attempt['input']['from_unit']=='bar'
    assert state(ident)['pending_calls'][0]['id']==attempt['call_id']
    with pytest.raises(ValueError,match='未知'):resume_run(ident,'')
    elapsed=state(ident)['active_seconds'];recover_runs()
    assert state(ident)['active_seconds']==elapsed


def test_recovery_http_and_auth_contract(client,project_id,monkeypatch):
    ident=crash(project_id,monkeypatch,'after')
    data=client.get('/api/runs/'+ident).json()
    attempt=data['unknown_calls'][0]
    assert 'messages' not in data['result']
    assert client.post('/api/runs/'+ident+'/resume',json={}).status_code==422
    url='/api/runs/'+ident+'/tool-attempts/'+attempt['id']+'/reconcile'
    assert client.post(url,json={'decision':'retry','reviewer':'','notes':'short'}).status_code==422
    assert client.post(url,json={'decision':'retry','reviewer':'QA operator','notes':'Explicit execution disposition confirmed through HTTP.'}).status_code==200
    monkeypatch.setattr(agent,'run_tool',toolbox.run_tool)
    monkeypatch.setattr(agent,'completion',lambda *a:({'role':'assistant','content':'QA completed'},{}))
    from app import main
    monkeypatch.setattr(main,'dispatch',execute_run)
    assert client.post('/api/runs/'+ident+'/resume',json={}).status_code==200
    assert client.get('/api/runs/'+ident).json()['status']=='completed'
