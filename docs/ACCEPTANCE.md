# 本地版验收记录（living document）

> 目标与判据见 [GOAL.md](GOAL.md)。每轮开发后更新本文件；失败与缺项保留，不删改历史。
> 记录格式：状态 / 证据（命令输出、文件路径）/ 下一步。

## 当前状态（v0.1 本地骨架，2026-10-22）

| 项 | 状态 | 证据 |
|---|---|---|
| 原项目归档 | ✅ | `old/` 含 app/web/tests/docs/data/云部署文件；根目录不再有旧入口 |
| 本地内核 | ✅ | `kernel/server.py`；`/v1/health` 200；数据在 `data/`、快照在 `.chem/` |
| DSH 插件 | ✅ | `@local/dsh-chemellm` installed/applied；`sidebar.panellist`+`main` 槽位 `chemellm` active |
| 域工具 | ✅ 12 个 | `chem_project/intake/requirements/plan/object/calc/evidence/generate/review/bundle/artifact/tool` |
| 旧工具透传（M1） | ✅ 完成 | Host 重启后主包 `chem_tool` 已 live：列出 49 个可执行工具，实测 `equipment_query`、`convert_units`（1 bar = 100 kPa）；伴生包 `chemellm-legacy` 已从 profile 移除 |
| 外部工具安装 | ✅ | LibreOffice 26.8.1.1、FreeCAD 1.1.4（`freecadcmd --version` 正常）、DWSIM 9.0.5、uv 0.13.5；`.venv-sim`：pyomo 6.10.1 / rdkit 2026.9.1 / idaes-pse 2.13.0 |
| Office→PDF 预览 | ⚠️ 受限 | LibreOffice 手工转换成功；内核在 DSH 沙箱内触发的 headless 转换会挂起（soffice.bin 不退出），DOCX 预览回退文本；PDF 直出不受影响 |
| IDAES 求解器扩展 | ✅ | `data/idaes/bin/ipopt.exe` 3.13.2；Pyomo `SolverFactory('ipopt')` 求解 `x²=4` → `x=2.0`，termination `optimal`；`scripts/sim-env.cmd` 提供带环境变量的 shell |
| 内核 `enforce` 门禁（M2） | ✅ | `CHEMELLM_PHASE_GATE=enforce`：intake 阶段调用 `material_balance` → HTTP 409；补齐 requirements/plan/basis 后 → HTTP 200 |
| 插件 `phaseGate: enforce`（M2） | ✅ | 覆盖包 `@local/dsh-chemellm-enforce`（仅 patch）装入后：requirements 阶段 `chem_calc` 被守卫拒绝「当前项目阶段为 requirements…」；补齐后成功 |
| 插件门禁回退 | ✅ | 移除覆盖包后：requirements 阶段 `chem_calc` 放行并返回 advisory 警告（非拒绝），证明配置可切换 |
| review 规则增强 | ✅ | 负例项目产生 blockers：「依据数值缺少单位/条件/来源/理由：b1/conversion」「成果计划缺少对应文件：D1」；演示项目复检 ready，warnings 记录未校验计算 |
| 成果包校验 | ✅ | 新增 `scripts/verify_bundle.py`：演示 zip 13 条目、manifest 7 文件哈希全部匹配（VERIFY OK）；smoke zip 同流程生成 |
| 项目删除接口 | ✅ | `DELETE /v1/projects/{id}`：删除测试项目均返回 200；修复归档 schema 的 FK 依赖（泛化清理 + 关 FK 后按表删除）；清理后仅剩演示项目 |
| 端到端演示 | ✅ | 示例项目走到 `review ready=true` → `done`，zip 296 KB；重新打包后 manifest 校验通过 |
| 冒烟测试 | ✅ | `scripts/smoke.py` 全链路通过（增强 review 规则后再次通过） |
| 技能 | ✅ | `.dsh/skills/chem-engineering/SKILL.md` 已被 DSH 技能目录发现 |
| 视觉截图 | ⚠️ 未完成 | DSH 对非 GUI 浏览器返回 `403 Browser access is disabled`，需在 GUI 内目视确认 |
| 标准文件（用户提供） | ✅ | 5 份已登记进案例 A：GB/T 3915-2021（8 页）、GB/T 150.1-2024（51 页）、GB 36894-2018（7 页）、HG/T 20519-2009（225 页六部分合订）、HG/T 20570-95（43 页，本 PDF 为 20570.2 安全阀分册）。扫描版已渲染页面图（`standards/*-pages/`）供逐页读取；明细见 `docs/STANDARDS.md` |
| 强制国标（自行获取） | ✅ | 平台已从政府公开渠道下载并登记：GB 18218-2018（12 页，重大危险源辨识）、GB 31571-2015（34 页，石油化学工业污染物排放标准）；GB 36894-2018 个人/社会风险基准已逐页核对。台账见 `docs/MANDATORY_GB.md` |
| 标准政策 | ✅ | 行标 HG/T、推荐标 GB/T 暂停深究；强制 GB 优先遵守；未取得原文的强制国标只写“待获取原文核对”，不写具体限值 |
| 案例 A（M3） | ✅ 二轮闭环 | 35 条要求（31 必需）全部登记；**13 项成果计划**，31/31 必需要求映射；**4 个工程对象**（basis/streams/equipment/hazard）、**11 条计算记录**、**23 个文件**：PFD+P&ID（SVG/PDF/DXF/JSON）、设计说明与安全环保合规说明（DOCX/PDF）、xlsx 数据表、FreeCAD FCStd/STEP、5 份标准 PDF；`chem_review` **ready=true**（仅 economics warning），zip **29 条目/23 文件哈希全部匹配**，phase `done` |
| 新增生成工具（M3） | ✅ | `export_xlsx`（6 工作表）与 `export_freecad`（FCStd+STEP，7 台设备）已接入 execute；`/v1/tools` 可执行 51 个 |
| 强制国标落地（M3） | ✅ | 新建 `hse-basis` 对象登记 GB 36894 个人风险基准、GB 18218 临界量（H2 5 t、苯乙烯 500 t）、GB 31571 水/气限值（表1/3/4/6，含页码与引句）；生成《安全环保与强制国标合规说明》；明确未做 QRA/环评/HAZOP，不声称达标 |
| 案例 A 遗留 | ⚠️ | `economics` 无显式校验（warning）；三维为简化布置，未做碰撞/检修/安全间距校核；设备尺寸为占位参数；P&ID 为简化草图；设备水力学/换热器详细/HAZOP/控制仪表待补 |
| 案例 B（M4） | ✅ 迁移闭环 | 苯-甲苯精馏（100 kmol/h，常压）：6 条要求、4 项成果计划（全部映射）、3 个对象、**11 条计算**、**14 个文件**（设计说明 DOCX/PDF、PFD+P&ID 的 SVG/PDF/DXF/JSON、xlsx、FCStd/STEP、GB 18218 PDF）；`chem_review` **ready=true**（heat_exchanger/economics 无校验 → warning），zip **21 条目/14 文件哈希全部匹配**，含 `recompute.md` |
| 迁移性观察 | ⚠️ | 可复用：二元 MESH（支持 benzene/toluene/ethylbenzene/styrene）、捷算法、PR 闪蒸、换热器、夹点、经济、PFD/DXF、xlsx、FreeCAD。硬编码：`material_balance`/`reaction_thermo` 仅乙苯-苯乙烯；塔模型仅理想 Raoult 与 4 组分；无动力学/塔水力学/合规 P&ID |
| 成果包复算说明 | ✅ | 内核打包新增 `recompute.md`：启动内核、按 `calculations.json` 重放各计算、重生成文件、SHA256 对照 manifest；两案例 zip 均含该文件 |

