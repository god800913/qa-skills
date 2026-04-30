"""Tests for shared/new_workbook.py."""
import json
import subprocess
import sys
from pathlib import Path

import pytest
from python_calamine import CalamineWorkbook


@pytest.fixture
def sample_rows_json(tmp_path: Path) -> Path:
    data = {
        "rows": [
            {
                "section": "1. 라운지 메인",
                "Priority": "P1", "OS": "All", "Automation Check": "All",
                "Test Item": "메인 화면 UI",
                "Test Summary": "라운지 진입 시 추천 카드 노출",
                "Remote Config / Admin": "enableNewLoungeRecommendation: true",
                "Pre-condition": "신규 사용자 로그인",
                "Test Step": "1. 앱 실행\n2. 라운지 탭 진입",
                "Expected Result": "추천 카드 섹션 노출",
                "Comment": "a: 카드 개수 확인\nb: 스크롤 동작 확인",
            },
            {
                "section": "1. 라운지 메인",
                "Priority": "P2", "OS": "All", "Automation Check": "Skip",
                "Test Item": "메인 화면 UI",
                "Test Summary": "추천 데이터 fetch 실패",
                "Pre-condition": "네트워크 연결 차단",
                "Test Step": "1. 앱 실행\n2. 라운지 탭 진입",
                "Expected Result": "fallback UI 노출",
            },
        ]
    }
    p = tmp_path / "rows.json"
    p.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
    return p


class TestNewWorkbook:
    def test_creates_xlsx_with_standard_columns(self, sample_rows_json: Path, tmp_path: Path):
        out = tmp_path / "out.xlsx"
        result = subprocess.run(
            [sys.executable, "shared/new_workbook.py",
             "--rows", str(sample_rows_json), "--output", str(out),
             "--tab-name", "TestTab"],
            capture_output=True, text=True, check=True,
        )
        assert out.exists()
        wb = CalamineWorkbook.from_path(str(out))
        assert wb.sheet_names == ["TestTab"]
        rows = wb.get_sheet_by_name("TestTab").to_python()
        # Header row should contain Priority, TC_ID, etc.
        header_row = next(r for r in rows if "Priority" in r)
        assert "TC_ID" in header_row
        assert "Test Summary" in header_row
        assert "Comment" in header_row

    def test_writes_section_headers_and_tc_rows(self, sample_rows_json: Path, tmp_path: Path):
        out = tmp_path / "out.xlsx"
        subprocess.run(
            [sys.executable, "shared/new_workbook.py",
             "--rows", str(sample_rows_json), "--output", str(out),
             "--tab-name", "TestTab"],
            check=True, capture_output=True, text=True,
        )
        wb = CalamineWorkbook.from_path(str(out))
        rows = wb.get_sheet_by_name("TestTab").to_python()
        # There should be at least one section header row containing "라운지 메인"
        assert any("라운지 메인" in str(c) for r in rows for c in r if c)
        # Two TC rows with TC_IDs auto-assigned 1-1, 1-2
        tc_ids = [str(c) for r in rows for c in r if isinstance(c, str) and c.startswith("1-")]
        assert "1-1" in tc_ids
        assert "1-2" in tc_ids

    def test_collision_appends_suffix(self, sample_rows_json: Path, tmp_path: Path):
        out = tmp_path / "out.xlsx"
        out.write_text("placeholder")  # pre-existing file
        result = subprocess.run(
            [sys.executable, "shared/new_workbook.py",
             "--rows", str(sample_rows_json), "--output", str(out),
             "--tab-name", "TestTab"],
            capture_output=True, text=True, check=True,
        )
        # Output should be out (2).xlsx or similar — script must report the actual path
        # via stdout (last line = path).
        actual_out = result.stdout.strip().splitlines()[-1]
        assert actual_out != str(out)
        assert Path(actual_out).exists()
