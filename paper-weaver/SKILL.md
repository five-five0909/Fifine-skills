---
name: paper-weaver
description: >
  统一论文阅读 skill。唯一入口必须是主论文 PDF，由 Python 主控脚本硬编码第一遍阅读/第二遍阅读/完整阅读/自定义阅读流程；脚本会强制生成骨架、检查缺字段、阻断未完成阶段，并要求补齐后再继续。适用于对同一篇论文生成 Abstract、Introduction/GAP、Related Work、Method、核心公式、Experiments 的结构化阅读结果。触发词：帮我读这篇论文、论文阅读、精读论文、paper-weaver、论文结构化分析。
---

# paper-weaver

## 核心原则

- **唯一入口是主论文 PDF。** 没有 PDF，不进入主流程。
- **主流程必须由 `scripts/run_pipeline.py` 控制。** 不能跳步、不能手写绕过、不能缺字段直接渲染。
- **AI 只能辅助子流程。** 比如帮助从 PDF 某一部分抽变量、给字段候选值、解释某个模块；但是否进入下一步、哪些字段必须补齐、何时允许渲染，都由 Python 脚本硬编码决定。
- **缺字段时脚本必须阻断。** 脚本会生成 `missing_fields.json` 和对应阶段的 `values.json` 模板，要求补齐后再继续。

## 阅读模式

由主控脚本写死四种模式：

1. `first-pass`
   - Abstract
   - Introduction / GAP
   - Related Work

2. `second-pass`
   - Method Overview
   - Formula Thread
   - Experiments / Claim-Evidence Trace

3. `full`
   - 按固定顺序依次执行全部六个阶段

4. `custom`
   - 用户可以多选模块
   - 但模块执行顺序仍由脚本固定，不允许自由调换

## 用户入口

对用户来说，标准使用方式就是：

- `@paper-weaver <pdf路径>`
- `@paper-weaver <pdf路径> 帮我精读`
- `@paper-weaver <pdf路径> 全部生成`
- `@paper-weaver <pdf路径> 只看实验`
- `@paper-weaver <pdf路径> 只看公式`
- `@paper-weaver <pdf路径> 只看摘要和实验`

也就是说，**用户只需要艾特 skill 并给出主论文 PDF 路径，再附带一句自然语言需求即可**。  
后续模式选择、阶段排序、缺字段阻断、骨架生成，全部由脚本在内部自动处理。

### 自动路由规则

脚本不会把主流程交给 AI 判断，而是用**硬编码关键词规则**做自动路由：

- 只给 PDF，没别的要求
  - 默认走 `first-pass`
- 提到“精读 / 深读 / 方法 / 公式 / 实验”
  - 默认走 `second-pass`
- 提到“全部 / 完整 / 全面”
  - 走 `full`
- 提到“只看实验 / 只看公式 / 只看摘要 / 只看引言 / 只看相关工作 / 只看方法”
  - 走 `custom`，并自动只选对应模块
- 一句话里同时点名多个模块
  - 走 `custom`，按脚本内固定顺序执行这些模块

## 脚本入口

内部执行时始终从以下命令进入：

```bash
python paper-weaver/scripts/run_pipeline.py --pdf <paper.pdf> --mode auto --request-text "<用户原话>"
```

高级用法：

```bash
python paper-weaver/scripts/run_pipeline.py --pdf <paper.pdf> --mode first-pass
python paper-weaver/scripts/run_pipeline.py --pdf <paper.pdf> --mode second-pass
python paper-weaver/scripts/run_pipeline.py --pdf <paper.pdf> --mode custom --modules abstract,introduction,experiments
python paper-weaver/scripts/run_pipeline.py --pdf <paper.pdf> --mode auto --request-text "只看实验"
python paper-weaver/scripts/run_pipeline.py --pdf <paper.pdf> --mode auto --request-text "只看摘要和实验"
```

## 硬编码主流程

主控脚本按以下固定步骤推进：

1. 校验主论文 PDF 是否存在
2. 若是 `auto` 模式，则用硬编码关键词规则解析用户意图
3. 生成固定阶段队列
4. 为每个阶段生成 skeleton
5. 为每个阶段生成 `values.json` 模板
6. 若当前阶段缺字段：
   - 生成 `missing_fields.json`
   - 阻断主流程
   - 提示先补齐该阶段变量
7. 补齐后重新运行脚本
8. 当前阶段通过校验后才允许 render
9. 全部阶段完成后汇总成总报告

## 输出结构

工作目录下会生成：

- `manifest.json`：记录 PDF、模式、阶段与规划参数
- `stages/<stage>/skeleton.json`
- `stages/<stage>/values.json`
- `stages/<stage>/filled.json`
- `stages/<stage>/output.md`
- `stages/<stage>/missing_fields.json`（如缺字段）
- `final_report.md`

## 阶段说明

- `abstract`：三句话摘要（Why / How / So-what）
- `introduction`：Introduction / GAP 三段式 + GAP 表
- `related_work`：Related Work 演化脉络
- `method_overview`：Method 的人话主线总结
- `formula_thread`：核心公式链、符号表、概念卡
- `experiments`：实验主张-证据链、消融与效率判断

## 重要说明

- 本 skill 不再暴露旧的 5 个独立入口。
- 不允许直接对旧模块逐个单独调用作为正式入口。
- 旧逻辑已经被整合为 `paper-weaver` 内部阶段。