## Goal 完成判据对照

| 判据 | 证据 |
|---|---|
| 1 工具链完整 | 51 个可执行工具（含 `chem_tool` 透传与 `export_xlsx/export_freecad`）；README 工具表一致 |
| 2 两个案例闭环 | 案例 A（35 要求/31 映射/23 文件）与案例 B（6 要求/4 成果/10 文件）均 `review ready=true`，zip 哈希校验通过 |
| 3 门禁与审核 | 内核 enforce 实测 409→200；插件覆盖包 enforce 实测拦截、移除后回退 advisory；review 与专业审核分离（`professionalReview: not_reviewed`） |
| 4 质量与可验证 | `smoke.py` 通过；`py_compile`/`node --check` 通过；`verify_bundle.py` 对两案例 VERIFY OK |
| 5 文档 | README、QUICKSTART、GOAL、ACCEPTANCE、TOOLS、STANDARDS、MANDATORY_GB、STANDARDS 均更新 |

## 下一步（按优先级）

1. **案例 A 深化**：设备水力学与换热器详细设计、安全阀选型（HG/T 20570.2 扫描页）、HAZOP 工作表、控制回路清单、消防/总图（GB 50160/GB 50016 待获取原文）、逐项覆盖台账。
2. **工具深度**：P&ID 结构化（按 HG/T 20519 扫描页读取）、DWSIM 自动化与 `.dwxmz` 源文件。
3. **扩展案例**：更多物系/规模/装置类型，继续检验迁移性。
4. **强制国标补全**：按 `docs/MANDATORY_GB.md` 清单继续自行检索（GB 50160/50016/30871/16297/8978/12348/14554/18597/50058/50057/12158 等）。
5. **M5**：文档收尾、回归、评估是否满足 GOAL 完成判据。

