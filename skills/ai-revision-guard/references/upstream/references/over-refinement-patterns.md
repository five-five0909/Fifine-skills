# Over-Refinement Pattern Catalog

When LLMs revise text, they systematically apply certain transformations that
degrade quality while appearing to "improve" it. This catalog documents 18
specific patterns, grouped by category, with before/after examples.

Load this file when checking a specific revision for problematic patterns.

---

## Category 1: Hedging and Weakening

### 1.1 Confidence Erosion
**What AI does:** Adds qualifiers to direct statements.
**Why it's bad:** Weakens the author's claims without reason.

| Before (author) | After (AI) |
|-----------------|------------|
| "The policy caused a 12% decline in emissions." | "The policy appears to have contributed to what may be approximately a 12% decline in emissions." |
| "We find strong evidence that X leads to Y." | "Our analysis suggests there may be evidence consistent with X potentially leading to Y." |

### 1.2 False Balance
**What AI does:** Adds unnecessary caveats to well-supported claims.
**Why it's bad:** Creates false equivalence between strong evidence and speculation.

| Before | After |
|--------|-------|
| "The results confirm our hypothesis." | "While the results are broadly consistent with our hypothesis, alternative explanations cannot be entirely ruled out." |

### 1.3 Passive Deflection
**What AI does:** Replaces active constructions with passive ones.
**Why it's bad:** Removes agency and makes prose limp.

| Before | After |
|--------|-------|
| "We argue that tariffs reduce welfare." | "It is argued that tariffs may reduce welfare." |
| "I find that the coefficient is significant." | "It was found that the coefficient is significant." |

---

## Category 2: De-Personalization

### 2.1 Voice Erasure
**What AI does:** Replaces first-person with impersonal constructions.
**Why it's bad:** Strips the author's presence from their own work.

| Before | After |
|--------|-------|
| "I use a difference-in-differences design." | "A difference-in-differences design is employed." |
| "Our contribution is threefold." | "The contributions of this study are threefold." |

### 2.2 Anecdote Replacement
**What AI does:** Replaces specific, personal observations with generic statements.
**Why it's bad:** Removes the concrete details that make writing vivid.

| Before | After |
|--------|-------|
| "During fieldwork in rural Bihar, farmers told me credit was their biggest constraint." | "Research indicates that access to credit remains a significant challenge in rural agricultural contexts." |

---

## Category 3: Formalization and Inflation

### 3.1 Vocabulary Inflation
**What AI does:** Replaces simple words with complex ones.
**Why it's bad:** Adds cognitive load without adding information.

| Simple (keep) | Inflated (avoid) |
|---------------|-----------------|
| use | utilize, leverage, employ |
| show | demonstrate, illustrate, elucidate |
| help | facilitate, enable |
| about | approximately, in the vicinity of |
| change | transform, paradigm shift |
| important | of paramount importance, critical |
| many | a significant number of, numerous |

### 3.2 Filler Preambles
**What AI does:** Adds empty introductory phrases.
**Why it's bad:** Delays the actual content.

| Filler (cut) | Better |
|--------------|--------|
| "It is worth noting that X." | "X." |
| "It is important to emphasize that Y." | "Y." |
| "In this context, it should be mentioned that Z." | "Z." |
| "It bears mentioning that..." | [delete entirely] |

### 3.3 Inflated Parallelism
**What AI does:** Creates artificial balance structures.
**Why it's bad:** Imposes a template onto natural prose.

| Before | After |
|--------|-------|
| "The policy failed." | "This is not merely a policy shortcoming — it is a fundamental challenge to the underlying paradigm." |

---

## Category 4: Generalization and Abstraction

### 4.1 Specificity Loss
**What AI does:** Replaces concrete numbers, names, or examples with vague references.
**Why it's bad:** Removes the evidence that supports the argument.

| Before | After |
|--------|-------|
| "Between 2008 and 2012, manufacturing employment fell by 2.4 million." | "In recent years, there has been a significant decline in manufacturing employment." |
| "Autor, Dorn, and Hanson (2013) show..." | "Previous research has shown..." |

