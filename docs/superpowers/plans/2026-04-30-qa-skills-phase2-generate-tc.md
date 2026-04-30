# QA Skills — Phase 2: qa:generate-tc Implementation Plan

> **For agentic workers:** REQUIRED: Use superpowers:subagent-driven-development (if subagents available) or superpowers:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** PRD를 입력으로 받아 표준 14컬럼 TC xlsx를 생성하는 `qa:generate-tc` 스킬을 출시. 신규 시트 모드 + 마스터 append 모드 둘 다 지원. Phase 1에서 만든 `inspect_master.py`를 재사용.

**Architecture:** 스킬 번들 `skills/qa-generate-tc/`에 자체 완결적으로 구성 (SKILL.md + scripts + reference + examples). Python 스크립트는 결정론적·테스트 가능: `inspect_master.py`(복제), `new_workbook.py`(신규 워크북), `append_to_master.py`(마스터에 행 삽입, 항상 새 파일 저장). TC 행 데이터는 JSON으로 입출력. 사람 컨펌 루프는 SKILL.md 프롬프트가 담당.

**Tech Stack:** Python 3.11+, openpyxl (write+style), python-calamine (read), pytest. (Phase 1과 동일)

**Spec reference:** `docs/superpowers/specs/2026-04-30-qa-skills-design.md` §5.2

---

## Phase 2 시작 전 결정 사항 (final reviewer 권고)

### 결정 1: shared/ ↔ 스킬 번들 복제 전략

**결정**: **옵션 (a) — `shared/`를 source of truth, `scripts/sync_shared.py`로 자동 복제**.

이유: 스킬 번들은 self-contained여야 하지만 (Anthropic Skills 패키징 요구), 변경 시마다 사람이 동기화하면 copy-rot 발생. 자동 동기화 스크립트 + pre-commit hook으로 실수 방지. 단순한 `shutil.copy2` 기반.

**구현 위치**: 이 플랜의 Task 0 (Phase 2 셋업) 첫 부분.

### 결정 2: `parse_tab_meta`에 `sample_rows` 추가

**결정**: 추가. 스펙 §5.2 명시 사항. 기본 3개 행 (`sample_rows: list[list]`) 반환. `qa-generate-tc`가 LLM 톤·세분도 매칭에 사용.

**구현 위치**: 이 플랜의 Task 1 (inspect_master 보강).

---

## File Structure

이 플랜에서 생성/수정되는 파일:

```
qa-skills/
├── shared/
│   └── inspect_master.py                        # MODIFY — sample_rows 추가
├── scripts/
│   └── sync_shared.py                            # NEW — shared/ → 각 스킬 scripts/ 복제
├── tests/
│   ├── test_inspect_master.py                    # MODIFY — sample_rows 테스트
│   ├── test_new_workbook.py                      # NEW
│   ├── test_append_to_master.py                  # NEW
│   └── fixtures/
│       └── (기존 fixture 재사용)
├── shared-reference/
│   ├── template-spec.md                          # NEW — 14컬럼 의미·작성 규칙
│   └── prioritization-guide.md                   # NEW — P1~P4 판단 기준
├── skills/
│   └── qa-generate-tc/
│       ├── SKILL.md                              # NEW
│       ├── scripts/
│       │   ├── inspect_master.py                 # NEW — sync 결과
│       │   ├── new_workbook.py                   # NEW
│       │   └── append_to_master.py               # NEW
│       ├── reference/
│       │   ├── template-spec.md                  # NEW — sync 결과
│       │   ├── prioritization-guide.md           # NEW — sync 결과
│       │   └── domain-glossary.md                # NEW — sync 결과 (Phase 1에서 만든 거)
│       └── examples/
│           └── sample-tcs.md                     # NEW
└── (.claude/skills 심볼릭 링크는 Phase 1에서 이미 설정됨)
```

원본 마스터 xlsx (`/Users/dongjin/Downloads/[ver117] Release QA_Testcase의 사본.xlsx`)는 통합 smoke test 입력으로만 사용.

---

## Phase 0: 셋업 — sync 스크립트 + sample_rows 추가

### Task 0.1: `scripts/sync_shared.py` — shared → skill scripts 동기화

**Files:**
- Create: `scripts/sync_shared.py`

설계: 모든 `skills/<skill>/scripts/` 디렉토리를 순회하며, `shared/`에 같은 이름의 파일이 있으면 복제. `reference/` 도 마찬가지로 `shared-reference/`에서 복제. 멱등.

- [ ] **Step 1: Write the complete script (final form, integrated)**

Create `scripts/sync_shared.py` with this content as a single complete file. Includes `--check` flag from the start (no mid-task refactor):

```python
"""Sync shared/ and shared-reference/ files into each skill bundle.

Treats shared/ and shared-reference/ as the source of truth. For each
skills/<skill>/scripts/ file that has a same-name counterpart in shared/, this
script overwrites the bundled copy. Same for skills/<skill>/reference/ vs
shared-reference/.

Only overwrites files that ALREADY EXIST in the skill bundle. New files in
shared/ do NOT get auto-added to bundles that haven't opted in (avoids
polluting unrelated skills). To opt a bundle in to a new shared file, create
an empty placeholder of the same name first.

Idempotent. Run before committing, or via pre-commit hook.

Usage:
    python scripts/sync_shared.py               # apply sync, write changes
    python scripts/sync_shared.py --check       # report what would change, exit 1 if drift
"""
from __future__ import annotations

import argparse
import shutil
from pathlib import Path

ROOT = Path(__file__).parent.parent
SHARED_SCRIPTS = ROOT / "shared"
SHARED_REFERENCE = ROOT / "shared-reference"
SKILLS_DIR = ROOT / "skills"


def _sync_dir(source: Path, target: Path, *, check_only: bool) -> list[str]:
    """Copy each source file into target IF target has a same-name file.

    If check_only is True, no files are mutated; would-be changes are reported
    with a "would-update:" prefix.
    """
    actions: list[str] = []
    if not target.exists() or not source.exists():
        return actions
    for src_file in sorted(source.iterdir()):
        if not src_file.is_file() or src_file.name == "__init__.py":
            continue
        dst_file = target / src_file.name
        if not dst_file.exists():
            continue
        if dst_file.read_bytes() == src_file.read_bytes():
            actions.append(f"unchanged: {dst_file.relative_to(ROOT)}")
            continue
        if check_only:
            actions.append(f"would-update: {dst_file.relative_to(ROOT)}")
        else:
            shutil.copy2(src_file, dst_file)
            actions.append(f"updated: {dst_file.relative_to(ROOT)}")
    return actions


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--check", action="store_true",
        help="Report what would change without writing. Exit 1 if any drift.",
    )
    args = parser.parse_args()

    if not SKILLS_DIR.exists():
        raise SystemExit(f"No skills dir: {SKILLS_DIR}")

    actions: list[str] = []
    for skill_dir in sorted(SKILLS_DIR.iterdir()):
        if not skill_dir.is_dir():
            continue
        actions.extend(_sync_dir(SHARED_SCRIPTS, skill_dir / "scripts", check_only=args.check))
        actions.extend(_sync_dir(SHARED_REFERENCE, skill_dir / "reference", check_only=args.check))

    if not actions:
        print("Nothing to sync.")
        return

    for line in actions:
        print(line)

    if args.check and any(a.startswith("would-update:") for a in actions):
        raise SystemExit(1)


if __name__ == "__main__":
    main()
```

