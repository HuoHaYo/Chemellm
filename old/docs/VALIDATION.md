# 验证记录

更新日期：2026-10-20。下表原始执行环境为Windows、Python 3.12、Microsoft Edge headless；使用工作区`.venv`共享已有科学依赖，补装openpyxl、defusedxml及CPU OCR运行库。新增阿里云Linux实机结果独立记录于[LINUX_VALIDATION.md](LINUX_VALIDATION.md)，不与Windows测试混计；真实DeepSeek基础工具交互已验证，工程验收仍未完成。

| 检查 | 实际结果 | 证据与范围 |
|---|---|---|
| Python 测试 | 当前203 passed，169.31秒，无skip | `data/qa/pytest-agent-recovery-final.xml`；新增恢复12项，修订后定向38项通过；历史191/168项保留，不相加。原13/1失败按实际失败ID协议修复。本次过宽异常分类曾引入5项422→409回归，修复后全量通过，失败报告仍保留。1条框架TestClient弃用提示 |
| 前端语法 | 通过 | 最新`node --check`：web/app.js、web/run-recovery.js、web/study.js；其他模块保留既有语法检查记录 |
| 研究任务浏览器 | 参数至报告、检查点复用、传递失效/选择性重算及下载通过 | `data/qa/workflow-browser-results.json`；1→2 bar，100→200 kPa，调用次数3/0/3，旧下载字节不变；1440桌面及390移动截图检查通过。HTML pattern兼容问题修复后重新加载无新增控制台错误；中断处置对话框未端到端验证 |
| 研究任务真实恢复 | 两次Docker实际SIGKILL/重启通过 | `data/qa/linux-server/workflow-recovery/results.json`及前后完整事件；QA包装暂停工具前/产物保存后，未知结果拦截、明确重试/采用、检查点和原文件复用。仅显式任务，不证明LLM对话恢复；详见STUDY_WORKFLOW.md |
| 对话执行器真实模型恢复 | 两条deepseek-flash真实SIGKILL/重启通过，各2次API请求 | `data/qa/linux-server/agent-recovery/results.json`及before/after上下文、最终轨迹；完整批次已保存，首项复用、未知调用拦截、第三项继续；采用3次/重试4次尝试，采用路径原文件保持；两条最终摘要准确。首次错误摘要和5项异常分类回归保留，详见AGENT_RECOVERY.md；不等于复杂/保留/视觉/科学评价 |
| 对话中断处置浏览器 | 采用、继续和持久处置历史通过 | `data/qa/agent-recovery-browser-results.json`；云端SSH隧道、Edge普通表单、390×844和1440×1000截图；移动页scrollWidth=390，无新增JS异常。重试为HTTP验收，显式研究任务的处置表单另待浏览器验收 |
| Cantera气相资格对照 | 3/3热力学、4/4构造解析解通过 | `scripts/cantera_benchmark.py`及`data/qa/cantera-benchmark.json`；冻结的NIST来源/容差见CANTERA_BENCHMARK_PROTOCOL.json。关联式可能共享原始来源；不是真实动力学实验或LLM保留评价 |
| Cantera真实浏览器 | 通过，JS异常0条 | `scripts/cantera_browser_smoke.py`；机理/TP选择、WGS四物种、实际ZIP下载、未知物种错误、定压绝热轨迹及SVG加载、定容恒温、CSV/PDF/YAML/JSON、390px无溢出；data/qa/cantera-browser-results.json |
| Cantera研究交付与解压复算 | 5/5原生包与5/5源码计算一致；48/48文件哈希一致 | `scripts/cantera_study.py`和`scripts/check_cantera_study.py`；`data/qa/cantera-study-verification.json`。最终解压目录cantera-replay-20261020-051838-426434；实际/发行YAML双哈希、记录的数值校验、全部采样状态通过；属于同引擎可复现性 |
| Cantera研究文档 | DOCX48段、PPTX4页、PDF2页、MD可读 | 从同一解压包解析原件；两页PDF均渲染并检查，版面可读、无裁切。Office原件未经过LibreOffice保真预览，不升级工程审核 |
| 全文证据真实浏览器 | 通过，JS异常0条 | `scripts/evidence_browser_smoke.py`；真实归档117段/分页、错引拒绝、审核与修改、四格式实际下载、扫描PDF识别/纠错/旧审核失效/保留替换记录、390px无溢出 |
| OCR原始准确性 | 控制PNG数值读取通过；扫描PDF出现100→1o0，未通过原始精确转录 | RapidOCR1.4.4/ONNX1.31 CPU实际推理；`data/qa/evidence-browser-results.json`记录raw_exact_match=false；原图和截图已查看。纠错流程通过不升级OCR准确性 |
| 开放全文真实联网 | 检索、导入函数及服务/浏览器均通过 | `scripts/fulltext_network_smoke.py`和`scripts/fulltext_browser_network_smoke.py`；PMC10110988、DOI/CC BY/117段与原件哈希。沙箱Python原先ConnectError，获准联网环境成功；均非mock |
| 全文研究与纠错案例包 | 归档研究4/4、在线研究4/4、纠错案例3/3引句及历史校验通过 | 独立解压后执行包内check_evidence_bundle.py；literature-replay-final-20261020、literature-live-replay-20261020、ocr-correction-replay-20261020；仅完整性/引句/纠正历史，不裁决科学支持 |
| 实验数据真实浏览器 | 通过，JS异常0条 | `scripts/experimental_browser_smoke.py`；NIST导入及单位、模型比较与参数区间、实际SVG加载、四格式下载入口、Excel上传/工作表、衰减拟合、390px无横向溢出；`data/qa/experimental-browser-results.json` |
| NIST独立认证数值 | 3/3通过 | `scripts/regression_benchmark.py`；原始`.dat`认证参数/标准差/SSE；参数最大相对偏差约1.83e-8；`data/qa/regression-benchmark.json`。只验证回归算法，不是化工模型或LLM验证 |
| 实验公开案例成果包 | 6/6回归复算一致；19/19文件哈希一致 | `scripts/experimental_study.py`；解压到 `data/qa/experimental-replay-20261020`，使用包内源码复算；3条表格编排和报告生成记录明确跳过，6条数值记录独立执行 |
| 浏览器操作 | 通过，JS异常0条 | `scripts/browser_smoke.py`；赛题、计算、二元MESH、前端/湿塔/循环的5/9/13条物流、50级剖面、质量纯度目标/外部边界、报告、图纸读写/拓扑、设备历史、验收和移动宽度 |
| HTTP 部署检查 | 本机通过 | `scripts/deployment_smoke.py`；赛题原件哈希、35项清单、计算、文档与成果包。DOCX/PPTX 本机为文本预览，PDF为视觉预览 |
| 真实网络 | 2026-10-18成功 | Crossref题录5条；PubChem styrene CID7501、C8H8、104.15 g/mol；原始响应记录 `data/qa/network-results.json` |
| 赛题研究成果包复算 | 5项数值计算全部一致 | 解压至 `data/qa/study-replay`，在包内 `reproduce/` 执行 `python replay.py`；两个报告生成记录明确 skipped |
| 前端联立研究成果包复算 | 3项敏感性计算全部一致 | 解压至 `data/qa/frontend-replay-current`，在包内 `reproduce/` 执行 `python replay.py`；图纸/报告生成明确 skipped |
| 四元湿塔联立研究包复算 | 6级/12级两项联立计算均一致 | 解压至 `data/qa/wet-train-replay`，在包内 `reproduce/` 执行 `python replay.py`；报告/图纸生成明确 skipped；物理结果容差1e-8 |
| 四元循环研究包复算 | 50级、四组分循环计算一致 | 初版解压至 `data/qa/recycle-replay`；最终版本为 `data/qa/recycle-replay-current`，使用包内源码及输入执行 `python replay.py`；外部组分/原子/质量/能量校验通过，物理结果容差1e-8；报告/图纸生成明确 skipped |
| 湿塔50级求解 | 新求解器通过完整四元方程 | 旧版曾超90秒；改用微量组分对数衡算、二元/逐级稀组分初始化与稀疏Newton，50级/25级进料/R=10单程和循环均成功；最终原关联式、逐级衡算及有限TPD检查 |
| 中文研究报告 | DOCX/PDF/MD/PPTX已生成 | `scripts/competition_study.py`；PDF4页，已检查首末页渲染；Office原件可解析，尚无保真渲染证据 |
| 反应-含氢冷凝研究 | DOCX/PDF/MD和SVG/PDF/JSON/DXF已生成 | `scripts/frontend_study.py`；报告PDF2页，已检查首面与计算边界图；指定折线避免支路穿过其他节点 |
| 四元湿塔联立研究 | DOCX/PDF/MD和SVG/PDF/JSON/DXF已生成 | `scripts/wet_train_study.py`；报告PDF2页已检查全部页渲染、研究边界图已检查；图中流股与计算对应，无产品验收声明 |
| 四元循环研究 | DOCX/PDF/MD/PPTX及SVG/PDF/JSON/DXF已生成 | `scripts/recycle_study.py`；报告PDF3页和循环图已检查渲染；PPTX仅解析/文本预览，未宣称保真渲染 |
| 源码包 | 白名单ZIP及SHA256 | `scripts/package.py`；包含新增模型、脚本、说明与测试，不含 `.env`、本地 `data/`、模型权重或密钥 |

