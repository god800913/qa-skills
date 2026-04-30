"""Tests for shared/append_to_master.py."""
import json
import shutil
import subprocess
import sys
from pathlib import Path

import pytest
from python_calamine import CalamineWorkbook


@pytest.fixture
def append_rows_json(tmp_path: Path) -> Path:
    data = {
        "rows": [
            {
                "section": "Async First Entry",  # existing section in Lounge fixture
                "Priority": "P3", "OS": "All", "Automation Check": "All",
                "Test Item": "라운지 진입",
                "Test Summary": "신규 추천 알고리즘 활성화 시 추천 노출",
                "Remote Config / Admin": "enableNewLoungeRecommendation: true",
                "Pre-condition": "신규 사용자",
                "Test Step": "라운지 탭 진입",
                "Expected Result": "추천 카드 섹션 노출",
            },
        ]
    }
    p = tmp_path / "append.json"
    p.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
    return p


@pytest.fixture
def master_copy(tmp_path: Path, minimal_master_path: Path) -> Path:
    """Copy of the minimal master so we can verify the original isn't mutated."""
    dst = tmp_path / "master_copy.xlsx"
    shutil.copy2(minimal_master_path, dst)
    return dst


class TestAppendToMaster:
    def test_does_not_modify_master(self, master_copy: Path, append_rows_json: Path,
                                     tmp_path: Path, minimal_master_path: Path):
        out = tmp_path / "appended.xlsx"
        original_bytes = minimal_master_path.read_bytes()
        subprocess.run(
            [sys.executable, "shared/append_to_master.py",
             "--master", str(master_copy), "--tab", "Lounge",
             "--rows", str(append_rows_json), "--output", str(out)],
            check=True, capture_output=True, text=True,
        )
        # Original master untouched
        assert minimal_master_path.read_bytes() == original_bytes
        # Master copy untouched (we only read from it)
        assert master_copy.read_bytes() == original_bytes

    def test_creates_new_file_with_appended_rows(self, master_copy: Path,
                                                   append_rows_json: Path, tmp_path: Path):
        out = tmp_path / "appended.xlsx"
        subprocess.run(
            [sys.executable, "shared/append_to_master.py",
             "--master", str(master_copy), "--tab", "Lounge",
             "--rows", str(append_rows_json), "--output", str(out)],
            check=True, capture_output=True, text=True,
        )
        assert out.exists()
        wb = CalamineWorkbook.from_path(str(out))
        # Both tabs preserved
        assert set(wb.sheet_names) == {"login", "Lounge"}
        # The appended row's Test Summary appears in the Lounge tab
        rows = wb.get_sheet_by_name("Lounge").to_python()
        flat = [str(c) for r in rows for c in r if c]
        assert any("신규 추천 알고리즘 활성화 시 추천 노출" in c for c in flat)

    def test_login_tab_unchanged(self, master_copy: Path, append_rows_json: Path,
                                  tmp_path: Path, minimal_master_path: Path):
        out = tmp_path / "appended.xlsx"
        subprocess.run(
            [sys.executable, "shared/append_to_master.py",
             "--master", str(master_copy), "--tab", "Lounge",
             "--rows", str(append_rows_json), "--output", str(out)],
            check=True, capture_output=True, text=True,
        )
        original_login = CalamineWorkbook.from_path(str(minimal_master_path)).get_sheet_by_name("login").to_python()
        new_login = CalamineWorkbook.from_path(str(out)).get_sheet_by_name("login").to_python()
        assert original_login == new_login

    def test_tc_id_auto_incremented(self, master_copy: Path, append_rows_json: Path,
                                     tmp_path: Path):
        out = tmp_path / "appended.xlsx"
        subprocess.run(
            [sys.executable, "shared/append_to_master.py",
             "--master", str(master_copy), "--tab", "Lounge",
             "--rows", str(append_rows_json), "--output", str(out)],
            check=True, capture_output=True, text=True,
        )
        # Find the appended row in output and verify its TC_ID is `1-N` where N
        # is one more than the last `1-X` TC_ID in the original Async First Entry section.
        wb = CalamineWorkbook.from_path(str(out))
        rows = wb.get_sheet_by_name("Lounge").to_python()
        # Find the row containing the new Test Summary
        new_row = next(r for r in rows if any(
            isinstance(c, str) and "신규 추천 알고리즘 활성화 시 추천 노출" in c
            for c in r
        ))
        # Find TC_ID in that row — should match pattern 1-N
        tc_ids = [c for c in new_row if isinstance(c, str) and c.startswith("1-")]
        assert tc_ids, f"No 1-* TC_ID found in appended row: {new_row}"
        # The numeric suffix should be > the last existing 1-N in original
        new_n = int(tc_ids[0].split("-")[1])
        # Compute original max in section 1
        orig_rows = CalamineWorkbook.from_path(str(master_copy)).get_sheet_by_name("Lounge").to_python()
        orig_section_1_tc_ids = [
            int(str(c).split("-")[1])
            for r in orig_rows for c in r
            if isinstance(c, str) and c.startswith("1-") and "-" in c and c.split("-")[1].isdigit()
        ]
        assert new_n == max(orig_section_1_tc_ids) + 1


class TestAppendCollision:
    def test_existing_output_gets_suffix(self, master_copy: Path, append_rows_json: Path,
                                           tmp_path: Path):
        out = tmp_path / "appended.xlsx"
        out.write_text("placeholder")  # pre-existing
        result = subprocess.run(
            [sys.executable, "shared/append_to_master.py",
             "--master", str(master_copy), "--tab", "Lounge",
             "--rows", str(append_rows_json), "--output", str(out)],
            capture_output=True, text=True, check=True,
        )
        actual = result.stdout.strip().splitlines()[-1]
        assert actual != str(out)
        assert Path(actual).exists()


class TestFindSection:
    def test_exact_match(self):
        from shared.append_to_master import _find_section
        sections = [
            {"name": "Async First Entry", "last_tc_id": "1-7"},
            {"name": "Lounge Navigation", "last_tc_id": "2-30"},
        ]
        result = _find_section("Async First Entry", sections)
        assert result is not None
        assert result["name"] == "Async First Entry"

    def test_user_name_is_more_specific_matches(self):
        from shared.append_to_master import _find_section
        sections = [{"name": "Async First Entry", "last_tc_id": "1-7"}]
        # User typed a more specific variant — should match the parent
        result = _find_section("Async First Entry — 신규 추천", sections)
        assert result is not None
        assert result["name"] == "Async First Entry"

    def test_user_name_is_prefix_does_not_match(self):
        """Regression: 'Lounge' should NOT match 'Lounge Navigation'."""
        from shared.append_to_master import _find_section
        sections = [
            {"name": "Lounge Navigation", "last_tc_id": "2-30"},
        ]
        result = _find_section("Lounge", sections)
        assert result is None  # user's name is less specific — treat as new section

    def test_no_match_returns_none(self):
        from shared.append_to_master import _find_section
        sections = [{"name": "Async First Entry", "last_tc_id": "1-7"}]
        assert _find_section("완전히 다른 섹션", sections) is None
