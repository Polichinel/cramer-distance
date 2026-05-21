"""Consistency checks for fuzzy CRPS.

The quantity computed by fuzzy_crps is the Cramér distance (also called
the L2 CDF distance) between F_pred and F_obs. When F_obs degenerates to
a step at y, it reduces to classical CRPS. Its propriety properties
therefore inherit from the Cramér-distance / energy-distance literature
(Székely & Rizzo 2013; Thorarinsdottir et al. 2013; Gneiting & Ranjan
2011; Gneiting & Raftery 2007 for the classical CRPS case) — there is
no new propriety theorem specific to fuzzy CRPS, and earlier framings
that claimed one were conflating L2 minimisation with the
Gneiting-Raftery definition of propriety.

What the operational pipeline actually needs is a *consistency* check:
when the reported y is drawn from the true data-generating distribution
Q and F_obs is constructed as a function of that draw, is the expected
fuzzy CRPS approximately minimised at F_pred = Q? This is weaker than
classical propriety and depends on the F_obs constructor being
well-specified with respect to Q, but it is the property a practitioner
actually needs.

This module provides two numerical checkers:

- `verify_propriety_numerical`: the fixed-F_obs L2-minimisation statement,
  sweeping a forecast parameter against a fixed observational CDF.

- `verify_propriety_in_expectation`: the stochastic-y consistency check,
  drawing N observations from a known truth and verifying that the
  expected fuzzy CRPS is minimised at the true forecast parameter.

Neither is an analytical proof. An analytical proof via the energy-
distance framework is possible but requires care about the joint
distribution of y and F_obs(y); we leave it to future work.
"""

from __future__ import annotations

from collections.abc import Callable

import numpy as np
from numpy.typing import NDArray
from scipy.stats import norm

from cramer_distance.fuzzy_crps import fuzzy_crps

# ---------------------------------------------------------------------------
# CDF constructors for different distribution families
# ---------------------------------------------------------------------------


def lognormal_cdf(
    mu: float, sigma: float
) -> Callable[[NDArray[np.float64]], NDArray[np.float64]]:
    """Convenience constructor for a LogNormal CDF callable."""
    def cdf(z: NDArray[np.float64]) -> NDArray[np.float64]:
        z_safe = np.maximum(z, 1e-12)
        return norm.cdf(np.log(z_safe), loc=mu, scale=sigma)
    return cdf


def normal_cdf(
    mu: float, sigma: float
) -> Callable[[NDArray[np.float64]], NDArray[np.float64]]:
    """Convenience constructor for a Normal CDF callable."""
    def cdf(z: NDArray[np.float64]) -> NDArray[np.float64]:
        return norm.cdf(z, loc=mu, scale=sigma)
    return cdf


def verify_propriety_numerical(
    true_mu: float = 1.0,
    true_sigma: float = 0.3,
    mu_sweep: np.ndarray | None = None,
    grid_min: float = 0.0,
    grid_max: float = 50.0,
    grid_n: int = 4001,
    cdf_factory: Callable[[float, float], Callable] | None = None,
) -> tuple[np.ndarray, np.ndarray, float]:
    """Sweep a forecast parameter and verify fuzzy CRPS is minimised at the truth.

    By default uses LogNormal CDFs. Pass ``cdf_factory`` to test other
    distribution families (e.g. ``normal_cdf`` for Gaussian).

    Args:
        true_mu: True location parameter.
        true_sigma: True scale parameter (held fixed for both F_obs and F_pred).
        mu_sweep: Array of forecast location values to test. Defaults to
            np.linspace(true_mu - 1, true_mu + 1, 41).
        grid_min: Lower bound for the integration grid.
        grid_max: Upper bound for the integration grid.
        grid_n: Number of points in the integration grid.
        cdf_factory: ``(mu, sigma) -> CDF callable``. Defaults to
            :func:`lognormal_cdf`.

    Returns:
        (mu_sweep, scores, argmin_mu) — the sweep array, the corresponding
        fuzzy CRPS values, and the mu at which the minimum occurs.
    """
    if cdf_factory is None:
        cdf_factory = lognormal_cdf
    if mu_sweep is None:
        mu_sweep = np.linspace(true_mu - 1.0, true_mu + 1.0, 41)

    f_obs = cdf_factory(true_mu, true_sigma)
    scores = np.zeros(len(mu_sweep))
    for i, mu in enumerate(mu_sweep):
        f_pred = cdf_factory(float(mu), true_sigma)
        scores[i] = fuzzy_crps(
            f_pred=f_pred,
            f_obs=f_obs,
            grid_min=grid_min,
            grid_max=grid_max,
            grid_n=grid_n,
        )

    argmin_idx = int(np.argmin(scores))
    return mu_sweep, scores, float(mu_sweep[argmin_idx])


