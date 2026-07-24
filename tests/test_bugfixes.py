"""Regression tests for the adversarial bug-hunt findings."""

from rules import extract_action_items, lint


def test_dual_alias_header_only_satisfies_one_section():
    """Regression: '## Root Cause and Impact' matched both the Root Cause
    and Impact alias lists, silently satisfying both from identical body
    content — even though there's no distinct Impact content at all."""
    text = (
        "# Incident\n\n"
        "## Summary\nThis is a long enough summary to not be flagged as empty by the checker.\n\n"
        "## Timeline\nThis is a long enough timeline section to not be flagged as empty either.\n\n"
        "## Root Cause and Impact\nThe database index was dropped causing full table scans under load.\n\n"
        "## Action Items\n- Fix it (@alice, due 2026-08-01)\n\n"
        "## What Went Well\nOn-call responded quickly and the rollback went smoothly overall.\n"
    )
    result = lint(text)
    # Only one of Root Cause / Impact should be satisfied by the combined header —
    # the other must be reported missing, not silently duplicated.
    satisfied = {"Root Cause", "Impact"} & set(result.present_sections)
    assert len(satisfied) == 1


def test_nested_subsection_does_not_satisfy_toplevel_requirement():
    """Regression: '### Action Items Owner' nested under an unrelated H2
    falsely satisfied the top-level Action Items requirement even though
    there's no real Action Items section anywhere in the document."""
    text = (
        "# Incident\n\n"
        "## Summary\nThis is a long enough summary to not be flagged as empty by the checker.\n\n"
        "## Some Other Topic\nUnrelated content here.\n\n"
        "### Action Items Owner\nThis is just a subsection about who owns action items generally.\n"
    )
    result = lint(text)
    assert "Action Items" in result.missing_sections


def test_unrelated_next_steps_header_does_not_satisfy_action_items():
    """Regression: 'Next Steps for the On-Call Rotation Process' (unrelated
    to incident follow-ups) matched the old 'next step' alias and falsely
    satisfied the Action Items requirement with irrelevant content."""
    text = (
        "# Incident\n\n"
        "## Next Steps for the On-Call Rotation Process\n"
        "We are considering changes to how on-call shifts are scheduled going forward.\n"
    )
    result = lint(text)
    assert "Action Items" in result.missing_sections


def test_header_inside_code_fence_does_not_split_the_real_section():
    """Regression: a '# not a real header' line inside a ``` fence was
    treated as a real markdown header, truncating the real section's body
    right before the fence and producing a false empty_section finding."""
    text = (
        "# Incident\n\n"
        "## Timeline\n"
        "Short intro.\n"
        "```\n"
        "# not a real header\n"
        "some log output here\n"
        "```\n"
        "More real timeline content that must not be truncated away by the fence.\n"
    )
    result = lint(text)
    assert not any(f.kind == "empty_section" and "Timeline" in f.detail for f in result.findings)


def test_bare_reference_date_is_not_treated_as_a_due_date():
    """Regression: a bare ISO-date-shaped string with no 'due' keyword
    (a reference date, not a deadline) previously false-positived as
    has_due_date."""
    items = extract_action_items("- Investigate the 2026-01-15 incident report (@alice)")
    assert items[0].has_owner
    assert not items[0].has_due_date


def test_due_date_with_due_keyword_still_detected():
    items = extract_action_items("- Fix the bug (@alice, due 2026-08-01)")
    assert items[0].has_due_date


def test_multiline_action_item_continuation_preserved():
    """Regression: a wrapped second physical line of an action item was
    silently dropped, losing any owner/due-date marker that lived there."""
    body = "- This item wraps onto\n  a second line with (@alice, due 2026-08-01)"
    items = extract_action_items(body)
    assert len(items) == 1
    assert items[0].has_owner
    assert items[0].has_due_date
    assert "second line" in items[0].text
