
# ADR-001: Ontology of the Repository

**Status:** Accepted  
**Date:** 2026-05-21  
**Deciders:** Simon Polichinel von der Maase  

---

## Context

This repository contains a methodology paper and its reference implementation. The paper proposes using the Cramér distance (a known quantity) for forecast evaluation when observations are uncertain. The code provides scoring functions, F_obs constructors, propriety verification, a demonstration pipeline, and figure generation.

Without an explicit ontology, it is easy for responsibilities to bleed across modules — scoring logic entering the data pipeline, plotting code computing statistics, or paper-specific hacks leaking into reusable functions.

---

## Decision

This repository defines a **closed set of conceptual categories** that are allowed to exist. Each category has a clear semantic role, an expected stability level, and explicit boundaries.

---

## Core Ontological Categories

### 1. Scoring Functions
**Modules:** `classical_crps`, `fuzzy_crps`  
**Purpose:** Compute CRPS and its Cramér-distance generalisation.  
**Authority:** Authoritative — these ARE the contribution.  
**Stability:** Stable.  
**Must not contain:** Heuristics, data loading, plotting, I/O.

### 2. F_obs Constructors
**Module:** `observation_uncertainty`  
**Purpose:** Build observational CDFs from data sources (bounds, parametric, weight-head).  
**Authority:** Authoritative — the three recipes are a stated contribution.  
**Stability:** Stable interface, extensible set (new constructors may be added).  
**Must not contain:** Scoring logic, data I/O.

### 3. Propriety Verification
**Module:** `propriety`  
**Purpose:** Numerical checks that the metric is consistent (minimised at truth).  
**Authority:** Derived — verifies scoring functions.  
**Stability:** Stable.  
**Must not contain:** Claims of analytical proof, paper-specific parameters.

### 4. Demonstration
**Module:** `demo`  
**Purpose:** Controlled examples showing ranking reversal under observational uncertainty.  
**Authority:** Derived — exercises scoring + constructors.  
**Stability:** Evolving (parameters may change as paper develops).  
**Must not contain:** Production logic, data loading.

### 5. Real Data Pipeline
**Module:** `real_data`  
**Purpose:** UCDP empirical comparison for the paper.  
**Authority:** Derived — depends on external data.  
**Stability:** Experimental (depends on data availability).  
**Must not contain:** Core metric logic, F_obs constructor definitions.

### 6. Figures
**Module:** `figures`  
**Purpose:** Paper visualisations.  
**Authority:** Derived — terminal output.  
**Stability:** Evolving.  
**Must not contain:** Computation beyond plotting.

### 7. Paper
**Directory:** `paper/`  
**Purpose:** LaTeX source, bibliography, pre-computed data for tables/figures.  
**Authority:** Authoritative — the deliverable.  
**Stability:** Evolving.  
**Must not contain:** Code, raw source data.

---

## Explicit Non-Entities

The following are **not allowed** as first-class concepts:

- No configuration system (parameters are function arguments)
- No orchestration layer (this is a library, not a pipeline)
- No model training or inference code
- No data storage or database abstractions
- Implicit or inferred semantics
- Objects that mix multiple ontological roles
- "Convenience" abstractions that hide meaning

If a concept matters, it must be explicit.

---

## Consequences

### Positive
- Shared vocabulary across contributors and sessions
- Clear review criteria for new code
- Prevents scope creep from paper-specific hacks into reusable functions

### Negative
- Requires upfront discipline
- Some refactors may be blocked until concepts are clarified

These trade-offs are accepted.

---

## Notes

This ADR defines *what exists*, not *how components depend on each other*.  
Dependency rules are defined in ADR-002.
