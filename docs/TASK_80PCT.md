# 任务设计：乙酸乙酯酯化—精制工艺包预可研（80% 工具覆盖验收）

> 任务性质：**工程任务 + 插件迁移验收**。不是纯演示；每个工具必须留下可核查的工程产物或项目记录，不允许“为空调用凑数”。
>
> 覆盖口径：本机 `/v1/tools` 当前 **60 个可执行工具**；80% = **48 个**。本任务要求 **50 个不同可执行工具（83.3%）**；另使用 **12 个 `chem_*` 领域工具**做编排。若把领域工具也计入 72 个插件工具，覆盖 **62/72 = 86.1%**。

## 1. 任务背景

某精细化工企业拟建一套 **50,000 t/a 乙酸乙酯** 装置，以乙醇和乙酸为原料、酸催化酯化，经脱轻、萃取/精制、废水与尾气处理后得到 99.5 wt% 乙酸乙酯产品。企业要求先做 **预可研级工艺包**，并借此验收本地工作台从旧接口迁移到新插件后的完整能力。

以下为**任务给定设计输入**（不是计算结果，执行时须以依据对象登记）：

- 产品规模：50,000 t/a，年运行 8,000 h，折合约 6.25 t/h；
- 原料：乙醇 95 wt%、乙酸 99.5 wt%，工业级；
- 反应：乙醇 + 乙酸 ⇌ 乙酸乙酯 + 水，酸催化；
- 产品：乙酸乙酯 ≥99.5 wt%；
- 边界：反应、分离、溶剂回收、废水/尾气预处理、公用工程与安全合规；
- 必须提供一份已建好的 DWSIM 稳态 flowsheet（`.dwxmz` 或 `.dwxml`），由工艺工程师在 DWSIM GUI 中创建，工作台只负责加载/求解/取数。

## 2. 任务输入

| 输入 | 用途 |
|---|---|
| 任务说明书 PDF（12 条要求） | `chem_intake`、要求登记 |
| 乙醇-水-乙酸乙酯 VLE/LLE 实验数据 CSV | `dataset_inspect`、`analyze_dataset`、`fit_data` |
| 旧版计算记录 1 份 | `calculation_read` 复用与对比 |
| 旧版 PFD/P&ID 草图 1 份 | `drawing_read` 复用与差异分析 |
| 3 篇文献 + 1 份标准 PDF | 证据链 |
| 设备/公用工程价格或估算依据 | `economics` |
| DWSIM 稳态 flowsheet | `dwsim` 交叉验证 |

## 3. 阶段、工具与交付物

### 阶段 A：项目定义与旧接口兼容（6 个旧工具 + 5 个领域工具）

| 工具 | 工程动作 | 产物/记录 |
|---|---|---|
| `project_context` | 读取当前项目上下文 | 项目上下文快照 |
| `engineering_status` | 检查旧接口迁移状态 | 迁移检查记录 |
| `engineering_requirements` | 用旧接口登记 12 条要求 | 要求清单 v1 |
| `engineering_plan` | 用旧接口建要求→成果计划 | 计划 v1 |
| `engineering_object` | 登记设计输入（规模、纯度、边界） | 依据对象 |
| `engineering_deliverable` | 登记旧接口交付物 | 交付物记录 |
| `chem_project` / `chem_intake` / `chem_requirements` / `chem_plan` / `chem_object` | 新接口同一项目建项与复核 | 项目、资料、要求、计划、依据 |

**兼容性要求**：旧接口与新接口必须指向同一 `projectId`，同类要求/依据不得出现两套互相矛盾的数据。

### 阶段 B：证据与数据质量（11 个证据工具 + 4 个数据/读取工具）

| 工具 | 工程动作 | 产物/记录 |
|---|---|---|
| `literature_search` | 检索乙酸乙酯酯化/共沸精馏文献 | 文献候选清单 |
| `open_literature_search` | 检索开放全文/报告 | 开放来源清单 |
| `pubchem` | 查询乙醇、乙酸、乙酸乙酯、水物性 | 物性卡 |
| `project_search` | 检索本项目旧资料 | 复用清单 |
| `fulltext_import` | 导入 3 篇 PDF 全文 | 全文记录 |
| `document_extract` | 抽取标准/文献中的条款与数据 | 抽取片段 |
| `document_read` | 逐页读取关键页 | 阅读记录 |
| `claim_save` | 保存“共沸组成/转化率/排放限值”等论断 | 论断清单 |
| `evidence_add` | 把引句绑定到论断 | 证据链 |
| `evidence_check` | 检查证据是否支撑论断 | 证据检查报告 |
| `evidence_export` | 导出证据包 | 证据包 JSON/MD |
| `dataset_inspect` | 检查 VLE 数据列、单位、缺失值 | 数据质量报告 |
| `analyze_dataset` | 统计组成/温度/压力范围与异常点 | 数据画像 |
| `calculation_read` | 读取旧版反应/精馏计算记录 | 对比基线 |
| `drawing_read` | 读取旧版 PFD/P&ID 草图 | 差异清单 |

