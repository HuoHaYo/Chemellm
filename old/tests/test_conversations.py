import json
from app import agent
from app.agent import RunInput, create_run, execute_run, resume_run
from app.conversations import ConversationWrite, create_conversation, conversation_resources, conversation_history, list_conversations
from app.db import init_db, execute, one, rows, uid, now


def test_legacy_migration_is_idempotent(project_id):
    message_id, run_id, stamp = uid(), uid(), now()
    execute('INSERT INTO messages VALUES(?,?,?,?,?)', (message_id, project_id, 'user', 'existing transcript', stamp))
    execute('INSERT INTO runs VALUES(?,?,?,?,?,?,?)', (run_id, project_id, 'completed', '{}', '{}', stamp, stamp))
    init_db()
    init_db()
    assert one('SELECT conversation_id FROM conversation_messages WHERE message_id=?', (message_id,))['conversation_id'] == 'legacy-' + project_id
    assert one('SELECT conversation_id FROM conversation_runs WHERE run_id=?', (run_id,))['conversation_id'] == 'legacy-' + project_id
    assert one('SELECT COUNT(*) AS n FROM conversations WHERE project_id=?', (project_id,))['n'] == 1
    assert one('SELECT content FROM messages WHERE id=?', (message_id,))['content'] == 'existing transcript'


def test_model_history_is_isolated_and_resume_stays_in_conversation(project_id, monkeypatch):
    monkeypatch.setenv('MODEL_BALANCED', 'test-model')
    a = create_conversation(project_id, ConversationWrite(title='A'))
    b = create_conversation(project_id, ConversationWrite(title='B'))
    seen = []
    def completion(cfg, p, history):
        seen.append([m.get('content') for m in history if m.get('role') != 'system'])
        return {'role': 'assistant', 'content': 'reply to ' + p.message}, {}
    monkeypatch.setattr(agent, 'completion', completion)
    first = create_run(project_id, RunInput(message='only in A', conversation_id=a['id']))
    execute_run(first)
    second = create_run(project_id, RunInput(message='only in B', conversation_id=b['id']))
    execute_run(second)
    assert seen[0] == ['only in A']
    assert seen[1] == ['only in B']
    third = create_run(project_id, RunInput(message='A followup', conversation_id=a['id']))
    execute_run(third)
    assert seen[2] == ['only in A', 'reply to only in A', 'A followup']
    execute("UPDATE runs SET status='awaiting_user' WHERE id=?", (third,))
    resume_run(third, 'A resume answer')
    assert one('SELECT cm.conversation_id FROM conversation_messages cm JOIN messages m ON m.id=cm.message_id WHERE m.content=?', ('A resume answer',))['conversation_id'] == a['id']


def test_api_conversation_scope_and_resource_previews(client, monkeypatch):
    monkeypatch.setattr('app.main.dispatch', lambda ident: None)
    monkeypatch.setenv('MODEL_BALANCED', 'test-model')
    project = client.post('/api/projects', json={'name': 'Resource QA'}).json()['id']
    other = client.post('/api/projects', json={'name': 'Other project'}).json()['id']
    prefix = '/api/projects/' + project
    a = client.post(prefix + '/conversations', json={'title': 'A'}).json()
    b = client.post(prefix + '/conversations', json={'title': 'B'}).json()
    foreign = client.post('/api/projects/' + other + '/conversations', json={'title': 'Foreign'}).json()
    assert client.post(prefix + '/runs', json={'message': 'bad', 'conversation_id': foreign['id']}).status_code == 422
    resource = client.post(prefix + '/upload?conversation_id=' + a['id'], files={'file': ('basis.txt', b'pressure = 100 kPa', 'text/plain')}).json()
    assert client.get(resource['preview_url']).status_code == 200
    assert '100 kPa' in client.get(resource['preview_url']).text
    assert len(client.get(prefix + '/conversations/' + a['id'] + '/resources').json()['artifacts']) == 1
    assert client.get(prefix + '/conversations/' + b['id'] + '/resources').json()['artifacts'] == []
    assert client.post(prefix + '/conversations/' + b['id'] + '/resources/' + resource['id']).status_code == 200
    assert len(client.get(prefix + '/conversations/' + b['id'] + '/resources').json()['artifacts']) == 1
    assert client.post('/api/projects/' + other + '/conversations/' + foreign['id'] + '/resources/' + resource['id']).status_code == 422
    run = client.post(prefix + '/runs', json={'message': 'A scoped message', 'conversation_id': a['id']}).json()
    assert len(client.get(prefix + '/messages?conversation_id=' + a['id']).json()) == 1
    assert client.get(prefix + '/messages?conversation_id=' + b['id']).json() == []
    assert client.get(prefix + '/runs?conversation_id=' + a['id']).json()[0]['id'] == run['id']
    assert client.get(prefix + '/runs?conversation_id=' + b['id']).json() == []
    assert client.get(prefix + '/conversations/' + foreign['id'] + '/resources').status_code == 422
    assert client.post(prefix + '/upload?conversation_id=' + foreign['id'], files={'file': ('bad.txt', b'bad', 'text/plain')}).status_code == 422
    assert len(client.get(prefix + '/artifacts').json()) == 1


