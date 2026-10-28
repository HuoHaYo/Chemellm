"""Verify the redesigned workspace against a local service, using isolated QA data.

Start the service with CHEMELLM_DATA_DIR pointing at output/playwright/redesign-data.
Chat fixtures only check browser behavior; calculations, files and project APIs are real.
"""
import argparse
import json
import time
from pathlib import Path

from playwright.sync_api import expect, sync_playwright

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "output" / "playwright" / "frontend-redesign"


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--capture-only", action="store_true")
    args = parser.parse_args()
    OUT.mkdir(parents=True, exist_ok=True)
    checks = []
    with sync_playwright() as p:
        browser = p.chromium.launch(channel="msedge", headless=True)
        page = browser.new_page(viewport={"width": 1440, "height": 960}, reduced_motion="reduce")
        errors, failed_resources = [], []
        page.on("pageerror", lambda error: errors.append(str(error)))
        page.on("response", lambda response: failed_resources.append(response.url) if response.status >= 400 and "/api/" not in response.url else None)
        page.goto("http://127.0.0.1:8000")
        expect(page.locator("#chat-form")).to_be_visible(timeout=30000)
        page.screenshot(path=str(OUT / "workspace-desktop.png"), full_page=True)
        if args.capture_only:
            print(json.dumps({"capture": str(OUT / "workspace-desktop.png"), "errors": errors}, ensure_ascii=False))
            browser.close()
            return

        project_name = "苯乙烯清洁生产 · 界面验收"
        page.locator("#new-project").click()
        page.locator('#new-project-form input[name="name"]').fill(project_name)
        page.locator("#new-project-form button").click()
        expect(page.locator("#project-name")).to_have_text(project_name)
        expect(page.locator(".chat-welcome")).to_be_visible()
        project_id = page.locator("#project-select").input_value()
        expect(page.locator("#send-button")).to_be_disabled()
        assert page.locator("main .metric").count() == 0
        checks.append("new project opens a focused conversation")
        page.screenshot(path=str(OUT / "workspace-desktop.png"), full_page=True)

        field = page.locator('#chat-form textarea')
        field.fill("请检查物料衡算的设计依据")
        expect(page.locator("#send-button")).to_be_enabled()
        page.locator('[data-page="research"]').click()
        expect(page.locator("#research-form")).to_be_visible()
        page.locator('[data-page="workspace"]').click()
        expect(field).to_have_value("请检查物料衡算的设计依据")
        page.reload()
        expect(field).to_have_value("请检查物料衡算的设计依据")
        field.press("End")
        field.press("Shift+Enter")
        field.press("a")
        expect(field).to_have_value("请检查物料衡算的设计依据\na")
        field.fill("")
        page.locator('[data-prompt]').first.click()
        expect(field).not_to_have_value("")
        checks.append("prompt filling, Shift+Enter and draft restoration after navigation/reload")

        page.locator("#project-overview-button").click()
        expect(page.locator("#project-dialog")).to_be_visible()
        page.locator('#project-dialog [data-action="import"]').click()
        expect(page.locator("#project-dialog .metric").nth(2)).to_contain_text("/ 31", timeout=20000)
        page.screenshot(path=str(OUT / "project-overview.png"), full_page=True)
        page.locator('#project-dialog [data-navigate="acceptance"]').click()
        expect(page.locator("#project-dialog")).not_to_be_visible()
        expect(page.locator("#content tbody tr")).to_have_count(35)
        checks.append("project drawer, real competition import, acceptance navigation")

        page.locator('[data-page="tools"]').click()
        page.locator("#tool-picker").select_option("convert_units")
        page.locator('#tool-form input[name="value"]').fill("2")
        page.locator('#tool-form input[name="from_unit"]').fill("bar")
        page.locator('#tool-form input[name="to_unit"]').fill("Pa")
        page.locator("#calculate-button").click()
        expect(page.locator("#tool-result")).to_contain_text("200000", timeout=20000)
        expect(page.locator(".tool-directory")).not_to_have_attribute("open", "")
        page.locator(".tool-directory > summary").click()
        expect(page.locator(".catalog")).to_be_visible()
        page.locator(".tool-directory > summary").click()
        page.screenshot(path=str(OUT / "tools-desktop.png"), full_page=True)
        checks.append("real unit conversion and collapsed tool directory")

        page.locator('[data-page="files"]').click()
        page.locator("#upload").set_input_files({"name": "界面验收说明.txt", "mimeType": "text/plain", "buffer": "界面验收资料：独立文件上传与预览。".encode()})
        card = page.locator(".file-card").filter(has_text="界面验收说明.txt")
        expect(card).to_be_visible(timeout=20000)
        card.get_by_role("button", name="打开预览").click()
        expect(page.locator("#preview-dialog")).to_be_visible()
        expect(page.frame_locator("#preview-frame").locator("body")).to_contain_text("独立文件上传与预览")
        page.locator('[data-close="preview-dialog"]').click()
        page.screenshot(path=str(OUT / "files-desktop.png"), full_page=True)
        checks.append("real file upload, ingestion and preview")

        for name, selector in [("research", "#research-form"), ("evidence", "#evidence-workspace"), ("datasets", "#dataset-picker"), ("study", "#study-workspace"), ("database", "#equipment-panel"), ("acceptance", "table")]:
            page.locator('#sidebar [data-page="' + name + '"]').click()
            expect(page.locator(selector).first).to_be_visible(timeout=20000)
            expect(page.locator('#sidebar [aria-current="page"]')).to_have_count(1)
            assert page.evaluate("document.documentElement.scrollWidth <= innerWidth"), name + " desktop overflow"
        checks.append("all nine page destinations and active navigation state")

        page.locator('[data-page="workspace"]').click()
        expect(field).not_to_have_value("")
        first_draft = field.input_value()
        page.locator("#new-project").click()
        page.locator('#new-project-form input[name="name"]').fill("独立草稿验证 · " + str(time.time_ns()))
        page.locator("#new-project-form button").click()
        expect(field).to_have_value("")
        field.fill("第二个项目的草稿")
        page.locator("#project-select").select_option(project_id)
        expect(field).to_have_value(first_draft)
        checks.append("drafts remain isolated between projects")

        page.locator("#sidebar-close").click()
        expect(page.locator("#sidebar-toggle")).to_be_visible()
        assert page.locator("#sidebar").evaluate("el => el.inert")
        page.reload()
        expect(field).to_be_visible()
        expect(page.locator("#sidebar-toggle")).to_have_attribute("aria-expanded", "false")
        page.screenshot(path=str(OUT / "workspace-collapsed.png"), full_page=True)
        page.locator("#sidebar-toggle").click()
        expect(page.locator("#sidebar-toggle")).not_to_be_visible()
        checks.append("desktop sidebar collapse persists after reload")

        for width, height in [(1024, 768), (768, 1024), (390, 844), (320, 640), (844, 390), (390, 450)]:
            page.set_viewport_size({"width": width, "height": height})
            expect(field).to_be_visible()
            assert page.evaluate("document.documentElement.scrollWidth <= innerWidth"), f"{width}px overflow"
            box = page.locator("#send-button").bounding_box()
            assert box and box["y"] + box["height"] < height, f"{width}px send button clipped"
            if width <= 760:
                expect(page.locator("#sidebar-toggle")).to_have_attribute("aria-expanded", "false")
                page.locator("#sidebar-toggle").click()
                expect(page.locator("#sidebar-toggle")).to_have_attribute("aria-expanded", "true")
                assert page.locator(".shell").evaluate("el => el.inert")
                page.locator("#settings-button").focus()
                page.keyboard.press("Tab")
                expect(page.locator(".brand")).to_be_focused()
                page.keyboard.press("Escape")
                expect(page.locator("#sidebar-toggle")).to_be_focused()
                assert page.locator("#sidebar").evaluate("el => el.inert")
                page.locator("#sidebar-toggle").click()
                page.locator('#sidebar [data-page="tools"]').click()
                expect(page.locator("#tool-form")).to_be_visible()
                assert not page.locator(".shell").evaluate("el => el.inert")
                assert page.evaluate("document.documentElement.scrollWidth <= innerWidth")
                page.locator("#sidebar-toggle").click()
                page.locator('#sidebar [data-page="workspace"]').click()
                page.screenshot(path=str(OUT / f"workspace-{width}.png"), full_page=True)
        checks.append("1024/768/390/320 layouts, landscape/short windows, mobile navigation, focus trap, Escape and usable composer")

        page.set_viewport_size({"width": 1440, "height": 960})
        page.locator("#settings-button").click()
        expect(page.locator("#form-dialog")).to_be_visible()
        expect(page.locator("#form-body")).to_contain_text("MODEL_PROVIDER")
        page.keyboard.press("Escape")
        checks.append("configuration dialog remains available")

        # Deterministic browser fixtures avoid calling a paid/external model.
        messages = []
        submitted = []
        run = {"id": "ui-fixture-run", "status": "completed", "unknown_calls": [], "events": [], "result": {"iterations": 1}}

        def runs_route(route):
            if route.request.method == "POST":
                payload = route.request.post_data_json
                submitted.append(payload)
                messages.extend([{"role": "user", "content": payload["message"]}, {"role": "assistant", "content": "已记录研究需求。\n以下为界面测试回复，尚需工程校核。"}])
                route.fulfill(json=run)
            else:
                route.fulfill(json=[run] if submitted else [])

        page.route("**/api/projects/*/messages", lambda route: route.fulfill(json=messages))
        page.route("**/api/projects/*/runs", runs_route)
        page.route("**/api/runs/ui-fixture-run", lambda route: route.fulfill(json=run))
        field.fill("物料衡算界面交互验证")
        page.locator('#chat-form select[name="speed"]').select_option("deep")
        field.press("Enter")
        expect(page.locator(".message-user")).to_contain_text("物料衡算界面交互验证")
        expect(page.locator(".message-assistant")).to_contain_text("界面测试回复")
        expect(field).to_have_value("")
        expect(page.locator('#chat-form select[name="speed"]')).to_have_value("deep")
        expect(page.locator("#send-button")).to_be_disabled()
        assert len(submitted) == 1 and submitted[0]["speed"] == "deep"
        page.screenshot(path=str(OUT / "conversation-desktop.png"), full_page=True)
        field.fill("第二轮界面验证")
        page.locator("#send-button").click()
        expect(page.locator(".message-user")).to_have_count(2)
        checks.append("fixture conversation: Enter/click submission, transcript, polling and model choice retention")

        messages[-1]["content"] = "长对话可读性与滚动验证。\n" * 100
        page.reload()
        expect(page.locator(".message-assistant").last).to_contain_text("长对话可读性")
        assert page.locator("#conversation-scroll").evaluate("el => el.scrollHeight > el.clientHeight")
        assert page.evaluate("document.documentElement.scrollHeight <= innerHeight + 1"), "transcript escaped its scroll container"
        page.set_viewport_size({"width": 390, "height": 844})
        box = page.locator("#send-button").bounding_box()
        assert box and box["y"] + box["height"] < 844
        page.screenshot(path=str(OUT / "conversation-mobile.png"), full_page=True)
        page.set_viewport_size({"width": 1440, "height": 960})
        checks.append("long transcripts scroll independently and retain a visible composer on mobile")

        # A pending run must remain locked after the POST finally block.
        run["status"] = "running"
        field.fill("忙碌状态测试")
        field.press("Enter")
        expect(page.locator("#run-panel")).to_contain_text("执行中")
        field.fill("运行中不可重复发送")
        expect(page.locator("#send-button")).to_be_disabled()
        field.press("Enter")
        assert len(submitted) == 3
        checks.append("busy run prevents duplicate submission")

        run["status"] = "completed"
        run["unknown_calls"] = [{"id": "unknown-1", "tool": "convert_units", "input": {}, "candidate_calculations": []}]
        page.reload()
        expect(page.locator("[data-run-reconcile]")).to_be_visible()
        field.fill("未知调用结果核对前不可发送")
        expect(page.locator("#send-button")).to_be_disabled()
        page.locator("[data-run-reconcile]").click()
        expect(page.locator("#run-reconcile-form")).to_be_visible()
        page.keyboard.press("Escape")
        checks.append("unknown tool result retains recovery controls and send lock")

        assert not errors, errors
        assert not failed_resources, failed_resources
        browser.close()
    result = {"passed": True, "browser": "Microsoft Edge headless", "checks": checks, "page_errors": errors, "failed_static_resources": failed_resources, "chat_validation": "deterministic browser fixtures; no external model call"}
    (OUT / "results.json").write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(result, ensure_ascii=False))


if __name__ == "__main__":
    main()
