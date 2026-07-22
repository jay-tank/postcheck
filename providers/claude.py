"""Anthropic Claude provider (default). Uses the official `anthropic` SDK."""

from __future__ import annotations

import os
from typing import Optional

from .base import LLMProvider, ProviderError

DEFAULT_CLAUDE_MODEL = "claude-opus-4-8"


class ClaudeProvider(LLMProvider):
    def __init__(self, model: Optional[str] = None):
        self.model = model or os.getenv("POSTCHECK_MODEL") or DEFAULT_CLAUDE_MODEL

    def complete(self, system: str, user: str) -> str:
        try:
            import anthropic
        except ImportError as exc:
            raise ProviderError(
                "The 'anthropic' package is required for the Claude provider. "
                "Install it with:  pip install 'postcheck[claude]'"
            ) from exc

        try:
            client = anthropic.Anthropic()  # resolves ANTHROPIC_API_KEY
            resp = client.messages.create(
                model=self.model,
                max_tokens=1024,
                system=system,
                messages=[{"role": "user", "content": user}],
            )
        except anthropic.AuthenticationError as exc:
            raise ProviderError(
                "Claude authentication failed. Set ANTHROPIC_API_KEY, "
                "or use --provider ollama for a local model."
            ) from exc
        except anthropic.APIError as exc:
            raise ProviderError(f"Claude API error: {exc}") from exc
        except TypeError as exc:
            # The SDK raises a plain TypeError (not AuthenticationError) when
            # no API key/credentials are configured at all.
            raise ProviderError(
                "ANTHROPIC_API_KEY is not set. Export it, or use "
                "--provider ollama for a local model."
            ) from exc

        return "".join(b.text for b in resp.content if getattr(b, "type", None) == "text")