## 变更日志

- 2026-10-22：本地骨架完成。原项目移入 `old/`；内核 + 插件 + 脚本 + 文档 + 技能落地；演示项目 end-to-end 通过；插件安装并验证槽位；截图受 403 限制。
- 2026-10-22（Goal 第 1 轮）：M1 旧工具透传落地（伴生包 `chem_legacy` live，49 个可执行工具可调）；主包 `chem_tool` 待 Host 重启生效；M2 内核 enforce 实测 409/200；内核新增 `DELETE /v1/projects/{id}` 并修复 FK 删除；清理测试项目，仅保留演示项目。
- 2026-10-22（Goal 第 2 轮）：M2 完成——插件 `phaseGate: enforce` 经覆盖包实测拦截、移除后回退 advisory；review 新增依据字段完整性/成果文件覆盖规则（负例验证）；新增 `scripts/verify_bundle.py` 并验证 manifest 哈希；演示项目复检/重打包；测试项目清理后仅剩演示项目。
- 2026-10-22（Goal 第 3 轮）：Host 重启后 M1 收尾——主包 `chem_tool` 生效并实测调用，伴生包移除；用户授权下装入 LibreOffice/FreeCAD/DWSIM/uv 与 `.venv-sim`（pyomo/rdkit/idaes）；内核补 LibreOffice 转换封装与 artifact 预览字段；记录 Office 预览沙箱限制与 IDAES 下载重试；新增 `docs/TOOLS.md` 工具清单。
- 2026-10-22（案例 A 启动）：用户提供 GB/T 3915-2021、GB/T 150.1-2024 并确认“开源替代 + 自查资料”。案例 A 项目建立：3 份资料登记、35 条要求、12 项成果计划（31/31 必需映射）、2 个依据对象（产品规格/标准引用、规模/转化率/水烃比假设）、5 项计算、概念 PFD、设计说明 DOCX/PDF；zip 15 条目/9 文件哈希校验通过。首轮 blockers：A-L04（三维源文件）、A-S03（xlsx 经济表）；economics 无显式校验（warning）。
- 2026-10-22（Goal 第 4 轮）：内核新增 `export_xlsx`（openpyxl 六工作表）与 `export_freecad`（FreeCADCmd 生成 FCStd+STEP，7 台设备参数化布置），经 `chem_tool` 实测成功；案例 A 复检 **ready=true**（仅 economics warning），phase `done`；重打包 23 条目/17 文件哈希全部匹配（17.2 MB，含 5 份标准 PDF）；可执行工具增至 51 个。首次尝试因缺少 `artifact_record` 导入返回 500，已修复并复测。
- 2026-10-22（Goal 第 5 轮）：案例 A 增加 `hse-basis`（GB 36894 个人风险、GB 18218 临界量、GB 31571 表1/3/4/6 限值，均带页码/引句）与 `equipment-list`（7 台设备占位尺寸）；新增成果 A-HSE（安全环保与强制国标合规说明 DOCX/PDF）；生成简化 P&ID（SVG/PDF/DXF/JSON）；复检 ready=true（23 文件/13 成果/4 对象/11 计算），重打包 29 条目/23 文件哈希全部匹配；`docs/MANDATORY_GB.md` 记录具体限值。
- 2026-10-22（Goal 第 6 轮）：迁移案例 B（苯-甲苯精馏）从空项目完成：6 条要求、4 项成果计划全映射、3 个对象、10 条计算（捷算/MESH/PR/换热器/夹点/经济 + 导出）、10 个文件；`chem_review` ready=true；zip 17 条目/10 文件哈希全部匹配。内核打包新增 `recompute.md`（重放计算 + 校验说明），两案例 zip 均含该文件并重新 VERIFY OK；smoke 回归通过；清理测试项目与旧包，仅保留 A/B 两案例。
- 2026-10-22（UI 修复）：面板「新建项目」点击无反应——原因是 `window.prompt` 在 DSH 嵌入式 WebView 中不可用（返回空/被拦截），代码直接 return。改为**内联输入框 + 创建/取消按钮**（Enter 创建、Esc 取消），不再依赖 prompt；`node --check` 通过。已安装插件为 workspace 目录 junction，刷新页面即可加载新 client.js。
- 2026-10-22（405 修复）：创建请求返回 HTTP 405，根因是 Host 代理注册了带尾斜杠的前缀路由 `/chemellm/`，而 DSH WebServer 的 prefix 匹配会拼成 `${prefix}/`，导致 `/chemellm/api/*` 全部不匹配、落到静态 fallback（对 POST 返回 405）。修复：(1) 面板改为**直连内核** `http://127.0.0.1:8765/v1`，内核启用 loopback CORS（`CHEMELLM_CORS_ORIGINS` 可限定来源）；(2) Host 代理注册路径改为 `/chemellm`（需 DSH 重启后生效，面板已不依赖）。实测 CORS 预检与 POST 均返回 `access-control-allow-origin`。
- 2026-10-22（赛题复跑）：新建项目 `81a186c1a027449298bc8a57a84ae175` 端到端复跑 2026 赛题：登记任务 PDF（5 页）→ 35 要求/12 成果计划（31/31 必需映射）→ 5 项计算（物料/热力学/50 级 MESH/UNIFAC/经济，校验全通过）→ basis/streams 对象（带单位/条件/来源）→ 报告 DOCX/PDF、PFD SVG/PDF/JSON/DXF、xlsx、FCStd/STEP → `chem_review` **ready=true**（仅 economics warning）→ zip **17 条目/10 文件哈希全部匹配**。与案例 A 原记录逐项对比：5 个模型的关键结果 **全部 MATCH（REPRODUCIBLE）**。本次复跑未生成 HSE 报告与 P&ID（案例 A 有），属演示级复跑。
- 2026-10-22（三维文件"打开为空"排查）：用 FreeCADCmd 打开生成的 FCStd/STEP 复核——**文件本身有效**：7 个 Solid，体积/包围盒正确（如 T-101 24 m 高、TK-101 8 m 直径），STEP 含 7 solids。问题出在预览链路：面板对 FCStd/STEP 直接回传二进制，浏览器显示空白。修复：`export_freecad` 额外生成等轴测 SVG 预览并让 FCStd/STEP 的 preview 指向它（实测返回 `image/svg+xml`）；磁盘文件名改为 ASCII（`layout.FCStd`/`layout.step`），中文仅作显示名；新增 `scripts/prune_3d.py` 清理重复三维记录。A/B/复跑三项目复检均 ready，zip 分别 31/24、22/15、18/11 条目/文件哈希全匹配。
- 2026-10-22（STEP 打开空视图）：用户截图显示 FreeCAD 中树里有 7 个 `Open CASCADE STEP translator` 对象但 3D 视图空白。复现 `Import.insert` 后确认：对象 `Visibility=True`、Shape 有效；判断为 **默认相机未适应场景**（模型跨度约 40 m × 18 m × 24 m，默认视图可能落在 R-101 内部）。处置：面板文件页与工具 warning 增加“视图 → 全部适应（Fit all）”提示；未改几何。若仍无效，再考虑导出 1:1000 预览件（非工程尺寸）。
- 2026-10-22（绘图工具落地）：新增 `kernel/drawing_tools.py` 与三个工具（`pid`、`pid_check`、`cad_part`），可执行工具 54 个。
  - **P&ID**：结构化 nodes/edges（设备/仪表/控制阀 + 工艺/信号/联锁 + 管线号）→ 校验 → SVG/PDF/DXF/JSON + DEXPI 风格 XML 子集；案例 A 生成 19 节点/24 边（5 仪表、3 控制阀），校验通过；PDF 内嵌中文字体（simhei/Deng/msyh 回退）。负例验证：缺工艺线的控制阀被拦截（"FV-101：控制阀没有工艺管线"）。
  - **设备 CAD**：`cad_part` 参数化（vessel/column/tank/exchanger，筒体 + 2:1 椭圆封头 + 裙座 + 接管），生成 FCStd/STEP/立面 SVG；R-101（DN3000×12000）与 T-101（DN2400×20000）经 FreeCADCmd 复核各 1 个有效 Solid。
  - 修复：成果包内同名文件（多次 P&ID/多台设备）会互相覆盖导致哈希不匹配 → bundle 归档名改为 `files/<artifactId8>-<name>`；案例 A 重打包 **52 条目/45 文件哈希全部匹配（VERIFY OK）**。
