# 化工工程平台目标与当前证据

目标修订：2026-10-21。主线改为建设能够胜任化工工程师大部分工作的通用工程平台；当前第一关是平台实际调用DeepSeek，用户一次完整任务输入后自主交付赛题全套正确、可编辑、可运行文件，见[平台目标](RESEARCH_PLATFORM_GOAL.md)和[整包验收](ENGINEERING_ACCEPTANCE.md)。既有研究/数值/测试证据保留，不再采用“先运行可靠性、再研究案例、最后完整赛题”的阶段顺序。以下实测截至2026-10-20，第一关尚未通过。

2026-10-21逐项测试更新：`test_competition_source_coverage.py`通过，验证原题PDF哈希、31项必需/4项条件材料源文片段，且通过平台文档工具逐条绑定35项真实原句。该结果是需求来源组件门槛，不是35项工程交付通过。只读审计器重查冻结失败包`282e073372c64a319885214c7b461881`，结果`0/35`通过，源文哈希/片段匹配通过、35项计划映射完整，但源绑定缺失，成果格式/内容门槛未过；未启动修订后的整包对话，见`data/qa/engineering-delivery/282e073372c64a319885214c7b461881/item-gate-baseline.json`。该包是旧平台冻结失败记录，不是当前源码运行结果。

| 验收层次 | 本轮要求 | 当前状态 |
|---|---|---|
| 第一关：一轮全套工程交付 | 新项目经实际用户入口，DeepSeek自主规划/计算/校核/修复/生成；覆盖31项必需和4项额外材料及原题条件，最终整包打开/运行/编辑/复算，无人工补件 | 未通过；局部计算、草稿和工具恢复不抵扣整包缺项 |
| 后续：通用工程能力 | 改变原料、规模、工况、体系或工程任务，复用平台数据/工具/模板，扩展至设计、运行诊断与技改等常见工作 | 待验收；不得以固定赛题答案代替能力 |

## 支撑能力与既有证据

| 要求 | 实现/实测证据 | 独立校核/审核状态 | 后续验收 |
|---|---|---|---|
| 功能审计与评价 | STATUS/VALIDATION/本审计；评价协议 | NIST回归3例；Cantera热力学3例/构造解析解4例资格验证 | 多类别开发/保留集、专家参考与真实模型对照未完成 |
| 可信数据 | 物性方法范围/单位缓存、设备来源版本审核 | 若干原始数据核对 | 实验/预测/假设统一模式、冲突/误差/许可/版本、厂家曲线与动力学待补 |
| 全文研究 | PDF/JATS原生文本快照、BM25、表格/公式候选、原句核查、版本审核；传统RapidOCR/ONNX已移除，显式AI图像转录路径待真实接口资格化 | 两论断四引句包独立完整性校验；历史传统OCR数值误识别及纠正原样保留；本轮源码离线测试覆盖AI请求/失败语义，非视觉能力测试 | 当前DeepSeek视觉接口未探测；复杂公式/表格/专业图纸视觉准确性、系统综述及科学支持审核、语义检索/保留评价未完成 |
| 实验建模 | CSV/XLSX、5类拟合/加权/局部区间/残差/AICc、真实浏览器 | 3项NIST认证；6项拟合独立包内复算；19文件哈希一致 | 正式DoE、多变量/ODE、独立实验预测与结构误差未完成 |
| 专业计算后端 | Python科学库、研究求解器及Cantera 3.2.0固定气相模型；原生文件/来源/轨迹/复算 | 3项NIST关联式和4项构造解析解；真实Web/HTTP和原生包复算；无当前流程独立工程基准 | 真实动力学与实验、成熟过程模拟/优化后端、物性/流程对照及完整全厂工程未完成 |
| 多轮执行 | 失败ID/子任务隔离、研究任务依赖/失效/检查点；对话完整批次与执行前输入持久化、未知调用处置及预算保留 | 最新完整203项通过；基础3项真实DeepSeek、显式研究任务2次恢复、另2条真实模型SIGKILL轨迹通过；采用3/重试4次，摘要准确，对话采用/继续Web通过 | 其余处置表单浏览器验收、全部来源依赖、复杂/跨天任务、费用资源预算和硬性终止待补 |
| Web和成果 | 研究任务页、专业图/实验图表/全文证据与文档预览下载；显式AI视觉识读选择 | 原功能、实验、全文及真实全文联网Edge操作；Linux简单DOCX/PPTX实际转PDF；SSH隧道Edge登录通过。当前图片界面 smoke 仅测试原生模式保留扫描件 | 当前实际AI视觉能力、复杂Office排版、模型速度费用及多用户权限待补 |
| 云端运行支撑 | Alibaba Cloud Linux 3实机构建/运行；鉴权、赛题、数值、Office、AI视觉接口资格、复算、数据保留；隔离容器任务及对话恢复 | 基础DeepSeek3项、任务2次恢复、另2条真实模型SIGKILL及采用/继续Web；43文件哈希一致，首次失败保留 | 真实视觉端点探测未执行；按整包交付需要补自主长任务、预算和资源；备份/压力及备案后HTTPS独立推进 |
| 工程资料与研究支撑 | 实验、全文证据及已有过程研究案例 | 算法、复算和引句校验部分通过 | 随工程任务补必要来源和独立校核；研究比较不作为启动整包交付的前置阶段 |
| 全套工程能力 | 原题35项映射、部分流程/文档/图纸工具 | 31项必需仍未工程验收，无一轮整包通过记录 | 完整流程/优化、设备、公用工程、安全环保/经济、完整图纸/布置及原生文件、生成校核与自主执行 |
| 扩展与训练 | 工具路线及微调原则已记录 | 无微调收益对照 | 首轮通过后检验迁移与常见工作覆盖；根据真实缺口选型，训练按证据决定 |
| 最终交付 | 源码、研究包、依赖和部署说明持续更新 | 尚无通用工程能力验收 | 平台源码/配置、整包实际成果、工程证据、真实自主执行和迁移结果 |

