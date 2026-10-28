# Linux 实机部署验收

2026-10-20，在用户授权的阿里云 ECS 上通过 SSH 实际构建、运行和复算。此记录覆盖基础部署、显式研究任务恢复，以及另行实测的真实模型对话批次恢复能力。

## 环境与运行状态

- 主机实际为 **Alibaba Cloud Linux 3.2104 U12**，x86_64，2核、1870MiB内存、1GiB swap；不是先前口述的Ubuntu。
- Docker 26.1.3，Compose 2.27.0；镜像内Debian bookworm、Python 3.12.15。
- 基础镜像来自官方 `public.ecr.aws/docker/library/python:3.12-slim-bookworm`，仓库摘要为 `sha256:34386ef0cb081344d7ec1c103ba398e6e9f64e9ab3a1509accc92a4e24a07258`。
- 原实测源码包SHA256：`0c9645a519f8c9624c61bd7968f584d6f5454e2bcaffa668063c6eb645d10918`。当前研究任务及失败修复增量已改变可执行代码；另以41个app/web文件哈希核对并在隔离容器测试，不能宣称原包即当前完整版本。发布包以附带校验文件及release-verification.json为准。
- 测试目录：`/opt/chemellm-linux-qa/20261020/chemellm`；Compose项目：`chemellm-linux-qa`；镜像：`chemellm-linux-qa:20261020`（构建ID `a67928fecc90`）。
- 只监听 `127.0.0.1:8000`，使用独立命名数据卷。工作台随机口令只保存在服务器 `.env`，报告不包含口令、私钥或模型密钥。
- 容器使用UID/GID 10001、只读根文件系统和原Compose安全设置；内存上限1400MiB，BLAS/OMP线程数为1。
- 重启后HTTP健康接口200、Docker健康状态为 `healthy`。重启后抽样内存约191MiB；复算期间记录的内存高水位1110994944字节（约1.03GiB，包含缓存），不是完整压力测试峰值。

## 实际通过的检查

| 检查 | 结果 | 本地证据（相对项目根目录） |
|---|---|---|
| 镜像构建和启动 | 通过；修复下面列出的实机问题后成功 | `data/qa/linux-server/test-logs/services.txt`、部署目录中的构建日志 |
| Python依赖一致性 | `pip check` 无冲突 | 依赖版本清单：`data/qa/linux-server/test-logs/dependencies.txt` |
| 健康、静态页、配置 | 通过 | `data/qa/linux-server/server-qa/deployment-results.json` |
| 赛题导入 | 35项要求、31项必需；原件哈希及PDF预览通过 | 同上 |
| 9类确定性计算 | 物料衡算、PR闪蒸、二元MESH、含氢分相、反应冷凝前端、湿塔、湿分离列、混合物反应、四元循环均通过数值校验 | 同上 |
| Office及PDF交付 | PDF/DOCX/PPTX生成下载通过，两个Office格式实际转换为PDF | 同上；使用 `--require-office`；不包含复杂排版的视觉QA |
| OCR真实推理 | `FLOW 100 kmol/h` 控制图实际识别且原始文本精确一致 | `data/qa/linux-server/server-qa/linux-server/ocr-runtime.json`；单个控制例不证明通用OCR准确性 |
| NIST回归基准 | Misra1a、BoxBOD、DanWood共3项通过 | `data/qa/linux-server/server-qa/regression-benchmark.json` |
| Cantera资格对照 | 3项热力学、4项解析解全部通过 | `data/qa/linux-server/server-qa/cantera-benchmark.json` |
| 鉴权及跨站写入 | 无口令/错误口令401、登录Cookie鉴权成功、跨站写入403 | `data/qa/linux-server/server-qa/linux-server/followup-results.json` |
| Cantera原生包 | 1个WGS平衡工况、1个反应器工况，经HTTP生成后解压执行 `simulation.py` 通过 | 同上及 `cantera_equilibrium/`、`cantera_reactor/` 中的复算结果 |
| 两个项目成果包 | 使用包内源码、隔离数据目录和独立进程复算；部署包9条、Cantera包2条数值记录全部一致 | 同上；非数值报告生成明确跳过；使用同一已安装依赖环境 |
| 服务重启持久化 | 两个项目可访问，两个成果包下载后的SHA256均与重启前一致 | `data/qa/linux-server/server-qa/linux-server/restart-results.json` |
| DeepSeek真实工具调用 | `deepseek-flash` 实际调用 `convert_units`，1 bar = 100 kPa，任务完成 | `data/qa/linux-server/server-qa/live-model-qa/results.json`、`tool-call-run.json` |
| 真实模型错误修复 | 故意输入 `kPaa` 后更正为 `kPa`，修复引用实际失败ID，无未解决失败，任务完成 | 同目录 `error-repair-run.json` |
| 追问后继续 | 缺热负荷时实际 `ask_user` 暂停；补充1000 kW后调用 `heat_exchanger`，面积22.222222 m²，任务完成 | 同目录 `question-retry-paused-run.json`、`question-retry-run.json`；F=1.0 |
| SSH隧道访问及真实浏览器登录 | 健康200、匿名API401、Cookie登录和配置读取通过；Edge实际登录并加载工作台，JS异常0条 | `data/qa/linux-server/server-qa/tunnel-access-results.json`、`ssh-workbench.png`；尚未验证公网HTTPS |

