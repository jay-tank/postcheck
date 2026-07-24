from pathlib import Path

from rules import extract_action_items, lint

FIXTURES = Path(__file__).parent / "fixtures"


def test_complete_postmortem_has_no_high_severity_findings():
    text = (FIXTURES / "complete_postmortem.md").read_text()
    result = lint(text)
    assert result.missing_sections == []
    assert not any(f.severity == "high" for f in result.findings)


def test_complete_postmortem_all_action_items_complete():
    text = (FIXTURES / "complete_postmortem.md").read_text()
    result = lint(text)
    assert len(result.action_items) == 2
    assert all(a.is_complete for a in result.action_items)


def test_incomplete_postmortem_flags_missing_sections():
    text = (FIXTURES / "incomplete_postmortem.md").read_text()
    result = lint(text)
    assert "Timeline" in result.missing_sections
    assert "Root Cause" in result.missing_sections
    assert "Impact" in result.missing_sections


def test_incomplete_postmortem_flags_incomplete_action_items():
    text = (FIXTURES / "incomplete_postmortem.md").read_text()
    result = lint(text)
    assert any(f.kind == "incomplete_action_item" for f in result.findings)


def test_empty_section_flagged():
    text = "# Incident\n\n## Summary\nBad\n\n## Timeline\n- 1\n- 2\n- 3\n\n## Root Cause\nUnclear.\n\n## Impact\nUsers affected somewhat significantly for a while.\n\n## Action Items\n- Fix (@a, due 2026-01-01)\n"
    result = lint(text)
    assert any(f.kind == "empty_section" for f in result.findings)


def test_action_item_with_at_mention_and_date_is_complete():
    items = extract_action_items("- Fix the bug (@alice, due 2026-08-01)")
    assert len(items) == 1
    assert items[0].has_owner
    assert items[0].has_due_date
    assert items[0].is_complete


def test_action_item_with_owner_colon_syntax():
    items = extract_action_items("- Fix the bug — owner: bob, due: 2026-08-01")
    assert items[0].has_owner
    assert items[0].has_due_date


def test_action_item_missing_owner():
    items = extract_action_items("- Fix the bug, due 2026-08-01")
    assert not items[0].has_owner
    assert items[0].has_due_date


def test_action_item_missing_date():
    items = extract_action_items("- Fix the bug (@alice)")
    assert items[0].has_owner
    assert not items[0].has_due_date


def test_checkbox_style_action_items_parsed():
    items = extract_action_items("- [ ] Fix the bug (@alice, due 2026-08-01)\n- [x] Already done (@bob, due 2026-01-01)")
    assert len(items) == 2


def test_numbered_action_items_parsed():
    items = extract_action_items("1. Fix the bug (@alice, due 2026-08-01)\n2. Add monitoring (@bob, due 2026-08-02)")
    assert len(items) == 2


def test_section_alias_matching_is_case_insensitive():
    text = (
        "# X\n\n## SUMMARY\nThis is a summary long enough to not be flagged as empty for testing purposes.\n\n"
        "## TIMELINE\nEvents happened here in some detail to avoid the empty check triggering.\n\n"
        "## Root cause analysis\nThe actual underlying root cause of this incident was found to be X.\n\n"
        "## impact\nModerate impact experienced by several users during this incident window.\n\n"
        "## Follow-up items\n- Do X (@a, due 2026-01-01)\n\n"
        "## Lessons learned\nOn-call responded quickly and communication was clear throughout.\n"
    )
    result = lint(text)
    assert result.missing_sections == []


def test_completely_empty_input():
    result = lint("")
    assert len(result.missing_sections) == len(result.missing_sections)  # no crash
    assert set(result.missing_sections) == {"Summary", "Timeline", "Root Cause", "Impact", "Action Items", "What Went Well"}
