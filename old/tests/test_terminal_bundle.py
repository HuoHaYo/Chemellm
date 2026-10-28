import json
import zipfile

from app import agent
from app.db import one, rows


def test_engineering_terminal_evidence_bundle_preserves_checkpoint_and_failure(project_id, monkeypatch):
    monkeypatch.setenv('MODEL_BALANCED', 'deepseek-flash')
    monkeypatch.setattr(agent, 'completion', lambda *args: ({'role': 'assistant', 'content': '未完成，保留工程缺口。'}, {}))
    run_id = agent.create_run(project_id, agent.RunInput(
        message='终态证据封包测试', mode='engineering', max_model_requests=2))
    agent.execute_run(run_id)
    status = one('SELECT status FROM runs WHERE id=?', (run_id,))['status']
    assert status in {'needs_review', 'budget_exhausted'}

    details = agent.capture_terminal_engineering_evidence(run_id)
    assert details['run_id'] == run_id
    assert details['status'] == status
    assert details['classification'].startswith('executor_terminal_evidence_')
    snapshot_events = rows("SELECT * FROM events WHERE run_id=? AND type='executor_terminal_snapshot'", (run_id,))
    assert len(snapshot_events) == 1
    assert json.loads(snapshot_events[0]['payload'])['snapshot_token'] == details['snapshot_token']

    zip_rows = rows("SELECT * FROM artifacts WHERE project_id=? AND kind='zip'", (project_id,))
    assert len(zip_rows) == 1
    metadata = json.loads(zip_rows[0]['metadata'])
    assert metadata['executor_terminal_evidence']['run_id'] == run_id
    with zipfile.ZipFile(zip_rows[0]['path']) as archive:
        manifest = json.loads(archive.read('manifest.json'))
    terminal = manifest['executor_terminal_evidence']
    assert terminal['run_id'] == run_id
    assert terminal['status'] == status
    assert terminal['checkpoint_sha256'] == details['checkpoint_sha256']
    assert terminal['classification'] == 'executor_terminal_evidence_not_model_authored_engineering_deliverable'
    assert terminal['professional_review'] == 'not_reviewed'
    assert any(e['type'] == 'executor_terminal_snapshot' for e in terminal['events'])


def test_terminal_capture_is_idempotent_for_same_checkpoint(project_id, monkeypatch):
    monkeypatch.setenv('MODEL_BALANCED', 'deepseek-flash')
    monkeypatch.setattr(agent, 'completion', lambda *args: ({'role': 'assistant', 'content': '未完成。'}, {}))
    run_id = agent.create_run(project_id, agent.RunInput(
        message='重复封包测试', mode='engineering', max_model_requests=1))
    agent.execute_run(run_id)
    first = agent.capture_terminal_engineering_evidence(run_id)
    second = agent.capture_terminal_engineering_evidence(run_id)
    assert second == first
    assert len(rows("SELECT id FROM artifacts WHERE project_id=? AND kind='zip'", (project_id,))) == 1
    assert len(rows("SELECT id FROM events WHERE run_id=? AND type='executor_terminal_snapshot'", (run_id,))) == 1


def test_interrupted_unknown_tool_is_captured_without_replay(project_id, monkeypatch):
    from app import toolbox
    from app.documents import ingest
    monkeypatch.setenv('MODEL_BALANCED', 'deepseek-flash')
    artifact = ingest(project_id, 'source.txt', b'engineering source input')
    calls = [{'id': 'unknown-call', 'type': 'function', 'function': {
        'name': 'document_extract', 'arguments': json.dumps({'artifact_id': artifact['id']})}}]
    monkeypatch.setattr(agent, 'completion', lambda *args: ({'role': 'assistant', 'content': None, 'tool_calls': calls}, {}))
    def interrupted(*args):
        raise toolbox.UncertainToolError('write result acknowledgement uncertain')
    monkeypatch.setattr(agent, 'run_tool', interrupted)
    run_id = agent.create_run(project_id, agent.RunInput(
        message='未知调用不重放测试', mode='engineering', max_model_requests=2))
    agent.execute_run(run_id)
    assert one('SELECT status FROM runs WHERE id=?', (run_id,))['status'] == 'interrupted'
    before = len(rows("SELECT id FROM calculations WHERE project_id=? AND tool='document_extract'", (project_id,)))
    agent.capture_terminal_engineering_evidence(run_id)
    after = len(rows("SELECT id FROM calculations WHERE project_id=? AND tool='document_extract'", (project_id,)))
    assert after == before == 0
    from app.run_recovery import unknown_calls
    assert unknown_calls(run_id)[0]['call_id'] == 'unknown-call'
    bundle = rows("SELECT path FROM artifacts WHERE project_id=? AND kind='zip'", (project_id,))[0]
    with zipfile.ZipFile(bundle['path']) as archive:
        terminal = json.loads(archive.read('manifest.json'))['executor_terminal_evidence']
    assert terminal['status'] == 'interrupted'
    assert any(attempt['status'] == 'unknown' for attempt in terminal['checkpoint']['tool_attempts'])
