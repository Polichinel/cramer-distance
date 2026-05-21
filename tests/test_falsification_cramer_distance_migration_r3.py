"""Failing test stubs from round 3 of the falsification audit.

Rounds 1-2 fixed documentary tissue and licensing. Round 3 probes
packaging metadata, compiled artifact hygiene, and brain project
staleness.

Audit date: 2026-05-21
Auditor: falsify skill, round 3
"""

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]


def test_pyproject_declares_license() -> None:
    """pyproject.toml must declare the license so tooling and GitHub
    can discover it without parsing the LICENSE file."""
    content = (REPO_ROOT / "pyproject.toml").read_text()
    assert "license" in content.lower(), (
        "pyproject.toml has no license field despite LICENSE file existing"
    )


def test_compiled_pdf_not_tracked() -> None:
    """main.pdf should not be tracked in git — the source is authoritative
    and the PDF drifts whenever LaTeX is edited without recompiling."""
    gitignore = (REPO_ROOT / ".gitignore").read_text()
    assert "main.pdf" in gitignore or "*.pdf" in gitignore, (
        "main.pdf is tracked in git but the README directs users to compile "
        "from source. Either gitignore the PDF or document why it's committed."
    )
