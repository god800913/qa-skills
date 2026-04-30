# QA Skills — Phase 1: Foundation + qa:prd-clarify Implementation Plan

> **For agentic workers:** REQUIRED: Use superpowers:subagent-driven-development (if subagents available) or superpowers:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 프로젝트 기반(deps, fixtures, 공유 스크립트 `inspect_master.py`)을 깔고, 가장 단순한 스킬인 `qa:prd-clarify`(PRD 모호점 추출, xlsx I/O 의존 없음)를 동작하는 상태로 출시.

**Architecture:** uv 기반 단일 Python 프로젝트. 스킬 번들은 `skills/<skill-name>/`에 자체 완결적으로 위치 (Anthropic Skills 표준). 공유 스크립트 `inspect_master.py`는 1차에 한 번 작성하고 추후 Phase 2/3에서 각 스킬 번들에 복제(스펙 §3.2 정책). `qa:prd-clarify`는 Python 스크립트 0개, SKILL.md 프롬프트 + reference 마크다운으로만 구성 — Claude Desktop/Code 양쪽에서 즉시 동작.

**Tech Stack:** Python 3.11+, uv (dep mgr), pytest, python-calamine (xlsx read), openpyxl (xlsx write & fixtures), Notion MCP (런타임).

**Spec reference:** `docs/superpowers/specs/2026-04-30-qa-skills-design.md`

**후속 플랜 (이 플랜 끝나면 별도 작성):**
- `2026-MM-DD-qa-skills-phase2-generate-tc.md` (qa:generate-tc + new_workbook.py + append_to_master.py)
- `2026-MM-DD-qa-skills-phase3-review-tc.md` (qa:review-tc + validate_format.py + find_duplicates.py + extract_tc_table.py)

---

## File Structure

이 플랜에서 생성/수정되는 파일:

```
qa-skills/
├── pyproject.toml                                          # NEW — deps + pytest config
├── README.md                                               # NEW — onboarding
├── .gitignore                                              # NEW
├── tests/
│   ├── __init__.py                                         # NEW
│   ├── conftest.py                                         # NEW — fixture paths
│   ├── fixtures/
│   │   ├── master_v117_minimal.xlsx                       # NEW — 2 탭만 (login: leading-blank-col, Lounge: no-leading-blank-col)
│   │   └── sample_prd.md                                   # NEW — 의도적 모호점 포함
│   └── test_inspect_master.py                              # NEW — 공유 스크립트 단위 테스트
├── shared/
│   └── inspect_master.py                                   # NEW — 1차 작성 위치, 추후 각 스킬에 복제
├── shared-reference/
│   ├── domain-glossary.md                                  # NEW — Azar 용어, 추후 각 스킬에 복제
│   └── ambiguity-checklist.md                              # NEW — qa:prd-clarify 전용
├── skills/
│   └── qa-prd-clarify/
│       ├── SKILL.md                                        # NEW
│       ├── reference/
│       │   ├── domain-glossary.md                          # NEW — shared-reference에서 복제
│       │   └── ambiguity-checklist.md                      # NEW — shared-reference에서 복제
│       └── examples/
│           └── sample-clarify-report.md                    # NEW
└── scripts/
    └── make_minimal_fixture.py                             # NEW — 마스터에서 fixture 추출하는 1회용 스크립트
```

원본 마스터 xlsx (`/Users/dongjin/Downloads/[ver117] Release QA_Testcase의 사본.xlsx`)는 fixture 생성 입력으로만 사용, 저장소에는 안 들어감.

---

## Phase 0: Project Foundation

### Task 0.1: Initialize Python project with uv

**Files:**
- Create: `qa-skills/pyproject.toml`
- Create: `qa-skills/.gitignore`
- Create: `qa-skills/README.md` (skeleton)

- [ ] **Step 1: Verify uv is installed**

```bash
uv --version
```
Expected: `uv 0.x.x` or higher. If missing: `brew install uv`.

- [ ] **Step 2: Write `pyproject.toml` directly (skip `uv init`)**

`uv init`은 이미 `docs/`가 있는 디렉토리에서 충돌 가능. 직접 작성:

```toml
[project]
name = "qa-skills"
version = "0.1.0"
description = "Hyperconnect Azar QA team's Claude Skills (PoC)"
requires-python = ">=3.11"
dependencies = [
    "openpyxl>=3.1.0",
    "python-calamine>=0.2.0",
]

[dependency-groups]
dev = [
    "pytest>=8.0.0",
    "pytest-cov>=5.0.0",
]

[tool.pytest.ini_options]
testpaths = ["tests"]
python_files = ["test_*.py"]
addopts = "-v --tb=short"
```

- [ ] **Step 3: Sync deps**

```bash
uv sync
```
Expected: virtualenv `.venv/` created, `uv.lock` 생성, deps 설치.

- [ ] **Step 4: Create `.gitignore`**

```
.venv/
__pycache__/
*.pyc
.pytest_cache/
.coverage
htmlcov/
*.egg-info/
dist/
build/
.DS_Store
```

- [ ] **Step 5: Create README skeleton**

```markdown
# qa-skills

Hyperconnect Azar QA 팀용 Claude Skills (PoC).

상세 디자인: [`docs/superpowers/specs/2026-04-30-qa-skills-design.md`](docs/superpowers/specs/2026-04-30-qa-skills-design.md)

## 설치
```bash
uv sync
```

## 테스트
```bash
uv run pytest
```

## 스킬 목록
- `qa-prd-clarify` — PRD 모호점 추출 (Phase 1)
- `qa-generate-tc` — TC xlsx 생성 (Phase 2, TBD)
- `qa-review-tc` — TC xlsx 리뷰 (Phase 3, TBD)
```

