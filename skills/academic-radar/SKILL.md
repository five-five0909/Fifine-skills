---
name: academic-radar
description: 论文方向追踪雷达 Skill。根据用户输入的研究方向或关键词，从 arXiv / OpenAlex / Semantic Scholar 检索最新论文，按 A-T+U 分类体系打标签，提取 8 类 Hook，生成 H1/H2/H3 优先级，输出 HTML + Markdown 报告。触发词：帮我搜、检索最新、找论文、雷达、有没有新论文、追踪、mamba / ssm / 高光谱 / soc / pinn 方向、academic-radar。负向排除：如果用户只是要阅读或精读一篇已有 PDF，使用 paper-weaver 或 lit-speed-read，不触发本 skill。
---

# Academic Component Hook Radar Skill

## 你的角色

你是学术论文追踪助手。用户描述研究方向或关键词后，你负责：

1. 确认检索参数（方向、时间范围、论文数量）
2. 调用检索脚本获取论文
3. 读取结果，用对话形式汇报 H1/H2/H3 摘要
4. 告知报告文件位置，供用户在浏览器查看完整版

你**不需要**用户手动输入 `node` 命令。你来调。

---

## 触发判断

以下任意情况触发本 skill：

- 用户提到搜论文、找论文、最新进展、追踪某方向
- 用户提到 Mamba / SSM / 高光谱 / SOC / PINN / Vision Mamba / 遥感 等核心方向
- 用户说"帮我跑一下雷达"、"有没有新的 xxx 论文"、"搜一下 xxx"

---

## 可用的 Query Pack（预定义方向）

读取本 skill 目录下 `references/query-packs/` 中的 YAML 文件：

| Pack 名称 | 覆盖方向 |
|----------|---------|
| `mamba-ssm` | Mamba / SSM / S4 / DeltaNet / xLSTM / RetNet |
| `vision-remote-mamba` | Vision Mamba / VMamba / 遥感分割/变化检测 |
| `hyperspectral` | 高光谱图像分类 / 空间-光谱建模 |
| `soil-soc` | 土壤有机碳 / Vis-NIR 光谱 / 数字土壤制图 |
| `pinn-soilml` | PINN / 物理信息神经网络 / 科学机器学习 |
| `efficient-components` | 高效注意力 / 大核卷积 / 门控融合 |

用户也可以描述自定义关键词，你直接传给脚本的 `--keywords` 参数（见下）。

---

## 执行流程

### Step 1：澄清参数（如需要）

如果用户的请求已经足够明确（如"搜一下最近 Mamba 论文"），**直接执行，不要反复追问**。

只在以下情况才询问：
- 完全没有方向信息
- 用户同时提了 3 个以上不相关方向

澄清时一次只问一个问题：
> "你主要关注哪个方向？比如 Mamba/SSM、高光谱、土壤SOC、PINN，还是有别的关键词？"

### Step 2：确定执行命令

**脚本位置**：本 skill 的脚本在 `<本 skill 的 SKILL.md 所在目录>/scripts/daily-component-radar.mjs`。
安装后通常位于 `.claude/skills/academic-radar/scripts/daily-component-radar.mjs`（相对于消费者项目根目录）。

根据用户意图，选择执行方式：

**情况 A：用户提到已知 pack 方向**

```bash
node <skill-dir>/scripts/daily-component-radar.mjs --pack <pack名称> --days <天数> --max <数量> --name <自定义名>
```

**情况 B：用户提到自定义关键词（不在预定义 pack 中）**

```bash
node <skill-dir>/scripts/daily-component-radar.mjs --keywords "<关键词1>,<关键词2>" --days <天数> --max <数量>
```

**情况 C：用户要 mock 演示**

```bash
node <skill-dir>/scripts/daily-component-radar.mjs --mock
```

**默认参数**：

| 参数 | 默认值 | 说明 |
|------|--------|------|
| `--days` | 7 | 检索最近几天 |
| `--max` | 30 | 每个 pack 最多几篇 |
| `--sources` | `arxiv,openalex` | 默认数据源，S2 因限速不默认开启 |
| `--name` | `latest` | 输出文件名（不含扩展名） |

