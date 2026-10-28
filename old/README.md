# ChemELLM 化工智能工作台

面向化工人的通用工程平台，目标是让接入的DeepSeek利用专业软件、数据库和工具胜任化工工程师的大部分工作。**当前第一验收目标：用户一轮对话提交任务和资料，平台自主生成2026化工设计赛题要求的全套正确、可编辑、可运行文件。** 赛题用于端到端验收；平台能力须可迁移至其他工程任务。当前仍是可运行原型，尚未通过这一关。见[平台目标](docs/RESEARCH_PLATFORM_GOAL.md)、[工程交付验收](docs/ENGINEERING_ACCEPTANCE.md)和[项目状态](docs/STATUS.md)。

包含中文 Web 界面、兼容 API/Ollama 的模型工具循环、确定性工程计算、CSV/Excel 数据分析、题录及全文证据检索、显式调用且待资格验证的AI图像转录、SVG/DXF识读与拓扑编辑、Office/PDF预览和导出、设备参数版本库、赛题逐项验收及成果打包。模型API密钥保留在服务端。版本化参数、任务依赖、修改失效和中断处置见[研究任务操作](docs/STUDY_WORKFLOW.md)；真实模型对话的持久调用、未知结果核对与继续见[对话恢复](docs/AGENT_RECOVERY.md)。

## 本地运行

Python 3.11+，建议创建虚拟环境。在本项目目录执行：

    python -m venv .venv
    .\.venv\Scripts\python -m pip install .
    .\.venv\Scripts\python -m uvicorn app.main:app --host 127.0.0.1 --port 8000

打开 http://127.0.0.1:8000 。不配置模型也可直接使用计算、赛题解析、文件、图纸和检索工具。Web 默认创建空项目，点击“导入赛题”后解析工作区提供的 PDF。

界面以“设计对话”为首页，左侧主要显示项目、研究任务与会话，九个功能入口下置。同一研究任务可以关联多个会话；每个会话独立保存上下文和未发送草稿，历史项目对话保留为“历史会话”。对话支持 Enter 发送、Shift + Enter 换行，手机上点击左上角展开导航。

会话功能上线前保存的计算和文件可从“项目历史记录”查看，包含实际输入、结果校验和文件预览；没有保存过聊天消息的项目不会生成虚构对话。左栏标注消息数、计算数或空会话，新执行的工具计算会保存到当前会话。

右上角“任务资源”显示当前任务的资料、会话引用和生成成果，支持文本/图纸预览、放大预览、下载及关联项目文件。桌面展开后可边对话边查看资料，“项目全部”可浏览项目中其他文件。

点击侧栏底部“化工研究空间”打开可编辑的模型设置，可配置 API/Ollama 地址、密钥、模型 ID 和调用参数。保存至数据目录中的 model-settings.json，对新任务立即生效，无需重启；密钥只在服务端保存，留空表示保留，清除需勾选对应选项。界面保存的配置优先于环境变量。环境变量仍可用于初始部署。

模型连接示例（PowerShell，在启动服务前设置）：

    $env:MODEL_PROVIDER="openai_compatible"
    $env:MODEL_BASE_URL="https://your-provider.example/v1"
    $env:MODEL_API_KEY="在本机设置，不提交到仓库"
    $env:MODEL_BALANCED="你的账户可用且支持工具调用的模型ID"
    $env:MODEL_FAST="你的快速模型ID"
    $env:MODEL_DEEP="你的深度模型ID"

Ollama：将 MODEL_PROVIDER 设为 ollama，OLLAMA_BASE_URL 设为 http://localhost:11434/v1，把 MODEL_BALANCED 等设置为已拉取、支持工具调用的模型名称。所选模型 ID 为空时明确拒绝启动任务。兼容服务确认支持 reasoning_effort 后才将 MODEL_REASONING_SUPPORTED=true；默认不发送。速度选择是模型映射，不是延迟承诺。