- [ ] **Step 6: Init git + initial commit**

```bash
cd /Users/dongjin/Dropbox/workplace/HyperConnect/poc/qa-skills
git init
git add pyproject.toml uv.lock .gitignore README.md docs/
git commit -m "chore: init qa-skills project (uv, pytest, deps)"
```

---

### Task 0.2: Create test scaffolding

**Files:**
- Create: `tests/__init__.py` (empty)
- Create: `tests/conftest.py`
- Create: `tests/fixtures/` (dir)

- [ ] **Step 1: Create empty `tests/__init__.py`**

```python
```

- [ ] **Step 2: Create `tests/conftest.py`**

```python
"""Shared pytest fixtures."""
from pathlib import Path

import pytest

FIXTURES_DIR = Path(__file__).parent / "fixtures"


@pytest.fixture
def fixtures_dir() -> Path:
    return FIXTURES_DIR


@pytest.fixture
def minimal_master_path(fixtures_dir: Path) -> Path:
    return fixtures_dir / "master_v117_minimal.xlsx"


@pytest.fixture
def sample_prd_path(fixtures_dir: Path) -> Path:
    return fixtures_dir / "sample_prd.md"
```

- [ ] **Step 3: Create empty fixtures dir + .gitkeep placeholder**

```bash
mkdir -p tests/fixtures
touch tests/fixtures/.gitkeep
```

- [ ] **Step 4: Verify pytest discovers (no tests yet, should run cleanly)**

```bash
uv run pytest
```
Expected: `no tests ran in 0.0Xs` (exit code 5 — that's fine for now since we'll add tests).

If you want to suppress the no-tests-ran warning: skip this — exit code 5 is OK during scaffolding.

- [ ] **Step 5: Commit**

```bash
git add tests/
git commit -m "test: add pytest scaffolding (conftest + fixtures dir)"
```

---

### Task 0.3: Generate minimal master xlsx fixture

**Files:**
- Create: `scripts/make_minimal_fixture.py`
- Create: `tests/fixtures/master_v117_minimal.xlsx` (script output)

원본 마스터에서 `login` 탭(leading 빈 컬럼 있음) + `Lounge` 탭(없음) 2개만 추출. 픽스처 요건(스펙 §8.1): 두 컬럼 변형 모두 커버.

- [ ] **Step 1: Create the extractor script**

Create `scripts/make_minimal_fixture.py`:

```python
"""One-shot script: extract 2 tabs from the master xlsx into a minimal test fixture.

Run once when setting up the project. Output is committed to tests/fixtures/.
"""
from pathlib import Path

from openpyxl import Workbook
from python_calamine import CalamineWorkbook

SOURCE = Path("/Users/dongjin/Downloads/[ver117] Release QA_Testcase의 사본.xlsx")
TARGET = Path(__file__).parent.parent / "tests" / "fixtures" / "master_v117_minimal.xlsx"
TABS_TO_EXTRACT = ["login", "Lounge"]
MAX_ROWS_PER_TAB = 30  # keep fixtures small


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
            out_ws.append(list(row))

    TARGET.parent.mkdir(parents=True, exist_ok=True)
    out_wb.save(TARGET)
    print(f"Wrote {TARGET} with tabs: {TABS_TO_EXTRACT}")


if __name__ == "__main__":
    main()
```

- [ ] **Step 2: Run the script**

```bash
uv run python scripts/make_minimal_fixture.py
```
Expected: `Wrote /Users/.../tests/fixtures/master_v117_minimal.xlsx with tabs: ['login', 'Lounge']`.

- [ ] **Step 3: Verify the fixture**

```bash
uv run python -c "from python_calamine import CalamineWorkbook; wb = CalamineWorkbook.from_path('tests/fixtures/master_v117_minimal.xlsx'); print(wb.sheet_names); print('login row 0:', wb.get_sheet_by_name('login').to_python()[0]); print('Lounge row 0:', wb.get_sheet_by_name('Lounge').to_python()[0])"
```
Expected:
- `['login', 'Lounge']`
- `login row 0: ['', 'Priority', 'OS', ...]` (leading blank col)
- `Lounge row 0: ['Priority', 'OS', ...]` (no leading blank)

If the leading-blank distinction is gone (both have leading blank or neither), inspect the source file:
```bash
uv run python -c "from python_calamine import CalamineWorkbook; wb = CalamineWorkbook.from_path('/Users/dongjin/Downloads/[ver117] Release QA_Testcase의 사본.xlsx'); print('login row 0:', wb.get_sheet_by_name('login').to_python()[0])"
```
and adjust the extraction (the openpyxl `None` handling above should preserve empty strings as actual empty cells).

- [ ] **Step 4: Commit script + fixture**

```bash
git add scripts/make_minimal_fixture.py tests/fixtures/master_v117_minimal.xlsx
git rm tests/fixtures/.gitkeep
git commit -m "test: add minimal master xlsx fixture (login + Lounge tabs)"
```

---

### Task 0.4: Create sample PRD fixture

**Files:**
- Create: `tests/fixtures/sample_prd.md`

`qa:prd-clarify`가 detect해야 할 모호점을 의도적으로 심어둔 PRD. 픽스처 요건: Blocker 1개 + Major 2개 + Minor 1개 + 깨끗한 부분도 포함.

- [ ] **Step 1: Write the fixture PRD**

Create `tests/fixtures/sample_prd.md`:

