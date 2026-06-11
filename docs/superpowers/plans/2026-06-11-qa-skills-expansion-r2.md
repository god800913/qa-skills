# QA Skills Expansion R2 Implementation Plan

> **For agentic workers:** REQUIRED: Use superpowers:subagent-driven-development (if subagents available) or superpowers:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.
> TDD 태스크는 @superpowers:test-driven-development 원칙(RED→GREEN, 실패 확인 필수)을 따른다.

**Goal:** 설계(`docs/plans/2026-06-11-qa-skills-expansion-v2-design.md`)의 Round 2 — `qa-prd-diff`, `qa-test-result-report` 출시 + `qa-prd-clarify`에 PRD 스냅샷 단계 추가.

**Architecture:** R0·R1과 동일한 번들 구조. 결정론 부분은 `shared/parse_results.py`(Result enum 집계) 하나뿐이며 TDD로 작성. prd-diff는 md-only 스킬(의미 비교는 LLM, difflib은 보조 신호). 실행 완료 픽스처(`sample_tc_executed.xlsx`)를 신규 생성해 통합 검증.

**Tech Stack:** Python 3.12, openpyxl, python-calamine, pytest, uv. 새 의존성 없음.

**저장소 규약 (공통):** 원본 xlsx 수정 금지, 출력 충돌 시 `(2)` 접미사, 한국어, `<type>: <description>` 커밋, 태스크마다 커밋, main 직커밋, push 금지. 작업 디렉토리 `/Users/dongjin/Dropbox/workplace/HyperConnect/poc/qa-skills`.

**현재 기준선:** 테스트 60개 PASS, `sync_shared.py --check` exit 0.

---

### Task 1: `qa-prd-clarify` 스냅샷 단계 추가

**Files:**
- Modify: `skills/qa-prd-clarify/SKILL.md`

- [ ] **Step 1:** SKILL.md를 읽고 PRD 수집/입력 단계(Notion fetch 직후 위치)에 아래 항목 추가 — `skills/qa-generate-tc/SKILL.md`의 스냅샷 항목과 동일 문구를 사용해 두 스킬 규약을 일치시킨다:

```markdown
- **[fetch 성공 시]** PRD 본문을 md 스냅샷으로 저장: 기본 `./prd-snapshots/<기능명>-<YYYYMMDD>.md` (기능명은 Notion 페이지 제목 또는 PRD 첫 H1에서 추출 — 공백은 하이픈으로, 특수문자 제거) (사용자가 다른 경로를 지정하면 그에 따름. 디렉토리 없으면 생성, 날짜는 `date '+%Y%m%d'`로 구함 — 암산 금지). 저장 경로를 사용자에게 알린다. 이 스냅샷은 나중에 `qa:prd-diff`가 PRD 변경분 분석에 사용한다.
```

- [ ] **Step 2:** 검증 `rg "prd-snapshots" skills/qa-prd-clarify/SKILL.md skills/qa-generate-tc/SKILL.md` — 두 파일 모두 매치, 문구 동일.
- [ ] **Step 3:** 커밋 `feat(prd-clarify): add prd snapshot step (r2 prerequisite)` — SKILL.md만.

### Task 2: `parse_results` 실패 테스트 (RED)

**Files:**
- Create: `tests/test_parse_results.py`

- [ ] **Step 1: 테스트 작성**