- 2026-10-22（工程化绘图升级）：绘图从“示意图”升级到工程图幅。
  - **P&ID → A1 工程图**：新增 `kernel/pid_sheet.py`；841×594 mm 图框 + 分区编号 + 标题栏/修改栏 + 图例 + 说明 + 设备一览/仪表与联锁/管线表；正交布线避让设备、ISA 风格仪表圆/控制阀、信号虚线与联锁点划线；标注“不按比例（示意）”，PDF 内嵌中文字体。案例 A 19 节点/24 边、5 仪表/3 控制阀，校验通过；负例仍正确拦截缺工艺线的控制阀。
  - **设备图 → A3 工程图**：新增 `kernel/cad_engineering.py`；A3 立面图含总高/切线长/直径尺寸、接管标高、接管表、设计数据、说明与标题栏；壁厚按 GB/T 150.1-2024 内压简化式计算（R-101：计算 3.8 mm→取 6 mm；T-101：3.01→6 mm），重量/接管法兰写入 BOM JSON；实体加接管法兰，未抽壳（图注明确）。
  - **修复**：PDF 虚线状态污染后续矩形/多边形（导致设备轮廓变虚线）→ 每个填充/描边前重置 dash；表格行高/列宽与 A1 区块重排，消除设备表与图例重叠；P&ID 比例改“不按比例（示意）”；管线表增加“共 N 条，显示前 8 条”说明；FreeCAD 实体裙座重量按实际壁厚修正（R-101 由 16.9 t 修正为 1.78 t）。
  - 案例 A 复检 ready=true（22 条计算、65 个文件）；zip **72 条目/65 文件哈希全部匹配（VERIFY OK）**；`smoke.py` 通过。
  - 文档：新增 `docs/DRAWING.md`（schema、规则、参数、限制）；README/TOOLS 同步。
