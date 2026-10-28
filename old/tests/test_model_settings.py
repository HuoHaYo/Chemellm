import json
import pytest
from app import config
from app.agent import RunInput, create_run
from app.db import one


@pytest.fixture
def settings_path(tmp_path, monkeypatch):
    path = tmp_path / 'model-settings.json'
    monkeypatch.setattr(config, 'SETTINGS_PATH', path)
    return path


def payload(**changes):
    return {'provider': 'openai_compatible', 'base_url': 'https://models.example/v1',
            'models': {'fast': 'fast-test', 'balanced': 'balanced-test', 'deep': 'deep-test'},
            'api_key': 'test-secret-never-return', 'reasoning_supported': True,
            'timeout': 90, 'iterations': 6, **changes}


def test_save_is_persistent_immediate_and_never_returns_key(client, settings_path, project_id, monkeypatch):
    response = client.put('/api/config', json=payload())
    assert response.status_code == 200
    assert response.json()['api_key_configured'] is True
    assert 'test-secret-never-return' not in response.text
    assert client.get('/api/config').json()['models']['balanced'] == 'balanced-test'
    assert 'test-secret-never-return' not in client.get('/api/config').text
    assert json.loads(settings_path.read_text(encoding='utf-8'))['key'] == 'test-secret-never-return'
    assert config.model_config()['base_url'] == 'https://models.example/v1'
    run = create_run(project_id, RunInput(message='configuration availability check'))
    assert one('SELECT status FROM runs WHERE id=?', (run,))['status'] == 'queued'


def test_blank_key_preserves_and_clear_removes_secret(client, settings_path):
    assert client.put('/api/config', json=payload()).status_code == 200
    assert client.put('/api/config', json=payload(api_key='', iterations=7)).status_code == 200
    assert config.model_config()['key'] == 'test-secret-never-return'
    result = client.put('/api/config', json=payload(api_key='', clear_api_key=True))
    assert result.json()['api_key_configured'] is False
    assert config.model_config()['key'] == ''


@pytest.mark.parametrize('url', ['file:///private/data', 'https://user:secret@models.example/v1', 'https://models.example/v1?api_key=secret', 'https://models.example/v1#secret', 'not-a-url'])
def test_invalid_addresses_do_not_replace_saved_settings(client, settings_path, url):
    client.put('/api/config', json=payload())
    previous = settings_path.read_bytes()
    assert client.put('/api/config', json=payload(base_url=url)).status_code == 422
    assert settings_path.read_bytes() == previous


def test_configuration_respects_auth_and_cross_site_protection(client, settings_path, monkeypatch):
    monkeypatch.setattr(config, 'AUTH_TOKEN', 'qa-workspace-token')
    assert client.put('/api/config', json=payload()).status_code == 401
    assert client.get('/api/config').status_code == 401
    headers = {'Authorization': 'Bearer qa-workspace-token'}
    assert client.put('/api/config', json=payload(), headers={**headers, 'Origin': 'https://unrelated.example'}).status_code == 403
    assert client.put('/api/config', json=payload(), headers=headers).status_code == 200


def test_health_advertises_current_ui_contract(client):
    health = client.get('/api/health').json()
    assert 'conversations' in health['capabilities']
    assert 'editable_model_settings' in health['capabilities']
    assert client.get('/app.js').headers['cache-control'] == 'no-store'