```markdown
# 라운지 신규 추천 알고리즘 (가짜 PRD)

## 배경
기존 라운지 추천 정확도가 낮아 신규 ML 모델로 교체.

## 사용자 시나리오
신규 사용자가 라운지에 진입하면 추천 카드가 노출된다.

## 화면
- 라운지 메인 화면 상단에 "추천" 섹션 추가
- 카드는 가로 스크롤
- 카드당 사용자 프로필 사진 + 닉네임 표시

## Remote Config
`enableNewLoungeRecommendation` 플래그가 활성화되면 신규 알고리즘이 동작.

## 분석 이벤트
화면 진입 시 `lounge_recommendation_shown` 이벤트 발생.

## 정책
사용자가 차단한 상대는 추천에서 제외.
```

**의도적 모호점** (qa:prd-clarify 검증용):
- **Blocker**: `enableNewLoungeRecommendation` 플래그 OFF 상태 동작 미정의
- **Major**: 추천 데이터 fetch 실패 시 fallback UI 미기술
- **Major**: OS 명시 없음 (iOS/Android/모두?)
- **Minor**: "가로 스크롤"의 카드 개수/크기 미정의

- [ ] **Step 2: Commit**

```bash
git add tests/fixtures/sample_prd.md
git commit -m "test: add sample PRD fixture with intentional ambiguities"
```

---

## Phase 1: Shared Script — `inspect_master.py`

`shared/inspect_master.py`에 1차 작성. 추후 Phase 2/3에서 각 스킬 번들에 복제 (스펙 §3.2). 이 플랜에서는 스크립트 작성 + 단위 테스트만.

### Task 1.1: Set up shared script package

**Files:**
- Create: `shared/__init__.py` (empty)
- Create: `shared/inspect_master.py` (skeleton)

- [ ] **Step 1: Create shared package**

```bash
mkdir -p shared
touch shared/__init__.py
```

- [ ] **Step 2: Create empty inspect_master.py**

```python
"""Inspect a master TC xlsx and extract structural metadata.

Used by qa-generate-tc (append mode) and qa-review-tc.

CLI:
    python inspect_master.py <xlsx_path> [--tab <tab_name>]

Without --tab: list all tabs (with Summary tabs marked excluded).
With --tab: full metadata for that tab (columns, sections, last TC_IDs, sample rows).

Output: JSON to stdout.
"""
```

- [ ] **Step 3: Commit**

```bash
git add shared/
git commit -m "chore: scaffold shared/inspect_master.py"
```

---

### Task 1.2: TDD — list_tabs (Summary exclusion)

**Files:**
- Create: `tests/test_inspect_master.py`
- Modify: `shared/inspect_master.py`

- [ ] **Step 1: Write the failing test**

Create `tests/test_inspect_master.py`:

```python
"""Tests for shared/inspect_master.py."""
from pathlib import Path

import pytest

from shared.inspect_master import list_tabs


class TestListTabs:
    def test_returns_all_tabs_with_summary_marked_excluded(self, minimal_master_path: Path):
        tabs = list_tabs(minimal_master_path)
        names = {t["name"] for t in tabs}
        assert names == {"login", "Lounge"}
        for tab in tabs:
            assert "is_summary" in tab
            assert "column_count" in tab
            assert tab["is_summary"] is False  # neither is a Summary tab
```

- [ ] **Step 2: Run — verify it fails**

```bash
uv run pytest tests/test_inspect_master.py::TestListTabs -v
```
Expected: `ImportError: cannot import name 'list_tabs'`.

- [ ] **Step 3: Implement minimal `list_tabs`**

Replace `shared/inspect_master.py` content with:

```python
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
```

- [ ] **Step 4: Run — verify it passes**

```bash
uv run pytest tests/test_inspect_master.py::TestListTabs -v
```
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add shared/inspect_master.py tests/test_inspect_master.py
git commit -m "feat(inspect_master): list_tabs with Summary exclusion flag"
```

---

### Task 1.3: TDD — list_tabs handles Summary tabs (extended fixture test)

**Files:**
- Modify: `tests/test_inspect_master.py`

이 테스트는 우리 minimal fixture에 Summary 탭이 없어서 한 단계 더 추가. 임시로 합성 xlsx를 만들어 검증.

- [ ] **Step 1: Add the test**

Append to `tests/test_inspect_master.py`:

```python
class TestListTabsSummaryDetection:
    def test_summary_tab_marked_excluded(self, tmp_path: Path):
        from openpyxl import Workbook

        wb = Workbook()
        wb.remove(wb.active)
        wb.create_sheet("Summary").append(["x"])
        wb.create_sheet("Summary의 사본").append(["x"])
        wb.create_sheet("Lounge").append(["Priority", "OS"])
        path = tmp_path / "synthetic.xlsx"
        wb.save(path)

        tabs = list_tabs(path)
        names_to_exclusion = {t["name"]: t["is_summary"] for t in tabs}
        assert names_to_exclusion == {
            "Summary": True,
            "Summary의 사본": True,
            "Lounge": False,
        }
```

- [ ] **Step 2: Run — verify it passes** (Summary detection should already work)

```bash
uv run pytest tests/test_inspect_master.py::TestListTabsSummaryDetection -v
```
Expected: PASS.

- [ ] **Step 3: Commit**

```bash
git add tests/test_inspect_master.py
git commit -m "test(inspect_master): verify Summary tab detection"
```

---

### Task 1.4: TDD — parse_tab_meta (header mapping handles leading-blank-col variation)

**Files:**
- Modify: `tests/test_inspect_master.py`
- Modify: `shared/inspect_master.py`

스펙 §6.1: 마스터에 leading 빈 컬럼이 있는 탭과 없는 탭이 섞여 있어 매번 헤더 매핑이 필요.

- [ ] **Step 1: Write the failing test**

Append to `tests/test_inspect_master.py`:

```python
from shared.inspect_master import parse_tab_meta


