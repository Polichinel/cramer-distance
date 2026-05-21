
# ADR-002: Topology and Dependency Rules

**Status:** Accepted  
**Date:** 2026-05-21  
**Deciders:** Simon Polichinel von der Maase  

---

## Context

Without explicit dependency rules, modules accumulate coupling. In this repo the risk is concrete: `real_data.py` could start importing demo logic, `figures.py` could embed scoring computations, or the paper data directory could become an implicit API.

A clear rule is required to define **who may depend on whom**.

---

## Decision

This repository enforces a strict, directional dependency structure.

> Dependencies must follow declared architectural direction.  
> No component may depend on a layer above it.

---

## Layering

The repo has three layers, from bottom (stable, depended-upon) to top (derived, depending):

```
Layer 0 (Foundation):  classical_crps, fuzzy_crps, observation_uncertainty, propriety
Layer 1 (Application):  demo, real_data
Layer 2 (Output):        figures, paper/
```

**Rules:**
- Layer 1 may import from Layer 0.
- Layer 2 may import from Layer 0 and Layer 1.
- Layer 0 modules may depend on each other but must not import from Layer 1 or 2.
- No circular dependencies.

**The one exception:** `real_data.py` has a conditional import of `lab_core` (an external package). This is a declared, documented fallback — not an architectural dependency. When `lab_core` is unavailable, the module operates from pre-computed CSVs.

---

## Forbidden Patterns

- Scoring functions importing data loading code
- Figure generation computing statistics (it should consume pre-computed results)
- Demo module defining new F_obs constructors
- Paper LaTeX files depending on runtime code paths
- Any module reaching outside the repo for non-Python-package dependencies

---

## Consequences

### Positive
- Improved modularity
- Easier reasoning about change impact
- Safer refactoring of paper-specific code without touching the metric

### Negative
- May require passing results between layers explicitly rather than sharing state

These costs are accepted intentionally.

---

## Notes

This ADR defines structural direction of dependencies.  
It does not define semantic authority (ADR-003) or testing obligations (ADR-005).
