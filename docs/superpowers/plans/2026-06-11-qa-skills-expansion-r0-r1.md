# QA Skills Expansion R0+R1 Implementation Plan

> **For agentic workers:** REQUIRED: Use superpowers:subagent-driven-development (if subagents available) or superpowers:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.
> TDD 태스크는 @superpowers:test-driven-development 원칙(RED→GREEN, 테스트 먼저 커밋 금지·실패 확인 필수)을 따른다.

**Goal:** 승인된 설계(`docs/plans/2026-06-11-qa-skills-expansion-v2-design.md`)의 Round 0(qa-generate-tc Figma+스냅샷 강화)과 Round 1(qa-risk-analysis, qa-regression-scope, qa-minimal-coverage, qa-release-checklist)을 출시한다.

**Architecture:** 기존 스킬 번들 구조(`skills/<name>/SKILL.md` + `reference/` + `examples/` + `scripts/`)를 그대로 따른다. xlsx를 만지는 부분만 `shared/` 결정론 스크립트(pytest TDD), 판단·문장은 LLM이 SKILL.md 워크플로우로 수행. `scripts/sync_shared.py`가 shared → 번들 동기화를 담당하며, **번들이 shared 파일을 받으려면 같은 이름의 placeholder 파일을 먼저 만들어야 한다**.

**Tech Stack:** Python 3.12, openpyxl, python-calamine, pytest, uv. 새 의존성 없음.

**저장소 규약 (모든 태스크 공통):**
- 원본 xlsx 절대 수정 금지. 출력 경로 충돌 시 `(2)` 접미사 (`shared/new_workbook.py:_resolve_output_path` 재사용).
- 모든 사용자 노출 텍스트는 한국어.
- 커밋 메시지는 `<type>: <description>` (feat/fix/test/docs).
- 각 태스크 끝에 커밋. 작업 디렉토리: `/Users/dongjin/Dropbox/workplace/HyperConnect/poc/qa-skills`.

---

## Round 0 — qa-generate-tc v2 (Figma + PRD 스냅샷)

### Task 1: `reference/figma-usage.md` 작성

**Files:**
- Create: `skills/qa-generate-tc/reference/figma-usage.md`

- [ ] **Step 1: 파일 작성**

`skills/qa-generate-tc/reference/figma-usage.md`:

````markdown
# Figma 입력 사용법

TC 작성 시 Figma 디자인을 보조 입력으로 쓰는 방법. Figma는 *TC 작성의 입력*일 뿐이다 — 디자인 자체의 QA(픽셀 검증, 디자인-구현 일치)는 비목표.

## MCP 감지 (런타임)

특정 서버를 하드코딩하지 않는다. 세션에서 사용 가능한 도구를 확인:

1. 도구 목록(또는 ToolSearch)에서 `figma` 키워드 검색.
2. 대표 계열:
   - **공식 Figma Dev Mode MCP** — 도구 예: `get_code`, `get_image`, `get_variable_defs`. Figma 데스크톱 앱에서 Dev Mode MCP 서버 활성화 필요.
   - **framelink (figma-developer-mcp)** — 도구 예: `get_figma_data`, `download_figma_images`. `FIGMA_API_KEY` 환경 변수 필요 (키를 명령에 하드코딩하지 말 것).
3. 둘 다 없으면 → **막지 않는다.** PRD 단독 모드로 진행하고 안내 한 줄:
   "Figma MCP를 연결하면 UI 상태 커버리지가 좋아집니다. 연결 방법: 공식 Dev Mode MCP(Figma 앱 설정) 또는 framelink MCP."

## URL 파싱

- `https://www.figma.com/design/<FILE_KEY>/<name>?node-id=<NODE_ID>` 형태.
- `FILE_KEY`와 `node-id`를 추출해 도구 인자로 사용. node-id의 `-`는 API에 따라 `:`로 바꿔야 할 수 있음.

## TC에 반영하는 정보

| Figma에서 읽는 것 | TC 반영 위치 |
|---|---|
| 프레임/화면 이름, 네비게이션 흐름 | Test Item, Test Step (화면 이동 단계 구체화) |
| 버튼·라벨 등 실제 텍스트 | Test Step·Expected Result (실제 문구 그대로) |
| 상태별 프레임 (빈 상태, 에러, 로딩, 비활성) | 상태별 TC 추가 |
| 분기 화면 (iOS/Android 별도 프레임) | OS 컬럼 |

## PRD ↔ 디자인 불일치 규칙

- 디자인에만 있고 PRD에 없는 상태/요소 → TC는 만들되 **Comment에 "PRD 미정의, 디자인 기준" 명시**.
- PRD에 있는데 디자인에 없는 흐름 → TC는 PRD 기준으로 만들고 Comment에 "디자인 미반영 — 확인 필요".
- 텍스트가 서로 다르면 → Expected Result는 PRD 우선, Comment에 디자인 문구 병기.
````

- [ ] **Step 2: 검증**

Run: `rg -l "figma-usage" skills/qa-generate-tc/`
Expected: `skills/qa-generate-tc/reference/figma-usage.md` 출력.

- [ ] **Step 3: 커밋**

```bash
git add skills/qa-generate-tc/reference/figma-usage.md
git commit -m "docs(generate-tc): add figma-usage reference"
```

### Task 2: `qa-generate-tc` SKILL.md 확장 (Figma + 스냅샷)

**Files:**
- Modify: `skills/qa-generate-tc/SKILL.md`

- [ ] **Step 1: frontmatter description 갱신**

기존 3행:
```yaml
description: Notion PRD를 분석해서 표준 14컬럼 QA 테스트케이스를 xlsx로 생성. 신규 시트 모드 또는 기존 마스터 xlsx에 append 모드 지원. 사람 컨펌 루프 필수. 트리거 — "테스트 케이스 생성", "TC 만들어", "PRD에서 TC 뽑아", "/qa:generate-tc".
```
다음으로 교체:
```yaml
description: Notion PRD(+옵션 Figma 디자인)를 분석해서 표준 14컬럼 QA 테스트케이스를 xlsx로 생성. 신규 시트 모드 또는 기존 마스터 xlsx에 append 모드 지원. 사람 컨펌 루프 필수. 트리거 — "테스트 케이스 생성", "TC 만들어", "PRD에서 TC 뽑아", "/qa:generate-tc".
```

- [ ] **Step 2: 섹션 1 끝에 스냅샷 단계 추가**

`### 1. PRD 수집` 섹션의 마지막 항목(`qa:prd-clarify` 권유 줄) 뒤에 추가:

```markdown
- fetch 성공 직후 PRD 본문을 md 스냅샷으로 저장: 기본 `./prd-snapshots/<기능명>-<YYYYMMDD>.md` (사용자가 다른 경로를 지정하면 그에 따름. 디렉토리 없으면 생성, 날짜는 `date '+%Y%m%d'`로 구함 — 암산 금지). 저장 경로를 사용자에게 알린다. 이 스냅샷은 나중에 `qa:prd-diff`가 PRD 변경분 분석에 사용한다.
```

