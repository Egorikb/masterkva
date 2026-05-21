from __future__ import annotations

from deeptutor.services.learning_rag import learning_rag


def test_retrieve_learning_context_stays_with_requested_grade() -> None:
    results = learning_rag.retrieve(grade=1, query="сложение и вычитание до 5", topic_id="3", top_k=3)

    assert results
    assert all(item["grade"] == 1 for item in results)
    assert any("СЛОЖЕНИЕ/ВЫЧИТАНИЕ" in item["text"].upper() or "СЛОЖЕНИЕ" in item["text"].upper() for item in results)
    assert all(item["grade"] != 9 for item in results)


def test_retrieve_learning_context_can_match_curriculum_for_high_grade() -> None:
    results = learning_rag.retrieve(grade=9, query="квадратные уравнения", topic_id="1", top_k=2)

    assert results
    assert all(item["grade"] == 9 for item in results)
    assert any(item["source_file"].startswith("grade_9") for item in results)


def test_format_context_includes_bullets() -> None:
    text = learning_rag.format_context(
        [
            {
                "title": "1 класс · ПОДГОТОВКА",
                "topic_id": "1",
                "snippet": "Учимся считать и сравнивать предметы",
            }
        ]
    )

    assert text.startswith("Учебный контекст из наших материалов:")
    assert "•" in text
