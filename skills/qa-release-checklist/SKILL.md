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
- **blocked**: Blocker 게이트(G1) 실패 또는 G1 확인 불가.
- **conditional**: Major 미해결이 있으나 risk-accept 가능(조건 명시), 또는 G2~G7 중 실패·확인 불가가 1개 이상.
- **ready**: 전 게이트 통과 + 확인 불가 0건. 예외 없음 — 정보가 부족하면 ready 대신 conditional로 내리고 채워야 할 조건을 명시한다.

### 3. 출력 (md)
판정 + 게이트별 표 (통과/실패/확인 불가 + 근거) + blocker 조건 + rollout/rollback 체크 + 잔여 known issue.

## 비목표
- TC 결과 집계 (그건 `qa:test-result-report`), 릴리즈 자체 실행/배포

## 예시
`examples/sample-release-checklist.md` 참조 (ready / conditional / blocked 3가지 모양).
