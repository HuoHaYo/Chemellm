# Cantera气相研究：模型、来源与验收边界

更新：2026-10-20。集成Cantera 3.2.0，提供`cantera_equilibrium`和`cantera_reactor`。这是成熟气相后端的局部研究能力，不代表乙苯催化动力学、液固多相、全流程优化、LLM规划或Linux运行已验收。

## 允许的模型

| 集合 | 来源 | 实际范围 |
|---|---|---|
| h2o2 | Cantera 3.2.0发布文件h2o2.yaml，源于GRI-Mech氢氧子机理 | 10物种、29反应；理想气相平衡或均相闭式反应器 |
| gri30 | Cantera 3.2.0发布文件gri30.yaml，GRI-Mech 3.0 | 53物种、325反应；理想气相平衡或均相闭式反应器 |
| wgs4 | 从同一gri30文件取CO/H2O/CO2/H2四物种热力学 | 只做四物种平衡；无动力学，排除甲烷、固体碳及其他产物 |

后端按安装包绝对路径读取固定文件，避免当前工作目录中的同名YAML覆盖。请求不接受上传机理、任意路径或执行代码。wgs4不能用来判断积碳或全物种平衡；h2o2/gri30不能替代乙苯催化脱氢的可靠机理。

输入相对摩尔量统一归一化，不改变其化学意义。压力为绝对压力，温度为K，组成按机理物种名称且区分大小写。输入温度300–3000 K、压力1 kPa–2 MPa是接口限额，不是机理已获实验验证的物理适用域；还检查物种共同热力学温区。具体机理的反应速率适用性和不确定度仍需原始文献与实验资格验证。

## 约束与求解

平衡提供TP（定温定压）和HP（定焓定压），使用Cantera Gibbs minimization，rtol=1e-10、max_steps=1000。检查元素质量分数、压力、指定温度或比焓及温区；结果仅对允许的物种和相态有效。

反应器为理想气体均相闭式batch，初始体积1m³，可选定压/定容、绝热/恒温四类边界。定压使用IdealGasConstPressureReactor，定容使用IdealGasReactor；CVODES/ReactorNet的rtol=1e-10、atol=1e-18、max_steps=20000。定压体积允许变化，定容压力允许变化；绝热定压检查比焓，绝热定容检查比内能，恒温检查温度。检查各输出时刻的质量、元素、边界约束及温区。

积分时间1e-8–10 s，输出初始点和20–600个对数采样点。输出网格与自适应积分内部步长不同，采样不足可能漏掉尖峰，不能将有限时间曲线当作稳态、平衡或点火延迟证书。恒温反应器尚不报告维持温度所需热量。没有流动进出口、传热传质、催化表面、压降或设备几何模型。

每次调用在独立Python子进程运行，60秒硬超时终止子进程。Windows明确使用UTF-8输入输出。数值工具目前仍在服务进程中排队；此隔离不等于完整任务队列、实时取消或多用户资源调度。

## 来源和原生交付

每个计算保存：

- `mechanism.yaml`：本次实际模型的初态、相定义、物种热力学及允许反应；仅移除写出时自动生成的日期以稳定哈希。
- `source-h2o2.yaml`或`source-gri30.yaml`：安装分发中的原始机理文件，保留原描述、注释及引用；结果保存其文件名、发行版本和SHA256。
- `input.json`、`result.json`、`simulation.py`、`LICENSE-Cantera.txt`及说明。
- 反应器另有`trajectory.csv`、`reactor-profile.svg`和PDF。

原生ZIP可以在应用之外安装Cantera 3.2.0、NumPy和ruamel.yaml后运行`python simulation.py`。脚本验证原生/原始机理文件哈希及记录的数值检查，通过后比较最终状态与全部采样点T/P/摩尔分数，容差rel=1e-6、abs=1e-8。改变YAML注释也会使完整性检查失败。版本不符明确拒绝。

通用项目成果包保留全部文件、输入输出和源代码；若有Cantera计算，包内安装说明明确启用`.[simulation]`。`replay.py`重新执行数值工具，要求双方数值校验通过，比较全部物理输出、采样状态和原生模型哈希；文件链接、CVODES迭代统计及已通过的校验残差作为诊断保留，不要求逐位一致。

Cantera发行许可为BSD-3-Clause，副本随原生包交付。机理来源与数据引用另保留，不能将软件许可误当成所有外部数据库的再分发授权。参考入口：[Cantera 3.2](https://cantera.org/3.2/)、[官方反应器例](https://cantera.org/3.2/examples/python/reactors/reactor1.html)、[GRI-Mech](https://combustion.berkeley.edu/gri-mech/)。

## 预先登记的资格对照

协议：`CANTERA_BENCHMARK_PROTOCOL.json`，包含原始NIST WebBook来源、归档文件SHA256、Shomate系数和首次Cantera比较前写定的容差。四份HTML是具体使用数据的溯源快照，保留NIST署名与来源，不是通用WebBook镜像。

反应CO+H2O⇌CO2+H2，初始相对摩尔量1/1/0.1/0.1，101325 Pa。独立实现NIST Shomate计算Cp、反应焓、Kp及解析平衡反应进度；与Cantera的NASA关联式/平衡结果比较。

| 温度/K | NIST参考Kp | Cantera Kp | Kp相对偏差 | 反应进度绝对偏差 |
|---|---|---|---|---|
| 600 | 28.3751718 | 28.2723269 | 0.36245% | 0.00026593 |
| 1000 | 1.43846402 | 1.43535769 | 0.21595% | 0.00029482 |
| 1500 | 0.387336923 | 0.386630277 | 0.18244% | 0.00023745 |

三例满足预定筛查容差：物种Cp相对2%、反应焓500 J/mol、Kp相对3%、反应进度绝对0.0075 mol/初始CO mol。它们是两种关联式和实现的对照；NASA和NIST可能共享原始实验来源，不能描述成完全独立实验验证。

另用构造一级反应A→B、k=2 s⁻¹、相同氩质量、恒定热容及给定反应焓，对照XA=exp(-2t)和相应绝热温升。定压/定容×绝热/恒温四例通过预定摩尔分数2e-7、温度2e-4 K的绝对容差。最大摩尔分数误差约6e-10、温度误差约4.84e-8 K。A/B是数值夹具，不是真实化学机理。

全部是公开开发资格案例，不是保留集、真实LLM成绩或当前乙苯流程的物理基准。每例采用一致的数值约束检查，不以文件生成或自我评价替代独立科学验证。

## 重现命令与研究实例

先安装可选扩展：

    python -m pip install ".[simulation]"
    python scripts/cantera_benchmark.py

启动Web服务后：

    python scripts/cantera_study.py
    python scripts/check_cantera_study.py
    python scripts/cantera_browser_smoke.py

研究脚本通过实际HTTP建立五例：WGS在600/1000/1500 K的TP平衡、1000 K初态的HP平衡，以及1001 K/1 atm/H2:O2:N2=2:1:4的定压绝热反应器积分1 ms。最后一例最终温度约2665.619 K，属于该固定机理的数值预测。生成DOCX/PDF/MD/PPTX和项目包，保留四份NIST原始快照及协议。

独立解压检查脚本下载五个原生包和项目包，在服务文件目录之外运行各包自带脚本及通用复算，检查每个归档文件哈希。真实Edge脚本检查约束选择、组分表、原生ZIP下载、错误物种、反应轨迹加载、恒温定容及390px布局。Office原件能生成不代表本机已有LibreOffice保真预览。

最终运行记录见`VALIDATION.md`和`data/qa`。Linux、真实API/Ollama、实验动力学及全厂设计仍待各自验收。
