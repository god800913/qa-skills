# 예시: qa:result-diff 출력 (Shop 탭, v116 → v117 → v118)

3회차 비교. `diff_results.py` JSON을 받아 합성한 리포트 형태.

## 결과 비교 — Shop (v116 → v118)

### 요약
신규 Fail **2건**, 연속 Fail 1건, flaky 의심 1건. pass rate **96.2% → 97.1% → 91.4%** — v118에서 하락, 신규 Fail이 원인.

### 신규 Fail (new_fail) — 최우선 확인

| TC_ID | Test Summary | 이력 (v116→v118) | flaky |
|---|---|---|---|
| SH-12 | 선물 결제 완료 후 잔액 갱신 | Pass → Pass → **Fail** | |
| SH-31 | 선물함 딥링크 진입 | Pass → N/T → **Fail** | |

### 연속 Fail (persistent_fail)

| TC_ID | Test Summary | 이력 | flaky |
|---|---|---|---|
| SH-07 | 매치 콜 실패 복구 | Fail → Fail → **Fail** | |

### flaky 의심 (전환 2회 이상)

| TC_ID | Test Summary | 이력 | 분류 |
|---|---|---|---|
| SH-19 | 선물함 목록 정렬 | Pass → Fail → **Pass** | recovered |

### 회복 / 신규·제거 TC / 미실행
- 회복(recovered): SH-19 1건 (위 flaky 의심과 동일 — 안정성 재확인 권장)
- 신규 TC(new_tc): SH-44 (v118에서 추가, Pass)
- 미실행(not_run): SH-28 (v118 N/T — v117까지 Pass)

### 공통 영역 가설 (LLM 추정)
신규 Fail 2건(SH-12 결제 잔액, SH-31 딥링크)은 섹션이 다르지만 둘 다 **화면 복귀 후 상태 갱신** 경로를 지난다. v118의 라이프사이클 변경 영향 가능성 — 확인 필요한 추정임.

### 경고
- v117 파일에서 TC_ID 없는 행 1건 제외
- ID 재사용 의심 없음

### 다음 액션
- SH-12·SH-31 → `qa:bug-report`
- 릴리즈 판단 → `qa:test-result-report`(v118) + 이 리포트로 `qa:release-checklist`
