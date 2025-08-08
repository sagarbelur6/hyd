from __future__ import annotations

import os
import re
import uuid
from typing import List, Optional

from .schemas import TestCase, GenerateResponse

try:
    from openai import OpenAI  # type: ignore
except Exception:  # pragma: no cover
    OpenAI = None  # type: ignore


def _generate_uuid(prefix: str) -> str:
    return f"{prefix}-{uuid.uuid4().hex[:8]}"


def _normalize_text(text: str) -> str:
    if not text:
        return ""
    text = text.strip()
    text = re.sub(r"\s+", " ", text)
    return text


def _extract_candidate_topics(text: str, max_topics: int = 8) -> List[str]:
    if not text:
        return []
    # Naive topic extraction: unique words > 3 chars, de-duplicated, preserve order
    words = re.findall(r"[A-Za-z][A-Za-z0-9_\-]{3,}", text)
    seen = set()
    topics: List[str] = []
    for w in words:
        lw = w.lower()
        if lw not in seen:
            seen.add(lw)
            topics.append(w)
        if len(topics) >= max_topics:
            break
    if not topics and text:
        topics = [text[:50]]
    return topics


def _local_generate_cases(source_text: str, num_cases: int = 8) -> GenerateResponse:
    cleaned = _normalize_text(source_text)
    topics = _extract_candidate_topics(cleaned, max_topics=max(4, num_cases))
    if not topics:
        topics = ["General Feature"]

    archetypes = [
        ("Functional Happy Path", "High", "Functional"),
        ("Negative Validation", "High", "Negative"),
        ("Boundary Condition", "Medium", "Boundary"),
        ("Error Handling", "Medium", "Functional"),
        ("Security", "High", "Security"),
        ("Performance", "Medium", "Performance"),
        ("Accessibility", "Low", "Accessibility"),
        ("Edge Case", "Medium", "Functional"),
    ]

    cases: List[TestCase] = []
    for i in range(num_cases):
        arch = archetypes[i % len(archetypes)]
        topic = topics[i % len(topics)]

        title = f"{arch[0]}: {topic}"
        objective = f"Verify {topic} works as expected under {arch[0].lower()} scenario."
        preconditions = ["Environment is configured", "User has necessary permissions if applicable"]
        steps = [
            f"Navigate to the relevant section for {topic}",
            f"Perform the primary action related to {topic}",
            "Observe behavior and captured outputs",
        ]
        expected = f"System responds correctly for {topic} in {arch[0].lower()} scenario without regressions."
        tags = [topic.lower(), arch[2].lower()]

        cases.append(
            TestCase(
                id=_generate_uuid("TC"),
                title=title,
                objective=objective,
                preconditions=preconditions,
                steps=steps,
                expected_result=expected,
                priority=arch[1],
                type=arch[2],
                tags=tags,
            )
        )

    summary = f"Generated {len(cases)} test cases across functional, negative, boundary, and non-functional categories."
    return GenerateResponse(summary=summary, source_summary=cleaned[:500], test_cases=cases)


def _openai_generate_cases(source_text: str, num_cases: int = 8, model: Optional[str] = None) -> GenerateResponse:
    if OpenAI is None:
        raise RuntimeError("openai package not available")

    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError("OPENAI_API_KEY not set")

    client = OpenAI()
    selected_model = model or os.getenv("OPENAI_MODEL", "gpt-4o-mini")

    system_prompt = (
        "You are a senior QA engineer. Generate high-quality, actionable test cases in JSON.\n"
        "Output JSON with fields: summary, source_summary, test_cases[]. Each test case fields: \n"
        "id, title, objective, preconditions, steps, expected_result, priority, type, tags."
    )

    user_prompt = (
        f"Create {num_cases} distinct test cases based on the following context.\n\n"
        f"Context:\n{source_text}\n\n"
        "Return only valid JSON."
    )

    completion = client.chat.completions.create(
        model=selected_model,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        temperature=0.2,
        response_format={"type": "json_object"},
    )

    content = completion.choices[0].message.content or "{}"

    # Parse using pydantic for validation
    # We avoid json.loads here and let pydantic parse_obj handle mapping
    import json

    payload = json.loads(content)

    # Ensure ids exist
    for idx, tc in enumerate(payload.get("test_cases", [])):
        if not tc.get("id"):
            tc["id"] = _generate_uuid("TC")

    return GenerateResponse(**payload)


def generate_test_cases(source_text: str, num_cases: int = 8, mode: str = "auto") -> GenerateResponse:
    text = _normalize_text(source_text)
    if not text:
        text = "General requirements and flows are unspecified. Generate broad, useful test cases."

    selected_mode = mode
    if mode == "auto":
        selected_mode = "openai" if os.getenv("OPENAI_API_KEY") else "local"

    if selected_mode == "openai":
        try:
            return _openai_generate_cases(text, num_cases=num_cases)
        except Exception:
            # Fallback to local if OpenAI fails
            return _local_generate_cases(text, num_cases=num_cases)

    return _local_generate_cases(text, num_cases=num_cases)