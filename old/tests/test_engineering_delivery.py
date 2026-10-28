import json
import zipfile
from pathlib import Path
import pytest

from app import agent
from app.db import execute, one, rows, uid, now
from app.competition import seed_requirements
from app.engineering import (ObjectWrite, DeliverableWrite, EngineeringQuery, EngineeringPlan,
    RequirementBatch, RequirementSource, save_object, save_deliverable, save_plan, save_requirements,
    engineering_status, engineering_phase, engineering_tool_policy)
from app.toolbox import run_tool, definitions
from app.documents import ingest


def object_input(key='basis', **extra):
    return ObjectWrite(key=key, kind='basis', title='设计依据', **extra)


def delivery_input(**extra):
    return DeliverableWrite(key='report',title='设计依据说明',requirement_codes=['B01'],
                            formats=['docx','pdf'],acceptance_criteria='原件可读，数据与统一工程依据一致',**extra)


def test_calculated_values_require_actual_same_project_result_and_units(project_id):
    result=run_tool(project_id,'convert_units',{'value':1,'from_unit':'bar','to_unit':'Pa'})
    q=dict(key='pressure',value=100,unit='kPa',origin='calculation',conditions='绝压，工具控制例',
           rationale='转换计算结果',calculation_id=result['calculation_id'],result_path='/value',result_unit='Pa')
    saved=save_object(project_id,object_input(quantities=[q]))
    assert saved['data']['quantities'][0]['base_value']==pytest.approx(100000)
    with pytest.raises(ValueError,match='不一致'):
        save_object(project_id,object_input('bad',quantities=[{**q,'value':101}]))
    with pytest.raises(ValueError,match='计算结果引用错误'):
        save_object(project_id,object_input('bad',quantities=[{**q,'result_unit':'kg'}]))
    with pytest.raises(ValueError,match='计算结果引用错误'):
        save_object(project_id,object_input('bad',quantities=[{**q,'result_path':'/absent'}]))
    with pytest.raises(ValueError,match='文档数值|快照引用'):
        ObjectWrite(key='bad-snapshot',kind='basis',title='bad',quantities=[{
            'key':'x','value':1,'unit':'kPa','origin':'document','conditions':'test','rationale':'test',
            'snapshot_id':'snapshot-only'}])
    other=uid()
    execute('INSERT INTO projects VALUES(?,?,?)',(other,'另一个工程',now()))
    with pytest.raises(ValueError,match='不属于当前项目'):
        save_object(other,object_input(quantities=[q]))


def test_transitive_revision_and_file_invalidation(project_id):
    seed_requirements(project_id)
    save_object(project_id,object_input())
    save_object(project_id,object_input('stream',depends_on=['basis']))
    save_object(project_id,object_input('equipment',depends_on=['stream']))
    generated=run_tool(project_id,'export_report',{'title':'有内容的依据说明','body':'原料规格与资源调查的实际记录。','formats':['docx','pdf']})
    save_deliverable(project_id,delivery_input(object_keys=['equipment'],files=[{'artifact_id':r['id'],'location':'正文第一段'} for r in generated['artifacts']]))
    status=engineering_status(project_id)
    assert status['deliverables'][0]['files_checked']
    save_object(project_id,object_input(expected_revision=1))
    status=engineering_status(project_id)
    assert not next(r for r in status['objects'] if r['key']=='equipment')['fresh']
    assert not status['deliverables'][0]['files_checked']
    assert len(rows('SELECT * FROM engineering_object_revisions WHERE project_id=? AND key=?',(project_id,'basis')))==2
    with pytest.raises(ValueError,match='版本冲突'):
        save_object(project_id,object_input())
    with pytest.raises(ValueError,match='循环'):
        save_object(project_id,object_input(depends_on=['equipment'],expected_revision=2))


def test_document_source_page_and_original_hash(project_id):
    from app.documents import export_report
    item=export_report(project_id,'原始条件','已知边界条件为定压工况',['pdf'])['artifacts'][0]
    # Use ingestion to establish page locators, as a real uploaded source would.
    source=ingest(project_id,'source.pdf',Path(one('SELECT path FROM artifacts WHERE id=?',(item['id'],))['path']).read_bytes())
    q=dict(key='pressure',value=100,unit='kPa',origin='document',conditions='压力条件',
           rationale='所给文档数值；匹配原件不代表科学校核',artifact_id=source['id'],page=1)
    save_object(project_id,object_input(quantities=[q]))
    with pytest.raises(ValueError,match='页码不可验证'):
        save_object(project_id,object_input('bad',quantities=[{**q,'page':2}]))
    path=Path(one('SELECT path FROM artifacts WHERE id=?',(source['id'],))['path'])
    path.write_bytes(path.read_bytes()+b'\nchanged')
    assert not engineering_status(project_id)['objects'][0]['fresh']


