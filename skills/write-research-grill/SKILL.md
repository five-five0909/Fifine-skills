---
name: write-research-grill
description: Use this skill when the user is preparing to write a paper, proposal, report, or argument and needs a structured pre-writing interrogation before drafting. Trigger: /write-research-grill, 写稿审问, pre-writing, paper draft, 写作前.
---

# Write Research Grill

## Trigger check
This skill applies when the user is about to write a paper, report, or argument and needs structured interrogation to clarify the claim and structure before drafting. If the user wants to start writing immediately — stop, this skill is a pre-writing step.

## 核心流程

1. 运行 `python scripts/grill.py`，脚本会问用户一系列问题并收集回答
2. 脚本输出一份结构化审问报告（markdown）
3. 读取报告，根据用户的回答给出判断、评分和下一步动作

## 什么时候用什么脚本

| 用户状态 | 脚本 | 说明 |
|---|---|---|
| "我要写 X"，还没想清楚 | `grill.py --mode topic` | 选题审问 |
| "我有想法但不知道材料够不够" | `grill.py --mode material` | 素材审计 |
| "我大致知道写什么但结构不清楚" | `grill.py --mode structure` | 结构预审 |
| "我有观点但论证弱" | `grill.py --mode argument` | 论证压力测试 |
| "帮我全面审一遍" | `grill.py --mode full` | 综合审问 |
| "我有草稿了帮我检查" | `audit.py` | 草稿逐部分审计 |

## 脚本输出后你该做什么

1. 读取脚本生成的报告
2. 对用户的每个回答判断：答得好 / 答得烂 / 没回答
3. 对答得烂的追问，对没回答的标记风险
4. 给出 0-5 分评分（参考下方评分标准速查）
5. 分配写前冲刺：今天做什么、本周做什么、下次带回什么

## 评分标准速查

| 分数 | 含义 |
|---:|---|
| 0 | 缺失 |
| 1 | 模糊，只有关键词 |
| 2 | 部分清楚，不能指导写作 |
| 3 | 可用，够写有风险的初稿 |
| 4 | 强，可以给导师审 |
| 5 | 定稿级别 |

## 输出格式

```markdown
## 写前状态快照
| 维度 | 状态 | 证据/缺口 |
|---|---|---|

## 审问结果
[基于脚本输出，逐项判断]

## 评分
| 维度 | 分数/5 | 原因 | 下一步 |
|---|---:|---|---|

## 写前冲刺
- 今天：...
- 本周：...
- 下次带回：...
```

