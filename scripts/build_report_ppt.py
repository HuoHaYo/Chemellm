"""Build the 2026-10-26 progress-report deck with python-pptx."""

from __future__ import annotations

from pathlib import Path

from PIL import Image
from pptx import Presentation
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_SHAPE
from pptx.enum.text import MSO_ANCHOR, PP_ALIGN
from pptx.util import Inches, Pt

ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "docs" / "assets"
OUT = ROOT / "docs" / "汇报_化工智能助手_20261026.pptx"

FONT = "Microsoft YaHei"
NAVY = RGBColor(0x0B, 0x22, 0x39)
NAVY2 = RGBColor(0x15, 0x32, 0x4D)
TEAL = RGBColor(0x1F, 0x9E, 0x8F)
TEAL_L = RGBColor(0xE3, 0xF2, 0xEF)
AMBER = RGBColor(0xE8, 0xA3, 0x3D)
AMBER_L = RGBColor(0xFD, 0xF1, 0xDE)
LIGHT = RGBColor(0xF5, 0xF7, 0xF9)
WHITE = RGBColor(0xFF, 0xFF, 0xFF)
INK = RGBColor(0x1B, 0x2B, 0x3A)
GRAY = RGBColor(0x61, 0x72, 0x80)
GRAY_L = RGBColor(0xE3, 0xE8, 0xEC)
RED = RGBColor(0xC0, 0x50, 0x4D)
GREEN = RGBColor(0x2E, 0x7D, 0x5B)

W, H = 13.333, 7.5


def set_bg(slide, color):
    fill = slide.background.fill
    fill.solid()
    fill.fore_color.rgb = color


def textbox(slide, x, y, w, h, text, size=14, color=INK, bold=False,
            align=PP_ALIGN.LEFT, line=1.0, anchor=MSO_ANCHOR.TOP):
    box = slide.shapes.add_textbox(Inches(x), Inches(y), Inches(w), Inches(h))
    frame = box.text_frame
    frame.word_wrap = True
    frame.margin_left = 0
    frame.margin_right = 0
    frame.margin_top = 0
    frame.margin_bottom = 0
    frame.vertical_anchor = anchor
    paragraph = frame.paragraphs[0]
    paragraph.alignment = align
    paragraph.line_spacing = line
    run = paragraph.add_run()
    run.text = text
    run.font.name = FONT
    run.font.size = Pt(size)
    run.font.bold = bold
    run.font.color.rgb = color
    return box


def bullets(slide, x, y, w, h, items, size=13, color=INK, space=6, bullet_color=None):
    box = slide.shapes.add_textbox(Inches(x), Inches(y), Inches(w), Inches(h))
    frame = box.text_frame
    frame.word_wrap = True
    frame.margin_left = 0
    frame.margin_right = 0
    frame.margin_top = 0
    frame.margin_bottom = 0
    for index, item in enumerate(items):
        paragraph = frame.paragraphs[0] if index == 0 else frame.add_paragraph()
        paragraph.space_after = Pt(space)
        paragraph.line_spacing = 1.05
        mark = paragraph.add_run()
        mark.text = "• "
        mark.font.name = FONT
        mark.font.size = Pt(size)
        mark.font.color.rgb = bullet_color or TEAL
        run = paragraph.add_run()
        run.text = item
        run.font.name = FONT
        run.font.size = Pt(size)
        run.font.color.rgb = color
    return box


def rect(slide, x, y, w, h, fill=None, line=None, radius=False, line_width=0.75):
    shape_type = MSO_SHAPE.ROUNDED_RECTANGLE if radius else MSO_SHAPE.RECTANGLE
    shape = slide.shapes.add_shape(shape_type, Inches(x), Inches(y), Inches(w), Inches(h))
    if fill is None:
        shape.fill.background()
    else:
        shape.fill.solid()
        shape.fill.fore_color.rgb = fill
    if line is None:
        shape.line.fill.background()
    else:
        shape.line.color.rgb = line
        shape.line.width = Pt(line_width)
    if radius:
        try:
            shape.adjustments[0] = 0.08
        except Exception:
            pass
    return shape


def line(slide, x1, y1, x2, y2, color=GRAY_L, width=1.0):
    connector = slide.shapes.add_connector(1, Inches(x1), Inches(y1), Inches(x2), Inches(y2))
    connector.line.color.rgb = color
    connector.line.width = Pt(width)
    return connector


def arrow(slide, x, y, w, h, color=TEAL):
    shape = slide.shapes.add_shape(MSO_SHAPE.RIGHT_ARROW, Inches(x), Inches(y), Inches(w), Inches(h))
    shape.fill.solid()
    shape.fill.fore_color.rgb = color
    shape.line.fill.background()
    return shape


def add_title(slide, kicker, title, subtitle=None):
    textbox(slide, 0.7, 0.42, 8.0, 0.3, kicker.upper(), 10.5, TEAL, True)
    textbox(slide, 0.7, 0.68, 11.8, 0.55, title, 25, NAVY, True)
    line(slide, 0.7, 1.28, 12.6, 1.28, GRAY_L, 1.0)
    if subtitle:
        textbox(slide, 0.7, 1.38, 11.9, 0.4, subtitle, 11.5, GRAY)


def add_footer(slide, number):
    textbox(slide, 0.7, 7.02, 8.0, 0.25, "化工特化智能助手 · 阶段进展汇报　2026-10-26", 8.5, GRAY)
    textbox(slide, 11.9, 7.02, 0.8, 0.25, f"{number:02d}", 9, GRAY, align=PP_ALIGN.RIGHT)


