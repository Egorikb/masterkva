from deeptutor.api.routers.plugins_api import check_answer_fuzzy


def test_check_answer_fuzzy_rejects_numeric_false_positives_stage2_red() -> None:
    assert check_answer_fuzzy("6", "5")[0] is False
    assert check_answer_fuzzy("12", "2")[0] is False
    assert check_answer_fuzzy("50", "5")[0] is False
    assert check_answer_fuzzy("ответ: 5", "5")[0] is True
