"""Failing test stubs from falsification audit: figure correctness (round 6).

Claim: "All plots are correct, they are correctly represented in both
        caption and main text, and they convey what they are meant to convey."

Focus: code-to-figure-to-caption consistency, visual accuracy, quantitative
       correctness of plotted data.

Audit date: 2026-04-21
Verdict: CONTESTED (0 hard, 1 soft falsification, 6 survived, 1 observation)

Each test below encodes a specific falsification finding.
"""

from __future__ import annotations

from pathlib import Path

PAPER_DIR = Path(__file__).resolve().parent.parent / "paper"
SECTIONS = PAPER_DIR / "sections"
SRC_DIR = Path(__file__).resolve().parent.parent / "src" / "cramer_distance"


# ---------------------------------------------------------------------------
# P1 — SOFT: fill_between label says (F-G)² but shading shows |F-G|
# ---------------------------------------------------------------------------
def test_figure1_shading_label_matches_what_is_plotted():
    r"""Figure 1's legend labels the shading as '(F_pred - F_obs)^2 area'
    in both panels. But matplotlib's fill_between(z, f_pred, f_obs) shades
    the region where the height at each z is |F_pred - F_obs|, not
    (F_pred - F_obs)^2. The label is quantitatively wrong: for the right
    panel, integral |F-G| = 3.83 while integral (F-G)^2 = 0.21 (18x ratio).

    The visual conveys the right qualitative message, but the label, caption
    ('The CRPS integrand'), and main text ('shows the integrand of classical
    CRPS') all claim the shading represents the squared integrand.

    Fix options:
    (a) Change the legend label to '|F_pred - F_obs| area' or just
        'score contribution' — simplest, preserves the visual.
    (b) Actually plot (f_pred - f_obs)**2 as the shaded region via
        fill_between(z, 0, (f_pred - f_obs)**2) — changes the visual.
    (c) Adjust caption/text to say 'illustrates the CDF overlap' rather
        than 'shows the integrand'."""
    figures_py = (SRC_DIR / "figures.py").read_text()

    # The label should NOT claim the shading is (F-G)^2 if fill_between
    # plots |F-G|.  Either the label should drop the square, or the code
    # should actually plot the squared difference.
    has_squared_label = r"$(F_{\mathrm{pred}} - F_{\mathrm{obs}})^2$" in figures_py

    if has_squared_label:
        # Check whether the code actually plots the squared difference
        # rather than raw fill_between between two curves.
        # If it uses fill_between(z, 0, (f_pred - f_obs)**2) that's fine.
        # If it uses fill_between(z, f_pred, f_obs) the label is wrong.
        plots_squared = "(f_pred - f_obs)**2" in figures_py or (
            "(f_pred - f_obs_" in figures_py and "**2" in figures_py
        )
        assert plots_squared, (
            "Figure 1 legend labels the shading as '(F_pred - F_obs)^2 area' "
            "but the code uses fill_between(z, f_pred, f_obs) which shades "
            "|F_pred - F_obs|, not (F_pred - F_obs)^2. For the right panel, "
            "the visual area overstates the actual Cramér distance by 18x. "
            "Either change the label or plot the actual squared difference."
        )
