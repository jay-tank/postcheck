import json
from pathlib import Path

from cli import main

FIXTURES = Path(__file__).parent / "fixtures"


def run_cli(args, capsys):
    code = main(args)
    captured = capsys.readouterr()
    return code, captured.out, captured.err


def test_complete_postmortem_exits_zero(capsys):
    code, out, err = run_cli([str(FIXTURES / "complete_postmortem.md"), "--no-color"], capsys)
    assert code == 0
    assert "All required sections present" in out


def test_incomplete_postmortem_exits_nonzero(capsys):
    code, out, err = run_cli([str(FIXTURES / "incomplete_postmortem.md"), "--no-color"], capsys)
    assert code == 1


def test_json_output_shape(capsys):
    code, out, err = run_cli([str(FIXTURES / "complete_postmortem.md"), "--json"], capsys)
    data = json.loads(out)
    assert "Timeline" in data["present_sections"]
    assert data["review"] is None


def test_ai_flag_adds_review_with_mock(capsys):
    code, out, err = run_cli([str(FIXTURES / "complete_postmortem.md"), "--ai", "--provider", "mock", "--json"], capsys)
    data = json.loads(out)
    assert data["review"] is not None


def test_missing_file_returns_clean_error_not_traceback(capsys):
    code, out, err = run_cli(["/nonexistent/file.md", "--no-color"], capsys)
    assert code == 1
    assert "Traceback" not in err


def test_empty_input_returns_clean_error(capsys, tmp_path):
    f = tmp_path / "empty.md"
    f.write_text("   ")
    code, out, err = run_cli([str(f), "--no-color"], capsys)
    assert code == 1
    assert "Error" in err


def test_ai_provider_failure_degrades_gracefully(capsys):
    code, out, err = run_cli([str(FIXTURES / "complete_postmortem.md"), "--ai", "--provider", "claude", "--no-color"], capsys)
    assert code == 0
    assert "Warning" in err


def test_stdin_input(capsys, monkeypatch):
    import io
    import sys

    text = (FIXTURES / "complete_postmortem.md").read_text()
    monkeypatch.setattr(sys, "stdin", io.StringIO(text))
    code, out, err = run_cli([], capsys)
    assert code == 0