- 2026-10-22（插件自包含部署）：按用户确认“能力必须随插件打包、换 DSH 后同等可用”，把运行时纳入插件：
  - 新增 `dsh-chemellm/runtime/`：便携 CPython 3.12.7 embeddable + 58 个依赖（fastapi/uvicorn/scipy/thermo/CoolProp/cantera/reportlab/ezdxf/openpyxl/python-docx/pptx/pypdf/pdfplumber/pypdfium2/pillow/pint/httpx/matplotlib…）+ 内核 4 个模块 + 归档 `app/` + `requirements.txt`。
  - 新增 Host 自动拉起：`autostart` 探测 `/v1/health`，失败时用包内 Python 启动 `runtime/kernel/server.py`，数据默认 `<DSH_PROFILE_DIR>/chemellm-data`；插件释放时停止子进程。
  - 内核路径解析支持工作区与运行时两种布局（`CHEMELLM_APP_DIR`/`CHEMELLM_DATA_ROOT`/`CHEMELLM_KERNEL_DATA`）。
  - 实测：便携运行时在 8799 端口启动内核 → `/v1/health` 200、**54 个可执行工具**、成功生成 P&ID（SVG/PDF/DXF/JSON/DEXPI 五件套）；`python -c "import fastapi, scipy, thermo, reportlab, ezdxf, openpyxl"` 通过。
  - 新增 `scripts/package-plugin.ps1`：组装 `dist/dsh-chemellm/` 并生成 `dsh-chemellm-<日期>-win-x64.zip`（含 SHA256SUMS）。
  - 能力边界：纯 Python 能力全部随包；FreeCAD/LibreOffice 不随包，已装则可用、缺失时工具返回明确错误（与用户确认一致）；运行时仅 Windows x64。
  - **打包结果**：`dist/dsh-chemellm-20261022-win-x64.zip`，**159.1 MB**（解包 508 MB / 10,820 文件），含 `SHA256SUMS.txt`；从该解包目录直接启动内核实测：`/v1/health` 200、54 个可执行工具、`server.py` 哈希与清单一致。
  - **自动拉起等价验证**：按 Host 相同方式 spawn（cwd=`runtime`、`CHEMELLM_APP_DIR=runtime/app`、`PYTHONPATH=site-packages;app`）在 8801 端口启动成功，health 200。Host 插件本身仍需 **重启 DSH** 才会加载新代码。
  - **待实测**：Host 自动拉起需重启 DSH 才能生效（当前运行中的 Host 仍是旧代码）；已用等价 spawn 命令验证运行时内核可独立启动。
