import pytest

from providers import ProviderError, get_provider, parse_review
from providers.base import MockProvider


def test_get_provider_mock():
    assert isinstance(get_provider("mock"), MockProvider)


def test_get_provider_unknown_raises():
    with pytest.raises(ProviderError):
        get_provider("not-a-real-provider")


def test_mock_provider_returns_valid_review():
    provider = MockProvider()
    raw = provider.complete("system", "postmortem text")
    review = parse_review(raw)
    assert review.summary
    assert review.confidence == "low"


def test_parse_review_tolerates_markdown_fence():
    raw = '```json\n{"summary": "ok", "weak_sections": ["Root Cause"], "notes": [], "confidence": "high"}\n```'
    review = parse_review(raw)
    assert review.summary == "ok"
    assert review.weak_sections == ["Root Cause"]


def test_parse_review_invalid_json_raises():
    with pytest.raises(ProviderError):
        parse_review("not json")


def test_claude_provider_wraps_missing_key_typeerror(monkeypatch):
    import anthropic

    from providers.claude import ClaudeProvider

    class FakeAnthropic:
        def __init__(self, *a, **k):
            raise TypeError("Could not resolve authentication method")

    monkeypatch.setattr(anthropic, "Anthropic", FakeAnthropic)
    provider = ClaudeProvider()
    with pytest.raises(ProviderError):
        provider.complete("system", "user")


def test_openai_provider_wraps_missing_key_error(monkeypatch):
    import openai as openai_module

    from providers.openai import OpenAIProvider

    class FakeOpenAI:
        def __init__(self, *a, **k):
            raise openai_module.OpenAIError("Missing credentials")

    monkeypatch.setattr(openai_module, "OpenAI", FakeOpenAI)
    provider = OpenAIProvider()
    with pytest.raises(ProviderError):
        provider.complete("system", "user")
