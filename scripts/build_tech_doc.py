"""Build the project technical document (DOCX -> PDF)."""

from __future__ import annotations

from pathlib import Path

from docx import Document
from docx.enum.section import WD_SECTION
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Cm, Inches, Pt, RGBColor

ROOT = Path(__file__).resolve().parents[1]
DOCX = ROOT / "docs" / "ChemELLM_技术文档_v0.1.docx"
PDF = ROOT / "docs" / "ChemELLM_技术文档_v0.1.pdf"

NAVY = RGBColor(0x0B, 0x22, 0x39)
TEAL = RGBColor(0x1F, 0x9E, 0x8F)
AMBER = RGBColor(0xB5, 0x74, 0x0B)
GRAY = RGBColor(0x5F, 0x6F, 0x7D)
LIGHT = "EAF3F1"
HEADER_FILL = "0B2239"


def set_cell_shading(cell, fill: str):
    tc_pr = cell._tc.get_or_add_tcPr()
    shd = OxmlElement("w:shd")
    shd.set(qn("w:fill"), fill)
    tc_pr.append(shd)


def set_cell_margins(cell, top=60, bottom=60, left=80, right=80):
    tc_pr = cell._tc.get_or_add_tcPr()
    mar = OxmlElement("w:tcMar")
    for key, value in (("top", top), ("bottom", bottom), ("start", left), ("end", right)):
        node = OxmlElement(f"w:{key}")
        node.set(qn("w:w"), str(value))
        node.set(qn("w:type"), "dxa")
        mar.append(node)
    tc_pr.append(mar)


def shade_paragraph(paragraph, fill: str):
    p_pr = paragraph._p.get_or_add_pPr()
    shd = OxmlElement("w:shd")
    shd.set(qn("w:fill"), fill)
    p_pr.append(shd)


def add_field(paragraph, instruction: str):
    run = paragraph.add_run()
    begin = OxmlElement("w:fldChar")
    begin.set(qn("w:fldCharType"), "begin")
    instr = OxmlElement("w:instrText")
    instr.set(qn("xml:space"), "preserve")
    instr.text = instruction
    separate = OxmlElement("w:fldChar")
    separate.set(qn("w:fldCharType"), "separate")
    text = OxmlElement("w:t")
    text.text = "1"
    end = OxmlElement("w:fldChar")
    end.set(qn("w:fldCharType"), "end")
    run._r.append(begin)
    run._r.append(instr)
    run._r.append(separate)
    run._r.append(text)
    run._r.append(end)


def header_footer(doc: Document):
    section = doc.sections[0]
    header = section.header
    paragraph = header.paragraphs[0]
    paragraph.alignment = WD_ALIGN_PARAGRAPH.RIGHT
    run = paragraph.add_run("ChemELLM 本地化工工程工作台 · 技术文档 v0.1")
    run.font.name = "Microsoft YaHei"
    run.font.size = Pt(8)
    run.font.color.rgb = GRAY
    p_pr = paragraph._p.get_or_add_pPr()
    borders = OxmlElement("w:pBdr")
    bottom = OxmlElement("w:bottom")
    bottom.set(qn("w:val"), "single")
    bottom.set(qn("w:sz"), "4")
    bottom.set(qn("w:space"), "4")
    bottom.set(qn("w:color"), "D5DCE2")
    borders.append(bottom)
    p_pr.append(borders)

    footer = section.footer
    paragraph = footer.paragraphs[0]
    paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = paragraph.add_run("第 ")
    run.font.size = Pt(8)
    run.font.name = "Microsoft YaHei"
    add_field(paragraph, "PAGE")
    run = paragraph.add_run(" 页 / 共 ")
    run.font.size = Pt(8)
    run.font.name = "Microsoft YaHei"
    add_field(paragraph, "NUMPAGES")
    run = paragraph.add_run(" 页")
    run.font.size = Pt(8)
    run.font.name = "Microsoft YaHei"