- 2026-10-22（P0-1：P&ID 数据链）：
  - 新增 `kernel/pid_data.py` 与工具 `pid_data`（可执行工具 54→**55**）；从 P&ID 模型生成管线表、MTO、仪表索引、I/O 清单、联锁因果表（C&E）、调节信号表。
  - 输出：xlsx（7 个工作表）、5 个 CSV、DOCX、JSON；MTO 中弯头/三通/法兰为拓扑估算并逐项标注，I/O 信号类型按位号推断并标注“待定”。
  - 正例：案例 A 生成 **15 条管线、13 项 MTO、8 个仪表/阀门、8 点 I/O、2 条联锁（2 原因×1 后果）**；xlsx 管线表 16 行、材料表 14 行、仪表索引 9 行、IO 9 行、C&E 3 行。
  - 负例：重复管线号被 `pid_data` 拒绝（“管线号重复：PL-101-100-A1A”）；`chem_tool` 接线测试通过（临时项目已删除）。
  - 案例 A 新增成果计划 `A-PID-DATA`（映射 P04/P05，格式 xlsx/docx/csv/json）；`chem_review` ready=true（23 条计算、73 个文件）；zip **80 条目/73 文件哈希全部匹配（VERIFY OK）**。
  - 运行时 `runtime/kernel` 已同步 `pid_data.py`/`server.py`；插件 zip 待五项完成后统一重打包。
- 2026-10-22（P0-2：设备数据表/规格书）：
  - 新增 `kernel/datasheet.py` 与工具 `equipment_datasheet`（可执行工具 55→**56**）；支持容器/塔器/储罐/换热器/泵/压缩机。
  - 内容：设计条件、材料与尺寸、壁厚（GB/T 150.1 内压简化式，计算/选取值）、容积/筒体重量估算、接管表、供货范围、检验与试验、标准引用、限制；缺失项标注“待定/待厂家确认”，不编造。
  - 输出 DOCX/PDF（A4 中文表格）/JSON；正例：案例 A 生成 R-101、T-101、E-101、P-101 四份数据表（R-101：φ3.8→6 mm、91.9 m3、5338 kg；T-101：3.01→6 mm、94.1 m3）。
  - 负例：设计压力 50 MPa 超 GB/T 150.1 范围被拒绝；重复位号被拒绝；`chem_tool` 接线测试通过。
  - 案例 A 新增成果计划 `A-DATASHEET`（映射 E01/E02/E03/E04/D03，格式 docx/pdf/json）；`chem_review` ready=true（15 成果计划、24 条计算、76 个文件）；zip **83 条目/76 文件哈希全部匹配（VERIFY OK）**。
- 2026-10-22（P0-3：安全阀/爆破片选型）：
  - 新增 `kernel/relief.py` 与工具 `relief_sizing`（可执行工具 56→**57**）；支持气体/蒸汽临界与亚临界流、液体、火灾工况；API 526 标准孔径选型；校核能力利用率、积聚压力（110%/121%）、背压（常规 10%/波纹管 30%）、设定压力≤设计压力；输出残差。
  - 公式按 API 520/521/526 公开资料实现，来源与“原文未取得，待核对”写入计算书；同时引用已登记的 GB/T 150.1 与 HG/T 20570.2。
  - 正例：R-101 气体阻塞流（1000 kg/h、M18、k1.3、500 K、0.5/0.8 MPa）→ 所需 315 mm2，选 API 526 **G**（324.5 mm2），利用率 97.1%，四项校核通过；V-101 火灾（30 m2 润湿、潜热 320 kJ/kg）→ 1866 mm2，选 **M**（2322.6 mm2），利用率 80.4%，通过。
  - 负例：设定压力>设计压力、缺少分子量、液体火灾工况均被拒绝。
  - 案例 A 新增成果计划 `A-RELIEF`（映射 P01/F05，格式 docx/pdf/json）；`chem_review` ready=true（16 成果计划、26 条计算、82 个文件）；zip **89 条目/82 文件哈希全部匹配（VERIFY OK）**。
  - 运行时 `runtime/kernel` 已同步 `relief.py`/`server.py`；插件 zip 待五项完成后统一重打包。