```python
"""Tests for shared/parse_results.py (in-memory rows)."""
import copy

from shared.parse_results import normalize_result, parse_results


def _row(result="", tc_id="1-1", priority="P2", summary="요약", jira=""):
    return {"Priority": priority, "TC_ID": tc_id, "Test Summary": summary,
            "Result": result, "Jira no.": jira}


def test_normalize_variants():
    assert normalize_result("pass") == "Pass"
    assert normalize_result(" FAIL ") == "Fail"
    assert normalize_result("block") == "Block"
    assert normalize_result("n/t") == "N/T"
    assert normalize_result("n/a") == "N/A"
    assert normalize_result("") is None
    assert normalize_result(None) is None
    assert normalize_result("Passed") == "unknown"


def test_counts_and_pass_rate_excludes_nt_na():
    rows = [_row("Pass"), _row("Pass"), _row("Fail"), _row("Block"),
            _row("N/T"), _row("N/A"), _row("")]
    agg = parse_results(rows)
    assert agg["total"] == 7
    assert agg["counts"]["Pass"] == 2
    assert agg["counts"]["미입력"] == 1
    assert agg["pass_rate"] == 0.5          # 2 / (2+1+1) — N/T·N/A·미입력 분모 제외


def test_pass_rate_none_when_nothing_executed():
    agg = parse_results([_row("N/T"), _row("")])
    assert agg["pass_rate"] is None


def test_fails_blocks_carry_tc_id_and_jira():
    rows = [_row("Fail", tc_id="2-1", jira="JIRA-1"), _row("Block", tc_id="2-2")]
    agg = parse_results(rows)
    assert agg["fails"] == [{"tc_id": "2-1", "summary": "요약", "jira": "JIRA-1"}]
    assert agg["blocks"][0]["tc_id"] == "2-2"


def test_unknown_values_reported_with_original():
    agg = parse_results([_row("성공")])
    assert agg["counts"]["unknown"] == 1
    assert agg["unknown"][0]["value"] == "성공"


def test_groups_by_priority_and_section():
    rows = [_row("Pass", tc_id="1-1", priority="P1"),
            _row("Fail", tc_id="1-2", priority="P1"),
            _row("Pass", tc_id="2-1", priority="P3")]
    agg = parse_results(rows)
    assert agg["by_priority"]["P1"]["Fail"] == 1
    assert agg["by_section"]["1"]["Pass"] == 1
    assert agg["by_section"]["2"]["Pass"] == 1


def test_input_not_mutated():
    rows = [_row("Pass"), _row("성공")]
    snap = copy.deepcopy(rows)
    parse_results(rows)
    assert rows == snap
```

- [ ] **Step 2:** `uv run pytest tests/test_parse_results.py -v` → FAIL (`ModuleNotFoundError`) 확인.
- [ ] **Step 3:** 커밋 `test(parse_results): enum normalize + aggregate + pass-rate + unknown (RED)` — 테스트 파일만.

### Task 3: `shared/parse_results.py` 구현 (GREEN)

**Files:**
- Create: `shared/parse_results.py`

- [ ] **Step 1: 구현**

```python
"""Parse and aggregate the Result column of an executed TC workbook.

Result enum (팀 표준 고정): Pass / Fail / Block / N/T / N/A
- 매칭은 대소문자 무시 + 공백 trim ("pass" → "Pass").
- enum 외 비어있지 않은 값은 `unknown`으로 분류하고 원래 값과 함께 보고.
- 빈 Result 셀은 "미입력" (미실행)으로 집계.
- pass_rate = Pass / (Pass + Fail + Block) — N/T·N/A·미입력·unknown은 분모 제외.
- 섹션은 TC_ID의 '-' 앞 접두사로 묶는다 ("3-12" → 섹션 "3").

CLI:
    python parse_results.py <xlsx_path> --tab <tab_name>
Output: JSON aggregate. 입력 행은 절대 변경하지 않는다.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

RESULT_ENUM = ("Pass", "Fail", "Block", "N/T", "N/A")
_CANONICAL = {v.lower(): v for v in RESULT_ENUM}


def normalize_result(value) -> str | None:
    """canonical enum 값, 빈 값이면 None, 그 외는 "unknown"을 반환."""
    text = str(value).strip() if value is not None else ""
    if not text:
        return None
    return _CANONICAL.get(text.lower(), "unknown")


def _section_of(row: dict) -> str:
    tc_id = str(row.get("TC_ID") or "").strip()
    return tc_id.split("-")[0] if "-" in tc_id else "(없음)"


def _empty_bucket() -> dict:
    return {**{v: 0 for v in RESULT_ENUM}, "unknown": 0, "미입력": 0}


def _bucket_add(bucket: dict, key: str | None) -> dict:
    label = "미입력" if key is None else key
    return {**bucket, label: bucket[label] + 1}


def _pass_rate(bucket: dict) -> float | None:
    executed = bucket["Pass"] + bucket["Fail"] + bucket["Block"]
    if executed == 0:
        return None
    return round(bucket["Pass"] / executed, 4)


def parse_results(rows: list[dict]) -> dict:
    """Result 집계. 입력 rows는 변경되지 않는다."""
    total = _empty_bucket()
    by_priority: dict[str, dict] = {}
    by_section: dict[str, dict] = {}
    fails: list[dict] = []
    blocks: list[dict] = []
    unknown: list[dict] = []

    for row in rows:
        norm = normalize_result(row.get("Result"))
        total = _bucket_add(total, norm)

        pri = str(row.get("Priority") or "").strip() or "(없음)"
        by_priority = {**by_priority,
                       pri: _bucket_add(by_priority.get(pri, _empty_bucket()), norm)}
        sec = _section_of(row)
        by_section = {**by_section,
                      sec: _bucket_add(by_section.get(sec, _empty_bucket()), norm)}

        ref = {"tc_id": row.get("TC_ID"), "summary": row.get("Test Summary"),
               "jira": row.get("Jira no.") or ""}
        if norm == "Fail":
            fails = fails + [ref]
        elif norm == "Block":
            blocks = blocks + [ref]
        elif norm == "unknown":
            unknown = unknown + [{**ref, "value": row.get("Result")}]

    return {
        "total": len(rows),
        "counts": total,
        "pass_rate": _pass_rate(total),
        "by_priority": by_priority,
        "by_section": by_section,
        "fails": fails,
        "blocks": blocks,
        "unknown": unknown,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Aggregate the TC Result column.")
    parser.add_argument("xlsx_path", type=Path)
    parser.add_argument("--tab", type=str, required=True)
    args = parser.parse_args()

    from extract_tc_table import extract_tc_table  # noqa: PLC0415
    rows = extract_tc_table(args.xlsx_path, args.tab)
    print(json.dumps(parse_results(rows), ensure_ascii=False, indent=2, default=str))


if __name__ == "__main__":
    main()
```

