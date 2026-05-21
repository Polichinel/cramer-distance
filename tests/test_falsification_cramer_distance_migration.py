"""Failing test stubs from the falsification audit of the claim
"the migration and setup of the cramer-distance repo was successfully
and correctly completed."

Audit date: 2026-05-21
Auditor: falsify skill

Severity legend:
  HARD = the repo violates its stated contract (self-containment, correct metadata)
  SOFT = the repo is technically functional but misleading or incomplete
"""

import re
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
PAPER_DIR = REPO_ROOT / "paper"
SECTIONS_DIR = PAPER_DIR / "sections"
SRC_DIR = REPO_ROOT / "src" / "cramer_distance"


# --- HARD: P1 — Dead section file with stale references ---



def test_no_dead_section_files_referencing_old_project() -> None:
    """paper/sections/ must not contain .tex files that reference the old
    views-lab00 triptych structure or the old package name."""
    context_file = SECTIONS_DIR / "01_context.tex"
    if not context_file.exists():
        return  # file removed = pass
    content = context_file.read_text()
    stale_markers = [
        "views-lab00",
        "triptych",
        "Notes A and B",
        "lab_fuzzy_crps",
        "lab\\_fuzzy\\_crps",
    ]
    found = [m for m in stale_markers if m in content]
    assert not found, (
        f"01_context.tex contains stale references: {found}. "
        f"Either remove the file or rewrite it for the standalone repo."
    )


# --- HARD: P2 — Preamble declares wrong authors ---



def test_preamble_does_not_declare_wrong_authors() -> None:
    """preamble.tex must not declare authors other than the paper's actual
    author. Even though main.tex overrides, the source file is misleading."""
    preamble = (PAPER_DIR / "preamble.tex").read_text()
    assert "Dornin Pinheiro" not in preamble, (
        "preamble.tex declares Dornin Pinheiro as co-author — "
        "this is a single-author paper"
    )
    assert "Häffner" not in preamble, (
        "preamble.tex declares Häffner as co-author — "
        "this is a single-author paper"
    )



def test_preamble_does_not_reference_triptych() -> None:
    """preamble.tex header comment must not reference the old multi-paper structure."""
    preamble = (PAPER_DIR / "preamble.tex").read_text()
    assert "triptych" not in preamble.lower(), (
        "preamble.tex references 'triptych' — stale from views-lab00 extraction"
    )
    assert "views-lab00" not in preamble, (
        "preamble.tex references 'views-lab00' — stale project name"
    )


# --- SOFT: P3 — Source docstrings reference non-existent sibling papers ---



def test_no_triptych_cross_references_in_source() -> None:
    """Source docstrings must not reference 'Note A', 'Note B', or 'Note C'
    — these were sibling papers in the old triptych and don't exist in
    this repo."""
    hits = []
    for py_file in SRC_DIR.glob("*.py"):
        content = py_file.read_text()
        for match in re.finditer(r"\bNote [ABC]\b", content):
            hits.append(f"{py_file.name}:{match.start()}: '{match.group()}'")
    assert not hits, (
        "Source files reference non-existent sibling papers:\n"
        + "\n".join(f"  {h}" for h in hits)
    )


# --- SOFT: P7 — README missing key instructions ---



def test_readme_covers_figure_generation() -> None:
    """README must explain how to regenerate figures."""
    readme = (REPO_ROOT / "README.md").read_text()
    assert "cramer_distance.figures" in readme or "make figures" in readme.lower(), (
        "README does not explain how to generate figures"
    )



def test_readme_covers_paper_compilation() -> None:
    """README must explain how to compile the paper."""
    readme = (REPO_ROOT / "README.md").read_text()
    has_make = "make" in readme.lower() and "paper" in readme.lower()
    has_pdflatex = "pdflatex" in readme.lower()
    assert has_make or has_pdflatex, (
        "README does not explain how to compile the paper"
    )
