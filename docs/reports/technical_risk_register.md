# Technical Risk Register

**Status:** Active  
**Last updated:** 2026-06-26  

---

## Summary

| ID | Tier | Risk | Status |
|----|------|------|--------|
| C-01 | 3 | pyarrow not declared in dependencies | Mitigated |
| C-02 | 4 | README test count stale | Mitigated |
| C-03 | 4 | figures.py docstring lists 3 figures, generates 4 | Mitigated |
| C-04 | 2 | Dual time encodings in real_data join (1989 vs 1980 base) | Open |
| C-05 | 2 | fuzzy_crps public default grid truncates heavy tails | Open |
| C-06 | 2 | RVI Gumbel constructor untested; integer-key dummies dead post-aggregation | Open |
| C-07 | 2 | Results regenerable by author only (private paths, orphan CSVs) | Open |
| C-08 | 3 | CellMonthScores dataclass vestigial; scoring returns untyped dict | Open |
| C-09 | 3 | score_cell_month silently coerces out-of-order bounds | Open |

---

## Tier Definitions

### Tier 1 — Critical
Risk that would invalidate the paper's claims or produce silently wrong results. Must be resolved before submission.

### Tier 2 — Significant
Risk that weakens confidence in the results or limits reproducibility. Should be resolved or explicitly documented before submission.

### Tier 3 — Minor
Risk that affects convenience, documentation, or maintainability but not correctness. Address when practical.

### Tier 4 — Cosmetic
Documentation or quality observation with no correctness, reproducibility, or maintainability cost beyond a single developer.

---

## Entries

### C-01: pyarrow not declared in dependencies
**Tier:** 3  
**Source:** Falsification audit — execution round, probe E5  
**Trigger:** A developer installs dependencies via `uv sync`, provides source parquet in `data/`, and runs `uv run python -m cramer_distance.real_data`.  
**Location:** `pyproject.toml` (dependencies), `src/cramer_distance/real_data.py:97`  
**Narrative:** `real_data.py` calls `pd.read_parquet()` but neither `pyarrow` nor `fastparquet` is in declared dependencies. The module crashes with a raw `ImportError` about parquet engines before even attempting to read the data file. The README documents the `lab_core` requirement but not the parquet backend.  
**Mitigation:** Added `pyarrow` to `pyproject.toml` dependencies.  
**Status:** Mitigated  

---

### C-02: README test count stale
**Tier:** 4  
**Source:** Falsification audit — execution round, probe E3  
**Trigger:** A user clones the repo, runs `uv run pytest tests/`, and sees 60 pass instead of the documented 51.  
**Location:** `README.md:55`  
**Narrative:** README says "51 tests pass" but actual count is 60. The count was correct when written; 9 falsification test stubs were added in migration rounds 1-3 without updating the README.  
**Mitigation:** Updated README: 51 → 60.  
**Status:** Mitigated  

---

### C-03: figures.py docstring lists 3 figures, generates 4
**Tier:** 4  
**Source:** Falsification audit — execution round, probe E6  
**Trigger:** A developer reads the `figures.py` module docstring to understand what the module produces.  
**Location:** `src/cramer_distance/figures.py:8`  
**Narrative:** The docstring says "Three figures:" and lists 3, but `main()` calls 4 figure functions. The 4th (`figure_real_data_comparison`) was added when the real-data pipeline was built and the docstring was not updated.  
**Mitigation:** Updated docstring: "Three figures" → "Four figures" with real_data_comparison documented.  
**Status:** Mitigated  

---

### C-04: Dual time encodings in real_data join (1989 vs 1980 base)
**Tier:** 2  
**Source:** repo-assimilation (2026-06-26) — Phase 5 invariant I7, Phase 3  
**Trigger:** When a contributor regenerates HydraNet results via `python -m cramer_distance.real_data` (or edits either time-conversion constant), verify the prediction↔observation join in `score_hydranet` retains the expected number of rows (the printed "N cell-months after join").  
**Location:** `src/cramer_distance/real_data.py:46-53` (`_TIME_ORIGIN=23869` ↔ 1989-01), `src/cramer_distance/real_data.py:503-506` (`_month_id_to_year_month`, 1980 base)  
**Narrative:** Two distinct integer time encodings coexist in one module: the assembled-grid `time_id` (1989-01 origin), used only to filter the training window in `load_historical_stats`, and the prediction `month_id` (1980 origin) decoded in `score_hydranet`. The prediction↔observation join (`real_data.py:559`) matches on derived `(year, month)`; an off-by-base error produces either an empty join (visible as a count printout) or a *shifted* non-empty join that silently scores the wrong cell-months with no error. No assertion guards join cardinality. Borderline Tier 1 in the shifted-join case (silent result corruption); held at Tier 2 because the dominant failure mode is a visible empty join and the two encodings serve independent data sources rather than a required symmetry.  
**Mirrored:** Writing harness FINDINGS F-29 (paper §6.3 impact).  
**Status:** Open  

---