- [ ] **Step 3: 섹션 1과 2 사이에 Figma 보강 섹션 추가**

```markdown
### 1.5 Figma 보강 (옵션)
- 사용자가 Figma 링크를 줬거나 PRD에 Figma 임베드가 있으면 → 연결된 Figma MCP 도구를 감지 (도구명에 `figma` 포함 여부). 사용법·URL 파싱·반영 규칙은 `reference/figma-usage.md` 참조.
- 연결됨: 프레임 구조·실제 텍스트·상태별 화면(빈/에러/로딩)을 읽어 Test Step·Expected Result를 화면 기준으로 구체화. 디자인에만 있는 상태는 TC로 만들되 Comment에 "PRD 미정의, 디자인 기준" 명시.
- 미연결: 진행을 막지 않는다. "Figma MCP를 연결하면 UI 상태 커버리지가 좋아집니다" 한 줄 안내 후 PRD 단독 모드.
```

- [ ] **Step 4: 검증**

Run: `rg "1.5 Figma|prd-snapshots" skills/qa-generate-tc/SKILL.md`
Expected: 두 패턴 모두 매치.

- [ ] **Step 5: 커밋**

```bash
git add skills/qa-generate-tc/SKILL.md
git commit -m "feat(generate-tc): add figma input + prd snapshot steps"
```

### Task 3: Round 0 smoke + README

**Files:**
- Modify: `README.md`

- [ ] **Step 1: fresh subagent smoke**

서브에이전트(일반 목적, 세션 컨텍스트 없이)에게 다음만 제공: `skills/qa-generate-tc/SKILL.md` 경로 + `tests/fixtures/sample_prd.md` 경로 + "이 SKILL.md 워크플로우를 따라 TC 초안 단계까지 시뮬레이션하라 (xlsx 생성 전 단계까지). Figma MCP는 연결돼 있지 않다."

확인 항목:
- PRD 스냅샷 저장 단계를 수행(또는 수행 계획 명시)하는가
- Figma 미연결 시 한 줄 안내 후 PRD 단독 모드로 자연스럽게 진행하는가 (막히면 FAIL)
- 기존 출력 품질 회귀 없음 (P1~P4 배분, Remote Config 분기, 한국어 톤)

- [ ] **Step 2: README 갱신**

`## 스킬 목록`의 generate-tc 줄을 다음으로 교체:
```markdown
- `qa-generate-tc` — Notion PRD(+옵션 Figma)로 TC xlsx 생성 (Phase 2 + R0 강화, 출시 ✅)
```
`## 검증 이력`에 추가:
```markdown
### Round 0 검증 (2026-06-11)
- [x] `qa:generate-tc` v2 — Figma 미연결 graceful fallback + PRD 스냅샷 단계, fresh subagent smoke PASS
```
(smoke 실패 항목이 있으면 수정 후 재실행하고, 통과한 내용만 기록한다.)

- [ ] **Step 3: 커밋**

```bash
git add README.md
git commit -m "docs: record round 0 verification (generate-tc v2)"
```

---

## Round 1 — 전략 코어 4종

### Task 4: `shared-reference/risk-taxonomy.md` 작성

**Files:**
- Create: `shared-reference/risk-taxonomy.md`

- [ ] **Step 1: 파일 작성**

````markdown
# 리스크 분류 체계 (risk taxonomy)

qa-risk-analysis · qa-regression-scope · qa-minimal-coverage · qa-exploratory-charter가 공유하는 분류. 영역별로 "무엇이 깨지면 어떤 피해인가"를 기준으로 영향도를 매긴다.

| 영역 | 대표 키워드 | 기본 영향도 | 비고 |
|---|---|---|---|
| 핵심 사용자 플로우 | 온보딩, 메인 진입, 매치 시작 | Blocker | 깨지면 서비스 사용 불가 |
| 결제·수익화 | 결제, 구매, 환불, 구독, 젬 | Blocker | 금전 피해·CS 폭증 |
| 매치·콜·실시간 | 매치, 콜, 라이브, 메시지, 영상 | Blocker~Major | 코어 가치. 양방향(mutual) 검증 필요 |
| 신고·차단·모더레이션 | 신고, 차단, 제재, 블라인드 | Blocker~Major | 안전·법적 리스크 |
| 인증·권한·프라이버시 | 로그인, 탈퇴, 권한, 개인정보 | Major | 데이터 유출·계정 피해 |
| Remote Config·롤아웃·실험 | remote config, 플래그, 실험, 어드민 | Major | on/off 양쪽 + 기본값 검증 |
| 크로스플랫폼·OS 분기 | iOS, Android, 버전 분기 | Major~Minor | 한쪽만 깨지는 회귀 빈발 |
| 마이그레이션·하위호환 | 마이그레이션, 구버전, 업그레이드 | Major | 기존 사용자 데이터 보존 |
| UI·카피 | 라벨, 문구, 정렬, 다크모드 | Minor | 기능 영향 없으면 Minor |

## 발생가능성 판단 힌트
- 이번 릴리즈에서 **변경된 코드 경로**에 가까울수록 높음.
- 상태 조합이 많을수록(로그인 상태 × OS × 플래그) 높음.
- 외부 의존(결제 모듈, 네트워크 품질)이 있으면 높음.

## 등급 = 영향도 × 발생가능성
- Blocker: 출시 차단. 즉시 보고.
- Major: 출시 전 수정 또는 명시적 risk-accept 필요.
- Minor: known issue로 출시 가능.
- Info: 관찰만.
````

- [ ] **Step 2: 커밋**

```bash
git add shared-reference/risk-taxonomy.md
git commit -m "docs: add shared risk taxonomy (round 1)"
```

### Task 5: `summary_xlsx` 실패 테스트 (RED)

**Files:**
- Create: `tests/test_summary_xlsx.py`

- [ ] **Step 1: 테스트 작성**

```python
"""Tests for shared/summary_xlsx.py."""
from pathlib import Path

import pytest
from openpyxl import load_workbook

from shared.summary_xlsx import write_summary_workbook

SHEETS = [
    {"title": "리스크 매트릭스",
     "headers": ["영역", "등급"],
     "rows": [["결제", "Blocker"], ["UI 카피", "Minor"]]},
    {"title": "테스트 포커스",
     "headers": ["영역", "권장 TC"],
     "rows": [["결제", "구매 실패 복구"]]},
]


def test_writes_sheets_in_order(tmp_path: Path):
    out = write_summary_workbook(SHEETS, tmp_path / "summary.xlsx")
    wb = load_workbook(out)
    assert wb.sheetnames == ["리스크 매트릭스", "테스트 포커스"]


def test_writes_headers_and_rows(tmp_path: Path):
    out = write_summary_workbook(SHEETS, tmp_path / "summary.xlsx")
    ws = load_workbook(out)["리스크 매트릭스"]
    assert [c.value for c in ws[1]] == ["영역", "등급"]
    assert [c.value for c in ws[2]] == ["결제", "Blocker"]
    assert [c.value for c in ws[3]] == ["UI 카피", "Minor"]


def test_collision_appends_suffix(tmp_path: Path):
    first = write_summary_workbook(SHEETS, tmp_path / "summary.xlsx")
    second = write_summary_workbook(SHEETS, tmp_path / "summary.xlsx")
    assert first.name == "summary.xlsx"
    assert second.name == "summary (2).xlsx"


def test_empty_sheets_raises(tmp_path: Path):
    with pytest.raises(ValueError):
        write_summary_workbook([], tmp_path / "summary.xlsx")
```

