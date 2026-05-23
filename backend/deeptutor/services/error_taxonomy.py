from __future__ import annotations

from typing import Any

# Small, deterministic topic-level taxonomy for the current curriculum slice.
# The mapping is intentionally narrow and can be extended skill-by-skill.
ERROR_CODE_BY_TOPIC: dict[str, str] = {
    "g1_t02": "sequencing_error",
    "g1_t03": "carry_error",
    "g1_t04": "subtraction_fact_error",
    "g1_t07": "carry_error",
    "g2_t01": "place_value_error",
    "g3_t01": "clock_reading_error",
    "g4_t01": "place_value_error",
    "g5_t01": "inverse_operation_error",
    "g6_t01": "percent_calculation_error",
    "g7_t01": "sign_error",
    "g8_t01": "inverse_operation_error",
    "g9_t01": "graph_shape_error",
}


def _family_from_error_code(error_code: str | None) -> str | None:
    if not error_code:
        return None
    if error_code.endswith("_error"):
        return error_code[: -len("_error")]
    return error_code


class ErrorTaxonomy:
    def classify_practice_error(self, question: dict[str, Any], practice_feedback: dict[str, Any], contract: dict[str, Any] | None = None) -> dict[str, Any]:
        if bool(practice_feedback.get("is_correct", False)):
            return {
                "error_code": None,
                "error_family": None,
                "remediation_path": None,
                "taxonomy_source": None,
            }

        topic_id = str(practice_feedback.get("topic_id") or question.get("topic_id") or "").strip()
        error_code = ERROR_CODE_BY_TOPIC.get(topic_id)
        taxonomy_source = "topic_map" if error_code else "contract"

        contract = contract or {}
        diagnostic = contract.get("diagnostic") or {}
        error_model = contract.get("error_model") or {}
        remediation_by_error = dict(error_model.get("remediation_by_error") or {})
        default_remediation = str(error_model.get("default_remediation") or (contract.get("remediation") or {}).get("default_path") or "slow_step_by_step")

        if not error_code:
            detectable = list(diagnostic.get("detectable_errors") or [])
            error_code = detectable[0] if detectable else "procedural_slip"
            taxonomy_source = "contract"

        remediation_path = remediation_by_error.get(error_code) or default_remediation
        return {
            "error_code": error_code,
            "error_family": _family_from_error_code(error_code),
            "remediation_path": remediation_path,
            "taxonomy_source": taxonomy_source,
        }


error_taxonomy = ErrorTaxonomy()
