# ChemELLM 本地版开发 Goal

> 状态：已写入 DSH 持久 Goal（`goal-33d58822-bb7f-4c36-9756-f2ce98d64696`，30 轮上限）。
> 用途：本文件是给人和 agent 都可读的目标基线；每轮开发前先读它和 [ACCEPTANCE.md](ACCEPTANCE.md)。

## 1. 目标定位（继承原项目目标，收敛到本地形态）

把「为化工人服务、能胜任化工工程师大部分工作」的平台目标，收敛成**本地可运行的 DSH 插件工作台**：

- **唯一形态**：`@local/dsh-chemellm`（DSH Host/Client 插件）+ 本地 Python 内核（`127.0.0.1:8765`，复用 `old/app` 的计算与文档能力）。
- **交互面**：DSH Web GUI（「化工工程」面板 + 对话内 `chem_*` 工具）；**不访问原 ChemELLM Web**。
- **不做云端**：不引入公网、备案、HTTPS、多租户、计费；`endpoint` 保留可切换能力即可。
- **归档**：`old/` 只读，不修改、不作为运行入口；数据只写 `data/` 与 `.chem/`。

## 2. 完成判据（全部满足才可标记 goal complete）

| # | 判据 | 证据形式 |
|---|---|---|
| 1 | 旧项目全部工具可在 DSH 内调用（补 `chem_tool` 透传；README 工具表一致） | 工具列表输出 + 实际调用记录 |
| 2 | 两个真实案例从空项目走完全流程并打包：(a) 赛题案例（赛题 PDF 由用户自备，未入库）；(b) 换原料/规模/装置迁移案例 | 项目状态、成果文件、zip |
| 3 | 每个案例 zip 含文件哈希清单且校验通过；成果可打开、可复核 | `manifest.json` + 复核命令输出 |
| 4 | 阶段门禁 `enforce` 真实拦截越阶段调用；自动校核与专业审核分离 | 拦截测试输出 + review 记录 |
| 5 | `scripts/smoke.py` 通过；内核 `py_compile`、插件 `node --check`、DSH 工具/槽位验证通过 | 命令输出 |
| 6 | README / QUICKSTART / GOAL / ACCEPTANCE 准确，限制与缺项如实记录 | 文档本身 |

## 3. 里程碑与建设顺序

1. **M1 工具链补全**：`chem_tool` 通用透传（覆盖 `equipment_save/query`、`drawing_read`、`dataset_inspect/analyze_dataset` 等）；工具说明与 README 对齐；重装插件并验证。
2. **M2 门禁与审核**：`phaseGate: enforce` 双端生效；越阶段测试；review 增加“计算缺校验/成果缺格式/依据无来源”等规则；人工审核记录与自动校核分离。
3. **M3 案例 A（赛题）**：从空项目在 DSH 内完成一轮尽可能完整的交付；逐项记录覆盖、缺口、失败；打包并哈希校验。
4. **M4 案例 B（迁移）**：换原料或规模（如苯/甲苯体系、不同产能）复用同一流程；记录哪些能力是通用的、哪些硬编码。
5. **M5 收尾**：文档与验收记录齐备，回归通过，标记 goal complete。

## 4. 每轮迭代规则（self-development loop）

1. 读 [ACCEPTANCE.md](ACCEPTANCE.md) 的「下一步」，选**一个最小可验证步骤**。
2. 改代码（内核 / 插件 / 脚本）——只动一个关注点，写清预期结果。
3. 跑校验：
   - 内核：`.\.venv\Scripts\python.exe -m py_compile kernel\server.py`
   - 插件：`node --check dsh-chemellm\index.js`、`node --check dsh-chemellm\client.js`
   - 链路：`.\scripts\start-kernel.cmd` + `.\.venv\Scripts\python.exe -X utf8 scripts\smoke.py`
   - DSH：改动 JS 后需重新 `install_bundle`（替换已安装包时 Host 需重启才会加载新 JS 模块，先把改动集中到一次再重启）；随后用 `cordis_inspect_query` 确认工具/槽位。
4. 更新 [ACCEPTANCE.md](ACCEPTANCE.md)：状态、证据、下一步；失败与缺项保留。
5. 同步 README / QUICKSTART 中受影响的部分。

**禁止**：伪造数据/文献/审核/软件源文件；把 `old/` 当运行入口；恢复云端；把“运行结束”记成“验收通过”。

## 5. 可复制的 Goal

```text
在 C:\Users\Lenovo\Desktop\ChemELlm 的「本地化工工程工作台」上持续自主开发，直到通过验收判据。

形态约束：唯一形态是「DSH 插件 @local/dsh-chemellm + 本地 Python 内核（127.0.0.1:8765）」，
不引入云端、公网、备案或多租户依赖；old/ 是只读归档，不修改、不作为运行入口；数据只放 data/ 与 .chem/。

开发目标：
1. 工具链完整：旧项目全部工具（22 个计算模型、证据/检索、报告与图纸生成、设备登记、图纸识读、
   数据集分析等）都能在 DSH 内经 chem_* 域工具调用（补 chem_tool 透传），README 工具表与实际一致。
2. 工程闭环：从空项目出发、只用本地内核 + DSH，完成至少 2 个真实案例——(a) 赛题案例（赛题 PDF
   由用户自备，未入库）的赛题交付；(b) 换原料/规模/装置的迁移案例。每个案例都要：要求登记→成果计划（要求零遗漏映射）→
   带单位/条件/来源的设计依据→计算（有校验或明确告警）→多格式成果（DOCX/PDF/SVG/DXF）→自动校核→
   打包 zip（含文件哈希清单与复算说明）。成果可打开、可复核，缺项与失败如实记录。
3. 门禁与审核：阶段门禁 advisory/enforce 可切换且 enforce 真实拦截越阶段调用；自动校核与专业审核
   严格分离；不伪造数据、文献、审核或软件源文件。
4. 质量与可验证：scripts/smoke.py 主链路通过；每次改动后做对应检查（内核 py_compile、node --check、
   smoke、必要时重装插件并 inspect 工具/槽位）；改动与验收结果记录到 docs/ACCEPTANCE.md。
5. 交付文档：README、docs/QUICKSTART.md、docs/GOAL.md 与验收记录保持准确，包含限制与后续事项。

完成判据（全部满足才可标记 complete）：第 1–4 项都有可复核的本地证据（命令输出、文件、验收记录）；
两个案例的最终 zip 通过 manifest 哈希校验，且 DSH 内工具调用轨迹与记录一致。未满足前继续迭代，
优先补工具与 enforce 门禁，再做案例验收，最后完善文档与回归；每轮保持一个可验证的小步，
失败保留并驱动修复。
```