- [ ] **Step 2: 실패 확인**

Run: `uv run pytest tests/test_summary_xlsx.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'shared.summary_xlsx'`

- [ ] **Step 3: 커밋**

```bash
git add tests/test_summary_xlsx.py
git commit -m "test(summary_xlsx): sheet order + headers + collision + empty guard (RED)"
```

### Task 6: `shared/summary_xlsx.py` 구현 (GREEN)

**Files:**
- Create: `shared/summary_xlsx.py`

- [ ] **Step 1: 구현**

```python
"""Write a summary workbook from a list of sheet specs.

Generic exporter for md+xlsx skills (qa-risk-analysis, qa-regression-scope).

CLI:
    python summary_xlsx.py --sheets sheets.json --output out.xlsx

sheets.json schema:
    {"sheets": [{"title": "리스크 매트릭스", "headers": ["영역", ...],
                 "rows": [["결제", ...], ...]}, ...]}

If output path already exists, appends "(2)", "(3)", ... suffix.
Prints the actual output path as the last stdout line.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from new_workbook import HEADER_FILL, HEADER_FONT, WRAP, _resolve_output_path  # noqa: E402

from openpyxl import Workbook  # noqa: E402


def write_summary_workbook(sheets: list[dict], output: Path) -> Path:
    """Create an xlsx with one tab per sheet spec. Returns actual path written."""
    if not sheets:
        raise ValueError("sheets must not be empty")
    actual_output = _resolve_output_path(output)

    wb = Workbook()
    wb.remove(wb.active)
    for spec in sheets:
        ws = wb.create_sheet(spec["title"])
        for col_idx, name in enumerate(spec.get("headers", []), start=1):
            cell = ws.cell(row=1, column=col_idx, value=name)
            cell.font = HEADER_FONT
            cell.fill = HEADER_FILL
            cell.alignment = WRAP
        for row_idx, row in enumerate(spec.get("rows", []), start=2):
            for col_idx, value in enumerate(row, start=1):
                ws.cell(row=row_idx, column=col_idx, value=value).alignment = WRAP

    actual_output.parent.mkdir(parents=True, exist_ok=True)
    wb.save(actual_output)
    return actual_output


def main() -> None:
    parser = argparse.ArgumentParser(description="Write a summary workbook.")
    parser.add_argument("--sheets", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    data = json.loads(args.sheets.read_text(encoding="utf-8"))
    actual = write_summary_workbook(data.get("sheets", []), args.output)
    print(f"Wrote {actual}")
    print(actual)


if __name__ == "__main__":
    main()
```

- [ ] **Step 2: 통과 확인**

Run: `uv run pytest tests/test_summary_xlsx.py -v`
Expected: 4 PASS

- [ ] **Step 3: 전체 회귀 확인**

Run: `uv run pytest`
Expected: 50 passed (기존 46 + 4)

- [ ] **Step 4: 커밋**

```bash
git add shared/summary_xlsx.py
git commit -m "feat(summary_xlsx): generic summary workbook exporter"
```

### Task 7: `qa-risk-analysis` 번들

**Files:**
- Create: `skills/qa-risk-analysis/SKILL.md`
- Create: `skills/qa-risk-analysis/reference/risk-taxonomy.md` (빈 placeholder → sync로 채움)
- Create: `skills/qa-risk-analysis/scripts/summary_xlsx.py` (빈 placeholder → sync로 채움)
- Create: `skills/qa-risk-analysis/scripts/new_workbook.py` (빈 placeholder — summary_xlsx가 import)
- Create: `skills/qa-risk-analysis/examples/sample-risk-report.md`

- [ ] **Step 1: SKILL.md 작성**

````markdown
---
name: qa-risk-analysis
description: PRD나 변경 요약을 QA 관점으로 분석해 고위험 영역, 테스트 집중 범위, 릴리즈 리스크를 심각도별 리스크 매트릭스(md + 요약 xlsx)로 정리. TC 작성 전 또는 회귀 범위 결정 전에 사용. 트리거 — "리스크 분석", "어디가 위험해", "테스트 어디에 집중", "/qa:risk-analysis".
---

# qa:risk-analysis

릴리즈/기능의 고위험 영역을 식별해 테스트 집중 범위를 제안한다.

## 입력
- PRD (Notion URL 또는 본문 붙여넣기) 또는 변경 요약 (필수)
- 도메인 노트, 이전 장애 이력 (옵션)

## 워크플로우

### 1. 입력 수집
- Notion URL이면 MCP로 fetch. 본문 50단어 미만이면 변경 요약을 직접 요청.
- 입력이 PRD인지 변경 요약인지 구분해 리포트에 명시.

### 2. 리스크 식별
`reference/risk-taxonomy.md`의 영역별로 점검:
- 이번 변경이 닿는 영역 → 발생가능성 상향.
- 영역별 영향도 × 발생가능성 = 등급 (Blocker/Major/Minor/Info).
- 근거 없는 추정 금지 — PRD에 없는 내용은 "가정"으로 분리.

### 3. 리포트 출력 (md)
```markdown
## 리스크 분석 — <기능/릴리즈 이름>
### 요약
(한 줄 결론: 최고 등급 리스크와 권장 집중 영역)
### 리스크 매트릭스
| # | 영역 | 리스크 | 영향도 | 발생가능성 | 등급 | 권장 테스트 포커스 |
### 가정
(입력에 없어서 가정한 것들 — PM 확인 필요 항목 표시)
```

### 4. 요약 xlsx 생성 (사용자가 원하면)
매트릭스를 JSON으로 만들어:
```bash
uv run python scripts/summary_xlsx.py --sheets /tmp/risk_sheets.json --output <out>.xlsx
```
sheets는 2개: "리스크 매트릭스", "가정". stdout 마지막 줄이 실제 출력 경로.

## 비목표
- TC 작성 (그건 `qa:generate-tc`), 회귀 범위 결정 (그건 `qa:regression-scope`)
- 코드 레벨 정적 분석

## 예시
`examples/sample-risk-report.md` 참조.
````

- [ ] **Step 2: 예시 작성**

