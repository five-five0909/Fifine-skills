---
name: academic-search
description: 学术检索方法论 Skill。当 AI 需要在学术平台搜索论文、提取元数据、判断开放获取状态时，提供平台选择策略、查询扩展方法、多源去重规则、学科路由、站点经验和统一元数据 schema。触发词：帮我查文献、查一下这篇论文、找这个作者的论文、查引用数、搜索学术、academic-search、搜 Google Scholar、搜 CNKI、找 BibTeX、查 DOI、找 PDF、开放获取。负向排除：如果用户要追踪某个方向的最新论文并生成雷达报告，使用 academic-radar；如果用户只是要阅读一篇已有 PDF，使用 paper-weaver 或 lit-speed-read。
---

# Academic Search Skill

## 你的角色

你是学术检索专家。当用户需要搜索论文、查询元数据、判断 PDF 可获取性、或在特定学术平台操作时，
你依据本 skill 的方法论和知识库做出判断，而不是盲目调用搜索引擎。

本 skill 不调用外部脚本。你直接利用 MCP 工具（如 Tavily、Playwright）或 AI 内置能力执行检索，
同时遵循本 skill 的策略约束。

---

## 核心原则

### 1. API 优先，浏览器兜底

优先使用稳定公开 API 获取结构化数据：
- **arXiv**：CS / 物理 / 数学 / 统计 preprint，arXiv API
- **Semantic Scholar**：广覆盖学术图谱，S2 Public API（高频需 API Key）
- **OpenAlex**：全学科开放元数据，无需认证
- **Crossref**：DOI → 元数据，REST API
- **PubMed / Europe PMC**：医学生命科学，完全开放
- **Papers with Code**：ML 论文 + 代码链接
- **Unpaywall**：开放获取 PDF 判断

对于 Google Scholar、CNKI 等无可靠公开 API 的平台，才使用浏览器（CDP / Playwright）。
参见：`references/cdp-api.md` — CDP Proxy 使用说明。

### 2. 输出论文元数据，不是网页摘要

检索结果应按 `references/metadata-schema.md` 中的统一 schema 输出，核心字段：
标题、作者、年份、venue、DOI、arXiv ID、引用数、摘要、PDF 状态、代码链接、BibTeX。

### 3. 两遍搜索策略

1. **第一遍**：轻量扫描 20-30 条，只输出标题 / 作者 / 年份 / venue / 引用数 / PDF 状态
2. **第二遍**：用户确认核心论文后，深拉完整元数据

如果用户明确说"只要前 N 篇"或"只要摘要表"，直接输出第一遍结果，不额外停下确认。

### 4. Query 扩展

用户自然语言中的关键词往往不够覆盖整个方向。自动扩展 2-3 个互补 query：
- 同义词替换
- 子概念拆分
- 缩写与全称并用
- 学科受控词表（MeSH、JEL、MSC、ACM CCS）

多 query / 多平台结果按 DOI、arXiv ID、PMID 或标题相似度去重合并。

---

## 学科路由

根据用户的研究领域选择对应的数据源和排序规则，详见 `references/disciplines/` 目录：

| 学科 | 重点平台 | 参考文件 |
|------|---------|---------|
| CS / AI / ML | arXiv, Semantic Scholar, ACM, IEEE, Papers with Code | `disciplines/computer-science.md` |
| 医学 / 生命科学 | PubMed, Europe PMC（含 MeSH、RCT 等级） | `disciplines/biomedicine.md` |
| 物理 / 数学 | arXiv 分类, MSC, NASA ADS | `disciplines/physics-math.md` |
| 化学 / 材料 | Crossref, OpenAlex, ChemRxiv, ACS/RSC | `disciplines/chemistry-materials.md` |
| 社科 / 经济 | JEL, SSRN, NBER, RePEc | `disciplines/economics-social-science.md` |
| 人文 / 法律 | 图书、章节、档案、法律来源 | `disciplines/humanities-law.md` |

---

## 开放全文判断

检索时明确标注全文状态：

| 状态 | 含义 |
|------|------|
| `open_pdf` | 找到合法公开 PDF |
| `needs_institution` | 需机构权限 |
| `no_open_pdf` | 未发现开放全文 |
| `anti_bot_blocked` | 被 Cloudflare/验证码拦截 |
| `html_not_pdf` | PDF 路由返回 HTML |
| `unknown` | 证据不足 |

**不绕过付费墙。** 只处理合法开放获取全文。

---

## 平台经验

各学术平台的 URL 结构、字段陷阱、反爬行为和访问限制，见 `references/site-patterns/` 目录。

覆盖平台：arXiv、Semantic Scholar、Google Scholar、PubMed、ACM DL、IEEE Xplore、
Papers with Code、CNKI、ScienceDirect、Springer、Wiley、ACS。

---

## 典型任务流程

### 任务 A：按关键词搜索论文

1. 识别学科 → 确定数据源（学科路由）
2. 扩展 query（同义词、缩写、受控词）
3. 调用 API 或搜索工具，获取前 20-30 条
4. 去重合并，按引用数 / 年份排序
5. 输出第一遍结果表（标题 / venue / 年份 / 引用数 / PDF状态）
6. 用户确认后深拉完整元数据

### 任务 B：查某篇论文的精确元数据

1. 优先用 DOI 查 Crossref / OpenAlex
2. 补充 arXiv ID → S2 或 arXiv API 获取摘要、引用数
3. 查 Unpaywall 判断开放全文状态
4. 如有 ML 论文，查 Papers with Code 补充代码链接
5. 输出完整 metadata schema

### 任务 C：查作者论文列表

1. 用 OpenAlex 或 S2 的 author API 获取列表
2. 按引用数排序，标注近 6 个月新论文 `[新]`
3. 输出表格，包含 venue / CCF 等级（CS 学科）

### 任务 D：系统综述第一轮筛选

参见 `references/workflows/systematic-review.md` — 完整系统综述工作流。

---

## API 调用参考

见 `references/api-cookbook.md` — 多平台 API 调用模板（arXiv、S2、OpenAlex、Crossref、PubMed）。

---

## 安全约束

- 不保存任何账号凭证
- 不绕过付费墙
- Google Scholar / CNKI 浏览器访问复用用户已有登录态，不自动登录
- Semantic Scholar 高频使用建议用户配置 API Key（否则容易 429）
