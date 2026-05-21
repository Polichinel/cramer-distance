"""Failing test stubs from round 2 of the falsification audit of the claim
"the migration and setup of the cramer-distance repo was successfully
and correctly completed."

Round 1 found 2 hard + 2 soft falsifications (all fixed).
Round 2 attacks from new angles: regression from fixes, deeper stale
references, functional completeness, licensing.

Audit date: 2026-05-21
Auditor: falsify skill, round 2
"""

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]


def test_repo_has_license_file() -> None:
    """A repo intended for public GitHub and scientific replication must
    include a LICENSE file so collaborators know terms of use."""
    license_candidates = [
        "LICENSE", "LICENSE.md", "LICENSE.txt",
        "COPYING", "COPYING.md", "COPYING.txt",
    ]
    found = [f for f in license_candidates if (REPO_ROOT / f).exists()]
    assert found, (
        "No license file found. Without one, the code is legally "
        "'all rights reserved' — collaborators and replicators cannot "
        "use, modify, or redistribute it."
    )