### C-05: fuzzy_crps public default grid truncates heavy tails
**Tier:** 2  
**Source:** repo-assimilation (2026-06-26) — Phase 5 invariant I2  
**Trigger:** When an external user calls `fuzzy_crps(f_pred, f_obs)` per the README usage example without overriding `grid_max`, on data whose CDF mass extends beyond 1000, verify the integral is not truncated (`f_pred(grid_max)` and `f_obs(grid_max)` ≈ 1).  
**Location:** `src/cramer_distance/fuzzy_crps.py:42-44` (`grid_min=0.0`, `grid_max=1000.0`, `grid_n=4001`)  
**Narrative:** The default integration grid `[0, 1000]` is a magic constant. LogNormal F_obs/F_pred for large `best` values can place non-trivial mass above 1000, truncating the integral and understating the score with no warning. Internal callers (`score_cell_month:262`, `demo`) override `grid_max` adaptively from the samples, so the paper's own results are not affected — but the public library default does not, and nothing asserts the grid covers both CDFs' support. Held at Tier 2 (silent for external users, but the repo's own pipeline mitigates via adaptive overrides).  
**Status:** Open  

---

### C-06: RVI Gumbel constructor untested; integer-key dummies dead post-aggregation
**Tier:** 2  
**Source:** repo-assimilation (2026-06-26) — Phase 6, Phase 5 invariant I8  
**Trigger:** When a contributor edits the Vesco Table A10 coefficients, the Gumbel mixture math, or the RVI samplers, verify behavior with a direct unit test (none currently exists; only static-CSV assertions would still pass).  
**Location:** `src/cramer_distance/observation_uncertainty.py:219-343` (`_TABLE_A10_*`, `_rvi_gumbel_params`, `f_obs_from_rvi_gumbel`, `sample_from_f_obs_rvi_gumbel`)  
**Narrative:** Constructor 4 (RVI Gumbel) has no direct unit tests; its only validation is `test_falsification_cramer_distance_hydranet.py`, which asserts on committed CSV fixtures that pass even if the generating code regresses — the primary residual risk. Separately, the vague-number dummies key on `int(y_reported)` exact match (`:264`), but `best` is a sum over aggregated events (`load_observations:103`), so dummy keys (2, 3, 13, …) rarely fire post-aggregation. This second behavior is **not** unintended-and-hidden: the paper explicitly discloses it as a unit-of-analysis mismatch (§7 discussion; Appendix B §B.4) with an argued conservative direction. The open code risk is therefore narrowed to the missing unit test plus the gap that F-09's σ verification (≈0.2–0.7) was computed on raw per-event ỹ, not the aggregated values the pipeline feeds the constructor. Both feed paper RVI reversal/concordance results. See also C-07 (CSV fixtures stand in for regeneration).  
**Mirrored:** Writing harness FINDINGS F-30 (relates to F-09 RVI verification).  
**Status:** Open  

---

### C-07: Results regenerable by author only (private paths, orphan CSVs)
**Tier:** 2  
**Source:** repo-assimilation (2026-06-26) — Phase 1, Phase 3  
**Trigger:** When a third party (reviewer, replicator) attempts full reproduction of `paper/data/*.csv` from source, verify every committed CSV has a producing code path in `real_data.main()` and that input data paths are not author-specific.  
**Location:** `src/cramer_distance/feature_frame_loader.py:28-32` (`VIEWS_FEATURE_FRAME_DIR` default `~/Documents/scripts/views_platform/...`), `paper/data/bright_starship_scores*.csv`, `paper/data/purple_alien_scores*.csv` vs `src/cramer_distance/real_data.py:658-695` (`main()` emits `real_data_scores*` and `hydranet_scores_*` only)  
**Narrative:** The regeneration path depends on a private VIEWS feature-frame directory defaulting to an author-specific absolute path, plus gitignored prediction frames under `data/predictions_purple_alien/`. Several committed result CSVs (`bright_starship_*`, `purple_alien_*`) have no producing code path in the current `main()`, indicating provenance drift between committed artifacts and the regeneration script. For a methodology paper targeting arXiv, this makes independent reproduction effectively author-only. See also C-06 (untested generators behind those CSVs).  
**Mirrored:** Writing harness FINDINGS F-31 (relates to F-26 bright_starship investigation).  
**Status:** Open  

---

### C-08: CellMonthScores dataclass vestigial; scoring returns untyped dict
**Tier:** 3  
**Source:** repo-assimilation (2026-06-26) — Phase 4  
**Trigger:** When a contributor edits the scoring output schema expecting `CellMonthScores` to be the contract, verify the actual keys returned by `score_cell_month` (a plain dict with a larger key set) and the columns `figures.py` reads.  
**Location:** `src/cramer_distance/real_data.py:221-239` (dataclass) vs `src/cramer_distance/real_data.py:302-315` (returned dict)  
**Narrative:** `CellMonthScores` is declared as the per-cell scores type but `score_cell_month` returns an untyped `dict` with a different, larger key set (adds rvi/bs fields). The dataclass is vestigial; the real contract is an untyped dict consumed positionally by `summarise` and downstream by `figures.py`, with no guard against schema drift between the pipeline output and the CSV reader (Phase 5 invariant I10).  
**Status:** Open  

---

### C-09: score_cell_month silently coerces out-of-order bounds
**Tier:** 3  
**Source:** repo-assimilation (2026-06-26) — Phase 5 invariant I3  
**Trigger:** When UCDP aggregation produces a cell-month where `best` falls outside `[low, high]`, verify whether the anomaly should surface rather than be repaired.  
**Location:** `src/cramer_distance/real_data.py:280-282` (`low_safe = min(low, best)`, `high_safe = max(high, best)`)  
**Narrative:** `f_obs_from_bounds` correctly raises on out-of-order bounds (`observation_uncertainty.py:54`), but `score_cell_month` pre-empts that guard by coercing `low_safe`/`high_safe` before the call. Genuine data-quality anomalies (best outside [low, high] after summation) are silently repaired rather than surfaced, masking upstream problems in the bounds-based Constructor 1 results.  
**Status:** Open  
