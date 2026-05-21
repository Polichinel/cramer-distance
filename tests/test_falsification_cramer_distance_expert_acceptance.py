"""Failing test stubs from falsification audit: expert acceptance (round 3).

Claim: "Three top-tier, expert academics with deep knowledge of this domain
        would accept this paper for publication with no or minor revisions."

Focus: scientific rigour, honesty, and the presence of an actual contribution.

Audit date: 2026-04-21
Verdict: CONTESTED (0 hard, 2 soft falsifications, 5 survived)
Resolution: Both soft falsifications resolved 2026-04-21.

Each test below encodes a specific falsification finding. Tests that were
marked xfail have been resolved and now pass.
"""

from __future__ import annotations

from pathlib import Path

PAPER_DIR = Path(__file__).resolve().parent.parent / "paper"
SECTIONS = PAPER_DIR / "sections"


# ---------------------------------------------------------------------------
# P3 — SOFT (RESOLVED): Convolution notation misleading for LogNormal
# ---------------------------------------------------------------------------
def test_convolution_notation_correct_for_lognormal():
    """§5's convolution notation should not use additive notation for
    a multiplicative noise model."""
    sec5 = (SECTIONS / "05_propriety.tex").read_text()

    # The paper should either:
    # (a) Use multiplicative notation for LogNormal, or
    # (b) Note that the convolution is in log-space, or
    # (c) Note that the √(σ²+σ²) formula is approximate for LogNormal
    has_multiplicative_note = any(
        phrase in sec5.lower()
        for phrase in [
            "multiplicative",
            "log-space",
            "in log space",
            "product of",
            "approximate for log-normal",
            "approximate for lognormal",
            "exact for gaussian",
        ]
    )

    assert has_multiplicative_note, (
        "§5 uses Q * N(0, σ²_obs) notation (additive convolution) to explain "
        "a mechanism that is multiplicative for LogNormal. The √(σ²+σ²) "
        "formula is exact for Gaussian but approximate for LogNormal "
        "(gap ≈ 0.006). The paper should note this distinction."
    )


# ---------------------------------------------------------------------------
# P7 — SOFT (RESOLVED): Table 4 "Propriety bias" column header ambiguous
# ---------------------------------------------------------------------------
def test_table_4_column_header_says_location():
    """Table 4's 'Propriety bias' column should explicitly say 'Location bias'
    to avoid confusion with the non-zero scale bias reported in §5."""
    sec6 = (SECTIONS / "06_demonstration.tex").read_text()

    # Find the table header row
    # Current: "Location bias" (was "Propriety bias")
    uses_location_qualifier = (
        "location bias" in sec6.lower()
        or "\\mu\\text{-bias}" in sec6
        or "Location bias" in sec6
        or "Loc.\\ bias" in sec6
    )

    # Also acceptable: the table caption explicitly warns about scale bias
    caption_warns_scale = (
        "scale bias" in sec6.lower()
        or "scale consistency" in sec6.lower()
        or "does not reflect scale" in sec6.lower()
    )

    assert uses_location_qualifier or caption_warns_scale, (
        "Table 4 header says 'Propriety bias' = 0.000 but §5 shows scale "
        "bias > 0. Either rename the column to 'Location bias' or add a "
        "caption note about the scale-consistency caveat."
    )
