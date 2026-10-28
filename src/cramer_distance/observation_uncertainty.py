"""Constructors for the observational CDF F_obs used by fuzzy CRPS.

Three sources of observational uncertainty are supported. They are not
mutually exclusive — a practitioner could combine them — but each is
sufficient on its own for demonstration purposes.

1. **Bounds-based.** Many event datasets (UCDP/GED, EM-DAT) provide
   low/best/high estimates per observation. The bounds reflect coding
   uncertainty and are documented in the dataset's codebook. We treat
   the bounds as the support of a uniform or LogNormal distribution
   centred on the best estimate.

2. **Parametric.** A simple default for datasets without explicit
   bounds: model the observation as LogNormal(log(y), σ_obs) where
   σ_obs is a fixed relative uncertainty (e.g. 30% standard deviation
   in log-space). This requires no per-observation metadata.

3. **Model-derived.** Use the confidence output of a trained weight
   trained weight head to scale the observational uncertainty per cell-month.
   Cells the model identifies as low-confidence get wider F_obs, on
   the rationale that the model's distrust of the observation is
   itself evidence that the observation is noisy.

All three constructors return Callable F_obs functions compatible with
`cramer_distance.fuzzy_crps.fuzzy_crps`.
"""

from __future__ import annotations

from collections.abc import Callable

import numpy as np
from numpy.typing import NDArray
from scipy.stats import lognorm, norm


def f_obs_from_bounds(
    low: float, best: float, high: float, distribution: str = "uniform"
) -> Callable[[NDArray[np.float64]], NDArray[np.float64]]:
    """Construct F_obs from explicit low/best/high bounds.

    Args:
        low: Lower bound (e.g. UCDP low estimate).
        best: Best estimate.
        high: Upper bound (e.g. UCDP high estimate).
        distribution: Either "uniform" (uniform on [low, high]) or
            "lognormal" (LogNormal centered on log(best) with the
            spread inferred so that ~95% of mass falls in [low, high]).

    Returns:
        Callable F_obs(z) that takes a 1D array of evaluation points
        and returns the CDF values at each point.
    """
    if low > best or best > high:
        raise ValueError(
            f"Bounds must satisfy low ≤ best ≤ high; got {low}, {best}, {high}"
        )

    if distribution == "uniform":
        def cdf(z: NDArray[np.float64]) -> NDArray[np.float64]:
            if high == low:
                return (z >= best).astype(np.float64)
            return np.clip((z - low) / (high - low), 0.0, 1.0)
        return cdf

    if distribution == "lognormal":
        if best <= 0:
            raise ValueError("lognormal distribution requires best > 0")
        if low <= 0:
            raise ValueError(
                "lognormal F_obs is undefined at low <= 0 because log(0) = -inf "
                "produces a near-uniform CDF over many orders of magnitude. "
                "Use distribution='uniform' when the low bound is zero."
            )
        log_best = np.log(best)
        log_low = np.log(low)
        log_high = np.log(high)
        log_sigma = max((log_high - log_low) / (2 * 1.96), 1e-3)

        def cdf(z: NDArray[np.float64]) -> NDArray[np.float64]:
            z_safe = np.maximum(z, 1e-12)
            return norm.cdf(np.log(z_safe), loc=log_best, scale=log_sigma)
        return cdf

    raise ValueError(f"Unknown distribution {distribution!r}")


def f_obs_from_parametric(
    y: float,
    relative_sigma: float = 0.4,
    distribution: str = "lognormal",
) -> Callable[[NDArray[np.float64]], NDArray[np.float64]]:
    """Default constructor: parametric observational uncertainty.

    Args:
        y: Observed value (the dataset's best estimate).
        relative_sigma: Standard deviation of the observational
            uncertainty, in log-space (default 0.4 = roughly 50% relative
            uncertainty, a working default for armed-conflict fatality
            counts approximating small-to-medium events).
        distribution: Either "lognormal" (right-skewed, appropriate
            for fatality counts) or "normal" (symmetric, for centred
            measurements).

    Returns:
        Callable F_obs(z).
    """
    if y <= 0:
        # For zero observations, default to a step at zero
        def cdf(z: NDArray[np.float64]) -> NDArray[np.float64]:
            return (z >= 0).astype(np.float64)
        return cdf

    if distribution == "lognormal":
        log_y = np.log(y)

        def cdf(z: NDArray[np.float64]) -> NDArray[np.float64]:
            z_safe = np.maximum(z, 1e-12)
            return norm.cdf(np.log(z_safe), loc=log_y, scale=relative_sigma)
        return cdf

    if distribution == "normal":
        sigma = relative_sigma * abs(y)

        def cdf(z: NDArray[np.float64]) -> NDArray[np.float64]:
            return norm.cdf(z, loc=y, scale=sigma)
        return cdf

    raise ValueError(f"Unknown distribution {distribution!r}")


