"""Real UI evidence workflow; test reviews do not approve scientific conclusions."""
import json
import time
import io
from pathlib import Path
from urllib.parse import urljoin

from playwright.sync_api import sync_playwright, expect
from PIL import Image, ImageDraw, ImageFont
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader

ROOT=Path(__file__).resolve().parent.parent
OUT=ROOT/"data"/"qa"


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
        name="全文证据界面QA · "+str(time.time_ns())
        page.locator('#new-project-form input[name="name"]').fill(name)
        page.locator("#new-project-form button").click()
        expect(page.locator("#project-name")).to_have_text(name)
        expect(page.locator("#form-dialog")).not_to_be_visible()
        page.locator('[data-page="evidence"]').click()
        page.locator("#upload").set_input_files(str(ROOT/"docs/sources/fulltext/PMC10110988.xml"))
        form=page.locator("#document-extract-form")
        expect(form.locator('option').filter(has_text="PMC10110988.xml")).to_have_count(1,timeout=20000)
        form.locator("button").click()
        expect(page.locator(".document-block")).to_have_count(20,timeout=20000)
        expect(page.locator("#reader-pages")).to_contain_text("117")
        page.locator('[data-reader-step="1"]').click()
        expect(page.locator("#reader-pages")).to_contain_text("21–40")
        page.locator('[data-reader-step="-1"]').click()
        expect(page.locator("#reader-pages")).to_contain_text("1–20")
        claim=page.locator("#claim-create-form")
        claim.locator("textarea").fill("此项为界面测试论断：储氢研究需要核对传质模型与试验条件。")
        claim.locator("button").click()
        expect(page.locator(".evidence-claim")).to_have_count(1)
        page.locator("[data-cite-block]").first.click()
        quote=page.locator("#quote-form")
        original=quote.locator('[name="quote"]').input_value()
        quote.locator('[name="quote"]').fill("This fabricated quotation must be rejected by the source check.")
        quote.locator("button").click()
        expect(page.locator("#evidence-notice .inline-error")).to_be_visible()
        expect(page.locator(".evidence-quote")).to_have_count(0)
        quote.locator('[name="quote"]').fill(original)
        quote.locator('[name="conditions"]').fill("界面QA仅验证记录工作流；不构成科学审核。")
        quote.locator("button").click()
        expect(page.locator(".evidence-quote")).to_have_count(1)
        expect(page.locator(".evidence-claim .pill")).to_contain_text("v2 · 待人工审核")
        review=page.locator(".claim-review-form")
        review.locator("xpath=..").locator("summary").click()
        review.locator('[name="reviewer"]').fill("界面QA自动测试")
        review.locator('[name="notes"]').fill("仅验证审核保存及版本门槛，不代表实际专家审核或科学支持。")
        review.locator("button").click()
        expect(page.locator(".evidence-claim .pill")).to_contain_text("人工判断：证据不足")
        edit=page.locator(".claim-edit-form")
        edit.locator("xpath=..").locator("summary").click()
        edit.locator("textarea").fill("修改后的界面测试论断：储氢传质模型必须结合试验条件核对。")
        edit.locator("button").click()
        expect(page.locator(".evidence-claim .pill")).to_contain_text("v3 · 待人工审核")
        expect(page.locator(".evidence-claim")).to_contain_text("修改后的界面测试论断")
        page.locator("#evidence-export").click()
        expect(page.locator('#evidence-notice a[download]')).to_have_count(4,timeout=20000)
        for link in page.locator('#evidence-notice a[download]').all():
            response=page.request.get(urljoin(page.url,link.get_attribute("href")))
            assert response.ok and len(response.body())>100
        page.screenshot(path=str(OUT/"evidence-workspace.png"),full_page=True)
        page.set_viewport_size({"width":390,"height":844})
        page.screenshot(path=str(OUT/"evidence-mobile.png"),full_page=True)
        assert page.evaluate("document.documentElement.scrollWidth <= window.innerWidth"),"mobile overflow"
        page.set_viewport_size({"width":1440,"height":1080})
        image=Image.new("RGB",(1400,360),"white")
        font=ImageFont.truetype("C:/Windows/Fonts/arial.ttf" if __import__('os').name=="nt" else "DejaVuSans.ttf",52)
        draw=ImageDraw.Draw(image)
        draw.text((40,70),"Hydrogen pressure = 100 kPa",font=font,fill="black")
        draw.text((40,180),"Temperature = 300 K",font=font,fill="black")
        image.save(OUT/"vision-controlled-original.png")
        stream=io.BytesIO();pdf=canvas.Canvas(stream,pagesize=(700,180))
        pdf.drawImage(ImageReader(image),0,0,width=700,height=180);pdf.save()
        (OUT/"vision-controlled-scan.pdf").write_bytes(stream.getvalue())
        page.locator("#upload").set_input_files(str(OUT/"vision-controlled-scan.pdf"))
        form=page.locator("#document-extract-form")
        expect(form.locator('option').filter(has_text="vision-controlled-scan.pdf")).to_have_count(1,timeout=20000)
        form.locator('[name="artifact_id"]').select_option(label="vision-controlled-scan.pdf")
        form.locator('[name="image_mode"]').select_option("native")
        form.locator("button").click()
        expect(page.locator("#document-reader")).to_contain_text("没有可提取的原生文本",timeout=30000)
        expect(page.locator(".document-block")).to_have_count(0)
        page.screenshot(path=str(OUT/"vision-native-only-workspace.png"),full_page=True)
        page.set_viewport_size({"width":390,"height":844})
        page.screenshot(path=str(OUT/"vision-native-only-mobile.png"))
        assert page.evaluate("document.documentElement.scrollWidth <= window.innerWidth"),"vision mobile overflow"
        assert not errors,errors
        browser.close()
    report={"passed":True,"browser":"Microsoft Edge headless","errors":errors,
            "checks":["real archived JATS upload/extraction","117 blocks and pagination","claim creation",
                      "fabricated quote rejected","literal quote accepted without scientific approval",
                      "test review saved","claim edit invalidates old review","four actual downloads","390px width",
                      "scanned PDF retained without OCR fallback"],
            "vision":{"ai_capability_tested":False,"native_only_mode_retained_original":True},
            "scope":"UI and native extraction only; AI visual capability is not tested by this browser smoke"}
    (OUT/"evidence-browser-results.json").write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding="utf-8")
    print(json.dumps(report,ensure_ascii=False))


if __name__=="__main__":main()
