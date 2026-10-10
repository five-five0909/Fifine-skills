# Domain-Specific Presets

Each preset defines which sections of a paper are "locked by default" — meaning
the AI should fix grammar and formatting only, without rephrasing arguments,
softening claims, or restructuring logic.

Users activate a preset by saying "Use [domain] preset" or the skill
auto-detects based on context.

---

## Economics

**Locked sections:**
- **Results interpretation.** The author's reading of regression coefficients,
  significance levels, and economic magnitudes. These are core academic claims.
- **Identification strategy justification.** Reasoning for why an instrument
  is valid, why parallel trends hold, or why a discontinuity is sharp. Do not
  soften "we argue that X is exogenous because..." into "it may be reasonable
  to suggest..."
- **Contribution statements.** Claims about what the paper adds to the literature.
  These define the paper's value proposition.
- **Robustness assessments.** If the author says results are robust, do not add
  hedging. If they acknowledge a limitation, do not amplify it.
- **Policy implications.** The author's judgment about what the findings mean
  for policy.

**Common AI mistakes in economics:**
- Replacing "causes" with "is associated with" when the identification strategy
  supports causal language
- Adding "further research is needed" to every limitation
- Softening coefficient interpretations ("large" → "moderate")
- Replacing specific estimator names (CSDID, rdrobust) with generic terms

---

## Law

**Locked sections:**
- **Legal reasoning chains.** The logical steps from statute/precedent to
  conclusion. Restructuring breaks the chain.
- **Case citation context.** Why a case is cited and what it stands for. Do not
  paraphrase holdings.
- **Jurisdictional specificity.** References to specific courts, circuits, or
  statutory provisions. Do not generalize "the Ninth Circuit held" to "courts
  have found."
- **Statutory interpretation.** Analysis of specific statutory language. The
  exact words matter.
- **Doctrinal arguments.** Application of legal tests (strict scrutiny, rational
  basis, etc.) to facts.

**Common AI mistakes in law:**
- Replacing precise legal terms ("proximate cause") with informal language
  ("related to")
- Removing pin cites (specific page numbers in case citations)
- Generalizing holdings across jurisdictions
- Softening "the court held" to "the court suggested"

---

## Medicine / Clinical Research

**Locked sections:**
- **Clinical findings.** Specific measurements, lab values, imaging results.
- **Diagnostic reasoning.** The chain from symptoms to differential diagnosis
  to working diagnosis.
- **Treatment protocols.** Dosages, frequencies, durations, routes of
  administration.
- **Patient-specific observations.** Case-specific details that distinguish
  this patient/cohort from general populations.
- **Statistical results.** Hazard ratios, confidence intervals, p-values,
  NNT/NNH.

**Common AI mistakes in medicine:**
- Removing specific dosages ("500mg BID" → "appropriate dosing")
- Generalizing diagnostic criteria
- Adding disclaimers that weaken evidence-based recommendations
- Replacing precise anatomical terms with lay language

**Error flagging for locked clinical content:** Locking protects precise detail
from being watered down, but it must not silently preserve dangerous errors.
If a locked section contains a clinically implausible value (e.g., a dosage
10x above standard range, a contradictory lab result), flag it:
> "This section is locked, but [specific concern]. Want me to fix it, or is
> it intentional?"
Never silently protect a potential patient-safety issue.

---

## Humanities

**Locked sections:**
- **Authorial voice.** In humanities, voice IS the argument. The way something
  is said matters as much as what is said.
- **Interpretive arguments.** The author's reading of a text, event, or
  cultural phenomenon. These are inherently subjective and personal.
- **Close reading passages.** Detailed analysis of specific textual evidence.
  The precision of engagement with primary sources is the scholarship.
- **Theoretical positioning.** How the author situates their work relative to
  theoretical frameworks (Marxist, feminist, postcolonial, etc.).
- **Rhetorical choices.** Deliberate use of metaphor, irony, or stylistic
  devices. These are features, not flaws.

