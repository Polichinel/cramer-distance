# Logging & Observability Standard

**Status:** Active  
**Governing ADRs:** ADR-003 (Authority of Declarations)  

---

## Scope

This repo is a small methodology package, not an operational pipeline. Logging requirements are minimal. This standard exists to establish the principle; details will evolve if the repo grows.

---

## Core Principle

Silent failure is prohibited (ADR-003). When a function encounters invalid input or a semantic error, it must raise an exception with a clear message. It must not return a default value, emit a warning, or continue silently.

---

## Current Practice

- Structural failures raise `ValueError` or `TypeError` with descriptive messages
- No logging framework is currently used (unnecessary at this scale)
- Print statements in `real_data.py` and `figures.py` are informational CLI output, not logging

---

## When to Revisit

If the repo grows to include:
- Long-running computations requiring progress tracking
- Pipeline orchestration requiring structured logging
- Production deployment requiring observability

then a proper logging standard should be adopted and this document updated.
