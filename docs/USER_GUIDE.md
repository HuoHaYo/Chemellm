# ChemELLM 本地化工工作台 · 插件使用教程

> 适用版本：DSH 插件 `@local/dsh-chemellm` v0.1.0，本地内核 **60 个可执行工具**。  
> 适用平台：Windows x64（插件包内置便携 Python 3.12）。  
> 原则：**数据与计算都在本机**；自动校核 ≠ 专业审核；不编造文献、厂家数据、标准条款。

---

## 1. 它能做什么

| 场景 | 对应能力 |
|---|---|
| 赛题/可研快速闭环 | 项目、要求、计划、依据、计算、报告、校核、打包 |
| 工艺图与交付数据 | A1 P&ID（SVG/PDF/DXF/JSON/DEXPI 子集）、管线表/MTO、仪表索引、I/O 清单、联锁因果表 |
| 设备询价 | 容器/塔器/储罐/换热器/泵/压缩机数据表（DOCX/PDF/JSON） |
| 安全分析 | 安全阀/爆破片选型计算书、HAZOP/LOPA 工作表 |
| 合规自查 | 标准条款符合性矩阵（符合/不符合/待确认/待核对） |
| 设备图 | A3 设备图 + FCStd/STEP（需目标机有 FreeCAD） |

---

## 2. 安装与启动

### 2.1 方式 A：开发模式（本仓库）

前置：本仓库已有 `.venv`，DSH 已安装 `@local/dsh-chemellm`。

```powershell
# 1) 启动本地内核（保持窗口运行）
.\scripts\start-kernel.cmd

# 2) 刷新 DSH 页面 → 左侧「化工工程」图标
```

内核默认监听 `http://127.0.0.1:8765`。

### 2.2 方式 B：独立部署包（换机器推荐）

1. 解压分发包 `dsh-chemellm-<日期>-win-x64.zip`；
2. 在 DSH 中用 `plugin_manager` 安装解压后的 `dsh-chemellm` 目录；
3. **重启 DSH**（Host 插件新代码/自动拉起在此之后生效）；
4. 插件会探测 `endpoint/v1/health`，不可达时用包内 `runtime/python/python.exe` 自动启动内核；
5. 数据默认写入 `<DSH_PROFILE_DIR>/chemellm-data`。

配置项在 `dsh-chemellm/cordis.patch.yml` 的 `chemellm` 行：

| 键 | 默认 | 说明 |
|---|---|---|
| `endpoint` | `http://127.0.0.1:8765` | 内核地址；端口也用于自动启动 |
| `token` | `''` | Host 访问令牌；自动启动时同步到内核，自行启动需设置 `CHEMELLM_KERNEL_TOKEN` |
| `phaseGate` | `advisory` | `enforce` 时越阶段调用会被拦截 |
| `autostart` | `true` | 探测不到内核时自动拉起 |
| `python` | `''` | 覆盖 Python 路径（默认包内运行时） |
| `dataDir` | `''` | 覆盖数据目录 |

面板、文件预览和下载统一经 DSH Host 的同源代理访问内核，浏览器不保存令牌。自动启动时也会同步 `phaseGate`，并把工程快照写入 `dataDir/.chem`。旧版的 legacy 透传包与 enforce 覆盖包已移除；升级时卸载这两个伴生插件，保留主插件并重启 DSH。

### 2.3 验证

```powershell
curl.exe -s http://127.0.0.1:8765/v1/health
# {"ok":true,...,"dataDir":"...","projectCount":N}

(Invoke-WebRequest http://127.0.0.1:8765/v1/tools -UseBasicParsing).Content
# executable 数量应为 60

# 包内运行时自检（独立部署包）
.\runtime\python\python.exe -c "import fastapi, scipy, thermo, reportlab, ezdxf, openpyxl, docx; print('runtime ok')"
```

### 2.4 停止与日志

- 开发模式：在内核窗口 `Ctrl+C`；
- 独立部署包：退出 DSH 时 Host 会停止子进程；
- 排查问题先看内核窗口/后台任务日志；不要同时起两个内核抢同一端口。

