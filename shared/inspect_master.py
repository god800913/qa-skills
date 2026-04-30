"""Inspect a master TC xlsx and extract structural metadata.

CLI:
    python inspect_master.py <xlsx_path> [--tab <tab_name>]
"""
from __future__ import annotations

from pathlib import Path

from python_calamine import CalamineWorkbook

SUMMARY_TAB_PATTERNS = ("Summary",)


def _is_summary_tab(name: str) -> bool:
    return any(p in name for p in SUMMARY_TAB_PATTERNS)


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
