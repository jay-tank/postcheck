"""Ollama provider — runs a local model, no API key required."""

from __future__ import annotations

import json
import os
import urllib.error
import urllib.request
from typing import Optional

from .base import LLMProvider, ProviderError

DEFAULT_OLLAMA_MODEL = "llama3"


class OllamaProvider(LLMProvider):
    def __init__(self, model: Optional[str] = None):
        self.model = model or os.getenv("POSTCHECK_MODEL") or DEFAULT_OLLAMA_MODEL
        self.host = os.getenv("OLLAMA_HOST", "http://localhost:11434").rstrip("/")

    def complete(self, system: str, user: str) -> str:
        payload = {
            "model": self.model,
            "system": system,
            "prompt": user,
            "stream": False,
            "format": "json",
        }
        req = urllib.request.Request(
            f"{self.host}/api/generate",
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json"},
        )
        try:
            with urllib.request.urlopen(req, timeout=120) as resp:
                body = json.loads(resp.read().decode("utf-8"))
        except urllib.error.URLError as exc:
            raise ProviderError(
                f"Could not reach Ollama at {self.host}. Is it running? "
                f"Start it with `ollama serve` and pull a model (`ollama pull {self.model}`). ({exc})"
            ) from exc
        except json.JSONDecodeError as exc:
            raise ProviderError(f"Unexpected response from Ollama: {exc}") from exc

        return body.get("response", "")