def test_page_less_snapshot_quantity_and_source_bound_requirement(project_id):
    from app.fulltext import extract_document, ExtractInput
    source=ingest(project_id,'source.html',b'<html><body><h1>Basis</h1><p>Operating temperature is 120 C for this case.</p></body></html>')
    snapshot=extract_document(project_id,ExtractInput(artifact_id=source['id']))
    from app.db import execute
    execute('INSERT INTO requirements(id,project_id,code,title,page,mandatory) VALUES(?,?,?,?,?,?)',
            (uid(),project_id,'B01','原料和操作依据',None,1))
    assert engineering_phase(project_id)['stage']=='requirements'
    assert 'engineering_requirements' in engineering_tool_policy(project_id)[1]
    assert 'convert_units' not in {item['function']['name'] for item in definitions(engineering_tool_policy(project_id)[1])}
    requirement=RequirementSource(code='B01',title='原料和操作依据',mandatory=True,applicability='适用于本设计工况',
        snapshot_id=snapshot['snapshot_id'],block_id='b00002',quote='Operating temperature is 120 C')
    bound=save_requirements(project_id,RequirementBatch(requirements=[requirement]))
    assert bound['source_bound']==['B01'] and bound['added']==[]
    assert engineering_phase(project_id)['stage']=='plan'
    with pytest.raises(ValueError,match='不允许模型覆盖'):
        save_requirements(project_id,RequirementBatch(requirements=[requirement.model_copy(update={'quote':'120 C for this case'})]))
    q=dict(key='temperature',value=120,unit='degC',origin='document',conditions='该操作工况',
           rationale='来自无页码HTML快照；精确引句可复查',snapshot_id=snapshot['snapshot_id'],
           block_id='b00002',quote='Operating temperature is 120 C')
    saved=save_object(project_id,object_input(quantities=[q]))
    stored=saved['data']['quantities'][0]
    assert stored['value']==120
    assert stored['source_snapshot_id']==snapshot['snapshot_id']
    assert stored['source_locator']['page'] is None
    assert stored['source_quote']==q['quote']
    assert not any('快照' in issue for issue in next(r for r in engineering_status(project_id)['objects'] if r['key']=='basis')['issues'])
    source_path=one('SELECT path FROM artifacts WHERE id=?',(source['id'],))['path']
    Path(source_path).write_bytes(Path(source_path).read_bytes()+b'changed')
    assert any('快照不可用' in issue or '来源文件' in issue for issue in
               next(r for r in engineering_status(project_id)['objects'] if r['key']=='basis')['issues'])


def test_plan_batch_is_atomic_and_pins_topological_revisions(project_id):
    execute('INSERT INTO requirements(id,project_id,code,title,page,mandatory) VALUES(?,?,?,?,?,?)',
            (uid(),project_id,'B01','设计依据',None,1))
    parent=object_input('root')
    child=object_input('child',depends_on=['root'])
    plan=EngineeringPlan(objects=[child,parent],deliverables=[DeliverableWrite(
        key='basis-note',title='依据记录',requirement_codes=['B01'],object_keys=['child'],formats=['md'],
        acceptance_criteria='引用根依据与派生依据')])
    result=save_plan(project_id,plan)
    assert result['objects']==[{'key':'root','revision':1},{'key':'child','revision':1}]
    saved=next(r for r in engineering_status(project_id)['objects'] if r['key']=='child')
    assert saved['data']['object_revisions']==[{'key':'root','revision':1}]
    assert result['deliverables']==[{'key':'basis-note','revision':1}]
    with pytest.raises(ValueError,match='不存在的要求'):
        save_plan(project_id,EngineeringPlan(objects=[object_input('rollback')],deliverables=[DeliverableWrite(
            key='bad-plan',title='不合法成果',requirement_codes=['NO_SUCH'],formats=['md'],acceptance_criteria='原子回滚')]))
    assert not any(r['key']=='rollback' for r in engineering_status(project_id)['objects'])