def setup(doc: Document):
    section = doc.sections[0]
    section.page_width = Cm(21.0)
    section.page_height = Cm(29.7)
    section.top_margin = Cm(2.0)
    section.bottom_margin = Cm(1.8)
    section.left_margin = Cm(2.0)
    section.right_margin = Cm(2.0)

    normal = doc.styles["Normal"]
    normal.font.name = "Microsoft YaHei"
    normal.font.size = Pt(9.8)
    normal.font.color.rgb = RGBColor(0x1B, 0x2B, 0x3A)
    normal.paragraph_format.line_spacing = 1.18
    normal.paragraph_format.space_after = Pt(4)

    for level, size, color in ((1, 16, NAVY), (2, 12.5, NAVY), (3, 10.5, TEAL)):
        style = doc.styles[f"Heading {level}"]
        style.font.name = "Microsoft YaHei"
        style.font.size = Pt(size)
        style.font.bold = True
        style.font.color.rgb = color
        style.paragraph_format.space_before = Pt(10 if level == 1 else 8)
        style.paragraph_format.space_after = Pt(4)
        style.paragraph_format.keep_with_next = True
    header_footer(doc)


def H(doc, text, level=1):
    doc.add_heading(text, level=level)


def P(doc, text, size=9.8, color=None, bold=False, space=4, align=None):
    paragraph = doc.add_paragraph()
    paragraph.paragraph_format.space_after = Pt(space)
    if align is not None:
        paragraph.alignment = align
    run = paragraph.add_run(text)
    run.font.name = "Microsoft YaHei"
    run.font.size = Pt(size)
    run.font.bold = bold
    if color is not None:
        run.font.color.rgb = color
    return paragraph


def B(doc, items, size=9.6, space=2):
    for item in items:
        paragraph = doc.add_paragraph(style="List Bullet")
        paragraph.paragraph_format.space_after = Pt(space)
        paragraph.paragraph_format.left_indent = Cm(0.55)
        run = paragraph.add_run(item)
        run.font.name = "Microsoft YaHei"
        run.font.size = Pt(size)


def _row_flags(row, header=False):
    tr_pr = row._tr.get_or_add_trPr()
    cant = OxmlElement("w:cantSplit")
    tr_pr.append(cant)
    if header:
        repeat = OxmlElement("w:tblHeader")
        tr_pr.append(repeat)


def Table(doc, headers, rows, widths=None, size=8.4, header_fill=HEADER_FILL):
    table = doc.add_table(rows=1, cols=len(headers))
    table.style = "Table Grid"
    table.alignment = WD_TABLE_ALIGNMENT.CENTER
    table.autofit = False
    header = table.rows[0]
    _row_flags(header, header=True)
    for index, text in enumerate(headers):
        cell = header.cells[index]
        set_cell_shading(cell, header_fill)
        set_cell_margins(cell)
        paragraph = cell.paragraphs[0]
        paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER
        run = paragraph.add_run(text)
        run.font.name = "Microsoft YaHei"
        run.font.size = Pt(size)
        run.font.bold = True
        run.font.color.rgb = RGBColor(0xFF, 0xFF, 0xFF)
        if widths:
            cell.width = Cm(widths[index])
    for row in rows:
        row_obj = table.add_row()
        _row_flags(row_obj)
        cells = row_obj.cells
        for index, value in enumerate(row):
            cell = cells[index]
            set_cell_margins(cell)
            paragraph = cell.paragraphs[0]
            paragraph.paragraph_format.space_after = Pt(0)
            run = paragraph.add_run(str(value))
            run.font.name = "Microsoft YaHei"
            run.font.size = Pt(size)
            if widths:
                cell.width = Cm(widths[index])
    return table


def Figure(doc, path, width_cm, caption):
    paragraph = doc.add_paragraph()
    paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = paragraph.add_run()
    run.add_picture(str(path), width=Cm(width_cm))
    cap = doc.add_paragraph()
    cap.alignment = WD_ALIGN_PARAGRAPH.CENTER
    cap.paragraph_format.space_after = Pt(8)
    run = cap.add_run(caption)
    run.font.name = "Microsoft YaHei"
    run.font.size = Pt(8)
    run.font.color.rgb = GRAY