## 真实模型与域名

服务端已配置 `https://api.deepseek.com`，`/models` 实际返回200，可用ID包含 `deepseek-flash` 和 `deepseek-v4-pro`；本轮只调用前者。快/均衡/深度三个选项暂时都映射到 `deepseek-flash`，未发送 `reasoning_effort`，不能把界面选项视为不同模型或速度承诺。密钥经SSH写入服务器0600权限的 `.env`，不在报告或源码包中；工作区测试凭据文件已排除出Git及Docker构建上下文。

首次追问案例未通过：模型曾将 `task_key` 放在工具schema之外，产生参数及修复关联错误；补充热负荷后虽算得24.691358 m²，又因“纯逆流、F=0.9”输入冲突继续追问。原始结果保留于 `initial-results.json` 和 `question-resume-run.json`。改用一致的F=1.0输入并明确schema后复测通过。三个小案例验证真实服务接入与基础工具链，不证明复杂任务稳定性或模型工程能力。

`chemellm.online` 的A记录已指向本机，但公网实测返回阿里云 `403 / Non-compliance ICP Filing`。Let's Encrypt HTTP-01也因403拒绝签发。**HTTPS证书尚未签发，域名服务未正式开通，证书续期未启用**；证据在 `data/qa/linux-server/server-qa/domain-results.json`。服务器准备了备案后的证书申请及代理启用脚本，缺少证书时拒绝修改配置的路径已验证。后续操作见[部署说明](DEPLOYMENT.md)。

## 实机发现及修复

1. Windows写出的SHA256文件带CRLF，Linux将CR当作文件名的一部分。`scripts/package.py`改为按字节写入LF。
2. 服务器无法直接访问Docker Hub；使用官方ECR公共仓库预加载基础镜像。
3. 默认Debian/PyPI下载缓慢。Dockerfile增加可选构建源参数；本次使用阿里云镜像，构建时将 `mirrors.aliyun.com` 映射到经实测的阿里云内网镜像地址 `100.100.2.148`，保持HTTPS证书验证。该地址仅用于本服务器测试配置，不应假定适用于所有地域。
4. 主机旧版 `unzip` 错误转换中文赛题文件名。改用 `LC_ALL=C.utf8 python3 -m zipfile -e`，并逐文件核对归档清单哈希。
5. 解压源码权限过严，导致容器普通账号无法导入应用。Dockerfile在切换到UID 10001之前明确赋予 `/app` 内容读取及目录遍历权限；程序仍由普通账号运行。

## 未覆盖

公网域名未通过备案，HTTPS反向代理、Secure Cookie、外部443连通性及证书自动续期尚未验收，也没有重启整台ECS。Linux没有重复运行完整Python单元测试。本轮单实例和少量顺序工况通过，不代表多用户容量、长期稳定性、通用OCR准确性或工程设计验收。项目包复算使用同一依赖环境，属于可复现性检查。

