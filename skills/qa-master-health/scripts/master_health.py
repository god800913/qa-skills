# /// script
# requires-python = ">=3.11"
# dependencies = ["openpyxl>=3.1.0", "python-calamine>=0.2.0"]
# ///
"""Health-check every TC tab in a master workbook in one pass.

기존 결정론 스크립트(validate_format·find_duplicates·parse_results)를 전 탭에
돌려 탭별 건강 지표와 등급을 집계한다. 신규 검증 로직은 없고 재사용만 한다.
정기 점검·인수인계·대청소 시점에 "어느 탭부터 정리해야 하나"를 판정한다.

탭 선별: Summary 탭 / Priority 헤더 없음 / TC_ID 컬럼 없음은 비-TC 탭으로 제외.
등급: empty(tc_count==0) / clean(위반 0) / minor(위반율 ≤ 0.1) / attention(그 외).

CLI:
    python master_health.py <xlsx_path> [--exclude tab1,tab2]
Output: JSON to stdout. 입력 파일은 절대 변경하지 않는다.
"""
from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from extract_tc_table import extract_tc_table  # noqa: E402
from find_duplicates import _find_intra_tab, _load_tc_rows  # noqa: E402
from inspect_master import list_tabs, parse_tab_meta  # noqa: E402
from parse_results import parse_results  # noqa: E402
from validate_format import validate_format  # noqa: E402

GRADE_MINOR_MAX = 0.1


def grade_tab(*, tc_count: int, format_violations: int,
              intra_dup_count: int) -> str:
    """결정론 등급. empty를 먼저 평가해 0 나눗셈을 피한다."""
    if tc_count == 0:
        return "empty"
    defects = format_violations + intra_dup_count
    if defects == 0:
        return "clean"
    return "minor" if defects / tc_count <= GRADE_MINOR_MAX else "attention"


def _assess_tab(xlsx_path: Path, tab: str, template: str) -> dict:
    fmt = validate_format(xlsx_path, tab)
    format_violations = fmt["summary"]["issue_count"]
    by_category = dict(Counter(i["category"] for i in fmt["issues"]))

    rows, _ = _load_tc_rows(xlsx_path, tab)
    intra_dup_count = len(_find_intra_tab(rows))

    agg = parse_results(extract_tc_table(xlsx_path, tab))
    tc_count = agg["total"]
    blank_ratio = (round(agg["counts"]["미입력"] / tc_count, 4)
                   if tc_count else None)

    return {
        "tab": tab,
        "template": template,
        "tc_count": tc_count,
        "format_violations": format_violations,
        "violations_by_category": by_category,
        "intra_dup_count": intra_dup_count,
        "blank_ratio": blank_ratio,
        "grade": grade_tab(tc_count=tc_count,
                           format_violations=format_violations,
                           intra_dup_count=intra_dup_count),
    }


def _classify(xlsx_path: Path, tab_info: dict,
              exclude: set[str]) -> tuple[str, str | None]:
    """('tc', template) 또는 ('non_tc', reason)."""
    name = tab_info["name"]
    if name in exclude:
        return "non_tc", "사용자 제외(--exclude)"
    if tab_info["is_summary"]:
        return "non_tc", "Summary 탭"
    try:
        meta = parse_tab_meta(xlsx_path, name)
    except ValueError:
        return "non_tc", "Priority 헤더 없음"
    if "TC_ID" not in meta["columns"]:
        return "non_tc", "TC_ID 컬럼 없음"
    return "tc", meta["template_type"]


def master_health(xlsx_path: Path, exclude: list[str] | None = None) -> dict:
    """마스터 전 탭 헬스 집계. 입력 파일은 변경되지 않는다."""
    exclude_set = set(exclude or [])
    tabs = list_tabs(xlsx_path)

    tc_tabs: list[dict] = []
    non_tc_tabs: list[dict] = []
    for tab_info in tabs:
        kind, detail = _classify(xlsx_path, tab_info, exclude_set)
        if kind == "tc":
            tc_tabs.append(_assess_tab(xlsx_path, tab_info["name"], detail))
        else:
            non_tc_tabs.append({"tab": tab_info["name"], "reason": detail})

    grade_counts = dict(Counter(t["grade"] for t in tc_tabs))
    attention = [t for t in tc_tabs if t["grade"] == "attention"]
    attention.sort(
        key=lambda t: (t["format_violations"] + t["intra_dup_count"]) / t["tc_count"],
        reverse=True)

    return {
        "file": xlsx_path.name,
        "tc_tabs": tc_tabs,
        "non_tc_tabs": non_tc_tabs,
        "summary": {
            "total_tabs": len(tabs),
            "tc_tab_count": len(tc_tabs),
            "non_tc_tab_count": len(non_tc_tabs),
            "total_tcs": sum(t["tc_count"] for t in tc_tabs),
            "total_violations": sum(t["format_violations"] for t in tc_tabs),
            "grade_counts": grade_counts,
            "cleanup_priority": [t["tab"] for t in attention],
        },
    }


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Health-check every TC tab in a master workbook.")
    parser.add_argument("xlsx_path", type=Path)
    parser.add_argument("--exclude", type=str, default=None,
                        help="스캔에서 제외할 탭, 쉼표 구분")
    args = parser.parse_args()

    exclude = args.exclude.split(",") if args.exclude else None
    out = master_health(args.xlsx_path, exclude)
    print(json.dumps(out, ensure_ascii=False, indent=2, default=str))


if __name__ == "__main__":
    main()