def verify_propriety_in_expectation(
    true_mu: float = 1.0,
    true_sigma: float = 0.3,
    obs_sigma_rel: float = 0.3,
    n_draws: int = 500,
    mu_sweep: np.ndarray | None = None,
    grid_min: float = 0.0,
    grid_max: float = 50.0,
    grid_n: int = 4001,
    seed: int | None = 0,
    cdf_factory: Callable[[float, float], Callable] | None = None,
    sampler: Callable[[np.random.Generator, int], NDArray[np.float64]] | None = None,
    f_obs_factory: Callable[[float], Callable] | None = None,
) -> tuple[np.ndarray, np.ndarray, float]:
    """Stochastic-y consistency check for the fuzzy CRPS pipeline.

    Draws n_draws observations y from a DGP, constructs a per-draw F_obs,
    sweeps a forecast parameter mu over mu_sweep, and computes the
    expected fuzzy CRPS E_y[CRPS_fuzzy(F_pred(mu), F_obs(y))] at each mu
    via Monte Carlo averaging. Returns the sweep, the expected scores,
    and the argmin.

    By default uses LogNormal DGP with f_obs_from_parametric. Pass
    ``cdf_factory``, ``sampler``, and ``f_obs_factory`` for other families.

    Args:
        true_mu: Location parameter of the data-generating distribution.
        true_sigma: Scale parameter of the data-generating distribution.
        obs_sigma_rel: sigma_rel to pass to f_obs_from_parametric when
            constructing F_obs per draw (only used when f_obs_factory is None).
        n_draws: Number of Monte Carlo draws of y.
        mu_sweep: Forecast location values to test.
        grid_min: Lower bound for the integration grid.
        grid_max: Upper bound for the integration grid.
        grid_n: Number of points in the integration grid.
        seed: Optional RNG seed for reproducibility.
        cdf_factory: ``(mu, sigma) -> CDF callable``. Defaults to
            :func:`lognormal_cdf`.
        sampler: ``(rng, n) -> array`` drawing n samples from the true DGP.
            Defaults to LogNormal(true_mu, true_sigma).
        f_obs_factory: ``(y) -> CDF callable`` constructing F_obs per draw.
            Defaults to ``f_obs_from_parametric(y, obs_sigma_rel, "lognormal")``.

    Returns:
        (mu_sweep, expected_scores, argmin_mu).
    """
    from cramer_distance.observation_uncertainty import f_obs_from_parametric

    if cdf_factory is None:
        cdf_factory = lognormal_cdf
    if mu_sweep is None:
        mu_sweep = np.linspace(true_mu - 1.0, true_mu + 1.0, 41)

    rng = np.random.default_rng(seed)

    if sampler is not None:
        draws = sampler(rng, n_draws)
    else:
        draws = np.exp(true_mu + true_sigma * rng.standard_normal(n_draws))

    if f_obs_factory is None:
        def _default_f_obs_factory(y: float) -> Callable:
            return f_obs_from_parametric(
                y=y, relative_sigma=obs_sigma_rel, distribution="lognormal",
            )
        f_obs_factory = _default_f_obs_factory

    expected_scores = np.zeros(len(mu_sweep))
    for i, mu in enumerate(mu_sweep):
        f_pred = cdf_factory(float(mu), true_sigma)
        acc = 0.0
        for y in draws:
            f_obs = f_obs_factory(float(y))
            acc += fuzzy_crps(
                f_pred=f_pred,
                f_obs=f_obs,
                grid_min=grid_min,
                grid_max=grid_max,
                grid_n=grid_n,
            )
        expected_scores[i] = acc / n_draws

    argmin_idx = int(np.argmin(expected_scores))
    return mu_sweep, expected_scores, float(mu_sweep[argmin_idx])
