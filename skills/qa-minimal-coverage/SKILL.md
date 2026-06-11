---
name: qa-minimal-coverage
description: 기존 QA TC xlsx에서 리스크 커버를 최대화하는 최소 실행 TC 세트를 결정론 스코어링으로 골라 5시트 xlsx(Selected/Coverage/Excluded/Next Best/Assumptions)로 저장. 제한된 시간에 어떤 TC를 돌릴지 결정할 때 사용. 트리거 — "최소 TC", "시간 없는데 뭐 돌려", "TC 줄여줘", "/qa:minimal-coverage".
---

# qa:minimal-coverage

TC 품질 검수(`qa:review-tc`)가 끝난 워크북에서 실행 부분집합을 고른다. 기본 목표는 **리스크 커버리지 최대화** (실행 시간 최소화는 명시 요청 시에만).

## 입력
- TC xlsx + 탭 이름 (필수)
- `--max-cases N`, 시간 제약 (옵션)
- `--next-best N` — Next Best 추천 개수 (옵션, 기본 5)
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
