# Spec Index

> **Purpose**: Fifine-skills 包的开发规范入口。

---

## 项目定位

这是一个 **AI Coding Skills 分发包**。核心活动：
1. 编写 `{skill-name}/SKILL.md` — 定义 skill 的触发方式和执行流程
2. 维护 `scripts/postinstall.js` — 保证安装后正确分发到各 AI 工具目录
3. 通过 `npm install github:five-five0909/Fifine-skills` 向消费项目分发

---

## Spec 文档

| 规范 | 用途 | 何时参考 |
|------|------|---------|
| [skill-format.md](./skill-format.md) | SKILL.md 格式规范（frontmatter + body） | 新增或修改 skill 时 |

---

## 关键约定

- 每个 skill 目录名 = skill 的 `name` 字段（kebab-case）
- SKILL.md frontmatter 必须包含 `name` 和 `description`
- description 必须包含触发词（供 Claude Code skill picker 显示）
- 伴随脚本（.py / .json）放在 skill 目录内，不单独放根目录
- postinstall 检测目标目录：`.claude/` → `.claude/skills/`，`.codex/` → `.codex/skills/`，`.agents/` → `.agents/skills/`
