# ChemELLM 本地化工工程工作台（DSH 插件版）

把化工工程的项目管理、计算、文档与验收搬进 **DeepSeek Harness**，全部在本机完成，不依赖云端。

- **交互面**：DSH Web GUI（侧栏「化工工程」面板 + 对话内 12 个 `chem_*` 工具）；面板直连本地内核（loopback CORS），Host 代理 `/chemellm` 作为备用。
- **计算内核**：本地 Python 服务（`http://127.0.0.1:8765`），复用原 ChemELLM 的 22 类确定性计算模型、文档生成与证据工具。
- **原项目**：完整归档在 [`old/`](old/)，不再作为运行入口。

> 当前是 v0.1 本地可用版：单用户、单机、默认无鉴权令牌（loopback）。边界见文末。
>
> 本机现有两个已验收案例（均在 DSH 内从空项目建设）：**案例 A** 2026 赛题·苯乙烯清洁生产（35 要求/18 成果/28 计算/88 文件）与 **案例 B** 苯-甲苯精馏迁移案例（6 要求/4 成果/14 文件）；两者 zip 均通过 manifest 哈希校验，并含 `recompute.md` 复算说明。

## 使用教程

**新手建议先读：[docs/USER_GUIDE.md](docs/USER_GUIDE.md)** —— 安装/启动、面板导览、第一个项目、12 个主域工具、五项 P0 工具（P&ID 数据链/设备数据表/安全阀选型/HAZOP-LOPA/符合性矩阵）、典型工作流、故障排查与能力边界。


## 目录结构

```
kernel/                本地内核（FastAPI，包装 old/app 的工具链）
  server.py            /v1 契约：项目、要求、计划、对象、执行、校核、打包、删除
dsh-chemellm/          DSH 插件包（bundle + Host 半 + Client 半）
  index.js             Host：12 个域工具（含 chem_tool）、阶段守卫、提示词、同源代理、内核自动拉起
  client.js            Client：侧栏入口、工程面板、设置页
  cordis.patch.yml     插件行配置（endpoint / token / phaseGate / autostart / dataDir）
  runtime/             便携运行时：python/ + site-packages/ + kernel/ + app/ + requirements.txt
  README.md            独立部署说明与能力矩阵
dist/                  打包产物（scripts/package-plugin.ps1 生成的可分发 zip）
dsh-chemellm-legacy/   伴生包源码（chem_legacy；主包 chem_tool 生效后已从 profile 移除）
dsh-chemellm-enforce/  门禁测试覆盖包（仅 patch，把插件 phaseGate 切到 enforce；不默认安装）
scripts/               启动、冒烟、成果包校验、UI 检查
data/                  本地数据（内核 SQLite、项目 JSON、成果文件）
.chem/                 只读工程快照（面板与 git diff 用）
.venv-sim/             扩展环境（pyomo / rdkit / idaes-pse；可选）
old/                   原 ChemELLM 项目归档（app/web/tests/docs/data…）
standards/             用户提供的标准 PDF 与文本/页面导出（GB/T 3915-2021、GB/T 150.1-2024）
docs/                  使用教程、快速上手、目标、验收记录、工具清单与专题说明
```

## 外部工具（本轮已安装）

| 工具 | 版本 | 用途 |
|---|---|---|
| LibreOffice | 26.8.1.1 | DOCX/PPTX→PDF 预览（沙箱内自动转换暂不稳定，见限制） |
| FreeCAD | 1.1.4 | 三维设备布置与源文件（命令行已可用） |
| DWSIM | 9.0.5 | 稳态流程模拟：外部自动化已接入，加载/求解 `.dwxmz/.dwxml`，输出 JSON/CSV |
| uv | 0.13.5 | 快速装包（`pip` 在本机沙箱内会卡住时的替代） |
| `.venv-sim` | pyomo 6.10.1 / rdkit 2026.9.1 / idaes-pse 2.13.0 / ipopt 3.13.2 | 流程优化、分子描述符、方程型建模；`scripts/sim-env.cmd` 打开已配置环境的 shell |

学生项目、非盈利用途；免费/开源组件仅本机调用，不随仓库分发。完整清单、路径与许可见 [docs/TOOLS.md](docs/TOOLS.md)。

## 快速开始

