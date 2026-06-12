---
name: qa-result-diff
description: 회차별로 실행 완료된 TC xlsx 2개 이상을 TC_ID 기준으로 비교해 신규 Fail/연속 Fail/회복/flaky 의심/신규·제거 TC를 분류하고 pass rate 추이를 md 리포트로 정리. 릴리즈 간 "뭐가 새로 깨졌는지" 볼 때 사용. 트리거 — "결과 비교", "지난 회차랑 비교", "뭐가 새로 깨졌어", "flaky 찾아", "/qa:result-diff".
---

# qa:result-diff

같은 탭의 실행 결과를 회차 간 비교한다. 신규 Fail·연속 Fail·회복·flaky 의심을 골라내 "이번 릴리즈에서 무엇이 나빠졌고 무엇이 돌아왔는지"를 한 장으로 만든다.

## 입력
- 회차 순서대로 `(xlsx 경로, 탭)` 쌍 **2개 이상** (필수). 같은 파일의 다른 탭도 허용
- 탭 이름을 모르면 `scripts/inspect_master.py`로 각 파일의 탭 목록을 보여주고 선택받기
- `--labels` 회차 라벨 (옵션, 기본 "회차 1..N" — 릴리즈 버전명 권장)

## 워크플로우

### 1. 결정론 비교
```bash
uv run scripts/diff_results.py <r1>.xlsx <탭1> <r2>.xlsx <탭2> [...] --labels v117,v118
```
JSON 결과:
- TC별 이력 행렬 + **상호 배제 7분류** (마지막 회차 기준): `new_fail` / `persistent_fail` / `recovered` / `still_pass` / `not_run` / `new_tc` / `removed_tc`
- **`flaky` 직교 플래그**: 실측값({Pass,Fail,Block})만 남긴 이력에서 Pass↔Fail/Block 전환 2회 이상 (회차 3개 이상부터 의미)
- 회차별 pass rate (= Pass/(Pass+Fail+Block), N/T·N/A·미입력·unknown 분모 제외)
- `warnings`: TC_ID 없는 행 제외 건수, ID 재사용 의심 (동일 ID인데 Test Summary 불일치)

### 2. 리포트 합성 (LLM)
```markdown
## 결과 비교 — <탭> (<라벨1> → <라벨N>)
### 요약
(한 줄: 신규 Fail n건·회복 m건, pass rate 추이 x% → y%)
### 신규 Fail (new_fail) — 최우선 확인
| TC_ID | Test Summary | 이력 | flaky |
### 연속 Fail (persistent_fail)
### flaky 의심
### 회복 (recovered) / 신규·제거 TC / 미실행
### 공통 영역 가설
(new_fail·flaky를 섹션·키워드로 묶은 LLM 추정 — 추정임을 명시)
### 경고
(warnings 내용 — ID 재사용 의심은 사람 확인 필요)
```
- 분류·수치는 스크립트 JSON 그대로 옮긴다 — LLM이 재집계하지 않는다.
- unknown 값이 있으면 리포트 전에 사용자에게 확인 (임의 재분류 금지 — `reference/format-rules.md`).

### 3. (원하면) 요약 xlsx
분류별 목록 + pass rate 추이를 시트로:
```bash
uv run scripts/summary_xlsx.py --sheets /tmp/diff_sheets.json --output <out>.xlsx
```
stdout 마지막 줄이 실제 출력 경로 (collision 시 `(2)` 접미사).

### 4. 다음 액션 안내
- `new_fail`·`persistent_fail` → `qa:bug-report`로 리포트 작성
- 릴리즈 판단이 목적이면 → 마지막 회차 리포트(`qa:test-result-report`)와 함께 `qa:release-checklist`
- flaky 의심 → 자동화/환경 점검 대상으로 표시 (원인 분석은 비목표)

## 비목표
- 단일 회차 집계 (그건 `qa:test-result-report`)
- flaky의 코드 레벨 원인 분석, Jira 자동 갱신, 결과 입력 대행

## 트러블슈팅
- 두 회차의 TC 구성이 크게 다르면 (`new_tc`+`removed_tc`가 과반) — 같은 탭의 회차가 맞는지 사용자에게 확인
- ID 재사용 의심 경고 → 해당 TC는 비교 신뢰도가 낮음을 리포트에 명시

## 예시
`examples/sample-result-diff.md` 참조.
