"""Failing test stubs from falsification audit: reproducibility (round 4).

Claim: "Three top-tier, expert academics with deep knowledge of this domain
        would accept this paper for publication with no or minor revisions."

Focus: reproducibility of reported numbers, numerical adequacy, experimental
       design, consistency between code and paper.

Audit date: 2026-04-21
Verdict: CONTESTED (0 hard, 1 soft falsification, 7 survived, 1 observation)
Resolution: Soft falsification resolved 2026-04-21.

Each test below encodes a specific falsification finding. Tests marked xfail
are expected to FAIL until the corresponding issue is resolved.
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd

PAPER_DIR = Path(__file__).resolve().parent.parent / "paper"
SECTIONS = PAPER_DIR / "sections"
DATA_DIR = PAPER_DIR / "data"


# ---------------------------------------------------------------------------
# BONUS — SOFT (RESOLVED): Paper reports stale sigma statistics
# ---------------------------------------------------------------------------
def test_paper_sigma_statistics_match_code():
    """The sigma statistics reported in section 6 should match what the
    code and cached CSV actually produce."""
    csv_path = DATA_DIR / "real_data_scores.csv"
    assert csv_path.exists(), f"Missing {csv_path}"

    df = pd.read_csv(csv_path)
    median_sigma = df["honest_sigma"].median()
    q25 = df["honest_sigma"].quantile(0.25)
    q75 = df["honest_sigma"].quantile(0.75)

    # Paper claims: "Median sigma_cell = 0.97; interquartile range [0.81, 1.16]"
    # Check that the paper's claimed values are close to reality
    # Tolerance: 0.05 (generous — these are summary statistics at 2dp)
    assert abs(median_sigma - 0.97) < 0.05, (
        f"Paper claims median sigma = 0.97 but CSV gives {median_sigma:.3f}"
    )
    assert abs(q25 - 0.81) < 0.05, (
        f"Paper claims Q25 = 0.81 but CSV gives {q25:.3f}"
    )
    assert abs(q75 - 1.16) < 0.05, (
        f"Paper claims Q75 = 1.16 but CSV gives {q75:.3f}"
    )