**Common AI mistakes in humanities:**
- Flattening rhetorical complexity into plain statements
- Replacing interpretive language with descriptive language
- Removing first-person scholarly voice
- Treating theoretical positions as claims that need hedging

---

## STEM (Natural Sciences / Engineering)

**Locked sections:**
- **Methodology descriptions.** Exact procedures, equipment, parameters,
  software versions. Reproducibility depends on specificity.
- **Data interpretations.** The author's reading of figures, spectra, or
  experimental results.
- **Technical specifications.** Dimensions, tolerances, materials, conditions.
- **Measurement details.** Instruments, calibration procedures, error bounds.
- **Mathematical derivations.** Do not "simplify" steps in a proof or
  derivation. Each step exists for a reason.

**Common AI mistakes in STEM:**
- Rounding precise measurements ("3.7 ± 0.2 nm" → "approximately 4 nm")
- Removing software version numbers or parameter settings
- Generalizing specific experimental conditions
- "Simplifying" mathematical notation in ways that lose information

---

## Psychology

**Locked sections:**
- **Statistical reporting.** Exact test statistics, degrees of freedom, effect
  sizes, confidence intervals. APA format requires precise reporting.
- **Operationalizations.** How constructs were measured — scale names, item
  counts, anchors. These define what was actually studied.
- **Participant descriptions.** Sample demographics, recruitment methods,
  inclusion/exclusion criteria. Reproducibility depends on specificity.
- **Theoretical framing.** The author's positioning within a specific
  theoretical tradition (cognitive, behavioral, psychodynamic, etc.).

**Common AI mistakes in psychology:**
- Rounding effect sizes ("d = 0.43" → "a moderate effect")
- Removing APA-mandated reporting elements (exact p-values, CIs)
- Generalizing specific scale names ("the Beck Depression Inventory-II" → "a depression measure")
- Softening pre-registered hypotheses after results are known

---

## Political Science

**Locked sections:**
- **Causal identification.** The argument for why the design identifies a
  causal effect — natural experiments, instrumental variables, regression
  discontinuity justifications.
- **Institutional descriptions.** Specific rules, laws, electoral systems, or
  political structures that underpin the research design. Getting these wrong
  invalidates the paper.
- **Case selection rationale.** Why these countries/elections/legislatures were
  chosen. This is a methodological argument, not a formatting choice.
- **Normative claims.** When the author makes explicit value judgments about
  policy or institutional design, those are deliberate positions.

**Common AI mistakes in political science:**
- Softening causal claims backed by strong identification
- Generalizing country-specific institutional details
- Replacing precise electoral/legislative terminology with informal language
- Adding false balance to normative arguments ("while others argue...")

---

## Education

**Locked sections:**
- **Intervention descriptions.** What was taught, how, for how long, by whom.
  The intervention IS the contribution — vague descriptions make it
  unreplicable.
- **Assessment instruments.** Which tests, rubrics, or observational protocols
  were used. Names and versions matter.
- **Effect sizes and practical significance.** Authors in education often
  distinguish statistical significance from educational significance. Preserve
  that distinction.
- **Equity and context framing.** How the author positions the work relative
  to equity, access, or social justice goals. These are deliberate framings.

**Common AI mistakes in education:**
- Generalizing specific curriculum or pedagogy descriptions
- Removing practical significance discussion in favor of p-values only
- Softening equity-related claims or removing critical framing
- Replacing specific assessment names with generic terms

---

## Custom Preset

Users can create their own preset by saying:
> "Lock [section type 1], [section type 2], and [section type 3] by default."

The skill will apply these locks in all subsequent revisions until the user
changes the preset or says "unlock everything."

---

## Interdisciplinary Work

For blended fields (law-and-economics, medical humanities, computational
social science, etc.), combine the relevant presets. If locks conflict — e.g.,
humanities wants to protect rhetorical voice while STEM wants to protect
technical precision — ask the user which takes priority for the specific
section being revised.

Do not guess. Interdisciplinary writing is where presets are most likely to
get in the way, so ask explicitly.