---

## 3. 界面导览

左侧「化工工程」→ 主面板：

| 区域 | 内容 |
|---|---|
| 顶部 | 项目下拉、刷新、「新建项目」（内联表单，输入名称即可） |
| 概览 | 要求/成果计划/工程对象/计算/文件计数，阶段进度（资料→要求→计划→依据→执行→校核→打包→完成） |
| 要求 | 编码、要求、是否必需、原文引句 |
| 计划 | 成果计划（key/标题/要求/格式）与对象计划 |
| 依据 | 工程对象列表（数值带单位、条件、来源） |
| 计算 | 计算记录、校验结果、计算 ID；点击查看详情 |
| 成果 | 资料与成果文件列表，支持预览/下载 |
| 验收 | 自动校核结果、blockers/warnings、「打包成果」按钮 |
| 设置 | 内核版本、阶段门禁、数据目录、项目数 |

阶段门禁默认 `advisory`（越阶段给警告）；`enforce` 时越阶段调用返回 `409`。

---

## 4. 第一个项目：从零到成果包

在任一会话中直接对模型说（工具名即函数名）：

```text
先用 chem_project 创建项目“示例·苯乙烯”；用 chem_intake 登记你的赛题/任务书 PDF（本仓库不提供原文）；
用 chem_requirements 登记 5 条要求（B01..B05）；用 chem_plan 建立成果计划（可研报告、物料衡算表、P&ID）；
用 chem_object 写入设计依据 basis-main（规模、纯度、压力、温度，带单位/条件/来源）；
用 chem_calc 算 material_balance；用 chem_generate 生成可研报告（docx+pdf）；
用 chem_review 自检；用 chem_bundle 打包。
```

推荐顺序与工具：

| 步骤 | 工具 | 关键点 |
|---|---|---|
| 1 | `chem_project` | `action=list/create/get`，返回 `projectId` |
| 2 | `chem_intake` | `path` 为工作区路径；返回哈希与页数 |
| 3 | `chem_requirements` | 每条 requirement 有稳定编码；题面要求零遗漏 |
| 4 | `chem_plan` | `deliverables` 映射 `requirementCodes`；`objects` 列对象 |
| 5 | `chem_object` | 数值必须带 `unit`、`origin`、`conditions` |
| 6 | `chem_calc` | `model` + `input`；缺参返回错误，不填假默认值 |
| 7 | `chem_generate` | `kind=report`（docx/pdf）或 `kind=pfd` |
| 8 | `chem_review` | `ready=true` 仅代表自动校核通过 |
| 9 | `chem_bundle` | 生成带哈希清单的 zip |

> `chem_review ready=true` 不等于专业审核；面板与验收记录仍标 `professionalReview: not_reviewed`。

---

## 5. 12 个主域工具速查

| 工具 | 用途 | 常用参数 |
|---|---|---|
| `chem_project` | 列表/创建/读取项目 | `action`, `name`, `projectId` |
| `chem_intake` | 登记工作区资料 | `path`, `name` |
| `chem_requirements` | 要求清单 | `action`, `items[{code,title,quote,...}]` |
| `chem_plan` | 要求→成果映射、对象计划 | `deliverables`, `objects` |
| `chem_object` | 设计依据/物流/设备/公用工程/安全/成本 | `kind`, `key`, `quantities[]`, `attributes` |
| `chem_calc` | 22 类计算模型 | `model`, `input` |
| `chem_evidence` | 文献检索、全文导入、证据与论断 | `action`, `arguments` |
| `chem_generate` | 报告/DOCX/PDF/PPTX/MD、PFD/P&ID 草图 | `kind`, `title`, `body`, `formats` |
| `chem_review` | 自动校核 | `projectId`, `note` |
| `chem_bundle` | 打包成果（zip + manifest） | `projectId` |
| `chem_artifact` | 列出/预览/下载成果文件 | `projectId`, `artifactId`, `mode` |
| `chem_tool` | 透传旧工具/扩展工具（不传 `tool` 时列出 60 个） | `tool`, `arguments` |