正式模型能力至少达到`deepseek-flash`基线，候选替代模型须按同任务/资料/预算验证；当前云端三个档位均映射该模型。传统RapidOCR/ONNX不再用于运行；AI图像转录仅在显式选择时调用配置视觉模型，当前真实接口视觉能力未资格化，拒绝图像输入时不会降级。模型和图片转录都不代表审核。具体要求及当前差距见[修订Goal](docs/RESEARCH_PLATFORM_GOAL.md)。

本地启动不会自动加载 .env。可直接配置系统环境变量；Docker Compose 会加载 .env。配置更改需重启服务。

## Linux 部署

详细步骤见 [部署说明](docs/DEPLOYMENT.md)。已在阿里云Linux实机完成镜像构建、基础部署验收、Office转PDF、源码复算、服务重启持久化，以及DeepSeek真实工具调用、错误修复和追问继续；范围及证据见[Linux验收](docs/LINUX_VALIDATION.md)。公网域名因未备案被阿里云拦截，HTTPS尚未开通；压力验收仍待执行。

    cp .env.example .env
    # 编辑 .env，设置随机 CHEMELLM_AUTH_TOKEN 和所需模型连接
    docker compose up -d --build
    docker compose logs --tail=100 chemellm
    curl http://127.0.0.1:8000/api/health

默认仅映射服务器回环地址。通过 SSH 隧道访问，或配置 HTTPS 反向代理。当前采用单一工作台口令，适用于单团队受控使用，尚无多租户隔离。只运行一个 Uvicorn worker；当前任务队列是进程内线程池，重启后任务标为“中断”，用户可继续。

## 操作路径

1. 导入提供的“26化工设计大赛题目.pdf”，建立 35 项要求（31 项必需、4 项额外计分）。
2. 上传设计依据与文献；使用物性、物料衡算、反应热与平衡、PR 闪蒸、UNIFAC 三元分相、精馏捷算法/逐级 MESH、换热器、管路压降、夹点和经济工具。默认输入是演示假设。
3. 配置模型后发起设计对话；工具错误会回传给模型，缺参数时追问；达到轮次上限后可继续。
4. 从文件页生成/预览 DOCX、PPTX、PDF、SVG 和 R2004 DXF 草图；识读矢量文字与位号候选，可编辑文件内置的 JSON 拓扑。外部图纸未声明的连接关系不自动重建。
5. 在验收页关联证据与人工校核说明。生成文件不会自动通过验收。
6. 打包项目成果，包内含文件、计算输入/结果、验收清单以及可复算的 Python 源码。

DOCX/PPTX在安装LibreOffice时转换为PDF保真预览，否则提供文本预览和原件下载。全文证据默认只解析原生文本。可显式使用`image_mode=ai`调用模型做图片文字转录，模型ID、图像/响应哈希和提示版本写入快照；必须核对原图，当前视觉接口尚未资格化。历史传统OCR数据只读保留。完整P&ID、三维布置与DWSIM原生模型尚未实现。范围、来源许可及操作见[全文证据说明](docs/FULLTEXT_EVIDENCE.md)。

全文工作流支持PDF/JATS快照、段落定位、原句核查、条件/相反证据标注、人工审核和导出。引句存在不代表科学支持；源转录纠正后，旧引用的审核需要复核。Europe PMC实际导入已在获准联网环境验证，受限网络失败时保留错误，可上传合法归档原文。

设备库支持带单位参数、原始文件/页码或计算记录关联、版本历史和人工审核。它不是厂家设备性能数据库。

## 赛题单元研究

    python -X utf8 scripts/competition_study.py

会建立明确标记的研究项目，导入原题，计算计量循环、NIST 脱氢热力学、50 级真空二元塔及水/乙苯/苯乙烯三元分相，生成 DOCX/PDF/Markdown 草稿和 PPTX 进展材料，最后打包计算记录及复算源码。路径保存于 data/competition-study-results.json。

