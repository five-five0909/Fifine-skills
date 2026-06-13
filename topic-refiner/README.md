# Topic Refiner Skill

把宽泛的研究方向或已有成果，转化为一个有问号、有谜题、可回答的研究问题。

方法论来源：《写作是门手艺》第7章（刘军强）

---

## 四种使用场景

| 模式 | 场景 | 触发词 |
|------|------|--------|
| **A 新选题引导** | 从零找研究问题 | "帮我选题"、"题目太大" |
| **B 论文叙事重构** | 有结果但叙事弱 | "帮我优化引言"、"像方法介绍" |
| **C 引言诊断** | 写了引言想检查 | "帮我看看引言"、"contribution对吗" |
| **D 谜题发现** | 发现奇怪实验现象 | "这个现象奇怪"、"出乎意料" |

---

## 核心方法论

**三类问题**：议题（太大）→ 难题（缺问号）→ 疑问（✅合格）

**三步提问法**：
1. 我要研究（宽泛议题）
2. 为什么有的……，有的……却……？+ 什么因素 + 作用机制
3. 回答上述疑问有助于帮助……解决……

**沙漏收口（四维度）**：Who × When × Where × What → 可驾驭的问题

**谜题测试**：说出来，别人反应是"为什么？"还是"哦"？

**核心价值观**：片面而深刻 > 全面而肤浅

---

## 命令行工具

```bash
# 交互式引导（Mode A）
python topic_refiner.py --interactive

# 快速生成示例框架
python topic_refiner.py --domain 深度学习 --subdomain 大语言模型

# 输出 JSON 格式
python topic_refiner.py --domain 深度学习 --output json
```

---

## 文件结构

```
topic-refiner/
├── SKILL.md                     # AI 行为指南（核心）
├── README.md                    # 本文件
├── topic_refiner.py             # 命令行工具
├── config.yaml                  # 多领域示例库
├── requirements.txt             # Python依赖
├── templates/
│   ├── three_step.md            # 三步提问法填空模板
│   ├── funnel_worksheet.md      # 沙漏收口工作表
│   ├── topic_card.md            # 选题卡片（Mode A）
│   └── paper_narrative.md       # 论文叙事重构模板（Mode B）
└── examples/
    ├── social_science.md        # 社会科学示例
    ├── natural_science.md       # 自然科学示例
    └── engineering.md           # 工程/技术研究示例
```

---

## 扩展领域配置

编辑 `config.yaml` 添加新的研究领域：

```yaml
domains:
  你的领域:
    description: 领域描述
    subdomains:
      - 子领域1
    examples:
      - subdomain: 子领域1
        step1: 宽泛议题
        step2_why: 为什么有的...有的却...
        step2_what: 影响因素
        step2_how: 作用机制
        step3: 价值关联
        who: 研究对象
        when: 时间范围
        where: 场景
        what: 问题切面
        question: 最终研究问题
```
