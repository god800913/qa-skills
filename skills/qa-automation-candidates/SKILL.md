---
name: qa-automation-candidates
description: TC xlsx의 Automation Check 컬럼과 실행 결과 이력을 바탕으로 자동화 전환 후보 TC를 우선순위로 추천 (반복 빈도·수동 비용·안정성 기준). Automation TC_ID가 이미 있는 행은 제외. 트리거 — "자동화 후보", "뭐부터 자동화하지", "/qa:automation-candidates".
---

# qa:automation-candidates

수동 TC 중 자동화로 옮길 후보를 골라 우선순위를 매긴다.

## 입력
- TC xlsx + 탭 (필수 — 여러 탭 가능)
- 실행 결과 (옵션 — `qa:test-result-report` 출력 md, 또는 실행 완료 xlsx면 `scripts/parse_results.py`로 직접 집계)

## 워크플로우

### 1. 후보 풀 추출
```bash
uv run python scripts/inspect_master.py <xlsx>                  # 탭 목록
uv run python scripts/extract_tc_table.py <xlsx> --tab "<탭>"   # 행 추출
```
필터: `Automation Check`가 All/iOS/Android인 행 중 **`Automation TC_ID`가 비어 있는 행만**.
- `Skip` 행과 이미 자동화된 행(`Automation TC_ID` 존재)은 후보에서 제외.
- `Automation Check`가 비어 있는 행은 "분류 미정"으로 별도 목록.

### 2. 우선순위 판단 (LLM)
| 기준 | 높음 (우선) | 낮음 (후순위) |
|---|---|---|
| 반복 빈도 | P1·P2 — 회귀마다 실행 | P4 — 가끔 실행 |
| 수동 비용 | Test Step 줄 수 많음, Remote Config 셋업 필요 | 한 줄 확인 |
| 안정성 | Expected Result가 결정론적 (UI 노출·텍스트) | 실시간·매치·타이밍 의존 — flaky 위험 |
| 결과 이력 (있으면) | 꾸준히 Pass — 안정적 | Fail/Block 잦음 — 자동화 전 안정화 필요 표시 |

### 3. 출력 (md)
```markdown
## 자동화 후보 — <탭/릴리즈>
### 요약
(후보 N건 / 제외 M건 — 한 줄 결론)
### 우선순위
| 순위 | TC_ID | Test Summary | Automation Check | 근거 | 비고 |
### 분류 미정 / 제외 요약
(Automation Check 공란 목록, Skip 사유 분포)
```

### 4. 다음 액션 안내
"이 목록을 자동화 팀과 공유하고, 전환 확정되면 마스터의 `Automation TC_ID` 컬럼을 채우세요 (다음 실행부터 후보에서 자동 제외됩니다)."

## 비목표
- 자동화 코드 작성, TC 품질 검수 (그건 `qa:review-tc`), 실행 결과 집계 리포트 (그건 `qa:test-result-report`)
- xlsx 수정 — `Automation TC_ID` 기입은 사람이 직접

## 예시
`examples/sample-candidates.md` 참조.
