---
name: qa-generate-tc
description: Notion PRD(+옵션 Figma 디자인)를 분석해서 표준 14컬럼 QA 테스트케이스를 xlsx로 생성. 신규 시트 모드 또는 기존 마스터 xlsx에 append 모드 지원. 사람 컨펌 루프 필수. 트리거 — "테스트 케이스 생성", "TC 만들어", "PRD에서 TC 뽑아", "/qa:generate-tc".
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
- **[fetch 성공 시]** PRD 본문을 md 스냅샷으로 저장: 기본 `./prd-snapshots/<기능명>-<YYYYMMDD>.md` (기능명은 Notion 페이지 제목 또는 PRD 첫 H1에서 추출 — 공백은 하이픈으로, 특수문자 제거) (사용자가 다른 경로를 지정하면 그에 따름. 디렉토리 없으면 생성, 날짜는 `date '+%Y%m%d'`로 구함 — 암산 금지). 저장 경로를 사용자에게 알린다. 이 스냅샷은 나중에 `qa:prd-diff`가 PRD 변경분 분석에 사용한다.

### 1.5 Figma 보강 (옵션)
- 사용자가 Figma 링크를 줬거나 PRD에 Figma 임베드가 있으면 (임베드를 발견한 경우 사용자에게 알린 뒤) → 연결된 Figma MCP 도구를 감지 (도구명에 `figma` 포함 여부). 사용법·URL 파싱·반영 규칙은 `reference/figma-usage.md` 참조.
- 연결됨: 프레임 구조·실제 텍스트·상태별 화면(빈/에러/로딩)을 읽어 Test Step·Expected Result를 화면 기준으로 구체화. 디자인에만 있는 상태는 TC로 만들되 Comment에 "PRD 미정의, 디자인 기준" 명시. PRD와 디자인 간 불일치 처리 규칙은 `reference/figma-usage.md` 참조.
- 미연결: 진행을 막지 않는다. "Figma MCP를 연결하면 UI 상태 커버리지가 좋아집니다" 한 줄 안내 후 PRD 단독 모드.

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