def test_task_supports_multiple_conversations_and_resources(client):
    project = client.post('/api/projects', json={'name': 'Task QA'}).json()['id']
    prefix = '/api/projects/' + project
    assert client.post(prefix + '/study/tasks', json={'key': 'pressure', 'title': '压力核对', 'tool': 'convert_units', 'arguments': {'value': 1, 'from_unit': 'bar', 'to_unit': 'Pa'}}).status_code == 200
    a = client.post(prefix + '/conversations', json={'title': '会话一', 'task_key': 'pressure'}).json()
    b = client.post(prefix + '/conversations', json={'title': '会话二', 'task_key': 'pressure'}).json()
    assert a['task_key'] == b['task_key'] == 'pressure'
    assert len(client.get(prefix + '/conversations').json()) == 2
    assert client.get(prefix + '/conversations/' + a['id'] + '/resources').json()['task']['config']['title'] == '压力核对'
    uploaded = client.post(prefix + '/upload?conversation_id=' + a['id'], files={'file': ('task-basis.txt', b'shared task resource', 'text/plain')}).json()
    assert client.get(prefix + '/conversations/' + b['id'] + '/resources').json()['artifacts'][0]['id'] == uploaded['id']
    assert client.post(prefix + '/conversations', json={'title': 'Invalid', 'task_key': 'missing'}).status_code == 422
    renamed = client.patch(prefix + '/conversations/' + a['id'], json={'title': '重命名', 'task_key': 'pressure'})
    assert renamed.json()['title'] == '重命名'
    assert client.patch(prefix + '/conversations/' + a['id'], json={'title': '   '}).status_code == 422


def test_tool_result_artifacts_appear_in_matching_conversation(project_id, monkeypatch):
    monkeypatch.setenv('MODEL_BALANCED', 'test-model')
    a = create_conversation(project_id, ConversationWrite(title='Report'))
    b = create_conversation(project_id, ConversationWrite(title='Other'))
    calls = [0]
    def completion(cfg, p, history):
        calls[0] += 1
        if calls[0] == 1:
            return {'role': 'assistant', 'content': None, 'tool_calls': [{'id': 'report', 'type': 'function', 'function': {'name': 'export_report', 'arguments': json.dumps({'title': 'resource-report', 'body': 'A generated test document.', 'formats': ['md']})}}]}, {}
        return {'role': 'assistant', 'content': 'Report saved.'}, {}
    monkeypatch.setattr(agent, 'completion', completion)
    ident = create_run(project_id, RunInput(message='make a report', conversation_id=a['id']))
    execute_run(ident)
    result = conversation_resources(project_id, a['id'])
    assert len(result['artifacts']) == 1
    assert '会话成果' in result['artifacts'][0]['relations']
    assert conversation_resources(project_id, b['id'])['artifacts'] == []
    assert conversation_history(project_id,a['id'])['total_calculations'] == 1
    assert conversation_history(project_id,b['id'])['total_calculations'] == 0


def test_historical_tool_only_project_recovers_records_without_fake_messages(client):
    project_id=client.post('/api/projects',json={'name':'Historical Cantera project'}).json()['id']
    prefix='/api/projects/'+project_id
    result=client.post(prefix+'/tools/convert_units',json={'arguments':{'value':2,'from_unit':'bar','to_unit':'Pa'}}).json()
    file=client.post(prefix+'/upload',files={'file':('old-basis.txt',b'100 kPa original data','text/plain')}).json()
    empty=create_conversation(project_id,ConversationWrite())
    init_db()
    init_db()
    conversations=list_conversations(project_id)
    history=next(c for c in conversations if c.get('history_cutoff'))
    assert history['id']=='history-'+project_id
    assert history['calculation_count']==1
    assert history['message_count']==0
    assert one('SELECT COUNT(*) AS n FROM messages WHERE project_id=?',(project_id,))['n']==0
    records=client.get(prefix+'/conversations/'+history['id']+'/history').json()
    assert records['is_project_history'] is True
    assert records['calculations'][0]['id']==result['calculation_id']
    assert records['calculations'][0]['input']['value']==2
    assert records['calculations'][0]['result']['value']==200000
    assert records['artifacts'][0]['id']==file['id']
    assert client.get(prefix+'/conversations/'+empty['id']+'/history').json()['total_calculations']==0
    assert conversation_resources(project_id,history['id'])['artifacts'][0]['id']==file['id']
    assert client.get(prefix+'/messages?conversation_id='+history['id']).json()==[]


def test_manual_tools_save_to_active_conversation_and_respect_history_cutoff(client):
    project_id=client.post('/api/projects',json={'name':'Manual work scope'}).json()['id']
    prefix='/api/projects/'+project_id
    a=create_conversation(project_id,ConversationWrite(title='A'))
    b=create_conversation(project_id,ConversationWrite(title='B'))
    result=client.post(prefix+'/tools/convert_units',json={'arguments':{'value':3,'from_unit':'bar','to_unit':'Pa'},'conversation_id':a['id']})
    assert result.status_code==200
    assert conversation_history(project_id,a['id'])['calculations'][0]['result']['value']==300000
    assert conversation_history(project_id,b['id'])['total_calculations']==0
    init_db()
    assert not any(c.get('history_cutoff') for c in list_conversations(project_id))
    other=client.post('/api/projects',json={'name':'Other project'}).json()['id']
    foreign=create_conversation(other,ConversationWrite())
    bad=client.post(prefix+'/tools/convert_units',json={'arguments':{},'conversation_id':foreign['id']})
    assert bad.status_code==422
    assert one('SELECT count(*) AS n FROM calculations WHERE project_id=?',(project_id,))['n']==1


def test_history_paginates_without_mixing_other_conversations(client):
    project_id=client.post('/api/projects',json={'name':'Paged history'}).json()['id']
    a=create_conversation(project_id,ConversationWrite(title='A'))
    for value in range(3):
        client.post('/api/projects/'+project_id+'/tools/convert_units',json={'arguments':{'value':value,'from_unit':'bar','to_unit':'Pa'},'conversation_id':a['id']})
    page=conversation_history(project_id,a['id'],limit=1,offset=1)
    assert page['total_calculations']==3 and len(page['calculations'])==1
    assert page['calculations'][0]['input']['value']==1
