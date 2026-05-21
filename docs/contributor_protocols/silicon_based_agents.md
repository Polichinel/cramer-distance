
# Silicon-Based Agent Protocol  
*(For contributors composed primarily of silicon, statistics, and confidence)*

**Status:** Active  
**Applies to:** All automated or AI-assisted code modification  
**Authority:** ADR-007 (Silicon-Based Agents as Untrusted Contributors)

---

## Purpose

This document defines **mandatory operational constraints** under which silicon-based agents may interact with this repository.

Silicon-based agents are powerful but unsafe by default. This protocol prevents silent semantic corruption, architectural erosion, and responsibility laundering.

---

## Threat Model

Silicon-based agents are assumed to:

- optimize for local plausibility, not global correctness,
- infer intent when it is not explicitly declared,
- collapse abstractions for convenience,
- silently omit or truncate content,
- produce outputs that *look valid* while being semantically incomplete.

---

## Global Rules (Non-Negotiable)

Silicon-based agents:

- are not authoritative
- do not own intent
- do not establish or infer semantics
- do not override ADRs

All silicon-based agent-assisted changes must comply with ADR-001 through ADR-005 and ADR-007.

---

## Allowed Operations

Silicon-based agents **may**:

- Perform scoped refactors within a single module
- Add or update tests that reflect declared intent
- Implement changes explicitly requested by Simon
- Make mechanical changes (renaming, formatting)
- Run falsification audits

---

## Forbidden Operations

Silicon-based agents **must not**:

- Modify the mathematical definition of the scoring functions without explicit instruction
- Infer F_obs constructor behaviour from naming conventions
- Cross layer boundaries (ADR-002)
- Remove validation or fail-loud behavior
- Refactor multiple layers in a single change
- Make "helpful" assumptions when required information is missing

If a silicon-based agent cannot proceed without guessing, it must stop.

---

## Anti-Truncation Rule

Silicon-based agents must use targeted edits for existing files. Full-file rewrites are forbidden. When modifying a file: read first, identify a precise edit location, apply a minimal replacement.

---

## Review Posture

Silicon-based agent-generated code must be reviewed with **heightened scrutiny**. Reviewers should assume intent may be misunderstood and semantics may have been altered unintentionally.

Responsibility remains fully with Simon.