---

## 6. 五项 P0 工具教程

### 6.1 `pid_data` —— P&ID 工程数据链

**先有结构化 P&ID 模型**（`nodes`/`edges`），可与 `pid` 绘图共用同一份模型。

最小可用模型：

```json
{
  "title": "示例 P&ID",
  "drawing_number": "PID-DEMO-001",
  "nodes": [
    {"id": "R-101", "kind": "reactor", "label": "反应器", "x": 300, "y": 300, "spec": "DN3000x12000"},
    {"id": "T-101", "kind": "column", "label": "塔", "x": 600, "y": 300, "spec": "DN2400x20000"},
    {"id": "TIC-101", "kind": "instrument", "label": "TIC 温控", "x": 450, "y": 500}
  ],
  "edges": [
    {"source": "R-101", "target": "T-101", "kind": "process",
     "line_no": "PL-101-80-A1A", "medium": "反应产物", "spec": "DN80"},
    {"source": "TIC-101", "target": "R-101", "kind": "interlock", "label": "I-1"}
  ]
}
```

调用：

```text
chem_tool(projectId=..., tool="pid_data", arguments={...上面的模型...})
```

输出（8 个文件）：

- `P&ID数据表.xlsx`：管线表 / 材料表 / 仪表索引 / IO清单 / 联锁因果表 / 调节信号表 / 说明；
- `P&ID数据表.docx`、`P&ID数据.json`；
- `管线表.csv`、`材料表.csv`、`仪表索引.csv`、`IO清单.csv`、`联锁因果表.csv`。

注意：

- 结构性问题（重复管线号、端点缺失、控制阀无工艺线等）直接返回 `422`；
- MTO 中弯头/三通/法兰为**拓扑估算**，I/O 信号类型为**按位号推断**，成果中已标注“需复核/待确认”；
- 可与 `pid` 工具用同一模型生成 A1 图，保证图表一致。

### 6.2 `equipment_datasheet` —— 设备数据表/规格书

输入 `items` 数组，每台设备：

```text
chem_tool(projectId=..., tool="equipment_datasheet", arguments={
  "project": "示例项目",
  "items": [{
    "tag": "R-101", "name": "脱氢反应器", "equipment_type": "vessel",
    "design_pressure_mpa": 0.1, "design_temperature_c": 650,
    "operating_pressure_mpa": 0.1, "operating_temperature_c": 600,
    "medium": "乙苯/苯乙烯/氢气/水蒸气",
    "diameter_mm": 3000, "tangent_length_mm": 12000,
    "material": "0Cr18Ni9", "allowable_stress_mpa": 60,
    "corrosion_allowance_mm": 1.0, "joint_efficiency": 1.0,
    "nozzles": [
      {"tag": "N1", "dn": 250, "service": "气相出口", "flange": "WN PN16 RF", "position": "顶部"}
    ]
  }]
})
```

- 支持类型：`vessel / column / tank / exchanger / pump / compressor`；
- 输出 `设备数据表.docx`、`设备数据表.pdf`、`设备数据表.json`；
- 壁厚按 **GB/T 150.1-2024 内压简化式** 计算并取钢板系列值；容积/筒体重量为估算；
- 缺失项写“待定/待厂家确认”，不编造；
- 负例：设计压力 >35 MPa、重复位号等返回 `422`。

### 6.3 `relief_sizing` —— 安全阀/爆破片选型

气体/蒸汽阻塞流示例：

```text
chem_tool(projectId=..., tool="relief_sizing", arguments={
  "equipment_tag": "R-101", "device_type": "psv", "scenario": "blocked_outlet",
  "fluid": "gas", "relief_flow_kg_h": 1000, "molecular_weight": 18, "k": 1.3,
  "temperature_K": 500, "set_pressure_mpag": 0.5, "design_pressure_mpag": 0.8,
  "backpressure_mpag": 0.05, "valve_type": "conventional"
})
```