- [ ] **Step 2:** `uv run pytest tests/test_parse_results.py -v` → 7 PASS.
- [ ] **Step 3:** `uv run pytest -q` → 67 passed (60 + 7). 회귀 시 BLOCKED.
- [ ] **Step 4:** 커밋 `feat(parse_results): result enum aggregation (counts, pass-rate, fails/blocks, unknown)` — 구현 파일만.

### Task 4: 실행 완료 픽스처 + 통합 테스트

**Files:**
- Create: `tests/test_parse_results_fixture.py`
- Create: `scripts/make_executed_fixture.py`
- Create: `tests/fixtures/sample_tc_executed.xlsx` (스크립트 산출물)

- [ ] **Step 1: 통합 테스트 먼저 (RED)**

```python
"""Integration: executed fixture → extract → parse_results."""
from pathlib import Path

from shared.extract_tc_table import extract_tc_table
from shared.parse_results import parse_results

FIXTURE = Path(__file__).parent / "fixtures" / "sample_tc_executed.xlsx"


def test_fixture_aggregates_match_known_distribution():
    rows = extract_tc_table(FIXTURE, "TabExec")
    agg = parse_results(rows)
    assert agg["total"] == 8
    assert agg["counts"]["Pass"] == 4
    assert agg["counts"]["Fail"] == 1
    assert agg["counts"]["Block"] == 1
    assert agg["counts"]["N/T"] == 1
    assert agg["counts"]["unknown"] == 1
    assert agg["fails"][0]["jira"] == "JIRA-2202"
    assert agg["unknown"][0]["value"] == "성공"
```

Run: `uv run pytest tests/test_parse_results_fixture.py -v` → FAIL (픽스처 없음).

- [ ] **Step 2: 픽스처 생성 스크립트** — `scripts/make_executed_fixture.py`: 기존 `scripts/make_sample_tc_with_issues.py` 패턴을 따라 `shared/new_workbook.write_workbook` 재사용. 셀 값 배열 `["Pass", "Pass", "pass", "Pass", "Fail", "Block", "N/T", "성공"]` — 소문자 "pass"는 normalize 후 Pass로 합산되므로 **테스트 기대값 Pass 4에 포함**. 핵심 코드:

```python
"""Generate tests/fixtures/sample_tc_executed.xlsx (Result column filled)."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "shared"))
from new_workbook import write_workbook  # noqa: E402

RESULTS = ["Pass", "Pass", "pass", "Pass", "Fail", "Block", "N/T", "성공"]
JIRA = {4: "JIRA-2202", 5: "JIRA-2203"}

rows = [
    {"section": "1. 실행 샘플", "Priority": "P2", "Test Item": "실행 샘플",
     "Test Summary": f"샘플 케이스 {i + 1}", "Test Step": "1. 실행",
     "Expected Result": "정상", "Result": result, "Jira no.": JIRA.get(i, "")}
    for i, result in enumerate(RESULTS)
]
out = Path(__file__).parent.parent / "tests" / "fixtures" / "sample_tc_executed.xlsx"
out.unlink(missing_ok=True)  # write_workbook은 충돌 시 (2) 접미사를 붙이므로 재생성 시 선삭제
actual = write_workbook(rows, "TabExec", out)
print(actual)
```

  실행: `uv run python scripts/make_executed_fixture.py` → `tests/fixtures/sample_tc_executed.xlsx` 생성 (TC_ID 1-1~1-8 자동 부여).
