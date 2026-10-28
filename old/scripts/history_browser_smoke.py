"""Verify persisted chat selection and historical research records; never calls a model."""
import json
import os
import sys
from pathlib import Path
from playwright.sync_api import sync_playwright, expect

ROOT=Path(__file__).resolve().parent.parent
sys.path.insert(0,str(ROOT))
OUT=ROOT/'output'/'playwright'/'history'
QA_DATA=ROOT/'output'/'playwright'/'history-data'


def main():
    OUT.mkdir(parents=True,exist_ok=True)
    checks,errors=[],[]
    with sync_playwright() as p:
        browser=p.chromium.launch(channel='msedge',headless=True)
        page=browser.new_page(viewport={'width':1278,'height':1012},reduced_motion='reduce')
        page.on('pageerror',lambda e:errors.append(str(e)))
        api=page.request
        base='http://127.0.0.1:8002'
        project=api.post(base+'/api/projects',data={'name':'历史与聊天显示验收'}).json()
        prefix=base+'/api/projects/'+project['id']
        api.post(prefix+'/tools/convert_units',data={'arguments':{'value':2,'from_unit':'bar','to_unit':'Pa'}})
        api.post(prefix+'/upload',multipart={'file':{'name':'历史设计依据.txt','mimeType':'text/plain','buffer':'历史资料压力 100 kPa'.encode()}})
        empty=api.post(prefix+'/conversations',data={'title':'新会话'}).json()
        os.environ['CHEMELLM_DATA_DIR']=str(QA_DATA)
        from app.db import init_db, connection, now, uid
        from app.conversations import add_message
        init_db()
        a=api.post(prefix+'/conversations',data={'title':'工艺参数讨论'}).json()
        b=api.post(prefix+'/conversations',data={'title':'设备选型讨论'}).json()
        # Persist test transcripts in the QA database instead of intercepting browser requests.
        with connection() as db:
            for c,question,answer in [(a,'请核对工况 A 的设计压力。','工况 A 为 100 kPa，需结合资料校核。'),(b,'请比较设备 B 的选型依据。','设备 B 需要温度、压力和材质依据。')]:
                run_id,stamp=uid(),now()
                request=json.dumps({'message':question,'conversation_id':c['id']})
                db.execute('INSERT INTO runs VALUES(?,?,?,?,?,?,?)',(run_id,project['id'],'completed',request,'{}',stamp,stamp))
                db.execute('INSERT INTO conversation_runs VALUES(?,?)',(run_id,c['id']))
                add_message(project['id'],run_id,'user',question,db)
                add_message(project['id'],run_id,'assistant',answer,db)
        history_id='history-'+project['id']
        page.goto(base)
        expect(page.locator('#chat-form')).to_be_visible(timeout=30000)
        page.locator('[data-project="'+project['id']+'"]').click()
        page.locator('[data-conversation="'+a['id']+'"]').click()
        expect(page.locator('.message-user')).to_contain_text('工况 A')
        expect(page.locator('.message-assistant')).to_contain_text('100 kPa')
        expect(page.locator('[data-conversation="'+a['id']+'"] .conversation-count')).to_have_text('2 条消息')
        page.screenshot(path=str(OUT/'saved-chat-a.png'),full_page=True)
        page.locator('[data-conversation="'+b['id']+'"]').click()
        expect(page.locator('.message-user')).to_contain_text('设备 B')
        expect(page.locator('#messages')).not_to_contain_text('工况 A')
        page.reload()
        expect(page.locator('.message-assistant')).to_contain_text('设备 B')
        checks.append('stored user/assistant messages display for the selected conversation and survive reload without mixing')

        page.locator('[data-conversation="'+empty['id']+'"]').click()
        expect(page.locator('.chat-welcome')).to_contain_text('此会话暂无消息')
        expect(page.locator('.history-empty-link')).to_be_visible()
        page.locator('.history-empty-link').click()
        expect(page.locator('.conversation-history')).to_be_visible()
        expect(page.locator('.history-heading')).to_contain_text('1 次计算')
        expect(page.locator('.history-heading')).to_contain_text('1 份文件')
        expect(page.locator('.message')).to_have_count(0)
        page.locator('.history-output > summary').click()
        expect(page.locator('.history-result')).to_contain_text('200000')
        page.locator('.history-files > summary').click()
        page.locator('.history-file-list button').first.click()
        expect(page.frame_locator('#preview-frame').locator('body')).to_contain_text('100 kPa')
        page.locator('[data-close="preview-dialog"]').click()
        page.screenshot(path=str(OUT/'recovered-project-records.png'),full_page=True)
        checks.append('historical calculations/files are visible and previewable without inventing AI messages; empty chat offers history navigation')

        page.locator('[data-conversation="'+a['id']+'"]').click()
        page.locator('[data-page="tools"]').click()
        page.locator('#tool-picker').select_option('convert_units')
        page.locator('#tool-form input[name="value"]').fill('3')
        page.locator('#calculate-button').click()
        expect(page.locator('#tool-result')).to_contain_text('300000')
        page.locator('[data-page="workspace"]').click()
        expect(page.locator('.history-heading')).to_contain_text('1 次计算')
        expect(page.locator('.message-user')).to_contain_text('工况 A')
        page.locator('[data-conversation="'+b['id']+'"]').click()
        expect(page.locator('.history-record')).to_have_count(0)
        checks.append('new manual tool results remain in the active conversation alongside its real chat history')
        page.set_viewport_size({'width':390,'height':844})
        expect(page.locator('.message-user')).to_contain_text('设备 B')
        assert page.evaluate('document.documentElement.scrollWidth <= innerWidth')
        box=page.locator('#send-button').bounding_box()
        assert box['y']+box['height']<844
        checks.append('mobile transcript and composer remain visible')

        # Read-only verification of the exact project named in the user's screenshot.
        page.set_viewport_size({'width':1278,'height':1012})
        page.goto('http://127.0.0.1:8000')
        expect(page.locator('#chat-form')).to_be_visible(timeout=30000)
        page.locator('[data-project="43176d352b814bbc91989a9f9fd84b1b"]').click()
        page.locator('[data-conversation="history-43176d352b814bbc91989a9f9fd84b1b"]').click()
        expect(page.locator('.history-heading')).to_contain_text('3 次计算 · 30 份文件')
        expect(page.locator('.history-record')).to_have_count(3)
        page.locator('.history-output > summary').first.click()
        expect(page.locator('.history-result').first).to_contain_text('气相平衡')
        page.screenshot(path=str(OUT/'original-cantera-history.png'),full_page=True)
        checks.append('original Cantera project displays its 3 stored calculations and 30 files')
        assert not errors,errors
        browser.close()
    report={'passed':True,'checks':checks,'page_errors':errors,'external_model_calls':0}
    (OUT/'results.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps(report,ensure_ascii=False))


if __name__=='__main__':
    main()
