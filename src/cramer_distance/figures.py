"""Figure generation for the Cramér distance paper.

Run as a module to regenerate all PDF figures into
paper/figures/:

    uv run python -m cramer_distance.figures

Four figures:

1. step_vs_sigmoid.pdf — the visual argument. Shows the classical CRPS
   integrand (step function indicator) next to a smooth observational CDF,
   highlighting why the integrand area changes.

2. propriety_verification.pdf — numerical sweep of a forecast parameter
   showing fuzzy CRPS is minimised at the truth.

3. uncertainty_aware_ranking.pdf — bar chart of classical vs fuzzy CRPS
   for a "tight" and "honest" forecaster, demonstrating the ranking
   reversal that motivates fuzzy CRPS.

4. real_data_comparison.pdf — reversal rates and score-difference
   distributions on UCDP conflict data. Reads pre-computed CSVs from
   paper/data/; skipped if the CSV is absent.
"""

from __future__ import annotations

from pathlib import Path

import matplotlib as mpl
import matplotlib.pyplot as plt
import numpy as np

from cramer_distance.demo import run_demo
from cramer_distance.observation_uncertainty import f_obs_from_parametric
from cramer_distance.propriety import verify_propriety_numerical

FIG_DIR = Path(__file__).resolve().parents[2] / "paper" / "figures"

# --- Publication style --------------------------------------------------
_PALETTE = {
    "blue": "#2166ac",
    "red": "#b2182b",
    "light_red": "#d6604d",
    "light_blue": "#4393c3",
    "grey": "#636363",
}


def _apply_style() -> None:
    """Consistent publication styling across all figures."""
    mpl.rcParams.update({
        "font.family": "serif",
        "font.size": 10,
        "axes.labelsize": 11,
        "axes.titlesize": 11,
        "legend.fontsize": 9,
        "xtick.labelsize": 9,
        "ytick.labelsize": 9,
        "axes.spines.top": False,
        "axes.spines.right": False,
        "axes.linewidth": 0.8,
        "lines.linewidth": 1.8,
        "figure.dpi": 300,
    })


def _save(fig: plt.Figure, name: str) -> None:
    FIG_DIR.mkdir(parents=True, exist_ok=True)
    out = FIG_DIR / name
    fig.savefig(out, dpi=300, bbox_inches="tight")
    plt.close(fig)
    print(f"  saved {out.relative_to(FIG_DIR.parents[2])}")


def figure_step_vs_sigmoid() -> None:
    """The visual argument: classical step indicator vs smooth observational CDF."""
    print("figure_step_vs_sigmoid()")
    fig, axes = plt.subplots(1, 2, figsize=(10, 3.8), sharey=True)

    z = np.linspace(0, 100, 1001)
    y_obs = 50.0

    # Forecast CDF: a moderately wide LogNormal centered on the observation
    log_y = np.log(y_obs)
    forecast_sigma = 0.4
    from scipy.stats import norm
    f_pred = norm.cdf(np.log(np.maximum(z, 1e-12)), loc=log_y, scale=forecast_sigma)

    # Left panel: classical CRPS — step indicator at y_obs
    f_obs_classical = (z >= y_obs).astype(float)
    axes[0].fill_between(
        z, f_pred, f_obs_classical, alpha=0.25, color=_PALETTE["light_red"],
        label=r"CDF difference",
    )
    axes[0].plot(z, f_pred, color=_PALETTE["blue"], label=r"$F_{\mathrm{pred}}$")
    axes[0].plot(
        z, f_obs_classical, color="black",
        label=r"$F_{\mathrm{obs}}$ = step at $y$",
    )
    axes[0].axvline(y_obs, color=_PALETTE["grey"], linestyle=":", alpha=0.5)
    axes[0].set_xlabel("$z$")
    axes[0].set_ylabel("CDF")
    axes[0].set_title(r"Classical CRPS ($F_{\mathrm{obs}}$ = step indicator)")
    axes[0].legend(loc="upper left")

    # Right panel: fuzzy CRPS — smooth F_obs reflecting observational uncertainty
    f_obs_smooth = f_obs_from_parametric(y=y_obs, relative_sigma=0.3)(z)
    axes[1].fill_between(
        z, f_pred, f_obs_smooth, alpha=0.25, color=_PALETTE["light_blue"],
        label=r"CDF difference",
    )
    axes[1].plot(z, f_pred, color=_PALETTE["blue"], label=r"$F_{\mathrm{pred}}$")
    axes[1].plot(
        z, f_obs_smooth, color="black",
        label=r"$F_{\mathrm{obs}}$ = LogNormal($y$, 0.3)",
    )
    axes[1].axvline(y_obs, color=_PALETTE["grey"], linestyle=":", alpha=0.5)
    axes[1].set_xlabel("$z$")
    axes[1].set_title(
        r"Cram$\acute{\mathrm{e}}$r distance"
        r" ($F_{\mathrm{obs}}$ = smooth CDF)"
    )
    axes[1].legend(loc="upper left")

    fig.tight_layout()
    _save(fig, "step_vs_sigmoid.pdf")


