# 예시: qa:review-tc 출력

`tests/fixtures/sample_tc_with_issues.xlsx` (TabA 8개 TC 행, 의도적 이슈 포함)를 입력으로 받았을 때 기대되는 리포트.

---

## TC 리뷰 리포트 — TabA

### 요약
- 총 TC: 7
- Blocker: 0 / Major: 5 / Minor: 1

### Major
1. [포맷] 행 6 (TC_ID 1-3) — Priority 비어있음. P1~P4 중 하나로 지정 필요.
2. [포맷] 행 7 (TC_ID 1-4) — Expected Result 비어있음. 관찰 가능한 결과 명시 필요.
3. [포맷] 행 5 (TC_ID 1-2) — TC_ID 1-2가 2회 등장 (rows [4, 5]). 두 번째를 1-3으로 또는 자동 패치 권장.
4. [탭 내 중복] 행 3·4 — Test Summary "메인 진입" 동일. 차별화 필요 (예: "메인 진입 — 신규 가입자").
5. [탭 간 중복] TabA 1-6 ↔ TabB 1-3 — Test Summary "차단 사용자 제외" 동일. 어느 탭이 정본인지 결정 후 다른 쪽 삭제 또는 컨텍스트 차별화.

### Minor
1. [포맷] 행 8 (TC_ID 1-5) — OS 'MacOS'는 허용 enum 아님 (iOS/And/Android/All/공란).

### 자동 패치 가능 항목
다음 1건은 `--patch` 옵션으로 자동 수정 가능:
- TC_ID 1-2 중복 → 두 번째를 1-2-dup-1로 임시 변경 (사람이 최종 ID 부여 권장)

나머지 이슈는 사람 판단 필요.