def f_obs_from_weight_head(
    y: float,
    confidence: float,
    sigma_base: float = 0.4,
    sigma_scale: float = 1.0,
) -> Callable[[NDArray[np.float64]], NDArray[np.float64]]:
    """Constructor that scales observational uncertainty by model confidence.

    The intuition: if the trained model has low confidence at a cell, this
    is itself evidence that the observation in that cell is noisy or the
    cell is in a regime the model cannot represent. In either case the
    evaluation should not penalise a forecaster that hedges in such cells.

    Args:
        y: Observed value.
        confidence: Per-cell confidence from the weight head, in [0, 1].
        sigma_base: Baseline relative observational uncertainty.
        sigma_scale: Multiplier on the inverse-confidence widening.
            Default 1.0 means low-confidence cells get sigma up to twice
            the baseline.

    Returns:
        Callable F_obs(z).
    """
    # Lower confidence → wider F_obs
    sigma = sigma_base * (1.0 + sigma_scale * (1.0 - confidence))
    return f_obs_from_parametric(y=y, relative_sigma=sigma, distribution="lognormal")


# ---------------------------------------------------------------------------
# Sampling utilities (for Bröcker-Smith conditional-expectation correction)
# ---------------------------------------------------------------------------


def sample_from_f_obs_parametric(
    y: float,
    relative_sigma: float = 0.4,
    n: int = 500,
    seed: int = 0,
) -> NDArray[np.float64]:
    """Draw samples from the same distribution as f_obs_from_parametric.

    Returns 1D array of shape (n,).
    """
    if y <= 0:
        return np.zeros(n)
    rng = np.random.default_rng(seed)
    return np.exp(rng.normal(np.log(y), relative_sigma, n))


def sample_from_f_obs_bounds(
    low: float,
    best: float,
    high: float,
    distribution: str = "uniform",
    n: int = 500,
    seed: int = 0,
) -> NDArray[np.float64]:
    """Draw samples from the same distribution as f_obs_from_bounds.

    Returns 1D array of shape (n,).
    """
    rng = np.random.default_rng(seed)
    if distribution == "uniform":
        if high == low:
            return np.full(n, best)
        return rng.uniform(low, high, n)
    if distribution == "lognormal":
        log_best = np.log(best)
        log_low = np.log(max(low, 1e-12))
        log_high = np.log(high)
        log_sigma = max((log_high - log_low) / (2 * 1.96), 1e-3)
        return np.exp(rng.normal(log_best, log_sigma, n))
    raise ValueError(f"Unknown distribution {distribution!r}")


# ---------------------------------------------------------------------------
# Constructor 4: Vesco et al. (2026) RVI Gumbel mixture
# ---------------------------------------------------------------------------

