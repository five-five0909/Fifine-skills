#!/usr/bin/env python3
"""
Topic Refiner - Research Question Narrowing Tool
Based on Chapter 7 of "Writing is a Craft" by Liu Junqiang
"""

import argparse
import json
import sys
from dataclasses import dataclass, asdict
from typing import Optional
from pathlib import Path

try:
    import yaml
except ImportError:
    yaml = None


@dataclass
class TopicCard:
    """Topic card data structure"""
    domain: str
    subdomain: str
    research_question: str
    # Three-step questioning method
    step1_topic: str
    step2_why: str
    step2_what_factors: str
    step2_how: str
    step3_value: str
    # Funnel narrowing
    who: str
    when: str
    where: str
    what_aspect: str
    # Chat test
    chat_test_passed: Optional[bool] = None
    chat_test_notes: str = ""

    def to_markdown(self) -> str:
        return f"""# Topic Card

## Basic Info
| Dimension | Content |
|-----------|---------|
| **Domain** | {self.domain} |
| **Subdomain** | {self.subdomain} |
| **Research Question** | {self.research_question} |

## Three-Step Questioning

### Step 1: Topic
> I want to research ({self.step1_topic})

### Step 2: Focused Questions
1. **Why/Difference**: {self.step2_why}
2. **What Factors**: {self.step2_what_factors}
3. **How (Mechanism)**: {self.step2_how}

### Step 3: Value Connection
> Answering these questions helps {self.step3_value}

## Funnel Narrowing
| Dimension | Narrowed Scope |
|-----------|----------------|
| **Who (Subject)** | {self.who} |
| **When (Time)** | {self.when} |
| **Where (Scene)** | {self.where} |
| **What (Aspect)** | {self.what_aspect} |

## Chat Test
- Passed: {"Yes" if self.chat_test_passed else "No" if self.chat_test_passed is False else "Pending"}
- Notes: {self.chat_test_notes}
"""

    def to_json(self) -> str:
        return json.dumps(asdict(self), ensure_ascii=False, indent=2)


def load_config(config_path: str = "config.yaml") -> dict:
    path = Path(__file__).parent / config_path
    if path.exists() and yaml:
        with open(path, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f)
    return {"domains": {}}


def interactive_refine() -> TopicCard:
    print("=" * 60)
    print("  Topic Refiner - Three-Step + Funnel Method")
    print("=" * 60)
    print()

    print("[Step 0] Identify your research domain")
    domain = input("Domain (e.g., Deep Learning / Education / Economics): ").strip()
    subdomain = input("Subdomain (e.g., LLM / Curriculum Design / Labor Econ): ").strip()
    print()

    print("[Step 1] Write your broad topic")
    step1 = input("I want to research (what in " + domain + "?): ").strip()
    print()

    print("[Step 2] Focus on specific questions")
    print('  Use the "some... while others..." pattern')
    step2_why = input("Why do some ____ while others ____?: ").strip()
    step2_what = input("What factors influence this result?: ").strip()
    step2_how = input("What is the mechanism between factors and result?: ").strip()
    print()

    print("[Step 3] Connect to broader value")
    step3 = input("Answering these questions helps ____ solve ____: ").strip()
    print()

    print("[Funnel Narrowing] Narrow with 4 dimensions")
    who = input("Subject Who (people/model/dataset): ").strip()
    when = input("Time When: ").strip()
    where = input("Scene Where (region/application): ").strip()
    what_aspect = input("Aspect What (specific focus): ").strip()
    print()

    question = f"{what_aspect}: {step2_why}"

    print("[Result] Your research question framework")
    print(f"  Suggested: {question}")
    print()

    chat_input = input("Chat test - would friends discuss this? (y/n): ").strip().lower()
    chat_passed = chat_input in ('y', 'yes')
    chat_notes = "" if chat_passed else input("Chat test notes: ").strip()

    return TopicCard(
        domain=domain,
        subdomain=subdomain,
        research_question=question,
        step1_topic=step1,
        step2_why=step2_why,
        step2_what_factors=step2_what,
        step2_how=step2_how,
        step3_value=step3,
        who=who,
        when=when,
        where=where,
        what_aspect=what_aspect,
        chat_test_passed=chat_passed,
        chat_test_notes=chat_notes,
    )


def quick_refine(domain: str, subdomain: str = "", topic: str = "") -> TopicCard:
    config = load_config()
    domain_config = config.get("domains", {}).get(domain, {})
    examples = domain_config.get("examples", [])

    if examples and not topic:
        ex = examples[0]
        return TopicCard(
            domain=domain,
            subdomain=subdomain or ex.get("subdomain", ""),
            research_question=ex.get("question", ""),
            step1_topic=ex.get("step1", ""),
            step2_why=ex.get("step2_why", ""),
            step2_what_factors=ex.get("step2_what", ""),
            step2_how=ex.get("step2_how", ""),
            step3_value=ex.get("step3", ""),
            who=ex.get("who", ""),
            when=ex.get("when", ""),
            where=ex.get("where", ""),
            what_aspect=ex.get("what", ""),
        )

    return TopicCard(
        domain=domain,
        subdomain=subdomain,
        research_question="(to fill)",
        step1_topic=topic or "(to fill)",
        step2_why="(to fill)",
        step2_what_factors="(to fill)",
        step2_how="(to fill)",
        step3_value="(to fill)",
        who="(to fill)",
        when="(to fill)",
        where="(to fill)",
        what_aspect="(to fill)",
    )


def main():
    parser = argparse.ArgumentParser(
        description="Research question narrowing tool",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python topic_refiner.py --interactive
  python topic_refiner.py -d Deep Learning -s LLM
  python topic_refiner.py -d Deep Learning -s LLM -o json
        """
    )
    parser.add_argument("--interactive", "-i", action="store_true",
                        help="Interactive guided mode")
    parser.add_argument("--domain", "-d", type=str, default="",
                        help="Research domain")
    parser.add_argument("--subdomain", "-s", type=str, default="",
                        help="Subdomain")
    parser.add_argument("--topic", "-t", type=str, default="",
                        help="Specific topic")
    parser.add_argument("--output", "-o", type=str, choices=["md", "json"],
                        default="md", help="Output format")

    args = parser.parse_args()

    if args.interactive:
        card = interactive_refine()
    elif args.domain:
        card = quick_refine(args.domain, args.subdomain, args.topic)
    else:
        parser.print_help()
        sys.exit(1)

    if args.output == "json":
        print(card.to_json())
    else:
        print(card.to_markdown())

    output_dir = Path(__file__).parent / "output"
    output_dir.mkdir(exist_ok=True)

    if args.output == "json":
        output_file = output_dir / "topic_card.json"
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(card.to_json())
    else:
        output_file = output_dir / "topic_card.md"
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(card.to_markdown())

    print(f"\nSaved to: {output_file}")


if __name__ == "__main__":
    main()
