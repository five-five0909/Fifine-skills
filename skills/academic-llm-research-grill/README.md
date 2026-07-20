# LLM Research Grill Skill

A ChatGPT Skill for rigorous self-grilling and research coaching around large language models, PyTorch, datasets, academic papers/books, and experiment design.

## What it does

This skill turns vague ML/LLM research confusion into structured pressure tests:

- research direction triage
- dataset structure interrogation
- PyTorch / Hugging Face / LLM implementation audit
- paper and research-book grilling
- experiment design and reproducibility review
- advisor/defense style questioning

## Project structure

```text
llm-research-grill/
├── SKILL.md
├── README.md
├── agents/
│   └── openai.yaml
├── scripts/
│   └── generate_grill_plan.py
├── references/
│   ├── dataset_audit.md
│   ├── literature_protocol.md
│   ├── pytorch_llm_audit.md
│   ├── question_bank.md
│   ├── research_design.md
│   ├── rubrics.md
│   └── session_templates.md
└── assets/
    ├── paper_card_template.md
    └── research_state_canvas.md
```

## Example prompts

- “Grill me on my LLM research direction. I only know I want to use PyTorch and a custom dataset.”
- “I have this dataset schema; attack it before I train.”
- “I am using Hugging Face Trainer with LoRA. Grill my setup.”
- “I read this paper; force me to connect it to my experiment.”
- “Pretend you are my advisor and make me defend my baseline/evaluation.”
