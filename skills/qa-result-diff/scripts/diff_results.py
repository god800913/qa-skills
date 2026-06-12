# /// script
# requires-python = ">=3.11"
# dependencies = ["openpyxl>=3.1.0", "python-calamine>=0.2.0"]
# ///
"""Compare the Result column across N executed rounds of the same TC tab.

회차 순서대로 받은 (xlsx, tab) 쌍들을 TC_ID 기준으로 매칭해 이력 행렬을 만들고,
마지막 회차 기준으로 상호 배제 7분류 + 직교 flaky 플래그를 부여한다.

이력 원소 인코딩: enum 값("Pass"/"Fail"/"Block"/"N/T"/"N/A") / "unknown" /
None(미입력) / "-"(해당 회차에 TC 미존재).

분류 우선순위 (정확히 하나):
1. removed_tc  — 마지막 회차에 없음
2. new_tc      — 이전 모든 회차에 미존재, 마지막 회차에 처음 등장
3. not_run     — 이번 회차 N/T·N/A·미입력·unknown
4. persistent_fail — 직전 유효 결과 {Fail, Block} → 이번 Fail/Block
5. new_fail    — 직전 유효 결과 Pass 또는 없음 → 이번 Fail/Block
6. recovered   — 직전 유효 결과 {Fail, Block} → 이번 Pass
7. still_pass  — 직전 유효 결과 Pass 또는 없음 → 이번 Pass

"직전 유효 결과" = 마지막 회차 이전 이력에서 N/T·N/A·미입력·unknown·미존재를
건너뛴 마지막 실측값. flaky = 같은 skip 후 {Pass}↔{Fail,Block} 인접 전환 ≥ 2.

CLI:
    python diff_results.py <xlsx1> <tab1> <xlsx2> <tab2> [...] [--labels a,b,...]
Output: JSON to stdout. 입력 파일은 절대 변경하지 않는다.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from parse_results import normalize_result  # noqa: E402

ABSENT = "-"
EFFECTIVE = ("Pass", "Fail", "Block")
FAILING = ("Fail", "Block")


def _prev_effective(history: list) -> str | None:
    """마지막 회차 이전에서 실측값({Pass,Fail,Block})만 역순 탐색."""
    for value in reversed(history[:-1]):
        if value in EFFECTIVE:
            return value
    return None


def _classify(history: list) -> str:
    last = history[-1]
    if last == ABSENT:
        return "removed_tc"
    if all(v == ABSENT for v in history[:-1]):
        return "new_tc"
    if last not in EFFECTIVE:
        return "not_run"
    prev = _prev_effective(history)
    if last in FAILING:
        return "persistent_fail" if prev in FAILING else "new_fail"
    return "recovered" if prev in FAILING else "still_pass"


def _is_flaky(history: list) -> bool:
    effective = ["F" if v in FAILING else "P" for v in history if v in EFFECTIVE]
    transitions = sum(1 for a, b in zip(effective, effective[1:]) if a != b)
    return transitions >= 2


def _pass_rate(rows: list[dict]) -> float | None:
    counts = {"Pass": 0, "Fail": 0, "Block": 0}
    for row in rows:
        norm = normalize_result(row.get("Result"))
        if norm in counts:
            counts[norm] += 1
    executed = sum(counts.values())
    return round(counts["Pass"] / executed, 4) if executed else None


def diff_results(rounds: list[list[dict]],
                 labels: list[str] | None = None) -> dict:
    """회차별 행 리스트들을 비교 집계. 입력 rows는 변경되지 않는다."""
    labels = labels or [f"회차 {i + 1}" for i in range(len(rounds))]

    rows_without_tc_id = 0
    indexed: list[dict[str, dict]] = []  # 회차별 tc_id → row (첫 등장 우선)
    order: list[str] = []                # 전체 TC_ID, 첫 등장 순서
    for rows in rounds:
        by_id: dict[str, dict] = {}
        for row in rows:
            tc_id = str(row.get("TC_ID") or "").strip()
            if not tc_id:
                rows_without_tc_id += 1
                continue
            if tc_id not in by_id:
                by_id[tc_id] = row
            if tc_id not in order:
                order.append(tc_id)
        indexed.append(by_id)

    tcs: list[dict] = []
    by_category: dict[str, list[str]] = {
        c: [] for c in ("new_fail", "persistent_fail", "recovered", "still_pass",
                        "not_run", "new_tc", "removed_tc")}
    id_reuse_suspect: list[dict] = []

    for tc_id in order:
        history = [normalize_result(by_id[tc_id].get("Result"))
                   if tc_id in by_id else ABSENT
                   for by_id in indexed]
        summaries = [str(by_id[tc_id].get("Test Summary") or "").strip()
                     for by_id in indexed if tc_id in by_id]
        present_summaries = [s for s in summaries if s]
        if len(present_summaries) >= 2 and present_summaries[0] != present_summaries[-1]:
            id_reuse_suspect.append({"tc_id": tc_id,
                                     "first_summary": present_summaries[0],
                                     "last_summary": present_summaries[-1]})
        category = _classify(history)
        tcs.append({
            "tc_id": tc_id,
            "summary": present_summaries[-1] if present_summaries else "",
            "history": history,
            "category": category,
            "flaky": _is_flaky(history),
        })
        by_category[category].append(tc_id)

    return {
        "labels": labels,
        "rounds": len(rounds),
        "pass_rates": [_pass_rate(rows) for rows in rounds],
        "tcs": tcs,
        "by_category": by_category,
        "warnings": {
            "rows_without_tc_id": rows_without_tc_id,
            "id_reuse_suspect": id_reuse_suspect,
        },
    }


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Diff TC Results across N executed rounds.")
    parser.add_argument("pairs", nargs="+",
                        help="<xlsx> <tab> 쌍을 회차 순서대로 2개 이상")
    parser.add_argument("--labels", type=str, default=None,
                        help="회차 라벨, 쉼표 구분 (기본: 회차 1..N)")
    args = parser.parse_args()

    if len(args.pairs) % 2 != 0 or len(args.pairs) < 4:
        parser.error("(xlsx, tab) 쌍을 2개 이상 짝수 인자로 주세요")
    labels = args.labels.split(",") if args.labels else None
    n_rounds = len(args.pairs) // 2
    if labels and len(labels) != n_rounds:
        parser.error(f"--labels 개수({len(labels)})가 회차 수({n_rounds})와 다릅니다")

    from extract_tc_table import extract_tc_table  # noqa: PLC0415
    rounds = [extract_tc_table(Path(args.pairs[i * 2]), args.pairs[i * 2 + 1])
              for i in range(n_rounds)]
    print(json.dumps(diff_results(rounds, labels),
                     ensure_ascii=False, indent=2, default=str))


if __name__ == "__main__":
    main()
