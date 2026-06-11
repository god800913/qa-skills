"""Parse and aggregate the Result column of an executed TC workbook.

Result enum (팀 표준 고정): Pass / Fail / Block / N/T / N/A
- 매칭은 대소문자 무시 + 공백 trim ("pass" → "Pass").
- enum 외 비어있지 않은 값은 `unknown`으로 분류하고 원래 값과 함께 보고.
- 빈 Result 셀은 "미입력" (미실행)으로 집계.
- pass_rate = Pass / (Pass + Fail + Block) — N/T·N/A·미입력·unknown은 분모 제외.
- 섹션은 TC_ID의 '-' 앞 접두사로 묶는다 ("3-12" → 섹션 "3").

CLI:
    python parse_results.py <xlsx_path> --tab <tab_name>
Output: JSON aggregate. 입력 행은 절대 변경하지 않는다.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

RESULT_ENUM = ("Pass", "Fail", "Block", "N/T", "N/A")
_CANONICAL = {v.lower(): v for v in RESULT_ENUM}


def normalize_result(value) -> str | None:
    """canonical enum 값, 빈 값이면 None, 그 외는 "unknown"을 반환."""
    text = str(value).strip() if value is not None else ""
    if not text:
        return None
    return _CANONICAL.get(text.lower(), "unknown")


def _section_of(row: dict) -> str:
    tc_id = str(row.get("TC_ID") or "").strip()
    return tc_id.split("-")[0] if "-" in tc_id else "(없음)"


def _empty_bucket() -> dict:
    return {**{v: 0 for v in RESULT_ENUM}, "unknown": 0, "미입력": 0}


def _bucket_add(bucket: dict, key: str | None) -> dict:
    label = "미입력" if key is None else key
    return {**bucket, label: bucket[label] + 1}


def _pass_rate(bucket: dict) -> float | None:
    executed = bucket["Pass"] + bucket["Fail"] + bucket["Block"]
    if executed == 0:
        return None
    return round(bucket["Pass"] / executed, 4)


def parse_results(rows: list[dict]) -> dict:
    """Result 집계. 입력 rows는 변경되지 않는다."""
    total = _empty_bucket()
    by_priority: dict[str, dict] = {}
    by_section: dict[str, dict] = {}
    fails: list[dict] = []
    blocks: list[dict] = []
    unknown: list[dict] = []

    for row in rows:
        norm = normalize_result(row.get("Result"))
        total = _bucket_add(total, norm)

        pri = str(row.get("Priority") or "").strip() or "(없음)"
        by_priority = {**by_priority,
                       pri: _bucket_add(by_priority.get(pri, _empty_bucket()), norm)}
        sec = _section_of(row)
        by_section = {**by_section,
                      sec: _bucket_add(by_section.get(sec, _empty_bucket()), norm)}

        ref = {"tc_id": row.get("TC_ID"), "summary": row.get("Test Summary"),
               "jira": row.get("Jira no.") or ""}
        if norm == "Fail":
            fails = fails + [ref]
        elif norm == "Block":
            blocks = blocks + [ref]
        elif norm == "unknown":
            unknown = unknown + [{**ref, "value": row.get("Result")}]

    return {
        "total": len(rows),
        "counts": total,
        "pass_rate": _pass_rate(total),
        "by_priority": by_priority,
        "by_section": by_section,
        "fails": fails,
        "blocks": blocks,
        "unknown": unknown,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Aggregate the TC Result column.")
    parser.add_argument("xlsx_path", type=Path)
    parser.add_argument("--tab", type=str, required=True)
    args = parser.parse_args()

    from extract_tc_table import extract_tc_table  # noqa: PLC0415
    rows = extract_tc_table(args.xlsx_path, args.tab)
    print(json.dumps(parse_results(rows), ensure_ascii=False, indent=2, default=str))


if __name__ == "__main__":
    main()
