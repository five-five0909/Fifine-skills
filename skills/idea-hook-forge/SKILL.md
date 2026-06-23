---
name: idea-hook-forge
description: Use this skill when the user wants to decompose a research paper PDF into structured components, extract hooks, and generate idea, experiment, and writing artifacts with an HTML report as the main output.
---

# idea-hook-forge

## 核心原则
- **唯一入口是主论文 PDF。** 没有 PDF，不进入主流程。
- **主流程必须由 `scripts/run_pipeline.py` 控制。** 不允许跳步、不允许临时删阶段。
- **分析框架由代码硬编码，不由 AI 自由决定。** AI 只负责把 PDF 内容填入固定字段。
- **最终主产物是 HTML。** Markdown / JSON 是中间产物或辅助产物。
- **公式必须原文保真。** 公式本体要和论文一致；解释、注释、符号说明可以额外补充，但不能篡改公式。
- **引用统一使用 reference_key 命名规则：** `{year}_{title}_{authors}`。

## 输出目录确认

在进入主流程前，AI **必须**先询问用户输出文件存放位置：

> 生成的所有文件将存放在哪里？  
> 默认路径：**PDF 所在目录下的 `idea/` 子文件夹**  
> 例如 PDF 在 `/papers/gpt4.pdf`，则默认输出到 `/papers/idea/`  
> 如需自定义，请告知完整路径。

用户确认后，将路径作为 `--output-dir` 参数传给脚本。若用户直接回车/不填，使用默认路径。

## 用户入口
- `@idea-hook-forge <pdf路径>`
- `@idea-hook-forge <pdf路径> 全流程`
- `@idea-hook-forge <pdf路径> 只提取 hook`
- `@idea-hook-forge <pdf路径> 只做分类`
- `@idea-hook-forge <pdf路径> 生成 HTML 报告`

## 模式
1. `scan`
   - Paper Profile
   - K-T 分类
   - A-J 组件拆解
   - U 标签初筛
   - 关键 Hook 初筛
2. `hook-pass`
   - K-T / A-J / U
   - 8 类 Hook
   - 卡片系统
   - 反向调用映射
3. `full`
   - 全部阶段完整执行
4. `custom`
   - 用户点选阶段，但执行顺序仍由脚本固定

## 硬编码阶段
1. `paper_profile`
2. `kt_classification`
3. `aj_component_breakdown`
4. `u_formula_tags`
5. `hook_extraction`
6. `cards_generation`
7. `reverse_call_map`
8. `quality_gate`
9. `html_render`

## 脚本入口
```bash
python <当前skill目录>/scripts/run_pipeline.py --pdf <paper.pdf> --mode auto --request-text "<用户原话>" --output-dir <确认后的输出目录>
```

## 输出结构
```text
manifest.json
source_snapshot.json
stages/
  01_paper_profile/
  02_kt_classification/
  03_aj_component_breakdown/
  04_u_formula_tags/
  05_hook_extraction/
  06_cards_generation/
  07_reverse_call_map/
  08_quality_gate/
final_report.html
final_report.md
```

## 公式要求
- block formula 单独渲染
- inline formula 与正文分离清晰
- 公式本体按论文原文保留
- 允许添加：符号表、中文解释、作用说明、组件映射、U 标签说明
- HTML 中使用 MathJax 渲染公式

## 引用命名规则
统一生成：
`2010_Using data mining to model and interpret soil diffuse reflectance spectra_Viscarra Rossel & Behrens`

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
- 这个 skill 的目标不是生成传统 Abstract/Introduction/Related Work 精读报告。
- 它的目标是把论文变成 **组件接口 + Hook 接口 + Idea 接口 + 写作接口**。
- 如果用户只想做传统论文分章阅读，应该走 `pdf-paper-weaver`。

