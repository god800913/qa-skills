# /// script
# requires-python = ">=3.11"
# dependencies = ["openpyxl>=3.1.0", "python-calamine>=0.2.0"]
# ///
"""Deterministic filter for automation-candidate TC rows (qa:automation-candidates step 1).

Classification per row (first match wins):
- `Automation TC_ID` non-blank      → excluded_automated (already automated)
- `Automation Check` == Skip        → excluded_skip
- `Automation Check` ∈ All/iOS/Android (trim, case-insensitive) → candidates
- `Automation Check` blank          → unclassified (needs human triage)
- anything else                     → unknown_check (reported, never guessed)

Prioritization of candidates stays with the LLM — this script only does the
deterministic filtering so it can be tested and never drifts.

CLI:
    python select_automation_candidates.py <xlsx_path> --tab <tab_name>

Output: JSON object with row groups and a counts summary.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from extract_tc_table import extract_tc_table  # noqa: E402

CANDIDATE_CHECKS = {"all", "ios", "android"}
SKIP_CHECK = "skip"


def _norm(value: object) -> str:
    return str(value).strip() if value is not None else ""


def classify_rows(rows: list[dict]) -> dict:
    groups: dict[str, list[dict]] = {
        "candidates": [],
        "excluded_automated": [],
        "excluded_skip": [],
        "unclassified": [],
        "unknown_check": [],
    }
    for row in rows:
        check = _norm(row.get("Automation Check")).lower()
        if _norm(row.get("Automation TC_ID")):
            group = "excluded_automated"
        elif check == SKIP_CHECK:
            group = "excluded_skip"
        elif check in CANDIDATE_CHECKS:
            group = "candidates"
        elif check == "":
            group = "unclassified"
        else:
            group = "unknown_check"
        groups[group].append(dict(row))

    counts = {"total": len(rows), **{name: len(g) for name, g in groups.items()}}
    return {**groups, "counts": counts}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("xlsx_path", type=Path)
    parser.add_argument("--tab", type=str, required=True)
    args = parser.parse_args()

    rows = extract_tc_table(args.xlsx_path, args.tab)
    result = {"tab": args.tab, **classify_rows(rows)}
    print(json.dumps(result, ensure_ascii=False, indent=2, default=str))


if __name__ == "__main__":
    main()