- [ ] **Step 2: Smoke test (no-arg)**

```bash
uv run python scripts/sync_shared.py
```
Expected: 2 `unchanged:` lines for `skills/qa-prd-clarify/reference/{domain-glossary,ambiguity-checklist}.md` (because those were manually copied identically in Phase 1). No `updated:` lines.

If you see `updated:`, Phase 1's manual copy drifted from shared-reference. Investigate (probably a trailing newline difference) before committing.

- [ ] **Step 3: --check exits 0 when in sync**

```bash
uv run python scripts/sync_shared.py --check
echo "exit: $?"
```
Expected: 2 `unchanged:` lines (or whatever Step 2 showed) + `exit: 0`.

- [ ] **Step 4: Commit**

```bash
git add scripts/sync_shared.py
git commit -m "chore: add sync_shared.py (shared/ → skill bundles)"
```

---

### Task 0.2: TDD — `parse_tab_meta` returns `sample_rows`

**Files:**
- Modify: `tests/test_inspect_master.py`
- Modify: `shared/inspect_master.py`

#### Step 1 (RED): write failing test

Append to `tests/test_inspect_master.py`:

```python
class TestParseTabMetaSampleRows:
    def test_returns_sample_rows(self, minimal_master_path: Path):
        meta = parse_tab_meta(minimal_master_path, "Lounge")
        assert "sample_rows" in meta
        assert isinstance(meta["sample_rows"], list)
        # By default 3 rows
        assert 1 <= len(meta["sample_rows"]) <= 3

    def test_sample_rows_are_tc_rows_not_section_headers(self, minimal_master_path: Path):
        meta = parse_tab_meta(minimal_master_path, "Lounge")
        # Each sample row should have a TC_ID matching the pattern
        for row in meta["sample_rows"]:
            tc_id_idx = meta["columns"].get("TC_ID")
            assert tc_id_idx is not None
            tc_id = str(row[tc_id_idx]) if tc_id_idx < len(row) else ""
            assert "-" in tc_id, f"Sample row TC_ID looks wrong: {tc_id}"
```

Run `uv run pytest tests/test_inspect_master.py::TestParseTabMetaSampleRows -v` — expect FAIL (KeyError or similar).

Commit:
```bash
git add tests/test_inspect_master.py
git commit -m "test(inspect_master): parse_tab_meta returns sample_rows (RED)"
```

#### Step 2 (GREEN): implement

In `shared/inspect_master.py`, add helper:

```python
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
```

Modify `parse_tab_meta` return:

```python
    return {
        "tab": tab_name,
        "template_type": _detect_template(columns),
        "columns": columns,
        "header_row": header_row_idx,
        "sections": _parse_sections(rows, columns, header_row_idx),
        "sample_rows": _pick_sample_rows(rows, columns, header_row_idx),
    }
```

Run `uv run pytest tests/test_inspect_master.py::TestParseTabMetaSampleRows -v` — expect PASS.

Commit:
```bash
git add shared/inspect_master.py
git commit -m "feat(inspect_master): parse_tab_meta returns sample_rows (TC rows only)"
```

#### Step 3: Update CLI test if it asserts return shape

Quick check: the existing `TestCLI::test_with_tab_returns_meta` only asserts `tab`, `columns`, `sections` keys. It will keep passing. No change needed.

#### Step 4: Run full test suite

```bash
uv run pytest -v
```
Expected: 13 tests pass (previous 11 + 2 new). Coverage still ≥80%.

If coverage dropped: add a quick test for the `_pick_sample_rows` early-break case.

---

## Phase 1: TC 행 데이터 모델 + new_workbook.py (TDD)

가장 단순한 출력 모드부터 — 신규 워크북.

### Task 1.1: Define `rows.json` schema (in code, not external schema file)

**Files:**
- Create: `shared/tc_row.py` (data model + validation)

행 데이터를 dict로 다루되, 검증 함수 + 표준 컬럼 enum을 한 곳에 모아둠.

- [ ] **Step 1: Write the module**

```python
"""Standardized TC row data model + lightweight validation.

A TC row is a dict with the standard 14 logical column keys + 'section'.
"""
from __future__ import annotations

# Logical column names. These are canonical names matching shared/inspect_master.py
# COLUMN_ALIASES canonical keys.
TC_COLUMN_KEYS = (
    "Priority",            # P1~P4
    "OS",                  # iOS / And / All / "" (blank)
    "Automation Check",    # All / iOS / Android / Skip / "" (blank)
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
AUTOMATION_VALUES = {"All", "iOS", "Android", "Skip", ""}


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
    if (auto := row.get("Automation Check")) is not None and auto not in AUTOMATION_VALUES:
        errors.append(f"{source_label}: invalid Automation Check '{auto}'")
    return errors
```

- [ ] **Step 2: Write tests**

Create `tests/test_tc_row.py`:

```python
"""Tests for shared/tc_row.py."""
import pytest

from shared.tc_row import validate_row


class TestValidateRow:
    def test_valid_row_no_errors(self):
        row = {
            "Priority": "P1",
            "OS": "All",
            "Automation Check": "All",
            "Test Summary": "라운지 진입",
            "Pre-condition": "...",
            "Test Step": "1. 앱 실행",
            "Expected Result": "라운지 노출",
        }
        assert validate_row(row) == []

    def test_missing_required_key(self):
        row = {"Priority": "P1"}
        errors = validate_row(row, source_label="row 5")
        # Should report missing Test Summary, Pre-condition, Test Step, Expected Result
        assert any("Test Summary" in e for e in errors)
        assert any("Pre-condition" in e for e in errors)
        assert all("row 5" in e for e in errors)

    def test_invalid_priority(self):
        row = {
            "Priority": "PX",
            "Test Summary": "x", "Pre-condition": "x",
            "Test Step": "x", "Expected Result": "x",
        }
        errors = validate_row(row)
        assert any("Priority" in e for e in errors)

    def test_blank_os_is_valid(self):
        row = {
            "Priority": "P1", "OS": "",
            "Test Summary": "x", "Pre-condition": "x",
            "Test Step": "x", "Expected Result": "x",
        }
        assert validate_row(row) == []
```

- [ ] **Step 3: Verify TDD (RED → GREEN order)**

Actually — since both files are being created here, RED requires committing test file first then impl. Let me restructure:

Sub-step 3a (RED): create only `tests/test_tc_row.py`. Run `uv run pytest tests/test_tc_row.py -v` — expect ImportError. Commit:
```
git add tests/test_tc_row.py
git commit -m "test(tc_row): validate_row schema (RED)"
```

Sub-step 3b (GREEN): create `shared/tc_row.py`. Run pytest — expect 4 PASS. Commit:
```
git add shared/tc_row.py
git commit -m "feat(tc_row): standard column keys + validate_row"
```

---

### Task 1.2: TDD — `new_workbook.py` happy path

**Files:**
- Create: `tests/test_new_workbook.py`
- Create: `shared/new_workbook.py`

#### Step 1 (RED): write the test

