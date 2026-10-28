"""Real Edge UI checks for source import, model comparison and XLSX input."""
import io
import json
import time
from pathlib import Path

from openpyxl import Workbook
from playwright.sync_api import sync_playwright, expect

OUT=Path(__file__).resolve().parent.parent/"data"/"qa"


def main():
    OUT.mkdir(parents=True,exist_ok=True)
    with sync_playwright() as playwright:
        browser=playwright.chromium.launch(channel="msedge",headless=True)
        page=browser.new_page(viewport={"width":1440,"height":1080})
        errors=[]
        page.on("pageerror",lambda error:errors.append(str(error)))
        page.goto("http://127.0.0.1:8000")
        expect(page.locator("#chat-form")).to_be_visible()
        page.locator("#new-project").click()
        project_name="实验数据界面验证 · "+str(time.time_ns())
        page.locator('#new-project-form input[name="name"]').fill(project_name)
        page.locator("#new-project-form button").click()
        expect(page.locator("#project-name")).to_have_text(project_name)
        expect(page.locator("#form-dialog")).not_to_be_visible()
        page.locator('[data-page="datasets"]').click()
        page.locator('[data-dataset-example="BoxBOD"]').click()
        form=page.locator("#dataset-form")
        expect(form).to_be_visible(timeout=30000)
        expect(page.locator("#dataset-sheet-field")).not_to_be_visible()
        expect(form.locator('[name="x_unit"]')).to_have_value("day")
        expect(form.locator('[name="y_unit"]')).to_have_value("mg/liter")
        form.locator("button").click()
        expect(page.locator("[data-model-comparison] tbody tr")).to_have_count(2,timeout=45000)
        expect(page.locator("[data-fit-parameters]")).to_have_count(2)
        expect(page.locator("#dataset-result")).to_contain_text("213.809")
        expect(page.locator(".dataset-plot")).to_be_visible()
        assert page.locator(".dataset-plot").evaluate("img => img.complete && img.naturalWidth > 0")
        assert page.locator('#dataset-result a[download]').count()==4
        page.screenshot(path=str(OUT/"experimental-analysis.png"),full_page=True)
        book=Workbook();book.active.title="Measurements"
        book.active.append(["time","concentration"])
        for row in [(0,10),(1,8.2),(2,6.7),(3,5.5),(4,4.5)]:book.active.append(row)
        stream=io.BytesIO();book.save(stream)
        page.locator("#upload").set_input_files({"name":"experimental-QA.xlsx","mimeType":"application/vnd.openxmlformats-officedocument.spreadsheetml.sheet","buffer":stream.getvalue()})
        expect(page.locator("#dataset-picker option").filter(has_text="experimental-QA.xlsx")).to_have_count(1,timeout=20000)
        expect(page.locator("#dataset-sheet")).to_have_value("Measurements")
        expect(page.locator("#dataset-sheet-field")).to_be_visible()
        form=page.locator("#dataset-form")
        form.locator('[name="x_unit"]').fill("s")
        form.locator('[name="y_unit"]').fill("mol/liter")
        form.locator('[name="models"][value="first_order_uptake"]').uncheck()
        form.locator('[name="models"][value="first_order_decay"]').check()
        form.locator("button").click()
        expect(page.locator("[data-model-comparison] tbody tr")).to_have_count(2,timeout=30000)
        expect(page.locator("#dataset-result")).to_contain_text("一级衰减")
        page.set_viewport_size({"width":390,"height":844})
        page.screenshot(path=str(OUT/"experimental-mobile.png"),full_page=True)
        assert page.evaluate("document.documentElement.scrollWidth <= window.innerWidth"),"mobile overflow"
        assert not errors,errors
        browser.close()
    report={"passed":True,"browser":"Microsoft Edge headless","errors":errors,"checks":["NIST import and source units","two-model comparison","parameters and local intervals","rendered SVG","four downloads","XLSX upload/sheet","decay model","mobile width"]}
    (OUT/"experimental-browser-results.json").write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding="utf-8")
    print(json.dumps(report,ensure_ascii=False))


if __name__=="__main__":main()
