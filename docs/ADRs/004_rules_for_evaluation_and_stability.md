
# ADR-004: Rules for Evolution and Stability

**Status:** Deferred  
**Date:** 2026-05-21  
**Deciders:** Simon Polichinel von der Maase  
**Informed:** All contributors  

---

## Context

The preceding ADRs establish:

- **ADR-001:** the ontology of the repository (what exists)
- **ADR-002:** the topology of the repository (how components may relate)
- **ADR-003:** semantic authority (who owns meaning and how it is declared)

What they do **not** yet define is how the system is allowed to **change over time**: which components are expected to be stable, which may evolve freely, what constitutes a breaking change, and when a new ADR is required.

---

## Decision

No decision is made at this time.

Rules governing stability, evolution, and backwards compatibility are **explicitly deferred**.

This ADR exists to:
- acknowledge the importance of this dimension
- reserve a place for a future, explicit decision
- prevent ad-hoc or implicit policies from emerging unnoticed

---

## Rationale for Deferral

At the time of writing:

- The paper is pre-submission and the metric's interface may still change
- The boundary between stable and experimental components is still settling
- Premature guarantees would either be ignored or constrain necessary exploration

Deferring this decision preserves design freedom while maintaining architectural honesty.

---

## Trigger Conditions for Reconsideration

This ADR should be revisited when one or more of the following become true:

- The paper is published and the code becomes a reference implementation
- External users depend on this repository
- Breaking changes begin to incur real coordination costs
- Contributors express uncertainty about what is safe to change

---

## Consequences

### Positive
- Avoids premature or brittle guarantees
- Preserves flexibility during paper development

### Negative
- Contributors must exercise judgment when making breaking changes

These consequences are accepted intentionally.

---

## Notes

This ADR is a placeholder by design. Until superseded, change is governed by ADR-001 through ADR-003 and by careful review.