```python
"""Tests for shared/new_workbook.py."""
import json
import subprocess
import sys
from pathlib import Path

import pytest
from python_calamine import CalamineWorkbook


@pytest.fixture
def sample_rows_json(tmp_path: Path) -> Path:
    data = {
        "rows": [
            {
                "section": "1. 라운지 메인",
                "Priority": "P1", "OS": "All", "Automation Check": "All",
                "Test Item": "메인 화면 UI",
                "Test Summary": "라운지 진입 시 추천 카드 노출",
                "Remote Config / Admin": "enableNewLoungeRecommendation: true",
                "Pre-condition": "신규 사용자 로그인",
                "Test Step": "1. 앱 실행\n2. 라운지 탭 진입",
                "Expected Result": "추천 카드 섹션 노출",
                "Comment": "a: 카드 개수 확인\nb: 스크롤 동작 확인",
            },
            {
                "section": "1. 라운지 메인",
                "Priority": "P2", "OS": "All", "Automation Check": "Skip",
                "Test Item": "메인 화면 UI",
                "Test Summary": "추천 데이터 fetch 실패",
                "Pre-condition": "네트워크 연결 차단",
                "Test Step": "1. 앱 실행\n2. 라운지 탭 진입",
                "Expected Result": "fallback UI 노출",
            },
        ]
    }
    p = tmp_path / "rows.json"
    p.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
    return p


class TestNewWorkbook:
    def test_creates_xlsx_with_standard_columns(self, sample_rows_json: Path, tmp_path: Path):
        out = tmp_path / "out.xlsx"
        result = subprocess.run(
            [sys.executable, "shared/new_workbook.py",
             "--rows", str(sample_rows_json), "--output", str(out),
             "--tab-name", "TestTab"],
            capture_output=True, text=True, check=True,
        )
        assert out.exists()
        wb = CalamineWorkbook.from_path(str(out))
        assert wb.sheet_names == ["TestTab"]
        rows = wb.get_sheet_by_name("TestTab").to_python()
        # Header row should contain Priority, TC_ID, etc.
        header_row = next(r for r in rows if "Priority" in r)
        assert "TC_ID" in header_row
        assert "Test Summary" in header_row
        assert "Comment" in header_row

    def test_writes_section_headers_and_tc_rows(self, sample_rows_json: Path, tmp_path: Path):
        out = tmp_path / "out.xlsx"
        subprocess.run(
            [sys.executable, "shared/new_workbook.py",
             "--rows", str(sample_rows_json), "--output", str(out),
             "--tab-name", "TestTab"],
            check=True, capture_output=True, text=True,
        )
        wb = CalamineWorkbook.from_path(str(out))
        rows = wb.get_sheet_by_name("TestTab").to_python()
        # There should be at least one section header row containing "라운지 메인"
        assert any("라운지 메인" in str(c) for r in rows for c in r if c)
        # Two TC rows with TC_IDs auto-assigned 1-1, 1-2
        tc_ids = [str(c) for r in rows for c in r if isinstance(c, str) and c.startswith("1-")]
        assert "1-1" in tc_ids
        assert "1-2" in tc_ids

    def test_collision_appends_suffix(self, sample_rows_json: Path, tmp_path: Path):
        out = tmp_path / "out.xlsx"
        out.write_text("placeholder")  # pre-existing file
        result = subprocess.run(
            [sys.executable, "shared/new_workbook.py",
             "--rows", str(sample_rows_json), "--output", str(out),
             "--tab-name", "TestTab"],
            capture_output=True, text=True, check=True,
        )
        # Output should be out (2).xlsx or similar — script must report the actual path
        # via stdout (last line = path).
        actual_out = result.stdout.strip().splitlines()[-1]
        assert actual_out != str(out)
        assert Path(actual_out).exists()
```

