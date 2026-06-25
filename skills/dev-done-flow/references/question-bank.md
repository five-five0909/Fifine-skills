# Dev Done Flow Question Bank

Use these only as needed. Ask at most five questions per turn.

## Classification

- Is this a new feature, bug diagnosis, refactor, architecture improvement, performance/security task, Java backend task, or LLM/Agent/RAG task?
- Is there an existing codebase, or is this greenfield?
- Is the expected output a design document, task plan, implementation, diagnosis, or release plan?

## Java Backend

- Which framework and project structure are used?
- Which APIs, DTOs, entities, database tables, and transactions are affected?
- Are idempotency, concurrency, permissions, cache, queues, migrations, or rollback involved?
- What tests should protect this change?

## LLM / Agent / RAG

- What are representative inputs and ideal outputs?
- Is RAG, tool calling, structured output, memory, or human approval needed?
- What bad cases should be captured in evaluation?
- What latency, cost, safety, hallucination, and observability constraints matter?

## Bug Diagnosis

- What is the symptom, expected behavior, and actual behavior?
- What are the reproduction steps and affected environment?
- What logs, errors, traces, recent changes, or suspicious code paths exist?
- What is the smallest failing test that would prove the bug?