class TestParseTabMeta:
    def test_login_tab_has_leading_blank_column_handled(self, minimal_master_path: Path):
        meta = parse_tab_meta(minimal_master_path, "login")
        # Standard columns must be present in mapping regardless of leading blank
        assert "Priority" in meta["columns"]
        assert "TC_ID" in meta["columns"]
        # The mapping value is the actual cell index in the row, so leading-blank tabs
        # have Priority at index 1, not 0.
        assert meta["columns"]["Priority"] >= 1

    def test_lounge_tab_no_leading_blank(self, minimal_master_path: Path):
        meta = parse_tab_meta(minimal_master_path, "Lounge")
        assert "Priority" in meta["columns"]
        # Lounge should have Priority at index 0 (no leading blank)
        assert meta["columns"]["Priority"] == 0

    def test_returns_template_type_single(self, minimal_master_path: Path):
        meta = parse_tab_meta(minimal_master_path, "Lounge")
        assert meta["template_type"] == "single"
```

- [ ] **Step 2: Run — verify it fails**

```bash
uv run pytest tests/test_inspect_master.py::TestParseTabMeta -v
```
Expected: `ImportError: cannot import name 'parse_tab_meta'`.

- [ ] **Step 3: Implement `parse_tab_meta`**

Append to `shared/inspect_master.py`:

```python
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
COLUMN_ALIASES = {
    "Automation TC_ID": ["Automation\nTC_ID", "Automation TC_ID"],
    "Test Summary": ["Test Summary", "Test Summary "],
    "Remote Config / Admin": ["Remote Config\n/ Admin", "Remote Config / Admin"],
    "Pre-condition": ["Pre-condition", "Pre - condition"],
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
```

- [ ] **Step 4: Run — verify it passes**

```bash
uv run pytest tests/test_inspect_master.py::TestParseTabMeta -v
```
Expected: all 3 tests PASS.

If failing on the leading-blank test: inspect with
```bash
uv run python -c "from shared.inspect_master import parse_tab_meta; from pathlib import Path; print(parse_tab_meta(Path('tests/fixtures/master_v117_minimal.xlsx'), 'login'))"
```
and adjust `_canonicalize` rules.

- [ ] **Step 5: Commit**

```bash
git add shared/inspect_master.py tests/test_inspect_master.py
git commit -m "feat(inspect_master): parse_tab_meta with header mapping + template detection"
```

---

### Task 1.5: TDD — section detection + last TC_ID per section

**Files:**
- Modify: `tests/test_inspect_master.py`
- Modify: `shared/inspect_master.py`

섹션 헤더는 일반적으로 `1.0`, `2.0` 같은 숫자만 있거나 같은 행에 카테고리명이 있는 행. TC_ID는 `<섹션>-<순번>` 패턴.

**실제 마스터 파일에서 확인한 섹션 헤더 모양 (참고)**:
- `Lounge` 탭 row 1: `[1.0, 'Async First Entry', '', '', '', '', '', ...]` — Priority cell이 float `1.0`, 두 번째 셀이 섹션명.
- `login` 탭 row 1 (leading-blank-col): `['-', 1.0, '로그인 화면', '', ...]` — 인덱스 0이 빈 칸 또는 `-`, 인덱스 1이 `1.0`, 인덱스 2가 섹션명.
- 일반 TC 행: `Priority` 셀에 `'P1'`, `'P2'`, `'P3'`, `'P4'` 같은 문자열.

→ 휴리스틱 단순: Priority 셀이 numeric (int/float) 이거나 `\d+\.?\s+\S` 패턴 문자열이면 섹션 헤더, 아니면 TC 행.

- [ ] **Step 1: Write the failing test**

Append to `tests/test_inspect_master.py`:

```python
class TestParseTabMetaSections:
    def test_lounge_has_sections(self, minimal_master_path: Path):
        meta = parse_tab_meta(minimal_master_path, "Lounge")
        # Lounge fixture has at least one section header in the first 30 rows
        assert "sections" in meta
        assert isinstance(meta["sections"], list)
        # Each section has name, header_row, last_tc_id (or None)
        for sec in meta["sections"]:
            assert "name" in sec
            assert "header_row" in sec
            assert "last_tc_id" in sec  # may be None if no TCs in section yet

    def test_last_tc_id_format(self, minimal_master_path: Path):
        meta = parse_tab_meta(minimal_master_path, "Lounge")
        ids_found = [s["last_tc_id"] for s in meta["sections"] if s["last_tc_id"]]
        # Pattern <section>-<number>, e.g. "1-12"
        for tc_id in ids_found:
            assert "-" in tc_id, f"Unexpected TC_ID shape: {tc_id}"
```

- [ ] **Step 2: Run — verify it fails**

```bash
uv run pytest tests/test_inspect_master.py::TestParseTabMetaSections -v
```
Expected: `KeyError: 'sections'` (or AssertionError).

- [ ] **Step 3: Extend `parse_tab_meta` with section parsing**

In `shared/inspect_master.py`, add helpers and extend `parse_tab_meta`:

```python
import re

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


def _section_name(row: list, columns: dict[str, int]) -> str:
    """Pick the most informative non-blank cell as section name."""
    for idx, cell in enumerate(row):
        if cell and idx != columns.get("Priority"):
            return str(cell).strip()
    # Fall back to Priority cell if everything else is blank
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
```

Then extend the `parse_tab_meta` return:

```python
def parse_tab_meta(xlsx_path: Path, tab_name: str) -> dict:
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
        "sections": _parse_sections(rows, columns, header_row_idx),
    }
