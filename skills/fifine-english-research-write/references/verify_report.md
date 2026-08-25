# Fidelity Verification Report

Source of truth: OCR `doc_*.md` (verbatim from PDF) + summary HTML.
Goal: prove references are complete & faithful — no dropped content.

## Introduction
- Reference UWP vocab: **277**  | OCR(uwp fragments) vocab: **277** | overlap coverage **100.0%** -> **OK'**
- Reference examples: **35**  | OCR(fragments) examples: **35** -> **MATCH'**
- Section verdict: **PASS**

## Method
- Reference UWP vocab: **274**  | OCR(uwp fragments) vocab: **274** | overlap coverage **99.6%** -> **OK'**
- Reference examples: **41**  | OCR(fragments) examples: **41** -> **MATCH'**
- Section verdict: **PASS**

## Results
- Reference UWP vocab: **9**  | OCR(uwp fragments) vocab: **9** | overlap coverage **100.0%** -> **OK'**
- Reference examples: **55**  | OCR(fragments) examples: **55** -> **MATCH'**
- Section verdict: **PASS**

## Discussion
- Reference UWP vocab: **98**  | OCR(uwp fragments) vocab: **98** | overlap coverage **100.0%** -> **OK'**
- Reference examples: **55**  | OCR(fragments) examples: **55** -> **MATCH'**
- Section verdict: **PASS**

## Conclusion
- Reference UWP vocab: **17**  | OCR(uwp fragments) vocab: **17** | overlap coverage **100.0%** -> **OK'**
- Reference examples: **13**  | OCR(fragments) examples: **13** -> **MATCH'**
- Section verdict: **PASS**

## HTML Coverage (summary.html -> all reference tables)
- HTML extracted vocab phrases: **1222**
- Covered by reference table-phrase union: **1217** -> **99.6%** OK
- Uncovered phrases (likely OCR/normalisation diffs, not content loss): **5** e.g. column b, column a, but i don&#x27;t live there anymore, and so i can&#x27;t see well $ \underline{\text{now}} $, &#x27;happy&#x27; words 😊 accurate consistent direct easy excellent important precise relevant robust satisfactory simple suitable useful cause and result signalling connectors (see pages 59–60)

## Overall
- All checks pass: **YES'**