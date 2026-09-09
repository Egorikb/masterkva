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

ERROR_CODE_BY_ITEM_FAMILY: dict[str, str] = {
    "counting_with_objects": "counting_with_objects_error",
    "number_successor": "number_successor_error",
    "addition_within_10_part_whole": "addition_within_10_part_whole_error",
    "subtraction_within_10_part_whole": "subtraction_within_10_part_whole_error",
    "number_bond_missing_part": "number_bond_missing_part_error",
    "compose_decompose_10": "compose_decompose_10_error",
    "addition_carry": "addition_carry_error",
    "subtraction_carry": "subtraction_carry_error",
    "multiplication_intro": "multiplication_intro_error",
    "division_intro": "division_intro_error",
    "measurement_length": "measurement_length_error",
    "time_unit_conversion": "time_unit_conversion_error",
    "measurement_large_units": "measurement_large_units_error",
    "clock_reading": "clock_reading_error",
    "geometry_2d": "geometry_2d_error",
    "multiplication_tables": "multiplication_tables_error",
    "division_via_multiplication": "division_via_multiplication_error",
    "division_with_remainder": "division_with_remainder_error",
    "fractions_intro": "fractions_intro_error",
    "fractions_addition": "fractions_addition_error",
    "fractions_comparison": "fractions_comparison_error",
    "decimals_intro": "decimals_intro_error",
    "area_perimeter": "area_perimeter_error",
    "large_numbers": "large_numbers_error",
    "decimals_operations": "decimals_operations_error",
    "fractions_multiplication": "fractions_multiplication_error",
    "mixed_numbers": "mixed_numbers_error",
    "simple_equations": "simple_equations_error",
    "area_triangle": "area_triangle_error",
    "linear_equations": "linear_equations_error",
    "proportions": "proportions_error",
    "volume": "volume_error",
    "rational_numbers": "rational_numbers_error",
    "rational_operations": "rational_operations_error",
    "systems_of_equations": "systems_of_equations_error",
    "percent": "percent_error",
    "angles_triangles": "angles_triangles_error",
    "quadratic": "quadratic_error",
    "linear_functions": "linear_functions_error",
    "trigonometry": "trigonometry_error",
    "statistics": "statistics_error",
    "quadratic_functions": "quadratic_functions_error",
    "trig_identities": "trig_identities_error",
    "probability": "probability_error",
    "sequences": "sequences_error",
}

REMEDIATION_BY_ITEM_FAMILY: dict[str, str] = {
    "counting_with_objects": "ten_frame",
    "number_successor": "number_line",
    "addition_within_10_part_whole": "number_bond",
    "subtraction_within_10_part_whole": "number_bond",
    "number_bond_missing_part": "number_bond",
    "compose_decompose_10": "number_bond",
    "addition_carry": "base_ten_blocks",
    "subtraction_carry": "base_ten_blocks",
    "multiplication_intro": "array_matrix",
    "division_intro": "division_groups",
    "measurement_length": "place_value_chart",
    "time_unit_conversion": "clock_face",
    "measurement_large_units": "place_value_chart",
    "clock_reading": "clock_face",
    "geometry_2d": "geoboard_dynamic",
    "multiplication_tables": "array_matrix",
    "division_via_multiplication": "division_groups",
    "division_with_remainder": "division_groups",
    "fractions_intro": "fraction_bars",
    "fractions_addition": "fraction_bars",
    "fractions_comparison": "fraction_bars",
    "decimals_intro": "place_value_chart",
    "area_perimeter": "area_model_grid",
    "large_numbers": "place_value_chart",
    "decimals_operations": "place_value_chart",
    "fractions_multiplication": "fraction_bars",
    "mixed_numbers": "fraction_bars",
    "simple_equations": "balance_scale_equation",
    "area_triangle": "cut_and_drag_parallelogram",
    "linear_equations": "balance_scale_equation",
    "proportions": "ratio_table",
    "volume": "net_of_solid",
    "rational_numbers": "double_number_line",
    "rational_operations": "double_number_line",
    "systems_of_equations": "balance_scale_equation",
    "percent": "percent_grid_10x10",
    "angles_triangles": "geoboard_dynamic",
    "quadratic": "algebra_tiles",
    "linear_functions": "cartesian_graph_slider",
    "trigonometry": "geoboard_dynamic",
    "statistics": "part_part_whole_bar",
    "quadratic_functions": "cartesian_graph_slider",
    "trig_identities": "geoboard_dynamic",
    "probability": "percent_grid_10x10",
    "sequences": "function_table",
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
        item_family = str(practice_feedback.get("item_family") or question.get("item_family") or "").strip()
        error_code = ERROR_CODE_BY_ITEM_FAMILY.get(item_family) if item_family else None
        remediation_path = REMEDIATION_BY_ITEM_FAMILY.get(item_family) if item_family else None
        taxonomy_source = "item_family" if error_code else "topic_map"

        contract = contract or {}
        diagnostic = contract.get("diagnostic") or {}
        error_model = contract.get("error_model") or {}
        remediation_by_error = dict(error_model.get("remediation_by_error") or {})
        remediation_targets = dict((contract.get("remediation") or {}).get("targets") or {})
        default_remediation = str(error_model.get("default_remediation") or (contract.get("remediation") or {}).get("default_path") or "slow_step_by_step")

        if not error_code:
            error_code = ERROR_CODE_BY_TOPIC.get(topic_id)
            taxonomy_source = "topic_map" if error_code else "contract"

        if not error_code:
            detectable = list(diagnostic.get("detectable_errors") or [])
            error_code = detectable[0] if detectable else "procedural_slip"
            taxonomy_source = "contract"

        remediation_path = remediation_path or remediation_by_error.get(error_code) or remediation_targets.get(item_family) or default_remediation
        return {
            "error_code": error_code,
            "error_family": _family_from_error_code(error_code),
            "item_family": item_family or None,
            "remediation_path": remediation_path,
            "taxonomy_source": taxonomy_source,
        }


error_taxonomy = ErrorTaxonomy()
