"""Extract TC rows from an xlsx tab as a JSON list of dicts.

CLI:
    python extract_tc_table.py <xlsx_path> --tab <tab_name>

Output: JSON array. Each item is a row dict keyed by canonical column name.
Skips section headers and blank rows.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from inspect_master import parse_tab_meta  # noqa: E402

from python_calamine import CalamineWorkbook  # noqa: E402


def extract_tc_table(xlsx_path: Path, tab_name: str) -> list[dict]:
    meta = parse_tab_meta(xlsx_path, tab_name)
    columns = meta["columns"]
    header_row_idx = meta["header_row"]

    wb = CalamineWorkbook.from_path(str(xlsx_path))
    raw_rows = wb.get_sheet_by_name(tab_name).to_python()

    out: list[dict] = []
    for idx in range(header_row_idx + 1, len(raw_rows)):
        row = raw_rows[idx]
        if not row or all(c is None or c == "" for c in row):
            continue
        # Skip section headers (Priority cell numeric)
        pri_idx = columns.get("Priority")
        if pri_idx is not None and pri_idx < len(row):
            cell = row[pri_idx]
            if isinstance(cell, (int, float)) and not isinstance(cell, bool):
                continue
        out.append({col: (row[col_idx] if col_idx < len(row) else None)
                    for col, col_idx in columns.items()})
    return out


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("xlsx_path", type=Path)
    parser.add_argument("--tab", type=str, required=True)
    args = parser.parse_args()

    out = extract_tc_table(args.xlsx_path, args.tab)
    print(json.dumps(out, ensure_ascii=False, indent=2, default=str))


if __name__ == "__main__":
    main()