### 1. 准备 Python 环境（本机已完成）

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -e old       # 复用原项目依赖
```

### 2. 启动本地内核

```powershell
.\scripts\start-kernel.cmd        # 或 .\scripts\start-kernel.ps1
```

首次启动会在 `data/kernel/` 建库、在 `data/projects/` 建项目目录；内核只监听 `127.0.0.1:8765`。

### 3. 插件已安装（开发模式）

本机当前 profile 已安装 `@local/dsh-chemellm`（bundle），并手动启动内核（见第 2 步）。换机器时有两种方式：

**A. 开发模式（本仓库）**：安装 `<仓库>\dsh-chemellm`，手动运行 `scripts\start-kernel.cmd`。

**B. 可独立部署包（推荐换机）**：插件包含**便携 Python 3.12 + 依赖 + 内核 + 归档应用**，Host 插件在探测不到内核时会自动拉起，目标机无需预装 Python。

```powershell
# 打包（生成 dist\dsh-chemellm-<日期>-win-x64.zip）
powershell -ExecutionPolicy Bypass -File scripts\package-plugin.ps1

# 目标机：解压后用 plugin_manager 安装该目录（或整个目录复制进 profile）
```

包内结构、配置项与能力矩阵见 [dsh-chemellm/README.md](dsh-chemellm/README.md)。要点：

- `autostart: true` 时，Host 插件探测 `endpoint/v1/health`，失败则用 `runtime/python/python.exe` 启动 `runtime/kernel/server.py`，数据目录默认 `<DSH_PROFILE_DIR>/chemellm-data`；
- **纯 Python 能力全部随包**：项目/要求/计划/依据/计算/证据/校核/打包、A1 P&ID、A3 设备图、xlsx、DOCX/PDF 报告；
- **FreeCAD**（FCStd/STEP）与 **LibreOffice**（Office 预览）不随包，目标机已装则可用，缺失时工具返回明确错误、其余能力不受影响；
- 运行时为 Windows x64；macOS/Linux 需替换对应便携 Python。

### 4. 开始一个项目

在面板点「新建项目」，然后在任意会话中让模型：

> 用 chem_project 创建项目；用 chem_intake 登记 old/26化工设计大赛题目.pdf；用 chem_requirements 登记赛题要求；用 chem_plan 建立成果计划；用 chem_object 写入设计依据；用 chem_calc 计算；用 chem_generate 生成报告；用 chem_review 自检；用 chem_bundle 打包。

完整链路示例（不经过模型，直接验证内核）：

```powershell
.\.venv\Scripts\python.exe -X utf8 scripts\smoke.py
```

## 域工具（11 个）

| 工具 | 作用 |
|---|---|
| `chem_project` | 列出 / 创建 / 读取本地项目 |
| `chem_intake` | 登记工作区资料（PDF/DOCX/XLSX/CSV/SVG/DXF…），生成哈希与页数 |
| `chem_requirements` | 要求清单登记与查看（编码、原文引句、适用性） |
| `chem_plan` | 成果计划：要求→成果映射、对象计划、格式与依赖 |
| `chem_object` | 工程对象（依据/物流/设备/公用工程/安全/成本…），数值带单位、条件与来源 |
| `chem_calc` | 22 类计算模型：物性、蒸汽、单位、衡算、反应热、PR 闪蒸、精馏 MESH、分相、含氢冷凝、湿塔、循环、换热、压降、夹点、经济、Cantera、回归 |
| `chem_evidence` | 文献检索、全文导入、引句证据、论断管理 |
| `chem_generate` | 生成 DOCX/PPTX/PDF/MD 报告或 PFD/P&ID 草图（SVG/DXF） |
| `chem_tool`（扩展） | 新增 `pid`（P&ID：设备/仪表/控制阀/联锁/管线号 → SVG/PDF/DXF/JSON/DEXPI 子集）、`pid_check`（P&ID 规则自检）、`cad_part`（参数化设备 CAD：FCStd/STEP/立面预览）。用法与限制见 [docs/DRAWING.md](docs/DRAWING.md) |
| `chem_review` | 自动校核：覆盖、依据、校验、文件、缺口与 blockers |
| `chem_bundle` | 打包项目：数据、计算、成果文件、哈希清单（zip） |
| `chem_artifact` | 列出文件 / 取预览或下载链接（`/chemellm/files/…`） |
| `chem_tool` | 通用透传：调用旧版任意已注册工具（设备登记/查询、图纸识读、数据集检查/分析等）；不传 `tool` 时列出全部工具名。**主包新代码需 Host 重启后生效** |
| `chem_legacy` | 伴生包提供的等价透传，当前进程已可用；实测 `convert_units` 1 bar = 100 kPa，可列出 49 个可执行工具。Host 重启并验证 `chem_tool` 后可移除伴生包 |

## 工程阶段与门禁

```
资料(intake) → 要求(requirements) → 计划(plan) → 依据(basis) → 执行(execute) → 校核(review) → 打包(bundle) → 完成(done)
```

- 阶段由内核根据项目数据自动推导，写入 `.chem/<项目>/project.json`。
- 插件配置 `phaseGate: advisory`（默认）时，越阶段调用仅在返回里给出警告；设为 `enforce` 时内核与插件守卫会拒绝。
- 阶段变更或数据变更会重置 `review`，旧审核不自动沿用。

## 插件配置

`dsh-chemellm/cordis.patch.yml`：

```yaml
- insert:
    - id: chemellm
      name: '@local/dsh-chemellm'
      config:
        endpoint: http://127.0.0.1:8765
        token: ''
        phaseGate: advisory