def figure_propriety_verification() -> None:
    """Numerical propriety: fuzzy CRPS minimised at the true mu."""
    print("figure_propriety_verification()")
    true_mu = 1.0
    true_sigma = 0.3
    mu_sweep, scores, argmin = verify_propriety_numerical(
        true_mu=true_mu,
        true_sigma=true_sigma,
        mu_sweep=np.linspace(-1.0, 3.0, 81),
    )

    fig, ax = plt.subplots(figsize=(5.5, 4))
    ax.plot(mu_sweep, scores, color=_PALETTE["blue"])
    ax.axvline(
        true_mu, color="black", linestyle="--", alpha=0.7,
        label=f"True $\\mu$ = {true_mu}",
    )
    ax.scatter([argmin], [scores.min()], color=_PALETTE["light_red"], s=60, zorder=5,
               label=f"Argmin = {argmin:.3f}")
    ax.set_xlabel(r"Forecast $\mu$")
    ax.set_ylabel(r"$\mathrm{CRPS}_{\mathrm{obs}}$")
    ax.set_title(r"$L^2$ minimisation: score minimised at the true $\mu$")
    ax.legend()
    ax.grid(alpha=0.15, linewidth=0.5)
    fig.tight_layout()
    _save(fig, "propriety_verification.pdf")


def figure_uncertainty_aware_ranking() -> None:
    """Ranking reversal: tight vs honest forecaster under classical and fuzzy CRPS."""
    print("figure_uncertainty_aware_ranking()")
    result = run_demo(
        y=50.0,
        relative_sigma=0.4,
        tight_sigma=0.05,
        honest_sigma=0.4,
    )

    fig, ax = plt.subplots(figsize=(5.5, 4))
    x = np.arange(2)
    width = 0.32

    classical_values = [result.tight_classical, result.honest_classical]
    fuzzy_values = [result.tight_fuzzy, result.honest_fuzzy]

    bars1 = ax.bar(x - width / 2, classical_values, width,
                   label="Classical CRPS", color=_PALETTE["light_red"],
                   edgecolor="white", linewidth=0.5)
    bars2 = ax.bar(x + width / 2, fuzzy_values, width,
                   label=r"Cram$\acute{\mathrm{e}}$r distance",
                   color=_PALETTE["light_blue"],
                   edgecolor="white", linewidth=0.5)

    ax.set_xticks(x)
    ax.set_xticklabels([
        "Tight forecaster\n($\\sigma$=0.05)",
        "Honest forecaster\n($\\sigma$=0.4)",
    ])
    ax.set_ylabel("Score (lower is better)")
    ax.set_title("Ranking reversal under observational uncertainty")
    ax.legend()

    # Annotate bars with values
    for b, v in zip(bars1, classical_values, strict=True):
        ax.text(b.get_x() + b.get_width() / 2, v + 0.08, f"{v:.3f}",
                ha="center", va="bottom", fontsize=8, color=_PALETTE["grey"])
    for b, v in zip(bars2, fuzzy_values, strict=True):
        ax.text(b.get_x() + b.get_width() / 2, v + 0.08, f"{v:.3f}",
                ha="center", va="bottom", fontsize=8, color=_PALETTE["grey"])

    fig.tight_layout()
    _save(fig, "uncertainty_aware_ranking.pdf")