def test_stale_tool_batch_cannot_cross_requirement_phase(project_id,monkeypatch):
    monkeypatch.setenv('MODEL_BALANCED','deepseek-flash')
    from app.fulltext import extract_document, ExtractInput
    source=ingest(project_id,'brief.txt',b'B01 evidence: Raw material specification and operating limits.')
    snapshot=extract_document(project_id,ExtractInput(artifact_id=source['id']))
    execute('INSERT INTO requirements(id,project_id,code,title,page,mandatory) VALUES(?,?,?,?,?,?)',
            (uid(),project_id,'B01','原料规格与操作限制',None,1))
    calls=[
        {'id':'bind','type':'function','function':{'name':'engineering_requirements','arguments':json.dumps({'requirements':[
            {'code':'B01','title':'原料规格与操作限制','mandatory':True,'applicability':'本任务设计边界',
             'snapshot_id':snapshot['snapshot_id'],'block_id':'b00001','quote':'Raw material specification'}
        ]})}},
        {'id':'stale','type':'function','function':{'name':'convert_units','arguments':json.dumps({'value':1,'from_unit':'bar','to_unit':'Pa'})}},
    ]
    monkeypatch.setattr(agent,'completion',lambda *args:({'role':'assistant','content':None,'tool_calls':calls},{}))
    run=agent.create_run(project_id,agent.RunInput(message='读取原文要求并规划工程',mode='engineering',max_model_requests=1))
    agent.execute_run(run)
    state=json.loads(one('SELECT result FROM runs WHERE id=?',(run,))['result'])
    assert one('SELECT status FROM runs WHERE id=?',(run,))['status']=='budget_exhausted'
    assert len(rows('SELECT * FROM engineering_requirement_sources WHERE project_id=?',(project_id,)))==1
    stale=next(a for a in state['tool_attempts'] if a['call_id']=='stale')
    assert stale['status']=='failed'
    assert '工程阶段为plan' in state['failures'][0]['error']
    assert not rows("SELECT id FROM calculations WHERE project_id=? AND tool='convert_units'",(project_id,))


def test_general_engineering_brief_is_frozen_and_source_bound_without_fake_page(project_id,monkeypatch):
    monkeypatch.setenv('MODEL_BALANCED','deepseek-flash')
    request='请为 500 kg/h 异丙醇回收单元比较精馏与膜分离，交付带成本估算的设计说明。'
    call={'id':'brief-requirement','type':'function','function':{'name':'engineering_requirements','arguments':json.dumps({'requirements':[
        {'code':'R01','title':'分离路线比选','mandatory':True,'applicability':'异丙醇回收单元的本轮规模与交付要求',
         'source_kind':'user_request','quote':'比较精馏与膜分离'}
    ]})}}
    monkeypatch.setattr(agent,'completion',lambda *args:({'role':'assistant','content':None,'tool_calls':[call]},{}))
    run=agent.create_run(project_id,agent.RunInput(message=request,mode='engineering',max_model_requests=1))
    assert engineering_phase(project_id)['stage']=='requirements'
    policy=engineering_tool_policy(project_id)[1]
    assert 'engineering_requirements' in policy and 'export_report' not in policy
    agent.execute_run(run)
    source=json.loads(one('SELECT data FROM engineering_requirement_sources WHERE project_id=? AND code=?',(project_id,'R01'))['data'])
    assert source['source_run_id']==run and source['source_kind']=='user_request'
    assert source['source_sha256'] and source['locator']=={'page':None,'section':'user request','paragraph':None}
    assert engineering_phase(project_id)['stage']=='plan'
    assert 'R01' in {r['code'] for r in engineering_status(project_id)['requirements']}
    execute('UPDATE runs SET request=? WHERE id=?',(json.dumps({**json.loads(one('SELECT request FROM runs WHERE id=?',(run,))['request']),'message':'different input'}),run))
    assert any(b['kind']=='requirement_source' and b['key']=='R01' for b in engineering_status(project_id)['blockers'])


def test_engineering_plan_cannot_skip_requirements_stage(project_id,monkeypatch):
    monkeypatch.setenv('MODEL_BALANCED','deepseek-flash')
    call={'id':'premature-plan','type':'function','function':{'name':'engineering_plan','arguments':json.dumps({
        'deliverables':[{'key':'report','title':'Premature report','requirement_codes':['R01'],'formats':['md'],
                        'acceptance_criteria':'must be gated'}]})}}
    monkeypatch.setattr(agent,'completion',lambda *args:({'role':'assistant','content':None,'tool_calls':[call]},{}))
    run=agent.create_run(project_id,agent.RunInput(message='设计一个分离单元',mode='engineering',max_model_requests=1))
    assert engineering_phase(project_id)['stage']=='requirements'
    assert 'engineering_plan' not in engineering_tool_policy(project_id)[1]
    agent.execute_run(run)
    state=json.loads(one('SELECT result FROM runs WHERE id=?',(run,))['result'])
    assert state['failures'][0]['tool']=='engineering_plan'
    assert '工程阶段为requirements' in state['failures'][0]['error']
    assert not rows('SELECT * FROM engineering_deliverables WHERE project_id=?',(project_id,))