```

- [ ] **Step 4: Run — verify it passes**

```bash
uv run pytest tests/test_inspect_master.py::TestParseTabMetaSections -v
```
Expected: PASS.

If section detection misses, inspect actual rows:
```bash
uv run python -c "from python_calamine import CalamineWorkbook; print([r for r in CalamineWorkbook.from_path('tests/fixtures/master_v117_minimal.xlsx').get_sheet_by_name('Lounge').to_python()][:10])"
```
and tune the heuristic in `_is_section_header`.

- [ ] **Step 5: Commit**

```bash
git add shared/inspect_master.py tests/test_inspect_master.py
git commit -m "feat(inspect_master): parse sections + last_tc_id per section"
```

---

### Task 1.6: CLI wiring

**Files:**
- Modify: `shared/inspect_master.py`
- Modify: `tests/test_inspect_master.py`

CLI는 stdout으로 JSON 출력. argparse 사용.

- [ ] **Step 1: Write CLI test (smoke)**

Append to `tests/test_inspect_master.py`:

```python
import json
import subprocess
import sys


class TestCLI:
    def test_no_tab_lists_all(self, minimal_master_path: Path):
        result = subprocess.run(
            [sys.executable, "shared/inspect_master.py", str(minimal_master_path)],
            capture_output=True,
            text=True,
            check=True,
        )
        data = json.loads(result.stdout)
        assert "tabs" in data
        names = {t["name"] for t in data["tabs"]}
        assert names == {"login", "Lounge"}

    def test_with_tab_returns_meta(self, minimal_master_path: Path):
        result = subprocess.run(
            [sys.executable, "shared/inspect_master.py", str(minimal_master_path), "--tab", "Lounge"],
            capture_output=True,
            text=True,
            check=True,
        )
        data = json.loads(result.stdout)
        assert data["tab"] == "Lounge"
        assert "columns" in data
        assert "sections" in data
```

- [ ] **Step 2: Run — verify it fails**

```bash
uv run pytest tests/test_inspect_master.py::TestCLI -v
```
Expected: `subprocess.CalledProcessError` (script doesn't have CLI yet).

- [ ] **Step 3: Add CLI to `shared/inspect_master.py`**

Append:

```python
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
```

- [ ] **Step 4: Run — verify it passes**

```bash
uv run pytest tests/test_inspect_master.py::TestCLI -v
```
Expected: both tests PASS.

- [ ] **Step 5: Smoke test on the real master file (manual)**

```bash
uv run python shared/inspect_master.py "/Users/dongjin/Downloads/[ver117] Release QA_Testcase의 사본.xlsx" | head -60
```
Expected: JSON listing all 28 tabs with `is_summary: true` for the 3 Summary tabs.

```bash
uv run python shared/inspect_master.py "/Users/dongjin/Downloads/[ver117] Release QA_Testcase의 사본.xlsx" --tab Lounge | head -40
```
Expected: full meta for Lounge — `template_type: single`, columns mapping, sections with last_tc_id.

If something looks wrong (e.g. all sections have `last_tc_id: null`), inspect by hand and tune `_is_section_header` / `_extract_tc_id`. Don't ship a wrong inspect_master.

- [ ] **Step 6: Commit**

```bash
git add shared/inspect_master.py tests/test_inspect_master.py
git commit -m "feat(inspect_master): CLI (json stdout)"
```

---

### Task 1.7: Run full test suite + coverage gate

- [ ] **Step 1: Run all tests**

```bash
uv run pytest --cov=shared --cov-report=term-missing
```
Expected: all PASS, coverage ≥ 80% for `shared/inspect_master.py`.

If coverage < 80%, look at the missing lines and either add tests or remove dead code.

- [ ] **Step 2: Commit if any test additions made**

(Skip if no new commits needed.)

---

## Phase 2: `qa:prd-clarify` skill

스킬 번들 자체에는 Python 스크립트 없음 (xlsx I/O 의존 없음). SKILL.md + reference 마크다운 + 예시.

### Task 2.1: Write the shared reference docs

**Files:**
- Create: `shared-reference/domain-glossary.md`
- Create: `shared-reference/ambiguity-checklist.md`

이 둘을 `shared-reference/`에 1차 작성하고, 다음 태스크에서 스킬 번들 안으로 복제. 스펙 §3.2의 PoC 단계 복제 정책 따름.

- [ ] **Step 1: Create shared-reference dir**

```bash
mkdir -p shared-reference
```

- [ ] **Step 2: Write `shared-reference/domain-glossary.md`**

```markdown
# Azar 도메인 용어집

QA 스킬이 PRD/TC를 다룰 때 알아야 할 Azar 핵심 용어. 한국어 표기 우선.

## 화면/탭
- **미러 (Mirror)**: 매치 시작 전 자기 모습 확인 화면. iOS는 일부 버전에서 제거됨.
- **라운지 (Lounge)**: 비실시간으로 다른 사용자 프로필을 둘러보는 탭. "Pick" 기능 포함.
- **매치 (Match)**: 실시간 영상 매칭. 1:1 동시 영상 통화.
- **메시지 (Message)**: 텍스트/이미지 채팅 탭.
- **콜 (Call)**: 음성/영상 통화 탭.
- **상점 (Shop)**: 보석(Gem) / 아이템 / 구독 결제.
- **히스토리 (History)**: 매치/콜 기록 탭.
- **더보기 (More) / 설정**: 계정·알림·환경설정 등 메뉴 모음.
- **새 프로필 (New Profile)**: 프로필 편집 화면.

