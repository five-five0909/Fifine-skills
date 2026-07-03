# 8 类 Hook 体系

每类 Hook 是一个从论文中提炼研究价值的维度。每篇论文可命中多类 Hook。

---

## Hook 1 — 问题 Hook

**核心问题**：别人定义的问题能不能转成我的问题？

**提取目标**：
- 论文解决什么核心问题
- 这个问题能否重新表述为土壤/高光谱/遥感领域的问题
- 输出新的研究问题表述

**触发信号**：
- 标题含"challenge"、"limitation"、"problem"、"gap"
- 摘要提出某类数据/场景的不足

**写作位置**：Introduction / Motivation

---

## Hook 2 — 方法 Hook

**核心问题**：别人的方法能不能改造我的模型？

**提取目标**：
- 替换模块：用这篇论文的组件替换自己模型中的对应组件
- 组合模块：把这篇论文的组件叠加进自己的 pipeline
- Baseline：把这篇方法作为竞争基线
- 未来变体：把这个思路列为 Future Work

**触发信号**：
- tags 含 D/E/G/I（模型组件类）
- 标题含"module"、"block"、"layer"、"operator"

**写作位置**：Method / Related Work

---

## Hook 3 — 变量 Hook

**核心问题**：某个参数、尺度、控制量能不能变成我的可学习变量？

**提取目标**：
- 论文中某个超参数可以变成可学习变量
- 某个手动设定的先验可以替换为数据驱动
- 输出可验证假设

**触发信号**：
- 论文引入新的可控参数或自适应机制
- tags 含 E/F/M（门控/选择/优化类）

**写作位置**：Method（Ablation Study 中验证）

---

## Hook 4 — 实验 Hook

**核心问题**：别人的实验能不能借到我的论文？

**提取目标**：
- 消融实验：可以迁移的消融设计
- 鲁棒性实验：可以复用的压力测试
- 效率实验：计算/内存对比实验
- 可解释性实验：可视化分析方法

**触发信号**：
- 论文有详细消融表
- tags 含 L/O/P（指标/可解释/可信类）

**写作位置**：Experiments / Ablation Study

---

## Hook 5 — 解释 Hook

**核心问题**：这篇论文能不能解释我自己实验中观察到的现象？

**提取目标**：
- 论文提供的理论解释能否对应我的实验结果
- 可以引用来支撑自己的 Discussion
- 输出 Discussion 段落草稿

**触发信号**：
- 论文有理论分析或可视化解释
- tags 含 R/O（理论/可解释类）

**写作位置**：Discussion / Analysis

---

## Hook 6 — 反例 Hook

**核心问题**：这篇论文会不会挑战我的假设？

**提取目标**：
- 作为公平 Baseline 防御审稿人质疑
- 发现自己方法可能失效的场景
- 输出风险提醒和防御实验

**触发信号**：
- 标题含"foundation model"、"pretrained"、"universal"、"zero-shot"
- 论文提出与自己方法相似但更简单的方案

**写作位置**：Experiments（对比实验） / Limitation

---

## Hook 7 — 失败 Hook

**核心问题**：这篇论文暴露了什么边界或局限？

**提取目标**：
- 论文自己承认的 Limitation
- 可以放进自己的 Limitation / Future Work 章节
- 提示方向的边界条件

**触发信号**：
- 论文有 Limitation 章节
- 标题含"challenge"、"difficulty"、"failure"
- 论文在特定场景表现下降

**写作位置**：Limitation / Future Work

---

## Hook 8 — 写作 Hook

**核心问题**：这篇论文能放进我论文哪个部分？

**提取目标**：
- Introduction 中可用的动机引用
- Related Work 中可归入的子类别
- Method 中可参考的公式表达方式
- Experiment 中可借鉴的分析框架
- Discussion 中可引用的讨论视角
- Limitation 中可援引的边界案例

**触发信号**：所有相关论文均需评估写作位置

**写作位置**：全文各章节
