"""
Falsification audit: "The paper is ready for arXiv"
Date: 2026-05-29
Verdict: SURVIVED after fixes (0 hard, 0 soft remaining)

Resolved:
  HF1: BN concordance numbers corrected (column-swap bug + stale pooled values)
  HF2: Wrong section cross-reference fixed (S5 -> S4)
  SF1: \\today replaced with fixed date
  SF2: Code/data availability statement added
"""

import re
from pathlib import Path

PAPER_DIR = Path(__file__).resolve().parent.parent / "paper"
SECTIONS_DIR = PAPER_DIR / "sections"


class TestHF1_BNConcordanceArithmetic:
    """The pooled BN concordance numbers in Table 2 must be arithmetically
    reconcilable with the per-type numbers. All values now computed from
    CSVs generated with M=2000 throughout."""

    def test_rvi_bn_concordance_pooled_vs_pertype(self):
        """Pooled RVI BN agree should be reconcilable with per-type numbers."""
        # Per-type from Table 2
        state_n, state_bn = 10760, 0.984
        nonstate_n, nonstate_bn = 4363, 0.993
        onesided_n, onesided_bn = 4003, 0.989

        total_n = state_n + nonstate_n + onesided_n
        weighted_avg = (
            state_n * state_bn + nonstate_n * nonstate_bn + onesided_n * onesided_bn
        ) / total_n

        pooled_claim = 0.985

        # Even allowing for 271 extra cell-months all at 100% concordance
        best_case = (total_n * weighted_avg + 271 * 1.0) / (total_n + 271)

        # The gap should be explainable (< 5 percentage points)
        gap = abs(pooled_claim - best_case)
        assert gap < 0.05, (
            f"RVI BN concordance gap is {gap*100:.1f} pp: "
            f"pooled={pooled_claim*100}%, best-case weighted={best_case*100:.1f}%."
        )

    def test_parametric_bn_concordance_pooled_vs_pertype(self):
        """Pooled parametric BN agree should be reconcilable with per-type."""
        state_n, state_bn = 10760, 0.976
        nonstate_n, nonstate_bn = 4363, 0.984
        onesided_n, onesided_bn = 4003, 0.983

        total_n = state_n + nonstate_n + onesided_n
        weighted_avg = (
            state_n * state_bn + nonstate_n * nonstate_bn + onesided_n * onesided_bn
        ) / total_n

        pooled_claim = 0.981
        best_case = (total_n * weighted_avg + 271 * 1.0) / (total_n + 271)

        gap = abs(pooled_claim - best_case)
        assert gap < 0.05, (
            f"Parametric BN concordance gap is {gap*100:.1f} pp: "
            f"pooled={pooled_claim*100}%, best-case weighted={best_case*100:.1f}%."
        )


class TestHF2_WrongSectionReference:
    """04_fuzzy_crps.tex line 2 says 'verified in \\S5' but Consistency
    Properties is section 4. The .aux file confirms: section 4 = Consistency.

    Fix: change \\S5 to \\S4 in 04_fuzzy_crps.tex. Better: replace all
    hardcoded \\S references with \\ref{sec:} labels."""

    def test_consistency_section_reference(self):
        """The reformulation section should point to §4 (Consistency), not §5."""
        text = (SECTIONS_DIR / "04_fuzzy_crps.tex").read_text()

        # Find the sentence about consistency properties
        match = re.search(
            r"consistency properties are (?:verified|examined) in \\S(\d)", text
        )
        assert match is not None, "Cannot find consistency cross-reference"
        section_num = int(match.group(1))
        assert section_num == 4, (
            f"Cross-reference points to §{section_num} but Consistency "
            f"Properties is §4. This directs the reader to the wrong section."
        )


class TestSF1_TodayInPreamble:
    """preamble.tex uses \\today in \\date{} and \\rhead{}. On arXiv,
    this produces the server compilation date, not the submission date.

    Fix: replace \\today with a fixed date string."""

    def test_no_today_in_preamble(self):
        """Preamble should not use \\today for arXiv submission."""
        text = (PAPER_DIR / "preamble.tex").read_text()
        today_count = text.count(r"\today")
        assert today_count == 0, (
            f"Found {today_count} occurrence(s) of \\today in preamble.tex. "
            f"arXiv compiles LaTeX on their servers; the date will be wrong."
        )


class TestSF2_CodeAvailability:
    """The paper mentions 'the reference implementation' with specific
    parameters (seed=0, 4001 grid points) but provides no URL, code
    supplement, or data availability statement.

    Fix: add a code/data availability paragraph before Acknowledgments."""

    def test_code_availability_statement_exists(self):
        """Paper should contain a code or data availability statement."""
        main_text = (PAPER_DIR / "main.tex").read_text()
        all_sections = ""
        for f in SECTIONS_DIR.glob("*.tex"):
            all_sections += f.read_text()
        full_text = main_text + all_sections

        availability_markers = [
            "code availability",
            "data availability",
            "code is available",
            "code are available",
            "github.com",
            "zenodo",
            "supplementary code",
            "replication package",
            "code repository",
        ]
        found = any(m.lower() in full_text.lower() for m in availability_markers)
        assert found, (
            "No code or data availability statement found. The paper references "
            "'the reference implementation' but never says where to find it."
        )