完整本地证据保存在 `data/qa`，不会自动混入部署源码包。源码包包含本记录和复现脚本；包的完整性可用附带 SHA256 校验。

## 数值实例

这些实例验证实现的数学检查，输入均为研究假设。早期单元实例相互独立；最后几行分别为反应-冷凝前端、湿塔单程及当前四组分循环边界，不代表完成全厂设计。

| 模型和工况 | 输出摘要 | 校验范围 |
|---|---|---|
| 乙苯脱氢，873.15 K、1 bar、蒸汽/乙苯8 | ΔH≈124.265696 kJ/mol；Kp≈0.237615918；理想平衡转化率≈0.754435 | NIST明确条目与高温Cp积分、质量/能量一致；无催化动力学和副反应 |
| 苯/甲苯二元塔，100 kmol/h、10级、R=3、常压 | xD≈0.960995905；xB≈0.039004095；QR≈1740.373 kW，QC≈1721.673 kW | 逐级物料和能量；末态直接用原蒸气压关联式检查Raoult关系 |
| 乙苯/苯乙烯塔，100 kmol/h、zEB=.4、50级、进料25级、20 kPa、R=10、D/F=.4 | xD≈0.989013704；xB≈0.007324197；QR≈4743.988 kW，QC≈4742.690 kW | 原关联式、逐级MESH和全塔能量；尚无独立模拟器/实测VLE基准 |
| 水/乙苯/苯乙烯，100 kmol/h、z=.8/.08/.12、310 K、101325 Pa | 两液相：水相≈79.734094 kmol/h，有机相≈20.265906 kmol/h | Dortmund UNIFAC预测；保留互溶；组分、逸度、231点液相TPD筛查 |
| 同上组成，360 K、80 kPa | 气液液三相 | 共存相逸度与组分闭合；有限TPD采样不能证明全局稳定性 |
| 反应-含H2冷凝，EB400 kmol/h、蒸汽比8、X=.6、823.15→873.15→310 K、100 kPa | 反应供热≈11646.002 kW；冷凝移热≈76066.943 kW；湿有机相仍含水≈5.516931、H2≈.200708 kmol/h | 四元全组分传递、原子/质量/共同焓基准；H2溶剂修正的Gibbs–Duhem和焓导数校验；有机Henry为PR预测 |
| 同上前端接20 kPa湿塔、12级/第6级进料、R=3、有机D/F=.4、塔顶310 K | 塔底苯乙烯x≈.799072674；塔再沸≈9375.337 kW、塔冷凝移热≈8735.779 kW；有机馏出/水相/尾气/塔底≈160.0171/3.41033/.32846/236.2869 kmol/h | 实际四组分和上游焓传递、逐级MESH、全流程物热/原子闭合、有限TPD搜索；尚无循环、合格产品或独立模拟器/实验基准 |
| 四元循环：新鲜液态EB400 kmol/h、总水/EB=8、50级/进料25级、20 kPa、R=10、1%有机排放 | 塔底SM质量分数≈.999002212；SM≈387.671466 kmol/h；循环EB≈254.435359、SM≈3.207295、水≈2.815614、H2≈.017982 kmol/h | 8轮循环闭合，实际杂质影响平衡；外边界物热/原子/质量；指定.998纯度目标达到，不等于完整产品标准 |
| 同上热负荷 | 预热汽化≈28331.539、反应≈19065.706、塔再沸≈39913.212 kW；前端/塔冷凝移热≈124596.187/38840.666 kW；循环泵≈.992290 kW | 泵功与冷液实际焓计入；外部水蒸汽已按气相温度供应，不含锅炉产汽、热集成和全厂公用工程 |
| Cantera/wgs4，1000 K、101325 Pa、初始CO/H2O/CO2/H2=1/1/.1/.1 | Kp≈1.435357685；NIST Shomate参考≈1.438464021；反应进度≈.499559645 | 冻结容差下的关联式与平衡实现对照；无甲烷/碳/其他相态或催化动力学 |
| Cantera/h2o2，1001 K、101325 Pa、H2/O2/N2=2/1/4、定压绝热积分1 ms | 最终温度≈2665.619 K | 均相闭式数值结果、质量/元素/比焓/约束/温区检查；未认证实验点火或真实机理适用性 |

