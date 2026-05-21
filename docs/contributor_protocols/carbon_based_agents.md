
# Carbon-Based Agent Protocol  
*(For contributors composed primarily of carbon, caffeine, and responsibility)*

**Status:** Active  
**Applies to:** All human contributors  
**Authority:** ADR-001 through ADR-005, ADR-007  

---

## Purpose

This protocol defines the responsibilities of **carbon-based agents** contributing to this repository.

Carbon-based agents are entrusted with intent, judgment, and architectural authority. With that trust comes responsibility.

---

## Core Principle: Stewardship of Intent

Carbon-based agents are **stewards of intent**, not merely authors of code.

Code may change. **Intent must not drift silently.**

---

## Ownership of Intent and Semantics

Carbon-based agents:
- own system intent and meaning,
- declare semantics explicitly,
- and are accountable for their correctness.

If a change alters the *meaning* of a component, a new ADR must be written or the change must not be merged.

---

## Fail-Loud Is a Moral Obligation

Silent failure is unacceptable. Introducing implicit behavior, fallback logic that hides errors, or ambiguity in scoring semantics is considered a defect, even if tests pass.

---

## Testing Is Part of the Change

A change is incomplete if it cannot be tested meaningfully. Carbon-based agents must ensure appropriate coverage across green team tests (correctness) and falsification tests (adversarial).

---

## Interaction with Silicon-Based Agents

Using silicon-based agents does **not** reduce responsibility.

Carbon-based agents must understand what the agent changed, verify changes against ADRs, and take full responsibility for the result.

---

## Non-Negotiable Expectations

Carbon-based agents must not:
- merge changes they do not understand,
- bypass tests under time pressure,
- defer intent clarification "until later",
- or shift responsibility to tools.