这些是独立工况，尚未组成闭合流程。二元塔采用理想相平衡，三元分相使用 Dortmund UNIFAC 预测且不含氢气；尚需实测 VLE/LLE、氢气分配、催化动力学及全流程基准验证。数学收敛不等于产品指标或工程设计通过。

新增反应—冷凝前端联立研究：

    python -X utf8 scripts/frontend_study.py

保留水、乙苯、苯乙烯和氢气，将反应器连接含氢气液液冷凝器，输出五条物流与共同焓基准热负荷，并计算有机溶剂亨利预测倍率0.5/1/2的敏感性。生成DOCX/PDF/Markdown、计算边界图和可复算成果包，路径保存在 data/frontend-study-results.json。水中H2采用实际读取的Sander汇编参数，有机溶剂中H2为PR预测；[模型与数据说明](docs/HYDROGEN_MODEL.md)明确列出证据和局限。尚未连接精馏、循环或全厂公用工程，湿有机相不能直接送入二元塔。

反应—冷凝—四元湿精馏联立研究：

    python -X utf8 scripts/wet_train_study.py

将前端湿有机相的实际四组分流量与焓送入低压MESH塔，塔顶有机液分为馏出/回流，水相和尾气单独排出。Web提供四组分逐级剖面、四股塔出口和九条流程物流。脚本生成6级/12级比较、DOCX/PDF/Markdown、SVG/PDF/JSON/DXF研究草图和可复算包，路径保存在 data/wet-train-study-results.json。水中H2宽温关联式已核对IAPWS原表；[湿塔模型说明](docs/WET_COLUMN_MODEL.md)和原指南包含在源码包内。默认12级塔底苯乙烯摩尔分数约0.799，未满足合格产品设计；尚无循环、设备工程设计或独立模拟器/实验基准。

四元循环与纯度目标研究：

    python -X utf8 scripts/recycle_study.py

实际连接四组分有机馏出循环、1%排放、循环泵轴功和冷料汽化/预热，反应器接纳回流苯乙烯和H2并检查混合进料平衡。默认50级、20 kPa、R=10案例的塔底苯乙烯质量分数约0.999002，达到指定0.998研究目标；该目标未覆盖完整产品标准。Web显示13条物流、外部边界、50级剖面及纯度比较。生成DOCX/PDF/Markdown/PPTX、SVG/PDF/JSON/DXF草图和可复算包，路径保存在 data/recycle-study-results.json。[循环模型说明](docs/RECYCLE_MODEL.md)列出能量边界和假设。四组分循环已闭合，仍缺催化动力学/副反应、物性独立基准、设备、安全和全厂设计。

## 验证与打包

完整开发验证需安装可选依赖：`python -m pip install ".[dev,simulation]"`。

    python -m pytest -q
    node --check web/app.js
    node --check web/datasets.js
    node --check web/evidence.js
    node --check web/simulation.js
    python scripts/conversation_browser_smoke.py --url http://127.0.0.1:8001
    python scripts/model_settings_browser_smoke.py
    python scripts/history_browser_smoke.py
    python scripts/browser_smoke.py
    python scripts/evidence_browser_smoke.py
    python scripts/deployment_smoke.py
    python scripts/package.py

赛题逐项验收：

    python -m pytest -q tests/test_competition_source_coverage.py tests/test_competition_item_gate.py
    python scripts/competition_item_gate.py --bundle path/to/project-deliverables.zip --output data/qa/competition-item-gates.json

源文覆盖组件通过不代表工程成果逐项通过。只要逐项门槛有失败，就不得开始下一轮全套对话验收。

源码部署包生成于 dist/chemellm-linux-source-0.1.0.zip，附 SHA256 文件。打包采用白名单，不含 .env、项目数据或密钥。

全文研究案例：`python scripts/literature_study.py`，记录至 `data/literature-study-results.json`。项目包解压后在 `reproduce` 内运行 `python check_evidence_bundle.py`，核查原件、快照、引句和转录历史；这不构成科学正确性或专家审核证明。