`examples/sample-risk-report.md`: 가상의 "라운지 선물하기" 기능에 대해 위 출력 포맷 그대로 Blocker 1(결제 이중 차감) / Major 2(Remote Config off 시 진입점 잔존, iOS 권한 거부 플로우) / Minor 1(다크모드 카피 대비) / 가정 2건을 채운 실제 모양의 리포트.

- [ ] **Step 3: placeholder 생성 + sync**

```bash
mkdir -p skills/qa-risk-analysis/reference skills/qa-risk-analysis/scripts skills/qa-risk-analysis/examples
touch skills/qa-risk-analysis/reference/risk-taxonomy.md
touch skills/qa-risk-analysis/scripts/summary_xlsx.py
touch skills/qa-risk-analysis/scripts/new_workbook.py
uv run python scripts/sync_shared.py
```
Expected: 세 placeholder 모두 `updated:` 로 채워짐.

- [ ] **Step 4: 검증**

Run: `uv run python skills/qa-risk-analysis/scripts/summary_xlsx.py --help && uv run python scripts/sync_shared.py --check`
Expected: help 출력 + exit 0.

- [ ] **Step 5: 커밋**

```bash
git add skills/qa-risk-analysis
git commit -m "feat(skill): add qa-risk-analysis bundle"
```

### Task 8: `qa-regression-scope` 번들

**Files:**
- Create: `skills/qa-regression-scope/SKILL.md`
- Create: `skills/qa-regression-scope/reference/scope-rules.md`
- Create: `skills/qa-regression-scope/reference/risk-taxonomy.md` (placeholder)
- Create: `skills/qa-regression-scope/scripts/{summary_xlsx,new_workbook,extract_tc_table,inspect_master}.py` (placeholder 4개)
- Create: `skills/qa-regression-scope/examples/sample-regression-scope.md`

- [ ] **Step 1: SKILL.md 작성**

````markdown
---
name: qa-regression-scope
description: PRD/변경 요약과 기존 TC xlsx를 바탕으로 이번 릴리즈에서 필수로 돌릴 회귀 범위와 생략 가능한 범위를 근거와 함께 정리 (md + 요약 xlsx). 릴리즈 회귀 계획 수립 시 사용. 트리거 — "회귀 범위", "리그레션 어디까지", "/qa:regression-scope".
---

# qa:regression-scope

이번 변경에 대해 기존 TC 중 무엇을 다시 돌릴지 결정한다.

## 입력
- PRD 또는 변경 요약 (필수)
- 기존 TC xlsx (필수 — 탭 단위로 분석)
- 리스크 분석 리포트 (`qa:risk-analysis` 출력, 강력 권장), 이전 릴리즈 노트 (옵션)

## 워크플로우

### 1. 변경 이해
변경이 닿는 도메인 영역을 `reference/risk-taxonomy.md` 기준으로 목록화.

### 2. 기존 TC 인벤토리
```bash
uv run python scripts/inspect_master.py <master>.xlsx          # 탭 목록
uv run python scripts/extract_tc_table.py <master>.xlsx --tab <name>  # 탭별 TC
```
탭·섹션 단위로 "이 영역이 변경의 영향권인가"를 판단.

### 3. 범위 판정 (`reference/scope-rules.md` 적용)
- **Required**: 변경 직접 영향권 + Blocker 영역 (결제·신고·매치·핵심 플로우는 간접 영향도 포함)
- **Optional**: 간접 영향권 (시간 남으면)
- **Skipped**: 무관 영역 — 반드시 생략 근거 + 잔여 리스크 기록
- **Open Questions**: 판정 불가 항목 — PM/개발 확인 필요

### 4. 출력
md 리포트 (Required/Optional/Skipped/Open Questions, 각 항목에 탭·섹션·근거) + 사용자가 원하면 요약 xlsx:
```bash
uv run python scripts/summary_xlsx.py --sheets /tmp/scope_sheets.json --output <out>.xlsx
```

## 비목표
- 개별 TC 선별·최적화 (그건 `qa:minimal-coverage`)
- TC 신규 작성

## 예시
`examples/sample-regression-scope.md` 참조.
````

- [ ] **Step 2: `reference/scope-rules.md` 작성**

강제 포함 규칙(변경 영역 + Blocker 영역 + 공유 컴포넌트), 선택 포함 규칙(간접 의존, 최근 2릴리즈 내 버그 발생 영역), 안전 생략 규칙(독립 모듈 + 최근 N릴리즈 무변경 + Minor 영역), "생략에는 반드시 근거와 잔여 리스크" 원칙을 표로 정리.

- [ ] **Step 3: 예시 작성**

`examples/sample-regression-scope.md`: "라운지 선물하기" 변경에 대해 Required(Shop 결제 탭 전체, Lounge 진입 섹션) / Optional(More 설정) / Skipped(login — 근거: 인증 경로 무변경) / Open Questions 1건.

- [ ] **Step 4: placeholder + sync + 검증 + 커밋**

```bash
mkdir -p skills/qa-regression-scope/{reference,scripts,examples}
touch skills/qa-regression-scope/reference/risk-taxonomy.md
touch skills/qa-regression-scope/scripts/{summary_xlsx,new_workbook,extract_tc_table,inspect_master}.py
uv run python scripts/sync_shared.py
uv run python scripts/sync_shared.py --check   # exit 0 확인
git add skills/qa-regression-scope
git commit -m "feat(skill): add qa-regression-scope bundle"
```

### Task 9: `select_minimal_coverage` 실패 테스트 (RED)

**Files:**
- Create: `tests/test_select_minimal_coverage.py`

- [ ] **Step 1: 테스트 작성**

