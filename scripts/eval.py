import asyncio
import json
import math
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from src.rag.query import query_rag


EVAL_PATH = Path(__file__).resolve().parents[1].joinpath("eval_set.json")
REPORT_PATH = Path(__file__).resolve().parents[1].joinpath("eval_report.json")
COLLECTION_NAME = "questions"


@dataclass
class EvalResult:
    id: str
    question: str
    expected: dict[str, Any]
    answer: str
    passed: bool
    score: float | None
    reason: str | None


def _normalize_text(text: str) -> str:
    return " ".join(_tokenize(text))


def _tokenize(text: str) -> list[str]:
    cleaned = text.lower().replace("№", " ")
    cleaned = re.sub(r"(?<=\d),(?=\d)", ".", cleaned)  # 1,5 -> 1.5
    cleaned = re.sub(r"[^0-9a-zа-яё\\.]+", " ", cleaned, flags=re.IGNORECASE)
    tokens = []
    for token in cleaned.split():
        token = token.strip(".")
        if token:
            tokens.append(token)
    return tokens


_STOPWORDS = {
    "и", "в", "во", "на", "по", "для", "а", "но", "или", "что", "как", "чем", "не", "более", "менее",
    "при", "с", "со", "к", "от", "до", "из", "у", "о", "об", "за", "над", "под", "про",
}


def _fuzzy_contains(expected: str, answer: str) -> bool:
    expected_tokens = [t for t in _tokenize(expected) if t not in _STOPWORDS]
    answer_tokens = _tokenize(answer)
    if not expected_tokens:
        return False

    for exp in expected_tokens:
        if len(exp) <= 2:
            # короткие токены ищем строго
            if exp not in answer_tokens:
                return False
            continue

        matched = False
        for ans in answer_tokens:
            if ans.startswith(exp) or exp.startswith(ans):
                matched = True
                break
            # мягкое совпадение по общему префиксу
            prefix_len = 5 if len(exp) >= 5 and len(ans) >= 5 else 3
            if exp[:prefix_len] == ans[:prefix_len]:
                matched = True
                break
        if not matched:
            return False

    return True


def _cosine_similarity(a: list[float], b: list[float]) -> float:
    if not a or not b or len(a) != len(b):
        return 0.0
    dot = sum(x * y for x, y in zip(a, b))
    norm_a = math.sqrt(sum(x * x for x in a))
    norm_b = math.sqrt(sum(y * y for y in b))
    if norm_a == 0.0 or norm_b == 0.0:
        return 0.0
    return dot / (norm_a * norm_b)


async def _evaluate_item(container: Any, item: dict[str, Any]) -> EvalResult:
    question = item["question"]
    expected = item["expected"]
    answer = await query_rag(container=container, query=question, collection_name=COLLECTION_NAME)

    expected_type = expected.get("type")
    expected_value = expected.get("value")

    normalized_answer = _normalize_text(answer)
    passed = False
    score: float | None = None
    reason: str | None = None

    if expected_type == "exact":
        passed = normalized_answer == _normalize_text(str(expected_value))
        if not passed:
            reason = "exact_mismatch"
    elif expected_type == "contains":
        expected_text = str(expected_value)
        if ", " in expected_text:
            parts = [part.strip() for part in expected_text.split(", ") if part.strip()]
            passed = all(_fuzzy_contains(part, answer) for part in parts)
        else:
            passed = _fuzzy_contains(expected_text, answer)
        if not passed:
            reason = "missing_substring"
    elif expected_type == "regex":
        pattern = re.compile(str(expected_value), flags=re.IGNORECASE)
        passed = pattern.search(answer) is not None
        if not passed:
            reason = "regex_no_match"
    elif expected_type == "keywords":
        keywords = [str(k) for k in expected_value or []]
        missing = [k for k in keywords if _normalize_text(k) not in normalized_answer]
        passed = len(missing) == 0
        if not passed:
            reason = f"missing_keywords: {', '.join(missing)}"
    elif expected_type == "similarity":
        threshold = float(expected.get("threshold", 0.8))
        expected_text = str(expected_value)
        vec_answer, vec_expected = await asyncio.gather(
            container.embeddings.embed_query(answer),
            container.embeddings.embed_query(expected_text),
        )
        score = _cosine_similarity(vec_answer, vec_expected)
        passed = score >= threshold
        if not passed:
            reason = f"similarity_below_threshold: {score:.3f} < {threshold:.3f}"
    else:
        reason = f"unknown_expected_type: {expected_type}"

    return EvalResult(
        id=item.get("id", ""),
        question=question,
        expected=expected,
        answer=answer,
        passed=passed,
        score=score,
        reason=reason,
    )


async def main() -> None:
    if not EVAL_PATH.exists():
        raise SystemExit(f"eval_set.json not found at {EVAL_PATH}")

    from src.rag.container import RAGContainer

    container = RAGContainer()
    if not await container.vector_store.is_collection_exists(collection_name=COLLECTION_NAME):
        raise SystemExit("Collection 'questions' not found. Run ingest first.")

    items = json.loads(EVAL_PATH.read_text(encoding="utf-8"))
    results: list[EvalResult] = []

    for item in items:
        results.append(await _evaluate_item(container, item))

    passed_count = sum(1 for r in results if r.passed)
    total_count = len(results)
    accuracy = (passed_count / total_count) * 100 if total_count else 0.0

    report = {
        "summary": {
            "total": total_count,
            "passed": passed_count,
            "failed": total_count - passed_count,
            "accuracy_percent": round(accuracy, 2),
        },
        "results": [
            {
                "id": r.id,
                "question": r.question,
                "expected": r.expected,
                "answer": r.answer,
                "passed": r.passed,
                "score": r.score,
                "reason": r.reason,
            }
            for r in results
        ],
    }

    REPORT_PATH.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")

    print("Eval complete")
    print(f"Total: {total_count}, Passed: {passed_count}, Failed: {total_count - passed_count}")
    print(f"Accuracy: {accuracy:.2f}%")
    print(f"Report: {REPORT_PATH}")


if __name__ == "__main__":
    asyncio.run(main())
