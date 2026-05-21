"""Side-by-side comparison of classical and fuzzy CRPS on the same forecasts.

The demonstration is constructed to make the difference visible:

1. **Setup.** Two forecasters predict the same noisy observation y. The
   first is a "tight" forecaster (narrow distribution centered on the
   reported value). The second is an "honest" forecaster (wider
   distribution that reflects the genuine uncertainty about y).

2. **Classical CRPS.** Both forecasts are scored against the step
   indicator at y. The tight forecaster wins because the integrand
   (F_pred - 1{y ≤ z})² is smaller for narrow predictions near y.

3. **Fuzzy CRPS.** Both forecasts are scored against a smooth F_obs
   that captures the actual observational uncertainty. The honest
   forecaster wins because its distribution matches F_obs, while the
   tight forecaster's narrow shape fails to overlap F_obs's tails.

This is the ranking reversal that motivates fuzzy CRPS: the tight
forecaster appears better under classical CRPS but worse under a metric
that respects observational uncertainty.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from scipy.stats import norm as _norm_dist

from cramer_distance.classical_crps import classical_crps
from cramer_distance.fuzzy_crps import (
    empirical_cdf_from_samples,
    fuzzy_crps,
    step_cdf_at,
)
from cramer_distance.observation_uncertainty import f_obs_from_bounds, f_obs_from_parametric


@dataclass(frozen=True)
class DemoResult:
    """Side-by-side comparison of classical and fuzzy CRPS for two forecasters."""

    y: float
    relative_sigma: float
    tight_classical: float
    tight_fuzzy: float
    honest_classical: float
    honest_fuzzy: float

    @property
    def classical_winner(self) -> str:
        return "tight" if self.tight_classical < self.honest_classical else "honest"

    @property
    def fuzzy_winner(self) -> str:
        return "tight" if self.tight_fuzzy < self.honest_fuzzy else "honest"

    @property
    def is_ranking_reversal(self) -> bool:
        return self.classical_winner != self.fuzzy_winner


def run_demo(
    y: float = 50.0,
    relative_sigma: float = 0.4,
    tight_sigma: float = 0.05,
    honest_sigma: float = 0.4,
    honest_loc_offset: float = 0.0,
    n_samples: int = 4000,
    seed: int = 0,
) -> DemoResult:
    """Run the side-by-side demonstration with two forecasters.

    Args:
        y: Observed value (best estimate).
        relative_sigma: True observational uncertainty (used for fuzzy F_obs).
        tight_sigma: Log-space sigma of the tight (overconfident) forecast.
        honest_sigma: Log-space sigma of the honest forecast.
        honest_loc_offset: Log-space location offset for the honest forecaster.
            When nonzero, the honest forecaster is centred at y * exp(offset)
            rather than y, simulating location error.
        n_samples: Number of samples to draw for the empirical forecast CDFs.
        seed: Random seed.

    Returns:
        DemoResult capturing all four scores and the winners.
    """
    rng = np.random.default_rng(seed)
    log_y = np.log(y)

    tight_samples = np.exp(rng.normal(loc=log_y, scale=tight_sigma, size=n_samples))
    honest_samples = np.exp(rng.normal(loc=log_y + honest_loc_offset, scale=honest_sigma, size=n_samples))

    # Classical CRPS: against the step at y
    tight_classical = classical_crps(tight_samples, y)
    honest_classical = classical_crps(honest_samples, y)

    # Fuzzy CRPS: against the parametric F_obs
    f_obs = f_obs_from_parametric(y=y, relative_sigma=relative_sigma)
    tight_pred = empirical_cdf_from_samples(tight_samples)
    honest_pred = empirical_cdf_from_samples(honest_samples)

    grid_max = float(max(np.max(tight_samples), np.max(honest_samples), y * 4))
    tight_fuzzy = fuzzy_crps(
        tight_pred, f_obs, grid_min=0.0, grid_max=grid_max, grid_n=4001
    )
    honest_fuzzy = fuzzy_crps(
        honest_pred, f_obs, grid_min=0.0, grid_max=grid_max, grid_n=4001
    )

    return DemoResult(
        y=y,
        relative_sigma=relative_sigma,
        tight_classical=tight_classical,
        tight_fuzzy=tight_fuzzy,
        honest_classical=honest_classical,
        honest_fuzzy=honest_fuzzy,
    )


def run_demo_normal(
    y: float = 50.0,
    obs_sigma: float = 10.0,
    tight_sigma: float = 2.0,
    honest_sigma: float = 10.0,
    n_samples: int = 4000,
    seed: int = 0,
) -> DemoResult:
    """Run the ranking-reversal demonstration under a Normal DGP.

    Both forecasters are Normal distributions centred on y. F_obs is
    Normal(y, obs_sigma). This tests whether the reversal holds when
    the data is symmetric and light-tailed (unlike conflict data).
    """
    rng = np.random.default_rng(seed)

    tight_samples = rng.normal(loc=y, scale=tight_sigma, size=n_samples)
    honest_samples = rng.normal(loc=y, scale=honest_sigma, size=n_samples)

    # Classical CRPS
    tight_classical = classical_crps(tight_samples, y)
    honest_classical = classical_crps(honest_samples, y)

    # Fuzzy CRPS with Normal F_obs
    def f_obs(z: np.ndarray) -> np.ndarray:
        return _norm_dist.cdf(z, loc=y, scale=obs_sigma)

    tight_pred = empirical_cdf_from_samples(tight_samples)
    honest_pred = empirical_cdf_from_samples(honest_samples)

    grid_min = y - 6 * max(obs_sigma, honest_sigma)
    grid_max = y + 6 * max(obs_sigma, honest_sigma)
    tight_fuzzy = fuzzy_crps(
        tight_pred, f_obs, grid_min=grid_min, grid_max=grid_max, grid_n=4001
    )
    honest_fuzzy = fuzzy_crps(
        honest_pred, f_obs, grid_min=grid_min, grid_max=grid_max, grid_n=4001
    )

    return DemoResult(
        y=y,
        relative_sigma=obs_sigma,
        tight_classical=tight_classical,
        tight_fuzzy=tight_fuzzy,
        honest_classical=honest_classical,
        honest_fuzzy=honest_fuzzy,
    )


def run_demo_zinb(
    y: float = 20.0,
    relative_sigma: float = 0.4,
    tight_sigma: float = 0.05,
    honest_sigma: float = 0.4,
    n_samples: int = 4000,
    seed: int = 0,
) -> DemoResult:
    """Run the ranking-reversal demonstration for a count-like observation.

    Uses the same LogNormal forecasters and parametric F_obs as the main
    demo, but with a smaller y typical of zero-inflated conflict data
    (conditional on y > 0). This tests whether the reversal holds at
    low counts where discreteness is pronounced.
    """
    rng = np.random.default_rng(seed)
    log_y = np.log(max(y, 1e-6))

    tight_samples = np.exp(rng.normal(loc=log_y, scale=tight_sigma, size=n_samples))
    honest_samples = np.exp(rng.normal(loc=log_y, scale=honest_sigma, size=n_samples))

    tight_classical = classical_crps(tight_samples, y)
    honest_classical = classical_crps(honest_samples, y)

    f_obs = f_obs_from_parametric(y=y, relative_sigma=relative_sigma)
    tight_pred = empirical_cdf_from_samples(tight_samples)
    honest_pred = empirical_cdf_from_samples(honest_samples)

    grid_max = float(max(np.max(tight_samples), np.max(honest_samples), y * 4))
    tight_fuzzy = fuzzy_crps(
        tight_pred, f_obs, grid_min=0.0, grid_max=grid_max, grid_n=4001
    )
    honest_fuzzy = fuzzy_crps(
        honest_pred, f_obs, grid_min=0.0, grid_max=grid_max, grid_n=4001
    )

    return DemoResult(
        y=y,
        relative_sigma=relative_sigma,
        tight_classical=tight_classical,
        tight_fuzzy=tight_fuzzy,
        honest_classical=honest_classical,
        honest_fuzzy=honest_fuzzy,
    )


def run_demo_bounds(
    y: float = 50.0,
    low: float = 25.0,
    high: float = 100.0,
    tight_sigma: float = 0.05,
    honest_sigma: float = 0.4,
    n_samples: int = 4000,
    seed: int = 0,
) -> DemoResult:
    """Run the demonstration with bounds-based Constructor 1."""
    rng = np.random.default_rng(seed)
    log_y = np.log(y)

    tight_samples = np.exp(rng.normal(loc=log_y, scale=tight_sigma, size=n_samples))
    honest_samples = np.exp(rng.normal(loc=log_y, scale=honest_sigma, size=n_samples))

    tight_classical = classical_crps(tight_samples, y)
    honest_classical = classical_crps(honest_samples, y)

    f_obs = f_obs_from_bounds(low=low, best=y, high=high, distribution="uniform")
    tight_pred = empirical_cdf_from_samples(tight_samples)
    honest_pred = empirical_cdf_from_samples(honest_samples)

    grid_max = float(max(np.max(tight_samples), np.max(honest_samples), high * 2))
    tight_fuzzy = fuzzy_crps(
        tight_pred, f_obs, grid_min=0.0, grid_max=grid_max, grid_n=4001
    )
    honest_fuzzy = fuzzy_crps(
        honest_pred, f_obs, grid_min=0.0, grid_max=grid_max, grid_n=4001
    )

    return DemoResult(
        y=y,
        relative_sigma=0.0,
        tight_classical=tight_classical,
        tight_fuzzy=tight_fuzzy,
        honest_classical=honest_classical,
        honest_fuzzy=honest_fuzzy,
    )


# Suppress unused import warning
_ = step_cdf_at