## 기능 키워드
- **Pre-screening**: 잠재 어뷰저를 매치 전 차단하는 휴리스틱.
- **Reddot**: 탭/메뉴 옆 빨간 점 알림.
- **VIP / XO / Squad / 라이브매치**: 상위/특수 매치 모드.
- **Remote Config**: 서버에서 토글하는 피처 플래그. PRD에 자주 등장 (예: `enablePickLounge`, `showPickLoungeReddot`).
- **mutual / 양방향**: 두 사용자 간 동시 동작이 일어나는 시나리오. 매치/메시지/콜에서 흔함.

## 글로벌/로컬
- **국가 코드**: KR, JP, TW, TH, ID, MY, CN 등. 로그인 수단/UI가 국가별로 다름.
- **VPN/위치 속이기**: QA가 국가 변경 테스트할 때 사용.

## 우선순위 약어
- P1 (핵심) / P2 (일반) / P3 (부가) / P4 (엣지)
```

- [ ] **Step 3: Write `shared-reference/ambiguity-checklist.md`**

```markdown
# PRD 모호점 체크리스트 (qa:prd-clarify)

PRD를 읽을 때 다음 카테고리를 순서대로 점검. 각 카테고리에 해당하는 모호점/누락이 있으면 [심각도] 태그로 분류해서 리포트한다.

## 심각도 정의
- **Blocker**: 이 정보 없이 TC 작성 불가능. PM 답변이 와야 진행 가능.
- **Major**: TC 품질 저하 우려. 답변 없이도 추정으로 진행 가능하지만 후속 수정 비용.
- **Minor**: 명확성 향상 차원. 우선순위 낮음.

## 검사 카테고리 (10개)

### 1. Remote Config 플래그
PRD에 `enableXxx`, `showXxx` 같은 플래그가 언급됐는데 OFF 상태 동작이 미정의됐는가?
- 예: "신규 알고리즘이 활성화되면..." → OFF면? → **Blocker**

### 2. OS 플랫폼
"iOS만", "Android만", "양 플랫폼" 같은 명시가 있는가? 없으면 양쪽 다 동일하다고 가정하는가?
- 명시 없음 → **Major**

### 3. 진입 경로
신규 화면이라면 진입 경로가 한 가지만 기술됐는가? 다른 진입점이 있는가?
- 진입 경로 미명세 → **Major**

### 4. 에러/예외 케이스
- 네트워크 실패
- 서버 응답 timeout
- 권한 거부 (카메라/마이크/위치)
- 잘못된 입력
이 중 누락된 것은? → 누락 카테고리당 **Major**

### 5. 정량 기준
"많은", "충분한 시간 후", "최대" 같은 비정량 표현?
- 정량 기준 모호 → **Minor**

### 6. 정책성 문구
- 결제/환불
- KYC/연령 제한
- 약관 변경
- 데이터 보존/삭제
이 영역 누락? → **Major**

### 7. Mutual 시나리오
PRD가 1인칭 동작만 기술하는데 사실은 두 사용자 간 상호작용? 상대방 측 동작 누락?
- 상대방 측 미기술 → **Major**

### 8. 권한 요청
신규 디바이스 권한 (카메라/위치/푸시 등) 요청 흐름 명세?
- 누락 → **Major**

### 9. 분석 이벤트/로깅
- 신규 이벤트 명세 (이름·파라미터)
- 기존 이벤트 영향
누락? → **Minor** (분석팀이 보강 가능하지만 QA가 미리 짚는 게 좋음)

### 10. A/B 테스트 / 롤아웃
- 트래픽 분배 비율
- 단계적 롤아웃
- 종료 조건
명세 없음 → **Minor**

## 출력 형식
각 발견을 다음 형식으로:

```
[심각도] [카테고리] 짧은 질문 — 왜 중요한지 한 줄
> PRD 인용 (있으면)
```

전부 모은 후, 사용자가 PM에게 그대로 복붙 가능한 톤으로 정리.
```

- [ ] **Step 4: Commit**

```bash
git add shared-reference/
git commit -m "docs: add shared domain-glossary + ambiguity-checklist (qa:prd-clarify reference)"
```

---

### Task 2.2: Build qa-prd-clarify skill bundle

**Files:**
- Create: `skills/qa-prd-clarify/SKILL.md`
- Create: `skills/qa-prd-clarify/reference/domain-glossary.md` (copy)
- Create: `skills/qa-prd-clarify/reference/ambiguity-checklist.md` (copy)
- Create: `skills/qa-prd-clarify/examples/sample-clarify-report.md`

- [ ] **Step 1: Create skill bundle directory + copies**

```bash
mkdir -p skills/qa-prd-clarify/reference skills/qa-prd-clarify/examples
cp shared-reference/domain-glossary.md skills/qa-prd-clarify/reference/
cp shared-reference/ambiguity-checklist.md skills/qa-prd-clarify/reference/
```

- [ ] **Step 2: Write `skills/qa-prd-clarify/SKILL.md`**

```markdown
---
name: qa-prd-clarify
description: Notion PRD를 QA 관점으로 분석해서 모호점·누락 엣지·미정의 상태를 PM에게 돌려보낼 질문 리스트로 추출. 테스트케이스를 짜기 *전* 단계에서 사용. 트리거 예시 — "PRD 검토해줘", "PRD에서 모호한 부분 찾아", "PM에게 물어볼 거 정리".
---

