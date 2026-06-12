# /// script
# requires-python = ">=3.11"
# dependencies = ["openpyxl>=3.1.0", "python-calamine>=0.2.0"]
# ///
"""Find duplicate TCs within a tab and across tabs in the same xlsx file.

CLI:
    python find_duplicates.py <xlsx_path> --tab <tab_name> [--no-cross-tab]

Output JSON:
    {
      "intra_tab": [{"row_a": int, "row_b": int, "field": str, "value": str}, ...],
      "cross_tab": [{"focus_tab": str, "focus_row": int, "focus_tc_id": str,
                     "other_tab": str, "other_row": int, "other_tc_id": str,
                     "field": str, "value": str}, ...]
    }

Detection: exact match on Test Summary OR normalized (whitespace-stripped) Test Step.
Summary tabs are auto-excluded.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

# Sibling
sys.path.insert(0, str(Path(__file__).parent))
from inspect_master import _is_section_header, _is_summary_tab, parse_tab_meta  # noqa: E402

from python_calamine import CalamineWorkbook  # noqa: E402

_WS_RE = re.compile(r"\s+")
_PUNCT_RE = re.compile(r"[·\-_\.,/\\!?\(\)\[\]{}]")

# Minimum normalized length for a Test Step to be considered for cross-tab dup.
# Filters boilerplate prefixes like "1. 진입" (normalized → "1 진입", 4 chars)
# that would otherwise produce floods of false positives across a large master.
_CROSS_TAB_STEP_MIN_LEN = 12


def _normalize(s: str) -> str:
    """Whitespace + punctuation normalization for fuzzy comparison."""
    if s is None:
        return ""
    s = str(s).strip()
    s = _WS_RE.sub(" ", s)
    s = _PUNCT_RE.sub("", s)
    return s.lower()


def _load_tc_rows(xlsx_path: Path, tab_name: str) -> tuple[list[tuple[int, dict]], dict]:
    """Return (list of (excel_row, row_dict), columns dict)."""
    meta = parse_tab_meta(xlsx_path, tab_name)
    columns = meta["columns"]
    header_row_idx = meta["header_row"]

    wb = CalamineWorkbook.from_path(str(xlsx_path))
    raw_rows = wb.get_sheet_by_name(tab_name).to_python()

    out: list[tuple[int, dict]] = []
    for idx in range(header_row_idx + 1, len(raw_rows)):
        row = raw_rows[idx]
        if not row or all(c is None or c == "" for c in row):
            continue
        if _is_section_header(row, columns):
            continue
        rd = {col: row[col_idx] if col_idx < len(row) else None
              for col, col_idx in columns.items()}
        out.append((idx + 1, rd))  # 1-based excel_row
    return out, columns


def _find_intra_tab(rows: list[tuple[int, dict]]) -> list[dict]:
    """Find Test Summary or normalized Test Step duplicates within one tab."""
    by_summary: dict[str, list[tuple[int, str]]] = {}
    by_step: dict[str, list[tuple[int, str]]] = {}

    for excel_row, rd in rows:
        summary = rd.get("Test Summary")
        step = rd.get("Test Step")
        if summary and str(summary).strip():
            key = str(summary).strip()
            by_summary.setdefault(key, []).append((excel_row, key))
        if step:
            key = _normalize(step)
            if key:
                by_step.setdefault(key, []).append((excel_row, str(step).strip()))

    dups: list[dict] = []
    for value, occurrences in by_summary.items():
        if len(occurrences) > 1:
            for i in range(len(occurrences) - 1):
                dups.append({
                    "row_a": occurrences[i][0],
                    "row_b": occurrences[i + 1][0],
                    "field": "Test Summary",
                    "value": value,
                })
    for _, occurrences in by_step.items():
        if len(occurrences) > 1:
            for i in range(len(occurrences) - 1):
                dups.append({
                    "row_a": occurrences[i][0],
                    "row_b": occurrences[i + 1][0],
                    "field": "Test Step (normalized)",
                    "value": occurrences[i][1],
                })
    return dups


def _find_cross_tab(xlsx_path: Path, focus_tab: str,
                    focus_rows: list[tuple[int, dict]]) -> list[dict]:
    """Compare focus tab rows against all other non-Summary tabs."""
    wb = CalamineWorkbook.from_path(str(xlsx_path))
    other_tabs = [t for t in wb.sheet_names
                  if t != focus_tab and not _is_summary_tab(t)]

    # Build lookup of (other_tab, excel_row, tc_id) by normalized values
    other_summaries: dict[str, list[tuple[str, int, str]]] = {}
    other_steps: dict[str, list[tuple[str, int, str]]] = {}

    for ot in other_tabs:
        try:
            other_rows, _ = _load_tc_rows(xlsx_path, ot)
        except Exception:
            continue  # tab without parseable header — skip
        for excel_row, rd in other_rows:
            tc_id = str(rd.get("TC_ID", "")).strip()
            summary = rd.get("Test Summary")
            step = rd.get("Test Step")
            if summary and str(summary).strip():
                other_summaries.setdefault(str(summary).strip(), []).append(
                    (ot, excel_row, tc_id))
            if step:
                key = _normalize(step)
                if key and len(key) >= _CROSS_TAB_STEP_MIN_LEN:
                    other_steps.setdefault(key, []).append((ot, excel_row, tc_id))

    dups: list[dict] = []
    for excel_row, rd in focus_rows:
        focus_tc_id = str(rd.get("TC_ID", "")).strip()
        summary = rd.get("Test Summary")
        step = rd.get("Test Step")
        if summary and str(summary).strip():
            key = str(summary).strip()
            for other in other_summaries.get(key, []):
                dups.append({
                    "focus_tab": focus_tab, "focus_row": excel_row,
                    "focus_tc_id": focus_tc_id,
                    "other_tab": other[0], "other_row": other[1],
                    "other_tc_id": other[2],
                    "field": "Test Summary", "value": key,
                })
        if step:
            key = _normalize(step)
            if key and len(key) >= _CROSS_TAB_STEP_MIN_LEN:
                for other in other_steps.get(key, []):
                    dups.append({
                        "focus_tab": focus_tab, "focus_row": excel_row,
                        "focus_tc_id": focus_tc_id,
                        "other_tab": other[0], "other_row": other[1],
                        "other_tc_id": other[2],
                        "field": "Test Step (normalized)", "value": str(step).strip(),
                    })
    return dups


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("xlsx_path", type=Path)
    parser.add_argument("--tab", type=str, required=True)
    parser.add_argument("--no-cross-tab", action="store_true")
    args = parser.parse_args()

    rows, _ = _load_tc_rows(args.xlsx_path, args.tab)
    intra = _find_intra_tab(rows)
    cross = [] if args.no_cross_tab else _find_cross_tab(args.xlsx_path, args.tab, rows)

    print(json.dumps({"intra_tab": intra, "cross_tab": cross},
                     ensure_ascii=False, indent=2, default=str))


if __name__ == "__main__":
    main()