## 研究任务真实中断增量

原依赖镜像派生`chemellm-workflow-qa:20261020`（ID `5194922be0bd`），只更新逐项核对的41个app/web文件，另加仅QA使用的暂停包装。独立目录和数据`/opt/chemellm-workflow-qa/20261020`，回环端口18002、850MiB内存限额。原服务和数据卷保持独立。

两次实际SIGKILL/启动分别覆盖报告工具执行前，以及报告和计算真正保存后、工作流确认前。重启后未知调用均阻止直接恢复/新执行；分别明确确认重试和采用已有计算后继续。两次上游检查点都复用，累计工具次数分别4和3；采用路径保持原产物ID及下载字节。没有通过编辑数据库状态模拟重启，也未用LLM完成此控制例。证据为`data/qa/linux-server/workflow-recovery/results.json`及两份完整事件报告；操作和边界见[研究任务说明](STUDY_WORKFLOW.md)。测试结束停止独立容器、保留数据；原服务最后确认healthy、OOMKilled=false。

以上41文件版本只验证显式研究任务，其处置浏览器对话框尚未端到端验证。对话执行器另有下述43文件版本实测，不能混用版本证据。备份迁移、压力和长期运行仍待补齐。

## 对话执行器与真实模型恢复增量

沿用已验收重依赖镜像，派生`chemellm-agent-qa:20261020`，最终镜像ID为`276eb1a324b604b4ed664dbf248bbca63e9605eed800ae9227efbfdf5cb98893`。43个当前app/web文件逐项哈希核对，清单为`data/qa/linux-server/agent-recovery/source-hashes.json`。目录`/opt/chemellm-agent-qa/20261020`、独立数据、850MiB、只读根、UID10001及回环18003。仅测试入口使用QA暂停包装；空鉴权仅用于回环/SSH隔离验收，原服务鉴权未改。该增量不等于新环境全量构建或Linux完整pytest。

真实`deepseek-flash`分别生成一批三项调用：换算、导出报告、换算。报告执行前或真实保存后各一次SIGKILL/重启，首项已确认，第三项未开始。两条均拦截未知结果的直接恢复和新建。保存后采用原计算/MD/PDF，累计3次；执行前明确重试，累计4次（含中断尝试）。首项检查点复用，第三项按原批次继续；采用路径原ID/字节不变，各只有一份报告，各2次真实API请求。采用、继续及持久处置历史经Edge普通界面操作，390移动/1440桌面截图检查通过；重试为HTTP路径。证据及边界见[对话恢复](AGENT_RECOVERY.md)。

首次执行链路正确，但模型摘要误写“无重试”，轨迹已保留在`initial-runs/`。修复为将服务记录的处置与累计次数送入模型上下文，页面独立保留历史后，两条最终摘要准确。曾发生5项422→409回归，修正正常输入错误与不确定副作用的分类后，Windows全量203项通过。另发现Compose带引号的.env不能直接传Docker --env-file，QA脚本改为服务端解析成0600运行文件，未输出或回传凭据。

测试结束只停止独立QA容器并保留全部数据、准备容器及失败轨迹；原`chemellm-linux-qa-chemellm-1`保持运行并复核healthy、OOMKilled=false。最新源码包另上传至隔离目录核对SHA256，不替换原运行服务。公开恢复控制例不构成复杂/跨天任务、视觉、科学准确性或工程审核资格。

服务器可通过项目内SSH配置连接：

    ssh -F data/qa/linux-server/ssh_config chemellm-server

配置和密钥副本只存在本机，不包含在部署包内。工作台口令另存于本机仅当前Windows用户可读的 `data/qa/linux-server/workbench-access.txt`；不包含模型密钥。服务管理命令须在上述测试目录内带上 `-p chemellm-linux-qa`，例如：

    docker compose -p chemellm-linux-qa ps
    docker compose -p chemellm-linux-qa logs --tail=100 chemellm
