# ChemELLM v0.1.0 · DSH 直装版（Windows x64）

DSH 直装包：把本地化工工程工作台打包为 **DSH Host 插件（`@local/dsh-chemellm` 0.1.0）+ 内置便携 Python 运行时**。
目标机只需已安装 DeepSeek Harness（DSH），**无需本仓库源码、无需预装 Python 环境**。

## 下载

| 文件 | 大小 | SHA256 |
|---|---|---|
| `dsh-chemellm-v0.1.0-win-x64.zip` | 166,874,710 B（159.1 MiB） | `ccd09b9f5b6d7cf2e6ab4bfe4284466e69569d04aa7e97f92a34b4d85a2bc5e2` |
| `SHA256SUMS-v0.1.0.txt` | 发布物哈希清单 | — |

- 构建：2026-10-30，由仓库内 `scripts/package-plugin.ps1` 生成（对应本 tag 的提交）。
- 解压后：9,386 个文件 / 473.4 MiB（含 `SHA256SUMS.txt` 全量清单）。

## 安装（直装三步）

1. 下载 zip，解压到本机任意本地目录，得到 `dsh-chemellm\` 目录。
2. 在 DSH 插件管理中安装该目录的**绝对路径**（等价于 `plugin_manager install_bundle <目录>`），或在 profile 中链接该包。
3. 重启 DSH Host。左侧栏出现「化工工程」即安装完成。

插件行为：先探测 `endpoint`（默认 `http://127.0.0.1:8765`）；内核未运行时用包内 `runtime\python\python.exe` **自动拉起**内核（`autostart: true`）；数据默认写到 `<DSH_PROFILE_DIR>/chemellm-data`，可用 `dataDir` 覆盖。面板预览与下载经 Host 的 `/chemellm/*` 同源代理转发，浏览器不持有内核令牌。

已安装旧版本的，先移除 `@local/dsh-chemellm-legacy`、`@local/dsh-chemellm-enforce`（本版已并入主插件：通用工具走 `chem_tool`，强制门禁用 `phaseGate: enforce`），再安装本包并重启 Host。

## 安装后自检

```powershell
cd <解压目录>\dsh-chemellm
# 1) 便携运行时
.\runtime\python\python.exe -c "import fastapi, scipy, thermo, reportlab, ezdxf, openpyxl, docx; print('runtime ok')"
# 2) 内核健康（插件已自动拉起时）
(Invoke-WebRequest http://127.0.0.1:8765/v1/health -UseBasicParsing).Content
# 3) 可执行工具数（应为 60）
(((Invoke-WebRequest http://127.0.0.1:8765/v1/tools -UseBasicParsing).Content | ConvertFrom-Json).executable).Count
```

包内 `SHA256SUMS.txt` 覆盖全部 9,386 个文件，可离线校验：

```powershell
$bad = 0
Get-Content .\SHA256SUMS.txt | ForEach-Object {
  if (-not $_.Trim()) { return }
  $h, $f = $_ -split '  ', 2
  if ((Get-FileHash -Algorithm SHA256 -LiteralPath $f).Hash.ToLowerInvariant() -ne $h) { $bad++; $f }
}
"mismatch: $bad"
```

## 包内结构

```text
dsh-chemellm/
  index.js / client.js / icon.svg / cordis.patch.yml / package.json / README.md
  lib/
    kernel.js        配置、令牌、HTTP 请求、内核启动与关闭
    tools.js         12 个 chem_* 域工具与阶段校验
    proxy.js         API、预览、下载的同源流式代理
  SHA256SUMS.txt     全部 9,386 个文件的 SHA256 清单
  runtime/
    python/          便携 CPython 3.12.7（Windows x64 embeddable）
    site-packages/   fastapi / uvicorn / scipy / thermo / CoolProp / cantera / reportlab /
                     ezdxf / openpyxl / python-docx / python-pptx / pypdf / pdfplumber /
                     pypdfium2 / pillow / pint / httpx 等内核依赖
    kernel/          打包时从仓库 kernel/ 复制的当前内核源码
    app/             打包时从仓库 old/app/ 复制的计算、证据与文档库
    requirements.txt 依赖清单（供审计与重建）
```

包内 Python、第三方库、内核源码与归档应用齐备；**不含**本机项目数据（`data/`）、只读快照（`.chem/`）、习题/赛题材料与本机标准原文。打包脚本按 `package.json.files` 收集插件文件，运行时只取 `python/`、`site-packages/`、`requirements.txt`，内核源码来自当前仓库，不做整棵 runtime 复制。

## 能力（装好即可用）

| 环节 | 能做什么 |
|---|---|
| 项目与资料 | 新建项目；登记 PDF/DOCX/XLSX/CSV/SVG/DXF，生成哈希与页数 |
| 要求 / 计划 | 要求逐条编码登记（含原文引句、适用性）；要求 → 成果映射与格式清单 |
| 依据 | 依据 / 物流 / 设备 / 公用工程 / 安全 / 成本对象，数值带单位、条件与来源 |
| 计算 | 22 类确定性模型：物性、蒸汽、单位换算、物料衡算、换热器、PR 闪蒸、反应热、混合物反应、精馏捷算、MESH 精馏、管压降、夹点分析、分相、含氢冷凝、前端流程联立、湿塔、湿法分离序列、循环流程、经济估算、数据回归、Cantera 平衡、Cantera 反应器 |
| 证据 | 文献检索、全文导入、引句登记、论断与证据检查、证据包导出（12 个证据工具） |
| 成果 | DOCX / PDF / PPTX / MD 报告；PFD、P&ID（A1）、设备图（A3，SVG/PDF/DXF）；xlsx 数据表；设备数据表、安全阀选型、HAZOP/LOPA、标准符合性矩阵 |
| 校核与打包 | 要求覆盖 / 依据完整性 / 成果文件 / 计算校验自检；打包 zip + SHA256 manifest + `recompute.md` |

