"""Real browser search and OA import against the local service; no route mocks."""
import json
import time
from pathlib import Path

from playwright.sync_api import sync_playwright, expect

ROOT=Path(__file__).resolve().parent.parent
OUT=ROOT/"data"/"qa"


def main():
    OUT.mkdir(parents=True,exist_ok=True)
    with sync_playwright() as playwright:
        browser=playwright.chromium.launch(channel="msedge",headless=True)
        page=browser.new_page(viewport={"width":1440,"height":1080})
        errors=[];page.on("pageerror",lambda error:errors.append(str(error)))
        page.goto("http://127.0.0.1:8000")
        expect(page.locator("#chat-form")).to_be_visible()
        page.locator("#new-project").click()
        name="开放全文真实联网浏览器QA · "+str(time.time_ns())
        page.locator('#new-project-form input[name="name"]').fill(name)
        page.locator("#new-project-form button").click()
        expect(page.locator("#project-name")).to_have_text(name)
        expect(page.locator("#form-dialog")).not_to_be_visible()
        project_id=page.evaluate("localStorage.getItem('chemellm-project')")
        page.locator('[data-page="research"]').click()
        form=page.locator("#research-form")
        form.locator('[name="source"]').select_option("open_literature_search")
        form.locator('[name="query"]').fill("PMCID:PMC10110988")
        form.locator("button").click()
        expect(page.locator('[data-import-pmc="PMC10110988"]')).to_have_count(1,timeout=40000)
        expect(page.locator("#research-results")).to_contain_text("10.3389/fmicb.2023.1150102")
        page.screenshot(path=str(OUT/"fulltext-live-search.png"))
        page.locator('[data-import-pmc="PMC10110988"]').click()
        form=page.locator("#fulltext-import-form")
        expect(form.locator('[name="pmcid"]')).to_have_value("PMC10110988")
        with page.expect_response(lambda r:r.url.endswith('/tools/fulltext_import') and r.request.method=='POST',timeout=80000) as pending:
            form.locator("button").click()
        response=pending.value
        assert response.ok, response.text()
        imported=response.json()
        expect(page.locator(".document-block")).to_have_count(20,timeout=20000)
        expect(page.locator("#reader-pages")).to_contain_text("117")
        expect(page.locator("#evidence-notice")).to_contain_text("开放全文已导入")
        expect(page.locator('#document-extract-form [name="artifact_id"] option')).to_have_count(1)
        expect(page.locator('#document-extract-form [name="artifact_id"]')).to_have_value(imported['artifact']['id'])
        assert imported['artifact']['metadata']['fulltext_source']['open_access_metadata']=='Y'
        assert imported['extraction']['blocks']==117
        page.screenshot(path=str(OUT/"fulltext-live-import.png"))
        assert not errors,errors
        browser.close()
    report={"passed":True,"project_id":project_id,"errors":errors,"browser":"Microsoft Edge headless",
            "search":"real Europe PMC PMCID search via service", "import":imported,
            "scope":"actual metadata/search/fulltext service and browser; not scientific review or LLM evaluation"}
    (OUT/"fulltext-browser-network-results.json").write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps({"passed":True,"project_id":project_id,"blocks":imported['extraction']['blocks'],"errors":errors}))


if __name__=='__main__':main()
