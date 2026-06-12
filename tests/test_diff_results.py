"""Tests for shared/diff_results.py (qa:result-diff 결정론 코어)."""
import itertools
import json
import subprocess
import sys
from pathlib import Path

from shared.diff_results import diff_results

CATEGORIES = {"removed_tc", "new_tc", "not_run", "persistent_fail",
              "new_fail", "recovered", "still_pass"}


def _row(tc_id: str, result, summary: str = "요약") -> dict:
    return {"TC_ID": tc_id, "Result": result, "Test Summary": summary,
            "Priority": "P2"}


def _tc(out: dict, tc_id: str) -> dict:
    return next(t for t in out["tcs"] if t["tc_id"] == tc_id)


def _rounds(*histories: dict) -> list[list[dict]]:
    """histories: {tc_id: [round1_result, ...]} — "-"는 해당 회차 미존재."""
    n = len(next(iter(histories[0].values())))
    rounds = []
    for i in range(n):
        rows = []
        for hist in histories:
            for tc_id, values in hist.items():
                if values[i] != "-":
                    rows.append(_row(tc_id, values[i]))
        rounds.append(rows)
    return rounds


class TestCategories:
    def test_two_round_basic_categories(self):
        out = diff_results(_rounds({
            "1-1": ["Pass", "Fail"],     # new_fail
            "1-2": ["Fail", "Block"],    # persistent_fail
            "1-3": ["Block", "Pass"],    # recovered
            "1-4": ["Pass", "Pass"],     # still_pass
        }))
        assert _tc(out, "1-1")["category"] == "new_fail"
        assert _tc(out, "1-2")["category"] == "persistent_fail"
        assert _tc(out, "1-3")["category"] == "recovered"
        assert _tc(out, "1-4")["category"] == "still_pass"

    def test_new_tc_takes_priority_even_if_fail(self):
        out = diff_results(_rounds({"1-1": ["-", "Fail"], "1-2": ["-", "Pass"]}))
        assert _tc(out, "1-1")["category"] == "new_tc"
        assert _tc(out, "1-2")["category"] == "new_tc"

    def test_reappearing_tc_is_not_new_tc(self):
        # 첫 회차에 있었다가 빠지고 재등장 — 직전 유효 결과(Pass) 기준 new_fail
        out = diff_results(_rounds({"1-1": ["Pass", "-", "Fail"]}))
        assert _tc(out, "1-1")["category"] == "new_fail"

    def test_removed_tc(self):
        out = diff_results(_rounds({"1-1": ["Pass", "-"], "1-2": ["Pass", "Pass"]}))
        assert _tc(out, "1-1")["category"] == "removed_tc"

    def test_not_run_last_round(self):
        out = diff_results(_rounds({
            "1-1": ["Pass", "N/T"], "1-2": ["Fail", ""], "1-3": ["Pass", "보류"],
        }))
        assert _tc(out, "1-1")["category"] == "not_run"
        assert _tc(out, "1-2")["category"] == "not_run"
        assert _tc(out, "1-3")["category"] == "not_run"   # unknown 값도 not_run

    def test_prev_effective_skips_non_results(self):
        out = diff_results(_rounds({
            "1-1": ["Fail", "N/T", "Pass"],   # recovered (N/T 건너뜀)
            "1-2": ["Pass", "N/T", "Fail"],   # new_fail
            "1-3": ["Fail", "N/T", "Fail"],   # persistent_fail
            "1-4": ["N/T", "N/T", "Pass"],    # 직전 유효 없음 → still_pass
            "1-5": ["N/T", "N/T", "Fail"],    # 직전 유효 없음 → new_fail
        }))
        assert _tc(out, "1-1")["category"] == "recovered"
        assert _tc(out, "1-2")["category"] == "new_fail"
        assert _tc(out, "1-3")["category"] == "persistent_fail"
        assert _tc(out, "1-4")["category"] == "still_pass"
        assert _tc(out, "1-5")["category"] == "new_fail"

    def test_totality_every_history_gets_exactly_one_category(self):
        """길이 3의 모든 이력 조합이 7분류 중 정확히 하나에 떨어진다."""
        values = ["Pass", "Fail", "Block", "N/T", "N/A", "", "이상값", "-"]
        combos = [c for c in itertools.product(values, repeat=3)
                  if not all(v == "-" for v in c)]
        histories = [{f"T-{i}": list(c)} for i, c in enumerate(combos)]
        out = diff_results(_rounds(*histories))
        assert len(out["tcs"]) == len(combos)
        for tc in out["tcs"]:
            assert tc["category"] in CATEGORIES, tc


class TestFlaky:
    def test_two_transitions_is_flaky(self):
        out = diff_results(_rounds({"1-1": ["Pass", "Fail", "Pass"]}))
        assert _tc(out, "1-1")["flaky"] is True

    def test_long_runs_still_flaky(self):
        out = diff_results(_rounds({"1-1": ["Pass", "Fail", "Fail", "Pass"]}))
        assert _tc(out, "1-1")["flaky"] is True

    def test_single_transition_not_flaky(self):
        out = diff_results(_rounds({"1-1": ["Pass", "Fail"]}))
        assert _tc(out, "1-1")["flaky"] is False

    def test_skips_not_run_when_counting(self):
        out = diff_results(_rounds({"1-1": ["Pass", "N/T", "Fail"]}))
        assert _tc(out, "1-1")["flaky"] is False   # 전환 1회

    def test_flaky_is_orthogonal_to_category(self):
        out = diff_results(_rounds({"1-1": ["Fail", "Pass", "Fail"]}))
        assert _tc(out, "1-1")["category"] == "new_fail"
        assert _tc(out, "1-1")["flaky"] is True


