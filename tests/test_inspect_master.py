"""Tests for shared/inspect_master.py."""
from pathlib import Path

import pytest

from shared.inspect_master import list_tabs
from shared.inspect_master import parse_tab_meta


class TestListTabs:
    def test_returns_all_tabs_with_summary_marked_excluded(self, minimal_master_path: Path):
        tabs = list_tabs(minimal_master_path)
        names = {t["name"] for t in tabs}
        assert names == {"login", "Lounge"}
        for tab in tabs:
            assert "is_summary" in tab
            assert "column_count" in tab
            assert tab["is_summary"] is False  # neither is a Summary tab


class TestListTabsSummaryDetection:
    def test_summary_tab_marked_excluded(self, tmp_path: Path):
        from openpyxl import Workbook

        wb = Workbook()
        wb.remove(wb.active)
        wb.create_sheet("Summary").append(["x"])
        wb.create_sheet("Summary의 사본").append(["x"])
        wb.create_sheet("Lounge").append(["Priority", "OS"])
        path = tmp_path / "synthetic.xlsx"
        wb.save(path)

        tabs = list_tabs(path)
        names_to_exclusion = {t["name"]: t["is_summary"] for t in tabs}
        assert names_to_exclusion == {
            "Summary": True,
            "Summary의 사본": True,
            "Lounge": False,
        }


class TestParseTabMeta:
    def test_login_tab_has_leading_blank_column_handled(self, minimal_master_path: Path):
        meta = parse_tab_meta(minimal_master_path, "login")
        # Standard columns must be present in mapping regardless of leading blank
        assert "Priority" in meta["columns"]
        assert "TC_ID" in meta["columns"]
        # The mapping value is the actual cell index in the row, so leading-blank tabs
        # have Priority at index 1, not 0.
        assert meta["columns"]["Priority"] >= 1

    def test_lounge_tab_no_leading_blank(self, minimal_master_path: Path):
        meta = parse_tab_meta(minimal_master_path, "Lounge")
        assert "Priority" in meta["columns"]
        # Lounge should have Priority at index 0 (no leading blank)
        assert meta["columns"]["Priority"] == 0

    def test_returns_template_type_single(self, minimal_master_path: Path):
        meta = parse_tab_meta(minimal_master_path, "Lounge")
        assert meta["template_type"] == "single"