## 既有具体证据（保留原范围）

- `data/qa/regression-benchmark.json`：NIST认证参数/标准差/SSE。
- `data/qa/experimental-browser-results.json`：实际Edge操作、XLSX及移动页面。
- `data/experimental-study-results.json`：案例项目、输入来源、分析、报告、成果包。
- `data/qa/experimental-replay-20261020/artifact-integrity.json`：19文件哈希。
- `data/qa/experimental-replay-20261020/reproduce/replay-results.json`：6条数值独立复算。
- 历史完整pytest168/191 passed保留；原13/1失败已按实际失败ID修复并补负例。最新`data/qa/pytest-agent-recovery-final.xml`为同一次完整203 passed、无skip、169.31秒；修订后定向38项通过，不是历史测试数量相加。保留本次过宽异常分类导致5项回归的报告，修复后全量通过。功能测试不作为LLM或物理过程准确性成绩。
- `data/qa/workflow-browser-results.json`：真实表单完成参数—两级计算—报告、重复执行0次新增调用、源参数改动传递失效、选择性重算及旧/新报告下载，桌面和移动截图已检查。
- `data/qa/linux-server/workflow-recovery/results.json`：2次真实SIGKILL/重启；QA暂停包装触及调用前和实际产物保存后的窗口，未知调用阻止直接执行，确认重试/采用已有记录后复用检查点和原文件；不含LLM调用或工程审核。
- `data/qa/linux-server/agent-recovery/results.json`及before/after上下文与最终轨迹：另2条真实deepseek-flash批次，各2次API请求及一次SIGKILL；首项保留、未开始余项继续，采用3次/重试4次，采用路径原文件不变。首次“无重试”错误摘要在initial-runs保留；修复后的两条摘要准确。
- `data/qa/agent-recovery-browser-results.json`：Edge通过普通表单采用已有结果、继续原任务及持久处置历史，390/1440截图已检查；重试经HTTP验收，其他处置表单浏览器资格不在此项内。
- `data/qa/cantera-benchmark.json`：3例NIST热力学关联式、4例构造一级反应解析解；公开开发资格，不是动力学实验或保留评价。
- `data/qa/cantera-browser-results.json`：实际Edge操作/轨迹/下载/错误/移动布局；`data/cantera-study-results.json`为五工况研究、报告及原生包。
- `data/qa/cantera-study-verification.json`：五个原生包、五条源码记录复算通过，48文件哈希一致；DOCX/PPTX解析及两页PDF渲染检查通过。同引擎复算不替代独立物理或Linux验证。
- `data/qa/evidence-browser-results.json`：全文、论断修改、审核失效、实际扫描OCR与纠错替换；原始100→1o0错误明确保留。
- `data/qa/fulltext-network-results.json`、`data/qa/fulltext-browser-network-results.json`：获准联网环境的真实Europe PMC检索与导入，非mock。
- `data/literature-study-results.json`：在线全文研究两项论断四条引句，仍待科学审核；`data/literature-study-archived-results.json`保留先前连接失败和合法归档回退记录。
- `data/qa/ocr-correction-replay-20261020/reproduce/evidence-integrity.json`：含纠错历史的三个引句记录校验通过。
- `data/qa/engineering-delivery/282e073372c64a319885214c7b461881/item-gate-baseline.json`：旧冻结失败包逐项检查0/35通过，源文PDF与35条源文片段通过；仅用于保留缺项基线。
- `data/qa/literature-live-replay-20261020/reproduce/evidence-integrity.json`：真实在线全文研究的四条引句记录校验通过。
- `data/qa/linux-server/server-qa/deployment-results.json`及`linux-server/`子目录：真实Linux部署、Office转换、数值/原生包/源码复算、服务重启数据保留。
- `data/qa/linux-server/server-qa/live-model-qa/results.json`：deepseek-flash真实3项基础交互；`initial-results.json`保留首次追问未通过结果。
- `data/qa/linux-server/server-qa/tunnel-access-results.json`：SSH隧道HTTP与真实Edge登录；`domain-results.json`：阿里云未备案403，HTTPS未开通。
- `data/qa/skill-download-retry.json`：官方固定版本的PDF、Playwright、Jupyter Notebook技能重新联网下载并安装；只说明开发技能可用，不作为平台后端接入或科学验收。

优先后续工作：按35项结果修复要求源绑定、跨文件数值校验、原生CAD/P&ID/布置、完整流程模拟、设备/经济软件源文件和所有缺项，再逐项实测通过后才启动新项目的一轮真实DeepSeek整包对话。203项回归等保持为支撑基线；网络重试、AI视觉资格、持久执行及预算按工程依赖推进。大规模保留评价和研究对照不再排在整包交付之前；必要科学/工程检查不省略，备案不阻塞SSH测试。
