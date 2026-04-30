"""Inspect a master TC xlsx and extract structural metadata.

CLI:
    python inspect_master.py <xlsx_path> [--tab <tab_name>]
"""
from __future__ import annotations

import re
from pathlib import Path

from python_calamine import CalamineWorkbook

SUMMARY_TAB_PATTERNS = ("Summary",)

# Logical column names we recognize (variants from real master file).
# Whitespace-normalized comparison.
KNOWN_COLUMNS = {
    "Priority", "OS", "Automation Check", "Test Item",
    "Automation\nTC_ID", "Automation TC_ID", "TC_ID",
    "Test Summary", "Test Summary ",
    "Remote Config\n/ Admin", "Remote Config / Admin",
    "Pre-condition", "Pre - condition",
    "Test Step", "Test Reproduce", "Test Item ",
    "Expected Result",
    "Result", "Jira no.", "Comment",
    "Policy : URL", "Policy_page",
    "A", "B",  # mutual template
}

# Canonical name → list of variant strings
COLUMN_ALIASES: dict[str, list[str]] = {
    "Automation TC_ID": ["Automation\nTC_ID", "Automation TC_ID"],
    "Test Summary": ["Test Summary", "Test Summary "],
    "Remote Config / Admin": ["Remote Config\n/ Admin", "Remote Config / Admin"],
    "Pre-condition": ["Pre-condition", "Pre - condition"],
    "Automation Check": ["Automation Check", "Automation\nCheck"],
}


def _canonicalize(header: str) -> str | None:
    """Map a raw header string to its canonical name. Returns None if unknown/blank."""
    if not header or not str(header).strip():
        return None
    s = str(header).strip()
    for canonical, variants in COLUMN_ALIASES.items():
        if s in variants:
            return canonical
    if s in KNOWN_COLUMNS:
        return s
    return None  # unknown column, ignore


def _find_header_row(rows: list[list]) -> int:
    """Find the index of the row that contains the column headers.

    Heuristic: the first row containing 'Priority' (in any cell). Real master sheets
    sometimes have a title row above the header.
    """
    for idx, row in enumerate(rows):
        if any(_canonicalize(cell) == "Priority" for cell in row):
            return idx
    raise ValueError("Could not locate header row (no 'Priority' cell found)")


def _detect_template(columns: dict[str, int]) -> str:
    """single or mutual based on presence of A/B columns."""
    return "mutual" if ("A" in columns and "B" in columns) else "single"


def _is_summary_tab(name: str) -> bool:
    return any(p in name for p in SUMMARY_TAB_PATTERNS)


def parse_tab_meta(xlsx_path: Path, tab_name: str) -> dict:
    """Return structural metadata for one tab.

    Output keys: tab, template_type, columns (dict header→index), header_row.
    """
    wb = CalamineWorkbook.from_path(str(xlsx_path))
    rows = wb.get_sheet_by_name(tab_name).to_python()
    header_row_idx = _find_header_row(rows)
    header_row = rows[header_row_idx]

    columns: dict[str, int] = {}
    for col_idx, cell in enumerate(header_row):
        canonical = _canonicalize(cell)
        if canonical is not None:
            columns[canonical] = col_idx

    return {
        "tab": tab_name,
        "template_type": _detect_template(columns),
        "columns": columns,
        "header_row": header_row_idx,
    }


def list_tabs(xlsx_path: Path) -> list[dict]:
    """Return all tab names with metadata. Summary tabs are marked but not removed."""
    wb = CalamineWorkbook.from_path(str(xlsx_path))
    out: list[dict] = []
    for name in wb.sheet_names:
        rows = wb.get_sheet_by_name(name).to_python()
        col_count = max((len(r) for r in rows), default=0)
        out.append(
            {
                "name": name,
                "is_summary": _is_summary_tab(name),
                "column_count": col_count,
            }
        )
    return out
