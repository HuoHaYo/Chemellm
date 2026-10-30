# 本地版快速上手

> 完整说明见根目录 [README.md](../README.md)；**逐步教程见 [USER_GUIDE.md](USER_GUIDE.md)**。本文只列最短路径。

## 1. 启动内核（二选一）

**A. 开发模式（本仓库）**

```powershell
.\scripts\start-kernel.cmd
```

看到 `ChemELLM local kernel 0.1.0 -> http://127.0.0.1:8765` 后保持窗口运行。

**B. 独立部署包（换机器推荐）**

```powershell
powershell -ExecutionPolicy Bypass -File scripts\package-plugin.ps1
```

生成 `dist\dsh-chemellm-<日期>-win-x64.zip`（内含便携 Python + 依赖 + 内核 + 归档应用）。目标机解压后用 DSH `plugin_manager` 安装该目录；插件会在内核未运行时**自动拉起**（`autostart: true`），数据默认写到 `<DSH_PROFILE_DIR>/chemellm-data`。

## 2. 打开 DSH 面板

刷新 DSH 页面 → 左侧栏出现「化工工程」图标 → 点开可见项目面板（概览/要求/计划/依据/计算/成果/验收）。

面板底部设置页可查看内核版本与数据目录。

## 3. 在对话里干活

任一会话中直接说：

> 先用 chem_project 列出项目；然后用 chem_intake 登记你的赛题（或任务书）PDF（本仓库不提供赛题原文）；用 chem_requirements 登记要求；用 chem_plan 建成果计划；用 chem_object 写设计依据；用 chem_calc 算物料衡算；用 chem_generate 生成报告；用 chem_review 自检；最后用 chem_bundle 打包。

P&ID 与设备图：

> 用 chem_tool tool=pid 传结构化图模型生成 A1 P&ID；用 chem_tool tool=pid_check 做规则校验；用 chem_tool tool=pid_data 生成管线表/MTO/仪表索引/IO清单/联锁因果表；用 chem_tool tool=equipment_datasheet 生成设备数据表（DOCX/PDF/JSON）；用 chem_tool tool=relief_sizing 做安全阀/爆破片选型计算；用 chem_tool tool=hazop_lopa 生成 HAZOP/LOPA 工作表；用 chem_tool tool=compliance_matrix 生成标准条款符合性矩阵；用 chem_tool tool=cad_part 生成 A3 设备图 + FCStd/STEP。

旧项目里没有包成域工具的能力（设备登记/查询、图纸识读、数据集检查/分析等）用 `chem_tool` 透传：`chem_tool projectId=… tool=equipment_query arguments={…}`；不带 `tool` 时列出全部可执行工具名。

## 4. 内核自检（可选）

```powershell
.\.venv\Scripts\python.exe -X utf8 scripts\smoke.py
.\.venv\Scripts\python.exe -X utf8 scripts\verify_bundle.py   # 校验最新成果包的 manifest 哈希
dsh-chemellm\runtime\python\python.exe -c "import fastapi, scipy, thermo, reportlab, ezdxf, openpyxl; print('runtime ok')"
```

## 5. 常用维护

| 操作 | 方式 |
|---|---|
| 查看状态 | 面板或 `http://127.0.0.1:8765/v1/health` |
| 停止内核 | 开发模式：内核窗口 Ctrl+C；部署包：退出 DSH 时插件会停止子进程 |
| 修改内核地址 | `dsh-chemellm/cordis.patch.yml` → `config.endpoint`（端口同时用于自动启动） |
| 关闭自动启动 | `config.autostart: false`，改为手动启动内核 |
| 开启强制门禁 | `config.phaseGate: enforce`；自动启动会同步到内核，自行启动需设置 `CHEMELLM_PHASE_GATE=enforce` |
| 加访问令牌 | 内核侧 `CHEMELLM_KERNEL_TOKEN=...`，插件 `config.token` 同步 |
| 指定数据目录 | `config.dataDir`（默认 `<DSH_PROFILE_DIR>/chemellm-data`） |

## 6. 当前数据

- 现有三个项目：案例 A（赛题）、案例 A 复跑、案例 B（迁移）；均通过 `chem_review` 并已打包。
- 开发数据目录：`data/`；只读快照：`.chem/`；部署包数据目录由 `dataDir` 决定。

## 7. 部署能力边界

| 能力 | 独立部署包 | 说明 |
|---|---|---|
| 项目/要求/依据/计算/证据/校核/打包 | ✅ | 内置 Python 运行 |
| A1 P&ID、A3 设备图、xlsx、DOCX/PDF 报告 | ✅ | 内置依赖 |
| FCStd/STEP | ⚠️ 需 FreeCAD | 缺失时工具报错，其他能力正常 |
| DOCX/PPTX 预览 | ⚠️ 需 LibreOffice | 缺失时预览回退文本/下载 |
| DWSIM/IDAES 扩展 | ⚠️ 可选 | 未随包 |
| macOS/Linux | ❌ | 运行时目前为 Windows x64 |
