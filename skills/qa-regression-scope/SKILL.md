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
uv run scripts/inspect_master.py <master>.xlsx          # 탭 목록
uv run scripts/extract_tc_table.py <master>.xlsx --tab <name>  # 탭별 TC
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
uv run scripts/summary_xlsx.py --sheets /tmp/scope_sheets.json --output <out>.xlsx
```

## 비목표
- 개별 TC 선별·최적화 (그건 `qa:minimal-coverage`)
- TC 신규 작성

## 예시
`examples/sample-regression-scope.md` 참조.