```

- `endpoint`：内核地址（默认 loopback）。将来如需远端内核，只改这里。
- `token`：可选。内核侧启动前设置 `CHEMELLM_KERNEL_TOKEN` 后，两边需一致；令牌只在 Host 侧使用，浏览器不可见。
- `phaseGate`：`advisory` | `enforce` | `off`。

## 数据位置

| 路径 | 内容 |
|---|---|
| `data/kernel/chemellm.sqlite3` | 计算记录与文件元数据（复用原库结构） |
| `data/kernel/artifacts/` | 成果与资料原件 |
| `data/projects/<id>/project.json` | 项目状态（唯一事实源） |
| `data/bundles/` | 打包后的 zip |
| `.chem/<id>/` | 只读快照（面板、git diff、离线审查） |

## 验证状态（本机实测）

| 项 | 结果 |
|---|---|
| 内核接口 | `/v1/health` 200；`scripts/smoke.py` 全链路通过（建项目→要求→计划→依据→计算→报告→校核→打包） |
| 插件安装 | 仅 `@local/dsh-chemellm` installed / `applied`；伴生包已移除 |
| 独立部署运行时 | 包内 `runtime/python`（CPython 3.12.7 embeddable）+ 58 个依赖；在 8799、8801、8802、8803 四个端口分别实测启动内核：`/v1/health` 200、**60 个可执行工具**、成功生成 P&ID（SVG/PDF/DXF/JSON/DEXPI） |
| 可分发安装包 | `dist/dsh-chemellm-20261027-win-x64.zip`，**169.0 MB / 10,379 条目**（9,452 文件，含 DWSIM 运行器），SHA256 `b96c005a…74aa`；从解包目录启动内核成功，`SHA256SUMS.txt` 抽样校验一致 |
| 部署包五工具实测 | 用打包后的 `runtime` 启动内核（8803 端口），在临时项目中实际调用 `pid_data`（8 文件）、`equipment_datasheet`（3）、`relief_sizing`（3）、`hazop_lopa`（3）、`compliance_matrix`（3），全部成功；工具数 60 |
| DWSIM 接入 | `dwsim` 工具：检测 DWSIM 9.0.5，加载 Cavett `.dwxmz` 并求解，solved=true、20 条物料流/15 个单元操作；输出 JSON/CSV；项目 `DWSIM 接入验证（Cavett）` 已 review/bundle |
| 自动拉起 | Host 插件 `autostart`：探测 `endpoint/v1/health` 失败时用包内 Python 启动 `runtime/kernel/server.py`；数据默认 `<DSH_PROFILE_DIR>/chemellm-data`。已按 Host 相同 spawn 参数验证；**运行中的 Host 仍是旧代码，需重启 DSH 后自动拉起才生效** |
| 工具注册 | **12 个主域工具**（含 `chem_tool`）已在本会话可见并可调用；Host 重启后新代码已生效 |
| 旧工具覆盖 | `chem_tool` 可列出 **60 个可执行工具**（含 `export_xlsx`、`export_freecad`、`pid`、`pid_check`、`pid_data`、`equipment_datasheet`、`relief_sizing`、`hazop_lopa`、`compliance_matrix`、`cad_part`、`dwsim`）并实际调用 |
| 案例 A（M3） | ✅ 八轮闭环：35 要求 / **18 成果计划**（31/31 必需映射）、28 条计算、88 个文件；`chem_review` ready=true；zip **95 条目、88 文件哈希全部匹配** |
| 生成新文件 | `export_xlsx`（6 表 xlsx）、`export_freecad`（布置 FCStd+STEP）、`pid`（A1 P&ID）、`pid_data`（管线表/MTO/仪表索引/IO/C&E）、`equipment_datasheet`（设备数据表 DOCX/PDF/JSON）、`relief_sizing`（安全阀/爆破片计算书）、`hazop_lopa`（HAZOP/LOPA 工作表）、`compliance_matrix`（标准符合性矩阵 xlsx/docx/json）、`cad_part`（A3 设备图 + FCStd/STEP + BOM）、`dwsim`（外部 DWSIM 求解结果 JSON/CSV） |
| P&ID / CAD | 案例 A 已生成 **A1 P&ID**（19 节点/24 边、5 仪表、3 控制阀，规则校验通过；不按比例）与 R-101/T-101 **A3 设备图**（壁厚按 GB/T 150.1 简化式计算：R-101 6 mm、T-101 6 mm；含接管表/设计数据/标题栏）；规则与限制见 `docs/DRAWING.md` |
| 外部工具 | LibreOffice 26.8.1.1、FreeCAD 1.1.4（`freecadcmd --version` 正常）、DWSIM 9.0.5、uv 0.13.5、`.venv-sim`（pyomo/rdkit/idaes）已安装 |
| 面板注册 | `sidebar.panellist` 与 `main` 槽位中 `chemellm` 均 active（来自实时页面 inspect） |
| enforce 门禁 | 内核 `CHEMELLM_PHASE_GATE=enforce`：intake 阶段调用 `material_balance` → HTTP 409；补齐依据后 → HTTP 200。插件侧经覆盖包实测：requirements 阶段 `chem_calc` 被守卫拒绝，移除覆盖包后回退 advisory（放行 + 警告） |
| review 规则 | 负例项目正确报告「依据数值缺少单位/条件/来源/理由」「成果计划缺少对应文件」；演示项目复检 ready，未校验计算进入 warnings |
| 成果包校验 | `scripts/verify_bundle.py`：演示 zip 13 条目、manifest 7 文件哈希全部匹配（VERIFY OK） |
| 项目删除 | `DELETE /v1/projects/<id>` 实测 200（清理 smoke 项目）；修复了归档 schema 的 FK 依赖 |
| 端到端 | 示例项目走到 `done`：校核 `ready=true` 后打包 296 KB zip；中间曾正确拦截“B03 未映射到成果” |
| Office 预览 | ⚠️ LibreOffice 已装且手工转换成功，但内核在 DSH 沙箱内触发的 headless 转换会挂起；DOCX 预览回退文本，PDF 直出不受影响 |
| 视觉截图 | **未完成**：DSH 对非 GUI 浏览器返回 `403 Browser access is disabled`，无法用 Playwright 截图；面板渲染请在 GUI 内刷新后目视确认 |

## 边界与限制（v0.1）

- 单用户、单机、loopback；没有多租户/权限/计费。`token` 为空时本机任意进程都能访问内核，介意时请设置。
- 自动校核 ≠ 专业审核；`chem_review` 只做数据与文件层面的自动检查。
- 外部软件：DWSIM 9.0.5 已通过外部自动化接入（加载/求解 `.dwxmz/.dwxml`，输出 JSON/CSV；不创建/编辑流程图）；FreeCAD 参数化三维已接入（FCStd/STEP）；P&ID 已升级为 A1 规范化示意（图框/标题栏/设备表/仪表阀门表/管线表，不按比例）；商业软件（Aspen/Icarus/PV Elite/AutoCAD）未授权。
- 域工具映射：22 个计算模型、12 个证据/检索工具、报告与图纸生成已覆盖；其余旧工具（`equipment_save/query`、`drawing_read`、`dataset_inspect/analyze_dataset` 等）通过 `chem_tool` 透传调用。
- Office 预览：LibreOffice 已安装，但在 DSH 沙箱内由内核触发的转换会挂起；建议在普通终端启动内核后再试，或直接用请求的 PDF 输出。
- 计算模型沿用原项目范围与假设（如 PR kij=0、理想精馏、UNIFAC 预测等），结果需工程判断。
- 原项目 `old/web`、`old/Dockerfile`、云部署脚本仅作归档，不参与本地运行。

## 原项目关系

原 ChemELLM（九页 Web、自研 agent 循环、云端 Docker 部署）已整体移入 `old/`。本版本只保留其**计算与工程数据能力**作为内核，把**交互、编排、UI**交给 DSH：会话历史、模型调用、审批、子代理都由 DSH 提供，不再自研。