def figure_real_data_comparison() -> None:
    """Real-data ranking reversal on UCDP conflict data."""
    print("figure_real_data_comparison()")
    import pandas as pd

    csv_path = FIG_DIR.parent / "data" / "real_data_scores.csv"
    if not csv_path.exists():
        print(
            f"  SKIP: {csv_path} not found."
            " Run: uv run python -m cramer_distance.real_data"
        )
        return

    df = pd.read_csv(csv_path)

    # Score difference: positive means tight wins, negative means honest wins
    df["diff_classical"] = df["tight_classical"] - df["honest_classical"]
    df["diff_parametric"] = df["tight_parametric"] - df["honest_parametric"]

    fig, axes = plt.subplots(1, 2, figsize=(10, 4))

    # Left panel: reversal rate by honest_sigma bucket
    bins = [0.1, 0.2, 0.4, 0.6, 0.8, 1.0, 1.5, 2.0]
    labels = [f"{a}–{b}" for a, b in zip(bins[:-1], bins[1:], strict=True)]
    df["sigma_bin"] = pd.cut(df["honest_sigma"], bins=bins, labels=labels)
    rev_rates = df.groupby("sigma_bin", observed=True).apply(
        lambda g: (g["honest_parametric"] < g["tight_parametric"]).mean(),
        include_groups=False,
    )
    counts = df.groupby("sigma_bin", observed=True).size()

    ax = axes[0]
    x = np.arange(len(rev_rates))
    bars = ax.bar(x, rev_rates.values * 100, color=_PALETTE["light_blue"],
                  edgecolor="white", linewidth=0.5)
    ax.set_xticks(x)
    ax.set_xticklabels(rev_rates.index, rotation=30, ha="right")
    ax.set_xlabel(r"Honest forecaster $\sigma_{\log}$")
    ax.set_ylabel("Ranking reversal (%)")
    ax.set_title("Reversal rate by forecast uncertainty")
    ax.axhline(50, color=_PALETTE["grey"], linestyle=":", alpha=0.5, linewidth=0.8)

    # Annotate with cell counts
    for b, n in zip(bars, counts.values, strict=True):
        ax.text(b.get_x() + b.get_width() / 2, b.get_height() + 1.5,
                f"n={n}", ha="center", va="bottom", fontsize=7,
                color=_PALETTE["grey"])

    # Right panel: histogram of score differences (parametric)
    # Positive diff = tight has higher score = honest wins
    ax = axes[1]
    moderate = df[df["honest_sigma"] <= 0.8]
    wide = df[df["honest_sigma"] > 1.0]

    bins_hist = np.linspace(-5, 5, 51)
    ax.hist(moderate["diff_parametric"].clip(-5, 5), bins=bins_hist,
            alpha=0.7, color=_PALETTE["light_blue"],
            label=rf"$\sigma_{{\log}} \leq 0.8$ (n={len(moderate)})")
    ax.hist(wide["diff_parametric"].clip(-5, 5), bins=bins_hist,
            alpha=0.5, color=_PALETTE["light_red"],
            label=rf"$\sigma_{{\log}} > 1.0$ (n={len(wide)})")
    ax.axvline(0, color="black", linewidth=0.8)
    ax.set_xlabel(
        r"$\mathrm{CRPS}_{\mathrm{tight}}"
        r" - \mathrm{CRPS}_{\mathrm{honest}}$ (Cramér)"
    )
    ax.set_ylabel("Cell-months")
    ax.set_title("Score difference distribution")
    ax.legend(fontsize=8)

    # Label regions
    ax.text(2.5, ax.get_ylim()[1] * 0.85, "Honest\nwins",
            ha="center", fontsize=8, color=_PALETTE["light_blue"], alpha=0.8)
    ax.text(-2.5, ax.get_ylim()[1] * 0.85, "Tight\nwins",
            ha="center", fontsize=8, color=_PALETTE["light_red"], alpha=0.8)

    fig.tight_layout()
    _save(fig, "real_data_comparison.pdf")


def main() -> None:
    _apply_style()
    figure_step_vs_sigmoid()
    figure_propriety_verification()
    figure_uncertainty_aware_ranking()
    figure_real_data_comparison()


if __name__ == "__main__":
    main()
