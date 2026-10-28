"""Exercise project/conversation navigation and actual resource previews on an isolated server."""
import argparse
import json
import time
from pathlib import Path
from playwright.sync_api import sync_playwright, expect

OUT = Path(__file__).resolve().parent.parent / 'output' / 'playwright' / 'conversations'


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--url', default='http://127.0.0.1:8001')
    args = parser.parse_args()
    OUT.mkdir(parents=True, exist_ok=True)
    checks, errors = [], []
    with sync_playwright() as p:
        browser = p.chromium.launch(channel='msedge', headless=True)
        page = browser.new_page(viewport={'width': 1536, 'height': 1024}, reduced_motion='reduce')
        page.on('pageerror', lambda e: errors.append(str(e)))
        api = page.request
        project = api.post(args.url + '/api/projects', data={'name': '苯乙烯清洁生产 · ' + str(time.time_ns())}).json()
        prefix = args.url + '/api/projects/' + project['id']
        task = {'key': 'material_balance', 'title': '物料衡算研究', 'tool': 'convert_units', 'arguments': {'value': 1, 'from_unit': 'bar', 'to_unit': 'Pa'}}
        assert api.post(prefix + '/study/tasks', data=task).ok
        a = api.post(prefix + '/conversations', data={'title': '设计依据与参数', 'task_key': task['key']}).json()
        b = api.post(prefix + '/conversations', data={'title': '工况比较与校核', 'task_key': task['key']}).json()
        c = api.post(prefix + '/conversations', data={'title': '文献检索与证据'}).json()
        other = api.post(args.url + '/api/projects', data={'name': '换热网络研究'}).json()
        api.post(args.url + '/api/projects/' + other['id'] + '/conversations', data={'title': '换热方案'})
        resource = api.post(prefix + '/upload?conversation_id=' + a['id'], multipart={'file': {'name': '设计依据.txt', 'mimeType': 'text/plain', 'buffer': '研究依据：操作压力 100 kPa。资料待工程校核。'.encode()}}).json()
        svg = b'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 300 120"><rect x="70" y="25" width="160" height="70" rx="10" fill="#eef2ff" stroke="#6d81cf"/><text x="150" y="65" text-anchor="middle" fill="#52659f">R-101</text></svg>'
        drawing = api.post(prefix + '/upload?conversation_id=' + a['id'], multipart={'file': {'name': '反应器概念图.svg', 'mimeType': 'image/svg+xml', 'buffer': svg}}).json()
        api.post(prefix + '/upload', multipart={'file': {'name': '项目公共资料.txt', 'mimeType': 'text/plain', 'buffer': b'Project reference.'}})
        page.goto(args.url)
        expect(page.locator('#chat-form')).to_be_visible(timeout=30000)
        page.locator('[data-project="' + project['id'] + '"]').click()
        page.locator('[data-conversation="' + a['id'] + '"]').click()
        expect(page.locator('#page-name')).to_have_text(a['title'])
        expect(page.locator('.conversation-group-label')).to_contain_text(task['title'])
        assert page.locator('.project-entry').count() >= 2
        tree_box = page.locator('.project-tree').bounding_box()
        nav_box = page.locator('.bottom-navigation').bounding_box()
        assert tree_box['y'] + tree_box['height'] <= nav_box['y'] + 1
        checks.append('sidebar primarily lists projects, task groups and multiple conversations; functional navigation is at the bottom')

        field = page.locator('#chat-form textarea')
        field.fill('会话 A 的未发送研究需求')
        page.locator('[data-conversation="' + b['id'] + '"]').click()
        expect(field).to_have_value('')
        field.fill('会话 B 的独立草稿')
        page.locator('[data-conversation="' + a['id'] + '"]').click()
        expect(field).to_have_value('会话 A 的未发送研究需求')
        page.reload()
        expect(field).to_have_value('会话 A 的未发送研究需求')
        expect(page.locator('#page-name')).to_have_text(a['title'])
        checks.append('conversation selection and per-conversation drafts persist after reload')

        page.locator('#project-overview-button').click()
        expect(page.locator('.resource-context h2')).to_have_text(task['title'])
        expect(page.locator('.resource-card')).to_have_count(2)
        assert page.locator('#project-dialog').evaluate('el => el.tagName') == 'ASIDE'
        composer_box = page.locator('.composer').bounding_box()
        drawer_box = page.locator('#project-dialog').bounding_box()
        assert composer_box['x'] + composer_box['width'] <= drawer_box['x'], 'desktop drawer covered composer'
        page.locator('[data-resource-preview="' + resource['id'] + '"]').first.click()
        expect(page.frame_locator('#resource-preview-frame').locator('body')).to_contain_text('100 kPa')
        page.screenshot(path=str(OUT / 'task-resources-desktop.png'), full_page=True)
        page.locator('[data-resource-preview="' + drawing['id'] + '"]').first.click()
        expect(page.frame_locator('#resource-preview-frame').locator('svg')).to_be_visible()
        page.locator('[data-expand-resource]').click()
        expect(page.locator('#preview-dialog')).to_be_visible()
        expect(page.frame_locator('#preview-frame').locator('svg')).to_be_visible()
        page.locator('[data-close="preview-dialog"]').click()
        checks.append('nonmodal task resources include live text/SVG previews and expanded preview')

        page.locator('[data-conversation="' + b['id'] + '"]').click()
        expect(page.locator('.resource-card')).to_have_count(2)
        expect(page.locator('#resource-preview')).not_to_be_visible()
        page.locator('[data-conversation="' + c['id'] + '"]').click()
        expect(page.locator('.resource-empty')).to_be_visible()
        page.locator('[data-resource-scope="project"]').first.click()
        expect(page.locator('.resource-card')).to_have_count(3)
        page.locator('[data-link-resource="' + resource['id'] + '"]').click()
        page.locator('[data-resource-scope="conversation"]').click()
        expect(page.locator('.resource-card')).to_have_count(1)
        checks.append('task conversations share related resources while unrelated conversations stay isolated; project resources can be linked')

        page.locator('#upload').set_input_files({'name': '本次会话资料.txt', 'mimeType': 'text/plain', 'buffer': '会话上传验收'.encode()})
        expect(page.locator('.resource-card')).to_have_count(2, timeout=20000)
        checks.append('uploaded files are associated with the active conversation')
        page.locator('#conversation-settings').click()
        page.locator('#conversation-settings-form input[name="title"]').fill('文献证据整理')
        page.locator('#conversation-settings-form button').click()
        expect(page.locator('#page-name')).to_have_text('文献证据整理')
        expect(page.locator('[data-conversation="' + c['id'] + '"]')).to_contain_text('文献证据整理')
        checks.append('conversation settings update title and project tree')

        page.locator('[data-task-conversation="' + task['key'] + '"]').click()
        expect(page.locator('#page-name')).to_have_text('新会话')
        expect(field).to_have_value('')
        expect(page.locator('.resource-context h2')).to_have_text(task['title'])
        checks.append('new conversations can be created under the same research task')

        for name, selector in [('study', '#study-workspace'), ('files', '.files-grid'), ('tools', '#tool-picker'), ('research', '#research-form'), ('evidence', '#evidence-workspace'), ('datasets', '#dataset-picker'), ('database', '#equipment-panel'), ('acceptance', '#content .empty')]:
            page.locator('.bottom-navigation [data-page="' + name + '"]').click()
            expect(page.locator(selector).first).to_be_visible(timeout=15000)
        page.locator('.bottom-navigation [data-page="workspace"]').click()
        checks.append('all nine relocated functional destinations work with the resource panel open')

        page.locator('[data-close-resources]').click()
        page.locator('[data-project="' + other['id'] + '"]').click()
        expect(page.locator('#project-name')).to_have_text('换热网络研究')
        expect(field).to_have_value('')
        page.locator('[data-project="' + project['id'] + '"]').click()
        page.locator('[data-conversation="' + a['id'] + '"]').click()
        expect(field).to_have_value('会话 A 的未发送研究需求')
        page.screenshot(path=str(OUT / 'projects-desktop.png'), full_page=True)
        checks.append('project switching retains independent conversations and drafts')

        for width, height in [(1024, 768), (768, 1024), (390, 844), (320, 640)]:
            page.set_viewport_size({'width': width, 'height': height})
            assert page.evaluate('document.documentElement.scrollWidth <= innerWidth'), str(width)
            expect(field).to_be_visible()
            box = page.locator('#send-button').bounding_box()
            assert box['y'] + box['height'] < height
            page.locator('#project-overview-button').click()
            expect(page.locator('.resource-card')).to_have_count(2)
            page.locator('[data-resource-preview="' + resource['id'] + '"]').first.click()
            expect(page.frame_locator('#resource-preview-frame').locator('body')).to_contain_text('100 kPa')
            page.screenshot(path=str(OUT / ('resources-' + str(width) + '.png')), full_page=True)
            page.locator('[data-close-resources]').click()
            if width <= 760:
                page.locator('#sidebar-toggle').click()
                expect(page.locator('.project-tree')).to_be_visible()
                page.locator('.bottom-navigation [data-page="tools"]').click()
                expect(page.locator('#tool-picker')).to_be_visible()
                page.locator('#sidebar-toggle').click()
                page.locator('.bottom-navigation [data-page="workspace"]').click()
        checks.append('1024/768/390/320 viewport layouts, mobile project navigation and resource previews')
        assert not errors, errors
        browser.close()
    result = {'passed': True, 'checks': checks, 'page_errors': errors, 'external_model_calls': 0}
    (OUT / 'results.json').write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding='utf-8')
    print(json.dumps(result, ensure_ascii=False))


if __name__ == '__main__':
    main()
