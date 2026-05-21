"""Failing test stubs from falsification audit: mathematical notation (round 5).

Claim: "All the math notations are 100% correct and conform to best
        practice and the wider literature."

Focus: notation correctness, internal consistency, conformance to cited
       conventions (Székely & Rizzo 2013, Gneiting & Raftery 2007,
       Thorarinsdottir et al. 2013).

Audit date: 2026-04-21
Verdict: CONTESTED (0 hard, 3 soft falsifications, 4 survived)
Resolution: All three soft falsifications resolved 2026-04-21.

Each test below encodes a specific falsification finding.
"""

from __future__ import annotations

from pathlib import Path

PAPER_DIR = Path(__file__).resolve().parent.parent / "paper"
SECTIONS = PAPER_DIR / "sections"


# ---------------------------------------------------------------------------
# P1 — SOFT (RESOLVED): Energy-distance identification off by factor of 2
# ---------------------------------------------------------------------------
def test_energy_distance_identification_has_factor_caveat():
    r"""§4 should state the precise relationship between the Cramér distance
    and the energy distance of Székely & Rizzo (2013): ∫(F−G)²dz = ½D².
    Resolution: removed incorrect 'squared energy distance' parenthetical,
    added explicit ½D² formula."""
    sec4 = (SECTIONS / "04_fuzzy_crps.tex").read_text()

    has_factor_caveat = any(
        phrase in sec4
        for phrase in [
            r"\tfrac{1}{2}",
            r"\frac{1}{2}",
            "half the squared energy distance",
        ]
    )

    assert has_factor_caveat, (
        "§4 should state the precise factor-of-2 relationship between "
        "the Cramér distance and the energy distance (∫(F−G)² = ½D²)."
    )


# ---------------------------------------------------------------------------
# P4 — SOFT (RESOLVED): "Squared" qualifier dropped in body text
# ---------------------------------------------------------------------------
def test_cramer_distance_convention_is_stated():
    r"""§4 should establish a convention for 'Cramér distance' so that
    downstream uses (without 'squared') are unambiguous.
    Resolution: added convention note following Zamo & Naveau (2018)."""
    sec4 = (SECTIONS / "04_fuzzy_crps.tex").read_text()

    has_convention_note = (
        "some authors reserve" in sec4.lower()
        or "we use" in sec4.lower() and "square root" in sec4.lower()
    )

    assert has_convention_note, (
        "§4 should state whether 'Cramér distance' means the integral "
        "or its square root, so downstream bare uses are unambiguous."
    )


# ---------------------------------------------------------------------------
# P7 — SOFT (RESOLVED): Bare-italic subscripts for word abbreviations
# ---------------------------------------------------------------------------
def test_subscript_notation_uses_text_for_word_abbreviations():
    r"""The paper uses \text{} for word-derived subscripts (F_\text{pred},
    σ_\text{rel}, etc.).  Table 2 and the RVI equation should follow the
    same convention.  ISO 80000-2 requires upright type for descriptive
    subscripts.
    Resolution: changed σ_h → σ_\text{h}, μ_{\log} → μ_{\text{log}},
    μ_g → μ_\text{g}, β_g → β_\text{g}."""
    sec6 = (SECTIONS / "06_demonstration.tex").read_text()

    violations = []

    if r"\sigma_h" in sec6 and r"\sigma_\text{h}" not in sec6:
        violations.append(r"\sigma_h (should be \sigma_\text{h})")

    if r"\mu_{\log}" in sec6:
        violations.append(r"\mu_{\log} (should be \mu_{\text{log}})")

    if r"\mu_g" in sec6 and r"\mu_\text{g}" not in sec6:
        violations.append(r"\mu_g (should be \mu_\text{g})")

    if r"\beta_g" in sec6 and r"\beta_\text{g}" not in sec6:
        violations.append(r"\beta_g (should be \beta_\text{g})")

    assert len(violations) == 0, (
        f"Found {len(violations)} bare-italic subscript(s) where the "
        f"paper's convention and ISO 80000-2 require \\text{{}}: "
        + "; ".join(violations)
    )
