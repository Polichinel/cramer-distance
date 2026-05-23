"""Failing test stubs from the falsification audit of the fuzzy CRPS paper.

These tests encode the falsifications found during the audit of the claim
"the quality and scientific rigor of the fuzzy CRPS paper is high and the
paper is ready for submission on arXiv under cs.AI, cs.CY, cs.LG, stat.AP."

Each test is currently expected to FAIL (xfail). They should be uncommented
and made to pass as the underlying issues are fixed.

Severity legend:
  HARD = the paper makes a claim that is empirically/structurally wrong
  SOFT = the paper makes a claim that is overstated or unsupported
"""

import re
from pathlib import Path

import numpy as np
import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
PAPER_DIR = REPO_ROOT / "paper"
SECTIONS_DIR = PAPER_DIR / "sections"
MAIN_TEX = PAPER_DIR / "main.tex"
REFS_BIB = PAPER_DIR / "refs.bib"


def test_paper_main_tex_has_abstract() -> None:
    """main.tex must contain a \\begin{abstract}...\\end{abstract} environment
    or a \\section*{Abstract} or an \\input of an abstract sections file."""
    main_tex_content = MAIN_TEX.read_text()
    has_abstract_env = re.search(
        r"\\begin\{abstract\}.*?\\end\{abstract\}",
        main_tex_content,
        re.DOTALL,
    )
    has_abstract_section = re.search(
        r"\\section\*?\{Abstract\}",
        main_tex_content,
    )
    has_input_abstract = re.search(
        r"\\input\{sections/.*abstract.*\}",
        main_tex_content,
    )
    assert has_abstract_env or has_abstract_section or has_input_abstract, (
        "main.tex contains no abstract environment, abstract section, or "
        "input of an abstract sections file"
    )


def test_bibliography_has_no_unused_entries() -> None:
    """Every entry in refs.bib should be cited at least once in a section .tex file."""
    bib_content = REFS_BIB.read_text()
    bib_keys = re.findall(r"^@\w+\{(\w+),", bib_content, re.MULTILINE)

    section_files = list(SECTIONS_DIR.glob("*.tex"))
    body_text = "\n".join(f.read_text() for f in section_files)

    unused = [k for k in bib_keys if k not in body_text]
    assert not unused, f"Unused bib entries: {unused}"


def test_propriety_in_expectation_is_verified_numerically() -> None:
    """After C-32 / C-43 re-scope, the module must expose a
    verify_propriety_in_expectation function that draws random y,
    constructs F_obs per draw, and checks that the expected fuzzy CRPS
    is minimised near the true forecast parameter. The function must
    actually run on a small example — merely exposing a name is not
    enough."""
    from cramer_distance.propriety import verify_propriety_in_expectation

    mu_sweep, scores, argmin = verify_propriety_in_expectation(
        true_mu=1.0,
        true_sigma=0.3,
        obs_sigma_rel=0.3,
        n_draws=30,
        mu_sweep=np.linspace(0.0, 2.0, 11),
        seed=0,
    )
    assert len(mu_sweep) == len(scores) == 11
    assert np.all(np.isfinite(scores))
    assert abs(argmin - 1.0) < 0.25, (
        f"verify_propriety_in_expectation argmin {argmin:.3f} is too far "
        f"from true_mu=1.0 even on a well-specified small sweep"
    )


def test_f_obs_from_bounds_lognormal_with_low_zero_does_not_silently_corrupt() -> None:
    """When low <= 0 is passed to the lognormal F_obs constructor, the function
    must raise ValueError directing the user to distribution='uniform'. The
    uniform fallback must itself work at low=0 so the caller has a clear escape
    hatch (C-33 Decision, 2026-04-11 — fail fast rather than silent corruption).
    """
    from cramer_distance.observation_uncertainty import f_obs_from_bounds

    with pytest.raises(ValueError, match="lognormal F_obs is undefined at low"):
        f_obs_from_bounds(low=0.0, best=10.0, high=20.0, distribution="lognormal")

    cdf = f_obs_from_bounds(low=0.0, best=10.0, high=20.0, distribution="uniform")
    z = np.array([20.0])
    assert cdf(z).item() == pytest.approx(1.0, abs=1e-6), (
        "uniform fallback must concentrate its mass inside [low, high]; got "
        f"CDF(z=high={20.0}) = {cdf(z).item():.3f}"
    )


