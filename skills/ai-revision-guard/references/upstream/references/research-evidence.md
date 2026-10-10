# Research Evidence: Why Over-Refinement and Homogenization Matter

This file documents the academic research and practitioner insights that inform
the revision-guard skill. Load this file when users ask why the skill exists or
want citations for its design decisions.

---

## 1. The Perfectionism Trap

**Source:** Liz Fosslien, LinkedIn post (2026)
**Link:** https://www.linkedin.com/posts/liz-fosslien_ai-is-great-at-many-things-including-amplifying-activity-7435386240037896192

**Key finding:** AI amplifies perfectionist tendencies. Because AI always
provides constructive feedback when asked, users iterate far past the point of
usefulness. The result is what Fosslien calls "Frankenstein-ed slop" — output
worse than the original draft after excessive back-and-forth.

**Design implication:** The revision cap (Step 4) and the MARGINAL self-assessment
(Step 3) directly address this by creating explicit stopping points.

---

## 2. LLMs Over-Replace: 3x Human Edit Rate

**Source:** CHI 2025 — "Can AI Writing Be Salvaged? Mitigating Idiosyncrasies
and Improving Human-AI Alignment in the Writing Process through Edits"
**Link:** https://dl.acm.org/doi/full/10.1145/3706598.3713559

**Key finding:** Using the ArgRewrite-v2 dataset, researchers compared how
humans vs. LLMs (GPT, Gemini, Claude) revised drafts given identical expert
feedback. LLMs made 3x the lexical changes humans did. Even when asked for
"minimal grammar edits," models replaced personal anecdotes with statistical
jargon and swapped first-person pronouns ("I feel") for impersonal nouns
("It is observed").

**Design implication:** The banned substitutions list (Step 2) and the
homogenization detection checklist (Step 5) target exactly these patterns.

---

## 3. 70% Neutrality Shift

**Source:** Wispaper.ai — "How LLMs Distort Our Written Language" (2026)
**Link:** https://www.wispaper.ai/en/blog/llms-distort-written-language-20260321/eng

**Key finding:** Users who heavily relied on LLMs produced responses that
diverged significantly in meaning from those of participants who only partially
relied on LLMs. Heavy LLM use causes a 70% shift toward neutrality in
arguments, replacing the unique human voice with a formal, detached, "safe" AI
persona. This is rooted in RLHF training, which rewards helpful, harmless, and
honest responses — often manifesting as refusal to take strong positions.

**Design implication:** The confidence-preservation checks in Step 5 ("Did tone
shift from confident to cautious?") and the domain presets that lock
argumentative sections directly counter this effect.

---

## 4. Homogenization Widens with Scale

**Source:** Georgetown University — "Homogenizing Effect of Large Language
Models on Creativity" (2025)
**Link:** https://repository.digital.georgetown.edu/downloads/b8414b3c-38b0-44f1-af19-8de793ac2082

**Key finding:** The diversity gap between human and AI-generated text widens
with more output. Enhancing GPT's creative diversity through parameter or
prompt modifications does not mitigate this gap. Generative AI models are
inherently prone to "regression toward the mean" — output variance shrinks
relative to real-world distributions.

**Design implication:** The revision cap exists because each additional round
compounds homogenization. The skill limits rounds rather than trying to fix
the underlying model behavior.

---

## 5. Regression Toward the Mean in AI Output

**Source:** Yu Xie & Yueqi Xie — "When Artificial Intelligence Makes
Everything Similar: The Risks of Content Homogenization" (2026)
**Link:** https://journals.sagepub.com/doi/10.1177/2057150X261419573

**Key finding:** AI-generated content does not reflect the style, tastes,
preferences, and personal idiosyncrasies of the user. Any output produced with
AI assistance is less precise than output produced without AI because
the model's statistical center dominates individual expression.

**Design implication:** The anchoring step (Step 0) preserves the user's
confirmed version — not the first draft, but whatever the user has approved —
as the reference point for all subsequent edits.

---

## 6. Self-Correction Can Make Things Worse

**Source:** TACL — "When Can LLMs Actually Correct Their Own Mistakes?"
**Link:** https://aclanthology.org/2024.tacl-1.78.pdf

**Source:** OpenReview — "Large Language Models Cannot Self-Correct Reasoning Yet"
**Link:** https://openreview.net/forum?id=IkmD3fKBPQ

**Key finding:** LLMs struggle to self-correct without external feedback. Poor
critic feedback leads to "over-refining good responses and neglecting to fix
bad ones." At times, performance degrades after self-correction.

**Design implication:** The skill does not rely on AI self-correction alone.
It uses structured checklists (Step 5) and explicit user confirmation (Step 0)
to provide the external feedback that models need.

---

## 7. Prompt Engineering Shows Diminishing Returns

**Source:** Softcery — "AI Agent Prompt Engineering: Early Gains, Diminishing
Returns, and Architectural Solutions"
**Link:** https://softcery.com/lab/the-ai-agent-prompt-engineering-trap-diminishing-returns-and-real-solutions

**Key finding:** First 5 hours of prompt optimization yields 35% improvement.
Next 20 hours yields 5%. Next 40 hours yields 1%. Returns diminish sharply,
and continued iteration can introduce new problems.

**Design implication:** The inverted-U model underlying this skill. After a
small number of productive revisions, further iteration becomes counterproductive.

---

## 8. Practitioner Observations

From the LinkedIn discussion (162 comments, 1567 reactions):

**XinChi Yang (Principal PM):** "Each iteration pulls language toward the
model's statistical center. After a few passes you start losing the structure
or voice that made the original draft work."

**Ana Petras (Strategic AI Transformation):** Stopped asking "make this better"
and started asking "is this good enough to send?" — fundamentally different
answers and mindset.

**Christopher Nguyen (UX Designer):** "The problem is not the AI. It is that
we outsourced the 'done' decision to a tool that has no concept of done."

**Design implication:** The "Is this good enough?" user command and the
MARGINAL assessment are direct implementations of these practitioner insights.
