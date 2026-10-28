# 专业后端资格记录

更新日期：2026-10-21。此记录仅报告实际安装、运行和接入证据，不把安装或局部模型构造等同于可交付工程能力。

## IDAES 与 Pyomo

| 阶段 | 结果 | 证据 |
|---|---|---|
| 安装 | 通过，隔离安装 IDAES-PSE 2.9.0、Pyomo 6.10.1 及其 Python 依赖 | `output/backend-qualification/idaes-install-report.json`；发行包 SHA-256 见 `idaes-qualification.json` |
| 运行 | 部分通过：成功导入 IDAES 并构造稳态 `FlowsheetBlock`；未执行非线性求解 | `scripts/backend_idaes_qualification.py` 的隔离烟测 |
| 求解器 | 未通过：本机 IPOPT、HiGHS、CBC、GLPK 均不可用 | 烟测中 `available_solvers` 全为 false |
| 平台接入 | 未接入 | 没有修改 ChemELlm 运行时代码或暴露模型工具 |
| 工程交付验收 | 未测试 | 没有生成工程文件、原生流程模型或赛题成果 |

IDAES/Pyomo 使用 BSD 系列许可；安装元数据、项目主页、安装报告中的下载 URL/哈希均在 JSON 记录中。IDAES 官方扩展清单报告版本 3.4.2 可用于 Windows，但实际下载扩展时先在沙箱遭到 Windows 网络权限拒绝。按要求请求 escalation 后，automatic approval review 服务返回 HTTP 503，命令未执行；没有尝试绕过审批。云端只读 SSH 探测也在沙箱中被拒绝，escalation 同样因 review 服务 503 未执行。故没有把扩展安装或求解记为通过。

复现安装（需要获准访问 Python 包索引；若执行 IDAES 官方扩展下载，需网络审批）：

```powershell
python -m venv output/backend-qualification/idaes-env
output/backend-qualification/idaes-env/Scripts/python.exe -m pip install idaes-pse==2.9.0 --report output/backend-qualification/idaes-install-report.json
$env:IDAES_DATA = (Resolve-Path output/backend-qualification/idaes-data).Path
$env:PYOMO_CONFIG_DIR = (Resolve-Path output/backend-qualification/pyomo-config).Path
output/backend-qualification/idaes-env/Scripts/python.exe scripts/backend_idaes_qualification.py
```

唯一合适的下一步是在获准网络路径中取得并核对 IDAES 3.4.2 solver extensions，再运行 IDAES 自带的有来源物性包/单元模型例题和预先冻结的物流/热量对照；之后才值得实现隔离进程适配、用户可复算原件和包内复算。此资格记录没有完成这些步骤。

## DeepSeek 视觉探测

没有执行图像请求。当前本地进程没有 `MODEL_*` / `MODEL_API_KEY` 配置或 `.env`，预期的 `127.0.0.1:18004` 隧道也未监听。历史一次完整工程运行证明模型标识为 `deepseek-flash`，但没有证明该端点接受 `chat/completions` 的图像 `image_url` 数据 URI 或具有可靠视觉能力。读取或复制受保护凭据、在模型能力未确认前发送图像均不合适。故视觉能力当前仍为未资格化，也没有开启平台视觉路由。

## 可复现记录

```powershell
$env:IDAES_DATA = (Resolve-Path output/backend-qualification/idaes-data).Path
$env:PYOMO_CONFIG_DIR = (Resolve-Path output/backend-qualification/pyomo-config).Path
output/backend-qualification/idaes-env/Scripts/python.exe scripts/backend_idaes_qualification.py
```

机器可读状态：`output/backend-qualification/idaes-qualification.json`。烟测只构造模型对象，不运行求解器，不证明热力学、流程、收敛、优化、软件集成、可运行交付或工程正确性。