- 2026-10-22（P0-4：HAZOP/LOPA 工作表）：
  - 新增 `kernel/hazop.py` 与工具 `hazop_lopa`（可执行工具 57→**58**）；支持节点划分、偏差矩阵（引导词×参数）、原因/后果/现有措施/建议、风险等级（严重度×可能性）；LOPA 场景计算（初始频率×独立 IPL PFD、缓解频率、所需 RRF、SIL 初判）。
  - 未提供 deviations 的节点自动生成偏差骨架行并标注“骨架行/待分析”，不编造原因后果。
  - 正例：案例 A 生成 3 个节点、13 行 HAZOP（5 行已分析 + N3 骨架）、2 个 LOPA 场景；L-01（0.1/a×0.1×0.01=1e-4/a）不满足 1e-5/a 目标，L-02（增加独立联锁 0.01）缓解至 1e-6/a 满足。
  - 负例：非法引导词（“高于”）、PFD=1.5 均被拒绝。
  - 案例 A 新增成果计划 `A-HAZOP`（映射 S01，格式 xlsx/docx/json）；`chem_review` ready=true（17 成果计划、27 条计算、85 个文件）；zip **92 条目/85 文件哈希全部匹配（VERIFY OK）**。
  - 文档：新增 `docs/HAZOP.md`（输入 schema、风险矩阵、LOPA 公式、SIL 分级与限制）；TOOLS/README/QUICKSTART 同步。
  - 运行时 `runtime/kernel` 已同步 `hazop.py`/`server.py`；插件 zip 待五项完成后统一重打包。
- 2026-10-22（P0-5：标准条款符合性矩阵）：
  - 新增 `kernel/compliance.py` 与工具 `compliance_matrix`（可执行工具 58→**59**）；内置台账 29 条，覆盖 GB/T 3915-2021、GB/T 150.1-2024、GB 36894-2018、GB 18218-2018、GB 31571-2015、HG/T 20519、HG/T 20570.2 及项目要求。
  - 判定：有确定判据的条款自动对照（产品指标、设计范围、临界量、排放限值、完成状态）；其余由 `answers` 人工判定；未取得原文的条款固定“待核对”，不填具体限值。
  - 正例：案例 A 生成 29 条矩阵 → **符合 13 / 不符合 0 / 待确认 14 / 待核对 2**；按标准汇总：GB/T 3915 7/7 符合、GB/T 150.1 2/2 符合、HG/T 20570.2 1/1 符合、项目要求 3/3 符合；GB 36894/18218/31571 全部待确认（缺 QRA、在线量与源强）；HG/T 20519 两条款待核对。
  - 负例：非法判定状态（“合格”）、台账条款 ID 重复均被拒绝。
  - 案例 A 新增成果计划 `A-COMPLIANCE`（映射 B01/F05，格式 xlsx/docx/json）；`chem_review` ready=true（18 成果计划、28 条计算、88 个文件）；zip **95 条目/88 文件哈希全部匹配（VERIFY OK）**。
  - 文档：新增 `docs/COMPLIANCE.md`（台账、判定规则、限制）；TOOLS/README/QUICKSTART 同步。
  - 运行时 `runtime/kernel` 已同步 `compliance.py`/`server.py`；**P0 五项已全部实现**。
- 2026-10-22（P0 收尾：插件重打包与部署验证）：
  - 9 个运行时内核模块与工作区 `kernel/` 哈希一致（server/pid_sheet/pid_data/datasheet/relief/hazop/compliance/cad_engineering/drawing_tools）。
  - 重打包 `dist/dsh-chemellm-20261022-win-x64.zip`：**159.1 MB / 9,404 条目**（解包 9,376 文件），SHA256 `61152ff90bcdb05990976c1cf7c6a2bc288f7f6366b287e267bfa2ccd9cb7fe9`；`SHA256SUMS.txt` 抽样（compliance.py）一致。
  - 用打包后的 `runtime/python` 启动内核（8803 端口）→ `/v1/health` 200、**59 个可执行工具**；在临时项目中实际调用五项 P0 工具全部成功：`pid_data`（8 个文件）、`equipment_datasheet`（3）、`relief_sizing`（3）、`hazop_lopa`（3）、`compliance_matrix`（3）；临时项目已删除。
  - 案例 A 最终：35 要求 / 18 成果计划 / 28 条计算 / 88 个文件；`chem_review` ready=true；zip 95 条目/88 文件哈希全部匹配。
  - 边界不变：FreeCAD/LibreOffice 不随包；Host 自动拉起需重启 DSH 后生效；专业审核状态仍为 `not_reviewed`。
