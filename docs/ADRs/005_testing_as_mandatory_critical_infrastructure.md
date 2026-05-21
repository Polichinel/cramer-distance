
# ADR-005: Testing as Mandatory Critical Infrastructure

**Status:** Accepted  
**Date:** 2026-05-21  
**Deciders:** Simon Polichinel von der Maase  

---

## Context

This repository supports a methodology paper whose claims must be empirically verifiable. The code is not just a reference implementation — it IS the evidence for the paper's claims. If the code silently produces wrong results, the paper's conclusions are wrong.

Given this, testing is not a convenience or a quality signal. It is **critical infrastructure**.

---

## Decision

This repository treats **testing as mandatory critical infrastructure**.

All non-trivial functionality **must be covered by tests**.

Tests are divided into **three complementary categories**:

- **Green team tests** (correctness) — does the metric compute what the paper says it does?
- **Red team tests** (adversarial) — can the metric be broken by edge cases, degenerate inputs, or parameter regimes?
- **Falsification tests** — can the paper's claims survive structured attempts to disprove them?

Each category serves a distinct purpose and **none may substitute for another**.

---

## Test Taxonomy for This Repo

### Green Team Tests (`test_cramer_distance.py`)

Correctness and consistency:
- Fuzzy CRPS with step F_obs recovers classical CRPS
- Fuzzy CRPS is zero when F_pred equals F_obs
- F_obs constructors produce valid CDFs
- Propriety verification finds minimum at truth
- Demo produces expected ranking reversal

### Red Team / Falsification Tests (`test_falsification_*.py`)

Structured adversarial probes:
- **arxiv_readiness** — does the paper have an abstract, are bib entries used, are arXiv tags correct?
- **claim_sufficiency** — do the paper's claims hold across parameter regimes?
- **expert_acceptance** — would a domain expert accept the notation and conventions?
- **figures** — do figure labels match what's plotted?
- **notation** — is mathematical notation consistent?
- **novelty** — does the paper properly cite prior work?
- **reproducibility** — do paper statistics match code output?
- **migration** — is the repo self-contained and correctly extracted?

### Beige Team Tests (not yet present)

Realistic misuse: what happens when a user applies the metric to data it wasn't designed for? This category is deferred until the paper is published and external users exist.

---

## Relationship to Other ADRs

- **ADR-001 (Ontology):** tests must respect declared categories and stability expectations
- **ADR-002 (Topology):** tests must not bypass architectural boundaries
- **ADR-003 (Authority):** tests must fail loudly on semantic ambiguity

---

## Enforcement Rules

- Code that affects the metric or paper claims **must not be merged without tests**
- Tests that only cover happy paths are insufficient
- Known failure modes that are untested must be tracked (as xfail stubs or in the risk register)

---

## Consequences

### Positive
- Paper claims are machine-verifiable
- Prevents silent regression during revision
- Structured falsification catches problems before reviewers do

### Negative
- Higher upfront development cost
- Some paper edits require updating tests

These costs are accepted intentionally.
