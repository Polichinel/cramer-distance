
# ADR-007: Silicon-Based Agents as Untrusted Contributors

**Status:** Accepted  
**Date:** 2026-05-21  
**Deciders:** Simon Polichinel von der Maase  

---

## Context

This repository is developed with significant assistance from silicon-based agents (Claude Code). The extraction from views-lab00, test generation, falsification audits, and documentation were all silicon-assisted.

Silicon-based agents differ fundamentally from carbon-based agents:

- They optimize for local plausibility, not global correctness
- They lack understanding of system intent and architectural constraints
- They may infer, invent, or collapse semantics silently
- They may introduce partial or structurally valid failures (e.g. truncation)

The extraction itself demonstrated this: bulk sed renames caught imports but missed narrative references ("Note B", triptych metadata, wrong authors in preamble). Three rounds of falsification audit were needed to surface these.

---

## Decision

Silicon-based agents are treated as **untrusted contributors**.

They are permitted to assist in code modification **only under explicit, documented constraints**, and **never as autonomous authorities**.

All silicon-based agent activity is subject to the same (or stricter) architectural rules as carbon-based agents, including:

- declared ontology (ADR-001),
- enforced topology (ADR-002),
- explicit semantic authority and fail-loud behavior (ADR-003),
- mandatory testing obligations (ADR-005).

The concrete operational rules are defined in `docs/contributor_protocols/silicon_based_agents.md`.

---

## Authority and Responsibility

Silicon-based agents:

- are not authoritative
- do not own intent
- do not establish semantics
- do not override architectural decisions

Simon remains fully responsible for the correctness of all changes, adherence to ADRs, and the consequences of merging silicon-assisted code.

---

## Consequences

### Positive
- Prevents silent architectural erosion
- Preserves semantic integrity under automation
- Makes responsibility explicit

### Negative
- Limits agent autonomy
- Requires active review of all agent output

These trade-offs are accepted intentionally.