- 2026-10-26（P&ID 规范化升级）：
  - 新增 `kernel/pid_standard.py`，`pid` 工具改用新渲染器：设备符号（2:1 封头容器/塔板塔器/管壳换热器/泵/储罐/压缩机）、现场/盘装仪表泡、控制阀、管道手动/止回/安全/爆破片/盲板、管线号+规格+管道等级+保温/伴热、标题栏/修改栏/图例/设备表/仪表阀门表/管线表。
  - `pid_check` 新增技术内容警告：管线缺规格/等级/介质、仪表缺量程、设备缺材料、管道阀缺位号、标题栏缺项。
  - 正例：案例 A 规范化模型（15 条管线、5 台/套阀门、5 仪表、2 联锁）生成 SVG/PDF/DXF/JSON/DEXPI，`pid_check` 0 warnings；`pid_data` 汇总 15 条管线、15 项 MTO、5 阀门（含 HV-101 手动阀、CV-101 止回阀）、8 点 I/O。
  - 旧图与规范化对比：`docs/assets/pid-before-after.png`；新图 `docs/assets/pid-standard-demo/pid.pdf`（另 SVG/DXF/JSON）。
  - 仍未实现：off-page 接续、管线断线、管道等级/材料等级库、设备管口表、仪表报警/联锁等级、企业图框模板；HG/T 20519 原文未取得，**不能声称条款级合规，也不能作为施工图**。
  - 运行时 `runtime/kernel` 已同步 `pid_standard.py`/`pid_data.py`/`server.py`；插件 zip 待统一重打包。

- 2026-10-27（DWSIM 接入）：新增 `kernel/dwsim_bridge.py` 与 `kernel/dwsim/DwsimRunner.exe`（C# .NET Framework，调用 DWSIM.Automation.Automation3）；`dwsim` 工具支持 status/run，加载 .dwxmz/.dwxml、求解并输出 `DWSIM结果.json` 与 `DWSIM物流表.csv`。用 DWSIM 9.0.5 自带 `Cavett's Problem.dwxmz` 实测：solved=true、20 条物料流、15 个单元操作；Host 内核与 8771 测试内核均通过，项目 `DWSIM 接入验证（Host / Cavett）` review ready=true 并打包。DWSIM 为外部 GPL-3.0 软件，不随插件分发；结果未做专业审核。

- 2026-10-29（DSH 插件重构与清理）：
  - Host 拆分为入口、工具、内核生命周期与代理；保留 12 个工具。面板、设置、文件与成果包统一通过 Host 同源代理访问，令牌由 Host 注入。
  - 自动启动传递令牌、门禁、数据路径与快照路径；开发优先当前源码和 `.venv`，分发使用便携 Python；并发请求只启动一个子进程，停用关闭自建内核。阶段检查读取最新项目，修复面板修改后阶段缓存过期。
  - 删除 legacy 透传包、enforce 配置覆盖包、5 组 DWSIM Probe 源码和二进制、源码目录的过期 SHA256 清单，共 16 个文件。保留正式 DWSIM Runner、`old/app` 和本地工程数据。
  - 打包只取 Python、第三方库、依赖清单与当前源码，排除旧 runtime 中的项目数据、快照、习题材料和缓存；显式包含目录安装需要的 `package.json`。
  - `node --test dsh-chemellm/test/*.test.js`：6 项通过。`scripts/test_kernel.py`：2 项通过，验证令牌、阶段拒绝、计算、报告、下载、打包哈希和依据变更使校核失效。
  - Playwright + Edge 隔离面板验证通过：新建、切换、校核、打包、同源下载链接、旧响应隔离；1280×850 与 860×760 截图已检查，0 页面异常。测试使用当前 Client 和 Host 代理，DSH 未运行，未改动 DSH profile，实际 DSH 加载仍需安装/重启后确认。
  - `node scripts/test_packaged_plugin.mjs`：使用包内 Python 启动真实内核，令牌、enforce、工具闭环及代理下载通过；独立测试数据已清理。Windows 系统临时目录对子进程的访问受限，分发测试改用工作区独立临时目录。
  - 最终 `dist/dsh-chemellm-20261029-win-x64.zip`：161.5 MiB，9386 项 SHA256 全部匹配，无 runtime/data、runtime/.chem、runtime/work_absorption。Python 依赖有上游弃用/资源警告，未影响回归通过。
