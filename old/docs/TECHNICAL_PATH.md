# 化工工程平台技术路径与工具调研

## 选择依据

2026-10-21调整：建设能够胜任化工工程师大部分工作的通用平台，以实际DeepSeek一轮对话完成赛题全套工程文件作为当前第一关。按完整流程/优化、设备、公用工程、安全环保/经济、PFD/P&ID、布置和三维原生文件等交付缺口选择后端，优先真正接入自动执行与文件生成。既有软件目录保留为候选，安装不等于接入；不能先做大规模评测或研究案例而延后完整工程交付。

模型负责需求理解、规划、决策和调用；数据库/文献提供依据，专业求解器负责数值，工程数据贯通报告和图纸，独立检查核对量纲、适用范围、数值和版本一致性。根据实际剩余错误再决定是否微调。当前未训练或微调模型，也没有可靠性优于通用模型的完整对照。验收规则见[ENGINEERING_ACCEPTANCE.md](ENGINEERING_ACCEPTANCE.md)。

## 已接入

| 工具/来源 | 使用方式 | 范围与限制 |
|---|---|---|
| [thermo](https://thermo.readthedocs.io/) / [Chemicals](https://chemicals.readthedocs.io/) | Python实际调用，物性及 PR 闪蒸 | 关联式/估算值需审查；PR混合物当前kij=0 |
| [CoolProp](https://coolprop.org/) | 水蒸汽状态计算 | 绝对压力，参考态明确；非全组分物性库 |
| [Cantera 3.2.0](https://cantera.org/3.2/) | 固定机理的TP/HP气相平衡和四类闭式反应器；原生YAML/来源机理/轨迹复算 | 3例NIST热力学、4例构造解析解通过；Linux已有局部实测，见LINUX_VALIDATION.md；均相理想气体不替代催化机理或完整流程优化 |
| NIST WebBook 原表 + SciPy | 乙苯脱氢高温反应焓/熵、Kp、气相供热量 | 数据原文已复核；理想气体单反应，不含催化动力学 |
| SciPy / MESH / thermo | 二元精馏逐级物料、相平衡与能量求解 | Raoult 理想相平衡、饱和液进料；未用实测 VLE/独立模拟器验证 |
| Dortmund UNIFAC / FlashVLN | 水/乙苯/苯乙烯 VLLE 预测，逸度/组分/采样稳定性检查 | 不含氢气；不是完整反应物流冷凝模型；未以实测 LLE 校核 |
| Sander 2023 / PR Henry / UNIFAC / SciPy | 含H2四元冷凝及反应器前端连接，物料/原子/共同焓基准 | 水中H2为汇编数据，有机H2为PR预测；303–313.15 K、50–200 kPa；尚无实验基准及全流程循环 |
| IAPWS G7-04 / UNIFAC / Henry / sparse MESH | 四元湿精馏及反应-冷凝-湿塔一次通过连接 | IAPWS水中H2已对照原表；有机H2为PR预测；单液热塔板、VLL塔顶，有限TPD搜索；此工具仅单程范围，无独立工程基准 |
| 四元循环 / 混合进料质量作用式 / Anderson | 有机馏出四组分循环、排放、泵功、冷料汽化预热及质量纯度比较 | 已闭合当前四组分研究边界；未含真实副产物/催化动力学、完整产品标准、独立物性基准和全厂设计 |
| fluids / 工程公式 | Darcy–Weisbach、FUG 精馏捷算法、显热夹点热量级联 | 定物性/恒α/恒热容假设分别适用，不等同设备工程选型 |
| [Pint](https://pint.readthedocs.io/) | 单位换算及不相容量纲拒绝 | 尚未给全部流程变量建立统一 Quantity 类型 |
| [Crossref](https://www.crossref.org/documentation/retrieve-metadata/rest-api/) | 论文题录、DOI、作者、年份 | 不是全文获取，需联网；错误明确返回 |
| [OpenAlex](https://docs.openalex.org/) | Crossref不足时回退 | 服务可能要求API key；配额取决于服务条款 |
| Europe PMC / PDF/JATS / BM25 / configured vision model | 开放题录与全文、原生文本快照、段落引句及审核失效；机器视觉转录仅显式调用 | 全文联网真实测试通过；旧RapidOCR误读100为1o0的历史证据保留；当前视觉接口未资格化，科学支持与复杂图纸连接待审核 |
| [PubChem PUG REST](https://pubchem.ncbi.nlm.nih.gov/docs/pug-rest) | 分子式、分子量、IUPAC/CID | 需联网；原始数据来源可能有各自条款 |
| [ezdxf](https://ezdxf.readthedocs.io/) | R2004 DXF 读写、图元/文字、实际几何预览、内置拓扑 | 未生成完整合规P&ID，gbcbig字体只引用不分发；外部连接语义未重建 |
| [python-docx](https://python-docx.readthedocs.io/)、[python-pptx](https://python-pptx.readthedocs.io/)、ReportLab | 报告/PPT/PDF生成 | 当前草稿排版，未符合竞赛期刊模板的全部细则 |
| [LibreOffice](https://www.libreoffice.org/) | Office转PDF | Windows未安装；Linux实际简单DOCX/PPTX转换通过，完整工程文件复杂排版仍须逐件检查 |

thermo/CoolProp 官方文档已在项目初始调研时获取。其余链接是实现与扩展的权威入口；链接本身不代表已完成当日联网验证。工具目录 app/catalog.py 同时标明集成状态。

## 待接入和研究参考

| 组件 | 角色 | 接入前必须完成 |
|---|---|---|
| [DWSIM](https://dwsim.org/) | 全流程稳态/动态模拟、原生源文件 | Linux运行方式、自动化接口、物性/单元基准验证、开源授权核对 |
| [IDAES](https://idaes.org/) / Pyomo / IPOPT | 方程型过程模拟和约束优化 | 求解器安装、热力学包适用性、初始化与收敛基准 |
| [RDKit](https://www.rdkit.org/) | 分子结构和描述符 | 输入结构校验；不替代物性实验和工程模型 |
| [NIST WebBook](https://webbook.nist.gov/chemistry/) 扩展 | 当前反应热力学已使用少量核对过的原表 | 尚未建立通用在线查询适配器；批量使用需核对条款；未镜像付费库 |
| [Semantic Scholar](https://www.semanticscholar.org/product/api) | 引文网络和论文发现 | API授权、限流、全文版权 |
| [PaperQA2](https://github.com/Future-House/paper-qa) | 文献证据问答参考 | 版本/授权、引用真实性、全文获取渠道与评估 |
| [ChemCrow](https://github.com/ur-whitelab/chemcrow-public) | 化学工具智能体参考 | 每个工具的边界、授权、适用问题和准确率 |
| [FreeCAD](https://www.freecad.org/) | 三维设备布置、原生CAD | 尺寸、管线碰撞、检修空间、安全间距与规范审查 |

## 数据库建设顺序

1. 物性：已接入库，保存每次查询的单位、温压、关联式和来源。后续增加原始文献引用、实验/估算分类、不确定度和相平衡二元参数。
2. 设备：已建立按项目的带单位参数、文件页码/计算依据、版本历史与人工审核；假设参数不能审核通过。尚无厂家规格/性能曲线库，应以授权手册录入并保留有效日期。
3. 模型：已登记计量循环、纯料及混合进料气相反应热力学、二元 MESH/FUG、PR/VLLE、含氢冷凝、四元湿塔及单程/循环连接、LMTD、压降、显热夹点和税前 DCF。后续需催化动力学/副产物、三相热塔板、独立物性基准、全厂优化、控制、安全分析和完整现金流。
4. 文献：已有题录/开放全文、PDF/JATS原生文本快照、BM25及原句定位。传统RapidOCR/ONNX已移除；显式AI视觉转录等待真实端点资格验证，并保留转录核对/版本审核。后续补语义检索与重排、召回评价、系统综述和科学支持审核；不得以引句匹配代替科学判断。

## 工程交付实现路线与赛题验收

先统一设计依据及工程对象，按原题要求建立成果清单，并行补各专业依赖；以可运行的完整流程和设备/布置等源文件、全套报告图集、同源校核及自主编排为交付主线。最终从新项目一次用户输入，由平台实际调用DeepSeek生成、检查、修复和打包全部成果。当前专门研究脚本只作组件基线，不能在平台外运行后把成品放进项目冒充自主通过。

已解析的原题允许团队自行决定原料、规格、产品与规模，因此这些参数须有资源/市场/政策调研证据。当前20万吨/年等默认值只是演示输入，不能直接升格为设计决策。

已有独立单元研究、反应-冷凝前端、湿塔单程及四元循环研究，分别由 scripts/competition_study.py、scripts/frontend_study.py、scripts/wet_train_study.py、scripts/recycle_study.py 生成可复算草稿。循环保留产品和H2杂质对反应平衡的影响，并计入泵功/冷料汽化预热。下一步需完整产品规格驱动优化、真实副产物/催化动力学、实测H2分配/VLE/LLE及独立模拟器基准。随后完成设备、HAZOP、热集成、布置及经济分析。每项对应原文页码、源文件、输入版本、检查结果和最终图文。整体验收还包含 DOCX+PDF、字数、图纸字体/版本、三维源文件和现场运行验证。

通用模型、工具增强模型和领域微调模型的对照应包含：数值误差、物性方法选择、守恒、可复算率、引用真实性、漏项率、工具失败修复率与人工复核时间。测试集需避免把生成答案本身当作真值。
