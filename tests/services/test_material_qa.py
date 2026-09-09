from __future__ import annotations

from deeptutor.services.material_qa import run_material_qa


def test_material_qa_has_no_blocking_issues() -> None:
    report = run_material_qa()

    assert report["ok"], report["issues"]
