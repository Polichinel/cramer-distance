"""Fuzzy CRPS: scoring against a smooth observational CDF.

The standard CRPS uses the indicator function 1{y ≤ z}, which treats the
observation y as a point known with infinite precision. For data with
measurement uncertainty -- UCDP fatality counts, weather observations,
epidemiological surveillance -- this assumption is wrong.

We replace the step indicator with a smooth observational CDF F_obs(z)
that captures the uncertainty about the observation itself:

    CRPS_fuzzy(F_pred, F_obs) = ∫ (F_pred(z) - F_obs(z))² dz

When F_obs is a step function at the reported value, this reduces to
the classical CRPS. When F_obs has positive variance, the integrand is
no longer dominated by the gap between the forecast CDF and a hard
step, and forecasts that honestly report uncertainty are no longer
penalised relative to forecasts that overconfidently hit the step.

This module implements fuzzy CRPS via numerical integration over a grid
of evaluation points spanning the support of both F_pred and F_obs. It is
not the most efficient implementation possible — a closed-form expression
exists for some specific F_obs families — but it is the most general and
suffices for the demonstration in Note C.

For propriety arguments and constructors of F_obs, see
`cramer_distance.propriety` and `cramer_distance.observation_uncertainty`
respectively.
"""

from __future__ import annotations

from collections.abc import Callable

import numpy as np
from numpy.typing import NDArray


def fuzzy_crps(
    f_pred: Callable[[NDArray[np.float64]], NDArray[np.float64]],
    f_obs: Callable[[NDArray[np.float64]], NDArray[np.float64]],
    grid: NDArray[np.float64] | None = None,
    grid_min: float = 0.0,
    grid_max: float = 1000.0,
    grid_n: int = 4001,
) -> float:
    """Compute fuzzy CRPS by numerical integration.

    Args:
        f_pred: Forecast CDF; takes a 1D array of evaluation points and
            returns a 1D array of CDF values in [0, 1].
        f_obs: Observational CDF; same interface as f_pred.
        grid: Optional pre-computed evaluation grid. If None, a uniform
            grid spanning [grid_min, grid_max] with grid_n points is used.
        grid_min: Lower bound of the default grid.
        grid_max: Upper bound of the default grid.
        grid_n: Number of points in the default grid.

    Returns:
        Scalar fuzzy CRPS value.
    """
    if grid is None:
        grid = np.linspace(grid_min, grid_max, grid_n)
    f_p = np.asarray(f_pred(grid), dtype=np.float64)
    f_o = np.asarray(f_obs(grid), dtype=np.float64)
    integrand = (f_p - f_o) ** 2
    return float(np.trapezoid(integrand, grid))


def empirical_cdf_from_samples(
    samples: NDArray[np.float64],
) -> Callable[[NDArray[np.float64]], NDArray[np.float64]]:
    """Build an empirical CDF callable from a 1D array of forecast samples.

    The empirical CDF is the standard step function

        F(z) = (1/N) * #{X_i ≤ z}

    The returned callable accepts a 1D array of evaluation points and
    returns the CDF values at each point.
    """
    sorted_samples = np.sort(np.asarray(samples, dtype=np.float64))
    n = len(sorted_samples)

    def cdf(z: NDArray[np.float64]) -> NDArray[np.float64]:
        # For each z, count how many sorted samples are ≤ z
        idx = np.searchsorted(sorted_samples, z, side="right")
        return idx / n

    return cdf


def step_cdf_at(value: float) -> Callable[[NDArray[np.float64]], NDArray[np.float64]]:
    """Build a step CDF at a single point (the classical CRPS observation CDF)."""
    def cdf(z: NDArray[np.float64]) -> NDArray[np.float64]:
        return (z >= value).astype(np.float64)
    return cdf
