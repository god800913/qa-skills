"""Tests for shared/master_health.py (qa:master-health 결정론 코어)."""
import json
import subprocess
import sys
from pathlib import Path

from openpyxl import Workbook

from shared.master_health import grade_tab, master_health

HEADER = ["Priority", "OS", "Automation Check", "Test Item",
          "Automation TC_ID", "TC_ID", "Test Summary",
          "Remote Config / Admin", "Pre-condition", "Test Step",
          "Expected Result", "Result", "Jira no.", "Comment"]


def _tc_row(tc_id, summary, *, priority="P1", step="1. 진입 후 동작 확인",
            expected="노출", result="", os="All"):
    return [priority, os, "", "라운지", "", tc_id, summary,
            "", "전제", step, expected, result, "", ""]


def _build(tmp_path: Path, tabs: dict) -> Path:
    """tabs: {tab_name: list_of_rows | "title" marker dict}. 각 값은 시트에 그대로 append."""
    wb = Workbook()
    wb.remove(wb.active)
    for name, rows in tabs.items():
        ws = wb.create_sheet(name)
        for row in rows:
            ws.append(row)
    path = tmp_path / "master.xlsx"
    wb.save(path)
    return path


def _tab(out: dict, name: str) -> dict:
    return next(t for t in out["tc_tabs"] if t["tab"] == name)


class TestGradeTab:
    def test_empty_before_rate(self):
        assert grade_tab(tc_count=0, format_violations=0, intra_dup_count=0) == "empty"
        # tc_count==0이면 defects가 있어도 empty (나눗셈 회피)
        assert grade_tab(tc_count=0, format_violations=3, intra_dup_count=1) == "empty"

    def test_clean_when_no_defects(self):
        assert grade_tab(tc_count=10, format_violations=0, intra_dup_count=0) == "clean"

    def test_minor_at_boundary(self):
        # 10건 중 1건 = 0.1 → minor (경계 포함)
        assert grade_tab(tc_count=10, format_violations=1, intra_dup_count=0) == "minor"

    def test_attention_above_boundary(self):
        # 10건 중 2건 = 0.2 > 0.1 → attention
        assert grade_tab(tc_count=10, format_violations=1, intra_dup_count=1) == "attention"

    def test_single_tc_one_defect_is_attention(self):
        assert grade_tab(tc_count=1, format_violations=1, intra_dup_count=0) == "attention"


class TestTabSelection:
    def test_selects_tc_tab(self, tmp_path):
        out = master_health(_build(tmp_path, {
            "Lounge": [HEADER, _tc_row("1-1", "라운지 진입")],
        }))
        assert [t["tab"] for t in out["tc_tabs"]] == ["Lounge"]
        assert out["tc_tabs"][0]["template"] == "single"

    def test_detects_mutual_template(self, tmp_path):
        mutual_header = ["Priority", "OS", "A", "B", "Test Item", "TC_ID",
                         "Test Summary", "Pre-condition", "Test Reproduce",
                         "Expected Result", "Result", "Jira no.", "Comment"]
        mutual_row = ["P1", "All", "발신", "수신", "매치", "1-1", "매치 성사",
                      "전제", "1. A가 매치", "성사", "", "", ""]
        out = master_health(_build(tmp_path, {"in Match": [mutual_header, mutual_row]}))
        assert _tab(out, "in Match")["template"] == "mutual"

    def test_excludes_tab_without_priority_header(self, tmp_path):
        out = master_health(_build(tmp_path, {
            "Lounge": [HEADER, _tc_row("1-1", "라운지")],
            "Notes": [["메모", "내용"], ["자유", "텍스트"]],
        }))
        assert [t["tab"] for t in out["tc_tabs"]] == ["Lounge"]
        excluded = {e["tab"]: e["reason"] for e in out["non_tc_tabs"]}
        assert "Notes" in excluded
        assert "Priority" in excluded["Notes"]

    def test_excludes_tab_without_tc_id_column(self, tmp_path):
        no_tcid = ["Priority", "OS", "Test Item", "Test Summary",
                   "Pre-condition", "Test Step", "Expected Result"]
        out = master_health(_build(tmp_path, {
            "Lounge": [HEADER, _tc_row("1-1", "라운지")],
            "Dashboard": [no_tcid, ["P1", "All", "집계", "통계", "-", "-", "-"]],
        }))
        excluded = {e["tab"]: e["reason"] for e in out["non_tc_tabs"]}
        assert "TC_ID" in excluded["Dashboard"]

    def test_excludes_summary_tab(self, tmp_path):
        out = master_health(_build(tmp_path, {
            "Summary": [HEADER, _tc_row("1-1", "요약")],
            "Lounge": [HEADER, _tc_row("1-1", "라운지")],
        }))
        excluded = {e["tab"]: e["reason"] for e in out["non_tc_tabs"]}
        assert "Summary" in excluded
        assert [t["tab"] for t in out["tc_tabs"]] == ["Lounge"]

    def test_exclude_argument(self, tmp_path):
        out = master_health(_build(tmp_path, {
            "Lounge": [HEADER, _tc_row("1-1", "라운지")],
            "Shop": [HEADER, _tc_row("1-1", "상점")],
        }), exclude=["Shop"])
        assert [t["tab"] for t in out["tc_tabs"]] == ["Lounge"]
        excluded = {e["tab"]: e["reason"] for e in out["non_tc_tabs"]}
        assert "제외" in excluded["Shop"] or "exclude" in excluded["Shop"].lower()