def test_output_plan_cannot_override_original_formats_or_review(project_id):
    seed_requirements(project_id)
    generated=run_tool(project_id,'export_report',{'title':'待完成报告','body':'TODO 待补充设备设计','formats':['md']})
    p=DeliverableWrite(key='report',title='项目可行性研究报告',requirement_codes=['D01'],formats=['md'],
                       acceptance_criteria='模型声称完成不能通过',files=[{'artifact_id':generated['artifacts'][0]['id'],'location':'全文'}])
    save_deliverable(project_id,p)
    status=engineering_status(project_id)
    assert not status['ready']
    assert any('DOCX及PDF' in i for i in status['deliverables'][0]['issues'])
    assert any('占位' in i for i in status['deliverables'][0]['issues'])
    assert status['deliverables'][0]['professional_review']=='not_reviewed'
    assert len(status['requirements'])==35
    with pytest.raises(ValueError,match='不存在的要求'):
        save_deliverable(project_id,delivery_input().model_copy(update={'key':'unknown','requirement_codes':['NOT_REAL']}))


def test_native_extension_is_not_runtime_verification(project_id):
    seed_requirements(project_id)
    generated=run_tool(project_id,'export_report',{'title':'流程结果','body':'结果汇总','formats':['pdf']})
    p=DeliverableWrite(key='simulation',title='模拟优化',requirement_codes=['P03','D05'],formats=['pdf'],
        native_software='任意模拟器 1.0',acceptance_criteria='需要真实原生执行',files=[{'artifact_id':generated['artifacts'][0]['id'],'location':'全文'}])
    save_deliverable(project_id,p)
    assert any('独立打开及运行' in i for i in engineering_status(project_id)['deliverables'][0]['issues'])


def test_frozen_run_and_external_output_rejection_and_packaging(project_id,monkeypatch,client):
    seed_requirements(project_id)
    source=ingest(project_id,'original.txt',b'Input task data')
    generated=run_tool(project_id,'export_report',{'title':'先前报告','body':'不能冒充本次平台成果','formats':['docx','pdf']})
    save_deliverable(project_id,delivery_input(files=[{'artifact_id':r['id'],'location':'第一段'} for r in generated['artifacts']]))
    monkeypatch.setenv('MODEL_BALANCED','deepseek-flash')
    ident=agent.create_run(project_id,agent.RunInput(message='整包任务',mode='engineering'))
    snapshot=json.loads(one('SELECT snapshot FROM engineering_run_inputs WHERE run_id=?',(ident,))['snapshot'])
    assert source['id'] in {r['id'] for r in snapshot['inputs']}
    assert snapshot['model']=='deepseek-flash' and 'key' not in snapshot
    with zipfile.ZipFile(snapshot['frozen_archive']) as archive:
        assert 'platform/app/agent.py' in archive.namelist()
    audit=engineering_status(project_id,run_id=ident)
    assert any(b['kind']=='autonomous_origin' for b in audit['blockers'])
    bundle=client.post('/api/projects/'+project_id+'/bundle').json()
    content=client.get(bundle['download_url']).content
    import io
    with zipfile.ZipFile(io.BytesIO(content)) as archive:
        manifest=json.loads(archive.read('manifest.json'))
        assert manifest['engineering']['ready'] is False
        assert manifest['frozen_runs'][0]['run_id']==ident
        assert 'frozen/'+ident+'/inputs-platform.zip' in archive.namelist()
        assert manifest['engineering_history']['engineering_deliverable_revisions']


def test_engineering_loop_continues_beyond_chat_limit_and_cannot_self_approve(project_id,monkeypatch):
    monkeypatch.setenv('MODEL_BALANCED','deepseek-flash')
    monkeypatch.setenv('MAX_AGENT_ITERATIONS','1')
    count=[0]
    def completion(cfg,p,messages):
        count[0]+=1
        if count[0]<=2:
            return {'role':'assistant','content':None,'tool_calls':[{'id':'call-'+str(count[0]),'type':'function','function':{'name':'convert_units','arguments':json.dumps({'value':1,'from_unit':'bar','to_unit':'kPa'})}}]},{}
        return {'role':'assistant','content':'我已完成所有工程任务。'},{}
    monkeypatch.setattr(agent,'completion',completion)
    ident=agent.create_run(project_id,agent.RunInput(message='整包任务',mode='engineering',max_model_requests=5))
    agent.execute_run(ident)
    record=one('SELECT * FROM runs WHERE id=?',(ident,))
    state=json.loads(record['result'])
    assert count[0]==5 and record['status']=='needs_review'
    assert state['engineering_acceptance']['ready'] is False
    assert state['delivery_repair_requested']
    assert state['failures'][0]['tool']=='convert_units'
    assert '工程阶段为requirements' in state['failures'][0]['error']