# Vesco et al. (2026) RVI Gumbel regression coefficients, one model per
# UCDP violence type, as shipped in the authors' R package uncertainUCDP
# 0.7.6 (CRAN; `internal_models$sb`, `$ns`, `$os`, `$any` in R/sysdata.rda).
# Each model predicts log1p(μ_g) and log(β_g) via OLS and w via logistic
# regression from log1p(ỹ) and vague-number dummies.  Keys: 1 = state-based,
# 2 = non-state, 3 = one-sided, 4 = all types pooled (the package flags this
# one as experimental).  The state-based set is the one previously used for
# all types; F-34 in the writing harness records the correction.
#
# Vague-number dummies in the regression (subset of UCDP vague numbers):
#   D_2, D_3, D_13, D_20, D_24, D_40, D_101, D_200, D_1001, D_2000
_RVI_MU = {
    1: {  # state-based
        "intercept": 0.609, "log1p_y": 0.932,
        2: 0.081, 3: -0.247, 13: -0.441, 20: -0.392, 24: -0.480, 40: -0.302, 101: -0.235, 200: -0.212, 1001: -0.043, 2000: -0.076,
    },
    2: {  # non-state
        "intercept": 0.575, "log1p_y": 0.936,
        2: -0.035, 3: -0.277, 13: -0.397, 20: -0.368, 24: -0.494, 40: -0.270, 101: -0.234, 200: -0.235, 1001: -0.039, 2000: -0.010,
    },
    3: {  # one-sided
        "intercept": 0.540, "log1p_y": 0.940,
        2: 0.018, 3: -0.148, 13: -0.373, 20: -0.317, 24: -0.425, 40: -0.271, 101: -0.222, 200: -0.189, 1001: -0.073, 2000: -0.024,
    },
    4: {  # all types pooled ('any'; experimental in the package)
        "intercept": 0.574, "log1p_y": 0.936,
        2: 0.021, 3: -0.223, 13: -0.403, 20: -0.358, 24: -0.467, 40: -0.280, 101: -0.230, 200: -0.212, 1001: -0.052, 2000: -0.036,
    },
}
_RVI_BETA = {
    1: {  # state-based
        "intercept": -0.304, "log1p_y": 0.823,
        2: 0.115, 3: -0.249, 13: -0.491, 20: -1.229, 24: -1.678, 40: -1.265, 101: -0.915, 200: -0.734, 1001: -0.196, 2000: 0.165,
    },
    2: {  # non-state
        "intercept": -0.702, "log1p_y": 0.855,
        2: 0.118, 3: -0.065, 13: -0.518, 20: -1.537, 24: -1.722, 40: -1.337, 101: -0.912, 200: -0.866, 1001: -0.683, 2000: 0.331,
    },
    3: {  # one-sided
        "intercept": -0.762, "log1p_y": 0.871,
        2: 0.030, 3: -0.047, 13: -0.379, 20: -1.531, 24: -1.749, 40: -1.223, 101: -0.874, 200: -0.575, 1001: -0.283, 2000: 0.231,
    },
    4: {  # all types pooled ('any'; experimental in the package)
        "intercept": -0.594, "log1p_y": 0.850,
        2: 0.088, 3: -0.118, 13: -0.461, 20: -1.434, 24: -1.720, 40: -1.278, 101: -0.900, 200: -0.725, 1001: -0.389, 2000: 0.244,
    },
}
_RVI_W = {
    1: {  # state-based
        "intercept": -0.086, "log1p_y": -0.053,
        2: 0.420, 3: -0.259, 13: 0.327, 20: -0.135, 24: -0.732, 40: -0.141, 101: -0.072, 200: -0.022, 1001: -0.013, 2000: -0.043,
    },
    2: {  # non-state
        "intercept": -0.341, "log1p_y": -0.030,
        2: 0.789, 3: 0.342, 13: 0.186, 20: -0.278, 24: -0.666, 40: -0.032, 101: 0.178, 200: 0.023, 1001: 0.118, 2000: -0.087,
    },
    3: {  # one-sided
        "intercept": -0.341, "log1p_y": -0.018,
        2: 0.520, 3: 0.272, 13: 0.300, 20: -0.320, 24: -0.740, 40: -0.088, 101: -0.028, 200: 0.029, 1001: 0.017, 2000: 0.032,
    },
    4: {  # all types pooled ('any'; experimental in the package)
        "intercept": -0.258, "log1p_y": -0.033,
        2: 0.577, 3: 0.124, 13: 0.270, 20: -0.243, 24: -0.713, 40: -0.087, 101: 0.028, 200: 0.011, 1001: 0.041, 2000: -0.031,
    },
}


