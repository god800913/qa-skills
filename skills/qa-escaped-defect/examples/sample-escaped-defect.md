# 예시: qa:escaped-defect 출력 (갭 유형 C)

## 유출 결함 분석 — 선물 결제 중 백그라운드 전환 시 이중 차감

### 버그 요약
- **증상**: 선물 결제 진행 중 앱을 백그라운드로 전환했다 복귀하면 잼이 이중 차감됨
- **환경**: iPhone 14 / iOS 17.5 / 앱 ver118, `enableLoungeGift` ON
- **영역**: 선물하기 — 결제 (출처: Jira AZAR-4821)

### 관련 TC 추적 (Shop 탭, ver118 실행분)

| TC_ID | Test Summary | 당시 Result | 버그 시나리오와의 차이 |
|---|---|---|---|
| SH-12 | 선물 결제 완료 후 잔액 갱신 | Pass | 정상 플로우만 — 백그라운드 전환 없음 |
| SH-15 | 결제 중 네트워크 끊김 | Pass | 네트워크 단절은 커버, 앱 상태 전환은 미커버 |

### 갭 유형: C — 실행했으나 못 잡음
결제 플로우 TC는 존재하고 실행도 됐으나, **"결제 진행 중 백그라운드 전환 → 복귀" 타이밍 조건이 어느 TC의 Test Step에도 없음**. 결제류는 risk-taxonomy 기준 Blocker 영역이므로 상태 전이 변형이 기본 커버 대상이어야 함.

### 보강 TC 후보

| Priority | OS | Test Item | Test Summary | Pre-condition | Test Step | Expected Result | Comment |
|---|---|---|---|---|---|---|---|
| P1 | All | 결제 | 결제 중 백그라운드 전환 후 복귀 시 단일 차감 | 잼 보유, enableLoungeGift ON | 1. 선물 결제 시작<br>2. 결제 진행 중 홈 버튼으로 백그라운드 전환<br>3. 5초 후 복귀 | 결제 1회만 처리, 잼 단일 차감, 결제 내역 1건 | 유출 버그 AZAR-4821 회귀 방지 |
| P2 | All | 결제 | 결제 중 앱 강제 종료 후 재진입 | 잼 보유, enableLoungeGift ON | 1. 선물 결제 시작<br>2. 결제 진행 중 앱 강제 종료<br>3. 재실행 후 선물함 확인 | TBD (PM 확인 필요) | (Blocker) 미완료 결제의 복구 정책 미정의 — 자동 취소인지 재시도 안내인지 |

### 프로세스 제안
1. 결제·신고 등 Blocker 영역 TC에는 상태 전이 변형(백그라운드·강제 종료·타이밍)을 기본 포함 — `qa:generate-tc` 휴리스틱으로 반영 검토
2. `qa:exploratory-charter`에서 결제 영역 상태 전이 차터를 다음 릴리즈에 우선 배치

### 다음 액션
보강 TC 후보는 `qa:generate-tc`에 이 리포트를 입력으로 넘기면 핸드오프 규약으로 반영됩니다.
