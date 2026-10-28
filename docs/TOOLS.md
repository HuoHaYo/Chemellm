# 化工工具清单与状态（本地版）

> 依据：2026-10-22 本机实测。学生项目、非盈利用途；下列免费/开源组件仅在本机安装使用，不随仓库分发二进制。
> 安装授权来自用户明确同意（LibreOffice / FreeCAD / DWSIM / pip 包 / 联网检索）。

## 1. 已安装并验证

| 工具 | 版本 | 位置 / 验证 |
|---|---|---|
| LibreOffice | 26.8.1.1 | `C:\Program Files\LibreOffice\program\soffice.exe`；手工 `--convert-to pdf` 成功 |
| FreeCAD | 1.1.4 | `%LOCALAPPDATA%\Programs\FreeCAD 1.1\bin\freecadcmd.exe`；`freecadcmd --version` 正常 |
| DWSIM | 9.0.5 | `%LOCALAPPDATA%\DWSIM`；已接入自动化：加载/求解 `.dwxmz`/`.dwxml`，输出 JSON/CSV |
| uv | 0.13.5 | `%LOCALAPPDATA%\Microsoft\WinGet\Packages\astral-sh.uv_*`；用于后续快速装包 |
| Python 扩展环境 | `.venv-sim` | `pyomo 6.10.1`、`rdkit 2026.9.1`、`idaes-pse 2.13.0` |
| IDAES 求解器 | ipopt 3.13.2 | `data/idaes/bin/ipopt.exe`；Pyomo `SolverFactory('ipopt')` 求解 `x²=4` → `x=2.0`，termination `optimal` |

## 2. 主环境已有（`.venv`）

thermo、chemicals、fluids、CoolProp、Cantera 3.2.0、ezdxf、python-docx、python-pptx、reportlab、openpyxl、matplotlib、Pillow、pdfplumber、pypdf、scipy、numpy、pandas（经旧项目依赖）。

## 3. 本轮新增的内核能力

- **项目删除**：`DELETE /v1/projects/{id}`（含快照、计算、成果与归档 DB 行）。
- **成果预览字段**：`hasVisualPreview` / `previewMode` 随 artifact 返回。
- **Office 预览改进**：内核自带 LibreOffice 转换封装（固定 profile 目录），不再依赖旧实现的临时 profile。
- **xlsx 导出**：`export_xlsx` 伪工具（`chem_tool tool=export_xlsx`）生成 6 个工作表（概览/要求/成果计划/设计依据/计算/成果文件）。
- **FreeCAD 三维**：`export_freecad` 伪工具调用 FreeCADCmd，按参数化布置生成 `FCStd` + `STEP`（默认 7 台设备；可用 `items` 覆盖）；同时生成**等轴测 SVG 预览**（`三维布置预览.svg`），FCStd/STEP 的 preview 指向该 SVG，面板预览不再空白；磁盘文件名用 ASCII（`layout.FCStd` / `layout.step`）避免中文路径兼容问题。**注意**：模型跨度约 40 m，FreeCAD 打开后若视图空白，执行“视图 → 全部适应（Fit all）”（已用 FreeCADCmd 验证文件含 7 个有效 Solid）。
- **独立部署运行时**：`dsh-chemellm/runtime/` 内置便携 CPython 3.12 + 58 个依赖（fastapi/uvicorn/scipy/thermo/CoolProp/cantera/reportlab/ezdxf/openpyxl/…）+ 内核 + 归档 app；`scripts/package-plugin.ps1` 生成 `dist/dsh-chemellm-<日期>-win-x64.zip`。Host 插件 `autostart` 在探测不到内核时自动启动；FreeCAD/LibreOffice 不随包，缺失时降级并提示。
- **P&ID 绘图（规范化）**：`pid` 输出 **A1 图**（841×594 mm，GB/T 14689 风格图框/分区/标题栏/修改栏），参照 HG/T 20519 内容深度与 ISA-5.1 符号：设备（容器/塔/换热器/泵/储罐/压缩机）、现场/盘装仪表泡、控制阀、手动/止回/安全/爆破片/盲板、管线号+规格+管道等级+保温/伴热；含设备表、仪表与阀门表、管线表、图例、说明；SVG/PDF/DXF/JSON + DEXPI 子集。规则见 `docs/DRAWING.md`。
- **P&ID 规则自检**：`pid_check` 校验位号唯一、端点存在、阀门/仪表连接、控制器→阀回路、管线号格式与重复，并新增管道规格/等级/介质、仪表量程、设备材料、标题栏字段等技术警告。
- **P&ID 数据链**：`pid_data` 从同一图模型生成管线表、材料表（MTO，含控制阀与管道阀、弯头/三通/法兰估算并标注）、仪表索引、I/O 清单（信号类型按位号推断、标注待定）、联锁因果表（C&E）与调节信号表；输出 xlsx（7 表）、5 个 CSV、DOCX 与 JSON。
- **设备数据表/规格书**：`equipment_datasheet` 按容器/塔器/储罐/换热器/泵/压缩机生成设计条件、材料与尺寸、接管表、供货范围、检验试验、标准引用与限制；壁厚/容积/重量按 GB/T 150.1 内压简化式估算并标注；输出 DOCX/PDF/JSON。
- **安全阀/爆破片选型**：`relief_sizing` 支持气体/蒸汽（临界/亚临界）、液体与火灾工况；计算泄放量、所需面积、API 526 标准孔径选型，校核能力利用率、积聚压力、背压与设定压力；输出带公式/来源/残差的计算书（DOCX/PDF/JSON）。公式按 API 520/521 公开资料实现，标注“原文未取得，待核对”。
- **HAZOP/LOPA 工作表**：`hazop_lopa` 生成节点清单、偏差矩阵（引导词×参数）、原因/后果/现有措施/建议、风险等级，以及 LOPA 场景（初始频率×IPL PFD、缓解频率、所需 RRF、SIL 初判）；输出 xlsx/docx/json；未提供偏差时生成骨架行并标注。方法与限制见 `docs/HAZOP.md`。
- **标准条款符合性矩阵**：`compliance_matrix` 按内置/自定义台账逐条判定（符合/不符合/待确认/待核对），自动对照产品指标、GB/T 150 范围、重大危险源临界量、GB 31571 排放限值与完成状态；未取得原文的条款只标“待核对”，不填限值；输出 xlsx/docx/json。台账与规则见 `docs/COMPLIANCE.md`。
- **DWSIM 流程模拟**：`dwsim` 通过外部 C# 运行器加载本机 DWSIM 9.0.5 的 `.dwxmz/.dwxml` flowsheet，调用 `Automation3` 求解，输出 `DWSIM结果.json` 与 `DWSIM物流表.csv`（T/K、P/Pa、质量流量 kg/s、摩尔组成）。DWSIM 为外部 GPL 软件，不随插件分发；详见 `docs/DWSIM.md`。
- **设备 CAD 与设备图**：`cad_part` 生成容器/塔器/储罐/换热器实体（筒体+2:1 椭圆封头+裙座+接管法兰），并出 **A3 设备图**（立面尺寸、接管表、设计数据、标题栏、比例），壁厚按 GB/T 150.1-2024 内压简化式计算；输出 FCStd/STEP/SVG/PDF/BOM JSON。
- **机械零件（齿轮）**：`cad_part` 的 `equipment_type="gear"` 生成标准直齿圆柱齿轮：渐开线齿廓、A3 零件图（端面+侧视+参数表）、DXF、FCStd/STEP；无变位/螺旋角/齿根修形，GB/T 1356/10095 原文未取得，标注“待核对”，不替代制造图。示例见 `docs/DRAWING.md` 4.1 与 `docs/USER_GUIDE.md` 7.2。