**门禁**：没有 `evidence_check` 通过的论断，不得进入报告“结论”章节。

### 阶段 C：工艺计算（18 个计算工具）

| 工具 | 工程用途 |
|---|---|
| `properties` | 原料/产品物性、密度、焓 |
| `steam` | 低压/中压蒸汽公用工程 |
| `convert_units` | 单位与基准换算（wt%/mol%、kJ/kmol） |
| `material_balance` | 全流程物料衡算与收率 |
| `reaction_thermo` | 酯化反应热、绝热温升 |
| `mixture_reaction` | 多组分反应平衡/转化率 |
| `flash` | 反应器出口 PR 闪蒸 |
| `aqueous_flash` | 水相/有机相分相与共沸 |
| `condenser_flash` | 塔顶冷凝分相 |
| `distillation_shortcut` | 脱轻/精制塔简捷设计 |
| `column_mesh` | 精制塔 MESH 逐板核算 |
| `wet_column` | 尾气水洗/吸收塔 |
| `recycle_process` | 乙醇/乙酸回收循环 |
| `heat_exchanger` | 预热器/再沸器/冷凝器换热面积 |
| `pipe_pressure_drop` | 主要管线压降与泵扬程 |
| `pinch_analysis` | 换热网络夹点与公用工程目标 |
| `economics` | 投资/成本/产品单位成本 |
| `fit_data` | VLE 数据回归与模型参数 |

**计算要求**：每个计算记录输入、假设、单位、校验；结果必须能复算。关键流股（反应器出口、塔顶、塔底、产品、废水）进入物流表。

### 阶段 D：图纸、设备与安全（10 个专项工具）

| 工具 | 工程动作 |
|---|---|
| `pfd` | 生成带物流号的 PFD |
| `pid` | 生成 A1 规范化 P&ID |
| `pid_check` | 校验位号、连接、管线号、仪表量程 |
| `pid_data` | 从 P&ID 出管线表、MTO、仪表索引、I/O、C&E |
| `equipment_datasheet` | 反应器/塔/换热器/泵/储罐数据表 |
| `relief_sizing` | 反应器/塔顶回流罐安全阀或爆破片 |
| `hazop_lopa` | 3 个节点 HAZOP + LOPA 场景 |
| `compliance_matrix` | GB/T 150、GB 36894、HG/T 20519 等条款矩阵 |
| `export_xlsx` | 项目 6 表数据包 |
| `export_report` | 预可研报告 DOCX/PDF |

**一致性要求**：PFD、P&ID、P&ID 数据表、设备数据表、报告中的位号/物流号/规模必须同源；改一个必须重生成受影响文件。

### 阶段 E：DWSIM 交叉验证（1 个工具）

| 工具 | 工程动作 |
|---|---|
| `dwsim` | 加载工程师提供的 DWSIM flowsheet，`action=status` 检测、`action=run` 求解；把 DWSIM 的 T/P/质量流量与工作台简捷计算对比；差异>10% 的流股必须解释 |

通过标准：`solved=true`；至少 3 条关键物流可对比；DWSIM 未安装则任务**阻断**，不得用其他结果冒充。

### 阶段 F：校核、打包与交付

- `chem_review`：要求覆盖、依据、计算校验、文件完整性；
- `chem_bundle`：项目数据 + 计算 + 文件 + manifest；
- `chem_artifact`：列出/下载/预览成果；
- `chem_generate`：报告/PFD 的领域入口（与 `export_report`/`pfd` 至少一种对齐）；
- 旧接口 `engineering_deliverable` 已在 A 阶段登记，最终交付物引用同一记录。

**交付清单**：

1. 要求清单与成果计划（新旧接口一致）；
2. 证据包与数据质量报告；
3. 工艺计算书（18 类计算，含假设与校验）；
4. PFD、A1 P&ID、P&ID 数据表；
5. 设备数据表、安全阀计算书、HAZOP/LOPA、合规矩阵；
6. 预可研报告 DOCX/PDF、项目数据 xlsx；
7. DWSIM 对比记录；
8. `chem_review` 结果与 bundle zip。

## 4. 50 个可执行工具清单（去重）