Run `uv run pytest tests/test_new_workbook.py -v` — expect ALL FAIL (script doesn't exist).

Commit:
```bash
git add tests/test_new_workbook.py
git commit -m "test(new_workbook): xlsx creation + section headers + collision (RED)"
```

#### Step 2 (GREEN): implement `shared/new_workbook.py`

```python
"""Create a new TC workbook from a rows JSON.

Usage:
    python new_workbook.py --rows rows.json --output out.xlsx \
        --tab-name "Lounge 신규" [--template single|mutual]

rows.json schema:
    {"rows": [{"section": "1. 라운지 메인", "Priority": "P1", ...}, ...]}

Each row's "section" field groups it. TC_IDs are auto-assigned per section
starting at <section_idx>-1.

If output path already exists, appends "(2)", "(3)", ... suffix.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

from openpyxl import Workbook
from openpyxl.styles import Alignment, Font, PatternFill

# Standard column order for the output sheet (single template).
SINGLE_COLUMNS = (
    "Priority", "OS", "Automation Check", "Test Item",
    "Automation TC_ID", "TC_ID", "Test Summary",
    "Remote Config / Admin", "Pre-condition", "Test Step", "Expected Result",
    "Result", "Jira no.", "Comment",
)

MUTUAL_EXTRA_COLUMNS = ("A", "B")

HEADER_FONT = Font(bold=True)
HEADER_FILL = PatternFill(start_color="DDDDDD", end_color="DDDDDD", fill_type="solid")
WRAP = Alignment(wrap_text=True, vertical="top")
SECTION_FONT = Font(bold=True)
SECTION_FILL = PatternFill(start_color="FFFFCC", end_color="FFFFCC", fill_type="solid")


def _resolve_output_path(path: Path) -> Path:
    """If path exists, append (2), (3), ... before suffix."""
    if not path.exists():
        return path
    stem = path.stem
    suffix = path.suffix
    parent = path.parent
    n = 2
    while True:
        candidate = parent / f"{stem} ({n}){suffix}"
        if not candidate.exists():
            return candidate
        n += 1


def _section_index(name: str) -> int:
    """Extract leading numeric section index from name like '1. 라운지 메인' → 1.
    Returns sequential index (1, 2, 3, ...) based on first-seen order if not parseable."""
    m = re.match(r"^(\d+)", name)
    if m:
        return int(m.group(1))
    return 0  # caller handles fallback


def _columns_for(template: str) -> tuple[str, ...]:
    if template == "mutual":
        # Insert A/B before Result.
        # KNOWN GAP (Phase 2 PoC): spec §6.2 also requires renaming "Test Step" → "Test Reproduce"
        # for mutual templates. Not implemented here — mutual append on a real `in Match`-style tab
        # would currently write blank Test Reproduce cells because row_data uses "Test Step" key.
        # Fix in a follow-up: either add a TEMPLATE_COLUMN_RENAMES map or have callers normalize keys.
        idx = SINGLE_COLUMNS.index("Result")
        return SINGLE_COLUMNS[:idx] + MUTUAL_EXTRA_COLUMNS + SINGLE_COLUMNS[idx:]
    return SINGLE_COLUMNS


def write_workbook(rows: list[dict], tab_name: str, output: Path,
                   template: str = "single") -> Path:
    """Create a new xlsx with one tab. Returns the actual path written
    (may differ from `output` due to collision suffix)."""
    actual_output = _resolve_output_path(output)
    columns = _columns_for(template)

    wb = Workbook()
    wb.remove(wb.active)
    ws = wb.create_sheet(tab_name)

    # Header row
    for col_idx, col_name in enumerate(columns, start=1):
        cell = ws.cell(row=1, column=col_idx, value=col_name)
        cell.font = HEADER_FONT
        cell.fill = HEADER_FILL
        cell.alignment = WRAP

    # Group rows by section, preserving first-seen order
    sections: dict[str, list[dict]] = {}
    for r in rows:
        s = r.get("section") or "(default)"
        sections.setdefault(s, []).append(r)

    excel_row = 2
    for section_idx, (section_name, section_rows) in enumerate(sections.items(), start=1):
        # Section header row — write the index in Priority column, name in Test Item col
        sec_pri_cell = ws.cell(row=excel_row, column=columns.index("Priority") + 1,
                               value=float(section_idx))
        sec_pri_cell.font = SECTION_FONT
        sec_pri_cell.fill = SECTION_FILL
        sec_name_cell = ws.cell(row=excel_row, column=columns.index("Test Item") + 1,
                                value=section_name)
        sec_name_cell.font = SECTION_FONT
        sec_name_cell.fill = SECTION_FILL
        excel_row += 1

        # TC rows
        for tc_seq, row_data in enumerate(section_rows, start=1):
            tc_id = f"{section_idx}-{tc_seq}"
            for col_idx, col_name in enumerate(columns, start=1):
                if col_name == "TC_ID":
                    value = tc_id
                else:
                    value = row_data.get(col_name, "")
                cell = ws.cell(row=excel_row, column=col_idx, value=value)
                cell.alignment = WRAP
            excel_row += 1

    actual_output.parent.mkdir(parents=True, exist_ok=True)
    wb.save(actual_output)
    return actual_output


def main() -> None:
    parser = argparse.ArgumentParser(description="Create a new TC workbook.")
    parser.add_argument("--rows", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--tab-name", type=str, default="Sheet1")
    parser.add_argument("--template", choices=["single", "mutual"], default="single")
    args = parser.parse_args()

    data = json.loads(args.rows.read_text(encoding="utf-8"))
    rows = data.get("rows", [])
    actual = write_workbook(rows, args.tab_name, args.output, template=args.template)
    print(f"Wrote {actual}")
    print(actual)


if __name__ == "__main__":
    main()
```

Run `uv run pytest tests/test_new_workbook.py -v` — expect 3 PASS.

If subprocess test fails because `shared.new_workbook` can't be imported as script: try `uv run python shared/new_workbook.py --rows ...` directly to see the error and adjust.

Commit:
```bash
git add shared/new_workbook.py
git commit -m "feat(new_workbook): create xlsx from rows.json (single template)"
```

---

### Task 1.3: TDD — `new_workbook.py` mutual template

#### Step 1 (RED): test mutual columns inserted

Append to `tests/test_new_workbook.py`:

```python
class TestNewWorkbookMutual:
    def test_mutual_template_has_a_and_b_columns(self, sample_rows_json: Path, tmp_path: Path):
        out = tmp_path / "out.xlsx"
        subprocess.run(
            [sys.executable, "shared/new_workbook.py",
             "--rows", str(sample_rows_json), "--output", str(out),
             "--tab-name", "MutualTab", "--template", "mutual"],
            check=True, capture_output=True, text=True,
        )
        wb = CalamineWorkbook.from_path(str(out))
        rows = wb.get_sheet_by_name("MutualTab").to_python()
        header_row = next(r for r in rows if "Priority" in r)
        assert "A" in header_row
        assert "B" in header_row
        # A and B come right before Result
        a_idx = header_row.index("A")
        b_idx = header_row.index("B")
        result_idx = header_row.index("Result")
        assert a_idx < result_idx
        assert b_idx < result_idx
        assert a_idx == result_idx - 2
```

Run — expect PASS (already implemented). If it fails, debug `_columns_for("mutual")`.

If it passes immediately (no need for impl change), still commit it as a verification:

```bash
git add tests/test_new_workbook.py
git commit -m "test(new_workbook): mutual template includes A/B columns"
```

(This is one commit, not RED→GREEN, because the impl already exists. That's fine — it's a verification test.)

---

## Phase 2: append_to_master.py (TDD, hardest part)

### Task 2.1: TDD — `append_to_master.py` happy path

**Files:**
- Create: `tests/test_append_to_master.py`
- Create: `shared/append_to_master.py`

핵심 요구사항:
1. 원본 마스터는 절대 수정 안 함 (in-place 금지)
2. 항상 새 파일에 저장 (collision 시 (2), (3) 접미사)
3. 지정 탭의 last TC_ID에서 +1 자동 증분
4. 다른 탭은 변경 없음
5. 셀 병합/줄바꿈 보존 (best effort)
6. 행 삽입 위치: 지정 섹션 마지막 TC 다음, 또는 새 섹션이면 시트 맨 끝

#### Step 1 (RED): write 4 tests

```python
"""Tests for shared/append_to_master.py."""
import json
import shutil
import subprocess
import sys
from pathlib import Path

import pytest
from python_calamine import CalamineWorkbook


@pytest.fixture
def append_rows_json(tmp_path: Path) -> Path:
    data = {
        "rows": [
            {
                "section": "Async First Entry",  # existing section in Lounge fixture
                "Priority": "P3", "OS": "All", "Automation Check": "All",
                "Test Item": "라운지 진입",
                "Test Summary": "신규 추천 알고리즘 활성화 시 추천 노출",
                "Remote Config / Admin": "enableNewLoungeRecommendation: true",
                "Pre-condition": "신규 사용자",
                "Test Step": "라운지 탭 진입",
                "Expected Result": "추천 카드 섹션 노출",
            },
        ]
    }
    p = tmp_path / "append.json"
    p.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
    return p


@pytest.fixture
def master_copy(tmp_path: Path, minimal_master_path: Path) -> Path:
    """Copy of the minimal master so we can verify the original isn't mutated."""
    dst = tmp_path / "master_copy.xlsx"
    shutil.copy2(minimal_master_path, dst)
    return dst


class TestAppendToMaster:
    def test_does_not_modify_master(self, master_copy: Path, append_rows_json: Path,
                                     tmp_path: Path, minimal_master_path: Path):
        out = tmp_path / "appended.xlsx"
        original_bytes = minimal_master_path.read_bytes()
        subprocess.run(
            [sys.executable, "shared/append_to_master.py",
             "--master", str(master_copy), "--tab", "Lounge",
             "--rows", str(append_rows_json), "--output", str(out)],
            check=True, capture_output=True, text=True,
        )
        # Original master untouched
        assert minimal_master_path.read_bytes() == original_bytes
        # Master copy untouched (we only read from it)
        assert master_copy.read_bytes() == original_bytes

    def test_creates_new_file_with_appended_rows(self, master_copy: Path,
                                                   append_rows_json: Path, tmp_path: Path):
        out = tmp_path / "appended.xlsx"
        subprocess.run(
            [sys.executable, "shared/append_to_master.py",
             "--master", str(master_copy), "--tab", "Lounge",
             "--rows", str(append_rows_json), "--output", str(out)],
            check=True, capture_output=True, text=True,
        )
        assert out.exists()
        wb = CalamineWorkbook.from_path(str(out))
        # Both tabs preserved
        assert set(wb.sheet_names) == {"login", "Lounge"}
        # The appended row's Test Summary appears in the Lounge tab
        rows = wb.get_sheet_by_name("Lounge").to_python()
        flat = [str(c) for r in rows for c in r if c]
        assert any("신규 추천 알고리즘 활성화 시 추천 노출" in c for c in flat)

    def test_login_tab_unchanged(self, master_copy: Path, append_rows_json: Path,
                                  tmp_path: Path, minimal_master_path: Path):
        out = tmp_path / "appended.xlsx"
        subprocess.run(
            [sys.executable, "shared/append_to_master.py",
             "--master", str(master_copy), "--tab", "Lounge",
             "--rows", str(append_rows_json), "--output", str(out)],
            check=True, capture_output=True, text=True,
        )
        original_login = CalamineWorkbook.from_path(str(minimal_master_path)).get_sheet_by_name("login").to_python()
        new_login = CalamineWorkbook.from_path(str(out)).get_sheet_by_name("login").to_python()
        assert original_login == new_login

    def test_tc_id_auto_incremented(self, master_copy: Path, append_rows_json: Path,
                                     tmp_path: Path):
        out = tmp_path / "appended.xlsx"
        subprocess.run(
            [sys.executable, "shared/append_to_master.py",
             "--master", str(master_copy), "--tab", "Lounge",
             "--rows", str(append_rows_json), "--output", str(out)],
            check=True, capture_output=True, text=True,
        )
        # Find the appended row in output and verify its TC_ID is `1-N` where N
        # is one more than the last `1-X` TC_ID in the original Async First Entry section.
        wb = CalamineWorkbook.from_path(str(out))
        rows = wb.get_sheet_by_name("Lounge").to_python()
        # Find the row containing the new Test Summary
        new_row = next(r for r in rows if any(
            isinstance(c, str) and "신규 추천 알고리즘 활성화 시 추천 노출" in c
            for c in r
        ))
        # Find TC_ID in that row — should match pattern 1-N
        tc_ids = [c for c in new_row if isinstance(c, str) and c.startswith("1-")]
        assert tc_ids, f"No 1-* TC_ID found in appended row: {new_row}"
        # The numeric suffix should be > the last existing 1-N in original
        new_n = int(tc_ids[0].split("-")[1])
        # Compute original max in section 1
        orig_rows = CalamineWorkbook.from_path(str(master_copy)).get_sheet_by_name("Lounge").to_python()
        orig_section_1_tc_ids = [
            int(str(c).split("-")[1])
            for r in orig_rows for c in r
            if isinstance(c, str) and c.startswith("1-") and "-" in c and c.split("-")[1].isdigit()
        ]
        assert new_n == max(orig_section_1_tc_ids) + 1
```

Run `uv run pytest tests/test_append_to_master.py -v` — expect ALL FAIL.

Commit:
```bash
git add tests/test_append_to_master.py
git commit -m "test(append_to_master): no-mutate + append + unchanged tabs + TC_ID increment (RED)"
```

#### Step 2 (GREEN): implement `shared/append_to_master.py`

```python
"""Append TC rows to a specific tab of an existing master xlsx.

Usage:
    python append_to_master.py --master master.xlsx --tab "Lounge" \
        --rows rows.json --output out.xlsx

NEVER modifies the master. Always writes a new file (collision-safe).
"""
from __future__ import annotations

import argparse
import json
import shutil
import sys
from pathlib import Path

from openpyxl import load_workbook
from openpyxl.styles import Alignment

# Local imports — shared/inspect_master.py for column mapping + section info
sys.path.insert(0, str(Path(__file__).parent))
from inspect_master import parse_tab_meta  # noqa: E402

WRAP = Alignment(wrap_text=True, vertical="top")


def _resolve_output_path(path: Path) -> Path:
    if not path.exists():
        return path
    stem, suffix = path.stem, path.suffix
    n = 2
    while True:
        candidate = path.parent / f"{stem} ({n}){suffix}"
        if not candidate.exists():
            return candidate
        n += 1


def _next_tc_id(section_idx_str: str, last_tc_id: str | None) -> str:
    """Given e.g. '1' and last '1-23', return '1-24'. If no last, start at <idx>-1."""
    if last_tc_id and "-" in last_tc_id:
        sec, num = last_tc_id.split("-", 1)
        if num.isdigit():
            return f"{sec}-{int(num) + 1}"
    return f"{section_idx_str}-1"


def append_to_master(master: Path, tab: str, rows: list[dict], output: Path) -> Path:
    """Append rows to `tab` of `master`. Writes to `output` (or collision-safe variant).
    Returns actual output path."""
    meta = parse_tab_meta(master, tab)
    columns: dict[str, int] = meta["columns"]
    sections: list[dict] = meta["sections"]

    # Map section name → (idx_str, last_tc_id). Use section name as user supplies it
    # in row.section; match against meta sections by name (substring tolerant).
    def _find_section(user_section: str) -> dict | None:
        # Exact name match first
        for s in sections:
            if s["name"] == user_section:
                return s
        # Substring match (tolerant: "Async First Entry" matches if either contains the other)
        for s in sections:
            if user_section in s["name"] or s["name"] in user_section:
                return s
        return None

    # Make output dir + collision-safe path
    actual_output = _resolve_output_path(output)
    actual_output.parent.mkdir(parents=True, exist_ok=True)

    # Open with openpyxl (preserves formatting, supports append)
    wb = load_workbook(master)
    if tab not in wb.sheetnames:
        raise ValueError(f"Tab '{tab}' not found in {master.name}. Available: {wb.sheetnames}")
    ws = wb[tab]

    # Determine append position: append at end of sheet for now (Phase 2 baseline).
    # TC_ID increments per section based on existing last_tc_id.
    # Group input rows by section name.
    section_buckets: dict[str, list[dict]] = {}
    for r in rows:
        s = r.get("section") or "(default)"
        section_buckets.setdefault(s, []).append(r)

    # Determine starting row for append (1-indexed, openpyxl uses 1-based)
    next_excel_row = ws.max_row + 1

    for user_section, bucket in section_buckets.items():
        match = _find_section(user_section)
        if match is None:
            # New section — write a section header row first
            new_section_idx = max(
                (int(s["last_tc_id"].split("-")[0]) for s in sections if s.get("last_tc_id") and "-" in s["last_tc_id"]),
                default=0,
            ) + 1
            # Section header: Priority cell = numeric idx, Test Item cell = section name
            pri_idx = columns.get("Priority")
            item_idx = columns.get("Test Item")
            if pri_idx is not None:
                ws.cell(row=next_excel_row, column=pri_idx + 1, value=float(new_section_idx))
            if item_idx is not None:
                ws.cell(row=next_excel_row, column=item_idx + 1, value=user_section)
            next_excel_row += 1
            section_idx_str = str(new_section_idx)
            last_tc_id = None
        else:
            section_idx_str = (
                match["last_tc_id"].split("-")[0] if match.get("last_tc_id") else "1"
            )
            last_tc_id = match.get("last_tc_id")

        for row_data in bucket:
            tc_id = _next_tc_id(section_idx_str, last_tc_id)
            last_tc_id = tc_id
            for col_name, col_idx in columns.items():
                if col_name == "TC_ID":
                    value = tc_id
                elif col_name == "Test Item" and "Test Item" not in row_data:
                    # Inherit from section name if not provided
                    value = user_section
                else:
                    value = row_data.get(col_name, "")
                cell = ws.cell(row=next_excel_row, column=col_idx + 1, value=value)
                cell.alignment = WRAP
            next_excel_row += 1

    wb.save(actual_output)
    return actual_output


def main() -> None:
    parser = argparse.ArgumentParser(description="Append TC rows to a master xlsx tab.")
    parser.add_argument("--master", type=Path, required=True)
    parser.add_argument("--tab", type=str, required=True)
    parser.add_argument("--rows", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    data = json.loads(args.rows.read_text(encoding="utf-8"))
    rows = data.get("rows", [])
    actual = append_to_master(args.master, args.tab, rows, args.output)
    print(f"Wrote {actual}")
    print(actual)


if __name__ == "__main__":
    main()
```

Run `uv run pytest tests/test_append_to_master.py -v` — expect 4 PASS.

**Likely debugging needed**:
- `last_tc_id` from `parse_tab_meta` may need to be normalized (e.g., trailing whitespace).
- `next_excel_row = ws.max_row + 1` may include trailing blank rows. Consider scanning backward to find the actual last non-blank row.

**Known limitation (acceptable for Phase 2 PoC)**:
- `section_idx_str` fallback `"1"` is wrong when appending to a section that has `last_tc_id: None` AND is not section 1 (i.e., a section with no TC rows yet). Real `[ver117]` master has no such empty sections, so this won't trigger in practice. Track as Phase 3 follow-up: `parse_tab_meta` should return `section.index` (the leading numeric) alongside `last_tc_id`, and `_next_tc_id` should use that.

Iterate until 4 tests pass. If a test seems unfixable, mark DONE_WITH_CONCERNS and report.

Commit:
```bash
git add shared/append_to_master.py
git commit -m "feat(append_to_master): append rows preserving other tabs + TC_ID increment"
```

---

### Task 2.2: TDD — collision suffix on output

#### Step 1 (RED): test

Append to `tests/test_append_to_master.py`:

```python
class TestAppendCollision:
    def test_existing_output_gets_suffix(self, master_copy: Path, append_rows_json: Path,
                                           tmp_path: Path):
        out = tmp_path / "appended.xlsx"
        out.write_text("placeholder")  # pre-existing
        result = subprocess.run(
            [sys.executable, "shared/append_to_master.py",
             "--master", str(master_copy), "--tab", "Lounge",
             "--rows", str(append_rows_json), "--output", str(out)],
            capture_output=True, text=True, check=True,
        )
        actual = result.stdout.strip().splitlines()[-1]
        assert actual != str(out)
        assert Path(actual).exists()
```

Run — expect PASS (already implemented in `_resolve_output_path`).

If passes immediately, commit as verification:
```bash
git add tests/test_append_to_master.py
git commit -m "test(append_to_master): output collision gets (2) suffix"
```

---

## Phase 3: qa-generate-tc 스킬 번들

### Task 3.1: shared-reference 추가 (template-spec, prioritization-guide)

**Files:**
- Create: `shared-reference/template-spec.md`
- Create: `shared-reference/prioritization-guide.md`

- [ ] **Step 1: Write `shared-reference/template-spec.md`**

Content based on spec §6.1:

```markdown
# 표준 TC 템플릿 스펙

## Single 템플릿 (14 컬럼)

| 컬럼 | 타입 | 의미 | LLM 작성 가이드 |
|---|---|---|---|
| Priority | enum P1~P4 | 중요도 | 핵심=P1, 일반=P2, 부가=P3, 엣지=P4 |
| OS | enum iOS/And/All/공란 | 플랫폼 한정 | PRD에 명시 없으면 공란 |
| Automation Check | enum All/iOS/Android/Skip | 자동화 가능성 | 단순 UI=All, 복잡=Skip |
| Test Item | str | 시나리오 그룹명 | 섹션 내 서브카테고리 |
| Automation TC_ID | str | 자동화 ID 매핑 | LLM은 비워둠 |
| TC_ID | `<섹션>-<순번>` | 식별자 | 자동 증분 |
| Test Summary | str (1줄) | 무엇을 검증하나 | 짧은 명사구 |
| Remote Config / Admin | str | 플래그·어드민 조건 | PRD에 있으면 명시 |
| Pre-condition | str (multiline) | 사전조건 | 국가/계정/설정 |
| Test Step | str (multiline) | 실행 절차 | 명령형 한 줄씩 |
| Expected Result | str (multiline) | 기대 결과 | 관찰 가능한 사실 |
| Result | str | 실행 결과 | 비움 (사람 채움) |
| Jira no. | str | 버그 티켓 | 비움 (사람 채움) |
| Comment | str (multiline) | 보충/의문 | a/b/c 서브케이스, 가정 명시 |

옵션 컬럼 (일부 시트만): `Policy : URL`, `Policy_page` — 마스터에 있으면 매핑하고 비워둠.

## Mutual 템플릿 (in Match 류)

위 14컬럼 + `A`, `B` 컬럼 추가, `Test Step`이 `Test Reproduce`로 변경. 두 디바이스로 양방향 동작 검증.

자동 감지: 마스터의 해당 탭에 `A`, `B` 컬럼 존재 시 mutual.

## 컬럼 인덱스 주의

마스터 시트는 탭마다 leading 빈 컬럼 인덱스 0이 있는 탭(`login`, `More`)과 없는 탭(`Lounge`, `Shop`)이 섞여 있다. 헤더명 → 실제 셀 인덱스 매핑은 매번 `inspect_master.parse_tab_meta`가 만들어낸다. 위 표의 순서는 *논리 순서*이지 셀 인덱스 아님.

## 줄바꿈·서식 규칙

- `Test Step`, `Expected Result`, `Pre-condition`, `Comment`는 multiline. `\n` 사용.
- 셀에 wrap_text=True 적용.
- `Comment`의 a/b/c 서브케이스는 다음 형식:
  ```
  a: 첫 번째 서브케이스 설명
  b: 두 번째 서브케이스 설명
  c: ...
  ```
```

- [ ] **Step 2: Write `shared-reference/prioritization-guide.md`**

```markdown
# Priority 판단 가이드 (P1~P4)

PRD에서 직접 명시하지 않은 경우의 휴리스틱.

## P1 — 핵심
- PRD의 "사용자 시나리오" 본문에 직접 등장하는 동작
- 신규 피처의 진입점 / 핵심 기능 / 결제 흐름
- 신규 화면의 정상 진입 경로
- Remote Config 플래그 ON 상태의 기본 동작

## P2 — 일반
- 핵심 기능의 OS별 차이 동작
- 부가 진입 경로 (예: 알림에서 진입, 딥링크 진입)
- Remote Config 플래그 OFF 상태 동작 (PRD에 명시된 경우)
- 일반적인 권한 요청 흐름

## P3 — 부가
- 화면 UI 디테일 (스크롤, 애니메이션, 작은 인터랙션)
- 정상 흐름의 예상 가능한 변형 (재시도, 새로고침 등)
- 분석 이벤트 발생 검증

## P4 — 엣지
- 네거티브 케이스 (네트워크 실패, 타임아웃, 권한 거부)
- 경계값 (최대/최소, 빈 결과)
- 동시성 / 백그라운드 전환 시나리오
- 드물게 발생하는 에러 처리

## 분배 가이드라인 (참고)
한 PRD당 P1:P2:P3:P4 비율은 대략 **2:4:3:1** 정도가 자연스러움.
P1만 잔뜩 있으면 우선순위가 무의미해지고, P4만 있으면 기본 동작 검증을 빠뜨릴 수 있음.
이 비율과 크게 다르면 다시 한번 점검.
```

- [ ] **Step 3: Commit**

```bash
git add shared-reference/
git commit -m "docs: add template-spec + prioritization-guide (qa:generate-tc reference)"
```

---

### Task 3.2: qa-generate-tc skill bundle skeleton + sync

**Files:**
- Create: `skills/qa-generate-tc/scripts/` (empty dir initially)
- Create: `skills/qa-generate-tc/reference/` (empty dir initially)
- Create: `skills/qa-generate-tc/examples/sample-tcs.md`
- Create: `skills/qa-generate-tc/SKILL.md`

- [ ] **Step 1: Create dirs**

```bash
mkdir -p skills/qa-generate-tc/scripts skills/qa-generate-tc/reference skills/qa-generate-tc/examples
```

- [ ] **Step 2: Touch the script slots so sync_shared.py copies into them**

`sync_shared.py` only overwrites files that already exist. So we need empty placeholder files first:

```bash
touch skills/qa-generate-tc/scripts/inspect_master.py
touch skills/qa-generate-tc/scripts/new_workbook.py
touch skills/qa-generate-tc/scripts/append_to_master.py
touch skills/qa-generate-tc/reference/template-spec.md
touch skills/qa-generate-tc/reference/prioritization-guide.md
touch skills/qa-generate-tc/reference/domain-glossary.md
```

- [ ] **Step 3: Run sync**

```bash
uv run python scripts/sync_shared.py
```
Expected output: 6 `updated:` lines (3 scripts + 3 reference files).

Then verify:
```bash
diff shared/inspect_master.py skills/qa-generate-tc/scripts/inspect_master.py
diff shared/new_workbook.py skills/qa-generate-tc/scripts/new_workbook.py
diff shared/append_to_master.py skills/qa-generate-tc/scripts/append_to_master.py
diff shared-reference/domain-glossary.md skills/qa-generate-tc/reference/domain-glossary.md
diff shared-reference/template-spec.md skills/qa-generate-tc/reference/template-spec.md
diff shared-reference/prioritization-guide.md skills/qa-generate-tc/reference/prioritization-guide.md
```
All should be clean (no diff output).

- [ ] **Step 4: Write `skills/qa-generate-tc/examples/sample-tcs.md`**

```markdown
# 예시: qa:generate-tc 출력 (Lounge 신규 추천 PRD)

LLM 톤·세분도 학습용 few-shot. `tests/fixtures/sample_prd.md`를 입력으로 받았을 때 기대되는 TC 표 (마크다운 미리보기 형태).

## 1. 라운지 메인 (신규 시트 모드 가정)

| Priority | OS | Automation | Test Item | TC_ID | Test Summary | Remote Config | Pre-condition | Test Step | Expected Result | Comment |
|---|---|---|---|---|---|---|---|---|---|---|
| P1 | All | All | 추천 섹션 | 1-1 | 라운지 진입 시 추천 섹션 노출 | enableNewLoungeRecommendation: true | 신규 사용자, KR | 1. 앱 실행<br>2. 라운지 탭 진입 | 상단에 "추천" 섹션 노출, 가로 스크롤 카드 | a: 카드 개수 확인<br>b: 첫 카드의 프로필 사진+닉네임 표시 |
| P1 | All | Skip | 추천 섹션 | 1-2 | Remote Config OFF 시 동작 | enableNewLoungeRecommendation: false | 신규 사용자 | 1. 앱 실행<br>2. 라운지 탭 진입 | (PRD 답변에 따라: 추천 섹션 비노출 OR 기존 알고리즘으로 폴백) | PRD 모호 — qa:prd-clarify 결과 필요 |
| P2 | All | Skip | 분석 이벤트 | 1-3 | lounge_recommendation_shown 발생 | enableNewLoungeRecommendation: true | 분석 로그 디버그 모드 | 1. 라운지 탭 진입 | 화면 진입 시 lounge_recommendation_shown 1회 발생 | 파라미터는 PRD 미정의 |
| P3 | All | Skip | 정책 | 1-4 | 차단한 상대 추천 제외 | enableNewLoungeRecommendation: true | A 사용자가 B 사용자 차단 상태 | 1. A로 라운지 진입 | 추천 카드에 B 미포함 | |
| P4 | All | Skip | 에러 케이스 | 1-5 | 추천 데이터 fetch 실패 | enableNewLoungeRecommendation: true, 네트워크 차단 | 비행기 모드 | 1. 라운지 탭 진입 | (PRD 답변에 따라: 빈 화면 OR 에러 메시지 OR 기본 추천) | PRD 모호 |

## 비고
- TC_ID는 자동 증분 (1-1, 1-2, ...)
- 모호한 PRD 항목은 Comment에 명시하고 진행 (`qa:prd-clarify` 권유)
- 한국어 톤: 짧은 명령형. 격식체 회피.
```

- [ ] **Step 5: Write `skills/qa-generate-tc/SKILL.md`**

```markdown
---
name: qa-generate-tc
description: Notion PRD를 분석해서 표준 14컬럼 QA 테스트케이스를 xlsx로 생성. 신규 시트 모드 또는 기존 마스터 xlsx에 append 모드 지원. 사람 컨펌 루프 필수. 트리거 — "테스트 케이스 생성", "TC 만들어", "PRD에서 TC 뽑아", "/qa:generate-tc".
---

# qa:generate-tc

PRD를 표준 TC 표로 변환한다. 두 모드:
- **신규 시트 모드**: 사용자가 새 탭 이름을 주면 빈 워크북에 14컬럼 + TC 행을 채워 출력.
- **append 모드**: 사용자가 기존 마스터 xlsx + 타겟 탭을 주면, 그 탭에 행을 삽입해 새 파일로 저장 (원본은 절대 수정 안 함).

## 워크플로우

### 1. PRD 수집
- Notion URL이면 `notion-fetch` MCP로 페이지 본문 + 자식 블록 + 임베드 객체 fetch.
- 본문이 50단어 미만이면 "PRD가 비어있는 듯, 본문 직접 붙여줄래?" 안내, 중단.
- PRD가 모호하면 사용자에게 `qa:prd-clarify`를 먼저 돌리라고 권유 (강제는 안 함).

### 2. 모드 결정
사용자가 명시하지 않았으면 묻기:
- "신규 시트로 만들까, 기존 마스터에 append 할까?"
- append 모드면 마스터 xlsx 경로(Code) 또는 업로드(Desktop) + 타겟 탭 이름 받기.

### 3. 컨텍스트 보강
**append 모드에서**: `scripts/inspect_master.py --tab <name>`을 subprocess로 호출해서 타겟 탭의 메타를 받음:
- `columns` (헤더명 → 셀 인덱스)
- `sections` (섹션 리스트, 각 섹션의 last_tc_id)
- `template_type` (single/mutual)
- `sample_rows` (3개 샘플 — 톤·세분도 학습)

**신규 시트 모드에서**: 표준 14컬럼 + `reference/template-spec.md` 참조.

### 4. TC 초안 생성
다음 휴리스틱 (`reference/prioritization-guide.md` + `reference/domain-glossary.md` 참조):
- 핵심 기능 = P1, 부가 = P2, 엣지/네거티브 = P3~P4
- PRD에 Remote Config 플래그 언급 → on/off 양쪽 TC 자동 분기
- PRD에 OS-specific 키워드 → OS 컬럼 명시
- mutual 키워드 (`매치`, `메시지`, `콜`, `라이브매치`) → mutual 템플릿 제안
- 한국어 작성, 기존 톤(짧은 명령형) 매칭
- 자동화 추정: 단순 UI=All, 결제·실시간=Skip
- 모호한 부분은 Comment에 가정 명시

### 5. 사용자 컨펌 루프 (필수)
xlsx 만들기 *전*에 마크다운 표 미리보기 출력. "추가/삭제/수정 의견 있으세요?" 질문. 수정 반영 → 재출력. 명시적 "OK" 또는 "진행해" 받으면 다음.

### 6. xlsx 생성
TC 행 데이터를 JSON으로 만들고 (`{rows: [{section, Priority, OS, ...}, ...]}`), 다음 중 하나 호출:

**신규 시트 모드**:
```bash
uv run python scripts/new_workbook.py \
    --rows /tmp/rows.json --output <out>.xlsx \
    --tab-name "<탭 이름>" [--template single|mutual]
```

**append 모드**:
```bash
uv run python scripts/append_to_master.py \
    --master <master>.xlsx --tab "<탭 이름>" \
    --rows /tmp/rows.json --output <out>.xlsx
```

스크립트 stdout 마지막 라인이 실제 출력 경로 (collision 시 `(2)`, `(3)` 접미사 자동 부여).

### 7. 결과 보고
- 출력 경로 + 추가된 TC 수
- append 모드면 "원본 마스터는 수정 안 됨, 새 파일에 저장" 명시
- 다음 액션 안내: "이 파일을 Google Sheets에 업로드하거나 마스터에 복붙하세요"

## 출력 톤
- 한국어 (모든 cells)
- TC Test Step·Expected Result는 짧은 명령형
- 모호 항목은 Comment에 명시

## 비목표
- PRD 자체 분석 (그건 `qa:prd-clarify`)
- 작성된 TC 검수 (그건 `qa:review-tc`)
- 자동 실행 / Jira 자동 등록

## 예시
`examples/sample-tcs.md` 참조.

## 트러블슈팅

**"마스터 xlsx 경로가 잘못됨"**: cwd부터 최대 2단계 하위까지 `*.xlsx` 검색해서 후보 제안. 시스템 전체 검색은 안 함.

**"마스터의 컬럼이 표준과 다름"**: 발견된 컬럼 표시 + 매핑 직접 묻기. `inspect_master.py`가 자동 매핑하는 컬럼 외에는 LLM 추정 금지.

**"같은 PRD를 두 번 돌렸음"**: append 모드에서 TC_ID 충돌이 감지되면 멈추고 사용자에게 보고. 자동 패치 안 함.
```

- [ ] **Step 6: Commit**

```bash
git add skills/qa-generate-tc/
git commit -m "feat(skill): add qa-generate-tc bundle (SKILL.md + scripts + reference + example)"
```

---

### Task 3.3: 통합 smoke test (수동, controller-driven)

이 태스크는 controller가 직접 수행. 자동 가능한 부분만 작성.

- [ ] **Step 1: 신규 시트 모드 smoke**

수동으로 가짜 rows.json을 만들고 새 워크북 생성:
```bash
cat > /tmp/sample_rows.json << 'EOF'
{"rows":[{"section":"1. 라운지 메인","Priority":"P1","OS":"All","Automation Check":"All","Test Item":"메인 화면","Test Summary":"라운지 진입 시 추천 노출","Pre-condition":"신규 사용자","Test Step":"1. 앱 실행\n2. 라운지 탭 진입","Expected Result":"추천 카드 섹션 노출","Comment":"a: 카드 개수\nb: 스크롤"}]}
EOF
uv run python skills/qa-generate-tc/scripts/new_workbook.py --rows /tmp/sample_rows.json --output /tmp/test_new.xlsx --tab-name "TestNew"
open /tmp/test_new.xlsx
```
육안 확인: 헤더 14컬럼 + 섹션 행 1개 + TC 행 1개 (TC_ID = 1-1).

- [ ] **Step 2: append 모드 smoke**

```bash
cp tests/fixtures/master_v117_minimal.xlsx /tmp/master_test.xlsx
uv run python skills/qa-generate-tc/scripts/append_to_master.py --master /tmp/master_test.xlsx --tab Lounge --rows /tmp/sample_rows.json --output /tmp/test_appended.xlsx
open /tmp/test_appended.xlsx
```
육안 확인:
- `login` 탭 그대로
- `Lounge` 탭 끝에 행 추가, TC_ID는 기존 마지막 1-N 다음 번호
- 원본 `/tmp/master_test.xlsx`는 변화 없음 (`md5sum` 비교)

- [ ] **Step 3: Fresh subagent로 SKILL.md 워크플로우 시뮬레이션**

Fresh subagent에게 `tests/fixtures/sample_prd.md`를 PRD로 주고, `skills/qa-generate-tc/SKILL.md` + reference를 읽고 신규 시트 모드로 TC 표를 작성하라고 지시. 결과를 `examples/sample-tcs.md`와 비교.

- [ ] **Step 4: README 업데이트**

`README.md`의 "검증 이력" 섹션에 Phase 2 결과 추가.

- [ ] **Step 5: Commit**

```bash
git add README.md
git commit -m "test(qa-generate-tc): smoke test (new + append) passed"
```

---

## Phase 2 완료 체크리스트

- [ ] `uv run pytest -v` 모든 테스트 PASS (Phase 1 13개 + Phase 2 새 테스트들)
- [ ] `uv run python scripts/sync_shared.py --check` 0 exit
- [ ] `qa-generate-tc` 스킬이 `.claude/skills/`에 디스커버 가능
- [ ] 신규 시트 + append 모드 둘 다 sample_rows.json으로 동작 확인
- [ ] 원본 마스터 절대 수정 안 됨 (md5sum 또는 read_bytes 비교)
- [ ] Fresh subagent 시뮬레이션으로 SKILL.md 워크플로우 검증
- [ ] README 업데이트
- [ ] 모든 변경 git commit

---

## 다음 플랜 — Phase 3 (`qa-review-tc`)

Phase 2 끝나면 별도 플랜으로:
- `inspect_master.py` 복제 (sync_shared.py가 자동)
- TDD: `validate_format.py` (필수 컬럼/enum/TC_ID 중복)
- TDD: `find_duplicates.py` (탭 내 + 탭 간)
- TDD: `extract_tc_table.py`
- SKILL.md + reference (format-rules, coverage-checklist) + example
- 의도적 이슈 fixture (`sample_tc_with_issues.xlsx`)
- 통합 smoke test

## Phase 2에서 의도적으로 보류한 이슈 (Phase 3 또는 후속에서)

1. **Empty section append bug**: `append_to_master.py`의 `section_idx_str` fallback이 빈 섹션(last_tc_id None인 비-1번 섹션) append 시 잘못된 결과 생성. `parse_tab_meta`에 `section.index` 추가하면 해결.
2. **Mutual template Test Step rename**: `new_workbook.py --template mutual`이 `Test Step`을 `Test Reproduce`로 rename 하지 않음. 매우 드문 mutual 신규 시트 케이스에만 영향 (실제 사용 빈도 낮음).
3. **list_tabs 성능**: `list_tabs`가 모든 탭의 전체 셀을 읽어서 column_count 계산. 큰 마스터 + Phase 3 cross-tab dup 스캔 시 중복 cost. 가벼운 `tab_dimensions(xlsx, name)` 분리 검토.
4. **inspect_master KNOWN_COLUMNS / COLUMN_ALIASES 구조적 중복**: 한쪽에 추가하고 다른 쪽 깜빡하면 silent bug. 단일 source로 통합.
