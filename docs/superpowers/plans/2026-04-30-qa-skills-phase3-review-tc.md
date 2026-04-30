# QA Skills — Phase 3: qa:review-tc Implementation Plan

> **For agentic workers:** REQUIRED: Use superpowers:subagent-driven-development (if subagents available) or superpowers:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 작성된 TC xlsx를 검수해서 (1) 포맷 위반 (2) 탭 내 일관성 (3) 탭 간 중복 (4) 커버리지 갭 (5) 톤·도메인 이슈를 심각도별 마크다운 리포트로 출력하는 `qa:review-tc` 스킬 출시.

**Architecture:** 3개 보조 Python 스크립트(`validate_format.py`, `find_duplicates.py`, `extract_tc_table.py`)로 결정론적 검사를 처리, LLM은 커버리지·톤 검사 + 리포트 합성 + 패치 결정. SKILL.md 프롬프트가 흐름 조율. 출력은 마크다운 리포트(인라인) + 옵션 `--patch`로 자동 수정 가능 이슈만 새 xlsx 생성.

**Tech Stack:** Python 3.11+, openpyxl, python-calamine, pytest. 동일.

**Spec reference:** `docs/superpowers/specs/2026-04-30-qa-skills-design.md` §4.3, §5.3

---

## File Structure

```
qa-skills/
├── shared/
│   ├── inspect_master.py                        # (existing, sync_shared가 복제)
│   ├── tc_row.py                                # (existing)
│   ├── validate_format.py                        # NEW
│   ├── find_duplicates.py                        # NEW
│   └── extract_tc_table.py                       # NEW
├── tests/
│   ├── test_validate_format.py                   # NEW
│   ├── test_find_duplicates.py                   # NEW
│   ├── test_extract_tc_table.py                  # NEW
│   └── fixtures/
│       └── sample_tc_with_issues.xlsx            # NEW — 의도적 이슈 fixture
├── shared-reference/
│   ├── format-rules.md                           # NEW
│   └── coverage-checklist.md                     # NEW
├── skills/
│   └── qa-review-tc/
│       ├── SKILL.md                              # NEW
│       ├── scripts/
│       │   ├── inspect_master.py                 # NEW (sync 결과)
│       │   ├── validate_format.py                # NEW (sync 결과)
│       │   ├── find_duplicates.py                # NEW (sync 결과)
│       │   └── extract_tc_table.py               # NEW (sync 결과)
│       ├── reference/
│       │   ├── format-rules.md                   # NEW (sync 결과)
│       │   ├── coverage-checklist.md             # NEW (sync 결과)
│       │   └── domain-glossary.md                # NEW (sync 결과)
│       └── examples/
│           └── sample-review-report.md           # NEW
└── scripts/
    └── make_sample_tc_with_issues.py             # NEW — 1회용 fixture 생성기
```

---

## Phase 0: Fixture 만들기

### Task 0.1: `sample_tc_with_issues.xlsx` fixture

**Files:**
- Create: `scripts/make_sample_tc_with_issues.py`
- Create: `tests/fixtures/sample_tc_with_issues.xlsx`

의도적 이슈 (각 카테고리당 1~2개):
- **포맷**: TC_ID 중복 (`1-2`가 두 번), Priority 누락, Expected Result 빈 셀, OS enum 위반 (`MacOS`)
- **탭 내 중복**: 같은 Test Summary가 두 행에 등장
- **탭 간 중복**: TabA 1-3 ↔ TabB 2-1 동일 Test Summary
- **(LLM이 잡는) 커버리지/톤은 fixture 자체로는 검증 어려움 → smoke test로 별도 확인**

- [ ] **Step 1: Write the fixture builder script**

