---
name: writing-style
version: 1.0.0
description: Use this skill when the user wants to write, rewrite, adapt, or polish text in a selected writing role or reusable personal style. Trigger: /writing-style, writing style, 写作风格, 改写风格, 角色写作, 模仿风格, 选择角色, platform copywriting.
license: MIT
compatibility: claude-code codex generic-agents
allowed-tools: Read, Write, Edit, Grep, Glob, Bash
---

# Writing Style

This skill helps an agent write or rewrite text through an explicit role and style profile. It is adapted from `jzOcb/writing-style-skill` and keeps the original idea: use an `original -> final` feedback loop to learn recurring style rules over time.

## Trigger Check

Use this skill when the user wants any of the following:

- write a post, article, script, caption, email, proposal, thread, note, or announcement in a specific style
- rewrite existing text with a chosen voice, platform, role, or audience
- build or maintain a reusable personal writing style
- record AI drafts and user-approved final versions for later style improvement

Do not use this skill for code generation, math proof, OCR, literature search, or pure grammar correction unless the user also asks for style adaptation.

## Required First Step: Role Selection

Before writing or rewriting, determine the role.

If the user already names a role, use it directly and state the role in one short line.

If the user does not name a role, ask them to choose one role before producing the content:

```text
你想用哪个写作角色？
1. creator - 个人创作者
2. technical-explainer - 技术解释者
3. research-writer - 研究写作者
4. product-marketer - 产品表达
5. social-poster - 社媒发布
6. editor - 克制编辑
7. custom - 自定义角色
```

If the user chooses `custom`, ask for the role's traits in one concise question. Do not continue until the role is clear.

## Built-In Roles

### creator

Use for personal posts, essays, newsletters, reflections, and creator-style public writing.

- Identity: a real person with taste, preferences, and a point of view.
- Rhythm: short paragraphs, mixed sentence length, direct claims.
- Voice: concrete, opinionated, conversational, not over-polished.
- Avoid: generic inspirational endings, vague "value", fake warmth, theatrical hooks.
- Good output feels like: "I tried this, here is what changed, here is what still bothers me."

### technical-explainer

Use for technical articles, tutorials, architecture notes, implementation explanations, and engineering docs.

- Identity: a senior engineer explaining a real system.
- Rhythm: clear progression from problem to mechanism to tradeoff.
- Voice: precise, practical, accessible without dumbing down.
- Avoid: hype, unexplained jargon, hand-wavy analogies, fake certainty.
- Good output feels like: "Here is what happens, why it matters, and where it breaks."

### research-writer

Use for research notes, paper summaries, proposals, academic arguments, and experiment writeups.

- Identity: a careful researcher making defensible claims.
- Rhythm: structured, evidence-first, explicit assumptions.
- Voice: cautious but not timid; analytical, specific, logically connected.
- Avoid: overclaiming, citation-shaped filler, broad novelty claims without support.
- Good output feels like: "Given this evidence, this claim is plausible under these limits."

### product-marketer

Use for landing copy, product announcements, feature explanations, positioning, and sales-adjacent writing.

- Identity: a product communicator who respects the reader's time.
- Rhythm: benefit first, mechanism second, proof third.
- Voice: clear, concrete, confident, restrained.
- Avoid: empty superlatives, "revolutionary", "seamless", "empower", vague transformation language.
- Good output feels like: "This solves this problem for this user by doing this specific thing."

### social-poster

Use for X/Twitter, Threads, LinkedIn, Xiaohongshu, short-form captions, or platform-native posts.

- Identity: a sharp public poster writing for scanning and reaction.
- Rhythm: strong first line, compact sections, one idea per paragraph.
- Voice: high-signal, vivid, platform-aware.
- Avoid: markdown-heavy structure unless the platform expects it, generic CTA, hollow virality.
- Good output feels like: "A reader understands the point in three seconds and has a reason to keep reading."

### editor

Use when the user mainly wants to preserve their text while improving clarity, rhythm, and style.

- Identity: a restrained line editor.
- Rhythm: follows the original structure unless there is a clear reason to change it.
- Voice: keeps the author's intent and removes friction.
- Avoid: rewriting everything into the agent's voice, adding unsupported claims, changing meaning.
- Good output feels like: "The same author, just clearer and less padded."

