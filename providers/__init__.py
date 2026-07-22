"""Provider registry / factory."""

from __future__ import annotations

from typing import Optional

from .base import LLMProvider, MockProvider, ProviderError, parse_review

__all__ = ["LLMProvider", "ProviderError", "parse_review", "get_provider"]


def get_provider(name: str, model: Optional[str] = None) -> LLMProvider:
    """Return an LLM provider by name. SDKs are imported lazily, so users only
    need the dependency for the provider they actually use."""
    key = (name or "").strip().lower()

    if key == "mock":
        return MockProvider()
    if key == "claude":
        from .claude import ClaudeProvider

        return ClaudeProvider(model=model)
    if key == "openai":
        from .openai import OpenAIProvider

        return OpenAIProvider(model=model)
    if key == "ollama":
        from .ollama import OllamaProvider

        return OllamaProvider(model=model)

    raise ProviderError(
        f"Unknown provider {name!r}. Choose one of: claude, openai, ollama, mock."
    )
