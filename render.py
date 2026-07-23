"""Render a LintResult (+ optional QualityReview) to the terminal or JSON."""

from __future__ import annotations

import io
import json
from dataclasses import asdict
from typing import Optional

from models import LintResult, QualityReview

_SEVERITY_COLOR = {
    "high": "bright_red",
    "medium": "yellow",
    "low": "cyan",
}


def to_json(result: LintResult, review: Optional[QualityReview]) -> str:
    return json.dumps(
        {
            "present_sections": result.present_sections,
            "missing_sections": result.missing_sections,
            "action_items": [asdict(a) for a in result.action_items],
            "findings": [asdict(f) for f in result.findings],
            "review": asdict(review) if review else None,
        },
        indent=2,
    )


def render_result(result: LintResult, review: Optional[QualityReview] = None, color: bool = True) -> str:
    from rich.console import Console
    from rich.markup import escape

    console = Console(
        record=True, no_color=not color, width=100, force_terminal=color, file=io.StringIO()
    )

    if not result.findings:
        console.print("\n[green]✓ All required sections present, all action items have an owner and due date.[/green]\n")
    else:
        for f in result.findings:
            colour = _SEVERITY_COLOR.get(f.severity, "yellow")
            console.print(f"[{colour}]{f.severity.upper()}[/{colour}] {escape(f.detail)}")

    console.print(f"\n[dim]Sections present: {', '.join(result.present_sections) or '(none)'}[/dim]")
    if result.missing_sections:
        console.print(f"[dim]Sections missing: {', '.join(result.missing_sections)}[/dim]")

    if review:
        console.print(f"\n[bold]AI quality review:[/bold] {escape(review.summary)}")
        if review.weak_sections:
            console.print(f"[yellow]Weak sections: {', '.join(escape(s) for s in review.weak_sections)}[/yellow]")
        for note in review.notes:
            console.print(f"[dim]· {escape(note)}[/dim]")

    return console.export_text(styles=color)