class TestHistoryAndAggregates:
    def test_history_encoding(self):
        out = diff_results(_rounds({"1-1": ["pass", "", "-"]}))
        # 대소문자 정규화 / 미입력 None / 미존재 "-"
        assert _tc(out, "1-1")["history"] == ["Pass", None, "-"]

    def test_unknown_encoded_in_history(self):
        out = diff_results(_rounds({"1-1": ["보류", "Pass"]}))
        assert _tc(out, "1-1")["history"][0] == "unknown"

    def test_pass_rate_trend_excludes_not_run(self):
        out = diff_results(_rounds({
            "1-1": ["Pass", "Pass"], "1-2": ["Fail", "Pass"],
            "1-3": ["N/T", "N/A"],
        }))
        assert out["pass_rates"] == [0.5, 1.0]

    def test_by_category_index(self):
        out = diff_results(_rounds({"1-1": ["Pass", "Fail"]}))
        assert out["by_category"]["new_fail"] == ["1-1"]

    def test_default_labels(self):
        out = diff_results(_rounds({"1-1": ["Pass", "Pass"]}))
        assert out["labels"] == ["회차 1", "회차 2"]


class TestWarnings:
    def test_rows_without_tc_id_counted_and_excluded(self):
        rounds = [[_row("", "Pass"), _row("1-1", "Pass")], [_row("1-1", "Pass")]]
        out = diff_results(rounds)
        assert out["warnings"]["rows_without_tc_id"] == 1
        assert len(out["tcs"]) == 1

    def test_id_reuse_suspect_on_summary_mismatch(self):
        rounds = [[_row("1-1", "Pass", summary="라운지 진입")],
                  [_row("1-1", "Fail", summary="선물함 노출")]]
        out = diff_results(rounds)
        suspects = out["warnings"]["id_reuse_suspect"]
        assert suspects == [{"tc_id": "1-1", "first_summary": "라운지 진입",
                             "last_summary": "선물함 노출"}]

    def test_no_reuse_warning_when_summary_matches_after_trim(self):
        rounds = [[_row("1-1", "Pass", summary="라운지 진입 ")],
                  [_row("1-1", "Fail", summary="라운지 진입")]]
        out = diff_results(rounds)
        assert out["warnings"]["id_reuse_suspect"] == []


class TestCli:
    def _make_xlsx(self, path: Path, tab: str, rows: list[tuple[str, str]]) -> None:
        from openpyxl import Workbook
        wb = Workbook()
        wb.remove(wb.active)
        ws = wb.create_sheet(tab)
        ws.append(["Priority", "OS", "Automation Check", "Test Item",
                   "Automation TC_ID", "TC_ID", "Test Summary",
                   "Remote Config / Admin", "Pre-condition", "Test Step",
                   "Expected Result", "Result", "Jira no.", "Comment"])
        for tc_id, result in rows:
            ws.append(["P1", "All", "", "라운지", "", tc_id, f"요약 {tc_id}",
                       "", "전제", "1. 실행", "노출", result, "", ""])
        wb.save(path)

    def test_cli_two_rounds(self, tmp_path: Path):
        r1, r2 = tmp_path / "r1.xlsx", tmp_path / "r2.xlsx"
        self._make_xlsx(r1, "TabA", [("1-1", "Pass"), ("1-2", "Fail")])
        self._make_xlsx(r2, "TabA", [("1-1", "Fail"), ("1-2", "Pass")])
        result = subprocess.run(
            [sys.executable, "shared/diff_results.py",
             str(r1), "TabA", str(r2), "TabA", "--labels", "v117,v118"],
            capture_output=True, text=True, check=True)
        out = json.loads(result.stdout)
        assert out["labels"] == ["v117", "v118"]
        assert out["by_category"]["new_fail"] == ["1-1"]
        assert out["by_category"]["recovered"] == ["1-2"]

    def test_cli_rejects_odd_arguments(self, tmp_path: Path):
        r1 = tmp_path / "r1.xlsx"
        self._make_xlsx(r1, "TabA", [("1-1", "Pass")])
        result = subprocess.run(
            [sys.executable, "shared/diff_results.py", str(r1), "TabA", str(r1)],
            capture_output=True, text=True)
        assert result.returncode != 0

    def test_cli_requires_two_rounds(self, tmp_path: Path):
        r1 = tmp_path / "r1.xlsx"
        self._make_xlsx(r1, "TabA", [("1-1", "Pass")])
        result = subprocess.run(
            [sys.executable, "shared/diff_results.py", str(r1), "TabA"],
            capture_output=True, text=True)
        assert result.returncode != 0
