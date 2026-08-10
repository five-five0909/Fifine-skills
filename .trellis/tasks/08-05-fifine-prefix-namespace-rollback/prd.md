# Restore Fifine skill names and replace the humanizer source

## 状态

- 创建时间：2026-08-05
- 类型：REFACTOR + SKILL_SOURCE_SWAP
- 优先级：P1
- 负责人：fifine

## 背景与动机

`skills-*` 分类命名改变了原有触发方式，用户无法继续按熟悉的名称使用 skill。需要恢复原始核心名称，并统一使用单一 `fifine-` 前缀。同时，humanizer 改用 `KKKKhazix/human-writing` 仓库内容，正式名称为 `fifine-live-humanizer`。`fifine-ai-research-writing-skill` 对应的 skill 不再发布。

## Canonical 命名映射

| 当前目录 | 新目录 |
|---|---|
| skills-writing-humanizer | fifine-live-humanizer |
| skills-research-hook-forge | fifine-paper-idea-hook-forge |
| skills-research-quick-read | fifine-lit-speed-read |
| skills-review-research | fifine-paper-llm-research-grill |
| skills-research-deep-read | fifine-paper-weaver |
| skills-research-radar | fifine-radar |
| skills-library-classify | fifine-pdf-ref-classify |
| skills-library-rename | fifine-pdf-ref-rename |
| skills-research-search | fifine-search |
| skills-research-topic | fifine-paper-topic-refiner |
| skills-review-writing | fifine-paper-write-research-grill |
| skills-session-trans-criptase | fifine-trans-criptase |
| skills-convert-document | fifine-paddleocr-vl |
| skills-session-handoff | fifine-handoff |
| skills-math-proof | fifine-rethlas |
| skills-convert-media | fifine-media-to-txt |
| skills-review-plan | fifine-grill-me-cn |
| skills-writing-paper-sections | fifine-research-paper-writing |
| skills-web-search | fifine-tavily-search |
| skills-workflow-parallel | fifine-parallel-executor-with-trellis |
| skills-writing-prompt | fifine-prompt-amplifier |
| skills-writing-style | fifine-writing-style |
| skills-writing-research-paper | retired and removed |

## Humanizer source

- Source: https://github.com/KKKKhazix/human-writing
- Source revision: `22d20b6` (shallow clone inspected during this task)
- Copy `human-writing/` contents into `skills/fifine-live-humanizer/`.
- Preserve the source MIT `LICENSE` and all references/scripts/assets shipped by the source.
- Set frontmatter name to `fifine-live-humanizer` and keep the source writing behavior unchanged.

## Compatibility

- `scripts/postinstall.js` uses the new `fifine-*` names as canonical names.
- Previous `skills-*`, `academic-*`, `workflow-*`, and pre-namespace names map to the corresponding new canonical skill where the skill still exists.
- The retired `ai-research-writing-skill` is intentionally not mapped or published.

## 验收标准

- [ ] Exactly 24 publishable skill directories remain, all named `fifine-*`.
- [ ] `fifine-live-humanizer` matches the external repository content and has valid neutral frontmatter.
- [ ] `fifine-ai-research-writing-skill` is absent from the source tree, index, and publishable list.
- [ ] `skills.json`, publishable list, README, AGENTS, and routing docs use canonical names.
- [ ] Legacy install configurations resolve to the new names where applicable.
- [ ] `npm run validate` passes.
- [ ] Existing trans-criptase tests and smoke tests pass after the directory rename.
- [ ] No old `skills-*` path remains in distributed indexes or skill trigger references.
