"""Tests for shared/select_minimal_coverage.py (in-memory rows, no xlsx)."""
import copy

from shared.select_minimal_coverage import select_minimal_coverage


def _row(priority="P3", summary="", os="", steps="step 1", rc=""):
    return {
        "Priority": priority, "OS": os, "Test Item": "", "TC_ID": "",
        "Test Summary": summary, "Remote Config / Admin": rc,
        "Pre-condition": "", "Test Step": steps, "Expected Result": "ok",
        "Comment": "",
    }


def test_force_includes_p1_and_high_risk_cases():
    rows = [
        _row("P1", "메인 진입"),
        _row("P3", "결제 실패 시 복구"),
        _row("P4", "버튼 라벨 확인"),
    ]
    result = select_minimal_coverage(rows)
    selected_idx = {s["index"] for s in result["selected"]}
    assert 0 in selected_idx          # P1 강제 포함
    assert 1 in selected_idx          # 고위험 키워드(결제) 강제 포함
    forced_reasons = [r for s in result["selected"] if s["index"] in (0, 1)
                      for r in s["reasons"]]
    assert any("강제 포함" in r for r in forced_reasons)


def test_prefers_case_with_higher_unique_risk_coverage():
    rows = [
        _row("P2", "설정 진입", os="iOS"),
        _row("P2", "설정 진입 재확인", os="iOS"),   # 동일 태그 → 중복
        _row("P2", "설정 진입", os="And"),          # 새 태그(os:And)
    ]
    result = select_minimal_coverage(rows)
    selected_idx = [s["index"] for s in result["selected"]]
    assert selected_idx[0] == 0 or selected_idx[0] == 2
    assert 1 not in selected_idx      # 중복 태그 행은 선택 안 됨
    assert {0, 2} <= set(selected_idx)


def test_penalizes_redundant_cases():
    rows = [
        _row("P2", "프로필 편집", os="iOS"),
        _row("P2", "프로필 편집 다시", os="iOS"),
    ]
    result = select_minimal_coverage(rows)
    assert len(result["selected"]) == 1
    leftovers = result["next_best"] + result["excluded"]
    assert any(item["index"] == 1 for item in leftovers)


def test_respects_max_cases():
    rows = [_row("P1", f"핵심 플로우 {i}") for i in range(5)]
    result = select_minimal_coverage(rows, max_cases=3)
    assert len(result["selected"]) == 3
    assert any("max-cases" in a for a in result["assumptions"])


def test_returns_next_best_and_excluded_with_reasons():
    rows = [_row("P2", "설정 진입", os="iOS")] + [
        _row("P4", f"라벨 확인 {i}") for i in range(8)
    ]
    result = select_minimal_coverage(rows, next_best_count=2)
    assert len(result["next_best"]) == 2
    assert result["excluded"]
    for e in result["excluded"]:
        assert e["reason"]
        assert "residual_risk" in e


def test_input_rows_not_mutated():
    rows = [_row("P1", "결제 진입"), _row("P3", "라벨")]
    snapshot = copy.deepcopy(rows)
    select_minimal_coverage(rows)
    assert rows == snapshot


def test_forced_overflow_rows_get_distinct_reason():
    rows = [_row("P1", f"결제 핵심 {i}") for i in range(5)]
    result = select_minimal_coverage(rows, max_cases=2, next_best_count=1)
    assert len(result["selected"]) == 2
    selected_idx = {s["index"] for s in result["selected"]}
    leftovers = result["next_best"] + result["excluded"]
    overflow = [item for item in leftovers if item["index"] not in selected_idx]
    assert len(overflow) == 3
    # next_best로 빠진 강제 포함 탈락 행에는 명시적 마커가 있어야 한다
    assert all(n["forced_overflow"] is True for n in result["next_best"])
    # excluded로 빠진 행은 사유에 "강제 포함 대상"이 드러나야 한다
    excluded_reasons = [e["reason"] for e in result["excluded"]]
    assert excluded_reasons
    assert all("강제 포함 대상" in r for r in excluded_reasons)
    # excluded 항목에도 forced_overflow 필드가 있어야 한다 (next_best와 대칭)
    assert all(e["forced_overflow"] is True for e in result["excluded"])
