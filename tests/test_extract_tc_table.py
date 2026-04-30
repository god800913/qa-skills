"""Tests for shared/extract_tc_table.py."""
import json
import subprocess
import sys
from pathlib import Path

import pytest


@pytest.fixture
def issues_xlsx_path(fixtures_dir: Path) -> Path:
    return fixtures_dir / "sample_tc_with_issues.xlsx"


def _run(xlsx: Path, tab: str) -> list[dict]:
    result = subprocess.run(
        [sys.executable, "shared/extract_tc_table.py", str(xlsx), "--tab", tab],
        capture_output=True, text=True, check=True,
    )
    return json.loads(result.stdout)


class TestExtractTCTable:
    def test_returns_list_of_dicts(self, issues_xlsx_path: Path):
        out = _run(issues_xlsx_path, "TabA")
        assert isinstance(out, list)
        assert all(isinstance(r, dict) for r in out)

    def test_each_row_has_canonical_keys(self, issues_xlsx_path: Path):
        out = _run(issues_xlsx_path, "TabA")
        # All rows should have at least Priority, TC_ID, Test Summary
        for r in out:
            for k in ("Priority", "TC_ID", "Test Summary"):
                assert k in r, f"Missing {k} in {r}"

    def test_skips_section_headers_and_blank_rows(self, issues_xlsx_path: Path):
        out = _run(issues_xlsx_path, "TabA")
        # TabA has 7 TC rows + 1 section header → expect 7 in output
        assert len(out) == 7