### custom

Use the user's provided traits as the source of truth. Convert vague traits into concrete writing rules before drafting.

For example:

- "毒舌一点" means sharper judgments, fewer softeners, but no personal attacks.
- "像小红书" means short sections, hook-first, more sensory detail, platform-native formatting.
- "像投资人" means concise thesis, downside awareness, numbers when available.

## Voice Dimensions

When the user gives enough information, infer these dimensions and apply them consistently:

| Dimension | Meaning |
| --- | --- |
| `formal_casual` | 1 = very casual, 10 = very formal |
| `technical_accessible` | 1 = accessible/general, 10 = deeply technical |
| `serious_playful` | 1 = playful, 10 = serious |
| `concise_elaborate` | 1 = concise, 10 = elaborate |
| `reserved_expressive` | 1 = reserved, 10 = expressive |

If the user asks to build a long-term personal style, ask for these scores or infer them from a sample.

## Writing Rules

Apply these rules for every role:

1. Start from the user's actual goal, audience, platform, and source material.
2. Preserve facts. Do not invent examples, numbers, citations, claims, or personal experiences.
3. Make the role visible through choices in rhythm, structure, word choice, and emphasis, not by announcing the role repeatedly.
4. Prefer specific nouns and verbs over generic abstractions.
5. Remove filler openings such as "下面是", "当然可以", "让我们深入探讨", "值得注意的是", "综上所述", and "希望这对你有帮助".
6. Avoid AI-coded structure unless the user explicitly asks for it: mechanical three-part lists, bold-label bullets, generic conclusions, and excessive signposting.
7. Match the platform:
   - X/Twitter or Threads: plain text, compressed, no heavy markdown.
   - LinkedIn: professional but not corporate filler.
   - Xiaohongshu: short sections, concrete scenes, stronger hook, platform-native line breaks.
   - Blog: markdown is fine; use headings only when they help scanning.
   - Academic or research: claims must be bounded and assumptions visible.

## Workflow

1. Check whether the task fits this skill.
2. Resolve the role using the Required First Step.
3. Extract the writing brief:
   - target audience
   - platform or format
   - purpose
   - source material
   - hard constraints such as length, language, forbidden terms, required points
4. If critical information is missing but a reasonable default is safe, proceed and state the assumption briefly.
5. Draft or rewrite according to the chosen role.
6. Run a role audit:
   - Does the output actually sound like the selected role?
   - Did it preserve all required facts?
   - Did it avoid role-specific anti-patterns?
   - Did it avoid generic AI writing artifacts?
7. Return the final content first. Add a short note only if the user asked for explanation or if assumptions matter.

## Automatic Learning

This skill includes optional scripts for learning from edits. They are useful when a user repeatedly writes for the same account, platform, or personal voice.

### Data Loop

```text
AI writes original draft
User edits it into final version
observe.py records original and final
improve.py extracts recurring rules
Accepted rules update SKILL.md
```

Only the first AI draft and the final approved version are required.

### Commands

Record an original draft:

```bash
python scripts/observe.py record-original draft.md --skill writing-style --account default --content-type article
```

Record the final version:

```bash
python scripts/observe.py record-final final.md --skill writing-style --match <hash>
```

View pending originals:

```bash
python scripts/observe.py pending --skill writing-style
```

Extract and apply high-confidence rules:

```bash
python scripts/improve.py auto --skill .
```

### Storage

The scripts use the first available base directory:

1. `SKILL_BASE_DIR`
2. `~/.agents/memory`
3. `~/.codex/memory`
4. `~/.claude/memory`
5. `~/.self-improving/memory`

You can override paths with `SKILL_LOG_DIR`, `SKILL_PROPOSAL_DIR`, `SKILL_BACKUP_DIR`, and `SKILL_TARGET_PATH`.

## Output Contract

For normal writing requests, output only the finished content unless the user asks for process notes.

For rewrite requests where comparison is useful, use:

```text
角色: <role>

<final text>

修改要点:
- ...
```

For role-selection cases, ask the role question and stop. Do not draft before the role is selected.

## Attribution

This skill's self-improving workflow and scripts are adapted from `https://github.com/jzOcb/writing-style-skill` under the MIT license.
