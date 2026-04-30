"""Inspect a master TC xlsx and extract structural metadata.

Used by qa-generate-tc (append mode) and qa-review-tc.

CLI:
    python inspect_master.py <xlsx_path> [--tab <tab_name>]

Without --tab: list all tabs (with Summary tabs marked excluded).
With --tab: full metadata for that tab (columns, sections, last TC_IDs, sample rows).

Output: JSON to stdout.
"""