- 火灾工况：`scenario="fire"`，必须给 `wetted_area_m2`、`latent_heat_kj_kg`；
- 液体：`fluid="liquid"`，给 `liquid_flow_m3_h`、`liquid_density_kg_m3`；
- 爆破片：`device_type="rupture_disc"`；
- 输出计算书 DOCX/PDF/JSON：输入、逐步公式、所需面积、API 526 孔径选型、能力利用率、积聚压力/背压/设定压力校核、残差、来源与限制；
- 负例：设定压力 > 设计压力、缺分子量、液体火灾工况等返回 `422`；
- **API 520/521/526 原文未取得**：公式按公开资料实现，计算书明确标注“待核对”。

### 6.4 `hazop_lopa` —— HAZOP/LOPA 工作表

```text
chem_tool(projectId=..., tool="hazop_lopa", arguments={
  "project": "示例项目", "unit": "反应单元",
  "nodes": [{
    "id": "N1", "name": "脱氢反应器", "intent": "乙苯脱氢", "tags": ["R-101"],
    "parameters": ["温度", "压力"],
    "deviations": [{
      "guide_word": "高", "parameter": "温度",
      "causes": ["TIC 失效"], "consequences": ["超温、结焦"],
      "safeguards": ["TIC 联锁"], "recommendations": ["独立高温联锁"],
      "severity": 4, "likelihood": 3
    }]
  }],
  "lopa": [{
    "id": "L-01", "node": "N1", "scenario": "超温", "initiating_event": "TIC 失效",
    "frequency_per_year": 0.1, "severity": "major",
    "ipls": [
      {"name": "BPCS", "pfd": 0.1, "independent": true},
      {"name": "联锁", "pfd": 0.01, "independent": true}
    ]
  }]
})
```

- 输出 `HAZOP_LOPA工作表.xlsx`（节点/HAZOP/LOPA/说明）、DOCX、JSON；
- 未给 `deviations` 的节点会生成**骨架行**并标注“待分析”，不编造原因后果；
- LOPA 自动计算缓解频率、所需 RRF、SIL 初判；`independent: false` 的保护层不计入；
- 负例：非法引导词、PFD>1 返回 `422`；
- 工作表不替代 HAZOP 会议与签署；SIL 未做验证。

### 6.5 `compliance_matrix` —— 标准条款符合性矩阵

```text
chem_tool(projectId=..., tool="compliance_matrix", arguments={
  "project": "示例项目", "unit": "反应单元",
  "project_data": {
    "product_purity": 0.998, "product_eb": 0.0008, "product_polymer": 10,
    "design_pressure_mpa": 0.1, "design_temperature_c": 650,
    "qra_done": false, "relief_set_pressure_mpag": 0.5,
    "hazop_done": true, "pid_done": true, "datasheet_done": true
  },
  "answers": {
    "GB31571-COD": {"status": "待确认", "evidence": "未给出废水源强与处理流程"}
  }
})
```

- 内置 29 条台账（GB/T 3915、GB/T 150.1、GB 36894、GB 18218、GB 31571、HG/T 20519、HG/T 20570.2、项目要求）；
- 状态只能是 `符合 / 不符合 / 待确认 / 待核对`；
- 未取得原文的条款（如 HG/T 20519）固定“待核对”，不填具体限值；
- 可用 `ledger` 覆盖台账，用于其他项目/标准版本；
- 输出 xlsx（矩阵/汇总/按标准汇总/说明）、DOCX（A4 横向）、JSON。

---

## 7. 其他生成类工具

### 7.1 `pid` —— A1 规范化 P&ID

与 `pid_data` 同一模型：

```text
chem_tool(projectId=..., tool="pid", arguments={...nodes/edges...})
```

输出 `P&ID.svg/.pdf/.dxf/.json/.dexpi.xml`。当前版本参照 **HG/T 20519 内容深度 + ISA-5.1 符号**：2:1 封头容器/塔器/换热器/泵/储罐/压缩机，现场/盘装仪表泡，控制阀、手动/止回/安全/爆破片/盲板，管线号+规格+管道等级+保温/伴热，标题栏/修改栏/图例/表格。

