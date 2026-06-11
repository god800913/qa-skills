"""Tests for shared/parse_results.py (in-memory rows)."""
import copy

from shared.parse_results import normalize_result, parse_results


def _row(result="", tc_id="1-1", priority="P2", summary="요약", jira=""):
    return {"Priority": priority, "TC_ID": tc_id, "Test Summary": summary,
            "Result": result, "Jira no.": jira}


def test_normalize_variants():
    assert normalize_result("pass") == "Pass"
    assert normalize_result(" FAIL ") == "Fail"
    assert normalize_result("block") == "Block"
    assert normalize_result("n/t") == "N/T"
    assert normalize_result("n/a") == "N/A"
    assert normalize_result("") is None
    assert normalize_result(None) is None
    assert normalize_result("Passed") == "unknown"


def test_counts_and_pass_rate_excludes_nt_na():
    rows = [_row("Pass"), _row("Pass"), _row("Fail"), _row("Block"),
            _row("N/T"), _row("N/A"), _row("")]
    agg = parse_results(rows)
    assert agg["total"] == 7
    assert agg["counts"]["Pass"] == 2
    assert agg["counts"]["미입력"] == 1
    assert agg["pass_rate"] == 0.5          # 2 / (2+1+1) — N/T·N/A·미입력 분모 제외


def test_pass_rate_none_when_nothing_executed():
    agg = parse_results([_row("N/T"), _row("")])
    assert agg["pass_rate"] is None


def test_fails_blocks_carry_tc_id_and_jira():
    rows = [_row("Fail", tc_id="2-1", jira="JIRA-1"), _row("Block", tc_id="2-2")]
    agg = parse_results(rows)
    assert agg["fails"] == [{"tc_id": "2-1", "summary": "요약", "jira": "JIRA-1"}]
    assert agg["blocks"][0]["tc_id"] == "2-2"


def test_unknown_values_reported_with_original():
    agg = parse_results([_row("성공")])
    assert agg["counts"]["unknown"] == 1
    assert agg["unknown"][0]["value"] == "성공"


def test_groups_by_priority_and_section():
    rows = [_row("Pass", tc_id="1-1", priority="P1"),
            _row("Fail", tc_id="1-2", priority="P1"),
            _row("Pass", tc_id="2-1", priority="P3")]
    agg = parse_results(rows)
    assert agg["by_priority"]["P1"]["Fail"] == 1
    assert agg["by_section"]["1"]["Pass"] == 1
    assert agg["by_section"]["2"]["Pass"] == 1


def test_input_not_mutated():
    rows = [_row("Pass"), _row("성공")]
    snap = copy.deepcopy(rows)
    parse_results(rows)
    assert rows == snap