def card(slide, x, y, w, h, title, body, accent=TEAL, fill=WHITE):
    rect(slide, x, y, w, h, fill=fill, line=GRAY_L, radius=True)
    rect(slide, x, y, 0.07, h, fill=accent, line=None)
    textbox(slide, x + 0.22, y + 0.16, w - 0.4, 0.3, title, 12.5, NAVY, True)
    textbox(slide, x + 0.22, y + 0.5, w - 0.4, h - 0.6, body, 10.2, GRAY, line=1.08)


def number_card(slide, x, y, w, h, number, label, accent=TEAL):
    rect(slide, x, y, w, h, fill=WHITE, line=GRAY_L, radius=True)
    textbox(slide, x + 0.2, y + 0.1, w - 0.4, 0.7, number, 30, accent, True)
    textbox(slide, x + 0.2, y + 0.82, w - 0.4, 0.3, label, 10.5, GRAY)


def table(slide, x, y, w, h, headers, rows, col_widths, font_size=9.5,
          header_fill=NAVY, status_col=None):
    shape = slide.shapes.add_table(len(rows) + 1, len(headers), Inches(x), Inches(y), Inches(w), Inches(h))
    tbl = shape.table
    for index, width in enumerate(col_widths):
        tbl.columns[index].width = Inches(width)
    tbl.rows[0].height = Inches(0.36)
    body_row_height = max(0.28, (h - 0.36) / max(len(rows), 1))
    for col, header in enumerate(headers):
        cell = tbl.cell(0, col)
        cell.fill.solid()
        cell.fill.fore_color.rgb = header_fill
        cell.margin_left = Inches(0.06)
        cell.margin_right = Inches(0.05)
        cell.margin_top = Inches(0.03)
        cell.margin_bottom = Inches(0.03)
        cell.vertical_anchor = MSO_ANCHOR.MIDDLE
        paragraph = cell.text_frame.paragraphs[0]
        paragraph.alignment = PP_ALIGN.CENTER if col == 0 else PP_ALIGN.LEFT
        run = paragraph.add_run()
        run.text = header
        run.font.name = FONT
        run.font.size = Pt(font_size)
        run.font.bold = True
        run.font.color.rgb = WHITE
    for row_index, row in enumerate(rows, start=1):
        tbl.rows[row_index].height = Inches(body_row_height)
        for col, value in enumerate(row):
            cell = tbl.cell(row_index, col)
            cell.fill.solid()
            cell.fill.fore_color.rgb = WHITE if row_index % 2 else LIGHT
            cell.margin_left = Inches(0.06)
            cell.margin_right = Inches(0.05)
            cell.margin_top = Inches(0.02)
            cell.margin_bottom = Inches(0.02)
            cell.vertical_anchor = MSO_ANCHOR.MIDDLE
            paragraph = cell.text_frame.paragraphs[0]
            paragraph.alignment = PP_ALIGN.CENTER if col == 0 else PP_ALIGN.LEFT
            run = paragraph.add_run()
            run.text = str(value)
            run.font.name = FONT
            run.font.size = Pt(font_size)
            run.font.color.rgb = INK
            if status_col is not None and col == status_col:
                if "已" in str(value):
                    run.font.color.rgb = GREEN
                elif "未" in str(value) or "调整" in str(value):
                    run.font.color.rgb = RED
                elif "部分" in str(value):
                    run.font.color.rgb = AMBER
                run.font.bold = True
    return tbl


def picture(slide, path, x, y, w, h, border=True):
    if border:
        rect(slide, x - 0.04, y - 0.04, w + 0.08, h + 0.08, fill=WHITE, line=GRAY_L)
    iw, ih = Image.open(path).size
    scale = min(w / iw, h / ih)
    nw, nh = iw * scale, ih * scale
    slide.shapes.add_picture(str(path), Inches(x + (w - nw) / 2), Inches(y + (h - nh) / 2),
                             width=Inches(nw), height=Inches(nh))


def base_slide(prs, number, kicker, title, subtitle=None):
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    set_bg(slide, LIGHT)
    add_title(slide, kicker, title, subtitle)
    add_footer(slide, number)
    return slide


