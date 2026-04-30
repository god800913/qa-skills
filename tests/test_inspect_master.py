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


class TestParseTabMetaErrors:
    def test_header_not_found_error_includes_tab_and_file_context(self, tmp_path: Path):
        from openpyxl import Workbook

        wb = Workbook()
        wb.remove(wb.active)
        ws = wb.create_sheet("BrokenTab")
        ws.append(["foo", "bar"])  # no Priority cell
        path = tmp_path / "broken.xlsx"
        wb.save(path)

        with pytest.raises(ValueError, match="BrokenTab"):
            parse_tab_meta(path, "BrokenTab")


class TestParseTabMetaSections:
    def test_lounge_has_sections(self, minimal_master_path: Path):
        meta = parse_tab_meta(minimal_master_path, "Lounge")
        # Lounge fixture has at least one section header in the first 30 rows
        assert "sections" in meta
        assert isinstance(meta["sections"], list)
        # Each section has name, header_row, last_tc_id (or None)
        for sec in meta["sections"]:
            assert "name" in sec
            assert "header_row" in sec
            assert "last_tc_id" in sec  # may be None if no TCs in section yet

    def test_last_tc_id_format(self, minimal_master_path: Path):
        meta = parse_tab_meta(minimal_master_path, "Lounge")
        ids_found = [s["last_tc_id"] for s in meta["sections"] if s["last_tc_id"]]
        # Pattern <section>-<number>, e.g. "1-12"
        for tc_id in ids_found:
            assert "-" in tc_id, f"Unexpected TC_ID shape: {tc_id}"

    def test_login_section_name_skips_dash_sentinel(self, minimal_master_path: Path):
        meta = parse_tab_meta(minimal_master_path, "login")
        # The login tab has '-' as Priority-1 cell in the section header row;
        # the real section label is in a later cell. Names should not be just '-'.
        names = [s["name"] for s in meta["sections"]]
        for n in names:
            assert n != "-", f"Section name '-' is the dash sentinel, not a real label"
            assert n.strip(), "Section name should not be empty"


import json
import subprocess
import sys


class TestCLI:
    def test_no_tab_lists_all(self, minimal_master_path: Path):
        result = subprocess.run(
            [sys.executable, "shared/inspect_master.py", str(minimal_master_path)],
            capture_output=True,
            text=True,
            check=True,
        )
        data = json.loads(result.stdout)
        assert "tabs" in data
        names = {t["name"] for t in data["tabs"]}
        assert names == {"login", "Lounge"}

    def test_with_tab_returns_meta(self, minimal_master_path: Path):
        result = subprocess.run(
            [sys.executable, "shared/inspect_master.py", str(minimal_master_path), "--tab", "Lounge"],
            capture_output=True,
            text=True,
            check=True,
        )
        data = json.loads(result.stdout)
        assert data["tab"] == "Lounge"
        assert "columns" in data
        assert "sections" in data
