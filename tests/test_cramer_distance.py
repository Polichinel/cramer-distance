"""Tests for cramer_distance: classical / fuzzy CRPS, F_obs constructors, propriety."""

import numpy as np
import pytest

from cramer_distance import (
    classical_crps,
    f_obs_from_bounds,
    f_obs_from_parametric,
    f_obs_from_weight_head,
    fuzzy_crps,
)
from cramer_distance.demo import run_demo
from cramer_distance.fuzzy_crps import (
    empirical_cdf_from_samples,
    step_cdf_at,
)
from cramer_distance.propriety import (
    lognormal_cdf,
    verify_propriety_in_expectation,
    verify_propriety_numerical,
)


def test_classical_crps_perfect_forecast() -> None:
    """A degenerate forecast at the true value gives CRPS = 0."""
    samples = np.full(64, 5.0)
    assert classical_crps(samples, observation=5.0) == pytest.approx(0.0)


def test_classical_crps_handles_empty() -> None:
    """Empty forecast samples give CRPS = 0 (defensive default)."""
    samples = np.array([])
    assert classical_crps(samples, observation=5.0) == 0.0


def test_step_cdf_is_step() -> None:
    """step_cdf_at returns 0 below value and 1 at/above."""
    cdf = step_cdf_at(5.0)
    z = np.array([0.0, 4.999, 5.0, 5.001, 10.0])
    expected = np.array([0.0, 0.0, 1.0, 1.0, 1.0])
    assert np.allclose(cdf(z), expected)


def test_empirical_cdf_from_samples_is_monotone() -> None:
    """The empirical CDF is monotone non-decreasing."""
    samples = np.array([1.0, 2.0, 3.0, 4.0, 5.0])
    cdf = empirical_cdf_from_samples(samples)
    z = np.linspace(0, 6, 50)
    values = cdf(z)
    assert np.all(np.diff(values) >= 0)
    assert values[0] == pytest.approx(0.0)
    assert values[-1] == pytest.approx(1.0)


def test_fuzzy_crps_against_step_recovers_classical() -> None:
    """When F_obs is a step at the true value, fuzzy CRPS ≈ classical CRPS."""
    rng = np.random.default_rng(0)
    samples = rng.normal(loc=5.0, scale=0.5, size=1000)
    f_pred = empirical_cdf_from_samples(samples)
    f_obs = step_cdf_at(5.0)
    fuzzy = fuzzy_crps(f_pred, f_obs, grid_min=0.0, grid_max=10.0, grid_n=4001)
    classical = classical_crps(samples, observation=5.0)
    # Allow some discrepancy due to numerical integration vs the kernel form
    assert abs(fuzzy - classical) < 0.05


def test_fuzzy_crps_zero_when_f_pred_equals_f_obs() -> None:
    """Fuzzy CRPS is exactly zero when F_pred = F_obs."""
    f = lognormal_cdf(mu=1.0, sigma=0.3)
    score = fuzzy_crps(f, f, grid_min=0.0, grid_max=20.0, grid_n=4001)
    assert score == pytest.approx(0.0, abs=1e-10)


def test_f_obs_from_bounds_uniform() -> None:
    """The uniform F_obs is linear between low and high."""
    cdf = f_obs_from_bounds(low=10.0, best=20.0, high=30.0, distribution="uniform")
    assert cdf(np.array([5.0])).item() == pytest.approx(0.0)
    assert cdf(np.array([20.0])).item() == pytest.approx(0.5)
    assert cdf(np.array([35.0])).item() == pytest.approx(1.0)


def test_f_obs_from_bounds_validates() -> None:
    """f_obs_from_bounds rejects out-of-order bounds."""
    with pytest.raises(ValueError, match="Bounds must satisfy"):
        f_obs_from_bounds(low=5.0, best=10.0, high=3.0)


