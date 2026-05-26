"""Real-data empirical comparison for the Cramér distance paper.

Loads UCDP/GED conflict data, constructs simple forecasters from
historical statistics, and scores them under classical CRPS and the
Cramér-distance reformulation with multiple F_obs constructors.
Results are written to paper/data/.

Run as a module:

    uv run python -m cramer_distance.real_data

This module requires external data not shipped with the repo.
Place source parquet in data/ (gitignored). Pre-computed results
are in paper/data/ and can be used directly by figures.py.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd
from numpy.typing import NDArray

from cramer_distance.feature_frame_loader import load_feature_frame, load_prediction_frame
from cramer_distance.classical_crps import brocker_smith_crps, classical_crps
from cramer_distance.fuzzy_crps import empirical_cdf_from_samples, fuzzy_crps
from cramer_distance.observation_uncertainty import (
    f_obs_from_bounds,
    f_obs_from_parametric,
    f_obs_from_rvi_gumbel,
    sample_from_f_obs_parametric,
    sample_from_f_obs_rvi_gumbel,
)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

_VIEWPOINT_DEFAULT = (
    Path(__file__).resolve().parents[2] / "data" / "production_parity.parquet"
)

# Assembled grid time encoding: time_id 23869 = 1989-01
_TIME_ORIGIN = 23869  # first time_id in assembled grid
_ORIGIN_YEAR = 1989
_ORIGIN_MONTH = 1


def _year_month_to_time_id(year: int, month: int) -> int:
    """Convert (year, month) to assembled-grid time_id."""
    return _TIME_ORIGIN + (year - _ORIGIN_YEAR) * 12 + (month - _ORIGIN_MONTH)


# GED feature columns in assembled grid (indices 1, 3, 5 = sb_best, ns_best, os_best)
_GED_BEST_COLS = {"ged_sb_best": 1, "ged_ns_best": 3, "ged_os_best": 5}


# ---------------------------------------------------------------------------
# Data loading
# ---------------------------------------------------------------------------


_TOV_MAP = {1: "state-based", 2: "non-state", 3: "one-sided"}


def load_observations(
    viewpoint_path: Path | None = None,
    eval_start: int = 2020,
    eval_end: int = 2024,
    violence_type: int | None = None,
) -> pd.DataFrame:
    """Load UCDP events and aggregate to cell-month with bounds.

    Args:
        viewpoint_path: Path to viewpoint parquet.
        eval_start: First evaluation year (inclusive).
        eval_end: Last evaluation year (inclusive).
        violence_type: If set, filter to this UCDP violence type
            (1 = state-based, 2 = non-state, 3 = one-sided) before
            aggregation.  Default ``None`` pools all types.

    Returns DataFrame with columns:
        priogrid_gid, year, month, best, low, high, n_events
    Filtered to eval window and best > 0.
    """
    vp = viewpoint_path or _VIEWPOINT_DEFAULT
    cols = ["date_month", "year", "priogrid_gid", "best", "low", "high"]
    if violence_type is not None:
        cols.append("type_of_violence")
    df = pd.read_parquet(vp, columns=cols)
    df = df[(df["year"] >= eval_start) & (df["year"] <= eval_end)].copy()

    if violence_type is not None:
        df = df[df["type_of_violence"] == violence_type]

    df["date_month"] = pd.to_datetime(df["date_month"])
    df["month"] = df["date_month"].dt.month

    agg = (
        df.groupby(["priogrid_gid", "year", "month"])
        .agg(best=("best", "sum"), low=("low", "sum"), high=("high", "sum"),
             n_events=("best", "count"))
        .reset_index()
    )
    # Keep only active cell-months
    return agg[agg["best"] > 0].reset_index(drop=True)


_TOV_FEATURE_MAP = {
    1: "ged_sb_best",
    2: "ged_ns_best",
    3: "ged_os_best",
}


def load_historical_stats(
    train_end: int = 2019,
    candidate_units: set[int] | None = None,
    violence_type: int | None = None,
) -> pd.DataFrame:
    """Compute per-cell historical mean and std from assembled grid.

    Args:
        train_end: Last year of training window.
        candidate_units: If given, only compute stats for these priogrid_gids.
            Dramatically speeds up loading by skipping irrelevant cells.
        violence_type: If set, use only the specified type's feature column
            (1 = ged_sb_best, 2 = ged_ns_best, 3 = ged_os_best).
            Default ``None`` sums all three.

    Returns DataFrame with columns:
        priogrid_gid, hist_mean, hist_std, n_active_months
    """
    ff = load_feature_frame()
    features = ff["features"]
    time_ids = ff["time_ids"]
    unit_ids = ff["unit_ids"]
    feature_names = ff["feature_names"]

    if violence_type is not None:
        col = _TOV_FEATURE_MAP[violence_type]
        total_ged = features[:, feature_names.index(col)]
    else:
        ged_idx = [feature_names.index(c) for c in ["ged_sb_best", "ged_ns_best", "ged_os_best"]]
        total_ged = features[:, ged_idx].sum(axis=1)

    # Filter to training window
    train_end_tid = _year_month_to_time_id(train_end, 12)
    mask = time_ids <= train_end_tid

    # Optionally filter to candidate units (huge speedup)
    if candidate_units is not None:
        unit_mask = np.isin(unit_ids, np.array(list(candidate_units)))
        mask = mask & unit_mask

    train_ged = total_ged[mask]
    train_units = unit_ids[mask]

    # Vectorised groupby: build a DataFrame, filter to active, then aggregate
    train_df = pd.DataFrame({"priogrid_gid": train_units, "ged": train_ged})
    train_df = train_df[train_df["ged"] > 0]

    grouped = train_df.groupby("priogrid_gid")["ged"].agg(["mean", "std", "count"])
    grouped.columns = ["hist_mean", "hist_std", "n_active_months"]
    grouped = grouped[grouped["n_active_months"] >= 3].reset_index()
    grouped["hist_std"] = grouped["hist_std"].fillna(0.0)

    return grouped


# ---------------------------------------------------------------------------
# Forecaster construction
# ---------------------------------------------------------------------------


def build_forecast_samples(
    best: float,
    hist_std: float,
    hist_mean: float,
    n_samples: int = 4000,
    seed: int = 0,
    tight_sigma: float = 0.05,
) -> tuple[NDArray[np.float64], NDArray[np.float64], float]:
    """Build tight and honest forecast sample arrays for one cell-month.

    Both forecasters are centred on the observation's best estimate (like
    the controlled demo). This isolates the effect of forecast spread on
    scoring — the only difference is how much uncertainty each forecaster
    claims.

    Tight: LogNormal centred on log(best) with σ = tight_sigma.
    Honest: LogNormal centred on log(best) with σ derived from the
    cell's empirical coefficient of variation.

    Returns (tight_samples, honest_samples, honest_sigma).
    """
    rng = np.random.default_rng(seed)
    log_mu = np.log(max(best, 1e-6))

    # Tight forecaster: claims to know the answer precisely
    tight = np.exp(rng.normal(log_mu, tight_sigma, n_samples))

    # Honest forecaster: uses empirical variability
    # Convert hist_std to approximate log-space sigma
    # σ_log ≈ sqrt(log(1 + (std/mean)²))
    cv = hist_std / max(hist_mean, 1e-6)
    honest_sigma = float(np.sqrt(np.log(1 + cv**2)))
    honest_sigma = float(np.clip(honest_sigma, 0.1, 2.0))

    honest = np.exp(rng.normal(log_mu, honest_sigma, n_samples))
    return tight, honest, honest_sigma


# ---------------------------------------------------------------------------
# Scoring
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class CellMonthScores:
    """Scores for one cell-month under all metrics."""

    priogrid_gid: int
    year: int
    month: int
    best: float
    low: float
    high: float
    hist_mean: float
    honest_sigma: float
    tight_classical: float
    honest_classical: float
    tight_parametric: float
    honest_parametric: float
    tight_bounds: float | None  # None when low == high
    honest_bounds: float | None


def score_cell_month(
    tight_samples: NDArray[np.float64],
    honest_samples: NDArray[np.float64],
    best: float,
    low: float,
    high: float,
    relative_sigma: float = 0.4,
    n_bs_draws: int = 2000,
    bs_seed: int = 0,
    violence_type: int = 1,
    skip_bs: bool = False,
) -> dict[str, float | None]:
    """Score both forecasters under classical CRPS + all constructors + BS."""
    # Classical CRPS
    tight_classical = classical_crps(tight_samples, best)
    honest_classical = classical_crps(honest_samples, best)

    # Constructor 2: parametric F_obs
    f_obs_param = f_obs_from_parametric(best, relative_sigma=relative_sigma)
    f_tight = empirical_cdf_from_samples(tight_samples)
    f_honest = empirical_cdf_from_samples(honest_samples)
    grid_max = float(max(np.max(tight_samples), np.max(honest_samples), best * 3))

    tight_parametric = fuzzy_crps(f_tight, f_obs_param, grid_min=0.0, grid_max=grid_max, grid_n=4001)
    honest_parametric = fuzzy_crps(f_honest, f_obs_param, grid_min=0.0, grid_max=grid_max, grid_n=4001)

    # Bröcker-Smith: E[CRPS(F, Y)] where Y ~ F_obs (parametric)
    tight_bs = None
    honest_bs = None
    if not skip_bs:
        obs_draws = sample_from_f_obs_parametric(
            best, relative_sigma=relative_sigma, n=n_bs_draws, seed=bs_seed,
        )
        tight_bs = brocker_smith_crps(tight_samples, obs_draws)
        honest_bs = brocker_smith_crps(honest_samples, obs_draws)

    # Constructor 1: bounds-based F_obs (only when bounds are valid)
    tight_bounds = None
    honest_bounds = None
    low_safe = min(low, best)
    high_safe = max(high, best)
    if high_safe > low_safe and low_safe > 0:
        f_obs_bnd = f_obs_from_bounds(low_safe, best, high_safe, distribution="lognormal")
        tight_bounds = fuzzy_crps(f_tight, f_obs_bnd, grid_min=0.0, grid_max=grid_max, grid_n=4001)
        honest_bounds = fuzzy_crps(f_honest, f_obs_bnd, grid_min=0.0, grid_max=grid_max, grid_n=4001)

    # Constructor 4: Vesco et al. RVI Gumbel mixture
    f_obs_rvi = f_obs_from_rvi_gumbel(best, violence_type=violence_type)
    tight_rvi = fuzzy_crps(f_tight, f_obs_rvi, grid_min=0.0, grid_max=grid_max, grid_n=4001)
    honest_rvi = fuzzy_crps(f_honest, f_obs_rvi, grid_min=0.0, grid_max=grid_max, grid_n=4001)

    # BS with RVI draws
    tight_rvi_bs = None
    honest_rvi_bs = None
    if not skip_bs:
        rvi_draws = sample_from_f_obs_rvi_gumbel(
            best, violence_type=violence_type, n=n_bs_draws, seed=bs_seed,
        )
        tight_rvi_bs = brocker_smith_crps(tight_samples, rvi_draws)
        honest_rvi_bs = brocker_smith_crps(honest_samples, rvi_draws)

    return {
        "tight_classical": tight_classical,
        "honest_classical": honest_classical,
        "tight_parametric": tight_parametric,
        "honest_parametric": honest_parametric,
        "tight_bs": tight_bs,
        "honest_bs": honest_bs,
        "tight_bounds": tight_bounds,
        "honest_bounds": honest_bounds,
        "tight_rvi": tight_rvi,
        "honest_rvi": honest_rvi,
        "tight_rvi_bs": tight_rvi_bs,
        "honest_rvi_bs": honest_rvi_bs,
    }


# ---------------------------------------------------------------------------
# Main comparison
# ---------------------------------------------------------------------------


def run_real_data_comparison(
    eval_start: int = 2020,
    eval_end: int = 2024,
    relative_sigma: float = 0.4,
    n_samples: int = 4000,
    seed: int = 0,
    max_cells: int | None = None,
    violence_type: int | None = None,
) -> pd.DataFrame:
    """Run the full real-data comparison.

    Args:
        violence_type: If set, filter observations and historical stats
            to this UCDP violence type (1=SB, 2=NS, 3=OS).

    Returns a DataFrame with one row per scored cell-month.
    """
    tov_label = _TOV_MAP.get(violence_type, "all") if violence_type else "all"
    print(f"Loading observations (type={tov_label})...")
    obs = load_observations(
        eval_start=eval_start, eval_end=eval_end, violence_type=violence_type,
    )
    print(f"  {len(obs)} active cell-months in {eval_start}–{eval_end}")

    print("Loading historical statistics...")
    candidate_units = set(obs["priogrid_gid"].unique())
    hist = load_historical_stats(
        train_end=eval_start - 1, candidate_units=candidate_units,
        violence_type=violence_type,
    )
    print(f"  {len(hist)} cells with ≥3 active months in training window")

    # Merge
    merged = obs.merge(hist, on="priogrid_gid", how="inner")
    print(f"  {len(merged)} cell-months after joining with history")

    if max_cells is not None:
        merged = merged.head(max_cells)
        print(f"  (capped to {max_cells} for testing)")

    # RVI violence_type defaults to 1 (state-based) when pooling all types
    rvi_tov = violence_type if violence_type is not None else 1

    rows = []
    n = len(merged)
    for i, r in merged.iterrows():
        if i > 0 and int(i) % 1000 == 0:
            print(f"  scoring {i}/{n}...")

        tight, honest, honest_sigma = build_forecast_samples(
            best=r["best"],
            hist_std=r["hist_std"],
            hist_mean=r["hist_mean"],
            n_samples=n_samples,
            seed=seed + int(i),
        )
        scores = score_cell_month(
            tight, honest,
            best=r["best"], low=r["low"], high=r["high"],
            relative_sigma=relative_sigma,
            bs_seed=seed + int(i) + 100000,
            violence_type=rvi_tov,
        )

        rows.append({
            "priogrid_gid": r["priogrid_gid"],
            "year": r["year"],
            "month": r["month"],
            "best": r["best"],
            "low": r["low"],
            "high": r["high"],
            "hist_mean": r["hist_mean"],
            "honest_sigma": honest_sigma,
            **scores,
        })

    return pd.DataFrame(rows)


def summarise(df: pd.DataFrame) -> str:
    """Pretty-print summary of the comparison results."""
    lines = []
    lines.append(f"Real-data empirical comparison: {len(df)} cell-months")
    lines.append("")

    # Classical CRPS
    t_cl = df["tight_classical"].mean()
    h_cl = df["honest_classical"].mean()
    lines.append("Classical CRPS (mean):")
    lines.append(f"  Tight:  {t_cl:.4f}")
    lines.append(f"  Honest: {h_cl:.4f}")
    lines.append(f"  Winner: {'Tight' if t_cl < h_cl else 'Honest'}")
    lines.append("")

    # Constructor 2: parametric
    t_p = df["tight_parametric"].mean()
    h_p = df["honest_parametric"].mean()
    lines.append("Constructor 2 — Parametric (mean):")
    lines.append(f"  Tight:  {t_p:.4f}")
    lines.append(f"  Honest: {h_p:.4f}")
    lines.append(f"  Winner: {'Tight' if t_p < h_p else 'Honest'}")

    reversal_p = (df["honest_parametric"] < df["tight_parametric"]).mean()
    lines.append(f"  Cell-months with reversal: {reversal_p:.1%}")
    lines.append("")

    # Constructor 1: bounds (only where available)
    bounds = df.dropna(subset=["tight_bounds", "honest_bounds"])
    if len(bounds) > 0:
        t_b = bounds["tight_bounds"].mean()
        h_b = bounds["honest_bounds"].mean()
        lines.append(f"Constructor 1 — Bounds (mean, N={len(bounds)}):")
        lines.append(f"  Tight:  {t_b:.4f}")
        lines.append(f"  Honest: {h_b:.4f}")
        lines.append(f"  Winner: {'Tight' if t_b < h_b else 'Honest'}")

        reversal_b = (bounds["honest_bounds"] < bounds["tight_bounds"]).mean()
        lines.append(f"  Cell-months with reversal: {reversal_b:.1%}")
    else:
        lines.append("Constructor 1 — Bounds: no cell-months with genuine uncertainty")

    # Bröcker-Smith comparison (parametric)
    if "tight_bs" in df.columns:
        lines.append("")
        t_bs = df["tight_bs"].mean()
        h_bs = df["honest_bs"].mean()
        lines.append("Bröcker-Smith E[CRPS(F,Y)] — Parametric (mean):")
        lines.append(f"  Tight:  {t_bs:.4f}")
        lines.append(f"  Honest: {h_bs:.4f}")
        lines.append(f"  Winner: {'Tight' if t_bs < h_bs else 'Honest'}")

        reversal_bs = (df["honest_bs"] < df["tight_bs"]).mean()
        lines.append(f"  Cell-months with reversal: {reversal_bs:.1%}")

        # Concordance with Cramér
        cramer_honest_wins = df["honest_parametric"] < df["tight_parametric"]
        bs_honest_wins = df["honest_bs"] < df["tight_bs"]
        concordance = (cramer_honest_wins == bs_honest_wins).mean()
        lines.append(f"  Ranking concordance with Cramér: {concordance:.1%}")

    # RVI Gumbel constructor
    if "tight_rvi" in df.columns:
        lines.append("")
        t_rvi = df["tight_rvi"].mean()
        h_rvi = df["honest_rvi"].mean()
        lines.append("Constructor 4 — RVI Gumbel (mean):")
        lines.append(f"  Tight:  {t_rvi:.4f}")
        lines.append(f"  Honest: {h_rvi:.4f}")
        lines.append(f"  Winner: {'Tight' if t_rvi < h_rvi else 'Honest'}")

        reversal_rvi = (df["honest_rvi"] < df["tight_rvi"]).mean()
        lines.append(f"  Cell-months with reversal: {reversal_rvi:.1%}")

    if "tight_rvi_bs" in df.columns:
        lines.append("")
        t_rbs = df["tight_rvi_bs"].mean()
        h_rbs = df["honest_rvi_bs"].mean()
        lines.append("Bröcker-Smith E[CRPS(F,Y)] — RVI (mean):")
        lines.append(f"  Tight:  {t_rbs:.4f}")
        lines.append(f"  Honest: {h_rbs:.4f}")
        lines.append(f"  Winner: {'Tight' if t_rbs < h_rbs else 'Honest'}")

        reversal_rbs = (df["honest_rvi_bs"] < df["tight_rvi_bs"]).mean()
        lines.append(f"  Cell-months with reversal: {reversal_rbs:.1%}")

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# HydraNet scoring
# ---------------------------------------------------------------------------

_TOV_TARGET_MAP = {1: "lr_sb_best", 2: "lr_ns_best", 3: "lr_os_best"}


def _month_id_to_year_month(month_id: int) -> tuple[int, int]:
    year = (month_id - 1) // 12 + 1980
    month = (month_id - 1) % 12 + 1
    return year, month


def score_hydranet(
    violence_type: int = 1,
    eval_start: int = 2021,
    eval_end: int = 2024,
    relative_sigma: float = 0.4,
    tight_sigma: float = 0.05,
    n_bs_draws: int = 2000,
    seed: int = 0,
    predictions_dir: Path | None = None,
) -> pd.DataFrame:
    """Score HydraNet MC Dropout predictions against UCDP observations.

    For each cell-month, constructs two versions of the same model output:
      - Full MC Dropout: the 64 predictive samples as empirical CDF
      - Tight: LogNormal(log(mean), 0.05) — discards uncertainty quantification

    Returns a DataFrame matching the hydranet_scores_*.csv format.
    """
    target = _TOV_TARGET_MAP[violence_type]
    tov_label = _TOV_MAP[violence_type]
    print(f"\nScoring HydraNet ({tov_label}, target={target})...")

    # Load predictions
    pf = load_prediction_frame(target, predictions_dir=predictions_dir)
    pred_times = pf["time_ids"]
    pred_units = pf["unit_ids"]
    pred_samples = pf["predictions"]

    # Build prediction DataFrame for joining
    pred_df = pd.DataFrame({
        "month_id": pred_times,
        "priogrid_gid": pred_units,
    })
    pred_df["year"] = pred_df["month_id"].apply(lambda m: _month_id_to_year_month(m)[0])
    pred_df["month"] = pred_df["month_id"].apply(lambda m: _month_id_to_year_month(m)[1])
    pred_df["pred_idx"] = np.arange(len(pred_df))

    # Filter to eval window
    pred_df = pred_df[
        (pred_df["year"] >= eval_start) & (pred_df["year"] <= eval_end)
    ].copy()

    # Load UCDP observations
    print(f"  Loading observations (type={tov_label})...")
    obs = load_observations(
        eval_start=eval_start, eval_end=eval_end, violence_type=violence_type,
    )
    print(f"  {len(obs)} active cell-months")

    # Join predictions with observations
    merged = obs.merge(
        pred_df[["priogrid_gid", "year", "month", "pred_idx"]],
        on=["priogrid_gid", "year", "month"],
        how="inner",
    )
    print(f"  {len(merged)} cell-months after join")

    rows = []
    n = len(merged)
    rng = np.random.default_rng(seed)

    for i, r in merged.iterrows():
        if len(rows) > 0 and len(rows) % 1000 == 0:
            print(f"  scoring {len(rows)}/{n}...")

        samples = pred_samples[r["pred_idx"]].astype(np.float64)
        post_mean = float(samples.mean())
        best = float(r["best"])

        # When the model predicts zero, both versions are degenerate
        if post_mean < 1e-4:
            zero_samples = np.zeros(4000)
            scores = score_cell_month(
                zero_samples, zero_samples,
                best=best, low=float(r["low"]), high=float(r["high"]),
                relative_sigma=relative_sigma,
                bs_seed=seed + len(rows) + 200000,
                violence_type=violence_type,
                skip_bs=True,
            )
        else:
            log_mu = np.log(post_mean)
            tight_samples = np.exp(rng.normal(log_mu, tight_sigma, 4000))
            scores = score_cell_month(
                tight_samples, samples,
                best=best, low=float(r["low"]), high=float(r["high"]),
                relative_sigma=relative_sigma,
                bs_seed=seed + len(rows) + 200000,
                violence_type=violence_type,
                skip_bs=True,
            )

        rows.append({
            "priogrid_gid": r["priogrid_gid"],
            "year": r["year"],
            "month": r["month"],
            "best": best,
            "low": r["low"],
            "high": r["high"],
            "post_mean": post_mean,
            **scores,
        })

    return pd.DataFrame(rows)


def summarise_hydranet(df: pd.DataFrame) -> str:
    """Pretty-print summary of HydraNet scoring results."""
    lines = []
    lines.append(f"HydraNet scoring: {len(df)} cell-months")
    lines.append("")

    # Classical CRPS
    tight_wins = (df["tight_classical"] < df["honest_classical"]).sum()
    ties = (df["tight_classical"] == df["honest_classical"]).sum()
    honest_wins = (df["tight_classical"] > df["honest_classical"]).sum()
    lines.append(f"Classical CRPS: tight wins {tight_wins} ({tight_wins/len(df):.1%}), "
                 f"ties {ties} ({ties/len(df):.1%}), "
                 f"honest wins {honest_wins} ({honest_wins/len(df):.1%})")

    # Factor-of-two subset
    ratio = df["post_mean"] / df["best"].clip(lower=1e-6)
    close_mask = (ratio >= 0.5) & (ratio <= 2.0)
    close = df[close_mask]
    if len(close) > 0:
        lines.append(f"\nFactor-of-two subset: {len(close)} cell-months ({len(close)/len(df):.1%})")
        classical_tight_mask = close["tight_classical"] < close["honest_classical"]
        tight_close = classical_tight_mask.sum()
        lines.append(f"  Classical tight wins: {tight_close} ({tight_close/len(close):.1%})")

        if tight_close > 0 and "tight_parametric" in close.columns:
            # Reversal: classical preferred tight, but parametric prefers honest
            classical_tight = close[classical_tight_mask]
            reversal_p = (classical_tight["honest_parametric"] < classical_tight["tight_parametric"]).sum()
            lines.append(f"  Parametric reversal: {reversal_p}/{tight_close} ({reversal_p/tight_close:.1%})")

        if tight_close > 0 and "tight_rvi" in close.columns:
            classical_tight = close[classical_tight_mask]
            reversal_r = (classical_tight["honest_rvi"] < classical_tight["tight_rvi"]).sum()
            lines.append(f"  RVI reversal: {reversal_r}/{tight_close} ({reversal_r/tight_close:.1%})")

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def main() -> None:
    out = Path(__file__).resolve().parents[2] / "paper" / "data"
    out.mkdir(parents=True, exist_ok=True)

    # All types pooled
    results = run_real_data_comparison()
    print()
    print(summarise(results))
    results.to_csv(out / "real_data_scores.csv", index=False)
    print(f"\nResults saved to {out / 'real_data_scores.csv'}")

    # Per-type comparisons
    for tov in (1, 2, 3):
        label = _TOV_MAP[tov]
        print(f"\n{'='*60}")
        print(f"Per-type comparison: {label} (type_of_violence={tov})")
        print(f"{'='*60}")
        res_tov = run_real_data_comparison(violence_type=tov)
        print()
        print(summarise(res_tov))
        res_tov.to_csv(out / f"real_data_scores_{label.replace('-', '_')}.csv", index=False)
        print(f"\nSaved to {out / f'real_data_scores_{label.replace(chr(45), chr(95))}.csv'}")

    # HydraNet per-type scoring
    hydra_labels = {1: "hydranet_scores_state_based.csv",
                    2: "hydranet_scores_non_state.csv",
                    3: "hydranet_scores_one_sided.csv"}
    for tov in (1, 2, 3):
        label = _TOV_MAP[tov]
        print(f"\n{'='*60}")
        print(f"HydraNet scoring: {label} (type_of_violence={tov})")
        print(f"{'='*60}")
        hydra = score_hydranet(violence_type=tov)
        print()
        print(summarise_hydranet(hydra))
        fname = hydra_labels[tov]
        hydra.to_csv(out / fname, index=False)
        print(f"\nSaved to {out / fname}")


if __name__ == "__main__":
    main()
