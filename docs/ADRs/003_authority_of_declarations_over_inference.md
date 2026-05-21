
# ADR-003: Authority of Declarations Over Inference

**Status:** Accepted  
**Date:** 2026-05-21  
**Deciders:** Simon Polichinel von der Maase  

---

## Context

In a repo that implements a scoring metric, the same concept appears in multiple forms: a mathematical definition in the paper, a function signature in code, numerical verification parameters, and demonstration defaults. When these diverge, the system can silently produce misleading results — a scoring function that doesn't match the paper's formula, or a demonstration that uses parameters inconsistent with the verification.

---

## Decision

In this repository:

> **All meaningful semantics must be explicitly declared.  
> Inference of semantics across component boundaries is forbidden.**

When multiple representations of the same concept exist, **the paper's mathematical definition is the source of truth** for the metric. Code implements the declared definition; tests verify the implementation against it.

If required semantics are missing, ambiguous, or contradictory, the system **must not guess**.

---

## Global Invariant: Fail Loud on Semantic Ambiguity

**Silent failure is considered a bug.**

Whenever required semantics are missing, ambiguous, or contradictory, the system must fail loudly and immediately. This includes:
- Raising explicit runtime errors
- Failing validation or consistency checks
- Refusing to proceed without explicit declaration

Warning-only behavior, implicit fallbacks, or "best-effort" inference are **forbidden** for any decision-relevant semantics.

---

## Examples of Forbidden Behavior

- Inferring the F_obs distribution family from variable names
- Guessing grid bounds from data rather than requiring explicit declaration
- Proceeding with scoring when F_obs returns values outside [0, 1]
- Silently substituting a default sigma when none is provided
- Computing the Cramér distance with a convention (integral vs. square root) that differs from the paper's stated convention

If behavior matters, it must be declared.

---

## Consequences

### Positive
- Eliminates silent semantic drift between paper and code
- Improves reproducibility
- Makes disagreements explicit and resolvable
- Enables principled failure under uncertainty

### Negative
- Requires more explicit function arguments (no magic defaults)
- Some convenience patterns are disallowed
- Errors surface earlier and more frequently

These costs are accepted intentionally.

---

## Notes

This ADR does not define what concepts exist (ADR-001) or how components depend on each other (ADR-002). It defines **who is allowed to say what something means**, and mandates **loud failure over silent misinterpretation**.
