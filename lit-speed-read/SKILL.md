---
name: lit-speed-read
description: >
  学术文献速读/精读引导工具。给 Claude 一篇论文（URL、PDF路径、HTML路径），
  Claude 自动读取、分析摘要、提炼核心、生成定制思考问题，最终输出学术风格 HTML 阅读报告。
  触发词：帮我读这篇论文、文献速读、精读这篇、分析摘要、/lit-speed-read。
---

# lit-speed-read

## 触发与输入

用户提供论文来源（三种形式之一）：
- URL（网页/DOI/preprint）
- 本地文件路径（.pdf / .html）
- 直接粘贴 Abstract 文本

触发后**立即**开始，不要先问一堆问题。

---

## 执行流程

### Step 0 · 读取论文

| 来源类型 | Claude 使用的工具 |
|---------|----------------|
| URL | WebFetch |
| 本地 PDF | Read（Claude 原生支持 PDF 阅读） |
| 本地 HTML | Read |
| 纯文本 Abstract | 直接使用 |

读取后，在内部定位并提取：
- 标题（Title）
- 作者（Authors）
- 期刊/会议（Venue）
- 发表年份（Year）
- Abstract 全文
- Introduction 最后一段（用于补充动机语境）
- Conclusion 最后一段（用于补充结论语境）

若无法自动提取某项，向用户询问该项，其他不问。

---

### Step 1 · 询问两个问题（合并成一次提问）

```
请确认两件事：
1. 阅读模式：速读（Fast）还是精读（Deep）？
   Fast — Abstract 解析 + 4问 + 5题思考问题
   Deep — 以上 + 变量梳理 + 关键数字 + 7题思考问题
2. 这篇与你自己研究的关系：继承 / 修正 / 挑战？
```

同时，Claude 自动根据论文内容判断领域（不问用户），从 config.json 匹配最近的领域，仅用于内部生成提示，不出现在 HTML 中。

---

### Step 2 · Abstract 逐句解析（Claude 独立完成）

将 Abstract 按英文句子分割（以 `.`/`!`/`?` + 空格 + 大写字母为边界）。

对每一句，Claude **独立完成**：
1. **中文译文**：直译，保留学术表述
2. **语境补充**：结合 Introduction 末段和 Conclusion，说明这句话背后的含义、前提假设、或需要注意的地方。若无特别补充，留空（HTML 中不生成对应行）。

**全部由 Claude 完成，不向用户逐句提问。**

---

### Step 3 · 核心4问（Claude 独立完成）

| 问题 | Claude 的分析依据 |
|------|----------------|
| 动机/研究空白 | Introduction 中 gap 表述 + 对比前人工作 |
| 研究对象 | 数据集、样本、场景描述 |
| 核心做法 | Method/Approach 核心逻辑，一句话，去掉专业词 |
| 结论方向 | Abstract + Conclusion 中的主要结果，带数字 |

---

### Step 3.5 · 局限性分析（Claude 独立完成）

从论文 Limitations / Discussion / Conclusion 部分提取：
1. **作者承认的局限性**：直接从文本提取，逐条列出
2. **Claude 发现的潜在问题**：结合律师辩护思维，标出作者未提及但明显存在的方法或结论漏洞（最多2条，需有依据）

同时提取：
- **理论框架**：论文显式引用或隐式依赖的理论视角（一句话）

这些内容写入 JSON 的 `limitations`、`theory_framework` 字段。

同时，若 Claude 在阅读过程中联想到关联文献，可将其记录在 `related_papers` 字段（字符串，可留空）。

---

### Step 4 · [仅 Deep 模式] 精读分析（Claude 独立完成）

**变量梳理**
- 自变量（可多个）
- 因变量
- 关系方向（正相关/负相关/非线性）

**关键数字**
从 Abstract + Results 中提取所有量化指标，格式：`指标名=值`。

**研究方法**
从 Method 部分提取方法类型。

---

### Step 5 · 文献定位（询问用户）

只询问 Claude 判断不了的：
```
还有两个问题：
1. 引用用途（可多选）：方法参照 / 观点支撑 / 概念来源 / 对比案例
2. 拟放入哪个章节？（可留空）
```

文献类型由 Claude 自动判断（理论/方法/背景/原创/衍生）。

---

### Step 6 · 生成思考问题（Claude 独立完成）

从 question_bank.json 中选题，用论文具体内容填充 `{{}}` 占位符（不截断，用真实内容替换）。

Fast 模式选5题：boundary、missing_var、causal、my_research、research_space
Deep 模式选7题：以上5题 + overreach、method_weak

思考问题必须结合论文具体内容，不能是通用套话。

---

### Step 6.5 · [仅 Fast 模式] 精读建议

基于以上分析，Claude 给出一句话建议，格式：

- **值得精读**：说明最值得深入的1个理由
- **选读**（只读 Method 或 Results）：说明哪个部分最有价值
- **跳过**：说明为什么与研究目标不相关

建议写入 JSON 的 `deep_read_suggestion` 字段。

---

### Step 7 · 调用 workflow.py 生成 HTML

Claude 将所有分析结果整理为 JSON，写入临时文件，然后调用：

```bash
python C:/Users/Administrator/.claude/skills/lit-speed-read/workflow.py \
  --data-file <临时JSON路径> \
  --output-dir <用户当前工作目录或指定目录>
```

workflow.py 生成 HTML 文件，文件名规则：`{作者姓}-{年份}-{标题前6词}.html`

完成后向用户报告 HTML 文件路径。

---

## 方法论来源

- 《做研究是有趣的》（刀熊）— 构造性阅读、挑战式阅读、律师辩护思维
- 《写作是门手艺》（刘军强）— 论证谬误、文献分类、为用而引
