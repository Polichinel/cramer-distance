"""Classical CRPS implementation for reference.

The Continuous Ranked Probability Score for a forecast CDF F and an
observation y is

    CRPS(F, y) = ∫ (F(z) - 1{y ≤ z})² dz

The integrand has a step function in z at z = y. Standard implementations
either compute the kernel form from forecast samples or evaluate the
integral analytically against parametric forecast families.

This module implements the kernel form via samples — the same convention
used by lab_anti_timid and the autoresearch experiments. The result is a
scalar score for a single (sample, observation) pair, or a vector for
batched inputs.

The Fuzzy CRPS in `cramer_distance.fuzzy_crps` generalises this by
replacing the step indicator with a smooth observational CDF.
"""

from __future__ import annotations

import numpy as np
from numpy.typing import NDArray


def classical_crps(
    forecast_samples: NDArray[np.float64], observation: float
) -> float:
    """Compute classical CRPS for one (sample-based forecast, observation) pair.

    Uses the kernel form

        CRPS(X, y) = E|X - y| - 0.5 * E|X - X'|

    Args:
        forecast_samples: 1D array of forecast samples, shape (S,).
        observation: Scalar observed value.

    Returns:
        Scalar CRPS value.
    """
    samples = np.asarray(forecast_samples, dtype=np.float64).ravel()
    n = samples.size
    if n == 0:
        return 0.0
    mae = float(np.mean(np.abs(samples - observation)))
    sorted_samples = np.sort(samples)
    weights = 2.0 * np.arange(1, n + 1) - n - 1
    gini = float(np.sum(sorted_samples * weights) / (n * n))
    return mae - gini


def brocker_smith_crps(
    forecast_samples: NDArray[np.float64],
    obs_draws: NDArray[np.float64],
) -> float:
    """Bröcker-Smith conditional-expectation correction for CRPS.

    Computes E[CRPS(F_pred, Y)] where Y is drawn from the observation
    distribution F_obs. This is the approach of Bröcker & Smith (2007):
    rather than replacing the step indicator with F_obs in the integrand,
    average the classical CRPS over draws from F_obs.

    Args:
        forecast_samples: 1D array of forecast samples, shape (S,).
        obs_draws: 1D array of draws from F_obs, shape (M,).

    Returns:
        Scalar: mean classical CRPS across the observation draws.
    """
    scores = np.array([
        classical_crps(forecast_samples, float(y))
        for y in obs_draws
    ])
    return float(scores.mean())


def classical_crps_batch(
    forecast_samples: NDArray[np.float64],
    observations: NDArray[np.float64],
) -> float:
    """Vectorised classical CRPS averaged over a batch of (forecast, obs) pairs.

    Args:
        forecast_samples: 2D array of shape (N, S).
        observations: 1D array of shape (N,).

    Returns:
        Mean CRPS across N observations (NaN-skipping in the first sample column).
    """
    valid = ~np.isnan(forecast_samples[:, 0])
    forecast_samples = forecast_samples[valid]
    observations = observations[valid]
    if len(observations) == 0:
        return 0.0
    mae = float(np.mean(np.abs(forecast_samples - observations[:, None])))
    sorted_samples = np.sort(forecast_samples, axis=1)
    n = sorted_samples.shape[1]
    weights = 2.0 * np.arange(1, n + 1) - n - 1
    gini = float(np.mean(sorted_samples @ weights / (n * n)))
    return mae - gini