> 仍为**规范化示意图**：未实现 off-page 接续、管线断线、完整管道等级库与材料等级库；未取得标准原文，不能声称条款级合规，也不能直接作为施工图。

### 7.2 `cad_part` —— A3 设备图 + CAD 实体

```text
chem_tool(projectId=..., tool="cad_part", arguments={
  "tag": "R-101", "equipment_type": "vessel",
  "diameter_mm": 3000, "tangent_length_mm": 12000,
  "design_pressure_mpa": 0.1, "design_temperature_c": 650,
  "material": "0Cr18Ni9", "allowable_stress_mpa": 60
})
```

- 输出 FCStd/STEP/A3 SVG/PDF/BOM JSON；
- **需要目标机安装 FreeCADCmd**，缺失时返回明确错误，其他能力不受影响；
- FreeCAD 打开若视图空白：执行“视图 → 全部适应（Fit all）”。

**机械零件示例：直齿圆柱齿轮**

```text
chem_tool(projectId=..., tool="cad_part", arguments={
  "equipment_type": "gear", "tag": "GEAR-001",
  "module_mm": 2, "teeth": 20, "pressure_angle_deg": 20,
  "face_width_mm": 20, "bore_mm": 20,
  "hub_diameter_mm": 40, "hub_width_mm": 30,
  "keyway_width_mm": 6, "keyway_depth_mm": 3.5,
  "accuracy_grade": "8", "material": "45钢"
})
```

输出：`齿轮图.svg/.pdf`（A3 端面齿形 + 侧视轮毂 + 参数表）、`齿轮图.dxf`（真实渐开线齿廓 + 分度/齿根/基圆 + 键槽）、`齿轮模型.FCStd/.step`、`齿轮设计数据.json`。  
限制：无变位/螺旋角/齿根修形/公差；GB/T 1356、GB/T 10095 原文未取得，图中标“待核对”，不替代制造图。

### 7.3 `export_xlsx` / `export_freecad`

- `export_xlsx`：把项目概览/要求/成果计划/依据/计算/文件导出为 6 表 xlsx；
- `export_freecad`：参数化三维布置（默认 7 台设备），输出 FCStd/STEP + 等轴测 SVG 预览；需 FreeCAD。

### 7.4 `dwsim` —— 外部 DWSIM 流程模拟

```text
chem_tool(projectId=..., tool="dwsim",
          arguments={"action": "status"})

chem_tool(projectId=..., tool="dwsim",
          arguments={"action": "run",
                     "flowsheet_path": "C:\\...\\DWSIM\\samples\\Cavett's Problem.dwxmz"})
```

- 仅支持本机已安装 DWSIM 9.0.5；默认目录 `%LOCALAPPDATA%\DWSIM`，可用 `DWSIM_HOME` 覆盖；
- 加载 `.dwxmz` / `.dwxml` 并求解，输出 `DWSIM结果.json` 与 `DWSIM物流表.csv`；
- 单位：温度 K、压力 Pa、质量流量 kg/s、摩尔分数；`solved=false` 时保留错误信息，不伪造结果；
- 不创建/编辑 DWSIM 流程图，不做动态模式/自定义脚本；DWSIM 为外部 GPL 软件，不随插件分发。

详见 [DWSIM.md](DWSIM.md)。

---

## 8. 典型工作流

### 8.1 赛题/可研闭环

```text
chem_project → chem_intake → chem_requirements → chem_plan → chem_object
→ chem_calc（物料/热量/精馏/换热…）→ chem_generate（报告）
→ chem_review → chem_bundle
```

### 8.2 设备询价包

```text
P&ID 模型 → pid_data（管线表/仪表/IO）
        → equipment_datasheet（设备数据表）
        → export_xlsx（汇总）
        → chem_bundle
```

### 8.3 安全分析包

