"""One-shot script: extract 2 tabs from the master xlsx into a minimal test fixture.

Run once when setting up the project. Output is committed to tests/fixtures/.
"""
import re
from pathlib import Path

from openpyxl import Workbook
from python_calamine import CalamineWorkbook

SOURCE = Path("/Users/dongjin/Downloads/[ver117] Release QA_Testcase의 사본.xlsx")
TARGET = Path(__file__).parent.parent / "tests" / "fixtures" / "master_v117_minimal.xlsx"
TABS_TO_EXTRACT = ["login", "Lounge"]
MAX_ROWS_PER_TAB = 30  # keep fixtures small

# openpyxl rejects XML-illegal control characters (except tab/LF/CR)
_ILLEGAL_CHARS_RE = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f]")


def _sanitize(value: object) -> object:
    """Strip XML-illegal characters from string values so openpyxl can write them."""
    if isinstance(value, str):
        return _ILLEGAL_CHARS_RE.sub("", value)
    return value


def main() -> None:
    if not SOURCE.exists():
        raise SystemExit(f"Source file not found: {SOURCE}")

    src_wb = CalamineWorkbook.from_path(str(SOURCE))
    out_wb = Workbook()
    # remove default sheet
    out_wb.remove(out_wb.active)

    for tab_name in TABS_TO_EXTRACT:
        rows = src_wb.get_sheet_by_name(tab_name).to_python()
        out_ws = out_wb.create_sheet(tab_name)
        for row in rows[:MAX_ROWS_PER_TAB]:
            # IMPORTANT: do NOT convert "" to None — that would erase the leading-blank-column
            # distinction that login (has it) vs Lounge (doesn't) relies on for §6.1 verification.
            # openpyxl preserves empty strings as empty cells; that's exactly what we want.
            out_ws.append([_sanitize(cell) for cell in row])

    TARGET.parent.mkdir(parents=True, exist_ok=True)
    out_wb.save(TARGET)
    print(f"Wrote {TARGET} with tabs: {TABS_TO_EXTRACT}")


if __name__ == "__main__":
    main()