- [ ] **Step 3:** `uv run pytest tests/test_parse_results_fixture.py -v` → 1 PASS. `uv run pytest -q` → 68 passed.
- [ ] **Step 4:** CLI 확인: `uv run python shared/parse_results.py tests/fixtures/sample_tc_executed.xlsx --tab TabExec` → JSON 출력, exit 0.
- [ ] **Step 5:** 커밋 `test(fixture): add executed TC fixture + parse_results integration` — 3개 파일.

### Task 5: `format-rules.md`에 Result enum 추가

**Files:**
- Modify: `shared-reference/format-rules.md`

- [ ] **Step 1:** 파일 끝에 섹션 추가 (기존 내용 변경 금지):

```markdown
## Result 컬럼 enum (parse_results 스코프)

`Result` 컬럼의 팀 표준 값: `Pass` / `Fail` / `Block` / `N/T` / `N/A` (대소문자 무시 매칭, 빈 셀 = 미입력).

> 이 항목은 `qa:test-result-report`의 `parse_results.py`가 집계 시 검사하는 기준이며,
> `validate_format.py`(qa:review-tc)의 결정론 검출 항목이 **아니다** — 작성 시점에는 Result가 비어 있는 게 정상이기 때문.
> enum 외 값은 unknown으로 분류되어 리포트에 경고로 표시된다.
```

- [ ] **Step 2:** `uv run python scripts/sync_shared.py` 실행 — format-rules.md를 placeholder로 가진 기존 번들(qa-review-tc 등)에 전파됨을 확인. `--check` exit 0.
- [ ] **Step 3:** 커밋 `docs: add result enum to format-rules (parse_results scope)` — shared-reference + 동기화된 번들 사본들.

### Task 6: `qa-test-result-report` 번들

**Files:**
- Create: `skills/qa-test-result-report/SKILL.md`
- Create: `skills/qa-test-result-report/examples/sample-result-report.md`
- Create: `skills/qa-test-result-report/reference/format-rules.md` (placeholder→sync)
- Create: `skills/qa-test-result-report/scripts/{parse_results,extract_tc_table,inspect_master}.py` (placeholder→sync)

- [ ] **Step 1: SKILL.md 작성**

````markdown
---
name: qa-test-result-report
description: 실행 완료된 QA TC xlsx의 Result 컬럼(Pass/Fail/Block/N/T/N/A)을 집계해 탭·섹션·Priority별 통과율, Fail/Block 목록(Jira 링크), 미실행·잔여 리스크를 md 리포트로 정리. qa:release-checklist의 입력으로 바로 사용 가능. 트리거 — "테스트 결과 정리", "결과 리포트", "통과율 뽑아", "/qa:test-result-report".
---

# qa:test-result-report

실행이 끝난 TC 워크북에서 QA 결과 리포트를 만든다.

## 입력
- 실행 완료된 TC xlsx + 탭 이름 (필수). 탭 미지정 시 `scripts/inspect_master.py`로 목록 보여주고 선택.
- 릴리즈/기능 이름 (리포트 제목용, 옵션)

## 워크플로우

### 1. 집계 (결정론)
```bash
uv run python scripts/parse_results.py <xlsx> --tab "<탭>"
```
JSON 결과: total, counts(enum별+미입력+unknown), pass_rate(= Pass/(Pass+Fail+Block)), by_priority, by_section, fails/blocks(tc_id·summary·Jira), unknown(원래 값 포함).

### 2. unknown 처리 (필수)
unknown이 1건이라도 있으면 **리포트 작성 전에** 사용자에게 원래 값 목록을 보여주고 의미를 확인받는다 (예: "성공"이 Pass 의미인지). 임의 재분류 금지 — 사용자가 정정하면 xlsx를 고친 뒤 재집계하라고 안내.

### 3. 리포트 작성 (LLM)
```markdown
## 테스트 결과 리포트 — <릴리즈/기능>
### 총괄
(한 줄 결론: 통과율 + Fail/Block 핵심)
| 구분 | Pass | Fail | Block | N/T | N/A | 미입력 | 통과율 |
### Fail / Block 상세
| TC_ID | Test Summary | 구분 | Jira |
### 미실행·잔여 리스크
(N/T·미입력이 몰린 섹션 — `reference/format-rules.md`의 enum 정의 참조, 섹션·Priority 분포에서 P1 미실행은 강조)
### 경고
(unknown 값, 데이터 품질 이슈)
```