```python
"""Tests for shared/select_minimal_coverage.py (in-memory rows, no xlsx)."""
import copy

from shared.select_minimal_coverage import select_minimal_coverage


def _row(priority="P3", summary="", os="", steps="step 1", rc=""):
    return {
        "Priority": priority, "OS": os, "Test Item": "", "TC_ID": "",
        "Test Summary": summary, "Remote Config / Admin": rc,
        "Pre-condition": "", "Test Step": steps, "Expected Result": "ok",
        "Comment": "",
    }


def test_force_includes_p1_and_high_risk_cases():
    rows = [
        _row("P1", "메인 진입"),
        _row("P3", "결제 실패 시 복구"),
        _row("P4", "버튼 라벨 확인"),
    ]
    result = select_minimal_coverage(rows)
    selected_idx = {s["index"] for s in result["selected"]}
    assert 0 in selected_idx          # P1 강제 포함
    assert 1 in selected_idx          # 고위험 키워드(결제) 강제 포함
    forced_reasons = [r for s in result["selected"] if s["index"] in (0, 1)
                      for r in s["reasons"]]
    assert any("강제 포함" in r for r in forced_reasons)


def test_prefers_case_with_higher_unique_risk_coverage():
    rows = [
        _row("P2", "설정 진입", os="iOS"),
        _row("P2", "설정 진입 재확인", os="iOS"),   # 동일 태그 → 중복
        _row("P2", "설정 진입", os="And"),          # 새 태그(os:And)
    ]
    result = select_minimal_coverage(rows)
    selected_idx = [s["index"] for s in result["selected"]]
    assert selected_idx[0] == 0 or selected_idx[0] == 2
    assert 1 not in selected_idx      # 중복 태그 행은 선택 안 됨
    assert {0, 2} <= set(selected_idx)


def test_penalizes_redundant_cases():
    rows = [
        _row("P2", "프로필 편집", os="iOS"),
        _row("P2", "프로필 편집 다시", os="iOS"),
    ]
    result = select_minimal_coverage(rows)
    assert len(result["selected"]) == 1
    leftovers = result["next_best"] + result["excluded"]
    assert any(item["index"] == 1 for item in leftovers)


def test_respects_max_cases():
    rows = [_row("P1", f"핵심 플로우 {i}") for i in range(5)]
    result = select_minimal_coverage(rows, max_cases=3)
    assert len(result["selected"]) == 3
    assert any("max-cases" in a for a in result["assumptions"])


def test_returns_next_best_and_excluded_with_reasons():
    rows = [_row("P2", "설정 진입", os="iOS")] + [
        _row("P4", f"라벨 확인 {i}") for i in range(8)
    ]
    result = select_minimal_coverage(rows, next_best_count=2)
    assert len(result["next_best"]) == 2
    assert result["excluded"]
    for e in result["excluded"]:
        assert e["reason"]
        assert "residual_risk" in e


def test_input_rows_not_mutated():
    rows = [_row("P1", "결제 진입"), _row("P3", "라벨")]
    snapshot = copy.deepcopy(rows)
    select_minimal_coverage(rows)
    assert rows == snapshot
```

- [ ] **Step 2: 실패 확인**

Run: `uv run pytest tests/test_select_minimal_coverage.py -v`
Expected: FAIL — `ModuleNotFoundError`

- [ ] **Step 3: 커밋**

```bash
git add tests/test_select_minimal_coverage.py
git commit -m "test(select_minimal_coverage): force-include + coverage + redundancy + max-cases (RED)"
```

### Task 10: `shared/select_minimal_coverage.py` 구현 (GREEN)

**Files:**
- Create: `shared/select_minimal_coverage.py`

- [ ] **Step 1: 구현**

```python
"""Select a minimal TC execution set that maximizes risk coverage.

Deterministic scoring over canonical row dicts:

    score = risk_score + coverage_gain - execution_cost - redundancy_penalty

Force-include: Priority == "P1" or any high-risk keyword match.
Input rows are never mutated.

CLI (full pipeline: extract → select → export, requires sibling scripts):
    python select_minimal_coverage.py --source <tc.xlsx> --tab <tab> \
        --output <out.xlsx> [--max-cases N] [--next-best N]
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

PRIORITY_BASE = {"P1": 3.0, "P2": 2.0, "P3": 1.0, "P4": 0.5}

HIGH_RISK_KEYWORDS = (
    "결제", "구매", "환불", "구독", "신고", "차단", "매치", "콜", "라이브",
    "권한", "로그인", "탈퇴", "remote config", "어드민",
)

_TAG_FIELDS = ("Test Summary", "Test Item", "Remote Config / Admin", "Pre-condition")


def _text_of(row: dict) -> str:
    return " ".join(str(row.get(f) or "") for f in _TAG_FIELDS).lower()


def risk_tags(row: dict) -> frozenset[str]:
    text = _text_of(row)
    tags = {kw for kw in HIGH_RISK_KEYWORDS if kw in text}
    os_val = str(row.get("OS") or "").strip()
    if os_val:
        tags.add(f"os:{os_val}")
    if str(row.get("Remote Config / Admin") or "").strip():
        tags.add("remote-config")
    return frozenset(tags)


def risk_score(row: dict) -> float:
    base = PRIORITY_BASE.get(str(row.get("Priority") or "").strip(), 1.0)
    bonus = 1.0 if any(kw in _text_of(row) for kw in HIGH_RISK_KEYWORDS) else 0.0
    return base + bonus


def execution_cost(row: dict) -> float:
    steps = str(row.get("Test Step") or "")
    n_lines = max(1, len([ln for ln in steps.splitlines() if ln.strip()]))
    cost = 0.1 * n_lines
    if str(row.get("Remote Config / Admin") or "").strip():
        cost += 0.5  # 플래그 셋업 부담
    return cost


def is_forced(row: dict) -> bool:
    if str(row.get("Priority") or "").strip() == "P1":
        return True
    return any(kw in _text_of(row) for kw in HIGH_RISK_KEYWORDS)


def _marginal(row: dict, covered: frozenset[str]) -> tuple[float, float]:
    """Returns (score, coverage_gain) against the already-covered tag set."""
    tags = risk_tags(row)
    gain = 0.5 * len(tags - covered)
    overlap = len(tags & covered) / len(tags) if tags else 0.0
    score = risk_score(row) + gain - execution_cost(row) - 1.0 * overlap
    return score, gain


def select_minimal_coverage(rows: list[dict], max_cases: int | None = None,
                            next_best_count: int = 5) -> dict:
    """Greedy risk-coverage selection.

    Returns {"selected", "excluded", "next_best", "assumptions"}; each selected
    item is {"index", "row", "score", "reasons", "new_tags"}.
    """
    assumptions = [
        "score = risk_score + coverage_gain - execution_cost - redundancy_penalty",
        "강제 포함: Priority P1 또는 고위험 키워드 (결제·신고·매치·콜·권한·Remote Config 등)",
    ]
    selected: list[dict] = []
    covered: frozenset[str] = frozenset()

    forced: list[tuple[int, dict]] = []
    remaining: list[tuple[int, dict]] = []
    for idx, row in enumerate(rows):
        (forced if is_forced(row) else remaining).append((idx, row))

    def pick(idx: int, row: dict, reasons: list[str]) -> None:
        nonlocal covered, selected
        score, _gain = _marginal(row, covered)
        new_tags = sorted(risk_tags(row) - covered)
        selected = selected + [{"index": idx, "row": row, "score": round(score, 2),
                                "reasons": reasons, "new_tags": new_tags}]
        covered = covered | risk_tags(row)

    overflow_noted = False
    for idx, row in sorted(forced, key=lambda p: (-risk_score(p[1]), p[0])):
        if max_cases is not None and len(selected) >= max_cases:
            if not overflow_noted:
                assumptions = assumptions + [
                    f"max-cases={max_cases} 제한으로 강제 포함 대상 일부 제외 — 잔여 리스크 확인 필요"]
                overflow_noted = True
            remaining = remaining + [(idx, row)]
            continue
        reason = ("강제 포함: P1" if str(row.get("Priority") or "").strip() == "P1"
                  else "강제 포함: 고위험 키워드")
        pick(idx, row, [reason])

    while remaining and (max_cases is None or len(selected) < max_cases):
        scored = sorted(((idx, row, *_marginal(row, covered)) for idx, row in remaining),
                        key=lambda t: (-t[2], t[0]))
        positive = [t for t in scored if t[3] > 0 and t[2] > 0]
        if not positive:
            break
        idx, row, _score, _gain = positive[0]
        pick(idx, row, [f"커버 확대: 신규 리스크 태그 {len(risk_tags(row) - covered)}개"])
        remaining = [(i, r) for i, r in remaining if i != idx]

    leftovers = sorted(((idx, row, *_marginal(row, covered)) for idx, row in remaining),
                       key=lambda t: (-t[2], t[0]))
    next_best = [{"index": i, "row": r, "score": round(s, 2),
                  "new_tags": sorted(risk_tags(r) - covered)}
                 for i, r, s, _g in leftovers[:next_best_count]]

    excluded = []
    for i, r, _s, _g in leftovers[next_best_count:]:
        tags = risk_tags(r)
        if tags and tags <= covered:
            reason = "선택된 TC가 동일 리스크를 이미 커버 (중복)"
        elif max_cases is not None and len(selected) >= max_cases:
            reason = f"max-cases={max_cases} 도달"
        else:
            reason = "점수 미달 (리스크 대비 실행 비용)"
        excluded.append({"index": i, "row": r, "reason": reason,
                         "residual_risk": sorted(tags - covered)})

    return {"selected": selected, "excluded": excluded,
            "next_best": next_best, "assumptions": assumptions}


def main() -> None:
    parser = argparse.ArgumentParser(description="Select + export minimal coverage set.")
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--tab", type=str, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--max-cases", type=int, default=None)
    parser.add_argument("--next-best", type=int, default=5)
    args = parser.parse_args()

    from export_minimal_coverage import export_minimal_coverage  # noqa: PLC0415
    from extract_tc_table import extract_tc_table  # noqa: PLC0415
    from inspect_master import parse_tab_meta  # noqa: PLC0415

    meta = parse_tab_meta(args.source, args.tab)
    columns = list(meta["columns"].keys())
    rows = extract_tc_table(args.source, args.tab)
    selection = select_minimal_coverage(rows, max_cases=args.max_cases,
                                        next_best_count=args.next_best)
    actual = export_minimal_coverage(selection, columns, args.output)
    print(f"Selected {len(selection['selected'])} / {len(rows)} TC")
    print(actual)


if __name__ == "__main__":
    main()
```

