"""Forecast evaluation with observational uncertainty: a Cramér-distance perspective.

The standard Continuous Ranked Probability Score uses an indicator function
`1{y ≤ z}` that treats the observation y as known with infinite precision.
For data with measurement error — UCDP fatality counts, weather observations,
epidemiological surveillance — this assumption penalises forecasts that
honestly report uncertainty about noisy observations.

This module reformulates CRPS evaluation against a smooth observational CDF
F_obs(z) rather than a step indicator. The resulting integral

    ∫ (F_pred(z) - F_obs(z))^2 dz

is the Cramér distance between the two distributions (also called the L2 CDF
distance or integrated Brier score against a distributional target). It is
NOT a new scoring rule — it has been a standard quantity in probability and
forecast verification for decades (Cramér 1928; Székely & Rizzo 2013;
Thorarinsdottir et al. 2013; Gneiting & Ranjan 2011). Classical CRPS is the
special case F_obs = δ_y. We call the reformulation "fuzzy CRPS" for
convenience but the contribution of this module is operational: three
principled constructors for F_obs and a pipeline that uses them.

Three constructors are provided for F_obs:

1. From external data quality bounds (e.g., UCDP low/high estimates)
2. Parametric — LogNormal centered on y with fixed relative sigma
3. Model-derived — from a trained weight head (see
   `cramer_distance.observation_uncertainty.f_obs_from_weight_head`)

Consistency under stochastic observations is verified numerically via
verify_propriety_in_expectation. An analytical proof via the energy-distance
framework is possible but requires care about the joint distribution of y
and F_obs(y); we leave it to future work.
"""

from cramer_distance.classical_crps import classical_crps
from cramer_distance.fuzzy_crps import fuzzy_crps
from cramer_distance.observation_uncertainty import (
    f_obs_from_bounds,
    f_obs_from_parametric,
    f_obs_from_weight_head,
)
from cramer_distance.propriety import (
    lognormal_cdf,
    normal_cdf,
    verify_propriety_in_expectation,
    verify_propriety_numerical,
)

__all__ = [
    "classical_crps",
    "fuzzy_crps",
    "f_obs_from_bounds",
    "f_obs_from_parametric",
    "f_obs_from_weight_head",
    "lognormal_cdf",
    "normal_cdf",
    "verify_propriety_in_expectation",
    "verify_propriety_numerical",
]