def test_f_obs_from_parametric_lognormal_centred_on_y() -> None:
    """The parametric LogNormal F_obs has CDF = 0.5 at y."""
    y = 50.0
    cdf = f_obs_from_parametric(y=y, relative_sigma=0.3, distribution="lognormal")
    assert cdf(np.array([y])).item() == pytest.approx(0.5, abs=1e-6)


def test_f_obs_from_weight_head_widens_with_low_confidence() -> None:
    """Lower confidence produces a wider F_obs (less mass near the centre)."""
    y = 50.0
    cdf_high = f_obs_from_weight_head(y=y, confidence=0.9, sigma_base=0.3)
    cdf_low = f_obs_from_weight_head(y=y, confidence=0.1, sigma_base=0.3)
    # At y itself, both should be ~0.5; the difference shows in the tails
    z = np.array([y * 2])
    assert cdf_low(z).item() < cdf_high(z).item()  # low conf has heavier right tail


@pytest.mark.parametrize("true_mu", [0.5, 1.0, 1.5, 2.0])
def test_verify_propriety_numerical_minimised_at_truth(true_mu: float) -> None:
    """The fixed-F_obs L2-minimisation check finds the argmin near true_mu.

    Parametrised over several true_mu values so the paper's "passes for
    several true mu values" claim in §5 is empirically backed (C-35).
    The mu_sweep is centred on each parametrised true_mu so the grid
    always contains the expected argmin.
    """
    mu_sweep, scores, argmin = verify_propriety_numerical(
        true_mu=true_mu, true_sigma=0.3,
        mu_sweep=np.linspace(true_mu - 1.5, true_mu + 1.5, 31),
    )
    assert abs(argmin - true_mu) < 0.15  # within one grid step of true


@pytest.mark.parametrize("true_mu", [0.5, 1.0, 1.5, 2.0])
def test_verify_propriety_in_expectation_finds_truth(true_mu: float) -> None:
    """The stochastic-y consistency check finds the argmin near true_mu
    when the F_obs constructor is well-specified.

    This is the substantive verification the Note C pipeline actually
    needs (C-32). It draws N=100 observations from LogNormal(true_mu,
    true_sigma), constructs a per-draw F_obs via the parametric
    constructor with matching sigma_rel, sweeps F_pred over a grid of
    mu values, and checks that the expected fuzzy CRPS is minimised
    near true_mu.
    """
    mu_sweep, scores, argmin = verify_propriety_in_expectation(
        true_mu=true_mu,
        true_sigma=0.3,
        obs_sigma_rel=0.3,  # well-specified
        n_draws=100,
        mu_sweep=np.linspace(true_mu - 1.0, true_mu + 1.0, 21),
        seed=0,
    )
    assert abs(argmin - true_mu) < 0.15, (
        f"Expected fuzzy CRPS should be minimised near true_mu={true_mu}; "
        f"argmin was {argmin:.3f}"
    )


def test_verify_propriety_in_expectation_biased_under_misspecification() -> None:
    """When obs_sigma_rel != true_sigma, the argmin may shift — but the
    function should still run and return a valid sweep. This guards
    against regressions that would crash the consistency checker."""
    mu_sweep, scores, argmin = verify_propriety_in_expectation(
        true_mu=1.0,
        true_sigma=0.3,
        obs_sigma_rel=0.5,  # mis-specified
        n_draws=50,
        mu_sweep=np.linspace(0.0, 2.0, 21),
        seed=0,
    )
    assert len(mu_sweep) == len(scores) == 21
    assert np.all(np.isfinite(scores))
    assert 0.0 <= argmin <= 2.0


def test_demo_produces_expected_ranking_reversal() -> None:
    """The honest forecaster wins under fuzzy CRPS even if it loses under classical."""
    result = run_demo(
        y=50.0,
        relative_sigma=0.4,
        tight_sigma=0.05,
        honest_sigma=0.4,
        n_samples=2000,
        seed=42,
    )
    # The honest forecaster (matched to F_obs) should at least tie under fuzzy
    assert result.fuzzy_winner == "honest"
    # Tight beats honest on classical (it hugs the step)
    assert result.tight_classical < result.honest_classical
