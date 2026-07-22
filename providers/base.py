"""Provider interface, output parsing, and the built-in mock provider."""

from __future__ import annotations

import json
from abc import ABC, abstractmethod

from models import QualityReview


class ProviderError(Exception):
    """Raised for provider selection, configuration, or output-parsing failures."""


class LLMProvider(ABC):
    """A pluggable LLM backend. Implementations turn a prompt into raw text."""

    @abstractmethod
    def complete(self, system: str, user: str) -> str:
        """Return the model's raw text response (expected to contain JSON)."""


def parse_review(raw: str) -> QualityReview:
    """Parse a model's raw response into a QualityReview.

    Tolerates prose or ```json fences around the JSON object.
    """
    start = raw.find("{")
    end = raw.rfind("}")
    if start == -1 or end == -1 or end < start:
        raise ProviderError(f"Model did not return JSON. Got: {raw[:200]!r}")
    try:
        data = json.loads(raw[start : end + 1])
    except json.JSONDecodeError as exc:
        raise ProviderError(f"Could not parse model output as JSON: {exc}") from exc

    return QualityReview(
        summary=str(data.get("summary", "")),
        weak_sections=list(data.get("weak_sections", []) or []),
        notes=list(data.get("notes", []) or []),
        confidence=str(data.get("confidence", "unknown")),
    )


class MockProvider(LLMProvider):
    """Deterministic provider for tests and no-key demos (`--provider mock`)."""

    def complete(self, system: str, user: str) -> str:
        return json.dumps(
            {
                "summary": "The postmortem covers the required structure; some sections "
                "may benefit from more specific detail.",
                "weak_sections": [],
                "notes": [
                    "Consider whether the root cause names an underlying cause rather "
                    "than just restating the symptom.",
                ],
                "confidence": "low",
            }
        )
