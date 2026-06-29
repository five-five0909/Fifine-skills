---
name: paper-weaver
description: Use this skill when the user wants a structured paper-reading pipeline driven from a PDF, especially to produce staged outputs for abstract, introduction, related work, method, formulas, and experiments. Trigger: /paper-weaver, read paper, 论文阅读, structured reading, abstract introduction.
---

# pdf-paper-weaver

## Trigger check
This skill applies when the user wants a structured multi-stage reading pipeline for a research paper PDF. If the user only wants a quick summary — stop, use lit-speed-read instead.

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

## 输出目录确认

在进入主流程前，AI **必须**先询问用户输出文件存放位置：

> 生成的所有文件将存放在哪里？  
> 默认路径：**PDF 所在目录下的 `weave/` 子文件夹**  
> 例如 PDF 在 `/papers/gpt4.pdf`，则默认输出到 `/papers/weave/`  
> 如需自定义，请告知完整路径。

用户确认后，将路径作为 `--output-dir` 参数传给脚本。若用户直接回车/不填，使用默认路径。

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

内部执行时应始终调用**当前已安装 skill 目录**中的主控脚本，而不是假设仓库根目录或 Claude 全局目录：

```bash
python <当前skill目录>/scripts/run_pipeline.py --pdf <paper.pdf> --mode auto --request-text "<用户原话>" --output-dir <确认后的输出目录>
```

主控脚本在全部阶段通过后，会自动额外生成：

- `final_report.md`
- `final_report.html`

高级用法：

```bash
python <当前skill目录>/scripts/run_pipeline.py --pdf <paper.pdf> --mode first-pass --output-dir <输出目录>
python <当前skill目录>/scripts/run_pipeline.py --pdf <paper.pdf> --mode second-pass --output-dir <输出目录>
python <当前skill目录>/scripts/run_pipeline.py --pdf <paper.pdf> --mode custom --modules abstract,introduction,experiments --output-dir <输出目录>
python <当前skill目录>/scripts/run_pipeline.py --pdf <paper.pdf> --mode auto --request-text "只看实验" --output-dir <输出目录>
python <当前skill目录>/scripts/run_pipeline.py --pdf <paper.pdf> --mode auto --request-text "只看摘要和实验" --output-dir <输出目录>
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
- `final_report.html`

## 阶段说明

- `abstract`：三句话摘要（Why / How / So-what）
- `introduction`：Introduction / GAP 三段式 + GAP 表
- `related_work`：Related Work 演化脉络
- `method_overview`：Method 的人话主线总结；输出应按“问题 / 主线 / 贡献”分段，而不是一整段糊在一起
- `formula_thread`：核心公式链、符号表、概念卡；公式部分必须写成“公式主线讲解稿”，要求：
  - block formula 单独起块
  - 关键变形前后要有解释段落
  - 推导按步骤推进，避免机械填空感
  - “问题是 / 目标是 / 进一步得到 / 这一部分真正解决的是” 这类提示语，在最终 HTML 中使用偏 Notion 引用块风格的橙色背景，不使用蓝色胶囊按钮样式
  - “视角切换” 采用居中的结构化卡片块，不再依赖容易炸掉的 LaTeX `cases` 展示
  - 允许保留概念卡和总结，但主体必须更像论文精读笔记，而不是模板拼接
- `experiments`：实验主张-证据链、消融与效率判断

## 公式审查步骤（收尾阶段）

HTML 生成后，脚本自动在同目录输出 `formula_manifest.json`。
AI 必须执行以下逐条审查：

1. 读取 `formula_manifest.json`
2. 对每条 `status: pending` 的公式逐条检查 `raw` 字段：
   - HTML 实体残留（`&lt;` `&gt;` `&amp;`）→ 修改 HTML 中对应公式，status 改为 `fixed`
   - 括号 `{}` 不平衡 → status 改为 `flagged`，note 填写原因
   - `\begin` / `\end` 不配对 → status 改为 `flagged`
   - 公式内容为空 → status 改为 `flagged`
   - 无问题 → status 改为 `ok`
3. 全部审查后将更新后的 manifest 写回文件
4. 打印摘要：ok N 条 / fixed N 条 / flagged N 条

## 重要说明

- 本 skill 不再暴露旧的 5 个独立入口。
- 不允许直接对旧模块逐个单独调用作为正式入口。
- 旧逻辑已经被整合为 `pdf-paper-weaver` 内部阶段。

