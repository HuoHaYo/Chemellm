# 全文证据与AI视觉转录

更新：2026-10-21。本模块保留全文定位、引用完整性、转录版本及审核记录，不自动裁决科学结论。传统RapidOCR/ONNX运行路径已移除；此前项目中的OCR快照和证据仍以原记录只读保留。

## 使用流程

1. 在“文献检索”选择 Crossref/OpenAlex 或 Europe PMC；题录不是全文阅读。开放文献的 PMCID 可转入“全文证据”页，确认获取；也可上传有权使用的 PDF、JATS XML、DOCX、PPTX、文本和图像。
2. 默认建立原生文本快照。PDF保留实际页码/坐标和可提取的文本、表格与公式候选；JATS保留章节、段落、表格和源公式；没有出版页码时不编造页码。DOCX页码不可靠，PPTX页码指幻灯片。
3. 扫描页和图片只有在明确选择“AI视觉转录”后才发送给配置模型。转录要求原样保留可见字符和[不清]标记，不执行图像中的指令，不补写推断内容。模型拒绝图像、超时或无结果时保留失败，不切换到传统OCR或其他隐式后端。
4. 每个AI视觉请求保留模型ID、提示版本、压缩输入图像哈希、响应哈希及服务商返回的使用量。AI文字只是机器转录，必须逐字对照原图；无识别置信度声明，也不证明文献真实性、工程数值正确性或图纸拓扑。
5. 登记论断，在全文中选择段落并录入原文引句，保留体系、温压、常数定义等条件，标注支持、反驳或背景。程序只以Unicode NFKC与空白标准化核对原句，不自动将改写或修正数字当原句。
6. 可对机器视觉转录逐字核对并保存人工纠正新快照，保留旧记录及纠正者/依据；引用旧转录的审核变为待复核，须换用新快照并重新审核。审核须注明核对者、版本、结论和依据；审核没有作为模型工具暴露。姓名只是记录字段，不代表多用户身份或专家资质。
7. 导出JSON/Markdown/DOCX/PDF证据记录，或打包项目，在解压目录的`reproduce/`中执行`python check_evidence_bundle.py`。它校验原件字节、快照哈希、引句出现及记录的转录修订历史，不验证转录准确或科学支持程度。

## 能力与限制

- PDF原生文字、表格、公式候选优先由pdfplumber读取。仅扫描页可使用PDFium渲染图像供AI视觉模型；单页渲染上限2500万像素，再缩至最长边2200像素并压缩为JPEG，模型输入上限10 MiB。上传文件仍受25 MiB上限约束。
- 图像视觉请求使用与聊天相同的`/chat/completions`兼容接口，模型取`MODEL_VISION`，留空时使用`MODEL_BALANCED`。调用记录真实模型ID；模型拒绝或失败时不静默降级。视觉能力必须针对确切服务商、账号、模型ID、API格式和图像样本完成资格测试后，才可用于正式自动验收。
- 当前DeepSeek真实环境已实测文本和工具调用，但尚未取得可用于图像探测的运行配置/在线隧道；图像能力尚未资格化。离线mock测试只验证请求结构和失败记录，不表示AI视觉可运行或识别准确。
- 页面内图像文字不自动解释为设备位号、管线连接、仪表拓扑、尺寸或工程结论。CAD矢量/文字走SVG/DXF解析流程；仅有截图仍不能代替原生CAD文件。
- 历史扫描控制例曾把100 kPa误读为1o0 kPa，原始结果及纠正记录保存在旧QA证据中。它们不代表新运行使用传统OCR，也不证明当前AI模型转录能力。
- 检索为词法BM25加未覆盖原文页的关键词回退，尚无语义重排、系统综述筛选或检索召回率资格评价。支持/反驳只是录入标注，不自动判断科学矛盾。
- 原件与快照保存SHA256，可检测已记录的文件变化；这不是数字签名，也不提供对数据库所有者不可篡改的审计保证。

## 固定开放全文来源

在线导入只接受PMCID，先查询固定Europe PMC端点确认`isOpenAccess=Y`，再下载固定全文端点。拒绝任意URL、非JATS XML和实体/外部资源，不把题录或生成文字作为全文。真实网络验证脚本为`scripts/fulltext_network_smoke.py`。沙箱内Python出现ConnectError；2026-10-20在获准联网环境运行同一搜索/导入实现成功，随后获准联网的本地服务也通过真实浏览器检索、全文导入。这不代表任意部署网络或所有来源均可访问。失败时可上传合法取得的原文，并明确记录获取方式。

## 研究案例与来源归属

`scripts/literature_study.py`研究亨利常数定义、气液平衡与地下储氢传质，建立两项论断、四条引句，导出证据和报告。该案例不是全面文献综述或专家科学审核，亦未完成真实LLM对照。

- Strobel, G.; Hagemann, B.; Lüddeke, C. T.; Ganzer, L. (2023). *Coupled model for microbial growth and phase mass transfer in pressurized batch reactors in the context of underground hydrogen storage*. Frontiers in Microbiology. DOI: [10.3389/fmicb.2023.1150102](https://doi.org/10.3389/fmicb.2023.1150102)，PMCID PMC10110988，CC BY；版权及原文许可保留在XML与导出文献归属中。归档：`docs/sources/fulltext/PMC10110988.xml`，SHA256 `3731358f5378c14afe4d3512475e864a44941658f0a7750ac58d8688f56e688e`。
- International Association for the Properties of Water and Steam (2004). *Guideline on the Henry's Constant and Vapor-Liquid Distribution Constant for Gases in H2O and D2O at High Temperatures*, G7-04，9页。原文允许注明IAPWS归属后转载。归档：`docs/sources/IAPWS-G7-04-HenGuide.pdf`，SHA256 `1e258e8d68e02ec7fb207f99c8e344ee41c13b28302165b262853096eead42b5`。

两来源对亨利常数的定义、浓度基准、温度和体系不同，不把不同定义的数字直接判为冲突或拿来混用。
