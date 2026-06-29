---
name: tavily-search
description: Use this skill when the user asks for current information, recent updates, documentation lookup, or fact verification, especially when a live web search is required instead of relying on stale model memory. Trigger: /tavily-search, search web, 联网搜索, current info, live search.
---

# Tavily Search Skill

## Trigger check
This skill applies when the user needs current, real-time information from the web that the model's training data cannot reliably provide. If the question can be answered from the existing codebase or static knowledge — stop, this skill doesn't apply.

## 核心原则

**遇到搜索需求，立刻调用工具，不要用记忆回答。**

## 工作流程

### 第一步：理解搜索意图

根据用户的问题，判断搜索策略：

| 意图类型     | 策略                              |
| ------------ | --------------------------------- |
| 单一明确问题 | 1 次搜索，精准关键词              |
| 技术调研     | 2-3 次搜索，从宽到窄              |
| 多方对比     | 每个对象各搜 1 次                 |
| 最新动态     | 关键词加年份（如 `2025`、`2026`） |

### 第二步：构造查询关键词

- **优先英文**：技术类问题英文结果质量更高
- **简短精准**：3-6 个关键词，避免长句
- **带时间**：需要最新信息时加 `2025` 或 `2026`
- **加限定词**：如 `tutorial`、`official`、`github`、`documentation`

**示例：**
```
用户：帮我搜一下 Claude Code 怎么配置 MCP
查询：Claude Code MCP configuration 2025

用户：最新的 PyTorch 版本是什么
查询：PyTorch latest version 2026

用户：BiMamba 论文
查询：BiMamba architecture paper arxiv
```

### 第三步：执行搜索

直接调用 `tavily-search`，无需询问用户确认。

```
tavily-search(query="你的查询关键词")
```

### 第四步：处理结果

搜索完成后：

1. **提炼核心信息**：不要原样罗列结果，用自己的话总结
2. **标注来源**：重要信息注明来自哪个网站
3. **判断是否需要追加搜索**：
   - 结果不够具体 → 换更精准的关键词再搜一次
   - 需要详细内容 → 用 `tavily-extract` 抓取具体页面
4. **给出结论**：直接回答用户的问题

### 第五步：追加搜索（按需）

如果第一次搜索结果不满意：

```
# 换角度
tavily-search(query="更具体的关键词")

# 抓取某个页面详情（如果需要）
tavily-extract(urls=["https://具体页面URL"])
```

---

## 常见场景示例

### 技术文档查询
```
用户：帮我找 mamba-ssm 的安装文档
→ tavily-search("mamba-ssm installation documentation github")
→ 如需要，tavily-extract 对应 README 页面
```

### 最新资讯
```
用户：搜一下 IEEE TGRS 2025 的投稿截止日期
→ tavily-search("IEEE TGRS 2025 submission deadline")
```

### 代码/工具问题
```
用户：搜搜 python-docx 怎么插入图片
→ tavily-search("python-docx insert image example")
```

### 论文/研究
```
用户：帮我搜 SOC 预测 hyperspectral 相关论文
→ tavily-search("soil organic carbon prediction hyperspectral deep learning 2024 2025")
```

---

## 注意事项

- **不要因为"可能知道答案"就跳过搜索**：凡是涉及版本号、最新状态、近期事件，都要搜
- **搜索失败时**：告知用户 Tavily MCP 可能未启动，让用户检查 `claude mcp list`
- **结果为空时**：换关键词重试，或改用中文关键词

---

## MCP 未配置时的提示

如果 `tavily-search` 工具不可用，提示用户：

```bash
# 安装 Tavily MCP（全局）
claude mcp add --scope user --transport http tavily \
  "https://mcp.tavily.com/mcp/?tavilyApiKey=你的API_KEY"

# 验证
claude mcp list
```
