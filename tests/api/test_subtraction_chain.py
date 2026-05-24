from __future__ import annotations

from deeptutor.services.skill_runtime import skill_resolver


def test_subtraction_chain_release_gate() -> None:
    resolution = skill_resolver.resolve(topic_id="g2_subtraction_core")
    assert resolution.skill_id == "g2_subtraction_core"
    assert resolution.contract is not None
