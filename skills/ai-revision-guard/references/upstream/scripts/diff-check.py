#!/usr/bin/env python3
"""
diff-check.py — Post-revision quality checker for revision-guard.

Compares original text against revised text and flags homogenization signals.
Usage:
    python scripts/diff-check.py original.txt revised.txt
    python scripts/diff-check.py --text "original" "revised"

Checks:
    1. Word count change (>15% increase = likely filler added)
    2. First-person pronoun change (decrease = de-personalization)
    3. Specific number count (decrease = generalization)
    4. Hedge word density (increase = confidence erosion)
    5. Sentence length variance (decrease = structural homogenization)
"""

import sys
import re
import argparse
from pathlib import Path


def count_words(text: str) -> int:
    return len(text.split())


def count_first_person(text: str) -> int:
    pattern = r'\b(I|we|my|our|me|us)\b'
    return len(re.findall(pattern, text, re.IGNORECASE))


def count_numbers(text: str) -> int:
    pattern = r'\b\d+\.?\d*%?\b'
    return len(re.findall(pattern, text))


def count_hedge_words(text: str) -> int:
    hedges = [
        r'\bmay\b', r'\bmight\b', r'\bcould\b', r'\bperhaps\b',
        r'\bappears?\b', r'\bsuggests?\b', r'\bpossibly\b',
        r'\bpotentially\b', r'\bseems?\b', r'\bapproximately\b',
        r'\bbroadly\b', r'\bgenerally\b', r'\btends?\b',
        r'\bit is worth noting\b', r'\bit is important to\b',
    ]
    total = 0
    for h in hedges:
        total += len(re.findall(h, text, re.IGNORECASE))
    return total


def sentence_length_variance(text: str) -> float:
    sentences = re.split(r'[.!?]+', text)
    sentences = [s.strip() for s in sentences if s.strip()]
    if len(sentences) < 2:
        return 0.0
    lengths = [len(s.split()) for s in sentences]
    mean = sum(lengths) / len(lengths)
    variance = sum((l - mean) ** 2 for l in lengths) / len(lengths)
    return variance


def analyze(original: str, revised: str) -> dict:
    results = {}

    # 1. Word count change
    orig_wc = count_words(original)
    rev_wc = count_words(revised)
    wc_change = (rev_wc - orig_wc) / orig_wc * 100 if orig_wc > 0 else 0
    results['word_count'] = {
        'original': orig_wc,
        'revised': rev_wc,
        'change_pct': round(wc_change, 1),
        'flag': abs(wc_change) > 15,
        'message': f"Word count changed {wc_change:+.1f}%"
                   + (" — likely filler added" if wc_change > 15 else "")
                   + (" — content may have been cut" if wc_change < -15 else "")
    }

    # 2. First-person pronouns
    orig_fp = count_first_person(original)
    rev_fp = count_first_person(revised)
    fp_decreased = rev_fp < orig_fp
    results['first_person'] = {
        'original': orig_fp,
        'revised': rev_fp,
        'flag': fp_decreased and orig_fp > 0,
        'message': f"First-person pronouns: {orig_fp} → {rev_fp}"
                   + (" — voice may be erased" if fp_decreased and orig_fp > 0 else "")
    }

    # 3. Specific numbers
    orig_nums = count_numbers(original)
    rev_nums = count_numbers(revised)
    nums_decreased = rev_nums < orig_nums
    results['numbers'] = {
        'original': orig_nums,
        'revised': rev_nums,
        'flag': nums_decreased and orig_nums > 0,
        'message': f"Specific numbers: {orig_nums} → {rev_nums}"
                   + (" — may have generalized" if nums_decreased and orig_nums > 0 else "")
    }

    # 4. Hedge words
    orig_hedges = count_hedge_words(original)
    rev_hedges = count_hedge_words(revised)
    hedges_increased = rev_hedges > orig_hedges
    results['hedge_words'] = {
        'original': orig_hedges,
        'revised': rev_hedges,
        'flag': hedges_increased,
        'message': f"Hedge words: {orig_hedges} → {rev_hedges}"
                   + (" — confidence may be eroded" if hedges_increased else "")
    }

    # 5. Sentence length variance
    orig_var = sentence_length_variance(original)
    rev_var = sentence_length_variance(revised)
    var_decreased = rev_var < orig_var * 0.5  # more than 50% reduction
    results['sentence_variance'] = {
        'original': round(orig_var, 1),
        'revised': round(rev_var, 1),
        'flag': var_decreased and orig_var > 0,
        'message': f"Sentence length variance: {orig_var:.1f} → {rev_var:.1f}"
                   + (" — sentences becoming uniform" if var_decreased and orig_var > 0 else "")
    }

    # Overall
    flags = sum(1 for r in results.values() if r['flag'])
    results['summary'] = {
        'flags_triggered': flags,
        'total_checks': 5,
        'homogenization_warning': flags >= 2,
        'verdict': "HOMOGENIZATION WARNING" if flags >= 2
                   else "MINOR CONCERNS" if flags == 1
                   else "CLEAN"
    }

    return results


def main():
    parser = argparse.ArgumentParser(
        description="Check for homogenization signals between original and revised text."
    )
    parser.add_argument('--text', nargs=2, metavar=('ORIGINAL', 'REVISED'),
                        help='Pass original and revised text directly as arguments')
    parser.add_argument('files', nargs='*',
                        help='Two file paths: original.txt revised.txt')

    args = parser.parse_args()

    if args.text:
        original, revised = args.text
    elif len(args.files) == 2:
        original = Path(args.files[0]).read_text()
        revised = Path(args.files[1]).read_text()
    else:
        print("Usage: python diff-check.py original.txt revised.txt")
        print("       python diff-check.py --text 'original' 'revised'")
        sys.exit(1)

    results = analyze(original, revised)

    print("\n=== Revision Guard: Diff Check ===\n")
    for key, value in results.items():
        if key == 'summary':
            continue
        flag = " ⚠️" if value['flag'] else " ✓"
        print(f"  {flag} {value['message']}")

    summary = results['summary']
    print(f"\n  {'⚠️' if summary['homogenization_warning'] else '✓'} "
          f"Verdict: {summary['verdict']} "
          f"({summary['flags_triggered']}/{summary['total_checks']} checks flagged)")
    print()


if __name__ == '__main__':
    main()
