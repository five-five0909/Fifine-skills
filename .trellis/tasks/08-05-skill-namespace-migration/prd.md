# Skills namespace migration

## 状态

- 创建时间：2026-08-05
- 类型：REFACTOR
- 优先级：P1
- 负责人：fifine

## 背景与动机

现有 skill 名称混用了 `academic-*`、`workflow-*`、`document-*`、`web-*` 等前缀，分类维度不一致，也没有统一的产品命名空间。需要将全部发布 skill 迁移到 `skills-<分类>-<能力>` 格式，并保留 `agent-trans-criptase` 的核心识别名 `trans-criptase`。

## 目标与成功标准

- [ ] 25 个发布 skill 的目录名和 frontmatter `name` 统一为 `skills-<分类>-<能力>`。
- [ ] `skills.json`、发布清单、README、AGENTS.md 和所有触发命令引用新名称。
- [ ] `postinstall.js` 可按新名称安装，并兼容旧名称配置。
- [ ] skill 内容中的交叉引用和触发命令不再指向已迁移名称。
- [ ] `npm run validate` 通过，且无未预期的目录或路径遗留。

## 命名映射

| 旧名称 | 新名称 |
|---|---|
| academic-topic-refiner | skills-research-topic |
| academic-radar | skills-research-radar |
| academic-search | skills-research-search |
| academic-lit-speed-read | skills-research-quick-read |
| academic-paper-weaver | skills-research-deep-read |
| academic-idea-hook-forge | skills-research-hook-forge |
| ai-research-writing-skill | skills-writing-research-paper |
| research-paper-writing | skills-writing-paper-sections |
| academic-humanizer | skills-writing-humanizer |
| writing-style | skills-writing-style |
| writing-prompt-amplifier | skills-writing-prompt |
| academic-llm-research-grill | skills-review-research |
| academic-write-research-grill | skills-review-writing |
| review-grill-me-cn | skills-review-plan |
| academic-ref-classify | skills-library-classify |
| academic-ref-rename | skills-library-rename |
| workflow-dev-done-flow | skills-workflow-dev |
| workflow-parallel-executor-with-trellis | skills-workflow-parallel |
| workflow-trellis-task-orchestrator | skills-workflow-trellis |
| agent-trans-criptase | skills-session-trans-criptase |
| handoff | skills-session-handoff |
| document-paddleocr-vl | skills-convert-document |
| media-transcript | skills-convert-media |
| web-tavily-search | skills-web-search |
| math-rethlas | skills-math-proof |

## 技术范围

### 涉及模块

- `skills/*/SKILL.md`、`agents/openai.yaml` 及 skill 内部引用
- `skills.json`
- `scripts/publishable-skills.json`
- `scripts/postinstall.js`
- `README.md`、`AGENTS.md`
- 迁移任务文档

### 不在范围内

- 不改变任何 skill 的执行逻辑、脚本实现或依赖。
- 不删除旧名称的安装配置兼容映射。
- 不改变展示名称的自然语言表达，除非其中包含旧命令路径。

## 实现思路

1. 建立旧名到新名的单一映射表。
2. 使用 `git mv` 迁移 25 个 skill 目录。
3. 更新 frontmatter、触发命令、交叉引用和索引文件。
4. 更新安装器：新名作为 canonical name，旧名作为 legacy alias。
5. 运行验证脚本并检查旧名称残留，仅允许出现在兼容映射或迁移说明中。

## 验收清单

- [ ] `npm run validate` 通过。
- [ ] 新名称目录均包含 `SKILL.md` 和 `agents/openai.yaml`。
- [ ] `skills.json` 的每个 path 都存在且 name/path 一致。
- [ ] 新旧 `skills.json` include 配置都能被 postinstall 正确解析。
- [ ] 所有 skill 内容中的 `/old-name` 触发命令已迁移。
- [ ] `git diff` 中没有意外删除 skill 内容。
