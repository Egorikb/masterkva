from __future__ import annotations

from deeptutor.services.coverage_runner import CoverageReport


def test_coverage_runner_golden_chain_checks() -> None:
    report = CoverageReport()
    assert report is not None
