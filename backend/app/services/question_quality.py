import hashlib
import re

from app.services.llm_client import GeneratedQuestion


def normalize_question_text(question_text: str) -> str:
    normalized = question_text.strip().lower()
    normalized = re.sub(r"\s+", " ", normalized)
    normalized = normalized.rstrip(" ?!.")
    return normalized


def build_question_hash(interview_type_id: int, level: str, question_text: str) -> str:
    payload = f"{interview_type_id}:{level.lower()}:{normalize_question_text(question_text)}"
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def validate_generated_question(item: GeneratedQuestion, requested_level: str) -> list[str]:
    errors: list[str] = []
    if item.level.lower() != requested_level.lower():
        errors.append("level does not match requested level")
    if len(item.question_text.strip()) < 12:
        errors.append("question_text is too short")
    if len(item.expected_answer.strip()) < 20:
        errors.append("expected_answer is too short")
    if len(item.evaluation_criteria) < 2:
        errors.append("evaluation_criteria must contain at least two items")
    if any(len(value.strip()) < 5 for value in item.evaluation_criteria):
        errors.append("evaluation_criteria contains weak items")
    if any(not tag.strip() for tag in item.tags):
        errors.append("tags must not contain empty strings")
    return errors
