from __future__ import annotations

from deeptutor.services.coverage_runner import CoverageReport


def test_coverage_runner_golden_chain_checks() -> None:
    report = CoverageReport()
    summary = report.run()

    assert summary["total_skills"] == 40
    assert summary["complete"] == 40
    assert summary["partial"] == 0
    assert summary["incomplete"] == 0
    assert summary["active_with_gaps"] == []
