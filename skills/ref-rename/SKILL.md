---
name: ref-rename
description: Use this skill when the user wants to batch rename research PDFs from extracted metadata, especially for incremental cleanup of literature libraries with user confirmation on naming choices. Trigger: /ref-rename, rename PDF, 文献重命名, batch rename.
---

# pdf-ref-rename

> 批量重命名学术文献 PDF。脚本提取原始数据，AI 做语义判断，用户做最终决策。
> 默认增量更新：已命名文件自动跳过，只处理新增/未命名文件。

## Trigger check
This skill applies when the user wants to batch rename research PDFs using extracted metadata. If the user wants to classify PDFs into topic folders — stop, use ref-classify instead.

## 触发与输入

用户提供以下任一输入：
- **文件夹路径** → 递归扫描所有子目录（增量模式）
- **单个 PDF 路径** → 只处理一个文件

触发后**立即开始** Step 1。

## 依赖

- Python 3.7+、PyMuPDF (`pip install PyMuPDF`)
- 脚本位置：`skills/ref-rename/scripts/`

---

## Step 1 · 扫描原始数据（增量模式）

**默认使用增量模式**，跳过已按 `YYYY_Title_Author.pdf` 格式命名的文件：

```bash
python <repo_root>/skills/ref-rename/scripts/scan_refs.py "<用户路径>" --incremental -o <temp_scan.json>
```

如果需要重新扫描全部文件（如校验已有命名），加 `--all` 不加 `--incremental`。

### 增量模式判定规则

文件名同时满足以下条件视为"已命名"，自动跳过：
1. 以 4 位数字年份开头（如 `2024`）
2. 紧跟下划线 `_`
3. 包含至少 2 个下划线（`YYYY_..._...pdf`）
4. 以 `.pdf` 结尾

### 输出字段

| 字段 | 说明 |
|------|------|
| `path` | 绝对路径 |
| `rel_path` | 相对路径 |
| `filename` | 当前文件名 |
| `metadata` | PDF 内嵌元数据（原始键值对，可能为空） |
| `first_page_lines` | 首页前 20 行非空文本（原始字符串数组） |
| `error` | 仅在打开失败时出现 |

**脚本不做任何语义判断。** 所有"哪行是标题、哪行是作者"的决策由你在 Step 2 完成。

若增量模式下所有文件都已命名，脚本会输出 "All N file(s) already renamed. Nothing to do." 并退出，无需继续后续步骤。

---

## Step 2 · AI 语义解析

你需要逐个阅读每个 PDF 的 `metadata` 和 `first_page_lines`，判断：

### 2.1 识别标题

按以下优先级确定标题：
1. `metadata.title` 非空 → 直接使用
2. 否则从 `first_page_lines` 中判断：学术论文的标题通常在前 3 行，是最长的一段连续文字，位于作者行之前
3. 如果标题跨多行（如全大写短行），合并为一句
4. 若实在无法判断 → 标注"待确认"，交给用户

### 2.2 识别作者

按以下优先级确定作者：
1. `metadata.author` 非空 → 直接使用
2. 否则从 `first_page_lines` 中找：通常在标题之后、Abstract 之前，包含多个人名、逗号、"and"、上标数字等
3. 清理上标标记（`∗`、`*`、数字角标）后保留人名
4. 若无法判断 → 标注"待确认"

### 2.3 识别年份

按以下优先级确定年份：
1. `metadata.subject` 或 `metadata.creationDate` 中提取四位数年份
2. `first_page_lines` 中找年份模式（如 "2024"、"Published 2023"）
3. 若无法判断 → 标注"待确认"

### 2.4 缩写作者

用于文件名中：
- 1 位作者 → `LastName`
- 2 位作者 → `LastName1 & LastName2`
- 3 位及以上 → `FirstAuthor et al.`

### 2.5 展示结果

解析完成后，用表格展示给用户：

```
| # | 当前文件名 | 识别的标题 | 作者 | 年份 | 置信度 |
|---|-----------|-----------|------|------|--------|
| 1 | 2312.00752v2.pdf | Mamba: Linear-Time... | Gu & Dao | 2024 | 高 |
| 2 | unknown.pdf | (待确认) | (待确认) | (待确认) | 低 |
```

对于"待确认"的文件，请用户补充信息或选择跳过。

---

## Step 3 · 制定命名计划

基于 Step 2 的解析结果，向用户提供 **三种命名方案**（使用 `AskUserQuestion`）：

| 方案 | 格式 | 示例 |
|------|------|------|
| **A（推荐）** | `YYYY_Title_Author.pdf` | `2024_Mamba - Linear-Time Sequence Modeling_Gu & Dao.pdf` |
| **B** | `Author - YYYY - Title.pdf` | `Gu & Dao - 2024 - Mamba - Linear-Time Sequence Modeling.pdf` |
| **C** | `Author-YYYY-TitleShort.pdf` | `Gu_Dao-2024-Mamba.pdf` |

### 文件名校验规则（AI 在生成 new_name 时遵守）

- **Windows 非法字符**：`< > : " / \ | ? *` → 冒号替换为 ` -`，其余替换为 `-`
- **文件名上限**：200 字符（含 `.pdf`）
- **完整路径上限**：255 字符（`目录路径 + 文件名`），`do_rename.py` 会自动截断超长标题
- **标题大小写**：保留原始大小写
- **方案 C 的 TitleShort**：只取标题前 3 个有意义的词

### 路径长度约束说明

Windows 系统限制完整路径不超过 260 字符。`do_rename.py` 内置了自动截断机制：

1. 计算 `目录路径长度 + 文件名长度`
2. 若超过 255 字符，自动截断标题部分并添加 `...` 后缀
3. 截断时保留年份和作者信息完整

**AI 生成计划时无需手动截断**，`do_rename.py` 会自动处理。但如果目录路径本身就很长（>100字符），建议 AI 主动缩短标题以提高可读性。

---

## Step 4 · 确认并执行

1. 生成 JSON 计划文件（写入临时目录），格式：

```json
[
  { "old_path": "E:\\refs\\old.pdf", "new_name": "2024_Title_Author.pdf" }
]
```

2. 先运行 dry-run 预览：

```bash
python <repo_root>/skills/ref-rename/scripts/do_rename.py <plan.json> --dry-run
```

3. 展示预览，再次确认

4. 正式执行：

```bash
python <repo_root>/skills/ref-rename/scripts/do_rename.py <plan.json>
```

5. 执行后：
   - 展示结果摘要
   - 删除临时 plan.json
   - 若项目中有引用这些 PDF 的 Markdown 索引文件，**主动提醒**用户是否更新
   - 若当前目录是 `plans/PISFM_Enhance/参考文献/`，**主动提示**：
     ```
     ✅ 重命名完成。如需将文件归入 A-F 板块子目录，可接着运行 /ref-classify。
     ```

---

## 边界情况

| 情况 | 处理 |
|------|------|
| `metadata` 和 `first_page_lines` 均为空 | 标注"无法识别"，请用户手动提供 |
| 目标文件名已存在 | `do_rename.py` 自动跳过 |
| 扫描版 PDF（无文本层） | `first_page_lines` 为空，仅依赖 `metadata` |
| 文件名含中文 | 正常保留（Windows 支持 Unicode） |
| HTML 文件 | 脚本暂不扫描 HTML；如需重命名，用户手动提供信息 |
| 路径超过 260 字符 | `do_rename.py` 自动截断标题部分 |
| 重复论文（同一标题+作者） | AI 检测后提醒用户，由用户决定保留或删除 |

