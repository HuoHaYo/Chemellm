"""Verify editable settings on an isolated server and the production preview without model calls."""
import json
from pathlib import Path
from playwright.sync_api import sync_playwright, expect

OUT = Path(__file__).resolve().parent.parent / 'output' / 'playwright' / 'model-settings'


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    checks, errors = [], []
    with sync_playwright() as p:
        browser = p.chromium.launch(channel='msedge', headless=True)
        page = browser.new_page(viewport={'width': 1278, 'height': 1012})
        page.on('pageerror', lambda error: errors.append(str(error)))
        page.goto('http://127.0.0.1:8000')
        expect(page.locator('#chat-form textarea')).to_be_visible(timeout=30000)
        expect(page.locator('.conversation-entry').first).to_be_visible()
        assert page.locator('#chat-form textarea').bounding_box()['height'] > 50
        page.screenshot(path=str(OUT / 'preview-chat-restored.png'), full_page=True)
        page.locator('#settings-button').click()
        expect(page.locator('#model-settings-form')).to_be_visible()
        expect(page.locator('#model-settings-form input[name="base_url"]')).to_be_editable()
        page.screenshot(path=str(OUT / 'preview-editable-settings.png'), full_page=True)
        page.keyboard.press('Escape')
        checks.append('8000 preview displays AI composer and editable model settings')

        # Only change settings on the dedicated QA server.
        page.goto('http://127.0.0.1:8001')
        expect(page.locator('#chat-form')).to_be_visible()
        page.locator('#settings-button').click()
        form = page.locator('#model-settings-form')
        form.locator('[name="base_url"]').fill('https://qa-model.invalid/v1')
        form.locator('[name="api_key"]').fill('qa-test-secret')
        for speed in ['fast', 'balanced', 'deep']:
            form.locator('[name="' + speed + '"]').fill('qa-model-' + speed)
        form.locator('.settings-advanced > summary').click()
        form.locator('[name="reasoning_supported"]').check()
        form.locator('[name="timeout"]').fill('100')
        form.locator('[type="submit"]').click()
        expect(page.locator('#form-dialog')).not_to_be_visible()
        expect(page.locator('#model-status')).to_have_text('模型已配置')
        expect(page.locator('#chat-form select[name="reasoning"]')).to_be_enabled()
        response = page.request.get('http://127.0.0.1:8001/api/config')
        assert response.json()['api_key_configured'] is True
        assert 'qa-test-secret' not in response.text()
        page.reload()
        expect(page.locator('#chat-form')).to_be_visible()
        page.locator('#settings-button').click()
        expect(form.locator('[name="balanced"]')).to_have_value('qa-model-balanced')
        expect(form.locator('[name="base_url"]')).to_have_value('https://qa-model.invalid/v1')
        expect(form.locator('[name="api_key"]')).to_have_value('')
        form.locator('[name="balanced"]').fill('qa-updated-model')
        form.locator('[type="submit"]').click()
        expect(page.locator('#form-dialog')).not_to_be_visible()
        assert page.request.get('http://127.0.0.1:8001/api/config').json()['api_key_configured'] is True
        checks.append('save applies immediately, survives reload, retains blank key and never echoes secrets')
        page.locator('#settings-button').click()
        form.locator('[name="clear_api_key"]').check()
        form.locator('[type="submit"]').click()
        expect(page.locator('#form-dialog')).not_to_be_visible()
        assert page.request.get('http://127.0.0.1:8001/api/config').json()['api_key_configured'] is False
        checks.append('explicit clear removes saved key')

        page.route('**/api/health', lambda route: route.fulfill(json={'status': 'ok', 'version': '0.1.0'}))
        page.reload()
        expect(page.locator('.load-error')).to_contain_text('旧版本')
        expect(page.locator('#retry-workspace')).to_be_visible()
        page.unroute('**/api/health')
        page.locator('#retry-workspace').click()
        expect(page.locator('#chat-form')).to_be_visible()
        checks.append('stale backend shows a recoverable error instead of a blank workspace')
        page.locator('#settings-button').click()
        page.set_viewport_size({'width': 390, 'height': 844})
        expect(form.locator('[type="submit"]')).to_be_visible()
        assert page.evaluate('document.documentElement.scrollWidth <= innerWidth')
        page.screenshot(path=str(OUT / 'settings-mobile.png'), full_page=True)
        assert not errors, errors
        browser.close()
    result = {'passed': True, 'checks': checks, 'page_errors': errors, 'external_model_calls': 0}
    (OUT / 'results.json').write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding='utf-8')
    print(json.dumps(result, ensure_ascii=False))


if __name__ == '__main__':
    main()
