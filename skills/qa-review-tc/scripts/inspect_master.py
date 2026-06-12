# /// script
# requires-python = ">=3.11"
# dependencies = ["openpyxl>=3.1.0", "python-calamine>=0.2.0"]
# ///
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
    "Test Summary",
    "Remote Config\n/ Admin", "Remote Config / Admin",
    "Pre-condition", "Pre - condition",
    "Test Step", "Test Reproduce",
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
    # Mutual tabs rename Test Step → Test Reproduce (template-spec §Mutual);
    # canonicalize so validate_format / find_duplicates / select_minimal_coverage
    # all see one key.
    "Test Step": ["Test Step", "Test Reproduce"],
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


TC_ID_PATTERN = re.compile(r"^(\d+)-(\d+)$")


def _is_section_header(row: list, columns: dict[str, int]) -> bool:
    """A row is a section header if Priority cell is numeric (e.g., 1.0) and
    other key data cells (TC_ID, Test Summary) are blank."""
    pri_idx = columns.get("Priority")
    if pri_idx is None or pri_idx >= len(row):
        return False
    cell = row[pri_idx]
    # Numeric-looking section index
    if isinstance(cell, (int, float)):
        return True
    if isinstance(cell, str) and re.match(r"^\d+(\.\d+)?\.?\s+\S", cell):
        # e.g. "1. 라운지 메인" pattern (some sheets use this)
        return True
    return False


_BLANK_SENTINELS = {"-", "—", "–", "_"}


def _section_name(row: list, columns: dict[str, int]) -> str:
    """Pick the most informative non-blank cell as section name. Treats sentinel
    placeholders like '-' as blank."""
    pri_idx = columns.get("Priority")
    for idx, cell in enumerate(row):
        if not cell or idx == pri_idx:
            continue
        s = str(cell).strip()
        if not s or s in _BLANK_SENTINELS:
            continue
        return s
    pri_idx = columns.get("Priority", 0)
    return str(row[pri_idx]).strip() if pri_idx < len(row) else "(unnamed)"


def _extract_tc_id(row: list, columns: dict[str, int]) -> str | None:
    """Return the TC_ID string if present and matching the pattern."""
    idx = columns.get("TC_ID")
    if idx is None or idx >= len(row):
        return None
    cell = row[idx]
    if not cell:
        return None
    s = str(cell).strip()
    if TC_ID_PATTERN.match(s):
        return s
    return None


def _pick_sample_rows(rows: list[list], columns: dict[str, int],
                      header_row_idx: int, n: int = 3) -> list[list]:
    """Pick up to n TC rows (skipping section headers and blank rows) from after the header."""
    samples: list[list] = []
    for idx in range(header_row_idx + 1, len(rows)):
        if len(samples) >= n:
            break
        row = rows[idx]
        if not row or all(c is None or c == "" for c in row):
            continue
        if _is_section_header(row, columns):
            continue
        if _extract_tc_id(row, columns) is None:
            continue  # only TC rows with valid IDs
        samples.append(row)
    return samples


def _parse_sections(rows: list[list], columns: dict[str, int], header_row_idx: int) -> list[dict]:
    """Walk rows after the header, identify section headers and TC rows.

    Returns sections in order, each with name, header_row, last_tc_id.
    """
    sections: list[dict] = []
    current: dict | None = None

    for idx in range(header_row_idx + 1, len(rows)):
        row = rows[idx]
        if not row or all(c is None or c == "" for c in row):
            continue
        if _is_section_header(row, columns):
            if current is not None:
                sections.append(current)
            current = {
                "name": _section_name(row, columns),
                "header_row": idx,
                "last_tc_id": None,
            }
            continue
        # Regular TC row inside current section
        if current is None:
            # Implicit "no section" prefix — start a default section
            current = {"name": "(default)", "header_row": header_row_idx, "last_tc_id": None}
        tc_id = _extract_tc_id(row, columns)
        if tc_id:
            current["last_tc_id"] = tc_id

    if current is not None:
        sections.append(current)
    return sections


def _is_summary_tab(name: str) -> bool:
    return any(p in name for p in SUMMARY_TAB_PATTERNS)


def parse_tab_meta(xlsx_path: Path, tab_name: str) -> dict:
    """Return structural metadata for one tab.

    Output keys: tab, template_type, columns (dict header→index), header_row, sections.
    """
    wb = CalamineWorkbook.from_path(str(xlsx_path))
    rows = wb.get_sheet_by_name(tab_name).to_python()
    try:
        header_row_idx = _find_header_row(rows)
    except ValueError as exc:
        raise ValueError(f"Tab '{tab_name}' in {xlsx_path.name}: {exc}") from exc
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
        "sections": _parse_sections(rows, columns, header_row_idx),
        "sample_rows": _pick_sample_rows(rows, columns, header_row_idx),
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


def main() -> None:
    import argparse
    import json as _json

    parser = argparse.ArgumentParser(description="Inspect a master TC xlsx.")
    parser.add_argument("xlsx_path", type=Path)
    parser.add_argument("--tab", type=str, default=None)
    args = parser.parse_args()

    if args.tab is None:
        out = {"tabs": list_tabs(args.xlsx_path)}
    else:
        out = parse_tab_meta(args.xlsx_path, args.tab)

    print(_json.dumps(out, ensure_ascii=False, indent=2, default=str))


if __name__ == "__main__":
    main()
