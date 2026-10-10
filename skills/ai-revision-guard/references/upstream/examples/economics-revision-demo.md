# Example: Revising an Economics Paper Section

This demonstrates the full revision-guard protocol applied to a Results section
from a difference-in-differences paper.

---

## Original text (user's draft)

> We find that the reform caused a 12.3% increase in college enrollment among
> affected cohorts (Column 3, Table 2). The effect is large — roughly equivalent
> to the enrollment gap between the top and bottom income quartiles in our
> baseline year. I argue this reflects genuine behavioral change rather than
> compositional shifts, because the enrollment increase persists when we restrict
> the sample to first-time enrollees.
>
> The parallel trends assumption holds. Figure 3 shows no differential
> pre-trends in the four years before the reform. The joint F-test on
> pre-treatment coefficients yields p = 0.47.

---

## Step 0: Anchor

**User says:** "Polish the language but don't change my argument."

**Skill identifies:**
```
LOCKED: Results interpretation — "caused a 12.3% increase" (causal claim backed by identification strategy)
LOCKED: Contribution claim — "genuine behavioral change rather than compositional shifts"
LOCKED: Robustness assessment — "parallel trends assumption holds"
Domain preset: Economics (auto-detected)
```

**Skill says:**
> "This is a language revision. I'll smooth the prose but won't touch your
> causal claims, the 12.3% figure, or your parallel trends assessment. OK?"

---

## Step 1: Classify

> "This is a **language** revision. I'll fix grammar and improve clarity but
> won't replace your word choices with academic clichés."

---

## Step 2: Execute (Round 1)

**Revised text:**

> We find that the reform caused a 12.3% increase in college enrollment among
> affected cohorts (Column 3, Table 2). This effect is large, roughly equivalent
> to the enrollment gap between the top and bottom income quartiles in our
> baseline year. I argue this reflects genuine behavioral change rather than
> compositional shifts, because the increase persists when we restrict the
> sample to first-time enrollees.
>
> The parallel trends assumption holds. Figure 3 shows no differential
> pre-trends in the four years before the reform, and the joint F-test on
> pre-treatment coefficients yields p = 0.47.

**Changes made:**
1. "The effect is large — roughly" → "This effect is large, roughly" (smoother connection)
2. "enrollment increase persists" → "increase persists" (removed redundant "enrollment")
3. Combined last two sentences with "and" (tighter)

---

## Step 3: Report

```
Revision Report
───────────────
Changes:    3
Types:      0 structural / 0 substantive / 3 language / 0 formatting
Locked:     none touched
Assessment: MINOR POLISH
```

> "Only minor polish. This is a good stopping point unless you have specific
> sentences you want changed."

---

## What a BAD revision would look like (without revision-guard)

> Our analysis suggests that the reform **may have contributed to** what appears
> to be approximately a 12.3% increase in college enrollment among affected
> cohorts (Column 3, Table 2). **It is worth noting that** this effect is
> **relatively** large, **potentially** equivalent to the enrollment gap between
> income quartiles. **The evidence is broadly consistent with** genuine
> behavioral change rather than compositional shifts, **although alternative
> explanations cannot be entirely ruled out**.
>
> **Importantly**, the parallel trends assumption **appears to be** satisfied.
> Figure 3 **suggests** no differential pre-trends, and the joint F-test
> **yields a p-value of** 0.47, **which may indicate** that pre-treatment
> coefficients are not jointly significant.

**What went wrong:**
- "caused" → "may have contributed to" — **causal language softened** (pattern 6.1)
- "I argue" → "The evidence is broadly consistent with" — **voice erased** (pattern 2.1)
- "holds" → "appears to be satisfied" — **confidence eroded** (pattern 1.1)
- Added "It is worth noting," "Importantly," "although alternative explanations
  cannot be entirely ruled out" — **filler and false balance** (patterns 3.2, 1.2)
- Every direct claim wrapped in hedging — **the entire section became weaker
  without any factual change**
