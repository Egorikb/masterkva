from __future__ import annotations

from deeptutor.services.skill_runtime import skill_resolver


def test_time_chain_hardening_run() -> None:
    resolution = skill_resolver.resolve(topic_id="g3_time_measurement_core")
    assert resolution.skill_id == "g3_time_measurement_core"
    assert resolution.contract is not None
