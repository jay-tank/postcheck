"""Deterministic postmortem structure checker.

Checks a markdown postmortem doc for required sections and, within the
action items section, whether each item has an assigned owner and a due
date. This is pure structural/pattern matching — generic markdown linters
(markdownlint, remark-lint) check formatting style, not semantic content
like "does this doc actually have a root cause section," which is the
actual gap this tool fills.
"""

from __future__ import annotations

import re
from typing import Dict, List, Optional, Tuple

from models import ActionItem, Finding, LintResult

# (aliases to match in a header, canonical name, severity if missing)
# "next step"/"follow up" were removed from Action Items' aliases — they're
# generic enough to false-positive on unrelated headers like "Next Steps for
# the On-Call Rotation Process". "follow-up" (hyphenated) is kept since it's
# specific enough to postmortem action-item conventions.
REQUIRED_SECTIONS: List[Tuple[List[str], str, str]] = [
    (["summary", "overview"], "Summary", "medium"),
    (["timeline"], "Timeline", "high"),
    (["root cause"], "Root Cause", "high"),
    (["impact"], "Impact", "medium"),
    (["action item", "follow-up"], "Action Items", "high"),
    (["what went well", "lessons learned", "positives"], "What Went Well", "low"),
]

_HEADER_RE = re.compile(r"^(#{1,6})\s+(.+?)\s*$", re.MULTILINE)
_FENCE_RE = re.compile(r"^\s*```")
_MIN_SECTION_LENGTH = 20  # chars; below this, a section is "present but empty"

_OWNER_RE = re.compile(r"@\w+|\bowner\s*:", re.IGNORECASE)
# Requires the word "due" itself, not just any ISO-date-shaped string — a
# bare date like "Investigate the 2026-01-15 incident report" references a
# date without assigning a deadline, and previously false-positived as
# "has_due_date".
_DATE_RE = re.compile(r"\bdue\b", re.IGNORECASE)
_ACTION_ITEM_LINE_RE = re.compile(r"^\s*(?:[-*]|\d+\.)\s*(?:\[[ xX]\]\s*)?(.+)$")


def _mask_code_fences(text: str) -> str:
    """Blank out the *content* of fenced code blocks (keeping line count and
    character offsets identical) so a line like '# not a real header' inside
    a ``` fence can never be mistaken for a real markdown header. Offsets
    are preserved so header-match positions found on the masked text still
    correctly index into the original text for body extraction."""
    lines = text.split("\n")
    masked_lines = []
    in_fence = False
    for line in lines:
        if _FENCE_RE.match(line):
            in_fence = not in_fence
            masked_lines.append(line)
        elif in_fence:
            masked_lines.append(" " * len(line))
        else:
            masked_lines.append(line)
    return "\n".join(masked_lines)


def _split_sections(text: str) -> List[Tuple[str, int, str]]:
    """Split markdown into a list of (title, header_level, body_text),
    in document order. Fenced code blocks are masked before header matching
    so their contents can never be mistaken for real headers; bodies are
    still sliced from the original (unmasked) text so real content —
    including genuine fenced code within a section — is preserved."""
    masked = _mask_code_fences(text)
    matches = list(_HEADER_RE.finditer(masked))
    sections: List[Tuple[str, int, str]] = []
    for i, m in enumerate(matches):
        title = m.group(2).strip()
        level = len(m.group(1))
        start = m.end()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
        sections.append((title, level, text[start:end].strip()))
    return sections


def _section_header_level(sections: List[Tuple[str, int, str]]) -> int:
    """The level real section headers live at. A lone level-1 header is
    treated as the document's title, not a section (the near-universal
    "# Title" then "## Section" convention) — so the section level is the
    minimum level among headers at level >= 2, defaulting to 2 if there are
    none (e.g. a doc with no headers at all, or only a single H1 title)."""
    candidate_levels = [level for _, level, _ in sections if level >= 2]
    return min(candidate_levels) if candidate_levels else 2


def _find_section(
    sections: List[Tuple[str, int, str]], aliases: List[str], claimed: set, section_level: int
) -> Optional[Tuple[int, str]]:
    """Find the first not-yet-claimed header at `section_level` matching any alias.

    Two fixes baked in here:
    - Only headers at the document's actual section level are considered —
      a deeper subsection like "### Action Items Owner" nested under an
      unrelated "## Some Topic" no longer falsely satisfies the top-level
      "Action Items" requirement.
    - `claimed` tracks which header INDEXES have already been assigned to a
      different required section, so a single header like "## Root Cause and
      Impact" can satisfy at most one required section (whichever appears
      first in REQUIRED_SECTIONS order) instead of silently satisfying both
      from identical body content.
    """
    for idx, (title, level, body) in enumerate(sections):
        if idx in claimed or level != section_level:
            continue
        title_lower = title.lower()
        if any(alias in title_lower for alias in aliases):
            return idx, body
    return None


def extract_action_items(body: str) -> List[ActionItem]:
    """Extract action items, joining wrapped continuation lines (text that
    follows a bullet without starting a new one) into the same item so an
    owner/due-date marker on a wrapped second line isn't lost."""
    raw_items: List[str] = []
    for line in body.splitlines():
        m = _ACTION_ITEM_LINE_RE.match(line)
        if m:
            content = m.group(1).strip()
            if content:
                raw_items.append(content)
        elif raw_items and line.strip():
            raw_items[-1] += " " + line.strip()

    return [
        ActionItem(
            text=text,
            has_owner=bool(_OWNER_RE.search(text)),
            has_due_date=bool(_DATE_RE.search(text)),
        )
        for text in raw_items
    ]


def lint(text: str) -> LintResult:
    sections = _split_sections(text)
    result = LintResult()

    action_items_body = None
    claimed: set = set()
    section_level = _section_header_level(sections)

    for aliases, canonical, severity in REQUIRED_SECTIONS:
        found = _find_section(sections, aliases, claimed, section_level)
        if found is None:
            result.missing_sections.append(canonical)
            result.findings.append(
                Finding(
                    kind="missing_section",
                    severity=severity,
                    detail=f"No '{canonical}' section found.",
                )
            )
            continue

        idx, body = found
        claimed.add(idx)
        result.present_sections.append(canonical)

        if len(body) < _MIN_SECTION_LENGTH:
            result.findings.append(
                Finding(
                    kind="empty_section",
                    severity="medium" if severity == "high" else "low",
                    detail=f"'{canonical}' section is present but nearly empty ({len(body)} chars).",
                )
            )

        if canonical == "Action Items":
            action_items_body = body

    if action_items_body:
        items = extract_action_items(action_items_body)
        result.action_items = items
        incomplete = [i for i in items if not i.is_complete]
        if items and incomplete:
            result.findings.append(
                Finding(
                    kind="incomplete_action_item",
                    severity="high",
                    detail=f"{len(incomplete)} of {len(items)} action item(s) have no owner and/or due date.",
                )
            )

    return result
