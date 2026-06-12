"""Tests for shared/select_automation_candidates.py."""
import copy
import json
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "shared"))
from select_automation_candidates import classify_rows  # noqa: E402


def _row(check: str | None, automation_id: str | None, tc_id: str = "1-1") -> dict:
    return {
        "Priority": "P1",
        "Automation Check": check,
        "Automation TC_ID": automation_id,
        "TC_ID": tc_id,
        "Test Summary": "요약",
    }


class TestClassifyRows:
    def test_all_ios_android_with_empty_automation_id_are_candidates(self):
        rows = [
            _row("All", None, "1-1"),
            _row("iOS", "", "1-2"),
            _row("Android", None, "1-3"),
        ]
        result = classify_rows(rows)
        assert [r["TC_ID"] for r in result["candidates"]] == ["1-1", "1-2", "1-3"]

    def test_check_value_matching_is_trimmed_and_case_insensitive(self):
        rows = [_row(" all ", None, "1-1"), _row("IOS", None, "1-2")]
        result = classify_rows(rows)
        assert len(result["candidates"]) == 2

    def test_rows_with_automation_tc_id_are_excluded_even_if_check_is_all(self):
        rows = [_row("All", "AUTO-001", "1-1")]
        result = classify_rows(rows)
        assert result["candidates"] == []
        assert [r["TC_ID"] for r in result["excluded_automated"]] == ["1-1"]

    def test_skip_rows_are_excluded(self):
        rows = [_row("Skip", None, "1-1"), _row("skip", None, "1-2")]
        result = classify_rows(rows)
        assert result["candidates"] == []
        assert len(result["excluded_skip"]) == 2

    def test_blank_check_goes_to_unclassified(self):
        rows = [_row(None, None, "1-1"), _row("", None, "1-2"), _row("  ", None, "1-3")]
        result = classify_rows(rows)
        assert result["candidates"] == []
        assert len(result["unclassified"]) == 3

    def test_unknown_check_value_is_separated(self):
        rows = [_row("Maybe", None, "1-1")]
        result = classify_rows(rows)
        assert result["candidates"] == []
        assert [r["TC_ID"] for r in result["unknown_check"]] == ["1-1"]

    def test_counts_match_group_sizes(self):
        rows = [
            _row("All", None, "1-1"),
            _row("All", "AUTO-001", "1-2"),
            _row("Skip", None, "1-3"),
            _row(None, None, "1-4"),
            _row("???", None, "1-5"),
        ]
        result = classify_rows(rows)
        assert result["counts"] == {
            "total": 5,
            "candidates": 1,
            "excluded_automated": 1,
            "excluded_skip": 1,
            "unclassified": 1,
            "unknown_check": 1,
        }

    def test_input_rows_are_not_mutated(self):
        rows = [_row("All", None, "1-1")]
        snapshot = copy.deepcopy(rows)
        classify_rows(rows)
        assert rows == snapshot


class TestCli:
    def test_cli_outputs_classified_json(self, tmp_path: Path):
        from openpyxl import Workbook

        wb = Workbook()
        wb.remove(wb.active)
        ws = wb.create_sheet("TabA")
        ws.append(["Priority", "Automation Check", "Automation TC_ID", "TC_ID", "Test Summary"])
        ws.append(["P1", "All", "", "1-1", "후보"])
        ws.append(["P2", "All", "AUTO-001", "1-2", "이미 자동화"])
        ws.append(["P3", "Skip", "", "1-3", "스킵"])
        xlsx = tmp_path / "tc.xlsx"
        wb.save(xlsx)

        result = subprocess.run(
            [sys.executable, "shared/select_automation_candidates.py",
             str(xlsx), "--tab", "TabA"],
            capture_output=True, text=True, check=True,
        )
        out = json.loads(result.stdout)
        assert out["tab"] == "TabA"
        assert [r["TC_ID"] for r in out["candidates"]] == ["1-1"]
        assert out["counts"]["excluded_automated"] == 1
        assert out["counts"]["excluded_skip"] == 1
