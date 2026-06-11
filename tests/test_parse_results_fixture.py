"""Integration: executed fixture → extract → parse_results."""
from pathlib import Path

from shared.extract_tc_table import extract_tc_table
from shared.parse_results import parse_results

FIXTURE = Path(__file__).parent / "fixtures" / "sample_tc_executed.xlsx"


def test_fixture_aggregates_match_known_distribution():
    rows = extract_tc_table(FIXTURE, "TabExec")
    agg = parse_results(rows)
    assert agg["total"] == 10
    assert agg["counts"]["Pass"] == 4
    assert agg["counts"]["Fail"] == 1
    assert agg["counts"]["Block"] == 1
    assert agg["counts"]["N/T"] == 1
    assert agg["counts"]["N/A"] == 1
    assert agg["counts"]["미입력"] == 1
    assert agg["counts"]["unknown"] == 1
    assert agg["fails"][0]["jira"] == "JIRA-2202"
    assert agg["unknown"][0]["value"] == "성공"
