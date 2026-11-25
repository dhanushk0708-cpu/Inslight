import asyncio
import pytest
from app.services.business_guard import BusinessContextGuard, GUARD_REJECTION_MESSAGE, NO_DATASET_MESSAGE


def test_deterministic_business_questions_allowed():
    allowed_questions = [
        "What is my total revenue?",
        "Show sales trends over time",
        "Which product category generated the highest profit?",
        "What is the average order discount percentage?",
        "Compare revenue between regions"
    ]
    for q in allowed_questions:
        det = BusinessContextGuard.evaluate_deterministic(q)
        assert det is not None, f"Expected deterministic match for: {q}"
        is_biz, reason = det
        assert is_biz is True, f"Question should be allowed: {q} (reason: {reason})"


def test_deterministic_unrelated_questions_rejected():
    rejected_questions = [
        "Who is the Prime Minister of India?",
        "Tell me a funny joke",
        "Write a Python program to sort an array",
        "What is 1 + 1?",
        "Write a poem about dogs"
    ]
    for q in rejected_questions:
        det = BusinessContextGuard.evaluate_deterministic(q)
        assert det is not None, f"Expected deterministic match for: {q}"
        is_biz, reason = det
        assert is_biz is False, f"Question should be rejected: {q}"


def test_guard_validation_rejects_unrelated():
    is_valid, msg = asyncio.run(BusinessContextGuard.validate_query("Who won the football world cup?", has_dataset=True))
    assert is_valid is False
    assert msg == GUARD_REJECTION_MESSAGE


def test_guard_validation_requires_dataset_when_none_loaded():
    is_valid, msg = asyncio.run(BusinessContextGuard.validate_query("Show our total revenue", has_dataset=False))
    assert is_valid is False
    assert msg == NO_DATASET_MESSAGE