# qa:prd-clarify

PRD가 모호하거나 누락된 정보가 있으면 TC 작성이 어려워지고, 나중에 TC를 다시 짜는 비용이 든다. 이 스킬은 TC 작성 전에 PRD를 QA 관점으로 한 번 검수해서 PM에게 보낼 질문 리스트를 뽑는다.

## 사용 방법

사용자가 다음 중 하나를 줄 때 활성화:
- Notion PRD URL
- PRD 본문을 직접 붙여넣기
- (둘 다 안 주면) "PRD 어디에 있어요?" 묻기

## 워크플로우

### 1. PRD 수집
- Notion URL이면 Notion MCP `notion-fetch`로 페이지 + 자식 블록 + 임베드 객체 fetch.
- 본문이 50단어 미만이면 "PRD가 비어있는 것 같아요. 본문을 붙여 주세요" 안내, 중단.
- 임베드된 Figma 링크/이미지가 있으면 함께 컨텍스트로 활용.

### 2. 체크리스트 적용
`reference/ambiguity-checklist.md`의 10개 카테고리를 순서대로 점검. 각 카테고리마다:
- 해당하는 모호점/누락이 있는가?
- 있다면 심각도(Blocker/Major/Minor) 분류.

도메인 용어는 `reference/domain-glossary.md` 참조 — Azar 특유의 라운지/매치/미러/Pre-screening 등.

### 3. 리포트 작성
다음 형식으로 마크다운 리포트:

```markdown
## PRD 모호점 분석 — <PRD 제목>

### Blocker (TC 작성 불가)
1. [카테고리] 짧은 질문 — 왜 중요한지 한 줄
   > PRD 인용 (있으면)

### Major (TC 품질 저하)
1. [카테고리] ...

### Minor (명확성)
1. [카테고리] ...

---
**PM에게 보내는 메모 (복붙 가능)**

안녕하세요, <PRD 제목> 검토 중 다음 부분이 모호해서 답변 부탁드립니다:

1. ...
2. ...
```

이슈가 0개면 "✅ 검토 완료. 모호점 없음. TC 작성 진행 가능"으로 마무리.

### 4. (옵션) 파일 저장
사용자가 `--save <path>` 또는 "리포트 파일로 저장해줘" 요청 시 마크다운 파일로 저장.

## 출력 톤
- 한국어 (PM이 한국인 가정)
- 정중하지만 단정적 ("…인가요?" 보다 "…미정의됨, 답변 필요")
- PRD 본문 인용은 큰따옴표 또는 인용문 블록

## 예시
`examples/sample-clarify-report.md` 참조.

## 비목표
- TC 자체 작성 (그건 `qa:generate-tc`)
- TC 검수 (그건 `qa:review-tc`)
- PRD 보강안 직접 제안 (질문만 던짐, 답은 PM이)
```

- [ ] **Step 3: Write `skills/qa-prd-clarify/examples/sample-clarify-report.md`**

```markdown
# 예시: qa:prd-clarify 출력

이 파일은 LLM이 출력 톤·구조를 학습하는 few-shot. `tests/fixtures/sample_prd.md` (라운지 신규 추천 알고리즘)를 입력으로 받았을 때 기대되는 리포트.

---

## PRD 모호점 분석 — 라운지 신규 추천 알고리즘

### Blocker (TC 작성 불가)
1. [Remote Config] `enableNewLoungeRecommendation` 플래그가 OFF일 때 동작 미정의. 기존 알고리즘으로 폴백되는가, 아예 추천 섹션이 안 노출되는가?
   > "`enableNewLoungeRecommendation` 플래그가 활성화되면 신규 알고리즘이 동작."

### Major (TC 품질 저하)
1. [에러 케이스] 추천 데이터 fetch 실패 / 빈 결과일 때의 fallback UI 미기술. 빈 화면? 에러 메시지? 기본 추천?
2. [OS 플랫폼] iOS/Android 양쪽 동일한 동작인지 명시 없음. 한쪽만 우선 출시인지?

### Minor (명확성)
1. [정량 기준] 가로 스크롤 카드의 표시 개수·크기 미정의. 디자인 시안에서 확인 가능한가?

---

**PM에게 보내는 메모 (복붙 가능)**

안녕하세요, 라운지 신규 추천 알고리즘 PRD 검토 중 다음 부분이 모호해서 답변 부탁드립니다:

1. (Blocker) `enableNewLoungeRecommendation` 플래그 OFF 시 동작 — 기존 알고리즘으로 폴백되나요, 추천 섹션이 안 노출되나요?
2. (Major) 추천 데이터 fetch 실패/빈 결과 시 fallback UI는 어떻게 되나요?
3. (Major) iOS/Android 동시 출시인지, 한쪽 우선인지 알려주세요.
4. (Minor) 가로 스크롤 카드 개수·크기 디자인 시안 위치 부탁드립니다.

