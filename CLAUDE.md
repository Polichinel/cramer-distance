# Cramér Distance Paper

Single-author methodology paper: "Forecast Evaluation with Observational Uncertainty: A Cramér-Distance Perspective." Targeting arXiv (stat.ME primary, cs.CY secondary).

## Layout

- `paper/` — LaTeX source. Build with `make` from inside `paper/`.
- `paper/sections/` — one file per section (01 intro through 08 conclusion, plus appendices).
- `tests/` — 66 falsification tests against paper content. Run with `uv run pytest tests/ -q` from repo root.
- `src/cramer_distance/` — Python implementation (constructors, scoring, real data pipeline).

## Writing harness

The editorial tracking system lives at `/home/simon/brain/2_projects/cramer-distance/_dev_materials/cramer_distance_paper/`:
- `DECISIONS.md` — 7 decisions, all implemented.
- `FINDINGS.md` — 24 findings from a 72-note readthrough. 7 landed, 6 rejected, 11 pending.
- `MANIFESTO.md` — strategic intent, audience, implicit/explicit tiers.

## Citation rule

Any new citations must be checked against the brain library at `~/brain/9_library/`. Papers not in the library must be acquired and read before citing. No hallucinated references.

## Current state (2026-05-23)

Paper compiles to 24 pages, 66/66 tests pass. All structural decisions resolved. See session log in `/home/simon/brain/2_projects/cramer-distance/index.md` for full history.