新冷凝模型还检查了两种VL（单水相、单有机相）及稳定全气相分支；没有强制所有工况都返回三相。0.5/1/2有机Henry倍率下，有机相H2分别约0.397846/0.200708/0.101289 kmol/h；倍率只是敏感性，不能解释为实验置信区间。Sander数据来源和所有限制见 [HYDROGEN_MODEL.md](HYDROGEN_MODEL.md)。

## 已修复的实测问题

- 并发冷启动调用触发 Chemicals 数据表未完成初始化，出现 `Tm_sources` 未定义；现计算入口使用进程内锁，独立子进程并发测试及浏览器/API同时操作均通过。
- R2004 DXF中文被编码为 `\U+` 后直接进入SVG预览；现先解码，保留文字居中/旋转与实际几何，已检查中文预览。
- 超过100条计算时成果包遗漏历史；现列表支持分页，成果包读取全量，103条案例通过。
- 复算时JSON数字键与字符串键不一致；现对两侧使用统一JSON格式。MESH求解迭代数和已通过的残差检查按诊断保留，物理结果仍以1e-8相对/绝对容差比较。
- 湿塔303 K下限取Henry温度导数时，曾同时访问302.998 K的苯乙烯蒸气压，超出原关联式范围；现只对Henry常数取差分，蒸气压及其导数保留在303 K原关联式范围，边界检查通过。
- Cantera子进程最初在Windows受GBK/UTF-8不一致影响；明确使用`-X utf8`和JSON编码后通过。实际YAML采用字节写入，避免换行转换造成SHA不一致；实际/发行机理篡改检查通过。固定发行文件以绝对路径加载，同名工作区YAML不能覆盖。

## 尚无证据的项目

- Windows本机无Docker、Ollama及LibreOffice；云Linux已完成基础镜像构建、Office转换、复算和服务重启持久化，见独立实机记录。
- Linux的 `python scripts/deployment_smoke.py --require-office` 及真实DeepSeek的工具调用/失败修复/追问继续已通过；域名遭未备案拦截，公网HTTPS、压力及长期运行尚未验收。三个人工构造的小案例不能代替通用模型评价。
- NIST原始HTML已人工检查，Crossref题录未当作全文阅读；补充材料DOI不能替代主论文全文。
- 没有该体系实验VLE/LLE、有机溶剂/混合溶剂H2溶解度、催化动力学、厂家设备曲线或独立专业模拟基准；Sander水中H2参数已读取，但局部温度式与溶剂混合仍需验证。
- 竞赛31项必需成果仍未完成工程验收；研究草稿没有自动升级为 verified。
- 新增NIST回归认证不能替代当前乙苯/苯乙烯流程的实验或独立软件基准；多类别LLM保留评价集与通用模型对照尚未完成。