def cover(doc: Document):
    table = doc.add_table(rows=1, cols=1)
    table.autofit = False
    cell = table.rows[0].cells[0]
    cell.width = Cm(17.0)
    set_cell_shading(cell, "0B2239")
    set_cell_margins(cell, top=420, bottom=420, left=420, right=420)
    paragraph = cell.paragraphs[0]
    run = paragraph.add_run("TECHNICAL DOCUMENT  /  v0.1")
    run.font.name = "Arial"
    run.font.size = Pt(10)
    run.font.color.rgb = RGBColor(0x7F, 0xD8, 0xCB)
    paragraph = cell.add_paragraph()
    paragraph.paragraph_format.space_before = Pt(10)
    run = paragraph.add_run("ChemELLM\n本地化工工程工作台")
    run.font.name = "Microsoft YaHei"
    run.font.size = Pt(28)
    run.font.bold = True
    run.font.color.rgb = RGBColor(0xFF, 0xFF, 0xFF)
    paragraph = cell.add_paragraph()
    paragraph.paragraph_format.space_before = Pt(8)
    run = paragraph.add_run("DSH 插件 + 本地计算内核　技术文档")
    run.font.name = "Microsoft YaHei"
    run.font.size = Pt(13)
    run.font.color.rgb = RGBColor(0xC9, 0xD5, 0xDF)

    P(doc, "", size=8)
    P(doc, "版本：v0.1　　日期：2026-10-26　　平台：Windows x64", size=10, color=GRAY)
    P(doc, "范围：只记录当前已实现并验证的功能；未实现内容在“边界”章节列出。",
      size=9.2, color=GRAY)
    doc.add_page_break()