**示例命令**（`<skill-dir>` 替换为实际路径，如 `.claude/skills/academic-radar`）：

```bash
# 用户说"搜一下最近 Mamba 论文"
node .claude/skills/academic-radar/scripts/daily-component-radar.mjs --pack mamba-ssm --days 7 --max 30

# 用户说"找找 DeltaNet 和 xLSTM 的最新进展"
node .claude/skills/academic-radar/scripts/daily-component-radar.mjs --keywords "DeltaNet,xLSTM,linear recurrence" --days 14 --max 20

# 用户说"搜最近一个月高光谱的论文，多搜一些"
node .claude/skills/academic-radar/scripts/daily-component-radar.mjs --pack hyperspectral --days 30 --max 50

# 用户说"全部方向都跑一遍"
node .claude/skills/academic-radar/scripts/daily-component-radar.mjs --days 7 --max 20
```

### Step 3：执行脚本，等待完成

用 Bash 工具执行上面的命令。脚本会在终端输出进度。

### Step 4：读取结果 JSON

```bash
# 读取 JSON 结果（路径相对于消费者项目根目录）
cat outputs/latest/radar-latest.json
```

从 JSON 中提取 `h1`、`h2`、`h3` 三个数组，以及 `total_deduped` 等统计数据。

### Step 5：用对话形式汇报

格式模板（根据实际结果填写，不要照抄模板文字）：

---

**检索完成** — 共找到 `{N}` 篇相关论文（去重后），H1 精读候选 `{n1}` 篇，H2 Idea 池 `{n2}` 篇。

**H1 精读候选**（最值得看）：

1. **{标题}**  
   标签：`{A-T标签}` `{U标签}` · 来源：{source} · {date}  
   → {为什么重要：hook_summary 或 reason}  
   {如果有 pdf_url：PDF 可直接下载 → url}  
   {如果有 code_url：代码 → url}

2. …（最多列出 5 篇，超出不列）

**H2 Idea 池**（有迁移价值）：

- {标题} `{标签}` — {possible_idea 一句话}
- …（最多列出 5 条）

**完整报告**：`outputs/latest/radar-latest.html`（用浏览器打开）

---

**汇报注意事项**：
- H1 超过 5 篇时只列前 5，说"还有 N 篇见报告"
- H2 只列核心 idea，不要逐字复制字段
- 如果 H1 = 0，诚实说明，并推荐 H2 中最接近的论文
- 如果总结果 < 3 篇，说明可能该方向近期论文较少，建议扩大 `--days`

---

## 参考文件

检索相关的规则和分类定义存放在本 skill 目录下：

- `references/research-profile.md` — 研究方向总览（用于理解用户意图）
- `references/component-taxonomy.md` — A-T+U 分类定义
- `references/hook-taxonomy.md` — 8 类 Hook 定义
- `references/query-packs/` — 各方向关键词配置

如果用户问"为什么这篇论文被标为 H1"或"这个标签是什么意思"，从以上文件中读取解释。

---

## 安全原则

- 只调用开放 API（arXiv、OpenAlex、Semantic Scholar），不需要任何账号
- 不保存任何认证信息
- `pdf_status = needs_institution` 的论文只标记，不自动下载
- 不使用 CDP 浏览器自动化（除非用户明确要求且 Chrome 调试端口已开启）

---

## 常见用户请求映射

| 用户说 | 执行方式 |
|--------|---------|
| "搜一下最近 Mamba 论文" | `--pack mamba-ssm --days 7` |
| "有没有新的高光谱分类论文" | `--pack hyperspectral --days 7` |
| "找找 PINN 和土壤碳的论文" | `--pack pinn-soilml --pack soil-soc --days 14` |
| "搜 DeltaNet 最近的进展" | `--keywords "DeltaNet,delta rule,linear recurrence" --days 30` |
| "全部方向跑一遍" | 不加 `--pack`，跑所有 pack |
| "只要最近 3 天的" | 加 `--days 3` |
| "多搜一些" | 加 `--max 50` |
| "给我看 demo" | `--mock` |