### 4. 다음 단계 안내
"이 리포트를 `qa:release-checklist`의 TC 실행 결과 입력으로 쓸 수 있습니다."

## 비목표
- 릴리즈 판정 (그건 `qa:release-checklist`), 버그 리포트 작성 (Round 3 `qa:bug-report`)
- xlsx 수정 — Result 정정은 사람이 직접

## 예시
`examples/sample-result-report.md` 참조.
````

- [ ] **Step 2: 예시 작성** — `sample_tc_executed.xlsx`의 실제 분포(8건: Pass 4/Fail 1 JIRA-2202/Block 1 JIRA-2203/N/T 1/unknown "성공" 1)를 소재로 위 섹션 3 형식 그대로. 통과율 계산은 코드 정의와 일치(4/(4+1+1)=66.7%). unknown 경고 섹션 포함. 30줄 내외, 기존 예시 톤.
- [ ] **Step 3: placeholder + sync + 검증**

```bash
mkdir -p skills/qa-test-result-report/{reference,scripts,examples}
touch skills/qa-test-result-report/reference/format-rules.md
touch skills/qa-test-result-report/scripts/{parse_results,extract_tc_table,inspect_master}.py
uv run python scripts/sync_shared.py
uv run python scripts/sync_shared.py --check   # exit 0
uv run python skills/qa-test-result-report/scripts/parse_results.py tests/fixtures/sample_tc_executed.xlsx --tab TabExec   # 번들 경로에서 JSON 정상
```

- [ ] **Step 4:** 커밋 `feat(skill): add qa-test-result-report bundle` — 해당 디렉토리만.

### Task 7: `qa-prd-diff` 번들

**Files:**
- Create: `skills/qa-prd-diff/SKILL.md`
- Create: `skills/qa-prd-diff/examples/sample-prd-diff.md`
- Create: `skills/qa-prd-diff/scripts/{extract_tc_table,inspect_master}.py` (placeholder→sync)

- [ ] **Step 1: SKILL.md 작성**

````markdown
---
name: qa-prd-diff
description: 과거 PRD 스냅샷 md와 현재 Notion PRD를 비교해 변경점(추가/수정/삭제)을 추출하고 기존 TC 영향(수정 필요/신규 필요/폐기 후보)을 분류. TC xlsx를 주면 TC_ID 단위로 매핑. PRD 개정 후 TC 갱신 범위를 정할 때 사용. 트리거 — "PRD 뭐 바뀌었어", "스펙 변경 영향", "PRD 디프", "/qa:prd-diff".
---

# qa:prd-diff

PRD 개정이 기존 TC에 미치는 영향을 정리한다.

## 입력
- 과거 PRD 스냅샷 md (필수) — 경로를 안 주면 `./prd-snapshots/`에서 기능명이 매칭되는 파일을 찾아 제안 (여러 개면 파일명의 날짜가 가장 최근인 것, 사용자 확인 필수)
- 현재 PRD: Notion URL (fetch) 또는 md 붙여넣기 (필수)
- 기존 TC xlsx + 탭 (옵션 — 있으면 TC_ID 단위 매핑)

## 워크플로우

### 1. 입력 수집
- 스냅샷 파일 읽기. 현재 PRD가 Notion URL이면 fetch하고, **fetch 직후 새 스냅샷도 저장** (`qa:generate-tc`와 같은 규약 — `./prd-snapshots/<기능명>-<YYYYMMDD>.md`).
- 스냅샷과 현재 본문이 사실상 동일하면(변경 없음) 그렇게 보고하고 종료.

### 2. 변경점 추출
- **의미 비교는 LLM이 수행한다.** 텍스트 diff는 보조 신호일 뿐:
```bash
python3 -c "
import difflib, pathlib
old = pathlib.Path('<snapshot.md>').read_text().splitlines()
new = pathlib.Path('<current.md>').read_text().splitlines()
print('\n'.join(difflib.unified_diff(old, new, lineterm='', n=1)))"
```
- 변경점을 추가 / 수정 / 삭제로 분류하고, 각 항목에 "QA 관점에서 무엇이 달라지나" 한 줄.
- 문구만 바뀌고 동작이 같은 항목은 "동작 동일 (카피 변경)"으로 별도 분류 — TC 영향 없음.