def test_demonstration_reversal_acknowledges_parameter_dependence() -> None:
    """Under Path 1 re-scope (C-34 Decision, 2026-04-11), the demonstration
    no longer claims universal reversal — it acknowledges the parameter
    regime where the reversal disappears.

    The test verifies three things:
      (a) the reversal DOES hold at default parameters,
      (b) the reversal does NOT hold at relative_sigma=0.1 (the
          degenerate regime), and
      (c) section 6 contains the 'When the reversal does not hold'
          paragraph that documents the regime.
    """
    from cramer_distance.demo import run_demo

    r_default = run_demo()
    assert r_default.is_ranking_reversal, "default params should still reverse"

    r_low = run_demo(y=50.0, relative_sigma=0.1, tight_sigma=0.05, honest_sigma=0.4)
    assert not r_low.is_ranking_reversal, (
        "at relative_sigma=0.1 the reversal must NOT hold — the paper's "
        "acknowledgement in section 6 depends on this being the correct "
        "behaviour"
    )

    results_tex = (
        REPO_ROOT / "paper" / "sections" / "06_results.tex"
    ).read_text()
    assert "When the reversal does not hold" in results_tex, (
        "results section must contain a 'When the reversal does not hold' "
        "paragraph that names the parameter regime (C-34 Decision)"
    )


def test_propriety_test_covers_several_true_mu_values() -> None:
    """The propriety test should parametrize over multiple true_mu values
    to back up the paper's 'passes for several true mu values' claim.

    Accepts either: (a) repeated `true_mu = N` assignments in the body, or
    (b) a `@pytest.mark.parametrize("true_mu", [...])` decorator supplying
    at least 2 distinct values. (C-35 Decision: parametrise.)
    """
    test_file = REPO_ROOT / "tests" / "test_cramer_distance.py"
    content = test_file.read_text()

    # Capture the decorator stack + function body for the propriety test.
    match = re.search(
        r"(?P<decorators>(?:@[^\n]*\n)*)"
        r"def test_verify_propriety_numerical_minimised_at_truth"
        r"(?P<body>.*?)(?=\n(?:@|def |\Z))",
        content,
        re.DOTALL,
    )
    assert match, "test_verify_propriety_numerical_minimised_at_truth not found"
    decorators = match.group("decorators")
    body = match.group("body")

    # Option (a): multiple literal assignments in the body
    assigned = set(re.findall(r"true_mu\s*=\s*([\d.]+)", body))

    # Option (b): a parametrize decorator listing values
    param_match = re.search(
        r'@pytest\.mark\.parametrize\(\s*["\']true_mu["\']\s*,\s*\[([^\]]+)\]',
        decorators,
    )
    parametrised: set[str] = set()
    if param_match:
        parametrised = set(re.findall(r"[\d.]+", param_match.group(1)))

    distinct = assigned | parametrised
    assert len(distinct) >= 2, (
        f"Test only covers {len(distinct)} distinct true_mu value(s): "
        f"{distinct}. Paper §5 claims 'several true mu values' — "
        f"parametrize the test or assign multiple true_mu values."
    )


def test_arxiv_tags_appropriate_for_methodology_paper() -> None:
    """The paper should declare arXiv tags consistent with its content. A
    paper proposing a new scoring rule belongs under stat.ME, not stat.AP."""
    # We don't have a tags field in main.tex, so this test encodes the
    # required final state: the paper README/main should specify stat.ME
    # as the primary tag, optionally with stat.AP as secondary.
    main_tex_content = MAIN_TEX.read_text()
    # Heuristic: if a tags comment is present, it should mention stat.ME
    has_stat_me_marker = "stat.ME" in main_tex_content or "stat.ME" in (
        REPO_ROOT / "paper" / "Makefile"
    ).read_text()
    assert has_stat_me_marker, (
        "main.tex (or paper Makefile) does not declare stat.ME as a tag "
        "despite the paper being a methodology contribution"
    )
