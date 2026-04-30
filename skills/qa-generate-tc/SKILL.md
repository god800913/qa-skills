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
