"""Tests for shared/patch_tc_ids.py."""
import hashlib
import json
import subprocess
import sys
from pathlib import Path

import pytest


@pytest.fixture
def issues_xlsx_path(fixtures_dir: Path) -> Path:
    return fixtures_dir / "sample_tc_with_issues.xlsx"


def _run_patch(xlsx: Path, tab: str, output: Path) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, "shared/patch_tc_ids.py", str(xlsx),
         "--tab", tab, "--output", str(output)],
        capture_output=True, text=True, check=True,
    )


def _run_validate(xlsx: Path, tab: str) -> dict:
    result = subprocess.run(
        [sys.executable, "shared/validate_format.py", str(xlsx), "--tab", tab],
        capture_output=True, text=True, check=True,
    )
    return json.loads(result.stdout)


class TestPatchTcIds:
    def test_original_file_not_modified(self, issues_xlsx_path: Path, tmp_path: Path):
        before = hashlib.sha256(issues_xlsx_path.read_bytes()).hexdigest()
        _run_patch(issues_xlsx_path, "TabA", tmp_path / "patched.xlsx")
        after = hashlib.sha256(issues_xlsx_path.read_bytes()).hexdigest()
        assert before == after

    def test_second_occurrence_gets_dup_suffix(self, issues_xlsx_path: Path, tmp_path: Path):
        from python_calamine import CalamineWorkbook

        out = tmp_path / "patched.xlsx"
        _run_patch(issues_xlsx_path, "TabA", out)
        rows = CalamineWorkbook.from_path(str(out)).get_sheet_by_name("TabA").to_python()
        flat = [str(c) for r in rows for c in r if c]
        # First occurrence keeps its ID; second gets -dup-2
        assert "1-2" in flat
        assert "1-2-dup-2" in flat

    def test_patched_file_has_no_duplicate_issues(self, issues_xlsx_path: Path, tmp_path: Path):
        out = tmp_path / "patched.xlsx"
        _run_patch(issues_xlsx_path, "TabA", out)
        validated = _run_validate(out, "TabA")
        dups = [i for i in validated["issues"] if i["category"] == "duplicate_tc_id"]
        assert dups == []

    def test_stdout_last_line_is_output_path(self, issues_xlsx_path: Path, tmp_path: Path):
        out = tmp_path / "patched.xlsx"
        result = _run_patch(issues_xlsx_path, "TabA", out)
        last = result.stdout.strip().splitlines()[-1]
        assert Path(last).exists()
        assert last.endswith(".xlsx")

    def test_collision_appends_suffix(self, issues_xlsx_path: Path, tmp_path: Path):
        out = tmp_path / "patched.xlsx"
        out.write_text("placeholder")
        result = _run_patch(issues_xlsx_path, "TabA", out)
        last = result.stdout.strip().splitlines()[-1]
        assert last != str(out)
        assert Path(last).exists()

    def test_no_duplicates_reports_zero_patches(self, tmp_path: Path):
        from openpyxl import Workbook

        wb = Workbook()
        wb.remove(wb.active)
        ws = wb.create_sheet("Clean")
        ws.append(["Priority", "TC_ID", "Test Summary"])
        ws.append(["P1", "1-1", "케이스 A"])
        ws.append(["P2", "1-2", "케이스 B"])
        src = tmp_path / "clean.xlsx"
        wb.save(src)

        result = _run_patch(src, "Clean", tmp_path / "out.xlsx")
        assert "0" in result.stdout.splitlines()[0]
