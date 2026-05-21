
# ADR-000: Use of Architecture Decision Records (ADRs)

**Status:** Accepted  
**Date:** 2026-05-21  
**Deciders:** Simon Polichinel von der Maase  
**Informed:** All contributors  

---

## Context

This repository contains a methodology paper and its reference implementation for forecast evaluation with observational uncertainty (Cramér distance reformulation of CRPS). It is single-authored but intended for public replication and review.

Many decisions — about metric conventions, constructor design, numerical verification strategies, and paper structure — are made under uncertainty and revised as the paper evolves. Without a shared record of *why* decisions were made, the project risks:
- Re-litigating settled questions across sessions
- Accidental reversals of critical design choices
- Losing context as the paper goes through review and revision
- Silicon-based agents reintroducing patterns that were deliberately rejected

We therefore use a lightweight but rigorous mechanism to document **significant decisions**, their **rationale**, and their **consequences**.

---

## Decision

We will use **Architecture Decision Records (ADRs)** to document significant technical, architectural, and conceptual decisions in this project.

ADRs are:
- Written in Markdown
- Stored in the repository under `docs/ADRs/`
- Numbered sequentially
- Treated as first-class project artifacts

An ADR records **a decision**, not a discussion or a design proposal.

---

## What Is an ADR?

An ADR is a short, structured document that captures:
- The context in which a decision was made
- The decision itself
- The rationale behind it
- The alternatives that were considered
- The consequences (positive and negative)

An ADR answers the question:

> *"Why is the system the way it is?"*

---

## When to Write an ADR

Write an ADR when making a decision that:
- Affects the metric's mathematical formulation or conventions
- Constrains how F_obs constructors work
- Changes the paper's claims or scope
- Introduces or accepts methodological debt
- Is likely to be questioned by a reviewer
- Has non-obvious trade-offs

Do **not** write ADRs for:
- Routine refactors
- Purely local implementation details
- LaTeX formatting choices

---

## What an ADR Is *Not*

An ADR is **not**:
- A full design document
- A tutorial or user guide
- A speculative roadmap
- A substitute for code comments
- A place to argue indefinitely

The goal is clarity and finality, not exhaustiveness.

---

## Structure and Template

All ADRs must follow the standard ADR template defined in `docs/ADRs/adr_template.md`.

Consistency matters more than perfection.

---

## Lifecycle of an ADR

ADRs have a status that reflects their lifecycle:

- **Proposed** — decision under consideration
- **Accepted** — decision is active and authoritative
- **Superseded** — replaced by a newer ADR
- **Deprecated** — decision remains but should no longer be used

Decisions are never deleted.  
If a decision changes, it is **superseded**, not erased.

---

## Relationship to Code

ADRs and code must agree.

- Code should implement the decision described in the ADR
- Significant deviations require a new ADR or an update
- ADRs should be referenced from code, issues, or PRs when relevant

If code and ADRs disagree, the ADR is the source of truth — or a new ADR is required.

---

## Consequences

### Positive
- Clearer decision-making
- Fewer repeated debates across sessions
- Easier onboarding for collaborators (Mike, reviewers)
- Better long-term coherence

### Negative
- Small upfront cost in writing
- Requires discipline to maintain

These costs are accepted intentionally.

---

## References

- `docs/ADRs/adr_template.md`