```python
"""One-shot script: build sample_tc_with_issues.xlsx for qa-review-tc tests.

Two tabs: TabA (8 rows with intentional intra-tab issues) + TabB (5 rows with
one cross-tab dup vs TabA).

Run once when setting up Phase 3.
"""
from pathlib import Path

from openpyxl import Workbook

TARGET = Path(__file__).parent.parent / "tests" / "fixtures" / "sample_tc_with_issues.xlsx"
HEADER = [
    "Priority", "OS", "Automation Check", "Test Item", "Automation TC_ID", "TC_ID",
    "Test Summary", "Remote Config / Admin", "Pre-condition", "Test Step",
    "Expected Result", "Result", "Jira no.", "Comment",
]


def main() -> None:
    wb = Workbook()
    wb.remove(wb.active)

    # ---- TabA ----
    a = wb.create_sheet("TabA")
    a.append(HEADER)
    # Section header
    a.append([1.0, "메인 화면", "", "", "", "", "", "", "", "", "", "", "", ""])
    # Valid row
    a.append(["P1", "All", "All", "메인", "", "1-1", "메인 진입",
              "", "신규 사용자", "1. 앱 실행", "메인 화면 노출", "", "", ""])
    # Intra-tab dup of Test Summary
    a.append(["P2", "All", "Skip", "메인", "", "1-2", "메인 진입",
              "", "신규 사용자", "1. 앱 실행 후 진입", "메인 화면 노출", "", "", ""])
    # TC_ID DUPLICATE (intentional — 1-2 repeated)
    a.append(["P3", "All", "Skip", "메인", "", "1-2", "추천 카드 노출",
              "", "신규", "1. 라운지", "추천 노출", "", "", ""])
    # Missing Priority (포맷 위반)
    a.append(["", "All", "Skip", "메인", "", "1-3", "에러 처리",
              "", "오프라인", "1. 진입", "에러 노출", "", "", ""])
    # Empty Expected Result (포맷 위반)
    a.append(["P2", "All", "Skip", "메인", "", "1-4", "딥링크 진입",
              "", "딥링크 클릭", "1. 클릭", "", "", "", ""])
    # OS enum 위반
    a.append(["P3", "MacOS", "Skip", "메인", "", "1-5", "macOS 진입",
              "", "", "1. 실행", "노출", "", "", ""])
    # Cross-tab dup target — same Test Summary as TabB row
    a.append(["P2", "All", "Skip", "정책", "", "1-6", "차단 사용자 제외",
              "", "차단 상태", "1. 라운지 진입", "차단 사용자 비노출", "", "", ""])

    # ---- TabB ----
    b = wb.create_sheet("TabB")
    b.append(HEADER)
    b.append([1.0, "라운지", "", "", "", "", "", "", "", "", "", "", "", ""])
    b.append(["P1", "All", "All", "라운지", "", "1-1", "라운지 진입",
              "", "신규", "1. 라운지", "라운지 노출", "", "", ""])
    b.append(["P3", "All", "Skip", "라운지", "", "1-2", "스크롤 동작",
              "", "카드 2개+", "1. 스와이프", "스크롤 정상", "", "", ""])
    # Cross-tab dup with TabA 1-6
    b.append(["P2", "All", "Skip", "정책", "", "1-3", "차단 사용자 제외",
              "", "차단 상태", "1. 라운지 진입", "차단 사용자 비노출", "", "", ""])
    b.append(["P4", "All", "Skip", "에러", "", "1-4", "네트워크 실패",
              "", "오프라인", "1. 진입", "에러 처리", "", "", ""])

    TARGET.parent.mkdir(parents=True, exist_ok=True)
    wb.save(TARGET)
    print(f"Wrote {TARGET}")


if __name__ == "__main__":
    main()
```

- [ ] **Step 2: Run + verify**

```bash
uv run python scripts/make_sample_tc_with_issues.py
```
Expected: `Wrote .../sample_tc_with_issues.xlsx`.

Verify:
```bash
uv run python -c "
from python_calamine import CalamineWorkbook
wb = CalamineWorkbook.from_path('tests/fixtures/sample_tc_with_issues.xlsx')
print('sheets:', wb.sheet_names)
print('TabA rows:', len(wb.get_sheet_by_name('TabA').to_python()))
print('TabB rows:', len(wb.get_sheet_by_name('TabB').to_python()))
"
```
Expected: 2 sheets, TabA 9 rows, TabB 6 rows.

- [ ] **Step 3: Commit**

```bash
git add scripts/make_sample_tc_with_issues.py tests/fixtures/sample_tc_with_issues.xlsx
git commit -m "test(fixture): add sample_tc_with_issues.xlsx (intentional format/dup issues)"
```

---

## Phase 1: validate_format.py (TDD)

`shared/validate_format.py` — 결정론적 포맷 검사 (필수 컬럼, enum, TC_ID 중복).

