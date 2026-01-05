# 0001 - Use ADRs for significant decisions

## Context
We need a lightweight, durable way to capture architectural and workflow decisions that affect long-term maintenance. This repo will be operated by humans and AI agents, so clarity and history matter.

## Decision
We will use Architecture Decision Records (ADRs) for changes that:
- Introduce new tooling or processes.
- Alter architecture, data flow, or deployment assumptions.
- Create long-lived constraints or trade-offs.

ADRs live in `docs/adr/` and use the template in `docs/adr/TEMPLATE.md`.

## Consequences
- Decisions are recorded and discoverable.
- Reviewers can understand the "why" behind changes.
- Small overhead for documenting significant choices.
