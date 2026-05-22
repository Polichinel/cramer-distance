"""Falsification audit: all code runs, all artifacts generate.

Round: execution audit (2026-05-22)
Claim: every executable entry point runs to completion and every
       artifact the repository claims to produce is generated.

Hard falsification:
  - E3: README test count is stale (says 51, actual is 60)

Soft falsifications:
  - E5: pyarrow missing from pyproject.toml (real_data.py needs parquet)
  - E6: figures.py docstring says "Three figures" but main() generates 4
"""

from pathlib import Path

REPO = Path(__file__).resolve().parents[1]


def test_readme_test_count_matches_reality():
    """E3: README claims '51 tests pass' but 60 actually pass.
    Fix: update the count in README.md."""
    readme = (REPO / "README.md").read_text()
    assert "51 tests pass" not in readme, (
        "README test count is stale: says 51 but actual pass count is 60."
    )


def test_figures_docstring_count_matches_main():
    """E6: figures.py docstring says 'Three figures' but main() calls 4."""
    src = (REPO / "src" / "cramer_distance" / "figures.py").read_text()
    assert "Three figures:" not in src, (
        "figures.py docstring says 'Three figures' but main() generates 4. "
        "Update the docstring to list all four."
    )


def test_pyarrow_in_dependencies():
    """E5: real_data.py uses pd.read_parquet() but pyarrow is not declared."""
    pyproject = (REPO / "pyproject.toml").read_text()
    assert "pyarrow" in pyproject, (
        "real_data.py uses pd.read_parquet() but pyarrow is not in "
        "pyproject.toml dependencies."
    )