### 3. TC 영향 분류
- TC xlsx 제공 시: `scripts/extract_tc_table.py <xlsx> --tab <탭>`으로 행을 받아 변경점별 영향 TC_ID 매핑.
- 분류: **수정 필요** (Expected Result/Step이 구버전 기준) / **신규 필요** (변경점을 커버하는 TC 없음) / **폐기 후보** (삭제된 스펙의 TC).
- 폐기는 후보일 뿐 — 실제 삭제 결정은 사람. 근거 없는 매핑 금지, 불확실하면 Open Questions로.

### 4. 출력 (md)
```markdown
## PRD 변경 분석 — <기능> (<구 스냅샷 날짜> → <오늘>)
### 요약
(한 줄: 변경 N건, TC 영향 — 수정 a / 신규 b / 폐기 후보 c)
### 변경점
| # | 분류 | 변경 내용 | QA 관점 영향 |
### TC 영향
| 변경점 # | 영향 | TC_ID (또는 "신규 작성 필요") | 근거 |
### Open Questions
(판단 불가 항목 — PM/개발 확인)
```

### 5. 다음 액션 안내
"수정/신규 TC는 `qa:generate-tc`로, 갱신 후 검수는 `qa:review-tc`로 이어가세요."

## 비목표
- TC 작성·수정 자체 (그건 `qa:generate-tc`), PRD 모호점 분석 (그건 `qa:prd-clarify`)
- Notion 페이지 버전 히스토리 조회 (MCP 미지원 — 스냅샷 규약이 그 대체물)

## 예시
`examples/sample-prd-diff.md` 참조.
````

- [ ] **Step 2: 예시 작성** — "라운지 선물하기" PRD v1(5/2 스냅샷) → v2(6/11): 추가(선물 취소 기능), 수정(젬 가격 50→30, iOS 권한 거부 시 토스트 문구), 삭제(주간 선물 랭킹), 카피 변경 1건(버튼 라벨). TC 영향: 수정 2(TC_ID 명시) / 신규 2 / 폐기 후보 1 / Open Questions 1. 섹션 4 형식 그대로, 40줄 내외, 기존 예시 서사·톤과 정합 (`enableLoungeGift` 플래그명 유지).
- [ ] **Step 3: placeholder + sync + 검증 + 커밋**

```bash
mkdir -p skills/qa-prd-diff/{scripts,examples}
touch skills/qa-prd-diff/scripts/{extract_tc_table,inspect_master}.py
uv run python scripts/sync_shared.py && uv run python scripts/sync_shared.py --check
git add skills/qa-prd-diff
git commit -m "feat(skill): add qa-prd-diff bundle"
```

### Task 8: Round 2 최종 검증 + README

**Files:**
- Modify: `README.md`

- [ ] **Step 1:** `uv run pytest -q` → 68 passed. `uv run python scripts/sync_shared.py --check` → exit 0.
- [ ] **Step 2: fresh subagent smoke 2회**
  1. `qa-test-result-report`: `sample_tc_executed.xlsx` TabExec → 번들 스크립트로 집계, unknown("성공") 1건을 사용자 확인으로 끌어올리는지 + 통과율 66.7% 정확 계산 확인. (`scripts/` 경로는 번들 디렉토리 기준임을 명시)
  2. `qa-prd-diff`: 구 스냅샷 = `tests/fixtures/sample_prd.md`, 현재 = /tmp에 만든 수정본(항목 1개 추가 + 1개 문구 변경 + 1개 삭제) → 변경점 분류·카피 변경 구분·Open Questions 처리 확인. TC xlsx는 `sample_tc_with_issues.xlsx` TabA 제공 → TC_ID 매핑 확인.
- [ ] **Step 3: README 갱신** — 스킬 목록에 2줄 추가:

```markdown
- `qa-prd-diff` — PRD 스냅샷 대비 변경분 → TC 영향 분류 (Round 2, 출시 ✅)
- `qa-test-result-report` — Result 집계 → 결과 리포트 (Round 2, 출시 ✅)
```

검증 이력에 `### Round 2 검증 (2026-06-11)` 섹션 — Step 1·2의 실제 결과만 기록.

- [ ] **Step 4:** 커밋 `docs: record round 2 verification (prd-diff, test-result-report)` → `git status --short` clean 확인.

---

## 남은 라운드

Round 3 (`qa-exploratory-charter`, `qa-automation-candidates`, `qa-bug-report`)는 별도 계획. 설계는 v2 설계 문서에 확정되어 있다.
