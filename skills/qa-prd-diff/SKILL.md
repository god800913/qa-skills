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
- 스냅샷 파일 읽기. 현재 PRD가 Notion URL이면 `reference/notion-fetch-policy.md`에 따라 fetch (도구 런타임 감지·내부 링크 1-depth follow·소스 매니페스트 의무)하고, **fetch 직후 새 스냅샷도 저장** — 규약은 `reference/snapshot-convention.md`.
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
- **형식 노이즈는 변경점에서 제외**: 구 스냅샷이 규약 이전(LLM 재서술본)이면 문장 표현·순서·헤더 구조 차이가 대량 발생 — `reference/snapshot-convention.md` §4에 따라 의미가 달라진 항목만 보고. 메타헤더(`---` 블록)도 비교 제외.

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
- 이 리포트를 `qa:generate-tc`에 입력으로 넘기면 **Open Questions는 모호점 핸드오프 규약으로 승계**된다: 기대 결과를 정할 수 없는 항목 → Expected Result `TBD (PM 확인 필요)` + Comment `(Blocker) <질문 요약>`, 가정 가능 항목 → 가정을 Expected Result에 + Comment `가정: ...`.

## 비목표
- TC 작성·수정 자체 (그건 `qa:generate-tc`), PRD 모호점 분석 (그건 `qa:prd-clarify`)
- Notion 페이지 버전 히스토리 조회 (MCP 미지원 — 스냅샷 규약이 그 대체물)

## 예시
`examples/sample-prd-diff.md` 참조.
