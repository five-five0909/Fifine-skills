# Fifine Skills

A collection of reusable AI agent skills.

## Install

Depending on your `ccswitch` version, install from GitHub with either:

```bash
ccswitch add five-five0909/Fifine-skills
```

or:

```bash
ccswitch add https://github.com/five-five0909/Fifine-skills.git
```

If you use the `skills` CLI:

```bash
npx skills add five-five0909/Fifine-skills
```

This repository can also still be installed through npm:

```bash
npm install github:five-five0909/Fifine-skills
```

## Environment variables

Skills that need credentials read them from a local plaintext env file instead of
the repository or the agent config. Resolution order, first path wins:

1. The file pointed at by `FIFINE_SKILLS_ENV` (optional override).
2. `~/.config/fifine-skills/secrets.env` (shared across all Fifine skills).
3. `~/.config/fifine-skills/<skill-name>.env` (skill-specific).

Existing process env always wins; the loader never overwrites a variable that is
already set (`skills/fifine-trans-criptase/lib/shared/config.mjs`). Values are
read once when the skill's config module loads, and a stdio MCP subprocess
freezes its environment at startup — restart the MCP server / agent after
editing an env file.

Several skills need credentials or external provider configuration only when you
use their live API features. Examples include `fifine-trans-criptase` (embedding
provider endpoint, key, and model for semantic/hybrid transcript and code
search), `fifine-paddleocr-vl` (AI Studio token for OCR parsing), and imported
image/diagram generation skills such as `baoyu-image-gen`, `stem-illustration`,
and `tech-diagrams` (provider-specific image API keys or cloud credentials). Copy
[`examples/fifine-skills-secrets.env.example`](examples/fifine-skills-secrets.env.example)
to `~/.config/fifine-skills/secrets.env`, fill in real values needed by the
skills you use, and keep the file at permissions `600`. That file lives outside
the repository on purpose: **never commit real keys or tokens here**.
`fifine-trans-criptase` also publishes an
[`docs/environment.md`](skills/fifine-trans-criptase/docs/environment.md) with
the full variable list, precedence rules, verified provider facts, and proxy
setup.

## Skills

Most original Fifine skills use the `fifine-<original-name>` namespace. Some
imports retain upstream names; the writing imports use unique host-neutral root
adapter names, with original instructions retained under `references/upstream/`
as `INSTRUCTIONS.md` rather than separately registered nested skills.

Examples include `fifine-live-humanizer`, `fifine-paper-weaver`,
`fifine-pdf-ref-classify`, `fifine-paper-idea-hook-forge`, and
`fifine-media-to-txt`. `fifine-translation-multiple-kanban` handles
structured single- or multi-file translation with resumable JobID chunks and
selectable HTML/Markdown output. `fifine-english-research-write` supports
scientific English drafting and IMRaD prose polishing with phrase banks,
section templates, and sentence-level style baselines. The imported
`fifine-science-research-writing-skills` skill remains available as a broader
STEMM paper-writing assistant for drafting, revising, reviewing, and
section-by-section guidance. `fifine-adaptive-runtime-orchestrator` discovers
the real execution environment, picks an executor and shell automatically,
waits on long builds, training runs, and remote jobs with adaptive polling, and
can run measure-first performance diagnosis/optimization without chasing raw
CPU/GPU utilization for its own sake. `fifine-session-memory-curator` preserves durable preferences, corrections,
pitfalls, and lessons in an auditable ledger, while promoting only grounded,
correctable rules into global agent instructions. `fifine-file-naming-organizer`
applies the 【状态标签】+YYYYMMDD+核心信息+版本号 formula: it proposes canonical names
for new files, audits an existing folder read-only, and executes a confirmed
rename/move plan with 定稿 locking, conflict refusal, a mapping log, and rollback.
The visual creation family includes `fifine-visual-creation-orchestrator` as an
AI-paper Figure Planner for NeurIPS/ICML/ICLR/ACL/CVPR and Nature-family work.
It maps scientific questions to an 18-category, 180-type registry, plans
Nature/NMI multi-panel evidence chains, prefers R for suitable statistical and
composition work, and selects Python, Graphviz/SVG, interactive, specialist, or
runtime-exposed generative engines by figure type. Existing visual skills remain
the semantic and rendering specialists for publication figures, STEM
illustrations, architecture diagrams, interactive visuals, and provider-based
image generation.

See [`skills.json`](skills.json) for the complete local scanner index, including
local-only entries. It is not the public installation whitelist; that is
[`scripts/publishable-skills.json`](scripts/publishable-skills.json).

### Writing imports and publication boundaries

Seven imported root adapters are retained locally, plus the original
`fifine-writing-orchestrator`:

| Root skill | Public installation | Source / license boundary |
|---|---|---|
| `kiterlin-anti-defensive-writing` | Yes | Kiterlin/anti-defensive-writing; MIT |
| `adkid-anti-defensive-writing` | Yes | Adkid-Zephyr/anti-defensive-writing-Skill; MIT, Chinese and English resources |
| `academic-defensive-writing-auditor` | Yes | Worigin0314/academic-defensive-writing-auditor; MIT, original attribution retained |
| `ai-revision-guard` | Yes | ShiyanW/ai-revision-guard; MIT |
| `nature-paper-skills` | Licensed subset only | Boom5426/Nature-Paper-Skills; component-specific MIT/Apache-2.0 notices |
| `momojee-writing-skills` | No, local-only | MoMoJee/MoMoJeeObsidian; mixed unresolved and noncommercial material |
| `writing-guard-skill` | No, local-only | xmutfyh/writing-guard-skill; declared MIT but third-party Apache attribution/notice obligations unresolved |
| `fifine-writing-orchestrator` | Yes | Original thin planner and single-lead writing orchestration |