## Cantera气相研究

安装 `python -m pip install ".[simulation]"` 后，工具页可选TP/HP气相平衡或定压/定容、绝热/恒温闭式反应器。固定h2o2/gri30及仅平衡的wgs4集合；每例保留实际YAML、原始发行机理、输入结果、许可证和独立复算脚本，反应器另有CSV/SVG/PDF轨迹。Docker配置已包含simulation扩展；Linux的7项资格对照、两个HTTP工况及原生/项目包复算通过，详见实机记录。

    python scripts/cantera_benchmark.py
    # 启动本地服务后：
    python scripts/cantera_study.py
    python scripts/check_cantera_study.py
    python scripts/cantera_browser_smoke.py

三个NIST热力学关联式对照和四个构造一级反应解析解通过预定容差。它们不验证真实动力学、乙苯催化机理或全厂设计。模型边界、原生交付和数据来源见[Cantera说明](docs/CANTERA_MODEL.md)。

## 实验数据与独立数值验证

“实验数据”页支持 UTF-8 CSV 和 XLSX（首行列名），可选择工作表、x/y及观测标准差列，拟合线性、一级趋近、一级衰减、幂律或 Arrhenius 模型。输出局部参数区间、残差、AIC/AICc比较及SVG/PDF/CSV/JSON，绑定原文件哈希。模型适用性和实验真实性仍需独立审核。

    python scripts/regression_benchmark.py
    # 启动本地服务后：
    python scripts/experimental_study.py
    python scripts/experimental_browser_smoke.py

三个NIST StRD案例已归档原件和哈希，用其认证参数、标准差和SSE验证数值算法。案例项目、报告和复算包路径见 `data/experimental-study-results.json`。它们不是LLM盲测或化学机理验证；详见 [实验模型边界](docs/EXPERIMENTAL_MODEL.md)、[评价协议](docs/EVALUATION_PROTOCOL.md)和[阶段审计](docs/RESEARCH_ACCEPTANCE.md)。

浏览器检查需要正在运行的本地服务、开发依赖及 Microsoft Edge。部署检查通过 HTTP 验证赛题、计算、文件和成果包；Linux 验收应增加 --require-office 强制 DOCX/PPTX 产生 PDF 预览。当前实际验证范围见 [验证记录](docs/VALIDATION.md)。

界面检查使用独立的 QA 服务：将 `CHEMELLM_DATA_DIR` 设置为 `output/playwright/conversation-data`，在 8001 端口启动。`conversation_browser_smoke.py` 验证项目/多会话切换、任务资源、预览和手机布局；`model_settings_browser_smoke.py` 只读检查 8000 的对话框与设置表单，在 8001 保存测试模型配置。两者不调用外部模型；截图和结果保存至 `output/playwright/conversations/` 和 `output/playwright/model-settings/`。

`history_browser_smoke.py` 使用 8002 端口、`output/playwright/history-data` 数据目录验证历史记录和聊天显示，只读检查 8000 中的原 Cantera 项目；不调用外部模型。截图与结果保存至 `output/playwright/history/`。

项目成果包保存全部计算记录。解压后进入 reproduce/，遵循包内README安装依赖，再执行 python replay.py；含Cantera计算时启用simulation扩展。生成 replay-results.json。逐级塔、含氢分相及前端联立复算要求双方校验通过，比较物理结果，允许迭代次数等诊断不同；检索、生成文件和项目状态工具列为 skipped。未知工具明确失败。

## 技术路径

当前优先实现“模型编排 + 检索证据 + 确定性计算 + 校验 + 人工审核”，不宣称已训练化工基础模型。库及扩展调研见 [工具与技术路线](docs/TECHNICAL_PATH.md)。面向工程专业性的后续工作应以有来源的参数、热力学适用性、模型验证与竞赛交付覆盖率作为评价标准，而不是只看语言流畅程度。
