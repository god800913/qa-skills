# 예시: 테스트 결과 리포트 — 실행 샘플 (TabExec)

> 입력: `tests/fixtures/sample_tc_executed.xlsx` TabExec (10건)
> 집계: `uv run python scripts/parse_results.py tests/fixtures/sample_tc_executed.xlsx --tab TabExec`

---

## 테스트 결과 리포트 — 실행 샘플

### 총괄

통과율 **66.7%** (Pass 4 / 실행 6건). Fail 1건·Block 1건 미해소 상태 — 릴리즈 전 확인 필요.

| 구분 | Pass | Fail | Block | N/T | N/A | 미입력 | 통과율 |
|---|---|---|---|---|---|---|---|
| 전체 | 4 | 1 | 1 | 1 | 1 | 1 | 66.7% |
| 섹션 1 | 4 | 1 | 1 | 1 | 1 | 1 | 66.7% |

> **통과율 = Pass / (Pass+Fail+Block) — N/T·N/A·미입력 제외** (= 4/6 = 66.7%)

### Fail / Block 상세

| TC_ID | Test Summary | 구분 | Jira |
|---|---|---|---|
| 1-5 | 샘플 케이스 5 | Fail | JIRA-2202 |
| 1-6 | 샘플 케이스 6 | Block | JIRA-2203 |

### 미실행·잔여 리스크

- **N/T 1건** (1-7): 미실행. 릴리즈 전 실행 여부 확인.
- **N/A 1건** (1-9): 해당 없음 처리. 근거 코멘트 권장.
- **미입력 1건** (1-10): Result 미기입 — 실행 여부 확인 필요.

### 경고

- **unknown 1건** (1-8, 원래 값: `"성공"`): 팀 표준 enum(`Pass/Fail/Block/N/T/N/A`) 외 값.
  사용자 확인 필요 — "성공"이 Pass를 의미하면 xlsx를 수정한 뒤 재집계하세요.
  임의 재분류 금지.

---

이 리포트를 `qa:release-checklist`의 TC 실행 결과 입력으로 쓸 수 있습니다.
