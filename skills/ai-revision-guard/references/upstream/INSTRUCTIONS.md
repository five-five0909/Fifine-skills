---
name: revision-guard
description: >
  Use this skill whenever the user asks to revise, edit, polish, rewrite,
  improve, refine, clean up, tighten, smooth out, or review any existing text
  — especially academic papers, dissertations, thesis chapters, literature
  reviews, grant proposals, or journal submissions. Also activate when the
  user asks "is this good enough?", "am I over-editing?", says "lock this
  paragraph", or is on their second or later revision of the same section.
  Do NOT activate when the user asks to write something from scratch.
version: 1.0.0
license: MIT
compatibility: Claude Code, Codex, OpenClaw, Gemini CLI, any SKILL.md-compatible agent
metadata:
  author: Shiyan Wang
  tags: writing revision academic over-refinement homogenization voice-preservation
---

# Revision Guard

LLM revisions cause two documented problems:

1. **The perfectionism trap.** AI always finds something to "improve." Users
   iterate far past usefulness, ending up worse than their original draft.

2. **Homogenization.** Each revision pulls language toward the model's
   statistical center. LLMs make 3x the lexical changes humans do, shift
   arguments 70% toward neutrality, and replace personal expression with
   impersonal formulas — even when told to make minimal edits.

This skill enforces a protocol that limits revision rounds, preserves the
author's voice, and detects when edits are making text worse.

For research citations, see `references/research-evidence.md`.

---

## Scope

This skill applies to **revising existing text**, not writing from scratch. If
the user asks "write me an introduction," do not activate. If the user asks
"rewrite my introduction" or "clean up this paragraph," activate.

Track revision rounds **per logical section** (Introduction, Methods, Results,
etc.), not per paragraph. If the user pastes a single paragraph for editing,
that paragraph is its own section.

---

## Protocol: 6 Steps (0 through 5)

### Step 0: Anchor — Identify What to Protect

Before any revision, establish what is locked.

**Ask the user:**
> "What parts are you happy with? I'll lock those and only edit what you want
> changed."

**If the user says "everything is open":**
Do not infer or force-lock anything. Respect the instruction. The user may need
a major rewrite — perhaps an advisor demanded it. Proceed with full revision
permission.

**If the user says "lock [specific thing]":**
Record locks explicitly:
```
LOCKED: [section/paragraph ID] — [user stated reason or "user request"]
```

**Domain presets** suggest default locks but the user can override any of them.
Load the preset from `references/domain-presets.md` based on the user's field.
If unknown, ask.

**Locked content and factual errors:** Locking protects voice and argument
framing, not factual accuracy. If you notice a locked section contains a
likely factual error (wrong number, incorrect citation, implausible claim),
flag it:
> "This section is locked, but I noticed [specific issue]. Want me to fix it,
> or is it intentional?"

Never silently preserve an error just because the section is locked.

---

### Step 1: Classify — What Type of Edit?

Before editing, classify the request and state it:

| Type | Scope | Boundary |
|------|-------|----------|
| **Structural** | Reorder sections, adjust flow, reorganize | Don't rewrite sentences |
| **Substantive** | Strengthen argument, add evidence, tighten logic | Don't change voice; word changes are OK when needed to improve the argument |
| **Language** | Fix grammar, improve clarity, smooth transitions | Don't replace the author's natural expressions with academic clichés |
| **Formatting** | Fix LaTeX, citations, references, tables | Don't touch content |
| **Full rewrite** | User explicitly asked to rewrite from scratch | Skip minimal-change constraint; still run homogenization check at the end |

Say:
> "This is a [TYPE] revision. I'll [scope] but won't [boundary]."

**If the user explicitly asks for a full rewrite** ("completely rewrite this,"
"I hate this section, start over"), classify as full rewrite. The minimal-change
constraint and revision cap do not apply. The user has signaled they want a
fresh take. Still run the homogenization check (Step 5) on the output.

---

### Step 2: Execute — Minimal Effective Change

Make the fewest changes that accomplish the stated goal. For each change, ask:
*"Would a careful human editor make this change, or am I making it because I
can?"*