- [ ] **Step 2: 통과 확인**

Run: `uv run pytest tests/test_select_minimal_coverage.py -v`
Expected: 6 PASS. 실패하면 구현을 고친다 (테스트 수정 금지 — 테스트가 틀린 경우만 예외, 사유 커밋 메시지에 명시).

- [ ] **Step 3: 커밋**

```bash
git add shared/select_minimal_coverage.py
git commit -m "feat(select_minimal_coverage): greedy risk-coverage scoring + selection"
```

### Task 11: `export_minimal_coverage` 실패 테스트 (RED)

**Files:**
- Create: `tests/test_export_minimal_coverage.py`

- [ ] **Step 1: 테스트 작성**

```python
"""Tests for shared/export_minimal_coverage.py."""
from pathlib import Path

from openpyxl import load_workbook

from shared.export_minimal_coverage import ANALYSIS_COLUMNS, export_minimal_coverage
from shared.select_minimal_coverage import select_minimal_coverage

EXPECTED_SHEETS = ["Selected TC", "Coverage Summary", "Excluded TC",
                   "Next Best", "Assumptions"]


def _mutual_row(tc_id, summary, priority="P2", os="", item="매치"):
    """Mutual 탭 형태: 14컬럼 변형 + A/B 컬럼, Test Step → Test Reproduce.

    item 기본값 "매치"는 고위험 키워드라 강제 포함됨 — 비강제 행이 필요한
    테스트는 비위험 값(예: "설정")을 넘길 것.
    """
    return {
        "Priority": priority, "OS": os, "Test Item": item, "TC_ID": tc_id,
        "Test Summary": summary, "Remote Config / Admin": "",
        "Pre-condition": "", "A": "발신", "B": "수신",
        "Test Reproduce": "1. A가 매치 시작", "Expected Result": "ok",
        "Result": "", "Jira no.": "", "Comment": "",
    }


def _selection(rows):
    return select_minimal_coverage(rows)


COLUMNS = ["Priority", "OS", "Test Item", "TC_ID", "Test Summary",
           "Remote Config / Admin", "Pre-condition", "A", "B",
           "Test Reproduce", "Expected Result", "Result", "Jira no.", "Comment"]


def test_writes_five_sheets(tmp_path: Path):
    rows = [_mutual_row("1-1", "매치 성사"), _mutual_row("1-2", "매치 거절")]
    out = export_minimal_coverage(_selection(rows), COLUMNS, tmp_path / "min.xlsx")
    assert load_workbook(out).sheetnames == EXPECTED_SHEETS


def test_preserves_all_source_columns_and_tc_id(tmp_path: Path):
    rows = [_mutual_row("1-1", "매치 성사")]
    out = export_minimal_coverage(_selection(rows), COLUMNS, tmp_path / "min.xlsx")
    ws = load_workbook(out)["Selected TC"]
    headers = [c.value for c in ws[1]]
    assert headers == COLUMNS + list(ANALYSIS_COLUMNS)   # mutual A/B 포함 범용 보존
    row2 = {h: c.value for h, c in zip(headers, ws[2])}
    assert row2["TC_ID"] == "1-1"                        # 원본 TC_ID 유지
    assert row2["실행 순서"] == 1


def test_excluded_sheet_has_reason(tmp_path: Path):
    rows = [_mutual_row("1-1", "매치 성사")] + [
        _mutual_row(f"2-{i}", "라벨 확인", priority="P4", item="설정") for i in range(8)]
    selection = select_minimal_coverage(rows, next_best_count=1)
    out = export_minimal_coverage(selection, COLUMNS, tmp_path / "min.xlsx")
    ws = load_workbook(out)["Excluded TC"]
    assert ws.max_row >= 2
    assert ws.cell(row=2, column=3).value  # 제외 사유 비어있지 않음
```

- [ ] **Step 2: 실패 확인**

Run: `uv run pytest tests/test_export_minimal_coverage.py -v`
Expected: FAIL — `ModuleNotFoundError: shared.export_minimal_coverage`

- [ ] **Step 3: 커밋**

```bash
git add tests/test_export_minimal_coverage.py
git commit -m "test(export_minimal_coverage): 5 sheets + generic column preservation (RED)"
```

### Task 12: `shared/export_minimal_coverage.py` 구현 (GREEN)

**Files:**
- Create: `shared/export_minimal_coverage.py`

- [ ] **Step 1: 구현**

