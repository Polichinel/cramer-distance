# Cramér Distance for Forecast Evaluation

Forecast evaluation with observational uncertainty. A generalization of the Continuous Ranked Probability Score (CRPS) to settings where the observed value itself is uncertain.

## Paper

von der Maase, S. (2026). *Forecast Evaluation with Observational Uncertainty: A Cramér-Distance Perspective.*

LaTeX sources in `paper/`. Pre-computed data in `paper/data/`.

## Installation

```bash
uv sync
```

## Usage

```python
from cramer_distance import fuzzy_crps, classical_crps, f_obs_from_parametric
```

## Figures

Regenerate all four PDF figures into `paper/figures/`:

```bash
uv run python -m cramer_distance.figures
```

## Compile the Paper

Requires a LaTeX distribution (pdflatex, bibtex):

```bash
cd paper && make
```

## Data

Pre-computed scoring results are committed in `paper/data/` and are sufficient for figure generation and paper compilation.

Source data for regeneration (UCDP parquet files) belongs in `data/` (gitignored). Regeneration requires `lab_core` from `views-datafactory`:

```bash
uv run python -m cramer_distance.real_data
```

## Tests

```bash
uv run pytest tests/
```

63 tests pass. 3 tests fail on paper-content TODOs (missing caveat paragraphs and table header renames in the LaTeX) — these are writing tasks, not code bugs.