def test_engineering_request_budget_and_model_floor(project_id,monkeypatch):
    monkeypatch.setenv('MODEL_BALANCED','weaker-model')
    with pytest.raises(ValueError,match='不会静默降级'):
        agent.create_run(project_id,agent.RunInput(message='正式整包',mode='engineering'))
    monkeypatch.setenv('MODEL_BALANCED','deepseek-flash')
    monkeypatch.setattr(agent,'completion',lambda *args:({'role':'assistant','content':'完成'},{}))
    ident=agent.create_run(project_id,agent.RunInput(message='请求预算测试',mode='engineering',max_model_requests=1))
    agent.execute_run(ident)
    assert one('SELECT status FROM runs WHERE id=?',(ident,))['status']=='budget_exhausted'


def test_ai_vision_subrequests_count_against_engineering_model_budget(project_id,monkeypatch):
    monkeypatch.setenv('MODEL_BALANCED','deepseek-flash')
    call={'role':'assistant','content':None,'tool_calls':[{'id':'vision-call','type':'function',
        'function':{'name':'document_extract','arguments':json.dumps({'artifact_id':'source-id','image_mode':'ai'})}}]}
    monkeypatch.setattr(agent,'completion',lambda *args:(call,{'total_tokens':12}))
    monkeypatch.setattr(agent,'run_tool',lambda *args:{
        'status':'extracted','vision_requests':[{'request_made':True,'model':'deepseek-flash',
            'status':'transcribed_not_verified','usage':{'total_tokens':7}}]})
    ident=agent.create_run(project_id,agent.RunInput(message='扫描原件逐页识读',mode='engineering',max_model_requests=2))
    agent.execute_run(ident)
    record=one('SELECT status,result FROM runs WHERE id=?',(ident,))
    state=json.loads(record['result'])
    assert record['status']=='budget_exhausted'
    assert state['iterations']==2
    assert state['model_usage']==[{'total_tokens':12},{'total_tokens':7}]
    vision=rows("SELECT payload FROM events WHERE run_id=? AND type='vision_model'",(ident,))
    assert len(vision)==1 and json.loads(vision[0]['payload'])['model']=='deepseek-flash'


def test_item_scope_does_not_skip_sources_or_approve_other_requirements(project_id,monkeypatch):
    from app.fulltext import ExtractInput, extract_document
    monkeypatch.setenv('MODEL_BALANCED','deepseek-flash')
    for code in ['R01','R02']:
        execute('INSERT INTO requirements(id,project_id,code,title,page,mandatory) VALUES(?,?,?,?,?,?)',
                (uid(),project_id,code,'Requirement '+code,None,1))
    with pytest.raises(ValueError,match='要求编码'):
        agent.create_run(project_id,agent.RunInput(message='unknown scope',mode='engineering',requirement_codes=['ABSENT']))
    source=ingest(project_id,'brief.txt',b'Raw material specification is required. Site design is required.')
    snapshot=extract_document(project_id,ExtractInput(artifact_id=source['id']))
    save_requirements(project_id,RequirementBatch(requirements=[RequirementSource(code='R01',title='Requirement R01',
        applicability='The raw material scope only',snapshot_id=snapshot['snapshot_id'],block_id='b00001',quote='Raw material specification is required.')]))
    assert engineering_phase(project_id)['stage']=='requirements'
    assert engineering_phase(project_id,['R01'])['stage']=='plan'
    save_deliverable(project_id,DeliverableWrite(key='raw-material',title='Raw material data',
        requirement_codes=['R01'],formats=['docx','pdf'],acceptance_criteria='Original sources and technical specification'))
    assert engineering_phase(project_id,['R01'])['stage']=='basis'
    scoped=engineering_status(project_id,EngineeringQuery(requirement_codes=['R01']))
    assert [r['code'] for r in scoped['requirements']]==['R01']
    assert not scoped['ready'] and not scoped['complete_project_acceptance']
    assert scoped['scope']==['R01']
    assert any(b['kind']=='professional_review' and b['key']=='R01' for b in scoped['blockers'])
    full=engineering_status(project_id)
    assert len(full['requirements'])==2
    assert any(b['key']=='R02' for b in full['blockers'])