Preserve:
- Sentence length variety (don't normalize to uniform length)
- Specificity (don't replace concrete examples with abstractions)
- Confidence level (don't add hedging the author didn't include)
- First-person voice (don't convert "I find" to "It is observed")

**Banned substitutions** — do not introduce these unless the user explicitly
asks for them:

| Pattern | Problem |
|---------|---------|
| "It is worth noting that..." | Filler |
| "This is not merely X, but also Y..." | Inflated parallelism |
| "In the rapidly evolving landscape of..." | Empty preamble |
| "A comprehensive analysis reveals..." | Vague authority claim |
| "It is important to emphasize that..." | Tells reader what to think |
| "This represents a paradigm shift..." | Hyperbole |
| "The findings underscore..." | Generic verb replacing a specific one |
| "This speaks to the broader question of..." | Vague pivot |
| "It is observed that..." replacing "I find..." | De-personalization |
| "A nuanced understanding..." | Empty modifier |
| "In light of the foregoing..." | Legalistic filler |
| "This is consistent with the notion that..." | Wordy agreement |

**Context-dependent words** — these are fine in moderation but flag overuse:

| Word | When it's OK | When it's AI slop |
|------|-------------|-------------------|
| "Notably" / "Importantly" | Once per section as genuine signposting | Every other paragraph |
| "The evidence suggests..." | When the evidence genuinely only suggests, not confirms | Replacing "The data shows" for no reason |
| "Leverage" | Technical meaning in finance/mechanics | Replacing "use" |
| "Demonstrate" / "Illustrate" | When describing proofs, experiments, figures | Replacing "show" generically |
| "Utilize" / "Employ" | "Employ a method" is fine in methods sections | Replacing "use" everywhere |

For the full pattern catalog, see `references/over-refinement-patterns.md`.

---

### Step 3: Report — Self-Assessment

After completing a revision, produce a brief report:

```
Revision Report
───────────────
Changes:    [number]
Types:      [X structural / Y substantive / Z language / W formatting]
Locked:     [none touched / list which and why]
Assessment: [SUBSTANTIAL / MINOR POLISH / MARGINAL]
```

**Assessment criteria:**

| Rating | Meaning | Action |
|--------|---------|--------|
| SUBSTANTIAL | Materially improved clarity, logic, or correctness | Continue if user wants |
| MINOR POLISH | Small grammar fixes, smoother transitions | Suggest finalizing |
| MARGINAL | Lateral moves, not improvements | Recommend stopping |

**Important caveat:** This self-assessment is a rough signal, not gospel. The
research shows LLM self-correction is unreliable (see `references/research-evidence.md`,
section 6). The report helps the user decide, but the user makes the call.
If the user disagrees with the assessment, the user is right.

**If MARGINAL:**
> "This revision is marginal — I'm polishing, not improving. I'd suggest
> finalizing. Want to move on?"

**If MINOR POLISH on round 2+:**
> "Only minor polish left. Good stopping point unless you have specific
> sentences you want changed."

**If user says "skip the report" or "brief report only":** Respect it. Give a
one-line assessment or skip entirely.

---

### Step 4: Limit — The Revision Cap

Track revision rounds per section:

| Round | What happens |
|-------|-------------|
| **1** | Full revision → Report |
| **2** | Follow-up on user's specific feedback → Report |
| **3** | Warning (see below) |

**Round 3 warning:**
> "Two rounds done on this section. More editing risks homogenization. Options:
>
> 1. **Finalize** this version
> 2. **You edit** the specific sentences you don't like
> 3. **Start fresh** in a new conversation with clear constraints
>
> Say 'continue anyway' to override."

The user can override. If they say the third round is driven by new reviewer
or advisor comments (not aimless polishing), skip the warning — that's
legitimate new input, not over-refinement.

**If user configured a different max** (e.g., "set max rounds to 3"), the
warning shifts to round N+1. The cap is a default, not a hard wall.

**Cross-session tracking:** If the user says "I already revised this twice in
a previous session," start the counter at their stated number.

---

### Step 5: Detect — Homogenization Check

After each revision, compare the new text against the pre-revision version:

- [ ] Replaced 3+ of the user's word choices with "safer" alternatives?
- [ ] Text became more hedged or qualified?
- [ ] Specific examples replaced with generalizations?
- [ ] Tone shifted from confident to cautious?
- [ ] Sentence length variety decreased?
- [ ] First-person voice replaced with impersonal constructions?
- [ ] Domain-specific terms replaced with generic academic language?

**If 2+ are YES:**
> "Homogenization warning: this revision made your text more generic.
> Specifically: [list what changed]. Want me to revert those changes?"

**Run this check even on full rewrites.** A rewrite should produce fresh,
specific text — not a blander version of what was there before.

---

### Step 5b (Optional): Cross-Model Verification

Self-assessment (Step 3) and self-detection (Step 5) both rely on the same
model that made the revision. The research evidence (section 6) shows this is
unreliable — a model that over-refined text may not recognize it did so.

A second, independent model eliminates this blind spot.

**When to offer cross-model verification:**
- Round 2+ on substantive or full-rewrite revisions
- When the self-assessment is uncertain (borderline MINOR POLISH / MARGINAL)
- When the user asks "is this good enough?" on important sections
- On high-stakes text: results interpretation, identification strategy,
  contribution statements

**How it works:**

If the user has Codex installed (`codex:rescue` available), offer:
> "Want me to send the before/after to a second model (Codex/GPT) for an
> independent homogenization check? This catches blind spots I might miss
> in my own revision."

If the user agrees, send to Codex:
```
/codex:rescue Compare these two versions of an academic text section.
The first is the author's version, the second is my revision.
Check: (1) Did the revision weaken any claims without justification?
(2) Did it replace specific language with generic alternatives?
(3) Did it shift tone from confident to hedged?
(4) Did it remove the author's voice?
Report only problems found. If the revision is clean, say so.

ORIGINAL:
[paste original]

REVISED:
[paste revised]
```

**If Codex is not installed:** Skip this step silently. Do not error or nag.
Mention in the revision report:
> "Tip: Install Codex (`/codex:setup`) to enable cross-model verification —
> a second AI independently checks whether my revision degraded your text."

This message appears **once per session**, not every round.

**If the user's agent tool supports other external models** (e.g., Gemini CLI,
OpenRouter), the same pattern applies — send the before/after to any
independent model for comparison.

---

## Domain Presets

Load full details from `references/domain-presets.md`. Summary of default locks:

| Domain | Locked by Default (grammar-only edits) |
|--------|----------------------------------------|
| **Economics** | Results interpretation, identification strategy, contribution claims, robustness assessments |
| **Law** | Legal reasoning chains, case citations, jurisdictional specificity, statutory interpretation |
| **Medicine** | Clinical findings, diagnostic reasoning, treatment protocols, statistical results |
| **Humanities** | Authorial voice, interpretive arguments, close reading passages, theoretical positioning |
| **STEM** | Methodology descriptions, data interpretations, technical specs, measurement details |
| **Psychology** | Statistical reporting (APA format), operationalizations, participant descriptions, theoretical framing |
| **Political Science** | Causal identification, institutional descriptions, case selection rationale, normative claims |
| **Education** | Intervention descriptions, assessment instruments, effect sizes, equity framing |

Presets are defaults. Users override any lock by saying "unlock [section]."

For fields not listed (sociology, business, public health, etc.), ask the user
which sections they consider core arguments, and lock those.

---

## Configuration

| Setting | Default | How to change |
|---------|---------|---------------|
| Max revision rounds | 2 | "Set max rounds to 3" |
| Domain preset | Auto-detect | "Use economics preset" / "Use law preset" |
| Strictness | Standard | "Be stricter" / "Be more flexible" |
| Report verbosity | Full | "Skip the report" / "Brief report only" |
| Cross-model check | Off (unless Codex installed) | "Cross-check this with Codex" / "Skip cross-check" |

---

## User Commands

| Command | Effect |
|---------|--------|
| "Lock this paragraph" | Preserve meaning and tone in future revisions |
| "Unlock everything" | Full revision permission — no forced locks |
| "Is this good enough?" | Honest assessment: finalize or keep editing |
| "Am I over-editing?" | Check revision count + homogenization indicators |
| "Revert last round" | Undo most recent revision |
| "Use [domain] preset" | Switch to field-specific default locks |
| "Continue anyway" | Override the revision cap warning |
| "Cross-check this" | Send before/after to second model for independent review |

---

## Reference Files

Loaded on demand, not all at once:

| File | When to load |
|------|-------------|
| `references/research-evidence.md` | User asks why the skill exists, or you need citations |
| `references/over-refinement-patterns.md` | Checking a specific pattern or expanding the banned list |
| `references/domain-presets.md` | Need full preset details for a field |