## 4. 已知限制（诚实记录）

1. **Office→PDF 预览**：LibreOffice 已装，但在 DSH 沙箱内由内核触发的 headless 转换会出现 `soffice.bin` 挂起（`Error: source file could not be loaded` / 进程不退出）。DOCX/PPTX 预览当前回退为文本模式；PDF 由 ReportLab 直接生成，不受影响。建议在普通终端（非沙箱）启动内核后再试转换。
2. **DWSIM 自动化**：已通过 `DWSIM.Automation.Automation3` 接入 `.dwxmz/.dwxml` 的加载与求解；不创建/编辑 DWSIM 流程图，不做动态模式与自定义脚本交互。详见 `docs/DWSIM.md`。
3. **FreeCAD 三维布置**：参数化 FCStd/STEP 生成器已实现并接入 `export_freecad`；仍为简化占位布置，未做碰撞、检修空间与安全间距校核。
4. **IDAES/Pyomo**：包与 ipopt 求解器已可用（`scripts/sim-env.cmd` 打开带环境变量与 PATH 的 shell）；`idaes get-extensions` 的原始下载会被网络截断，当前求解器二进制由 `curl -C -` 断点续传后手工放入 `data/idaes/bin`。
5. **AutoCAD 2004 / gbcbig.shx**：未安装商业 CAD；DXF 由 ezdxf 生成（R2004 兼容），"目标 CAD 实际打开与字体合规" 仍需环境。
6. **商业软件源文件**：Aspen/Icarus/PV Elite 等未授权；赛题 S03/S04 类专业软件源文件暂不可交付。
7. **厂家数据/动力学/实测相平衡**：仍缺；涉及处必须标注为假设或预测，不能当作实验/厂家数据。

## 5. 使用方式

```powershell
# 主内核（本地）
.\scripts\start-kernel.cmd

# 扩展环境（pyomo/idaes/ipopt/rdkit）：打开一个已设置 IDAES_DATA 与 PATH 的 shell
.\scripts\sim-env.cmd
# 或直接检查
.\.venv-sim\Scripts\python.exe -c "import pyomo, rdkit, idaes; print('sim env ok')"

# FreeCAD 命令行
& "$env:LOCALAPPDATA\Programs\FreeCAD 1.1\bin\freecadcmd.exe" --version

# DWSIM（GUI 或后续 .NET 自动化）
& "$env:LOCALAPPDATA\DWSIM\DWSIM.exe"
```

## 6. 许可说明

- LibreOffice：MPL-2.0；FreeCAD：LGPL-2.1+；DWSIM：GPL-3.0；IDAES/Pyomo/RDKit：BSD 类。
- 本项目为学生非盈利项目，仅本机调用这些程序，不修改其源码、不重新分发其二进制；报告/成果中如需引用其输出，将注明软件名称、版本与运行条件。