### 4.2 Example Removal
**What AI does:** Replaces illustrative examples with abstract claims.
**Why it's bad:** Examples are what make arguments concrete and testable.

| Before | After |
|--------|-------|
| "Consider a farmer deciding whether to adopt drought-resistant seeds. She faces..." | "Agricultural decision-making under uncertainty involves complex trade-offs." |

---

## Category 5: Structural Homogenization

### 5.1 Sentence Length Convergence
**What AI does:** Makes all sentences roughly the same length.
**Why it's bad:** Monotonous rhythm. Good prose alternates short and long sentences.

**Before (varied, good):**
> "The coefficient is 0.34. This is large. In the baseline specification with
> firm and year fixed effects, clustered standard errors at the state level,
> and the full set of demographic controls, the treatment effect remains
> statistically significant at the 1% level."

**After (uniform, bad):**
> "The coefficient is 0.34, which represents a substantial effect. The baseline
> specification includes firm and year fixed effects along with clustered
> standard errors. The treatment effect remains significant with the full set
> of controls."

### 5.2 Transition Word Monotony
**What AI does:** Inserts "However," "Moreover," "Furthermore," "Additionally,"
at the start of every other sentence.
**Why it's bad:** Creates a mechanical rhythm. Real writing varies transitions.

**Before (monotonous):**
> "The treatment effect is positive. However, the confidence interval is wide.
> Moreover, the placebo test raises concerns. Furthermore, the sample size is
> small. Additionally, we lack data on the pre-treatment period."

**After (varied):**
> "The treatment effect is positive, though the confidence interval is wide.
> The placebo test raises concerns — and the small sample size makes it hard
> to rule out noise. We also lack pre-treatment data."

### 5.3 Paragraph Template
**What AI does:** Forces every paragraph into topic-sentence → evidence →
interpretation structure.
**Why it's bad:** Not all paragraphs serve the same function. Some argue, some
narrate, some compare.

**Before (every paragraph identical structure):**
> "Trade liberalization affects labor markets. Smith (2020) finds a 5% decline
> in manufacturing wages. This suggests that trade policy has distributional
> consequences.
>
> Immigration policy also affects labor markets. Jones (2021) documents wage
> compression in low-skill sectors. This indicates that immigration interacts
> with trade shocks."

**After (varied paragraph functions):**
> "Trade liberalization affects labor markets differently depending on who you
> ask — and when. Smith (2020) finds a 5% decline in manufacturing wages, but
> only in the first three years after liberalization.
>
> Why the temporary effect? One explanation: workers retrain. Another: firms
> relocate. The data can't distinguish between the two, which is exactly the
> gap this paper fills."

---

## Category 6: Domain-Specific Distortions

### 6.1 Causal Language Softening (Economics)
**What AI does:** Replaces causal claims with correlational language.
**Why it's bad:** If your identification strategy supports causal claims, don't
undermine it.

| Before | After |
|--------|-------|
| "The reform caused a 15% increase in enrollment." | "The reform was associated with a 15% increase in enrollment." |

### 6.2 Legal Precision Loss (Law)
**What AI does:** Replaces precise legal terms with informal language.
**Why it's bad:** Legal writing requires specificity.

| Before | After |
|--------|-------|
| "The court held that the statute was unconstitutional under strict scrutiny." | "The court found that the law did not meet constitutional standards." |

### 6.3 Clinical Detail Removal (Medicine)
**What AI does:** Removes specific dosages, protocols, or diagnostic criteria.
**Why it's bad:** Clinical writing requires reproducible detail.

---

## Detection Heuristic

After any revision, a quick check:

1. **Word count change:** If revision is 15%+ longer, likely added filler.
2. **First-person count:** If "I/we" decreased, likely de-personalized.
3. **Number count:** If specific numbers decreased, likely generalized.
4. **Hedge word count:** If "may/might/could/appears/suggests" increased,
   likely hedged.
5. **Read it aloud:** If it sounds like a textbook instead of your voice,
   revert.
