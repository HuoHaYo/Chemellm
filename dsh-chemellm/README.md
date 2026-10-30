# @local/dsh-chemellm —— 可独立部署的本地化工工作台

本插件把化工工程工作台打包为 **DSH Host 插件 + 内置 Python 内核**，部署到另一台 DSH 时无需预装 Python 环境。

## 包内结构

```
dsh-chemellm/
  index.js / client.js / icon.svg / cordis.patch.yml / package.json
  lib/
    kernel.js         配置、令牌、HTTP 请求、内核启动与关闭
    tools.js          12 个域工具与阶段校验
    proxy.js          API、预览、下载的同源流式代理
  runtime/
    python/           便携 CPython 3.12（Windows x64，embeddable）
    site-packages/    内核所需第三方依赖（fastapi/uvicorn/scipy/thermo/CoolProp/
                      cantera/reportlab/ezdxf/openpyxl/python-docx/pptx/pypdf/
                      pdfplumber/pypdfium2/pillow/pint/httpx/...）
    kernel/           打包时从仓库 kernel/ 复制的当前源码
    app/              打包时从 old/app/ 复制的计算、证据与文档库
    requirements.txt  依赖清单（供审计/重建）
```

## 安装（目标机）

1. 关闭 DSH（或准备重启 Host）。
2. 将整个 `dsh-chemellm/` 目录复制到目标机的 DSH profile 可访问位置。
3. 用 DSH 的插件管理安装该目录（等价于 `plugin_manager install_bundle <目录>`），或在 profile 中链接该包。
4. 启动 DSH。Host 插件会：
   - 先探测 `endpoint`（默认 `http://127.0.0.1:8765/v1/health`）；
   - 若不可达且 `autostart: true`，用包内 `runtime/python/python.exe` 启动 `runtime/kernel/server.py`；
   - 数据目录默认 `<DSH_PROFILE_DIR>/chemellm-data`（可用 `dataDir` 覆盖）。
5. 左侧「化工工程」出现即表示 Client 已加载；面板经 DSH Host 的 `/chemellm/api/*` 访问内核，预览与下载也经 Host 转发，浏览器无需持有内核令牌。

### 配置项（cordis.patch.yml）

| 键 | 默认 | 说明 |
|---|---|---|
| `endpoint` | `http://127.0.0.1:8765` | 内核地址；端口同时用于启动内置内核 |
| `token` | `''` | Host 请求使用的内核令牌；自动启动时同步到内核 |
| `phaseGate` | `advisory` | `enforce` 时越阶段调用被拦截 |
| `autostart` | `true` | 内核未运行时是否自动拉起 |
| `python` | `''` | 覆盖 Python 路径；开发模式优先仓库 `.venv`，分发模式使用包内运行时 |
| `dataDir` | `''` | 覆盖数据目录（默认 profile 下 `chemellm-data`） |

自动启动仅用于 `http://127.0.0.1:<端口>` 或 `http://localhost:<端口>`；其他 HTTP(S) 地址只连接现有服务。自行启动的内核需手动配置相同令牌和 `CHEMELLM_PHASE_GATE`。自动启动会同步令牌、阶段门禁、数据路径，并将快照写入 `dataDir/.chem`。停用插件会关闭它自行启动的内核。

## 开发与打包

```powershell
node --test dsh-chemellm/test/*.test.js
python -X utf8 scripts/test_kernel.py
.\scripts\package-plugin.ps1 -ValidateOnly
.\scripts\package-plugin.ps1
node scripts/test_packaged_plugin.mjs
```

打包脚本按 `package.json.files` 收集插件文件，从便携 runtime 中只取 `python/`、`site-packages/` 和 `requirements.txt`，内核源码来自当前仓库。项目数据、快照、习题材料及缓存不进入分发包；SHA256 清单只在 `dist/dsh-chemellm/` 中生成。`-SkipArchive` 可只生成分发目录，`-RuntimeDirectory <路径>` 可指定便携依赖来源。

升级旧版本时，在 DSH 中移除 `@local/dsh-chemellm-legacy` 和 `@local/dsh-chemellm-enforce`，主插件已提供 `chem_tool`，强制门禁直接设置 `phaseGate: enforce`，随后重启 DSH Host。

## 能力矩阵（目标机无预装 Python 时）

| 能力 | 是否随插件可用 | 说明 |
|---|---|---|
| 项目/要求/计划/依据/计算/证据/校核/打包 | ✅ | 全部由内置 Python 内核提供 |
| P&ID（A1，规范化：HG/T 20519 参照 + ISA-5.1 符号） | ✅ | reportlab/ezdxf 已随包；条款级合规待核对 |
| P&ID 数据链（`pid_data`：管线表/MTO/仪表索引/IO/C&E） | ✅ | xlsx + 5 CSV + DOCX + JSON |
| 设备数据表/规格书（`equipment_datasheet`） | ✅ | DOCX/PDF/JSON，壁厚按 GB/T 150.1 简化式 |
| 安全阀/爆破片选型（`relief_sizing`） | ✅ | DOCX/PDF/JSON，API 520/521 公开式并标注待核对 |
| HAZOP/LOPA 工作表（`hazop_lopa`） | ✅ | xlsx/docx/json |
| 标准符合性矩阵（`compliance_matrix`） | ✅ | xlsx/docx/json，未取得原文标“待核对” |
| xlsx（openpyxl）、DOCX/PDF 报告（python-docx/reportlab） | ✅ | 不依赖 LibreOffice |
| 设备图（A3，SVG/PDF）与设计数据 | ✅ | 纯 Python 绘制 |
| 齿轮零件图（`cad_part` gear：A3/DXF/FCStd/STEP） | ⚠️ 需 FreeCAD | 渐开线齿廓；GB/T 1356/10095 原文未取得，标“待核对” |
| FCStd/STEP（`cad_part`、`export_freecad`） | ⚠️ 需 FreeCAD | 目标机需装 FreeCADCmd；缺失时工具返回明确错误，其余能力不受影响 |
| DOCX/PPTX 预览（转 PDF） | ⚠️ 需 LibreOffice | 缺失时预览回退为文本/下载，报告 PDF 仍可直接生成 |
| DWSIM 外部流程模拟（`dwsim`） | ✅（需 DWSIM） | 加载/求解 `.dwxmz`/`.dwxml`，输出 JSON/CSV；DWSIM 为外部 GPL-3.0，不随包 |
| IDAES/Pyomo 扩展 | ⚠️ 可选 | 未随包，按需安装 |

## 验证

```powershell
# 内核健康
Invoke-WebRequest http://127.0.0.1:8765/v1/health -UseBasicParsing
# 可执行工具数（应为 60）
(Invoke-WebRequest http://127.0.0.1:8765/v1/tools -UseBasicParsing).Content
# 便携运行时自检
.\runtime\python\python.exe -c "import fastapi, scipy, thermo, reportlab, ezdxf, openpyxl, docx; print('runtime ok')"
```

## 边界

- 运行时为 **Windows x64**；其他平台需换对应 Python 运行时（macOS/Linux 需自行构建）。
- 包内 Python 仅含内核所需依赖，不含 FreeCAD/LibreOffice/DWSIM 等外部软件；`dwsim` 调用目标机已安装的 DWSIM。
- 插件自动拉起的内核绑定 `127.0.0.1`，无云端、无公网依赖。
- 自动校核 ≠ 专业审核；交付物仍需工程复核。