### Task 1.1: TDD 골격 + 빈 행 처리

**Files:**
- Create: `tests/test_validate_format.py`
- Create: `shared/validate_format.py`

**Output schema** (JSON, stdout):
```json
{
  "tab": "TabA",
  "issues": [
    {"row": 5, "tc_id": "1-3", "category": "missing_required", "field": "Priority",
     "severity": "major", "message": "Priority is empty"},
    {"row": 4, "tc_id": "1-2", "category": "duplicate_tc_id", "severity": "major",
     "message": "TC_ID 1-2 appears 2 times"}
  ],
  "summary": {"total_rows": 7, "issue_count": 4}
}
```

#### RED commit

Create `tests/test_validate_format.py`:
```python
"""Tests for shared/validate_format.py."""
import json
import subprocess
import sys
from pathlib import Path

import pytest


@pytest.fixture
def issues_xlsx_path(fixtures_dir: Path) -> Path:
    return fixtures_dir / "sample_tc_with_issues.xlsx"


def _run(xlsx: Path, tab: str) -> dict:
    result = subprocess.run(
        [sys.executable, "shared/validate_format.py", str(xlsx), "--tab", tab],
        capture_output=True, text=True, check=True,
    )
    return json.loads(result.stdout)


class TestValidateFormat:
    def test_returns_dict_with_issues_and_summary(self, issues_xlsx_path: Path):
        out = _run(issues_xlsx_path, "TabA")
        assert "issues" in out
        assert "summary" in out
        assert "total_rows" in out["summary"]

    def test_detects_missing_priority(self, issues_xlsx_path: Path):
        out = _run(issues_xlsx_path, "TabA")
        msgs = [i for i in out["issues"]
                if i["category"] == "missing_required" and i["field"] == "Priority"]
        assert len(msgs) == 1, f"Expected 1 missing Priority, got: {msgs}"

    def test_detects_missing_expected_result(self, issues_xlsx_path: Path):
        out = _run(issues_xlsx_path, "TabA")
        msgs = [i for i in out["issues"]
                if i["category"] == "missing_required" and i["field"] == "Expected Result"]
        assert len(msgs) == 1

    def test_detects_invalid_os_enum(self, issues_xlsx_path: Path):
        out = _run(issues_xlsx_path, "TabA")
        msgs = [i for i in out["issues"]
                if i["category"] == "invalid_enum" and i["field"] == "OS"]
        assert len(msgs) == 1
        assert "MacOS" in msgs[0]["message"]

    def test_detects_duplicate_tc_id(self, issues_xlsx_path: Path):
        out = _run(issues_xlsx_path, "TabA")
        msgs = [i for i in out["issues"] if i["category"] == "duplicate_tc_id"]
        # 1-2 appears twice
        assert len(msgs) >= 1
        assert any("1-2" in m["message"] for m in msgs)

    def test_each_issue_has_row_number(self, issues_xlsx_path: Path):
        out = _run(issues_xlsx_path, "TabA")
        for issue in out["issues"]:
            assert "row" in issue
            assert isinstance(issue["row"], int)
            assert issue["row"] > 0
```