```python
"""Export a minimal-coverage selection to a 5-sheet workbook.

Sheets: Selected TC / Coverage Summary / Excluded TC / Next Best / Assumptions.
Preserves ALL source columns generically (mutual tabs incl. A/B survive),
keeps original TC_ID values, appends analysis columns after source columns.
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from new_workbook import HEADER_FILL, HEADER_FONT, WRAP, _resolve_output_path  # noqa: E402
from select_minimal_coverage import risk_tags  # noqa: E402

from openpyxl import Workbook  # noqa: E402

ANALYSIS_COLUMNS = ("실행 순서", "선택 사유", "커버 리스크", "점수")


def export_minimal_coverage(selection: dict, columns: list[str], output: Path) -> Path:
    """Write the 5-sheet workbook. Returns actual path written."""
    actual_output = _resolve_output_path(output)
    wb = Workbook()
    wb.remove(wb.active)

    def add_sheet(title: str, headers: list[str], rows: list[list]) -> None:
        ws = wb.create_sheet(title)
        for col_idx, name in enumerate(headers, start=1):
            cell = ws.cell(row=1, column=col_idx, value=name)
            cell.font = HEADER_FONT
            cell.fill = HEADER_FILL
            cell.alignment = WRAP
        for row_idx, row in enumerate(rows, start=2):
            for col_idx, value in enumerate(row, start=1):
                ws.cell(row=row_idx, column=col_idx, value=value).alignment = WRAP

    add_sheet(
        "Selected TC",
        list(columns) + list(ANALYSIS_COLUMNS),
        [[item["row"].get(c) for c in columns]
         + [order, "; ".join(item["reasons"]),
            ", ".join(item["new_tags"]), item["score"]]
         for order, item in enumerate(selection["selected"], start=1)],
    )

    counts: dict[str, int] = {}
    for item in selection["selected"]:
        for tag in risk_tags(item["row"]):
            counts[tag] = counts.get(tag, 0) + 1
    add_sheet("Coverage Summary", ["리스크 태그", "커버 TC 수"],
              [[tag, n] for tag, n in sorted(counts.items())])

    add_sheet("Excluded TC", ["TC_ID", "Test Summary", "제외 사유", "잔여 리스크"],
              [[e["row"].get("TC_ID"), e["row"].get("Test Summary"),
                e["reason"], ", ".join(e["residual_risk"])]
               for e in selection["excluded"]])

    add_sheet("Next Best", ["TC_ID", "Test Summary", "점수", "추가 커버"],
              [[n["row"].get("TC_ID"), n["row"].get("Test Summary"),
                n["score"], ", ".join(n["new_tags"])]
               for n in selection["next_best"]])

    add_sheet("Assumptions", ["가정"], [[a] for a in selection["assumptions"]])

    actual_output.parent.mkdir(parents=True, exist_ok=True)
    wb.save(actual_output)
    return actual_output
```

- [ ] **Step 2: 통과 + 전체 회귀 확인**

Run: `uv run pytest tests/test_export_minimal_coverage.py tests/test_select_minimal_coverage.py -v && uv run pytest -q`
Expected: 신규 9 PASS, 전체 59 passed (46 + 4 + 6 + 3).

- [ ] **Step 3: 커밋**

```bash
git add shared/export_minimal_coverage.py
git commit -m "feat(export_minimal_coverage): 5-sheet workbook with generic column preservation"
```

### Task 13: `qa-minimal-coverage` 번들 + CLI smoke

**Files:**
- Create: `skills/qa-minimal-coverage/SKILL.md`
- Create: `skills/qa-minimal-coverage/reference/scoring-rules.md`
- Create: `skills/qa-minimal-coverage/reference/risk-taxonomy.md` (placeholder)
- Create: `skills/qa-minimal-coverage/scripts/{select_minimal_coverage,export_minimal_coverage,extract_tc_table,inspect_master,new_workbook}.py` (placeholder 5개)
- Create: `skills/qa-minimal-coverage/examples/sample-selection-summary.md`

- [ ] **Step 1: SKILL.md 작성**

````markdown
---
name: qa-minimal-coverage
description: 기존 QA TC xlsx에서 리스크 커버를 최대화하는 최소 실행 TC 세트를 결정론 스코어링으로 골라 5시트 xlsx(Selected/Coverage/Excluded/Next Best/Assumptions)로 저장. 제한된 시간에 어떤 TC를 돌릴지 결정할 때 사용. 트리거 — "최소 TC", "시간 없는데 뭐 돌려", "TC 줄여줘", "/qa:minimal-coverage".
---

# qa:minimal-coverage

TC 품질 검수(`qa:review-tc`)가 끝난 워크북에서 실행 부분집합을 고른다. 기본 목표는 **리스크 커버리지 최대화** (실행 시간 최소화는 명시 요청 시에만).

## 입력
- TC xlsx + 탭 이름 (필수)
- `--max-cases N`, 시간 제약 (옵션)
- 리스크 분석 리포트 (옵션 — 있으면 결과 해석에 활용)

## 워크플로우

### 1. 실행
```bash
uv run python scripts/select_minimal_coverage.py \
    --source <tc.xlsx> --tab "<탭>" --output <out>.xlsx [--max-cases N]
```
- 원본은 절대 수정되지 않는다. stdout 마지막 줄이 실제 출력 경로.
- 스코어링 규칙은 `reference/scoring-rules.md` (P1·고위험 키워드 강제 포함, greedy 커버 확대).

### 2. 결과 해석 (LLM)
출력 xlsx의 Excluded TC / Next Best를 보고:
- 잔여 리스크가 Blocker 영역(`reference/risk-taxonomy.md`)에 걸리면 경고.
- 사용자 제약(시간)과 Next Best를 비교해 "여유 있으면 이것부터" 제안.

### 3. 보고
선택 수 / 전체 수, 커버된 리스크 태그, 잔여 리스크 경고, 출력 경로.

## 비목표
- TC 품질 검수 (그건 `qa:review-tc` 먼저), 회귀 범위 결정 (그건 `qa:regression-scope`)
- 원본 워크북 수정

## 예시
`examples/sample-selection-summary.md` 참조.
````

- [ ] **Step 2: `reference/scoring-rules.md` 작성**

스코어 공식, PRIORITY_BASE 표, HIGH_RISK_KEYWORDS 목록, 강제 포함 조건, greedy 종료 조건(신규 태그 없음 / max-cases), Excluded 사유 3종을 그대로 문서화 (`shared/select_minimal_coverage.py`가 진실의 원천임을 명시). "Next Best는 제외(Excluded)가 아니라 여유 시간용 추천 목록이므로 제외 사유·잔여 리스크 대신 점수·추가 커버를 기록한다"는 한 줄 포함.

- [ ] **Step 3: 예시 작성**

`examples/sample-selection-summary.md`: 28 TC 탭에서 `--max-cases 10`으로 10개 선택된 가상 결과 보고 모양 (선택/잔여 리스크 경고/Next Best 제안 포함).

- [ ] **Step 4: placeholder + sync**