def _rvi_gumbel_params(
    y_reported: float,
    violence_type: int = 1,
) -> tuple[float, float, float]:
    """Predict RVI Gumbel mixture parameters from reported fatalities.

    Returns (mu_g, beta_g, w) where:
        mu_g:   location of the Gumbel component
        beta_g: scale of the Gumbel component (> 0)
        w:      mixture weight on the point mass at y_reported, in [0, 1]

    Coefficients are the per-violence-type models of Vesco et al. (2026)
    as shipped in uncertainUCDP 0.7.6.  The regression predicts log1p(μ_g)
    and log(β_g) via OLS and w via logistic regression, from log1p(ỹ) and
    vague-number dummies.  ``violence_type`` selects the model:
    1 = state-based, 2 = non-state, 3 = one-sided, 4 = all types pooled.
    """
    if violence_type not in _RVI_MU:
        raise ValueError(f"violence_type must be 1, 2, 3 or 4, got {violence_type!r}")
    coef_mu = _RVI_MU[violence_type]
    coef_beta = _RVI_BETA[violence_type]
    coef_w = _RVI_W[violence_type]
    log1p_y = np.log1p(max(y_reported, 0.0))
    y_int = int(y_reported)

    # --- Linear predictor for log1p(mu_g) ---
    eta_mu = coef_mu["intercept"] + coef_mu["log1p_y"] * log1p_y
    if y_int in coef_mu:
        eta_mu += coef_mu[y_int]
    mu_g = np.expm1(eta_mu)  # mu_g = exp(eta_mu) - 1

    # --- Linear predictor for log(beta_g) ---
    eta_beta = coef_beta["intercept"] + coef_beta["log1p_y"] * log1p_y
    if y_int in coef_beta:
        eta_beta += coef_beta[y_int]
    beta_g = np.exp(eta_beta)

    # --- Logistic predictor for w ---
    eta_w = coef_w["intercept"] + coef_w["log1p_y"] * log1p_y
    if y_int in coef_w:
        eta_w += coef_w[y_int]
    w = 1.0 / (1.0 + np.exp(-eta_w))

    return float(max(mu_g, 0.0)), float(max(beta_g, 1e-6)), float(np.clip(w, 0.01, 0.99))


def f_obs_from_rvi_gumbel(
    y_reported: float,
    violence_type: int = 1,
) -> Callable[[NDArray[np.float64]], NDArray[np.float64]]:
    """Construct F_obs using the Vesco et al. (2026) RVI Gumbel mixture.

    The RVI (Reported-Value Inflated) Gumbel mixture places probability
    mass w at the exact reported value ỹ and distributes the remaining
    (1-w) mass according to a Gumbel distribution centred above ỹ. The
    Gumbel component's right skew captures the asymmetric nature of
    underreporting: the true fatality count is more likely to be above
    the reported value than below it.

    Args:
        y_reported: UCDP best estimate of fatalities for the event.
        violence_type: 1 = state-based, 2 = non-state, 3 = one-sided,
            4 = all types pooled.

    Returns:
        Callable F_obs(z) that takes a 1D array and returns CDF values.
    """
    if y_reported <= 0:
        def cdf(z: NDArray[np.float64]) -> NDArray[np.float64]:
            return (z >= 0).astype(np.float64)
        return cdf

    mu_g, beta_g, w = _rvi_gumbel_params(y_reported, violence_type)

    def cdf(z: NDArray[np.float64]) -> NDArray[np.float64]:
        # Point mass component: step at y_reported
        point_mass = (z >= y_reported).astype(np.float64)
        # Gumbel CDF: exp(-exp(-(z - mu) / beta))
        gumbel = np.exp(-np.exp(-(z - mu_g) / beta_g))
        return w * point_mass + (1.0 - w) * gumbel

    return cdf


def sample_from_f_obs_rvi_gumbel(
    y_reported: float,
    violence_type: int = 1,
    n: int = 500,
    seed: int = 0,
) -> NDArray[np.float64]:
    """Draw samples from the RVI Gumbel mixture distribution.

    Returns 1D array of shape (n,).
    """
    if y_reported <= 0:
        return np.zeros(n)

    mu_g, beta_g, w = _rvi_gumbel_params(y_reported, violence_type)
    rng = np.random.default_rng(seed)

    # Decide which component each sample comes from
    use_point = rng.random(n) < w
    # Gumbel samples: inverse CDF = mu - beta * log(-log(U))
    u = rng.random(n)
    gumbel_samples = mu_g - beta_g * np.log(-np.log(np.clip(u, 1e-15, 1 - 1e-15)))

    samples = np.where(use_point, y_reported, gumbel_samples)
    return np.maximum(samples, 0.0)  # fatalities can't be negative


# Suppress unused import warning; lognorm kept for future closed-form expansion
_ = lognorm