```text
HAZOP/LOPA 工作表（hazop_lopa）
→ 安全阀选型（relief_sizing）
→ 标准符合性矩阵（compliance_matrix）
→ chem_review / chem_bundle
```

### 8.4 标准对标

```text
compliance_matrix（project_data + answers）
→ 查看“待确认/待核对”清单 → 补 QRA/在线量/源强/原文
→ 重新生成矩阵
```

---

## 9. 数据、备份与迁移

| 路径 | 内容 |
|---|---|
| `data/projects/<id>/project.json` | 项目数据（要求/计划/对象/计算/文件） |
| `data/kernel/chemellm.sqlite3` | 内核数据库 |
| `data/kernel/artifacts/<uid>/` | 生成的文件 |
| `data/bundles/*.zip` | 成果包（含 `manifest.json`、`recompute.md`、文件哈希） |
| `.chem/` | 只读工程快照 |

- 迁移整个项目：复制 `data/projects/<id>` 与对应 artifacts，或用 `chem_bundle` 打包；
- 独立部署包的数据目录由 `dataDir` 决定，默认 `<DSH_PROFILE_DIR>/chemellm-data`；
- 手工修改项目 JSON 前先停内核，改完再启动，避免缓存与写入竞争。

---

## 10. 故障排查

| 现象 | 处理 |
|---|---|
| 面板“本地内核未运行” | 先访问 `/v1/health`；开发模式运行 `scripts\start-kernel.cmd`；部署包确认 `autostart` 并重启 DSH |
| 工具数量不是 60 | 内核仍是旧代码：停止后重启 `kernel\server.py`；部署包确认解压/安装的是新 zip |
| 调用返回 `422` | 看 `detail`：多为缺字段/超范围/重复位号/管线号重复；按提示修正 schema |
| 调用返回 `409` | 阶段门禁 `enforce`：按 资料→要求→计划→依据→执行 顺序补齐 |
| 端口被占用 | 改 `endpoint` 端口（插件配置），部署包会自动用新端口启动 |
| FreeCAD 相关报错 | 目标机未装 FreeCADCmd；装好后重试，其余工具不受影响 |
| DOCX/PPTX 预览失败 | LibreOffice 未装或转换失败；直接下载文件，PDF 报告仍可生成 |
| PDF 中文/符号异常 | 内核注册 Windows 中文字体；若字体缺失，安装常用中文字体后重试 |
| token 401 | 内核 `CHEMELLM_KERNEL_TOKEN` 与插件 `config.token` 必须一致 |
| 打包失败 | 先 `chem_review` 看 blockers；验收页有 blocker 时不能打包 |

---

## 11. 能力边界与合规声明

- 单用户、单机、loopback；默认无鉴权（`token` 为空时本机进程可访问），介意请设置令牌；
- 自动校核 ≠ 专业审核；`chem_review ready=true` 不代表设计文件通过签审；
- API 520/521/526、HG/T 20519 等未取得原文的条款/公式标注“待核对”，不得据此宣称合规；
- FreeCAD/LibreOffice 不随包；缺失时降级并提示；
- 运行时仅 Windows x64；
- 工具输出为方案筛选/草稿，正式交付需专业复核与签署。

---

## 12. 参考文档

- [README.md](../README.md)：项目总览与验证记录
- [docs/QUICKSTART.md](QUICKSTART.md)：最短上手路径
- [docs/TOOLS.md](TOOLS.md)：工具清单与限制
- [docs/DRAWING.md](DRAWING.md)：P&ID/设备图规则
- [docs/HAZOP.md](HAZOP.md)：HAZOP/LOPA 方法与限制
- [docs/COMPLIANCE.md](COMPLIANCE.md)：标准台账与判定规则
- [docs/ACCEPTANCE.md](ACCEPTANCE.md)：验收记录
- [dsh-chemellm/README.md](../dsh-chemellm/README.md)：插件部署与能力矩阵
- [scripts/package-plugin.ps1](../scripts/package-plugin.ps1)：独立部署包构建脚本
