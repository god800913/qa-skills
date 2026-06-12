# /// script
# requires-python = ">=3.11"
# dependencies = ["openpyxl>=3.1.0", "python-calamine>=0.2.0"]
# ///
"""Validate TC rows in an xlsx tab against format rules.

CLI:
    python validate_format.py <xlsx_path> --tab <tab_name>

Output: JSON to stdout with `tab`, `issues` (list), `summary`.

Categories:
- missing_required (missing required field)
- invalid_enum (field value not in allowed set)
- duplicate_tc_id (TC_ID appears more than once)
"""
from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from pathlib import Path

# Sibling import
sys.path.insert(0, str(Path(__file__).parent))
from inspect_master import _is_section_header, parse_tab_meta  # noqa: E402
from tc_row import (  # noqa: E402
    OS_VALUES, PRIORITY_VALUES, REQUIRED_LLM_KEYS,
)

from python_calamine import CalamineWorkbook  # noqa: E402


def _row_to_dict(row: list, columns: dict[str, int]) -> dict:
    """Convert a sheet row (list) to a dict keyed by canonical column name."""
    out = {}
    for col_name, col_idx in columns.items():
        if col_idx < len(row):
            out[col_name] = row[col_idx]
    return out


def validate_format(xlsx_path: Path, tab_name: str) -> dict:
    meta = parse_tab_meta(xlsx_path, tab_name)
    columns = meta["columns"]
    header_row_idx = meta["header_row"]

    wb = CalamineWorkbook.from_path(str(xlsx_path))
    rows = wb.get_sheet_by_name(tab_name).to_python()

    issues: list[dict] = []
    tc_id_seen: list[tuple[int, str]] = []  # (excel_row, tc_id)
    total_tc_rows = 0

    # Iterate TC rows (skip header + section headers + blank rows)
    for idx in range(header_row_idx + 1, len(rows)):
        row = rows[idx]
        excel_row = idx + 1  # 1-based for human readability

        if not row or all(c is None or c == "" for c in row):
            continue
        if _is_section_header(row, columns):
            continue

        total_tc_rows += 1
        rd = _row_to_dict(row, columns)
        tc_id = rd.get("TC_ID", "")

        # missing_required
        for k in REQUIRED_LLM_KEYS:
            v = rd.get(k)
            if v is None or (isinstance(v, str) and not v.strip()):
                issues.append({
                    "row": excel_row,
                    "tc_id": str(tc_id) if tc_id else "",
                    "category": "missing_required",
                    "field": k,
                    "severity": "major",
                    "message": f"{k} is empty",
                })

        # invalid_enum (Priority, OS)
        if (pri := rd.get("Priority")) and pri not in PRIORITY_VALUES:
            issues.append({
                "row": excel_row,
                "tc_id": str(tc_id) if tc_id else "",
                "category": "invalid_enum",
                "field": "Priority",
                "severity": "major",
                "message": f"Invalid Priority '{pri}' (must be P1~P4)",
            })
        if (os_v := rd.get("OS")) is not None and str(os_v).strip() not in OS_VALUES:
            issues.append({
                "row": excel_row,
                "tc_id": str(tc_id) if tc_id else "",
                "category": "invalid_enum",
                "field": "OS",
                "severity": "minor",
                "message": f"Invalid OS '{os_v}' (must be iOS/And/Android/All/blank)",
            })
        # Track for dup detection
        if tc_id and isinstance(tc_id, str) and tc_id.strip():
            tc_id_seen.append((excel_row, tc_id.strip()))

    # duplicate_tc_id
    counts = Counter(tc_id for _, tc_id in tc_id_seen)
    for tc_id, n in counts.items():
        if n > 1:
            rows_with = [r for r, t in tc_id_seen if t == tc_id]
            issues.append({
                "row": rows_with[0],
                "tc_id": tc_id,
                "category": "duplicate_tc_id",
                "severity": "major",
                "message": f"TC_ID {tc_id} appears {n} times (rows {rows_with})",
            })

    return {
        "tab": tab_name,
        "issues": issues,
        "summary": {"total_rows": total_tc_rows, "issue_count": len(issues)},
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Validate TC format in an xlsx tab.")
    parser.add_argument("xlsx_path", type=Path)
    parser.add_argument("--tab", type=str, required=True)
    args = parser.parse_args()

    out = validate_format(args.xlsx_path, args.tab)
    print(json.dumps(out, ensure_ascii=False, indent=2, default=str))


if __name__ == "__main__":
    main()
