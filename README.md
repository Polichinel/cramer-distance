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

## Tests

```bash
uv run pytest tests/
```
