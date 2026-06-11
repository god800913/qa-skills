---
name: qa-test-result-report
description: 실행 완료된 QA TC xlsx의 Result 컬럼(Pass/Fail/Block/N/T/N/A)을 집계해 탭·섹션·Priority별 통과율, Fail/Block 목록(Jira 링크), 미실행·잔여 리스크를 md 리포트로 정리. qa:release-checklist의 입력으로 바로 사용 가능. 트리거 — "테스트 결과 정리", "결과 리포트", "통과율 뽑아", "/qa:test-result-report".
---

# qa:test-result-report

실행이 끝난 TC 워크북에서 QA 결과 리포트를 만든다.

## 입력
- 실행 완료된 TC xlsx + 탭 이름 (필수). 탭 미지정 시 `scripts/inspect_master.py`로 목록 보여주고 선택.
- 릴리즈/기능 이름 (리포트 제목용, 옵션)

## 워크플로우

### 1. 집계 (결정론)
```bash
uv run python scripts/parse_results.py <xlsx> --tab "<탭>"
```
JSON 결과: total, counts(enum별+미입력+unknown), pass_rate(= Pass/(Pass+Fail+Block)), by_priority, by_section, fails/blocks(tc_id·summary·Jira), unknown(원래 값 포함).

### 2. unknown 처리 (필수)
unknown이 1건이라도 있으면 **리포트 작성 전에** 사용자에게 원래 값 목록을 보여주고 의미를 확인받는다 (예: "성공"이 Pass 의미인지). 임의 재분류 금지 — 사용자가 정정하면 xlsx를 고친 뒤 재집계하라고 안내.

### 3. 리포트 작성 (LLM)
```markdown
## 테스트 결과 리포트 — <릴리즈/기능>
### 총괄
(한 줄 결론: 통과율 + Fail/Block 핵심)
| 구분 | Pass | Fail | Block | N/T | N/A | 미입력 | 통과율 |
### Fail / Block 상세
| TC_ID | Test Summary | 구분 | Jira |
### 미실행·잔여 리스크
(N/T·미입력이 몰린 섹션 — `reference/format-rules.md`의 enum 정의 참조, 섹션·Priority 분포에서 P1 미실행은 강조)
### 경고
(unknown 값, 데이터 품질 이슈)
```

### 4. 다음 단계 안내
"이 리포트를 `qa:release-checklist`의 TC 실행 결과 입력으로 쓸 수 있습니다."

## 비목표
- 릴리즈 판정 (그건 `qa:release-checklist`), 버그 리포트 작성 (그건 `qa:bug-report`)
- xlsx 수정 — Result 정정은 사람이 직접

## 예시
`examples/sample-result-report.md` 참조.
