"""Data structures passed between the parser/checker, providers, and renderer."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class ActionItem:
    """One action-item line extracted from the postmortem's action items section."""

    text: str
    has_owner: bool
    has_due_date: bool

    @property
    def is_complete(self) -> bool:
        return self.has_owner and self.has_due_date


@dataclass
class Finding:
    """A single deterministic lint finding — missing section, thin section,
    or an incomplete action item."""

    kind: str  # "missing_section" | "empty_section" | "incomplete_action_item"
    severity: str  # "high" | "medium" | "low"
    detail: str


@dataclass
class LintResult:
    present_sections: List[str] = field(default_factory=list)
    missing_sections: List[str] = field(default_factory=list)
    action_items: List[ActionItem] = field(default_factory=list)
    findings: List[Finding] = field(default_factory=list)


@dataclass
class QualityReview:
    """Optional AI-generated layer on top of the deterministic lint. Only
    ever sees the postmortem's own text (no external data) — used to judge
    depth/quality of what's written, never to decide whether a section is
    present (that's the deterministic parser's job)."""

    summary: str
    weak_sections: List[str] = field(default_factory=list)
    notes: List[str] = field(default_factory=list)
    confidence: str = "unknown"
