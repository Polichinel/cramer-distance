# Technical Risk Register

**Status:** Active  
**Last updated:** 2026-05-22  

---

## Summary

| ID | Tier | Risk | Status |
|----|------|------|--------|
| C-01 | 3 | pyarrow not declared in dependencies | Mitigated |
| C-02 | 4 | README test count stale | Mitigated |
| C-03 | 4 | figures.py docstring lists 3 figures, generates 4 | Mitigated |

---

## Tier Definitions

### Tier 1 — Critical
Risk that would invalidate the paper's claims or produce silently wrong results. Must be resolved before submission.

### Tier 2 — Significant
Risk that weakens confidence in the results or limits reproducibility. Should be resolved or explicitly documented before submission.

### Tier 3 — Minor
Risk that affects convenience, documentation, or maintainability but not correctness. Address when practical.

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
