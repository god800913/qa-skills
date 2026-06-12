"""Standardized TC row data model + lightweight validation.

A TC row is a dict with the standard 14 logical column keys + 'section'.
"""
from __future__ import annotations

# Logical column names. These are canonical names matching shared/inspect_master.py
# COLUMN_ALIASES canonical keys.
TC_COLUMN_KEYS = (
    "Priority",            # P1~P4
    "OS",                  # iOS / And / All / "" (blank)
    "Automation Check",    # human-filled; LLM leaves blank
    "Test Item",
    "Automation TC_ID",    # human-filled; LLM leaves blank
    "TC_ID",               # auto-incremented per section
    "Test Summary",
    "Remote Config / Admin",
    "Pre-condition",
    "Test Step",
    "Expected Result",
    "Result",              # human-filled
    "Jira no.",            # human-filled
    "Comment",
    # Optional extras
    "Policy : URL",
    "Policy_page",
)

# Required keys for LLM-generated rows. The rest are optional / human-filled.
REQUIRED_LLM_KEYS = (
    "Priority", "Test Summary", "Pre-condition", "Test Step", "Expected Result"
)

PRIORITY_VALUES = {"P1", "P2", "P3", "P4"}
OS_VALUES = {"iOS", "And", "Android", "All", ""}


def validate_row(row: dict, *, source_label: str = "row") -> list[str]:
    """Return a list of human-readable validation error messages. Empty list = valid.

    Does NOT raise. Caller decides what to do with errors.
    """
    errors: list[str] = []
    for k in REQUIRED_LLM_KEYS:
        v = row.get(k)
        if v is None or (isinstance(v, str) and not v.strip()):
            errors.append(f"{source_label}: missing required '{k}'")
    if (pri := row.get("Priority")) and pri not in PRIORITY_VALUES:
        errors.append(f"{source_label}: invalid Priority '{pri}' (must be P1~P4)")
    if (os_v := row.get("OS")) is not None and os_v not in OS_VALUES:
        errors.append(f"{source_label}: invalid OS '{os_v}' (must be iOS/And/Android/All/blank)")
    return errors
