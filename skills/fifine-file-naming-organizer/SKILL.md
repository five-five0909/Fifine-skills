---
name: fifine-file-naming-organizer
description: 'Use this skill when the user creates a file or folder that should follow the 【状态标签】+YYYYMMDD+核心信息+版本号 convention, or asks to audit, tidy, unify, version-bump, or rename existing files and folders. Trigger: /fifine-file-naming-organizer, file naming, naming convention, folder structure, rename files, 整理文件, 整理文件夹, 命名规范, 文件重命名, 状态标签, 版本号, 定稿锁定. Produces compliance diagnostics, proposed target names, and an executed rename/move plan with mapping log and rollback. Not for research-PDF title renaming — use fifine-pdf-ref-rename; not for literature topic buckets — use fifine-pdf-ref-classify.'
---

# 文件与文件夹命名整理

> 公式：**【状态标签】+ YYYYMMDD + 核心信息 + 版本号**
> 完整示例：`【定稿】20260918_秋季活动-报价单_V4.docx`
> 目的：搜索友好、排序整齐、一眼看清状态。
> 分工：脚本只做确定性校验、冲突检测和落盘；**核心信息由你判断，脚本不会替你臆造**。

依赖：Python 3.7+ 标准库，无需安装任何第三方包。

## Trigger check

本 skill 只在两类需求下生效：①新建文件/文件夹需要按上述公式命名；②需要体检、统一、改名或升降级存量的文件与目录。

- 需要从 PDF 元数据识别论文标题再批量改名 → 停止，改用 `fifine-pdf-ref-rename`。
- 需要把文献按主题归入字母前缀目录 → 停止，改用 `fifine-pdf-ref-classify`。
- 与命名无关的单次移动或复制 → 停止，直接完成，不要调用本 skill。

## 命名公式（核心）

| 字段 | 规则 | 例 |
|------|------|-----|
| 状态标签 | 可选；恰好两个字 + 全角中括号，置顶；**封闭集合**：草稿 / 待审 / 待改 / 定稿 / 归档 | `【定稿】` |
| 日期 | 8 位 `YYYYMMDD`，紧跟标签（无分隔符），后接 `_` | `20260918_` |
| 核心信息 | 2~5 个关键词，`项目-内容` 结构，用 `-` 连接 | `秋季活动-报价单` |
| 版本号 | `_V主` 或 `_V主.次` | `_V4` / `_V1.1` |

分隔符契约（违反即不合规）：`_` 只出现在字段之间，核心信息内部禁用；`-` 只出现在核心信息的关键词之间；`.` 只用于扩展名和版本号小数；空格只出现在单个关键词内部（英文词之间）。

| ❌ | ✅ | 为什么 |
|----|----|--------|
| `报价.docx` | `20260910_秋季活动-报价单_V1.docx` | 无日期、单关键词，搜不到也排不齐 |
| `新建 DOCX 文档.docx` | `20261007_部门-季度会议纪要_V1.docx` | 默认名不含任何可检索信息 |
| `会议纪要最终版v3(1).docx` | `20260912_部门-会议纪要_V3.docx` | `最终版`/`v3`/`(1)` 不是内容，是版本噪声 |
| `【待定】20260910_项目-内容_V1.docx` | `【待审】20260910_项目-内容_V1.docx` | 标签必须落在封闭集合内 |
| `20260910_项目-需求-V1.2.pptx` | `20260910_项目-需求评审_V1.2.pptx` | 版本号要用 `_V` 前置下划线，不是 `-V` |

## 两种模式

- **A 新建即用（默认）**：用户只是要一个名字。直接按公式给 1~3 个候选名并说明标签取舍，**不跑脚本、不动磁盘**。
- **B 整理存量**：用户点名某个目录要体检或统一。走 Step 1–5。未经确认不得改名。

## Step 1 · 判定范围与协作模式

缺任何一项就用 AskUserQuestion 一次问齐（≤3 问），不要分多轮：

1. **整理根目录**（绝对路径）。
2. **协作模式**：`collab`（有评审、交接、多人参与）→ 文件必须带状态标签；`solo`（默认）→ 标签可省略。
3. **处理范围**：`--targets files|dirs|all`，默认 `files`。

## Step 2 · 体检（只读）

```bash
python <skill-dir>/scripts/audit_names.py "<根目录>" --mode solo --targets files \
  --depth 3 --problems-only --json /tmp/naming-audit.json
```

`<skill-dir>` 指本 SKILL.md 所在目录。脚本只读目录元数据与 mtime，绝不写盘。报告每条给出 `问题` / `线索` / `建议`：`线索` 含 mtime 日期、上级目录日期、上级目录关键词、候选关键词；`建议` 只在校验自身通过后才会给出，否则标注「线索不足，需 AI 判定」。

## Step 3 · 生成目标名与目录方案

依据线索补上核心信息——这是你的语义判断，不是脚本猜测：