**证据 11**：`literature_search`、`open_literature_search`、`pubchem`、`project_search`、`fulltext_import`、`document_extract`、`document_read`、`claim_save`、`evidence_add`、`evidence_check`、`evidence_export`

**数据/读取 4**：`dataset_inspect`、`analyze_dataset`、`calculation_read`、`drawing_read`

**旧接口/上下文 6**：`project_context`、`engineering_status`、`engineering_requirements`、`engineering_plan`、`engineering_object`、`engineering_deliverable`

**计算 18**：`properties`、`steam`、`convert_units`、`material_balance`、`reaction_thermo`、`mixture_reaction`、`flash`、`aqueous_flash`、`condenser_flash`、`distillation_shortcut`、`column_mesh`、`wet_column`、`recycle_process`、`heat_exchanger`、`pipe_pressure_drop`、`pinch_analysis`、`economics`、`fit_data`

**专项 10**：`pfd`、`pid`、`pid_check`、`pid_data`、`equipment_datasheet`、`relief_sizing`、`hazop_lopa`、`compliance_matrix`、`export_xlsx`、`export_report`

**DWSIM 1**：`dwsim`

合计 **50/60 = 83.3%**。

另用 12 个领域工具：`chem_project`、`chem_intake`、`chem_requirements`、`chem_plan`、`chem_object`、`chem_calc`、`chem_evidence`、`chem_generate`、`chem_review`、`chem_bundle`、`chem_artifact`、`chem_tool`（不计入 50）。

## 5. 不要求的 10 个工具（明确排除）

| 工具 | 排除理由 |
|---|---|
| `source_fetch` | 任务提供本地 PDF，用 `fulltext_import` 即可；只有 URL 源才需要 |
| `frontend_process` | 本流程为单反应+分离+循环，用 `recycle_process` 足够 |
| `wet_separation_train` | 尾气只做单塔水洗，`wet_column` 足够 |
| `cantera_equilibrium` | 本任务无燃烧/高温平衡场景 |
| `cantera_reactor` | 本任务无 Cantera 动力学反应器 |
| `cad_part` | 预可研不要求三维设备图，只要数据表 |
| `export_freecad` | 不做 3D 布置 |
| `equipment_query` | 不接设备库，直接按数据表输入 |
| `equipment_save` | 不维护设备台账 |
| `engineering_bundle` | 与 `chem_bundle` 重复；旧接口只验 requirement/plan/object/status/deliverable |

> 如果任务扩展到 3D 布置、燃烧/尾气焚烧或 URL-only 文献，可把上述工具补入，覆盖可提高到 55+/60；但本任务按 50 个设计。

## 6. 验收标准

### 6.1 覆盖

- 50 个不同可执行工具均在同一 `projectId` 下实际调用；
- 每个工具至少对应 1 个项目记录/产物/证据，**空调用不计**；
- 提交 `TOOL_LEDGER.md`：工具名、阶段、调用时间、产物路径或记录 ID；
- 自动统计 distinct 工具数 ≥48（80%）；本任务目标 50。

### 6.2 工程质量

- 12 条要求全部映射；`chem_review ready=true`；
- 每个数值有单位、条件、来源（假设/设计选择/文档/计算）；
- 关键流股物料/能量平衡闭合，偏差有解释；
- 文献论断有 `evidence_check`，未取得原文的标准条款标“待核对”；
- PFD/PID/数据表/设备表/报告位号一致；
- DWSIM `solved=true`，3 条关键物流与简捷计算对比，差异>10% 有解释。

### 6.3 诚实边界

- `professionalReview=not_reviewed`，不得声称已签审；
- P&ID 是规范化示意，不称条款级合规/施工图；
- DWSIM 是外部 GPL 软件，不随插件分发；未安装则任务阻断；
- 数据不足时标“待确认”，不编造厂家数据、标准原文或计算结果。

## 7. 建议排期（2 个工作日）

| 时间 | 工作 |
|---|---|
| Day 1 上午 | A 项目/要求/计划 + B 证据与数据质量 |
| Day 1 下午 | C 计算：物性/反应/分相/精馏/循环/换热/经济 |
| Day 2 上午 | D 图纸/数据表/安全/合规 + E DWSIM 对比 |
| Day 2 下午 | F review 修复、bundle、工具覆盖台账与交付说明 |

## 8. 任务成功的定义

不是“50 个工具都点过”，而是：

> 同一套乙酸乙酯工艺数据，经过要求→证据→计算→图纸→安全→DWSIM 对比→校核→打包，形成可复算、可追溯、边界诚实的预可研包；工具覆盖率达到 80% 以上，且每个工具都有工程产物为证。
