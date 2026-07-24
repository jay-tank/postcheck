# postcheck

> Check an incident postmortem doc for required sections and complete action items — deterministic first, optional AI content-quality review.

[![Python 3.9+](https://img.shields.io/badge/python-3.9%2B-blue.svg)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

Every team has a postmortem template. Almost nobody enforces it — postmortems
drift into "here's roughly what happened," with action items that never got
an owner or a due date attached, so they quietly never happen.
`postcheck` checks a markdown postmortem against that template, so a
missing root cause or an unassigned action item is a CI failure, not
something nobody notices for six months.

```text
$ postcheck incident-2026-07-20.md

HIGH No 'Root Cause' section found.
HIGH 2 of 2 action item(s) have no owner and/or due date.

Sections present: Summary, Timeline, Action Items
Sections missing: Root Cause, Impact, What Went Well
```

## Why postcheck

- **Checks content, not formatting.** Generic markdown linters
  (`markdownlint`, `remark-lint`) only check style — heading levels, line
  length. Nothing checks whether a postmortem doc actually *has* a root
  cause section, or whether its action items have real owners and dates.
- **CI-gate-ready.** Exits non-zero if any required section is missing or
  any high-severity finding exists — wire it into a PR check that gates
  merging an incident's postmortem doc.
- **Deterministic core, no AI required.** Section presence and action-item
  completeness are pure structural checks. `--ai` adds an optional layer
  that judges whether present sections are actually *substantive* (a root
  cause that just restates the symptom) — a genuinely different question
  the structural check can't answer.

## Install

```bash
pip install postcheck
```

## Usage

```bash
postcheck incident.md                        # structural lint only, no AI needed
postcheck incident.md --ai --provider mock    # + content-quality review, no key needed
postcheck incident.md --json                  # machine-readable output
cat incident.md | postcheck                   # reads stdin if no file given
```

Required sections (matched case-insensitively, by header alias): Summary,
Timeline, Root Cause, Impact, Action Items, What Went Well. Action items are
checked for an owner (`@name` or `owner:`) and a due date (containing the
word "due").

## Providers

`--provider claude` (default) · `openai` · `ollama` (local, no API key) ·
`mock` (offline, deterministic). Only used with `--ai`.

## License

MIT — see [LICENSE](LICENSE).