class TestAggregation:
    def test_counts_format_violations(self, tmp_path):
        # 필수 누락(Expected Result 빈칸) → 위반 1건, OS enum 위반 → 1건
        out = master_health(_build(tmp_path, {
            "Lounge": [HEADER,
                       _tc_row("1-1", "정상"),
                       _tc_row("1-2", "엣지", expected="", os="MacOS")],
        }))
        tab = _tab(out, "Lounge")
        assert tab["tc_count"] == 2
        assert tab["format_violations"] >= 2
        assert tab["grade"] == "attention"

    def test_counts_intra_duplicates(self, tmp_path):
        out = master_health(_build(tmp_path, {
            "Lounge": [HEADER,
                       _tc_row("1-1", "같은 요약"),
                       _tc_row("1-2", "같은 요약")],
        }))
        assert _tab(out, "Lounge")["intra_dup_count"] >= 1

    def test_blank_ratio(self, tmp_path):
        out = master_health(_build(tmp_path, {
            "Lounge": [HEADER,
                       _tc_row("1-1", "실행됨", result="Pass"),
                       _tc_row("1-2", "미실행", result="")],
        }))
        assert _tab(out, "Lounge")["blank_ratio"] == 0.5

    def test_master_summary(self, tmp_path):
        out = master_health(_build(tmp_path, {
            "Lounge": [HEADER, _tc_row("1-1", "라운지")],
            "Shop": [HEADER,
                     _tc_row("1-1", "상점", expected=""),
                     _tc_row("1-2", "상점2", expected="", os="bad")],
            "Notes": [["메모"], ["자유"]],
        }))
        s = out["summary"]
        assert s["total_tabs"] == 3
        assert s["tc_tab_count"] == 2
        assert s["non_tc_tab_count"] == 1
        assert s["total_tcs"] == 3

    def test_cleanup_priority_orders_attention_by_defect_rate(self, tmp_path):
        out = master_health(_build(tmp_path, {
            "Clean": [HEADER, _tc_row("1-1", "정상")],
            "Bad": [HEADER, _tc_row("1-1", "x", expected=""),
                    _tc_row("1-2", "y", expected="", os="bad")],
            "Worse": [HEADER, _tc_row("1-1", "z", expected="", priority="PX",
                                      os="bad")],
        }))
        priority = out["summary"]["cleanup_priority"]
        # attention 등급만, defect_rate 내림차순 — Worse(1건 다수위반)가 Bad보다 앞
        assert priority[0] == "Worse"
        assert "Clean" not in priority


class TestEmptyTcTab:
    def test_empty_tab_graded_empty(self, tmp_path):
        out = master_health(_build(tmp_path, {"Lounge": [HEADER]}))
        tab = _tab(out, "Lounge")
        assert tab["tc_count"] == 0
        assert tab["grade"] == "empty"
        assert tab["blank_ratio"] is None


class TestCli:
    def test_cli_outputs_json(self, tmp_path):
        path = _build(tmp_path, {"Lounge": [HEADER, _tc_row("1-1", "라운지")]})
        result = subprocess.run(
            [sys.executable, "shared/master_health.py", str(path)],
            capture_output=True, text=True, check=True)
        out = json.loads(result.stdout)
        assert out["summary"]["tc_tab_count"] == 1

    def test_cli_exclude_flag(self, tmp_path):
        path = _build(tmp_path, {
            "Lounge": [HEADER, _tc_row("1-1", "라운지")],
            "Shop": [HEADER, _tc_row("1-1", "상점")],
        })
        result = subprocess.run(
            [sys.executable, "shared/master_health.py", str(path),
             "--exclude", "Shop"],
            capture_output=True, text=True, check=True)
        out = json.loads(result.stdout)
        assert [t["tab"] for t in out["tc_tabs"]] == ["Lounge"]
