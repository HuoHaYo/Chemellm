"""Exercise gas equilibrium/reactor controls, plots and native downloads in Edge."""
import json
import time
import zipfile
from pathlib import Path

from playwright.sync_api import expect, sync_playwright

OUT=Path(__file__).resolve().parent.parent/"data/qa"


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
        name="Cantera界面验证 · "+str(time.time_ns())
        page.locator('#new-project-form input[name="name"]').fill(name)
        page.locator("#new-project-form button").click()
        expect(page.locator("#project-name")).to_have_text(name)
        expect(page.locator("#form-dialog")).not_to_be_visible()
        page.locator('[data-page="tools"]').click()
        page.locator("#tool-picker").select_option("cantera_equilibrium")
        form=page.locator("#tool-form")
        expect(form.locator('select[name="mechanism"]')).to_have_value("wgs4")
        expect(form.locator('select[name="constraint"]')).to_have_value("TP")
        expect(form).to_contain_text("物种相对摩尔量")
        page.locator("#calculate-button").click()
        expect(page.locator("[data-cantera-species] tbody tr")).to_have_count(4,timeout=30000)
        expect(page.locator("[data-cantera-summary]")).to_contain_text("气相平衡")
        expect(page.locator("[data-cantera-summary]")).to_contain_text("一致性检查通过")
        page.screenshot(path=str(OUT/"cantera-equilibrium.png"),full_page=True)
        with page.expect_download() as download_info:
            page.locator("[data-native-download]").click()
        download=download_info.value
        assert download.failure() is None
        target=OUT/"cantera-browser-native.zip";download.save_as(target)
        with zipfile.ZipFile(target) as archive:
            assert {"mechanism.yaml","simulation.py","input.json","result.json"}<=set(archive.namelist())
        form.locator('textarea[name="composition"]').fill('{"CO":1,"CH4":1}')
        page.locator("#calculate-button").click()
        expect(page.locator("#tool-result .inline-error")).to_contain_text("CH4",timeout=20000)
        page.locator("#tool-picker").select_option("cantera_reactor")
        form=page.locator("#tool-form")
        expect(form.locator('select[name="constraint"]')).to_have_value("constant_pressure")
        expect(form.locator('select[name="energy"]')).to_have_value("adiabatic")
        form.locator('input[name="samples"]').fill("40")
        page.locator("#calculate-button").click()
        expect(page.locator("[data-cantera-summary]")).to_contain_text("有限时间积分",timeout=30000)
        expect(page.locator("[data-cantera-summary]")).to_contain_text("2665.62")
        expect(page.locator(".dataset-plot")).to_be_visible()
        page.wait_for_function("document.querySelector('.dataset-plot')?.complete && document.querySelector('.dataset-plot')?.naturalWidth > 0")
        assert page.locator('[data-cantera-summary] a[download]').count()==6
        page.screenshot(path=str(OUT/"cantera-reactor.png"),full_page=True)
        form.locator('select[name="constraint"]').select_option("constant_volume")
        form.locator('select[name="energy"]').select_option("isothermal")
        with page.expect_response(lambda response:"/tools/cantera_reactor" in response.url and response.request.method=="POST") as response_info:
            page.locator("#calculate-button").click()
        assert response_info.value.status==200
        expect(page.locator("[data-cantera-summary]")).to_contain_text("1001.00",timeout=30000)
        page.set_viewport_size({"width":390,"height":844})
        page.screenshot(path=str(OUT/"cantera-mobile.png"),full_page=True)
        assert page.evaluate("document.documentElement.scrollWidth <= innerWidth"),"mobile overflow"
        assert not errors,errors
        browser.close()
    report={"passed":True,"browser":"Microsoft Edge headless","errors":errors,
            "checks":["mechanism and constraint selectors","WGS species table","actual native ZIP download",
                      "unknown species error","adiabatic reactor result","rendered trajectory SVG",
                      "CSV/PDF/YAML/JSON downloads","constant volume/isothermal selectors","mobile390"]}
    (OUT/"cantera-browser-results.json").write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding="utf-8")
    print(json.dumps(report,ensure_ascii=False))


if __name__=="__main__":main()