```bash
mkdir -p skills/qa-minimal-coverage/{reference,scripts,examples}
touch skills/qa-minimal-coverage/reference/risk-taxonomy.md
touch skills/qa-minimal-coverage/scripts/{select_minimal_coverage,export_minimal_coverage,extract_tc_table,inspect_master,new_workbook}.py
uv run python scripts/sync_shared.py
```

- [ ] **Step 5: CLI smoke (원본 불변 확인 포함)**

```bash
rm -f /tmp/minimal-smoke.xlsx   # stale 파일이 있으면 (2) 접미사로 빠져 검증이 어긋남
md5 tests/fixtures/sample_tc_with_issues.xlsx
uv run python skills/qa-minimal-coverage/scripts/select_minimal_coverage.py \
    --source tests/fixtures/sample_tc_with_issues.xlsx --tab TabA \
    --output /tmp/minimal-smoke.xlsx --max-cases 3
md5 tests/fixtures/sample_tc_with_issues.xlsx   # 동일해야 함
uv run python -c "
from openpyxl import load_workbook
wb = load_workbook('/tmp/minimal-smoke.xlsx')
assert wb.sheetnames == ['Selected TC','Coverage Summary','Excluded TC','Next Best','Assumptions'], wb.sheetnames
print('smoke OK')"
```
Expected: md5 동일, `smoke OK`.

- [ ] **Step 6: 커밋**

```bash
git add skills/qa-minimal-coverage
git commit -m "feat(skill): add qa-minimal-coverage bundle + cli smoke"
```

### Task 14: `qa-release-checklist` 번들

**Files:**
- Create: `skills/qa-release-checklist/SKILL.md`
- Create: `skills/qa-release-checklist/reference/release-gates.md`
- Create: `skills/qa-release-checklist/examples/sample-release-checklist.md`

- [ ] **Step 1: SKILL.md 작성**

````markdown
---
name: qa-release-checklist
description: PRD/릴리즈 요약, TC 실행 결과, known issue, 리스크 분석을 바탕으로 릴리즈 전 QA sign-off 체크리스트와 blocker 조건을 정리. 릴리즈 승인 최종 점검에 사용. 트리거 — "릴리즈 체크리스트", "출시해도 돼?", "sign-off", "/qa:release-checklist".
---

# qa:release-checklist

QA 증거를 모아 릴리즈 판정(ready / conditional / blocked)을 내린다.

## 입력
- 릴리즈 요약 또는 PRD (필수)
- TC 실행 결과 요약 — `qa:test-result-report` 출력 권장, 수기 요약도 허용 (필수)
- known issue 목록, 리스크 분석 리포트 (옵션)

## 워크플로우

### 1. 게이트 점검
`reference/release-gates.md`의 7개 게이트(Blocker/Major/known issue/rollout/rollback/monitoring/owner)를 입력과 대조. 입력에 정보가 없는 게이트는 "확인 불가"로 표시 — 추정으로 통과 처리 금지.

### 2. 판정
- **blocked**: Blocker 게이트 1개라도 실패.
- **conditional**: Major 미해결이 있으나 risk-accept 가능 — 조건 명시.
- **ready**: 전 게이트 통과 또는 합리적 예외.

### 3. 출력 (md)
판정 + 게이트별 표 (통과/실패/확인 불가 + 근거) + blocker 조건 + rollout/rollback 체크 + 잔여 known issue.

## 비목표
- TC 결과 집계 (그건 `qa:test-result-report`), 릴리즈 자체 실행/배포

## 예시
`examples/sample-release-checklist.md` 참조 (ready / conditional / blocked 3가지 모양).
````

- [ ] **Step 2: `reference/release-gates.md` 작성**

7개 게이트 정의: ① Blocker 결함 0건 ② Major 결함 해결 또는 risk-accept 서명 ③ known issue 문서화 + CS 공유 ④ rollout 계획 (단계 배포 비율, Remote Config 기본값) ⑤ rollback 절차 (트리거 조건 + 담당자) ⑥ 모니터링 (핵심 지표 + 알람) ⑦ owner 확인 (QA/PM/개발 sign-off). 각 게이트에 "통과 기준"과 "확인 불가 시 처리"를 명시.

- [ ] **Step 3: 예시 작성 + 커밋**

```bash
git add skills/qa-release-checklist
git commit -m "feat(skill): add qa-release-checklist bundle"
```

### Task 15: Round 1 최종 검증 + README

**Files:**
- Modify: `README.md`

- [ ] **Step 1: 전체 테스트**

Run: `uv run pytest`
Expected: 59 passed.

- [ ] **Step 2: sync 검증**

Run: `uv run python scripts/sync_shared.py --check`
Expected: exit 0 (`would-update:` 없음).

- [ ] **Step 3: md-only 스킬 smoke**

fresh subagent 3회:
1. `skills/qa-risk-analysis/SKILL.md` + `tests/fixtures/sample_prd.md` → 리스크 매트릭스 형식·등급 분류·가정 분리 확인.
2. `skills/qa-regression-scope/SKILL.md` + `tests/fixtures/sample_prd.md` + `tests/fixtures/sample_tc_with_issues.xlsx` → 탭 인벤토리(inspect/extract 스크립트 호출 — SKILL.md의 `scripts/` 상대 경로는 번들 디렉토리 기준임을 subagent에게 명시), Required/Skipped 근거 기록 확인.
3. `skills/qa-release-checklist/SKILL.md` + 가상의 TC 결과 요약(Pass 25/Fail 2/Block 1) → "확인 불가" 게이트 처리와 conditional 판정 로직 확인.

- [ ] **Step 4: README 갱신**

스킬 목록에 4종 추가:
```markdown
- `qa-risk-analysis` — 리스크 매트릭스 md+xlsx (Round 1, 출시 ✅)
- `qa-regression-scope` — 회귀 범위 결정 md+xlsx (Round 1, 출시 ✅)
- `qa-minimal-coverage` — 최소 실행 TC 세트 5시트 xlsx (Round 1, 출시 ✅)
- `qa-release-checklist` — 릴리즈 sign-off 체크리스트 (Round 1, 출시 ✅)
```
검증 이력에 `### Round 1 검증 (2026-06-11)` 섹션 추가 — Step 1~3 실제 결과를 기록 (통과한 것만).

- [ ] **Step 5: 최종 커밋**

```bash
uv run python scripts/sync_shared.py --check && git add README.md
git commit -m "docs: record round 1 verification (4 strategy skills)"
git status --short   # clean 확인
```

---

## 남은 라운드 (이 계획 비포함)

Round 2(qa-prd-diff, qa-test-result-report + prd-clarify 스냅샷 단계)와 Round 3(qa-exploratory-charter, qa-automation-candidates, qa-bug-report)은 Round 1 출시 후 별도 계획으로 작성한다. 설계는 `docs/plans/2026-06-11-qa-skills-expansion-v2-design.md`에 이미 확정되어 있다.