阶段门禁：`资料 → 要求 → 计划 → 依据 → 执行 → 校核 → 打包`；`phaseGate: enforce` 时内核与插件双侧拒绝越阶段调用，任何数据变更都会重置 `review`。

## 配置（`cordis.patch.yml`）

| 键 | 默认 | 说明 |
|---|---|---|
| `endpoint` | `http://127.0.0.1:8765` | 内核地址；端口同时用于启动内置内核 |
| `token` | `''` | Host 请求使用的内核令牌；自动启动时同步到内核 |
| `phaseGate` | `advisory` | `enforce` 时越阶段调用被拦截 |
| `autostart` | `true` | 内核未运行时是否自动拉起 |
| `python` | `''` | 覆盖 Python 路径；分发模式默认用包内运行时 |
| `dataDir` | `''` | 覆盖数据目录（默认 profile 下 `chemellm-data`） |

自动启动只针对 `http://127.0.0.1:<端口>` / `http://localhost:<端口>`；其他 HTTP(S) 地址只连接已有服务。自行启动的内核需手动配置相同令牌与 `CHEMELLM_PHASE_GATE`。

## 本版内容

- **首个直装包**：插件 + 便携 Python 运行时一体分发，目标机免装 Python。
- 插件由单文件拆分为 `lib/{kernel,tools,proxy}.js`，`index.js` 只负责注册工具、提示词、路由与清理回调。
- 移除 `dsh-chemellm-legacy`、`dsh-chemellm-enforce` 两个伴生包，能力并入主插件。
- 移除 5 组仅开发探测用的 DWSIM Probe 源码与二进制，以及源码目录 `SHA256SUMS.txt`；正式 DWSIM Runner 与构建脚本保留。
- 新增回归测试：Host 集成与进程生命周期（`dsh-chemellm/test/`）、内核回归（`scripts/test_kernel.py`）、分发包端到端回归（`scripts/test_packaged_plugin.mjs`）。
- `scripts/package-plugin.ps1` 收紧收集范围：只取 `package.json.files` 与必需运行时目录，缓存与 `*.pyc` 排除，清单在分发目录重新生成。

## 发布前验证（2026-10-30，本机 Windows x64）

| 检查 | 命令 | 结果 |
|---|---|---|
| 插件回归 | `node --test dsh-chemellm/test/*.test.js` | 6 项全部通过 |
| 内核回归 | `python -X utf8 scripts/test_kernel.py` | 2 项通过（令牌、阶段拒绝、计算、报告、打包哈希、审核失效） |
| 分发包端到端 | `node scripts/test_packaged_plugin.mjs` | `PACKAGED PLUGIN OK`：便携内核自启、令牌、enforce 门禁、12 工具、报告、校核、打包、代理下载 |
| 便携运行时导入 | `runtime\python\python.exe -c "import ..."` | `runtime imports ok`（Python 3.12.7） |
| 内核自检 | 由包内运行时启动 | `/v1/health` → `version 0.1.0`；`/v1/tools.executable` → **60**；计算模型 22、证据工具 12 |
| 清单完整性 | 分发目录逐文件校验 | 9,386 条，0 处不一致 |
| 发布 zip 校验 | 解压后按包内清单复核 | 9,386 条，0 处不一致 |

自动校核与专业审核保持分离：`chem_review` 只检查数据与文件层面的一致性，审核状态恒为 `not_reviewed`，不能作为签审结论。

## 边界与限制（v0.1.0）

- **平台**：运行时为 Windows x64；macOS / Linux 需自行构建对应 Python 运行时。
- **外部软件不随包**：FreeCAD（FCStd/STEP）、LibreOffice（Office 预览）、DWSIM（稳态模拟）需目标机自行安装；缺失时对应工具返回明确错误，其余能力不受影响。
- **单机单用户**：内核只监听 loopback；`token` 为空时本机任意进程均可访问，介意请设置 `CHEMELLM_KERNEL_TOKEN`。
- **自动校核 ≠ 专业审核**：交付物仍需工程复核。
- **图纸为示意图**：P&ID / 设备图不按比例，不作施工图，无管道等级库、off-page 接续与仪表量程等完整工程属性。
- **模型假设有限**：部分模型只覆盖特定体系，精馏按理想 Raoult 处理，缺动力学、塔水力学与详细设备设计；假设写在各自返回的 `warnings` 里。
- **标准原文不入库**：GB/T、HG/T 等第三方版权标准需本地自备。

## 许可证

本项目为学生非营利项目，**尚未选定开源许可证**；如需复用代码，请先联系作者。第三方库与外部软件按各自许可证使用，商业软件不随本包分发。