감사합니다.
```

- [ ] **Step 4: Commit**

```bash
git add skills/qa-prd-clarify/
git commit -m "feat(skill): add qa-prd-clarify (PRD ambiguity extraction)"
```

---

### Task 2.3: Smoke test the skill in Claude Code

이건 자동화 안 되는 통합 테스트. 사람이 직접 실행 + 결과 확인.

- [ ] **Step 1: Make the skill discoverable in Claude Code**

```bash
mkdir -p .claude
ln -snf ../skills .claude/skills
```
이제 `.claude/skills/qa-prd-clarify/SKILL.md`로 접근 가능.

- [ ] **Step 2: Restart Claude Code in this project (or reload skills)**

Claude Code 세션을 새로 열면 `qa-prd-clarify` 스킬이 사용 가능 스킬 목록에 떠야 함.

- [ ] **Step 3: Manual smoke test**

Claude Code에서:
1. `/qa-prd-clarify` 호출 (또는 자연어로 "PRD 모호점 찾아줘")
2. 사용자 메시지로 `tests/fixtures/sample_prd.md` 본문을 붙여넣기 (이 단계에서는 Notion 미사용)
3. 결과 리포트 확인:
   - `Blocker` 섹션에 `enableNewLoungeRecommendation` 플래그 OFF 이슈가 있는가?
   - `Major` 섹션에 fallback UI / OS 명시 누락이 있는가?
   - `Minor` 섹션에 카드 개수·크기 모호성이 있는가?
   - PM 메모가 복붙 가능한 톤인가?

미흡한 부분이 있으면 SKILL.md 또는 ambiguity-checklist.md 수정 → 재실행.

- [ ] **Step 4: Document the smoke test result**

`README.md`에 짧게 기록:

```markdown
## Phase 1 검증 (2026-04-30)
- [x] qa-prd-clarify 스킬 ↔ sample_prd.md 입력 → Blocker/Major/Minor 모두 정확히 검출
```

- [ ] **Step 5: Commit**

```bash
git add README.md .claude/
git commit -m "test(qa-prd-clarify): smoke test passed against sample_prd.md"
```

---

### Task 2.4: (선택) Notion MCP로 실제 PRD 검수

Notion MCP가 환경에 연결돼 있으면, 실제 라운지/상점 관련 PRD URL 1개로 동일하게 돌려본다. 이건 사람이 결과를 검수해야 하는 단계라 자동화 X.

- [ ] **Step 1: 실제 PRD URL 1개 준비**

본인 액세스 가능한 Hyperconnect Notion PRD 1건 URL.

- [ ] **Step 2: 스킬 호출 + 검수**

Claude Code에서:
```
/qa-prd-clarify <Notion URL>
```

리포트가 나오면 다음 기준으로 검수:
- Blocker로 분류된 항목이 진짜 TC 작성 불가능한 수준인가? (false positive 비율 < 30%)
- Major/Minor 분류가 합리적인가?
- 누락한 모호점이 있는가? (false negative — 사람이 보면 보이는데 스킬은 놓친)

- [ ] **Step 3: 결과 기반 튜닝**

문제 패턴이 보이면 `ambiguity-checklist.md` 수정 + 재실행. 1~2회 반복으로 만족스러우면 Phase 2 종료.

- [ ] **Step 4: 검증 결과 기록 + 커밋**

```bash
git add shared-reference/ skills/qa-prd-clarify/
git commit -m "docs(qa-prd-clarify): tune checklist after real-PRD smoke test"
```

(만약 튜닝 없었으면 commit 생략.)

---

## Phase 1 완료 체크리스트

- [ ] `uv run pytest --cov=shared` 모두 PASS, 커버리지 80%+
- [ ] `uv run python shared/inspect_master.py "<real master xlsx>"` JSON 출력 정상
- [ ] `qa-prd-clarify` 스킬이 Claude Code 스킬 목록에 등장
- [ ] sample_prd.md fixture로 Blocker/Major/Minor 모두 검출되는 리포트 생성
- [ ] (선택) 실제 Notion PRD 1건으로 검수 완료
- [ ] 모든 변경 git commit + README 갱신

이 단계가 끝나면:
- 즉시 사용 가능한 스킬 1개 (`qa-prd-clarify`) 출시
- 다음 플랜(Phase 2: `qa-generate-tc`)을 위한 공유 인프라(`inspect_master.py`, fixtures, deps) 완비

---

## 다음 단계 — Phase 2 / 3 플랜 작성 가이드

Phase 1 완료 후 별도 플랜 문서로:

**Phase 2 (`qa-generate-tc`)** — 추가될 작업:
- `shared/inspect_master.py`를 `skills/qa-generate-tc/scripts/`로 복제
- TDD: `new_workbook.py` (신규 워크북 생성, 14컬럼 + 줄바꿈 + 섹션)
- TDD: `append_to_master.py` (마스터 복제 → 행 삽입 → TC_ID 증분 → 새 파일 저장)
- SKILL.md (PRD → TC 변환 워크플로우 + 사용자 컨펌 루프)
- reference: template-spec.md, prioritization-guide.md, domain-glossary.md (복제)
- examples: sample-tcs.md
- 통합 smoke test: 가짜 PRD + minimal master → append 동작 확인

**Phase 3 (`qa-review-tc`)** — 추가될 작업:
- `shared/inspect_master.py`를 `skills/qa-review-tc/scripts/`로 복제
- TDD: `validate_format.py` (필수 컬럼/enum/TC_ID 중복 검사)
- TDD: `find_duplicates.py` (탭 내 + 탭 간 중복 — 정규화 후 비교)
- TDD: `extract_tc_table.py` (헤더 매핑 적용된 TC 행 리스트)
- SKILL.md (4 카테고리 검사 워크플로우)
- reference: format-rules.md, coverage-checklist.md, domain-glossary.md (복제)
- examples: sample-review-report.md
- 통합 smoke test: 의도적 이슈가 심어진 fixture xlsx → 모든 이슈 검출 확인
