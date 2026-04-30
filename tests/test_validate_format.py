"""Tests for shared/validate_format.py."""
import json
import subprocess
import sys
from pathlib import Path

import pytest


@pytest.fixture
def issues_xlsx_path(fixtures_dir: Path) -> Path:
    return fixtures_dir / "sample_tc_with_issues.xlsx"


def _run(xlsx: Path, tab: str) -> dict:
    result = subprocess.run(
        [sys.executable, "shared/validate_format.py", str(xlsx), "--tab", tab],
        capture_output=True, text=True, check=True,
    )
    return json.loads(result.stdout)


class TestValidateFormat:
    def test_returns_dict_with_issues_and_summary(self, issues_xlsx_path: Path):
        out = _run(issues_xlsx_path, "TabA")
        assert "issues" in out
        assert "summary" in out
        assert "total_rows" in out["summary"]

    def test_detects_missing_priority(self, issues_xlsx_path: Path):
        out = _run(issues_xlsx_path, "TabA")
        msgs = [i for i in out["issues"]
                if i["category"] == "missing_required" and i["field"] == "Priority"]
        assert len(msgs) == 1, f"Expected 1 missing Priority, got: {msgs}"

    def test_detects_missing_expected_result(self, issues_xlsx_path: Path):
        out = _run(issues_xlsx_path, "TabA")
        msgs = [i for i in out["issues"]
                if i["category"] == "missing_required" and i["field"] == "Expected Result"]
        assert len(msgs) == 1

    def test_detects_invalid_os_enum(self, issues_xlsx_path: Path):
        out = _run(issues_xlsx_path, "TabA")
        msgs = [i for i in out["issues"]
                if i["category"] == "invalid_enum" and i["field"] == "OS"]
        assert len(msgs) == 1
        assert "MacOS" in msgs[0]["message"]

    def test_detects_duplicate_tc_id(self, issues_xlsx_path: Path):
        out = _run(issues_xlsx_path, "TabA")
        msgs = [i for i in out["issues"] if i["category"] == "duplicate_tc_id"]
        assert len(msgs) >= 1
        assert any("1-2" in m["message"] for m in msgs)

    def test_each_issue_has_row_number(self, issues_xlsx_path: Path):
        out = _run(issues_xlsx_path, "TabA")
        for issue in out["issues"]:
            assert "row" in issue
            assert isinstance(issue["row"], int)
            assert issue["row"] > 0