def build():
    doc = Document()
    setup(doc)
    cover(doc)

    # 1
    H(doc, "1　概述", 1)
    H(doc, "1.1　定位", 2)
    P(doc, "ChemELLM 本地化工工程工作台运行在 DeepSeek Harness（DSH）内，由一个 Host 插件和一个本机 Python 内核组成。"
           "原 ChemELLM 的确定性计算、证据、文档与图纸能力被保留为本地内核；会话、模型、审批与子代理交给 DSH。"
           "除模型调用外，项目数据、计算结果与成果文件全部留在本机，不依赖云端服务。")
    P(doc, "当前版本是 v0.1 的本地可用版，单用户、单机、loopback。它已能完成“资料→要求→计划→依据→计算→成果→校核→打包”"
           "的项目闭环，并已在两个案例上跑通。本文描述的是这一状态，不包含未来计划。")

    H(doc, "1.2　当前规模", 2)
    Table(doc, ["维度", "当前实现"], [
        ["可执行工具", "60 个（含 22 类计算与 11 个专项工具）"],
        ["主域工具", "12 个 chem_* 工具（项目/资料/要求/计划/对象/计算/证据/生成/校核/打包/成果/透传）"],
        ["确定性计算模型", "22 类（物性、衡算、反应、闪蒸、精馏、换热、压降、夹点、经济、Cantera 等）"],
        ["优先工程能力", "5 项：P&ID 数据链、设备数据表、安全阀/爆破片选型、HAZOP/LOPA、标准符合性矩阵"],
        ["验收案例", "2 个：案例 A（2026 赛题·苯乙烯）、案例 B（苯-甲苯精馏）"],
        ["部署包", "169.0 MB / 10,379 条目；内置 CPython 3.12.7 与依赖"],
        ["专业审核", "未签审（chem_review 为自动校核，professionalReview=not_reviewed）"],
    ], widths=[3.0, 13.9])

    H(doc, "1.3　设计原则", 2)
    B(doc, [
        "确定性计算与 LLM 分离：数值、图纸、表格由内核代码生成，模型只负责编排与解释。",
        "数据不出机：项目、成果、哈希与知识库保存在本机目录；内核只监听 127.0.0.1。",
        "可追溯：要求→成果计划→依据→计算→文件→校核→打包形成链，数值必须带单位、条件与来源。",
        "边界显式：未取得原文的标准条款、缺失参数、估算项在成果中标注“待核对/待确认”，不编造。",
    ])

    # 2
    H(doc, "2　系统架构", 1)
    Figure(doc, ROOT / "docs" / "assets" / "tech-architecture.png", 16.6,
           "图 1　系统分层：DSH 交互层、Host 插件、本地内核与本机数据层")
    H(doc, "2.1　组件", 2)
    Table(doc, ["组件", "实现", "职责"], [
        ["DSH Web GUI", "DSH 内置会话与面板", "对话、模型、审批、子代理、成果面板"],
        ["Host 插件", "dsh-chemellm/index.js", "12 个工具注册、阶段守卫、内核探测与自动拉起、同源代理"],
        ["Client 插件", "dsh-chemellm/client.js", "侧栏入口、项目面板、设置页"],
        ["本地内核", "kernel/server.py（FastAPI）", "项目数据、计算、校核、打包与成果生成"],
        ["计算与文档内核", "old/app 归档模块", "22 类计算、证据、文档、数据集等工具"],
        ["工程模块", "pid_standard / pid_data / datasheet / relief / hazop / compliance / cad_engineering / gear", "P&ID、数据表、安全、合规、设备图与齿轮"],
        ["DWSIM 桥接", "dwsim_bridge.py + dwsim/DwsimRunner.exe", "检测外部 DWSIM、加载/求解 .dwxmz/.dwxml、导出物流 JSON/CSV"],
        ["数据层", "data/ 与 .chem/", "项目 JSON、SQLite、成果文件、bundle、只读快照"],
    ], widths=[2.5, 6.0, 8.4])

    H(doc, "2.2　一次请求的数据流", 2)
    B(doc, [
        "DSH 会话中的模型选择 chem_* 工具并给出参数；Host 插件校验阶段并转发到本机内核。",
        "内核读取项目、执行确定性计算或渲染，将结果写入 data/kernel/artifacts，并登记文件哈希与来源。",
        "chem_review 按规则检查要求映射、依据单位/来源、计算校验与文件存在性。",
        "chem_bundle 将项目数据、计算记录、成果文件打包为 zip，并附 manifest 与 recompute.md。",
    ])
    P(doc, "内核只监听 127.0.0.1:8765；插件可在内核未启动时用包内 Python 自动拉起。", size=9.2, color=GRAY)

    # 3
    H(doc, "3　运行与部署", 1)
    H(doc, "3.1　开发模式", 2)
    P(doc, "本仓库使用 .venv + 本地内核：")
    B(doc, [
        "启动内核：scripts\\start-kernel.cmd（或 .ps1），监听 8765。",
        "DSH 安装 dsh-chemellm 目录；刷新页面后出现“化工工程”侧栏。",
        "数据目录：data/projects、data/kernel、data/bundles；快照在 .chem/。",
    ])
    H(doc, "3.2　便携部署包", 2)
    P(doc, "dist/dsh-chemellm-20261027-win-x64.zip：169.0 MB，10,379 个条目，内含：")
    B(doc, [
        "runtime/python：CPython 3.12.7 embeddable（Windows x64）。",
        "runtime/site-packages：58 个依赖（fastapi、uvicorn、scipy、thermo、CoolProp、Cantera、reportlab、ezdxf、openpyxl、python-docx 等）。",
        "runtime/kernel：本地内核模块（server、pid、pid_data、datasheet、relief、hazop、compliance、cad、gear、dwsim）。",
        "runtime/app：归档的 old/app 计算与文档模块。",
    ])
    P(doc, "Host 插件探测 /v1/health；不可达时用包内 python.exe 启动 runtime/kernel/server.py，数据默认写入 "
           "<DSH_PROFILE_DIR>/chemellm-data。目标机需 Windows x64；FreeCAD、LibreOffice 不随包，缺失时相关工具降级并提示。")
    H(doc, "3.3　配置项", 2)
    Table(doc, ["键", "默认", "说明"], [
        ["endpoint", "http://127.0.0.1:8765", "内核地址；端口也用于自动启动"],
        ["token", "空", "可选访问令牌；与内核 CHEMELLM_KERNEL_TOKEN 同步"],
        ["phaseGate", "advisory", "enforce 时越阶段调用返回 409"],
        ["autostart", "true", "探测不到内核时自动拉起"],
        ["python", "空", "覆盖 Python 路径（默认包内 runtime）"],
        ["dataDir", "空", "覆盖数据目录"],
    ], widths=[2.4, 5.0, 9.5])
    H(doc, "3.4　部署验证", 2)
    P(doc, "用包内 runtime 在 8803 端口启动内核：/v1/health 返回 200、列出 60 个工具；临时项目实际调用五项优先工具"
           "（pid_data、equipment_datasheet、relief_sizing、hazop_lopa、compliance_matrix）均成功生成文件；"
           "SHA256SUMS 抽样一致。以上为打包后的运行时验证，不是源码目录测试。")

    # 4
    H(doc, "4　项目生命周期与数据模型", 1)
    H(doc, "4.1　阶段", 2)
    Table(doc, ["阶段", "进入条件/产出", "门禁"], [
        ["intake", "登记资料（哈希、页数）", "advisory 放行；enforce 拦截越阶段"],
        ["requirements", "要求清单（编码、必需性、引句）", "同左"],
        ["plan", "要求→成果映射、对象计划", "同左"],
        ["basis", "工程对象（数值、单位、条件、来源）", "同左"],
        ["execute", "计算与文件生成", "同左"],
        ["review", "自动校核（blockers/warnings）", "ready=true 才能打包"],
        ["bundle", "zip + manifest + recompute", "生成后进入 done"],
    ], widths=[2.6, 9.8, 4.5], size=8.2)
    H(doc, "4.2　数据对象", 2)
    B(doc, [
        "项目：data/projects/<id>/project.json，含阶段、要求、计划、对象、计算、文件与 bundle 记录。",
        "要求：稳定编码、标题、是否必需、原文引句、适用性。",
        "计划：deliverables（key、标题、requirementCodes、formats）与 objects。",
        "依据：quantities 每项带 key、value、unit、origin（assumption/design_choice/document/calculation）、conditions、rationale；"
        "计算来源可带 calculationId 与 resultPath。",
        "计算：模型、输入、结果、校验结果与时间；文件：哈希、类型、来源、预览/下载路径。",
    ])
    H(doc, "4.3　校核与打包", 2)
    P(doc, "chem_review 检查：要求是否映射到成果、依据数值是否带单位/条件/来源/理由、计划文件是否存在、"
           "计算是否有校验记录。ready=true 只表示这些数据完整性条件满足，不表示设计正确，也不代表专业审核。")
    P(doc, "chem_bundle 生成 zip：project.json、requirements.json、plan.json、calculations.json、files/*，"
           "以及 manifest.json（逐文件 SHA256）与 recompute.md（复算说明）。scripts/verify_bundle.py 可独立校验。")

    # 5
    H(doc, "5　工具与计算能力", 1)
    H(doc, "5.1　12 个主域工具", 2)
    Table(doc, ["工具", "作用"], [
        ["chem_project", "列出/创建/读取项目"],
        ["chem_intake", "登记工作区资料（哈希、页数）"],
        ["chem_requirements", "要求清单登记与查看"],
        ["chem_plan", "要求→成果映射与对象计划"],
        ["chem_object", "工程对象（依据/物流/设备/公用工程/安全/成本）"],
        ["chem_calc", "调用 22 类计算模型"],
        ["chem_evidence", "文献检索、全文导入、证据与论断"],
        ["chem_generate", "报告 DOCX/PDF/PPTX/MD、PFD/PID 草图"],
        ["chem_review", "自动校核（blockers/warnings）"],
        ["chem_bundle", "打包成果（manifest + recompute）"],
        ["chem_artifact", "列出/预览/下载成果文件"],
        ["chem_tool", "透传旧工具/扩展开关工具（不传 tool 时列 60 个）"],
    ], widths=[3.4, 13.3], size=8.4)
    H(doc, "5.2　22 类确定性计算", 2)
    Table(doc, ["类别", "模型"], [
        ["物性与单位", "properties、steam、convert_units"],
        ["衡算与反应", "material_balance、reaction_thermo、mixture_reaction"],
        ["相平衡与分离", "flash、aqueous_flash、condenser_flash、distillation_shortcut、column_mesh、wet_column、wet_separation_train"],
        ["换热与流动", "heat_exchanger、pipe_pressure_drop、pinch_analysis"],
        ["流程与循环", "frontend_process、recycle_process"],
        ["经济与数据", "economics、fit_data"],
        ["Cantera", "cantera_equilibrium、cantera_reactor"],
    ], widths=[3.2, 13.5], size=8.4)
    P(doc, "计算模型沿用原项目假设（如 PR kij=0、理想精馏、UNIFAC 预测等）；validation.passed 是数值校验，不等于工程正确。",
      size=8.8, color=GRAY)
    H(doc, "5.3　专项生成工具", 2)
    Table(doc, ["工具", "输出"], [
        ["pid / pid_check", "A1 规范化 P&ID（SVG/PDF/DXF/JSON/DEXPI 子集）+ 结构/技术警告"],
        ["pid_data", "管线表、MTO、仪表索引、IO 清单、C&E、调节信号表（xlsx/CSV/DOCX/JSON）"],
        ["equipment_datasheet", "容器/塔/储罐/换热器/泵/压缩机数据表（DOCX/PDF/JSON）"],
        ["relief_sizing", "安全阀/爆破片计算书（DOCX/PDF/JSON）"],
        ["hazop_lopa", "HAZOP 偏差矩阵与 LOPA 表（xlsx/DOCX/JSON）"],
        ["compliance_matrix", "标准条款符合性矩阵（xlsx/DOCX/JSON）"],
        ["cad_part", "A3 设备图 + FCStd/STEP + BOM；gear 模式为直齿圆柱齿轮"],
        ["export_xlsx / export_freecad", "项目 6 表 xlsx；参数化三维布置 FCStd/STEP + 预览"],
    ], widths=[4.2, 12.5], size=8.4)
    H(doc, "5.4　DWSIM 外部流程模拟", 2)
    P(doc, "`dwsim` 工具接入本机外部 DWSIM 9.0.5：加载并求解 .dwxmz/.dwxml，输出 DWSIM结果.json 与 "
           "DWSIM物流表.csv（T/K、P/Pa、质量流量 kg/s、摩尔组成）。DWSIM 为 GPL-3.0 外部软件，不随包分发。",
      size=8.8, color=GRAY)

    # 6
    H(doc, "6　工程图纸与数据链", 1)
    H(doc, "6.1　规范化 P&ID", 2)
    P(doc, "pid 输出 A1 横放（841×594 mm）图：GB/T 14689 风格图框、分区编号、标题栏、修改栏、图例、说明、"
           "设备表、仪表与阀门表、管线表。图元包括：")
    B(doc, [
        "容器/反应器（2:1 椭圆封头、裙座、接管、搅拌器）、塔器（封头、塔板/填料）、卧式换热器（壳体、管束、管箱）、"
        "泵（泵体+电机+底座）、储罐、压缩机。",
        "ISA-5.1 风格仪表泡：现场仪表空心圆，DCS/盘装带水平线；功能字母、回路号、量程与联锁标注。",
        "控制阀（阀体+执行机构）、手动/闸/球/蝶阀、止回阀、安全阀、爆破片、盲板、过滤器；"
        "可在工艺边上写 valves 列表，沿路由自动放置。",
        "管线号 + 管径/规格 + 管道等级 + 保温/伴热；工艺线实线、仪表信号虚线、联锁点划线。",
    ])
    Figure(doc, ROOT / "docs" / "assets" / "pid-standard-detail.png", 15.6,
           "图 2　规范化 P&ID 局部：2:1 封头、搅拌器、接管、管线标注与控制阀")
    P(doc, "边界：本图参照 HG/T 20519 内容深度与 ISA-5.1 符号，但未取得标准原文；off-page 接续、管线断线、"
           "管口表、管道等级库与材料等级库尚未实现，不能作为条款级合规图或施工图。", size=8.8, color=GRAY)
    H(doc, "6.2　P&ID 数据链", 2)
    P(doc, "pid_data 从同一 P&ID 模型生成工程数据表，不重新绘图。案例 A 模型补齐管道等级/仪表量程/材料并加入 2 个管道阀后的结果：15 条工艺管线、15 项 MTO、"
           "5 个仪表、5 个阀门（3 个控制阀 + 2 个管道阀）、8 点 I/O、2 条联锁。输出：")
    Table(doc, ["输出", "内容"], [
        ["P&ID数据表.xlsx", "管线表、材料表、仪表索引、IO 清单、联锁因果表、调节信号表、说明"],
        ["5 个 CSV", "管线表、材料表、仪表索引、IO 清单、联锁因果表"],
        ["P&ID数据表.docx", "同内容 Word 版"],
        ["P&ID数据.json", "模型 + 表格数据，便于复算"],
    ], widths=[5.0, 11.7], size=8.4)
    H(doc, "6.3　设备图与 CAD", 2)
    P(doc, "cad_part 生成压力容器/塔器/储罐/卧式换热器的实体（筒体+2:1 椭圆封头+裙座+接管法兰），并出 A3 设备图："
           "立面、总高/切线长/直径尺寸、接管标高、接管表、设计数据、标题栏、比例。壁厚按 GB/T 150.1-2024 内压简化式计算，"
           "注明未计开孔补强、蠕变、外压稳定性。输出 FCStd/STEP/SVG/PDF/BOM JSON。gear 模式输出直齿圆柱齿轮的 A3 零件图、DXF、"
           "FCStd/STEP，齿廓为渐开线、齿根为简化过渡。")
    P(doc, "设备图与齿轮图均为参数化外形/示意，不含制造公差、焊缝详图、热处理与检验要求，不能直接作为制造图。",
      size=8.8, color=GRAY)

    # 7
    H(doc, "7　安全与合规", 1)
    H(doc, "7.1　安全阀/爆破片选型", 2)
    P(doc, "relief_sizing 支持气体/蒸汽（临界与亚临界）、液体与火灾工况；计算所需泄放面积，按 API 526 常用孔径选型，"
           "校核能力利用率、积聚压力（110%/121%）、背压与设定压力，并输出带公式、假设、来源与残差的 DOCX/PDF/JSON 计算书。"
           "案例 A：R-101 阻塞流所需 315 mm²，选 G 型（324.5 mm²），利用率 97.1%；V-101 火灾工况所需 1866 mm²，"
           "选 M 型（2322.6 mm²），利用率 80.4%。")
    P(doc, "API 520/521/526 原文未取得，公式按公开资料实现并在计算书中标注“待核对”；不替代厂家选型与专业审核。",
      size=8.8, color=GRAY)
    H(doc, "7.2　HAZOP / LOPA", 2)
    P(doc, "hazop_lopa 生成节点清单、偏差矩阵（引导词×参数）、原因/后果/现有措施/建议、严重度×可能性风险等级；"
           "LOPA 计算初始频率 × 独立保护层 PFD 的缓解频率、所需 RRF 与 SIL 初判。案例 A：3 个节点、13 行 HAZOP、"
           "2 个 LOPA 场景；L-01 缓解后 1.0e-4/a 高于 1e-5/a 目标，L-02 增设独立联锁后 1.0e-6/a 满足。")
    P(doc, "工作表不替代 HAZOP 会议与签署；SIL 仅为按 RRF 的初判，未做 SIL 验证（PFD 计算、架构约束、共因失效）。",
      size=8.8, color=GRAY)
    H(doc, "7.3　标准符合性矩阵", 2)
    P(doc, "compliance_matrix 按内置 29 条台账逐条判定，覆盖 GB/T 3915-2021、GB/T 150.1-2024、GB 36894-2018、"
           "GB 18218-2018、GB 31571-2015、HG/T 20519、HG/T 20570.2 与项目要求。判定为符合/不符合/待确认/待核对；"
           "未取得原文的条款固定“待核对”，不填具体限值。案例 A 当前：13 符合、0 不符合、14 待确认、2 待核对。")
    P(doc, "“符合”仅表示现有项目数据满足该数值或完成状态，不代表设计文件已通过专业审核，也不构成合规结论。",
      size=8.8, color=GRAY)

    # 8
    H(doc, "8　校核、打包与验证", 1)
    H(doc, "8.1　自动校核的语义", 2)
    P(doc, "chem_review ready=true 的规则是：要求均映射到成果、依据数值带单位/条件/来源/理由、成果计划中的文件存在、"
           "计算有校验记录。它不检查流程是否最优、设备选型是否合理、P&ID 是否合规、经济性是否成立。"
           "professionalReview 始终为 not_reviewed，除非另行人工签审。")
    H(doc, "8.2　已验证结果", 2)
    Table(doc, ["验证项", "结果"], [
        ["案例 A：2026 赛题·苯乙烯", "35 要求 / 18 成果 / 28 计算 / 88 文件（55 个唯一文件名）；chem_review ready=true；"
                                           "bundle 95 条目、88 文件哈希全部匹配"],
        ["案例 B：苯-甲苯精馏", "6 要求 / 4 成果 / 12 计算 / 15 文件；chem_review ready=true"],
        ["P&ID 数据链（规范化示例）", "15 管线 / 15 MTO / 5 仪表 / 5 阀门 / 8 点 I/O / 2 联锁"],
        ["安全阀选型", "阻塞流 G 型 324.5 mm²，利用率 97.1%；火灾 M 型 2322.6 mm²，利用率 80.4%"],
        ["HAZOP / LOPA", "3 节点 / 13 行 / 2 场景（1 不满足、1 满足）"],
        ["合规矩阵", "29 条：13 符合 / 0 不符合 / 14 待确认 / 2 待核对"],
        ["便携运行时", "包内 Python 启动内核：health 200、60 工具；五项优先工具烟测 5/5 成功"],
        ["DWSIM 接入", "DWSIM 9.0.5 / Cavett .dwxmz：solved=true、20 条物料流、15 个单元；输出 JSON/CSV；项目 review ready=true"],
        ["P&ID 规范化", "补齐管道等级/量程/材料后 pid_check 0 warnings；原模型会列出待补项"],
        ["齿轮 CAD", "m2/z20 直齿圆柱齿轮：STEP 1 个 Solid，体积 17,816.7 mm³，valid=True"],
    ], widths=[4.1, 12.6], size=8.2)
    P(doc, "以上数字来自本机项目记录与打包验证；它们是当前实现的验证结果，不构成赛题设计正确性或专业审核结论。",
      size=8.8, color=GRAY)

    # 9
    H(doc, "9　边界与限制", 1)
    Table(doc, ["类别", "当前边界"], [
        ["流程模拟", "DWSIM 9.0.5 已接入（加载/求解 .dwxmz/.dwxml，输出 JSON/CSV）；Aspen 未接入；22 类模型为简化/开源路线"],
        ["设备设计", "无换热器详细设计、塔内件水力学、管道水力/两相、材料等级库；设备数据表为工程示意"],
        ["图纸", "P&ID 为规范化示意，非 HG/T 20519 条款级合规；无 off-page、管线断线、管口表；设备图为外形图，非施工图"],
        ["标准", "API 520/521/526、HG/T 20519 原文未取得；相关公式/条款标注“待核对”"],
        ["外部软件", "DWSIM/FreeCAD/LibreOffice 均为外部安装；DWSIM 为 GPL-3.0，不随包；缺失时对应能力提示或降级"],
        ["平台", "Windows x64；单用户、单机、loopback；无多租户、移动端、云端部署"],
        ["审核", "chem_review 是自动校核；专业审核未签审；所有成果需人工复核"],
    ], widths=[2.6, 14.1], size=8.2)
    P(doc, "这些边界不是“未完成事项清单”，而是当前版本的适用边界；在此边界内，工作台可完成项目化、可追溯的工程文档与数据交付。",
      size=8.8, color=GRAY)

    # 10
    H(doc, "10　文件与入口", 1)
    Table(doc, ["路径", "内容"], [
        ["README.md", "项目总览、验证记录与边界"],
        ["docs/USER_GUIDE.md", "插件安装、面板、工具与故障排查教程"],
        ["docs/TOOLS.md", "工具清单与已知限制"],
        ["docs/DRAWING.md", "P&ID/设备图规则与 P&ID 规范化说明"],
        ["docs/DWSIM.md", "DWSIM 外部自动化接入、调用方式与边界"],
        ["docs/HAZOP.md、COMPLIANCE.md", "HAZOP/LOPA 与合规矩阵的方法/台账"],
        ["docs/ACCEPTANCE.md", "逐项验收记录"],
        ["kernel/", "本地内核与工程模块源码"],
        ["dsh-chemellm/", "Host/Client 插件与便携 runtime"],
        ["dist/dsh-chemellm-20261027-win-x64.zip", "可分发部署包（169.0 MB，含 DWSIM 运行器）"],
        ["data/", "项目、成果、bundle（运行数据）"],
    ], widths=[6.0, 10.7], size=8.2)
    P(doc, "常用验证命令：")
    B(doc, [
        "curl http://127.0.0.1:8765/v1/health　（内核健康）",
        "curl http://127.0.0.1:8765/v1/tools　（60 个工具）",
        ".\\.venv\\Scripts\\python.exe -X utf8 scripts\\smoke.py　（全链路冒烟）",
        ".\\.venv\\Scripts\\python.exe -X utf8 scripts\\verify_bundle.py <bundle.zip>　（哈希校验）",
    ], size=8.8)
    P(doc, "文档版本：v0.1　|　生成日期：2026-10-26　|　对应代码与数据以本机工作区为准。",
      size=8.8, color=GRAY)

    doc.save(DOCX)
    print("DOCX", DOCX, DOCX.stat().st_size)


if __name__ == "__main__":
    build()

