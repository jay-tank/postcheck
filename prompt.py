"""Builds the prompt for the optional --ai quality-review layer.

The deterministic checker (rules.py) already decided WHICH sections exist
and whether action items are complete. The AI's job is different: judge
whether the *content* of present sections is actually substantive — e.g. a
"Root Cause" section that exists but just says "unclear, will investigate"
technically passes the structural check but isn't a real root cause.
"""

from __future__ import annotations

SYSTEM_PROMPT = """You review the text of an incident postmortem document \
and judge whether its sections are substantive, not just present (structural \
presence has already been checked separately — you are NOT being asked to \
check whether sections exist, only whether their content is actually useful).

Respond with ONLY a JSON object, no prose outside it:
{
  "summary": "<1-3 sentence overview of the postmortem's overall quality>",
  "weak_sections": ["<section names whose content is vague, superficial, or non-actionable>"],
  "notes": ["<short, specific notes, e.g. 'Root Cause names a symptom (service was slow) rather than a cause'>"],
  "confidence": "high|medium|low"
}

Rules:
- Base your answer only on the text given.
- A section can be "present" but still weak — e.g. a root cause that
  restates the symptom, or an action item that's vague ('improve monitoring')
  rather than concrete.
"""


def build_user_prompt(postmortem_text: str) -> str:
    return f"Postmortem document:\n\n{postmortem_text}"
