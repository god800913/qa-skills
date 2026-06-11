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
