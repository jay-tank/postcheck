"""postcheck CLI — check an incident postmortem doc for required
sections and complete action items, deterministic first, AI as an optional
quality-review layer."""

from __future__ import annotations

import argparse
import sys
from typing import List, Optional

from prompt import SYSTEM_PROMPT, build_user_prompt
from providers import ProviderError, get_provider, parse_review
from render import render_result, to_json
from rules import lint

__version__ = "0.1.0"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="postcheck",
        description="Check an incident postmortem markdown doc for required sections and complete action items.",
    )
    parser.add_argument("file", nargs="?", help="Path to the postmortem markdown file. Reads stdin if omitted.")
    parser.add_argument("--ai", action="store_true", help="Add an AI content-quality review on top of the structural lint")
    parser.add_argument("--provider", default="claude", choices=["claude", "openai", "ollama", "mock"])
    parser.add_argument("--model", help="Override the provider's default model")
    parser.add_argument("--json", action="store_true", dest="as_json", help="Output machine-readable JSON")
    parser.add_argument("--no-color", action="store_true", help="Disable colored output")
    parser.add_argument("--version", action="version", version=f"postcheck {__version__}")
    return parser


def _read_input(path: Optional[str]) -> str:
    if path:
        with open(path, "r", encoding="utf-8") as f:
            return f.read()
    return sys.stdin.read()


def main(argv: Optional[List[str]] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    try:
        text = _read_input(args.file)
    except (OSError, UnicodeDecodeError) as exc:
        print(f"Error: could not read input: {exc}", file=sys.stderr)
        return 1

    if not text.strip():
        print("Error: no input text provided.", file=sys.stderr)
        return 1

    result = lint(text)

    review = None
    if args.ai:
        try:
            provider = get_provider(args.provider, model=args.model)
            response = provider.complete(SYSTEM_PROMPT, build_user_prompt(text))
            review = parse_review(response)
        except ProviderError as exc:
            print(f"Warning: AI review unavailable ({exc}); showing structural lint only.", file=sys.stderr)
        except Exception as exc:  # last-resort guard: never dump a raw traceback
            print(f"Warning: unexpected error from the '{args.provider}' provider ({exc}); showing structural lint only.", file=sys.stderr)

    if args.as_json:
        print(to_json(result, review))
    else:
        print(render_result(result, review, color=not args.no_color))

    return 1 if result.missing_sections or any(f.severity == "high" for f in result.findings) else 0


if __name__ == "__main__":
    raise SystemExit(main())
