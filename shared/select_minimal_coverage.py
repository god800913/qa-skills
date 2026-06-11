"""Select a minimal TC execution set that maximizes risk coverage.

Deterministic scoring over canonical row dicts:

    score = risk_score + coverage_gain - execution_cost - redundancy_penalty

Force-include: Priority == "P1" or any high-risk keyword match.
Input rows are never mutated.

CLI (full pipeline: extract → select → export, requires sibling scripts):
    python select_minimal_coverage.py --source <tc.xlsx> --tab <tab> \
        --output <out.xlsx> [--max-cases N] [--next-best N]
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

PRIORITY_BASE = {"P1": 3.0, "P2": 2.0, "P3": 1.0, "P4": 0.5}

HIGH_RISK_KEYWORDS = (
    "결제", "구매", "환불", "구독", "신고", "차단", "매치", "콜", "라이브",
    "권한", "로그인", "탈퇴", "remote config", "어드민",
)

_TAG_FIELDS = ("Test Summary", "Test Item", "Remote Config / Admin", "Pre-condition")


def _text_of(row: dict) -> str:
    return " ".join(str(row.get(f) or "") for f in _TAG_FIELDS).lower()


def risk_tags(row: dict) -> frozenset[str]:
    text = _text_of(row)
    tags = {kw for kw in HIGH_RISK_KEYWORDS if kw in text}
    os_val = str(row.get("OS") or "").strip()
    if os_val:
        tags.add(f"os:{os_val}")
    if str(row.get("Remote Config / Admin") or "").strip():
        tags.add("remote-config")
    return frozenset(tags)


def risk_score(row: dict) -> float:
    base = PRIORITY_BASE.get(str(row.get("Priority") or "").strip(), 1.0)
    bonus = 1.0 if any(kw in _text_of(row) for kw in HIGH_RISK_KEYWORDS) else 0.0
    return base + bonus


def execution_cost(row: dict) -> float:
    steps = str(row.get("Test Step") or "")
    n_lines = max(1, len([ln for ln in steps.splitlines() if ln.strip()]))
    cost = 0.1 * n_lines
    if str(row.get("Remote Config / Admin") or "").strip():
        cost += 0.5  # 플래그 셋업 부담
    return cost


def is_forced(row: dict) -> bool:
    if str(row.get("Priority") or "").strip() == "P1":
        return True
    return any(kw in _text_of(row) for kw in HIGH_RISK_KEYWORDS)


def _marginal(row: dict, covered: frozenset[str]) -> tuple[float, float]:
    """Returns (score, coverage_gain) against the already-covered tag set."""
    tags = risk_tags(row)
    gain = 0.5 * len(tags - covered)
    overlap = len(tags & covered) / len(tags) if tags else 0.0
    score = risk_score(row) + gain - execution_cost(row) - 1.0 * overlap
    return score, gain


def select_minimal_coverage(rows: list[dict], max_cases: int | None = None,
                            next_best_count: int = 5) -> dict:
    """Greedy risk-coverage selection.

    Returns {"selected", "excluded", "next_best", "assumptions"}; each selected
    item is {"index", "row", "score", "reasons", "new_tags"}.
    """
    assumptions = [
        "score = risk_score + coverage_gain - execution_cost - redundancy_penalty",
        "강제 포함: Priority P1 또는 고위험 키워드 (결제·신고·매치·콜·권한·Remote Config 등)",
    ]
    selected: list[dict] = []
    covered: frozenset[str] = frozenset()

    forced: list[tuple[int, dict]] = []
    remaining: list[tuple[int, dict]] = []
    for idx, row in enumerate(rows):
        (forced if is_forced(row) else remaining).append((idx, row))

    def pick(idx: int, row: dict, reasons: list[str]) -> None:
        nonlocal covered, selected
        score, _gain = _marginal(row, covered)
        new_tags = sorted(risk_tags(row) - covered)
        selected = selected + [{"index": idx, "row": row, "score": round(score, 2),
                                "reasons": reasons, "new_tags": new_tags}]
        covered = covered | risk_tags(row)

    overflow_noted = False
    for idx, row in sorted(forced, key=lambda p: (-risk_score(p[1]), p[0])):
        if max_cases is not None and len(selected) >= max_cases:
            if not overflow_noted:
                assumptions = assumptions + [
                    f"max-cases={max_cases} 제한으로 강제 포함 대상 일부 제외 — 잔여 리스크 확인 필요"]
                overflow_noted = True
            remaining = remaining + [(idx, row)]
            continue
        reason = ("강제 포함: P1" if str(row.get("Priority") or "").strip() == "P1"
                  else "강제 포함: 고위험 키워드")
        pick(idx, row, [reason])

    while remaining and (max_cases is None or len(selected) < max_cases):
        scored = sorted(((idx, row, *_marginal(row, covered)) for idx, row in remaining),
                        key=lambda t: (-t[2], t[0]))
        positive = [t for t in scored if t[3] > 0 and t[2] > 0]
        if not positive:
            break
        idx, row, _score, _gain = positive[0]
        pick(idx, row, [f"커버 확대: 신규 리스크 태그 {len(risk_tags(row) - covered)}개"])
        remaining = [(i, r) for i, r in remaining if i != idx]

    leftovers = sorted(((idx, row, *_marginal(row, covered)) for idx, row in remaining),
                       key=lambda t: (-t[2], t[0]))
    next_best = [{"index": i, "row": r, "score": round(s, 2),
                  "new_tags": sorted(risk_tags(r) - covered)}
                 for i, r, s, _g in leftovers[:next_best_count]]

    excluded = []
    for i, r, _s, _g in leftovers[next_best_count:]:
        tags = risk_tags(r)
        if tags and tags <= covered:
            reason = "선택된 TC가 동일 리스크를 이미 커버 (중복)"
        elif max_cases is not None and len(selected) >= max_cases:
            reason = f"max-cases={max_cases} 도달"
        else:
            reason = "점수 미달 (리스크 대비 실행 비용)"
        excluded.append({"index": i, "row": r, "reason": reason,
                         "residual_risk": sorted(tags - covered)})

    return {"selected": selected, "excluded": excluded,
            "next_best": next_best, "assumptions": assumptions}


def main() -> None:
    parser = argparse.ArgumentParser(description="Select + export minimal coverage set.")
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--tab", type=str, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--max-cases", type=int, default=None)
    parser.add_argument("--next-best", type=int, default=5)
    args = parser.parse_args()

    from export_minimal_coverage import export_minimal_coverage  # noqa: PLC0415
    from extract_tc_table import extract_tc_table  # noqa: PLC0415
    from inspect_master import parse_tab_meta  # noqa: PLC0415

    meta = parse_tab_meta(args.source, args.tab)
    columns = list(meta["columns"].keys())
    rows = extract_tc_table(args.source, args.tab)
    selection = select_minimal_coverage(rows, max_cases=args.max_cases,
                                        next_best_count=args.next_best)
    actual = export_minimal_coverage(selection, columns, args.output)
    print(f"Selected {len(selection['selected'])} / {len(rows)} TC")
    print(actual)


if __name__ == "__main__":
    main()