- 首词写项目或归属，其余写内容；`最终版`、`副本`、`v3`、`(1)`、纯数字一律不进名字。
- 【定稿】【归档】文件保持原主名，**不得**借改名顺手改版本号。
- 需要目录骨架时：根层第一层用 `YYYYMMDD_项目`，内部结构目录用裸名（`交付物/`、`原始素材/`）。
- 单轮方案上限 50 个文件，超出先分批确认，避免一次性铺开。

## Step 4 · 确认门（强制）

先把方案摊成表，等用户确认后才可写盘：

```
| # | 现名 | 目标名 | 依据 | 风险 |
```

`风险` 列必须写明：可能的同名冲突、核心信息靠猜、跨目录移动、版本号来源。

## Step 5 · 预览与执行

```bash
python <skill-dir>/scripts/apply_naming.py /tmp/naming-plan.json --dry-run
python <skill-dir>/scripts/apply_naming.py /tmp/naming-plan.json --mapping-log /tmp/naming-map.json
```

plan 条目格式：`{"old_path", "new_name", "new_dir"(可选)}`。不给 `new_dir` 就是原地改名，给了就是移动（可同时改名）；版本号**已经写进 `new_name`**，确认表里是什么就落盘什么，脚本不会二次计算。

- 同一会话内没跑过 `--dry-run`，不得正式执行。
- dry-run 出现 `CONFLICT` / `LOCKED-REFUSE` / `INVALID_NAME` 时先改方案；脚本没有 `--force`。
- 执行后保留映射日志并把回滚命令交给用户；临时 plan 与 audit JSON 可删。

## 文件夹命名规则

- 根层第一层：`YYYYMMDD_项目` —— 日期在这里才必填，排序靠它。
- 第二层起：裸名 `交付物/`、`需求文档/`、`原始素材/`，不带日期。
- 目录一律**不带** `【】`、**不带** `_V`。

## 版本与定稿锁定

| 变更类型 | 判据 | 动作 |
|---|---|---|
| 大改动 | 结构重编、方案更换、章节增删、结论反转 | 主版本 +1：`V1 → V2` |
| 小改动 | 文字调整、格式微调、错别字 | 次版本 +0.1：`V1 → V1.1 → V1.2` |
| 定稿后 | 标签为【定稿】 | **锁定**：禁止在原件上改；另存 `【待改】<今天>_同一核心信息_V(n+1).<ext>` |

`apply_naming.py` 对改动【定稿】/【归档】文件主名的请求返回 `LOCKED-REFUSE`；同名纯目录移动仍放行。

## 冲突与跳过规则

| 情况 | 处理 |
|---|---|
| 目标名已被占用 | `CONFLICT`，**绝不自动加后缀**；回 Step 3 调整核心信息 |
| A↔B 互换名字 | 脚本经 `.naming-tmp*` 两阶段自动完成，日志标出中转步 |
| 仅大小写不同的重名 | 视为冲突（Windows 不区分大小写） |
| 名称已合规 | `SKIP-SAME`，重复执行不再改动 |
| 含 `< > : " / \ | ? *` | `INVALID_NAME`，必须替换 |
| `CON` / `NUL` / `COM1` 等 | `INVALID_NAME`，Windows 保留设备名 |
| 中文名过长 | 单段 ≤200 字节、主名 ≤100 字符、完整路径 ≤240 字符 |

## 边界情况

| 情况 | 处理 |
|---|---|
| 图片、压缩包、音视频 | 要日期 + 核心信息；`_V` 只给手工编辑的产物 |
| 源码、工程文件、受 Git 管理的目录 | 不加 `_V`、不加标签——版本由 VCS 管；建议排除在整理范围外 |
| 无扩展名文件 | 保留原样，仅在报告里提示确认 |
| `.tar.gz` 等复合后缀 | 整体保留，不当成两个扩展名 |
| 同步盘（OneDrive/Dropbox/坚果云） | `【】` 合法但个别同步工具有兼容问题，先整理 1~2 个文件验证再批量跑 |
| 日期无法确定 | 用文件 mtime 或上级目录日期作候选，并在 `依据` 列写明来源 |
| 用户只要求「给个名字」 | 停在模式 A，不要调用脚本 |

## Final response

报告以下要点，不要只说「整理完成」：

- 根目录、模式、`--targets` 范围；
- 体检计数：合规 / 不合规 / 锁定；
- 执行计数：改动 / 冲突 / 拒绝，以及新建的目录骨架；
- 映射日志路径与可直接复制的回滚命令；
- 仍需用户决定的文件名（脚本标为「线索不足」那几条）。

## 参考文件（按需读，禁止开头全量加载）

| 需要什么 | 读哪个 |
|---|---|
| 完整正则、字符集、合规判据矩阵 | `references/naming-grammar.md` |
| Windows/macOS/Linux 与同步盘禁忌、长度预算、NFC | `references/platform-safety.md` |
| 目录骨架三层结构与日期适用范围 | `references/folder-structure.md` |
| 版本号升降级决策与定稿锁定流程 | `references/version-workflow.md` |