Run pytest — expect ALL FAIL (script doesn't exist).

Commit:
```bash
git add tests/test_validate_format.py
git commit -m "test(validate_format): missing required + enum + dup TC_ID (RED)"
```

#### GREEN commit

Create `shared/validate_format.py`:
```python
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
from inspect_master import parse_tab_meta  # noqa: E402
from tc_row import (  # noqa: E402
    AUTOMATION_VALUES, OS_VALUES, PRIORITY_VALUES, REQUIRED_LLM_KEYS,
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
        # Section header detection (Priority cell numeric)
        pri_idx = columns.get("Priority")
        if pri_idx is not None and pri_idx < len(row):
            cell = row[pri_idx]
            if isinstance(cell, (int, float)) and not isinstance(cell, bool):
                continue  # section header

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

        # invalid_enum (Priority, OS, Automation Check)
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
        if (auto := rd.get("Automation Check")) is not None and str(auto).strip() not in AUTOMATION_VALUES:
            issues.append({
                "row": excel_row,
                "tc_id": str(tc_id) if tc_id else "",
                "category": "invalid_enum",
                "field": "Automation Check",
                "severity": "minor",
                "message": f"Invalid Automation Check '{auto}'",
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
```

Run pytest — expect 6 PASS.

Commit:
```bash
git add shared/validate_format.py
git commit -m "feat(validate_format): missing required + enum + dup TC_ID detection"
```

---

## Phase 2: find_duplicates.py (TDD)

`shared/find_duplicates.py` — 탭 내 중복 + 탭 간 중복.

### Task 2.1: TDD intra-tab + cross-tab

#### RED commit

Create `tests/test_find_duplicates.py`:
```python
"""Tests for shared/find_duplicates.py."""
import json
import subprocess
import sys
from pathlib import Path

import pytest


@pytest.fixture
def issues_xlsx_path(fixtures_dir: Path) -> Path:
    return fixtures_dir / "sample_tc_with_issues.xlsx"


def _run(xlsx: Path, tab: str, no_cross: bool = False) -> dict:
    args = [sys.executable, "shared/find_duplicates.py", str(xlsx), "--tab", tab]
    if no_cross:
        args.append("--no-cross-tab")
    result = subprocess.run(args, capture_output=True, text=True, check=True)
    return json.loads(result.stdout)


class TestFindDuplicates:
    def test_returns_intra_and_cross_keys(self, issues_xlsx_path: Path):
        out = _run(issues_xlsx_path, "TabA")
        assert "intra_tab" in out
        assert "cross_tab" in out

    def test_detects_intra_tab_test_summary_dup(self, issues_xlsx_path: Path):
        out = _run(issues_xlsx_path, "TabA")
        # TabA has '메인 진입' on rows 3 and 4 (1-1 and 1-2)
        intra = [d for d in out["intra_tab"] if d["field"] == "Test Summary"
                 and "메인 진입" in d.get("value", "")]
        assert len(intra) >= 1

    def test_detects_cross_tab_test_summary_dup(self, issues_xlsx_path: Path):
        out = _run(issues_xlsx_path, "TabA")
        # TabA 1-6 ↔ TabB 1-3 share '차단 사용자 제외'
        cross = [d for d in out["cross_tab"]
                 if "차단 사용자" in d.get("value", "")]
        assert len(cross) >= 1
        assert all(d["focus_tab"] == "TabA" and d["other_tab"] == "TabB"
                   for d in cross)

    def test_no_cross_flag_disables_cross_scan(self, issues_xlsx_path: Path):
        out = _run(issues_xlsx_path, "TabA", no_cross=True)
        assert out["cross_tab"] == []

    def test_summary_tabs_excluded_from_cross_scan(self, tmp_path: Path):
        # Build a synthetic xlsx with TabA + Summary
        from openpyxl import Workbook
        wb = Workbook()
        wb.remove(wb.active)
        for tab_name in ("TabA", "Summary"):
            ws = wb.create_sheet(tab_name)
            ws.append(["Priority", "OS", "Automation Check", "Test Item",
                       "Automation TC_ID", "TC_ID", "Test Summary",
                       "Remote Config / Admin", "Pre-condition", "Test Step",
                       "Expected Result", "Result", "Jira no.", "Comment"])
            ws.append([1.0, "x", "", "", "", "", "", "", "", "", "", "", "", ""])
            ws.append(["P1", "All", "All", "x", "", "1-1", "공통 텍스트",
                       "", "x", "x", "x", "", "", ""])
        path = tmp_path / "sm.xlsx"
        wb.save(path)
        out = _run(path, "TabA")
        # Summary tab's row should NOT appear in cross_tab
        summary_hits = [d for d in out["cross_tab"] if d["other_tab"] == "Summary"]
        assert summary_hits == []
```

Run pytest — expect ALL FAIL.

Commit:
```bash
git add tests/test_find_duplicates.py
git commit -m "test(find_duplicates): intra-tab + cross-tab + Summary exclusion (RED)"
```

#### GREEN commit

Create `shared/find_duplicates.py`:
```python
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
from inspect_master import _is_summary_tab, parse_tab_meta  # noqa: E402

from python_calamine import CalamineWorkbook  # noqa: E402

_WS_RE = re.compile(r"\s+")
_PUNCT_RE = re.compile(r"[·\-_\.,/\\!?\(\)\[\]{}]")


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
        # Skip section headers
        pri_idx = columns.get("Priority")
        if pri_idx is not None and pri_idx < len(row):
            cell = row[pri_idx]
            if isinstance(cell, (int, float)) and not isinstance(cell, bool):
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
                if key:
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
            if key:
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
```

Run pytest — expect 5 PASS.

Commit:
```bash
git add shared/find_duplicates.py
git commit -m "feat(find_duplicates): intra-tab + cross-tab + Summary exclusion"
```

---

## Phase 3: extract_tc_table.py (TDD)

`shared/extract_tc_table.py` — 헤더 매핑 적용된 TC 행 리스트를 LLM 분석용 JSON으로 평탄화.

### Task 3.1: TDD

#### RED commit

Create `tests/test_extract_tc_table.py`:
```python
"""Tests for shared/extract_tc_table.py."""
import json
import subprocess
import sys
from pathlib import Path

import pytest


@pytest.fixture
def issues_xlsx_path(fixtures_dir: Path) -> Path:
    return fixtures_dir / "sample_tc_with_issues.xlsx"


def _run(xlsx: Path, tab: str) -> list[dict]:
    result = subprocess.run(
        [sys.executable, "shared/extract_tc_table.py", str(xlsx), "--tab", tab],
        capture_output=True, text=True, check=True,
    )
    return json.loads(result.stdout)


class TestExtractTCTable:
    def test_returns_list_of_dicts(self, issues_xlsx_path: Path):
        out = _run(issues_xlsx_path, "TabA")
        assert isinstance(out, list)
        assert all(isinstance(r, dict) for r in out)

    def test_each_row_has_canonical_keys(self, issues_xlsx_path: Path):
        out = _run(issues_xlsx_path, "TabA")
        # All rows should have at least Priority, TC_ID, Test Summary
        for r in out:
            for k in ("Priority", "TC_ID", "Test Summary"):
                assert k in r, f"Missing {k} in {r}"

    def test_skips_section_headers_and_blank_rows(self, issues_xlsx_path: Path):
        out = _run(issues_xlsx_path, "TabA")
        # TabA has 7 TC rows + 1 section header → expect 7 in output
        assert len(out) == 7
```

Commit:
```bash
git add tests/test_extract_tc_table.py
git commit -m "test(extract_tc_table): row dict + section skip (RED)"
```

#### GREEN commit

Create `shared/extract_tc_table.py`:
```python
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
```

Run pytest — expect 3 PASS.

Commit:
```bash
git add shared/extract_tc_table.py
git commit -m "feat(extract_tc_table): row dict extraction (skip section headers)"
```

---

## Phase 4: 스킬 번들 (SKILL.md + reference + sync)

### Task 4.1: shared-reference docs

**Files:**
- Create: `shared-reference/format-rules.md`
- Create: `shared-reference/coverage-checklist.md`

- [ ] **Step 1: Write `shared-reference/format-rules.md`**

```markdown
# 포맷 규칙 (qa:review-tc 카테고리 A)

`validate_format.py`가 자동 검출하는 결정론적 위반 항목.

## 필수 컬럼 (missing_required)
다음 컬럼이 비어있으면 위반:
- Priority
- Test Summary
- Pre-condition
- Test Step
- Expected Result

## Enum 위반 (invalid_enum)

| 컬럼 | 허용 값 |
|---|---|
| Priority | P1, P2, P3, P4 |
| OS | iOS, And, Android, All, "" (공란) |
| Automation Check | All, iOS, Android, Skip, "" (공란) |

## TC_ID 중복 (duplicate_tc_id)
같은 탭 내에서 동일한 TC_ID가 두 번 이상 등장하면 위반.
자동 패치 가능 (`--patch`): 두 번째 이후 ID에 `-dup-N` 접미사 부여.

## 자동 패치 가능 여부

| 카테고리 | 자동 패치 |
|---|---|
| missing_required | 불가 (사람 판단) |
| invalid_enum | 불가 (사람 판단) |
| duplicate_tc_id | 가능 |

## 심각도 매핑
- 필수 컬럼 누락 → Major
- Priority enum 위반 → Major
- OS / Automation Check enum 위반 → Minor
- TC_ID 중복 → Major
```

- [ ] **Step 2: Write `shared-reference/coverage-checklist.md`**

```markdown
# 커버리지·일관성 체크리스트 (qa:review-tc 카테고리 D·E)

LLM이 PRD와 TC를 비교해서 검출하는 항목.

## D. 커버리지 검사 (PRD 제공 시)

PRD를 같이 읽고 다음을 점검:

1. **언급된 기능 X가 TC에 없음** — PRD §N의 기능이 어느 행도 다루지 않음.
2. **Remote Config 한 상태만 테스트** — 플래그 ON 동작만 있고 OFF는 없음 (또는 그 반대).
3. **OS-specific인데 All로 표기** — PRD가 "iOS 전용"이라고 명시했는데 TC OS=All.
4. **mutual 시나리오인데 mutual 템플릿 미사용** — PRD에 양방향 키워드 (`매치`, `메시지`, `콜`, `라이브매치`)가 있는데 TC가 single 템플릿.
5. **네거티브/엣지 빈약** — P1/P2만 잔뜩, P3/P4가 없음. PRD에 에러 케이스가 명시되어 있는데 TC에 없음.

## E. 톤·도메인 검사

기존 시트의 sample_rows를 참고해서:

1. **톤 불일치** — 격식체/구어체 혼용 (예: "확인하시오" vs "확인해").
2. **도메인 용어 오용** — 라운지를 "lounge"로 영문 표기, 매치를 "matching"으로 표기 등.
3. **불필요한 long-form** — Test Step이 5문장 넘게 길어짐 (관찰 가능성 저하).

## 자동 패치 가능 여부
**모두 불가**. 사람 판단 필요. 리포트에 제안만 명시.

## 심각도 매핑
- 핵심 기능 누락 (Coverage 1번) → Major
- Remote Config 양분기 누락 (Coverage 2번) → Major
- OS-specific 불일치 (Coverage 3번) → Major
- mutual 미사용 (Coverage 4번) → Minor (제안)
- 엣지 빈약 (Coverage 5번) → Minor
- 톤 불일치 (Tone 1번) → Minor
- 도메인 오용 (Tone 2번) → Minor
- long-form (Tone 3번) → Info
```

- [ ] **Step 3: Commit**

```bash
git add shared-reference/
git commit -m "docs: add format-rules + coverage-checklist (qa:review-tc reference)"
```

---

### Task 4.2: qa-review-tc skill bundle + sync

**Files:**
- Create: `skills/qa-review-tc/scripts/` + `reference/` + `examples/`
- Create: `skills/qa-review-tc/SKILL.md`
- Create: `skills/qa-review-tc/examples/sample-review-report.md`

- [ ] **Step 1: Create dirs + placeholders for sync**

```bash
mkdir -p skills/qa-review-tc/scripts skills/qa-review-tc/reference skills/qa-review-tc/examples
touch skills/qa-review-tc/scripts/inspect_master.py
touch skills/qa-review-tc/scripts/validate_format.py
touch skills/qa-review-tc/scripts/find_duplicates.py
touch skills/qa-review-tc/scripts/extract_tc_table.py
touch skills/qa-review-tc/reference/format-rules.md
touch skills/qa-review-tc/reference/coverage-checklist.md
touch skills/qa-review-tc/reference/domain-glossary.md
```

- [ ] **Step 2: Run sync**

```bash
uv run python scripts/sync_shared.py
```
Expected: 7 `updated:` lines (4 scripts + 3 reference) + previous unchanged lines.

Verify diffs are clean.

- [ ] **Step 3: Write `skills/qa-review-tc/SKILL.md`**

```markdown
---
name: qa-review-tc
description: 작성된 QA 테스트케이스 xlsx를 검수해서 포맷 위반·탭 내 일관성·탭 간 중복·커버리지 갭·톤 이슈를 심각도별 마크다운 리포트로 출력. 옵션 --patch로 자동 수정 가능 이슈만 새 xlsx 생성. 트리거 — "TC 리뷰", "테스트케이스 검토", "TC 문제점 찾아", "/qa:review-tc".
---

# qa:review-tc

작성된 TC xlsx의 품질을 5개 카테고리로 검수한다:
- A. 포맷 (스크립트, 결정론적)
- B. 탭 내 일관성 (스크립트, 결정론적)
- C. 탭 간 중복 (스크립트, 결정론적)
- D. 커버리지 (LLM, PRD 제공 시)
- E. 톤·도메인 (LLM)

## 입력
- TC xlsx 파일 (Code: 로컬 경로 / Desktop: 업로드)
- `--tab <name>`: 1차 검토 탭 (필수). 미지정 시 전체 탭 목록 보여주고 선택.
- `--prd-url <url>`: PRD 참조 → 카테고리 D 활성화 (옵션)
- `--severity <level>`: blocker|major|minor|all (기본 major)
- `--patch <out.xlsx>`: 자동 수정 가능 이슈만 패치 (포맷 + TC_ID 중복만)
- `--cross-tab-scan` 기본 ON, `--no-cross-tab`로 비활성

## 워크플로우

### 1. 입력 수집
- xlsx 경로 또는 업로드 받기
- 탭 미지정 시 `scripts/inspect_master.py`로 전체 탭 목록 보여주고 사용자 선택 받기
- (옵션) PRD URL 받기 → Notion MCP fetch

### 2. 결정론적 검사 (카테고리 A·B·C)

**카테고리 A — 포맷**:
```bash
uv run python scripts/validate_format.py <xlsx> --tab <name>
```
JSON 결과: 필수 누락, enum 위반, TC_ID 중복.

**카테고리 B·C — 중복**:
```bash
uv run python scripts/find_duplicates.py <xlsx> --tab <name>
```
JSON 결과: 탭 내 (Test Summary/Step 반복) + 탭 간 (다른 탭의 동일 항목).

### 3. LLM 분석 (카테고리 D·E, 옵션)

**TC 데이터 평탄화**:
```bash
uv run python scripts/extract_tc_table.py <xlsx> --tab <name>
```
JSON 행 리스트를 받아서 `reference/coverage-checklist.md`의 항목별로 점검:
- PRD 제공 시 카테고리 D (커버리지)
- 항상 카테고리 E (톤·도메인)

### 4. 리포트 합성
모든 결과를 심각도별로 그룹화한 마크다운:

```markdown
## TC 리뷰 리포트 — <탭 이름>

### 요약
- 총 TC: N
- Blocker: 0 / Major: M / Minor: m / Info: i

### Blocker
1. [카테고리] 행 N (TC_ID X-Y) — 문제 — 수정 제안

### Major
...

### Minor
...

### (선택) 자동 패치 미리보기
다음 이슈는 `--patch` 옵션으로 자동 수정 가능:
- TC_ID 중복 N건 → 두 번째 이후에 -dup-N 접미사
```

### 5. (옵션) 패치 적용
사용자가 "자동 수정해줘" 또는 `--patch <out>` 지정 시:
- 자동 패치 가능 카테고리 (포맷 + TC_ID 중복)만 새 xlsx로 출력
- 원본 xlsx는 절대 수정 안 함
- 커버리지·톤 이슈는 패치 안 함, 리포트에만 남김

### 6. 결과 보고
- 출력 형식: 인라인 마크다운 (또는 `--save <path>` 시 파일)
- 패치 출력 경로 (있는 경우)

## 비목표
- TC 자체 작성 (그건 `qa:generate-tc`)
- PRD 분석 (그건 `qa:prd-clarify`)

## 트러블슈팅
- 검토 대상 탭 없음 → 사용 가능 탭 목록 제공
- PRD 미제공 → 카테고리 D 스킵, 리포트에 명시
- 포맷 위반이 너무 많음 (>30%) → "포맷 먼저 정리하세요" + 위반만 리포트 (LLM 분석 스킵)

## 예시
`examples/sample-review-report.md` 참조.
```

- [ ] **Step 4: Write `skills/qa-review-tc/examples/sample-review-report.md`**

```markdown
# 예시: qa:review-tc 출력

`tests/fixtures/sample_tc_with_issues.xlsx` (TabA 8개 TC 행, 의도적 이슈 포함)를 입력으로 받았을 때 기대되는 리포트.

---

## TC 리뷰 리포트 — TabA

### 요약
- 총 TC: 7
- Blocker: 0 / Major: 5 / Minor: 1

### Major
1. [포맷] 행 6 (TC_ID 1-3) — Priority 비어있음. P1~P4 중 하나로 지정 필요.
2. [포맷] 행 7 (TC_ID 1-4) — Expected Result 비어있음. 관찰 가능한 결과 명시 필요.
3. [포맷] 행 5 (TC_ID 1-2) — TC_ID 1-2가 2회 등장 (rows [4, 5]). 두 번째를 1-3으로 또는 자동 패치 권장.
4. [탭 내 중복] 행 3·4 — Test Summary "메인 진입" 동일. 차별화 필요 (예: "메인 진입 — 신규 가입자").
5. [탭 간 중복] TabA 1-6 ↔ TabB 1-3 — Test Summary "차단 사용자 제외" 동일. 어느 탭이 정본인지 결정 후 다른 쪽 삭제 또는 컨텍스트 차별화.

### Minor
1. [포맷] 행 8 (TC_ID 1-5) — OS 'MacOS'는 허용 enum 아님 (iOS/And/Android/All/공란).

### 자동 패치 가능 항목
다음 1건은 `--patch` 옵션으로 자동 수정 가능:
- TC_ID 1-2 중복 → 두 번째를 1-2-dup-1로 임시 변경 (사람이 최종 ID 부여 권장)

나머지 이슈는 사람 판단 필요.
```

- [ ] **Step 5: Commit**

```bash
git add skills/qa-review-tc/
git commit -m "feat(skill): add qa-review-tc bundle (SKILL.md + 4 scripts + reference + example)"
```

---

### Task 4.3: 통합 smoke test (controller-driven)

- [ ] **Step 1: validate_format smoke**

```bash
uv run python skills/qa-review-tc/scripts/validate_format.py tests/fixtures/sample_tc_with_issues.xlsx --tab TabA
```
육안 확인:
- Priority 누락 1건
- Expected Result 누락 1건
- OS 'MacOS' invalid_enum 1건
- TC_ID 1-2 중복 1건

- [ ] **Step 2: find_duplicates smoke**

```bash
uv run python skills/qa-review-tc/scripts/find_duplicates.py tests/fixtures/sample_tc_with_issues.xlsx --tab TabA
```
육안 확인:
- intra_tab: '메인 진입' Test Summary 1건
- cross_tab: '차단 사용자 제외' TabA→TabB 1건

- [ ] **Step 3: Fresh subagent SKILL.md 시뮬레이션**

Fresh subagent에게 sample_tc_with_issues.xlsx의 TabA를 검토하라고 시키고, 결과 리포트가 sample-review-report.md와 비교했을 때 모든 이슈를 잡았는지 확인.

- [ ] **Step 4: README 업데이트**

`README.md`의 "검증 이력"에 Phase 3 결과 기록.

- [ ] **Step 5: Commit**

```bash
git add README.md
git commit -m "test(qa-review-tc): smoke test (format + dup + fresh subagent) passed"
```

---

## Phase 3 완료 체크리스트

- [ ] `uv run pytest -v` 모든 테스트 PASS (Phase 1·2 30개 + Phase 3 새 테스트들 = 약 44개)
- [ ] `uv run python scripts/sync_shared.py --check` 0 exit
- [ ] `qa-review-tc` 스킬 디스커버 가능
- [ ] sample_tc_with_issues.xlsx 입력으로 4개 카테고리 모두 검출
- [ ] Fresh subagent 시뮬레이션으로 SKILL.md 워크플로우 검증
- [ ] README 업데이트
- [ ] 모든 변경 git commit

---

## Phase 3 의도적 보류 / 후속

1. **`--patch` 자동 수정 구현 보류** — 우선 SKILL.md에 명시 + 리포트에 패치 가능 항목만 표시. 실제 패치 코드는 사용자 피드백 받고 v4에서 추가.
2. **LLM-judge 자동 평가 루프** — 스펙 §8 명시대로 PoC 범위 밖.
3. **임의 마스터 (사용자 본인의 [ver118] 등)에 대한 cross-tab 성능** — 28개 탭 × 평균 100행 = 2800 행. 큰 마스터는 5초 이상 걸릴 수 있음. 필요 시 캐싱/병렬화 후속.
4. **inspect_master.py KNOWN_COLUMNS / COLUMN_ALIASES 구조 정리** — Phase 1 reviewer 권고. v4 candidate.
