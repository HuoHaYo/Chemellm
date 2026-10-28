# HAZOP / LOPA 工作表（`hazop_lopa`）

> 定位：把 HAZOP/LOPA 的**结构化工作表**生成自动化；它不是 HAZOP 会议，也不替代风险评审与签署。

## 输入

```json
{
  "project": "案例A · 2026赛题 · 苯乙烯清洁生产",
  "unit": "乙苯脱氢与分离单元",
  "nodes": [
    {
      "id": "N1", "name": "脱氢反应器", "intent": "乙苯脱氢生成苯乙烯",
      "tags": ["R-101"], "parameters": ["温度", "压力", "流量"],
      "deviations": [
        {"guide_word": "高", "parameter": "温度",
         "causes": ["TIC-101 失效", "蒸汽中断"],
         "consequences": ["超温、催化剂结焦"],
         "safeguards": ["TIC-101 联锁"],
         "recommendations": ["增设独立高温联锁（SIL 评估）"],
         "severity": 4, "likelihood": 3}
      ]
    }
  ],
  "lopa": [
    {"id": "L-01", "node": "N1", "scenario": "R-101 超压",
     "initiating_event": "冷却失效", "frequency_per_year": 0.1,
     "severity": "major", "target_frequency_per_year": 1e-5,
     "ipls": [
       {"name": "BPCS 压力控制", "pfd": 0.1, "independent": true},
       {"name": "PSV", "pfd": 0.01, "independent": true}
     ]}
  ]
}
```

- 引导词：无 / 高 / 低 / 反向 / 异常 / 过量
- 参数：压力 / 温度 / 流量 / 液位 / 组成
- 若节点未给 `deviations`，工具生成**偏差矩阵骨架行**并标注“骨架行”，不会编造原因/后果。
- 风险等级 = 严重度 × 可能性：1–3 低、4–8 中、9–14 高、≥15 极高（示例矩阵，需企业标准确认）。

## LOPA 计算

- 缓解后频率 `f_mit = f_init × Π PFD_i`（仅计入 `independent: true` 的保护层）；
- 所需风险降低因子 `RRF = f_init / f_target`；
- SIL 初判：RRF <10 无、10–100 SIL1、100–1000 SIL2、1000–10000 SIL3、≥10000 SIL4；
- 目标频率：按严重度示例值（轻微 1e-4、较大 1e-5、重大 1e-6、灾难 1e-7 /a），或由用户给定；
- 结论：`f_mit ≤ f_target` 为满足；否则提示增加保护层。

## 输出

- `HAZOP_LOPA工作表.xlsx`：节点清单 / HAZOP工作表 / LOPA表 / 说明；
- `HAZOP_LOPA工作表.docx`：同内容 Word 版；
- `HAZOP_LOPA数据.json`：完整输入 + 计算过程，便于复算。

## 诚实边界

- HAZOP 是会议驱动方法：本工具只生成工作表与骨架，不替代会议、记录与签署；
- 初始频率、PFD、目标频率、严重度需企业风险标准（如 IEC 61882、企业 LOPA 导则）与项目数据确认；
- SIL 为“所需 RRF 初判”，**未做 SIL 验证**（PFD 计算、架构约束、共因失效、诊断覆盖率）；
- 未提供的偏差原因/后果保持“待分析”，不得据此关闭建议措施。
