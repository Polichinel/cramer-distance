# Instantiation Checklist

Bootstrapped from base_docs templates on 2026-05-21.

---

## ADR Adaptation

### All adopted ADRs
- [x] Update Status from `--template--` to `Accepted` (or `Deferred` for ADR-004)
- [x] Fill in Date, Deciders fields

### Per-ADR adaptation
- [x] **ADR-000:** Updated `ADRs/` path to `docs/ADRs/`; adapted examples to methodology paper context
- [x] **ADR-001:** Defined 7 ontological categories: scoring functions, F_obs constructors, propriety verification, demonstration, real data pipeline, figures, paper
- [x] **ADR-002:** Defined 3-layer dependency structure (Foundation → Application → Output)
- [x] **ADR-003:** Adapted forbidden behavior examples to scoring metric domain
- [x] **ADR-004:** Deferred (as designed)
- [x] **ADR-005:** Adapted test taxonomy to green/falsification structure; beige team deferred
- [x] **ADR-007:** Grounded in actual extraction experience (triptych tissue, 3 falsification rounds)

### Skipped ADRs
- [x] Intent Contracts (006) — not adopted; repo is function-based, no complex classes
- [x] Observability (008) — not adopted; no logging infrastructure needed at this scale
- [x] Boundary Contracts (009) — not adopted; no configuration validation layer

---

## CICs
- [x] CIC infrastructure present (template + README)
- [x] No active contracts needed (function-based repo)

---

## Contributor Protocols
- [x] `carbon_based_agents.md` adapted for single-author + collaborator context
- [x] `silicon_based_agents.md` adapted with repo-specific forbidden operations
- [ ] Hardened protocol template — not included (standard protocols sufficient)

---

## Standards
- [x] `logging_and_observability_standard.md` — lightweight version appropriate for repo scale

---

## Risk Register
- [x] `reports/technical_risk_register.md` present with tier definitions

---

## Final Verification
- [x] No files have Status `--template--` (ADR-004 is `Deferred`, not template)
- [x] All cross-ADR references resolve to adopted ADRs
- [ ] Run `validate_docs.sh` to check internal consistency