def build():
    prs = Presentation()
    prs.slide_width = Inches(W)
    prs.slide_height = Inches(H)

    # 01 cover
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    set_bg(slide, NAVY)
    rect(slide, 9.1, 0, 4.23, H, fill=NAVY2, line=None)
    rect(slide, 9.1, 0, 0.08, H, fill=TEAL, line=None)
    rect(slide, 9.9, 1.1, 2.4, 0.06, fill=AMBER, line=None)
    rect(slide, 9.9, 1.3, 1.3, 0.06, fill=TEAL, line=None)
    textbox(slide, 0.8, 0.65, 7.5, 0.3, "中国石油大学（华东） · 化学化工学院", 11, RGBColor(0xB9, 0xC7, 0xD4))
    textbox(slide, 0.8, 1.55, 8.1, 1.7, "从云端原型到本地插件", 40, WHITE, True, line=1.0)
    textbox(slide, 0.8, 3.05, 8.1, 0.5, "化工特化智能助手 · 阶段进展汇报", 20, TEAL)
    textbox(slide, 0.8, 3.85, 7.9, 0.9,
            "把“能算”变成“能交付”：一次本地化重构，五项优先工程能力，\n一套可打包带走的 DSH 插件。", 13.5, RGBColor(0xC9, 0xD5, 0xDF), line=1.3)
    line(slide, 0.8, 5.35, 7.9, 5.35, RGBColor(0x3A, 0x55, 0x6E), 1.0)
    textbox(slide, 0.8, 5.55, 4.8, 0.3, "汇报人：霍昊塬　化学工程与工艺 24005 班", 11.5, WHITE)
    textbox(slide, 0.8, 5.95, 4.8, 0.3, "汇报日期：2026 年 10 月 26 日", 11.5, RGBColor(0xB9, 0xC7, 0xD4))
    textbox(slide, 9.9, 6.25, 2.7, 0.5, "v0.1\n3 天冲刺", 13, AMBER, True, line=1.2)

    # 02 executive summary
    slide = base_slide(prs, 2, "01 / 两个三天", "两个三天，把云端原型改造成能带走的本地工作台",
                       "第一个三天：Codex / GPT-6.1sol 做云端原型；第二个三天：DeepSeek 做本地插件与交付。")
    number_card(slide, 0.7, 1.85, 2.4, 1.45, "60", "可执行工具", TEAL)
    number_card(slide, 3.3, 1.85, 2.4, 1.45, "5", "优先能力（内部）", AMBER)
    number_card(slide, 5.9, 1.85, 2.4, 1.45, "55", "唯一文件名（去重后）", NAVY2)
    number_card(slide, 8.5, 1.85, 2.4, 1.45, "2", "已验收案例", GREEN)
    bullets(slide, 0.75, 3.75, 7.55, 2.2, [
        "保留原 ChemELLM 的确定性计算内核（22 类模型），把会话、编排与审批交给 DSH。",
        "新增 P&ID 数据链、设备数据表、安全阀选型、HAZOP/LOPA、合规矩阵五项优先能力。",
        "案例 A 自动校核通过（数据完整性）：35 要求 / 18 成果 / 28 计算；88 个文件按文件名去重后为 55 个唯一文件名（内容重复仅 2 组，其余为不同版本）。",
        "插件带便携 Python 运行时，目标机解压安装、重启 DSH 即可自动拉起内核。",
    ], size=11.4, space=7)
    textbox(slide, 0.75, 6.02, 11.9, 0.3,
            "88 → 55：按文件名去重；内容重复仅 2 组，其余是不同运行版本，仍需清理。核心交付约 15 份（人类可读口径）。",
            8.4, GRAY)
    rect(slide, 8.55, 3.75, 4.05, 2.55, fill=NAVY, line=None, radius=True)
    textbox(slide, 8.8, 3.95, 3.6, 0.3, "一句话", 10.5, TEAL, True)
    textbox(slide, 8.8, 4.3, 3.55, 1.8,
            "原来是一个人守着服务器跑 Web 原型；\n现在是每个学生在自己电脑上，\n用 DSH 把同一个工程闭环跑完。",
            14, WHITE, False, line=1.35)
    rect(slide, 0.7, 6.38, 5.75, 0.45, fill=TEAL_L, line=None, radius=True)
    textbox(slide, 0.85, 6.47, 5.5, 0.3, "第 1 个 3 天｜Codex / GPT-6.1sol：云端原型", 9.2, NAVY, True)
    rect(slide, 6.7, 6.38, 5.75, 0.45, fill=AMBER_L, line=None, radius=True)
    textbox(slide, 6.85, 6.47, 5.5, 0.3, "第 2 个 3 天｜DeepSeek：本地插件 + 五项优先能力", 9.2, NAVY, True)

    # 03 opening goals
    slide = base_slide(prs, 3, "02 / 开题回顾", "开题时，我们想解决的是“普惠”问题",
                       "2026-10-12 开题汇报：贯通基础计算、流程模拟与工艺设计，服务学生与一线工程师。")
    card(slide, 0.7, 1.75, 5.6, 1.85, "总目标",
         "以自然语言为入口，构建“计算—模拟—设计”全链路的化工特化智能助手；\n"
         "结果专业可靠、开源合规、开箱即用，优先服务学生与一线工程师。\n"
         "关键词：自然语言 · 专业可靠 · 开源合规 · 普惠。", TEAL)
    card(slide, 6.55, 1.75, 6.05, 1.85, "要跨过的鸿沟",
         "专业软件：强、贵、难学、绑桌面；通用大模型：会说、不懂化工、算不准。\n"
         "缺的是一个“自然语言可用、结果专业可靠、开箱即用”的入口。\n"
         "结果：要么贵而难，要么会说但算不准。", AMBER)
    textbox(slide, 0.7, 3.9, 3.0, 0.3, "三阶段路线（开题版）", 11, NAVY, True)
    stages = [
        ("近期 0–8 周", "基础计算", "物性、单位、物料/能量衡算\nWeb 对话端上线"),
        ("中期 2–6 月", "流程模拟", "DWSIM 外部模拟（已接）\n闪蒸/精馏/吸收/反应器"),
        ("远期 6–12 月", "工艺设计", "设备选型与计算\nPFD/P&ID、经济优化"),
    ]
    for index, (period, title, body) in enumerate(stages):
        x = 0.7 + index * 4.18
        rect(slide, x, 4.3, 3.85, 1.45, fill=WHITE, line=GRAY_L, radius=True)
        textbox(slide, x + 0.18, 4.42, 1.9, 0.25, period, 9.5, TEAL, True)
        textbox(slide, x + 0.18, 4.68, 3.4, 0.3, title, 13, NAVY, True)
        textbox(slide, x + 0.18, 5.0, 3.45, 0.65, body, 9.8, GRAY, line=1.1)
    textbox(slide, 0.7, 6.15, 11.8, 0.35,
            "开题已完成的可行性验证：7 类基础计算跑通（thermo / CoolProp / Cantera / pint）；DWSIM 自动化已验证（外部加载/求解）。",
            10.2, GRAY)

    # 04 previous cloud prototype
    slide = base_slide(prs, 4, "03 / 第一个 3 天", "第一个 3 天：云端原型",
                       "Codex / GPT-6.1sol 协作，重点是把“化工工具链 + 对话 + Web”先跑通。")
    bullets(slide, 0.75, 1.75, 7.3, 4.1, [
        "中文 Web 端 9 个功能入口 + FastAPI 后端；自研 agent 循环（Function Calling / ReAct）。",
        "22 类确定性计算、证据检索、DOCX/PPTX/PDF/SVG/DXF 生成、Office/PDF 预览、设备参数版本库。",
        "按 2026 赛题登记 35 项要求并逐项验收；成果包附带可复算的 Python 源码。",
        "Docker Compose 部署到阿里云 Linux；HTTPS 未开通、单租户、无多用户隔离。",
    ], size=11.8, space=10)
    number_card(slide, 8.45, 1.8, 2.15, 1.15, "9", "Web 功能入口", TEAL)
    number_card(slide, 10.8, 1.8, 2.15, 1.15, "22", "确定性计算模型", NAVY2)
    number_card(slide, 8.45, 3.12, 2.15, 1.15, "35", "赛题要求", AMBER)
    number_card(slide, 10.8, 3.12, 2.15, 1.15, "3 天", "原型周期", GREEN)
    rect(slide, 8.45, 4.55, 4.5, 1.55, fill=AMBER_L, line=None, radius=True)
    textbox(slide, 8.65, 4.7, 4.1, 0.3, "但旧 README 明确记录：", 10, RED, True)
    textbox(slide, 8.65, 5.0, 4.15, 1.0,
            "赛题全流程仍未通过首轮验收；云端部署、运维、数据合规与成本，成为继续推进的瓶颈。",
            9.8, INK, line=1.15)
    rect(slide, 0.7, 4.55, 7.3, 1.55, fill=NAVY, line=None, radius=True)
    textbox(slide, 0.95, 4.72, 6.8, 0.3, "原型资产已归档 old/", 10.5, TEAL, True)
    textbox(slide, 0.95, 5.05, 6.8, 0.85,
            "app / web / tests / docs / Dockerfile / compose / Linux 验收记录 —— 这些资产没有被丢掉，而是变成了本地内核与插件的基础。",
            10.0, WHITE, line=1.15)

    # 05 why pivot
    slide = base_slide(prs, 5, "04 / 转折", "为什么把“云”换成“本地插件”",
                       "不是否定开题目标，而是先解决当前资源下最要命的五个问题。")
    left = ["部署运维重：Docker / Linux / 域名 / HTTPS / 证书", "数据与合规：云端数据、多租户未做、密钥托管",
            "成本与可用性：学生没有服务器，长期在线成本高", "交互重复：自研 agent 与 DSH 原生会话/审批重叠",
            "维护成本：两套 UI + 自研 agent，长期要人守"]
    right = ["能力下沉：计算内核与工具留在本地，不再依赖云", "交互上移：会话、模型、审批、子代理交给 DSH",
             "数据不出机：data/ 本地项目库 + 哈希清单", "一次安装、换机可部署：便携 Python 运行时",
             "可验证：review / manifest / 阶段门禁都留在本地"]
    rect(slide, 0.7, 1.75, 5.85, 2.95, fill=WHITE, line=GRAY_L, radius=True)
    textbox(slide, 0.95, 1.9, 4.8, 0.3, "原方案的五个瓶颈", 13, RED, True)
    bullets(slide, 0.95, 2.35, 5.3, 2.2, left, size=10.8, space=6, bullet_color=RED)
    rect(slide, 6.85, 1.75, 5.75, 2.95, fill=WHITE, line=GRAY_L, radius=True)
    textbox(slide, 7.1, 1.9, 4.8, 0.3, "这次的五条设计选择", 13, GREEN, True)
    bullets(slide, 7.1, 2.35, 5.25, 2.2, right, size=10.8, space=6, bullet_color=GREEN)
    rect(slide, 3.1, 5.0, 7.1, 0.85, fill=NAVY, line=None, radius=True)
    textbox(slide, 3.3, 5.2, 6.8, 0.4, "能力下沉，交互上移；先可信，再普惠。", 16, WHITE, True, align=PP_ALIGN.CENTER)

    # 06 architecture
    slide = base_slide(prs, 6, "05 / 新架构", "DSH 插件 + 本地内核：三层解耦",
                       "DSH 负责理解与编排，内核负责确定性计算，数据全部留在本机。")
    # top layer
    rect(slide, 0.8, 1.8, 3.3, 1.05, fill=NAVY, line=None, radius=True)
    textbox(slide, 1.0, 1.95, 2.9, 0.3, "DSH Web GUI / 会话", 12.5, WHITE, True)
    textbox(slide, 1.0, 2.3, 2.9, 0.4, "模型 · 审批 · 子代理 · 面板", 9.5, RGBColor(0xC9, 0xD5, 0xDF))
    # host
    rect(slide, 4.75, 1.8, 3.9, 1.05, fill=TEAL, line=None, radius=True)
    textbox(slide, 4.95, 1.95, 3.5, 0.3, "Host 插件 @local/dsh-chemellm", 12, WHITE, True)
    textbox(slide, 4.95, 2.3, 3.5, 0.4, "12 个 chem_* 工具 · 阶段守卫 · 自动拉起", 9.5, WHITE)
    # kernel
    rect(slide, 9.35, 1.8, 3.25, 1.05, fill=NAVY2, line=None, radius=True)
    textbox(slide, 9.55, 1.95, 2.9, 0.3, "本地内核 FastAPI :8765", 12, WHITE, True)
    textbox(slide, 9.55, 2.3, 2.9, 0.4, "60 个可执行工具", 9.5, RGBColor(0xC9, 0xD5, 0xDF))
    for x, w in ((4.12, 0.55), (8.72, 0.55)):
        arrow(slide, x, 2.18, w, 0.3, color=GRAY)
    # kernel contents
    rect(slide, 0.8, 3.2, 11.8, 2.2, fill=WHITE, line=GRAY_L, radius=True)
    textbox(slide, 1.0, 3.35, 4.0, 0.3, "内核里的四类能力", 11, TEAL, True)
    modules = [
        ("计算", "22 类模型\n物性/衡算/精馏/换热"),
        ("工程", "P&ID 数据链\n设备数据表/安全阀"),
        ("安全", "HAZOP/LOPA\n标准符合性矩阵"),
        ("交付", "A1/A3 图纸\n报告/xlsx/打包"),
    ]
    for index, (title, body) in enumerate(modules):
        x = 1.0 + index * 2.9
        rect(slide, x, 3.75, 2.65, 1.4, fill=LIGHT, line=GRAY_L, radius=True)
        textbox(slide, x + 0.15, 3.88, 2.3, 0.3, title, 11.5, NAVY, True)
        textbox(slide, x + 0.15, 4.2, 2.35, 0.8, body, 9.3, GRAY, line=1.1)
    # data layer
    rect(slide, 0.8, 5.7, 11.8, 0.85, fill=TEAL_L, line=None, radius=True)
    textbox(slide, 1.0, 5.85, 11.4, 0.55,
            "本机数据层：data/projects（项目 JSON） · data/kernel/artifacts（成果文件） · data/bundles（带 SHA256 manifest 的 zip）",
            10.5, NAVY, True)

    # 07 capability map
    slide = base_slide(prs, 7, "06 / 能力地图", "60 个工具，四条交付主线",
                       "从“能聊天”变成“能出图、出表、出计算书、出合规清单”。")
    cols = [
        ("01 计算与文档", TEAL, ["22 类确定性计算", "DWSIM 外部流程模拟", "报告 DOCX/PDF/PPTX", "xlsx / 证据检索", "项目-要求-计划-校核", "计算校验与复算说明"]),
        ("02 图纸与 CAD", NAVY2, ["A1 P&ID（SVG/PDF/DXF）", "A3 设备图 + FCStd/STEP", "P&ID 数据表 xlsx/CSV", "齿轮零件图（扩展）", "标题栏/接管表/参数表"]),
        ("03 优先工程数据", AMBER, ["管线表 / MTO", "仪表索引 / IO 清单", "联锁因果表 C&E", "设备数据表/规格书", "估算项/待定项标注"]),
        ("04 安全与合规", GREEN, ["安全阀/爆破片选型", "HAZOP / LOPA 工作表", "标准符合性矩阵", "SIL 初判 / RRF", "review + manifest"]),
    ]
    for index, (title, color, items) in enumerate(cols):
        x = 0.7 + index * 3.12
        rect(slide, x, 1.75, 2.9, 3.25, fill=WHITE, line=GRAY_L, radius=True)
        rect(slide, x, 1.75, 2.9, 0.08, fill=color, line=None)
        textbox(slide, x + 0.18, 1.95, 2.55, 0.3, title, 12.5, color, True)
        bullets(slide, x + 0.18, 2.4, 2.55, 2.4, items, size=10.0, space=6, bullet_color=color)
    rect(slide, 0.7, 5.45, 11.9, 0.75, fill=NAVY, line=None, radius=True)
    textbox(slide, 0.95, 5.63, 11.4, 0.4,
            "60 个可执行工具　·　12 个主域 chem_* 工具　·　22 类计算　·　5 项优先能力　·　阶段门禁 + 自动校核 + 哈希打包",
            11.5, WHITE, True, align=PP_ALIGN.CENTER)

    # 08 P0 data chain + datasheet
    slide = base_slide(prs, 8, "07 / 优先能力 1-2", "P&ID 规范化：符号、管线标注与数据链同源",
                       "参照 HG/T 20519 内容深度与 ISA-5.1 符号；同一模型出管线表/MTO/仪表/IO/C&E。")
    picture(slide, ASSETS / "pid-standard-demo" / "render" / "page-01.png", 0.7, 1.7, 7.55, 4.75)
    rect(slide, 8.55, 1.7, 4.15, 2.25, fill=WHITE, line=GRAY_L, radius=True)
    textbox(slide, 8.75, 1.85, 3.8, 0.3, "P&ID 数据链（案例 A）", 11, TEAL, True)
    bullets(slide, 8.75, 2.2, 3.75, 1.35, [
        "15 条工艺管线、15 项 MTO",
        "5 仪表 + 5 阀门（3 控制阀 + 2 管道阀）",
        "8 点 I/O、2 条联锁（2×1）",
    ], size=10.0, space=4)
    textbox(slide, 8.75, 3.55, 3.75, 0.45, "图：2:1 封头/塔板/阀门/管道等级\n参照 HG/T 20519 + ISA-5.1，条款待核对", 8.4, GRAY, line=1.0)
    rect(slide, 8.55, 4.15, 4.15, 2.3, fill=WHITE, line=GRAY_L, radius=True)
    textbox(slide, 8.75, 4.3, 3.8, 0.3, "设备数据表（案例 A）", 11, AMBER, True)
    bullets(slide, 8.75, 4.65, 3.75, 1.5, [
        "R-101：设计 0.1 MPa(G) / 650 ℃，壁厚 3.8→6 mm",
        "T-101：0.1 MPa(G) / 200 ℃，94.1 m3",
        "E-101、P-101：面积/流量/功率待厂家确认项明确标注",
    ], size=9.8, space=4)
    textbox(slide, 8.75, 5.95, 3.8, 0.3, "输出：DOCX + PDF + JSON", 9.2, GRAY)

    # 09 safety + compliance
    slide = base_slide(prs, 9, "08 / 优先能力 3-5", "安全与合规：把“定性描述”变成可核查的表",
                       "安全阀选型、HAZOP/LOPA、标准符合性矩阵，全部落到可复算/可追溯的文件。")
    card(slide, 0.7, 1.75, 3.85, 2.3, "安全阀 / 爆破片",
         "阻塞流：R-101 → API 526 G 型，324.5 mm²，能力利用率 97.1%\n"
         "火灾：V-101 → M 型，2322.6 mm²，利用率 80.4%\n"
         "校核：积聚压力、背压、设定压力全部通过", TEAL)
    card(slide, 4.75, 1.75, 3.85, 2.3, "HAZOP / LOPA",
         "3 个节点、13 行偏差矩阵\n"
         "LOPA 2 个场景：L-01 1.0e-4/a 不满足 1e-5/a；\nL-02 增设独立联锁后 1.0e-6/a 满足\n"
         "自动给出所需 RRF 与 SIL 初判", AMBER)
    card(slide, 8.8, 1.75, 3.85, 2.3, "标准符合性矩阵（自查）",
         "29 条条款：13 符合 / 0 不符合 /\n14 待确认 / 2 待核对\n"
         "GB/T 3915 产品指标 7/7 符合\n"
         "未取得原文的 HG/T 20519 固定“待核对”", GREEN)
    evidence = [
        ("安全阀计算书", "DOCX / PDF / JSON", TEAL_L),
        ("HAZOP/LOPA 工作表", "XLSX / DOCX / JSON", AMBER_L),
        ("符合性矩阵", "XLSX / DOCX / JSON", TEAL_L),
    ]
    for index, (title, files, fill) in enumerate(evidence):
        x = 0.7 + index * 4.05
        rect(slide, x, 4.25, 3.75, 0.62, fill=fill, line=None, radius=True)
        textbox(slide, x + 0.15, 4.34, 1.9, 0.25, title, 9.2, NAVY, True)
        textbox(slide, x + 2.0, 4.34, 1.65, 0.25, files, 8.2, GRAY, align=PP_ALIGN.RIGHT)
    rect(slide, 0.7, 5.1, 11.95, 1.15, fill=WHITE, line=GRAY_L, radius=True)
    textbox(slide, 0.95, 5.22, 5.0, 0.3, "为什么这三件事重要", 10.5, NAVY, True)
    bullets(slide, 0.95, 5.52, 11.4, 0.65, [
        "比赛/答辩最容易被追问的是：超压工况怎么定？联锁是否独立？条款依据在哪一页？",
        "每个结论都能追到输入、公式、标准条款/页码与校核结果；“待确认/待核对”显式保留，不装作已合规。",
    ], size=9.6, space=3)
    textbox(slide, 0.7, 6.45, 11.9, 0.35,
            "注：API 520/521/526、HG/T 20519 原文未取得，公式与限值标注“待核对”；计算书不替代厂家选型与专业审核。",
            8.8, GRAY)

    # 10 case evidence
    slide = base_slide(prs, 10, "09 / 案例验证", "流程闭环，不是参赛作品",
                       "案例 A/B 是回归用例：验证交付链路与数据一致性，不代表赛题设计完成。")
    table(slide, 0.7, 1.8, 6.1, 2.45,
          ["项目", "要求", "成果", "计算", "唯一文件名", "状态"],
          [["案例 A · 苯乙烯", "35", "18", "28", "55 / 88", "数据完整"],
           ["案例 B · 苯-甲苯", "6", "4", "12", "15", "数据完整"],
           ["案例 A 复跑", "35", "12", "10", "11", "数据完整"]],
          [1.85, 0.6, 0.6, 0.6, 0.9, 0.7], font_size=9.2)
    textbox(slide, 0.7, 4.45, 6.1, 0.3, "可复现证据（以及它的边界）", 10.5, NAVY, True)
    bullets(slide, 0.7, 4.8, 6.05, 1.7, [
        "chem_review ready=true：只代表要求/依据/文件等数据完整性，专业审核仍为 not_reviewed",
        "案例 A：88 个文件含重复版本，去重后 55 个；核心交付约 15 份，其余为源文件/内部文件",
        "成果包可复算、可校验；哈希清单放附录，不作为主成果指标",
        "P&ID 是规范化示意图，不是 HG/T 20519 条款级合规图；严格设计仍未完成",
    ], size=9.3, space=4)
    picture(slide, ASSETS / "equipment-demo" / "page-01.png", 7.0, 1.75, 5.65, 3.9)
    rect(slide, 7.0, 5.85, 5.65, 0.75, fill=TEAL_L, line=None, radius=True)
    textbox(slide, 7.2, 5.98, 5.3, 0.5,
            "A3 设备图：尺寸、接管表、设计数据、标题栏齐全；壁厚按 GB/T 150.1 简化式计算。",
            9.2, NAVY, True)

    # 11 deployment
    slide = base_slide(prs, 11, "10 / 可部署性", "换一台 DSH，能力跟着走",
                       "不是“我这台机器能跑”，而是“打包带走、目标机自动拉起”。")
    number_card(slide, 0.7, 1.8, 2.6, 1.35, "169 MB", "安装包（含 Python）", TEAL)
    number_card(slide, 3.5, 1.8, 2.6, 1.35, "10,379", "包内条目（含依赖）", NAVY2)
    number_card(slide, 6.3, 1.8, 2.6, 1.35, "60", "包内可执行工具", AMBER)
    number_card(slide, 9.1, 1.8, 2.6, 1.35, "5/5", "优先工具烟测", GREEN)
    textbox(slide, 0.7, 3.25, 11.9, 0.25,
            "169 MB 主要来自便携 Python 与依赖；只说明目标机可免装环境，不是能力或质量指标。",
            8.6, GRAY)
    steps = [
        ("1", "解压分发包", "dsh-chemellm-*.zip"),
        ("2", "安装插件", "plugin_manager 指向目录"),
        ("3", "重启 DSH", "Host 新代码生效"),
        ("4", "自动拉起", "包内 Python 启动内核"),
    ]
    for index, (num, title, body) in enumerate(steps):
        x = 0.7 + index * 3.12
        rect(slide, x, 3.55, 2.85, 1.2, fill=WHITE, line=GRAY_L, radius=True)
        textbox(slide, x + 0.15, 3.65, 0.5, 0.5, num, 22, TEAL, True)
        textbox(slide, x + 0.65, 3.68, 2.0, 0.3, title, 10.5, NAVY, True)
        textbox(slide, x + 0.65, 4.0, 2.0, 0.6, body, 8.8, GRAY, line=1.1)
    rect(slide, 0.7, 5.0, 11.9, 0.45, fill=WHITE, line=GRAY_L, radius=True)
    textbox(slide, 0.95, 5.1, 11.4, 0.3,
            "目标机：Windows x64　·　已装 DSH　·　FreeCAD/LibreOffice 可选（缺失时降级并提示）",
            9.5, GRAY)
    rect(slide, 0.7, 5.65, 11.9, 1.05, fill=AMBER_L, line=None, radius=True)
    textbox(slide, 0.95, 5.78, 11.4, 0.3, "已经验证过什么", 10.5, RED, True)
    textbox(slide, 0.95, 6.08, 11.4, 0.55,
            "在 8803 端口用包内 runtime 启动内核：health 200、60 个工具；临时项目实际调用五项优先工具，"
            "全部生成文件；SHA256SUMS 抽样一致。",
            9.8, INK, line=1.15)

    # 12 vs opening goals
    slide = base_slide(prs, 12, "11 / 对照开题", "哪些做到了，哪些还没",
                       "不回避差异：方向从“云端普惠平台”收敛为“本地工程工作台”，是阶段选择，不是终点。")
    table(slide, 0.7, 1.75, 7.7, 4.3,
          ["开题目标", "状态", "说明"],
          [["基础计算", "已交付", "22 类模型 + 60 个工具；案例 A/B 实测"],
           ["流程模拟", "部分交付", "DWSIM 9.0.5 已接入外部自动化；简捷模型仍保留"],
           ["工艺设计", "部分交付", "P&ID 规范化示意/数据表/安全/合规已落地；严格设计待 P1"],
           ["零安装 / 移动", "调整", "本地插件需一次安装；云端/移动推迟"],
           ["开源合规", "部分", "开源库为主；FreeCAD/LibreOffice 外部；API/HG 原文待核对"],
           ["可信、可复现", "已交付", "阶段门禁 + review + manifest + 复算"]],
          [1.55, 1.15, 5.0], font_size=9.0, status_col=1)
    rect(slide, 8.75, 1.75, 3.85, 4.3, fill=NAVY, line=None, radius=True)
    textbox(slide, 8.98, 1.92, 3.4, 0.3, "三条取舍逻辑", 11, TEAL, True)
    reasons = [
        ("先本地", "学生团队没有长期服务器；先把单机闭环跑通。"),
        ("保留内核", "22 类计算与证据是积累，只换交互外壳。"),
        ("先补优先能力", "比赛最缺数据表、P&ID 数据链、安全与合规证据。"),
    ]
    for index, (title, body) in enumerate(reasons):
        y = 2.35 + index * 1.2
        textbox(slide, 8.98, y, 3.4, 0.3, title, 10.5, WHITE, True)
        textbox(slide, 8.98, y + 0.3, 3.35, 0.75, body, 8.8, RGBColor(0xC9, 0xD5, 0xDF), line=1.05)
    textbox(slide, 0.7, 6.35, 11.9, 0.5,
            "结论：先把“可信、可交付”做扎实，再回到“普惠、云端”。开题的三阶段路线不变，顺序调整。",
            10.5, NAVY, True)

    # 13 retrospective / gaps
    slide = base_slide(prs, 13, "12 / 第二个 3 天", "第二个 3 天：本地插件与交付",
                       "DeepSeek 接手：把云端原型拆成 DSH 插件 + 本地内核，补五项优先能力与可部署包。")
    card(slide, 0.7, 1.75, 3.85, 3.1, "三天完成",
         "Day 1　插件骨架 + 本地内核 + 项目闭环\n"
         "Day 2　A1 P&ID/A3 设备图 + 优先数据链/数据表/安全阀\n"
         "Day 3　HAZOP/LOPA + 合规矩阵 + 便携打包 + P&ID 规范化\n"
         "附加：教程、齿轮 CAD 扩展、插件说明\n"
         "验证：60 工具 / 2 案例 / 5 工具烟测", TEAL)
    card(slide, 4.75, 1.75, 3.85, 3.1, "还没做",
         "Aspen/商业流程模拟\n"
         "换热器/塔内件详细设计、管道水力\n"
         "3D 布置、施工图深度\n"
         "多用户/移动端/云端部署\n"
         "专业审核与签审", RED)
    card(slide, 8.8, 1.75, 3.85, 3.1, "风险与边界",
         "API/HG 原文未取得，部分公式/条款待核对\n"
         "P&ID 未达 HG/T 20519 条款级；仍为示意\n"
         "简化模型不替代 Aspen/HTRI\n"
         "FreeCAD/LibreOffice 不随包，Windows x64\n"
         "自动校核 ≠ 专业审核", AMBER)
    textbox(slide, 0.7, 5.2, 11.9, 0.5,
            "最需要补的不是“更多功能”，而是“更深的工程校核”和“真实赛题演练”。",
            11.5, NAVY, True, align=PP_ALIGN.CENTER)
    textbox(slide, 0.7, 5.9, 11.9, 0.35,
            "会后补充：DWSIM 9.0.5 外部自动化已接入（Cavett 流程：20 条物料流 / 15 个单元，solved=true）。",
            9.0, GRAY)

    # 14 next steps
    slide = base_slide(prs, 14, "13 / 下一步", "两条线：补工程深度，打一场真实比赛",
                       "接下来 2–4 周，把 P1 能力补上，同时用案例 C 做一次完整演练。")
    phases = [
        ("本周", "收口与演示", "修文档/演示脚本；\n把齿轮、教程、打包纳入版本；\n确认比赛规则与 AI 披露。\n三件事：演示、文档、规则。", TEAL),
        ("2–4 周", "P1 工程深度", "换热器详细设计、塔板水力学、\n管道水力/两相、DWSIM 流程模板、\n图纸版本/修订。\n先选 2 项做深。", AMBER),
        ("比赛前", "案例 C 实战", "选一道真实赛题，\n2 周内跑完 P&ID/数据表/安全/合规/报告，\n请专业老师审一遍。\n形成可复用的模板。", GREEN),
    ]
    for index, (period, title, body, color) in enumerate(phases):
        x = 0.7 + index * 4.12
        rect(slide, x, 1.8, 3.85, 2.95, fill=WHITE, line=GRAY_L, radius=True)
        rect(slide, x, 1.8, 3.85, 0.08, fill=color, line=None)
        textbox(slide, x + 0.2, 1.98, 3.3, 0.3, period, 10, color, True)
        textbox(slide, x + 0.2, 2.3, 3.4, 0.35, title, 14, NAVY, True)
        textbox(slide, x + 0.2, 2.75, 3.45, 1.85, body, 9.6, GRAY, line=1.15)
    rect(slide, 0.7, 5.15, 11.95, 0.9, fill=NAVY, line=None, radius=True)
    textbox(slide, 0.95, 5.33, 11.5, 0.6,
            "汇报后请老师定两件事：① 比赛题目与分工；② P1 优先做“设备详细设计”还是“DWSIM 流程模板深度”。",
            10.5, WHITE, True, align=PP_ALIGN.CENTER)

    # 15 closing
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    set_bg(slide, NAVY)
    rect(slide, 0, 6.9, W, 0.6, fill=NAVY2, line=None)
    textbox(slide, 0.8, 1.25, 11.8, 0.6, "从能算，到能交付，再到能比赛", 34, WHITE, True)
    textbox(slide, 0.8, 2.15, 11.2, 0.5, "明天现场可以演示：", 12, TEAL, True)
    bullets(slide, 0.8, 2.65, 11.5, 2.3, [
        "面板：案例 A 项目 → 要求/计划/依据/计算/成果/验收一键查看",
        "图纸：A1 P&ID、A3 设备图、齿轮零件图（DXF/STEP）",
        "安全与合规：安全阀计算书、HAZOP/LOPA、标准符合性矩阵",
        "部署：169 MB 便携包 + 60 工具 + 自动拉起",
    ], size=12.5, color=RGBColor(0xDD, 0xE6, 0xED), space=8, bullet_color=AMBER)
    textbox(slide, 0.8, 5.35, 11.5, 0.5, "恳请各位老师批评指正", 22, WHITE, True)
    textbox(slide, 0.8, 5.9, 11.5, 0.35, "汇报人：霍昊塬　｜　2026 年 10 月 26 日", 11, RGBColor(0xB9, 0xC7, 0xD4))

    OUT.parent.mkdir(parents=True, exist_ok=True)
    prs.save(OUT)
    print(OUT, OUT.stat().st_size, "slides", len(prs.slides))


if __name__ == "__main__":
    build()