Downloaded or publicly accessible does **not** mean cleared for redistribution.
Each imported package retains its own `source.json`, applicable licenses,
attributions and notices; the repository's MIT declaration does not relicense
third-party content. The two local-only packages are excluded from both the npm
archive and the postinstall whitelist. Nature's unresolved
`references/upstream/skills/core/rebuttal-response/` subtree is excluded from the
npm archive **and** postinstall copying, including direct GitHub installations.
Its manifest records the local inventory, not a guarantee that every listed file
is shipped; the adapter checks for this optional component before using it.
Other installers or direct source scanners may discover local-only skills and
need their own explicit selection; the npm whitelist does not govern them.

### Writing routing and recommended bundle

Use `fifine-writing-orchestrator` for natural-language writing planning, drafting,
revision or audit requests spanning multiple skills. It selects one lead writer,
loads specialists only as needed, preserves evidence and original-text locks,
and checks actual availability before falling back with disclosure. Simple edits
can go directly to a specialist; planning-only requests do not authorize a full
draft. Automatic routing depends on the host discovering the installed metadata;
it is not guaranteed on every host or every request.

- ML/CV/NLP paper structure: `fifine-research-paper-writing`.
- General STEMM drafting: `fifine-science-research-writing-skills`.
- Scientific English and English template-like/AI-like prose:
  `fifine-english-research-write`, optionally `ai-revision-guard`; do not apply
  the Chinese humanizer's punctuation/style constraints to English papers.
- Chinese reader-facing creation/revision: `fifine-live-humanizer`;
  requested role/style: `fifine-writing-style`.
- Nature-style whole-paper/review architecture and focused checks:
  `nature-paper-skills`; defensive-prose diagnosis: the auditor;
  evidence-preserving anti-defensive edits: Kiterlin; contribution narrative
  restructuring: Adkid only when needed, not three repeated full rewrites.
- Faithful translation: `fifine-translation-multiple-kanban`; figure evidence
  planning remains with `fifine-visual-creation-orchestrator`.

For selective npm installation, a recommended writing bundle in the consuming
project's `skills.json` is:

```json
{
  "include": [
    "fifine-writing-orchestrator",
    "fifine-research-paper-writing",
    "fifine-science-research-writing-skills",
    "fifine-english-research-write",
    "fifine-live-humanizer",
    "fifine-writing-style",
    "fifine-translation-multiple-kanban",
    "ai-revision-guard",
    "academic-defensive-writing-auditor",
    "kiterlin-anti-defensive-writing",
    "adkid-anti-defensive-writing",
    "nature-paper-skills"
  ],
  "targets": ["claude", "codex", "agents"]
}
```

Omit `include` to install all available publishable skills. Omit `targets` to
select existing `.claude`, `.codex` and `.agents` directories; if none exist,
postinstall skips installation. No dependency resolver is added: selecting only
the orchestrator does not install its specialists. This writing integration has
been inspected statically only; no runtime tests, installs or skill executions
were performed.

## Prompt Templates

This repository also includes reusable prompt templates under [`prompts/`](prompts/).
They are reference prompts, separate from installable skills, and are included in
the npm package for users who want to reuse or adapt them manually.

### General prompts

- [`BASE AGENTS.md`](prompts/BASE%20AGENTS.md): general agent behavior and engineering workflow guidance.
- [`Claude Fable 5.md`](prompts/Claude%20Fable%205.md): a Claude-style system prompt reference.

### Product research and strategy

- [`competitive-analyst.md`](prompts/competitive-analyst.md)
- [`data-analyst.md`](prompts/data-analyst.md)
- [`product-director.md`](prompts/product-director.md)
- [`requirement-analyst.md`](prompts/requirement-analyst.md)
- [`roadmap-planner.md`](prompts/roadmap-planner.md)
- [`user-researcher.md`](prompts/user-researcher.md)

### Design and delivery

- [`critique-reviewer.md`](prompts/critique-reviewer.md)
- [`design-engine-team-lead.md`](prompts/design-engine-team-lead.md)
- [`design-system-expert.md`](prompts/design-system-expert.md)
- [`discovery-analyst.md`](prompts/discovery-analyst.md)
- [`export-specialist.md`](prompts/export-specialist.md)
- [`prototype-builder.md`](prompts/prototype-builder.md)

### Software engineering

- [`software-architect.md`](prompts/software-architect.md)
- [`software-engineer.md`](prompts/software-engineer.md)
- [`software-product-manager.md`](prompts/software-product-manager.md)
- [`software-qa-engineer.md`](prompts/software-qa-engineer.md)
- [`software-team-lead.md`](prompts/software-team-lead.md)

### Platform and operations

- [`database-optimization-expert.md`](prompts/database-optimization-expert.md)
- [`infrastructure-operations-expert.md`](prompts/infrastructure-operations-expert.md)
- [`security-expert.md`](prompts/security-expert.md)

## Development

```bash
npm run validate
```

This is a publishable skill tree, so `npm run validate` rejects build artifacts
and private state anywhere in the repository — `node_modules/`, `.venv/`,
`__pycache__/`, `dist/`, `build/`, plus index directories such as `data/` and
`index/`. Never run `npm install` inside `skills/` to pull a dependency for a
skill script: put runtime dependencies in a directory outside the repository (for
example `~/sdk-tools/mcp-proxy`) and point the skill's config at that path.

## Structure

The collection follows this structure:

```text
skills/<skill-name>/SKILL.md
skills/<skill-name>/agents/openai.yaml
skills/<skill-name>/references/
skills/<skill-name>/scripts/
skills/<skill-name>/assets/
prompts/<prompt-name>.md
```

Repository-level scripts live under `scripts/`, prompt templates live under
`prompts/`, and `skills.json` serves as the root index for scanners.
