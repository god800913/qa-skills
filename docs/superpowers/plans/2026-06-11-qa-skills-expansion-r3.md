# QA Skills Expansion R3 Implementation Plan

> **For agentic workers:** REQUIRED: Use superpowers:subagent-driven-development (if subagents available) or superpowers:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 설계(`docs/plans/2026-06-11-qa-skills-expansion-v2-design.md`)의 Round 3 — `qa-exploratory-charter`, `qa-automation-candidates`, `qa-bug-report` 출시로 확장 로드맵 완결.

**Architecture:** 3종 모두 md-only 스킬 (신규 결정론 스크립트 없음 → 신규 pytest 없음). 기존 shared 스크립트(extract_tc_table, inspect_master, parse_results)를 placeholder sync로 재사용. bug-report만 외부 쓰기 액션(Jira)이 있으므로 **사용자 컨펌 게이트를 SKILL.md에 강제**한다.

**Tech Stack:** Markdown 스킬 정의, 기존 shared 스크립트 재사용, Atlassian MCP (bug-report의 Jira 초안 — 옵션).

**저장소 규약 (공통):** 한국어, `<type>: <description>` 커밋, 태스크마다 커밋, main 직커밋, push 금지. 예시 TC_ID는 표준 `<섹션>-<순번>` 형식. "라운지 선물하기/추천" 서사·`enableLoungeGift` 플래그·JIRA-2202/2203 번호는 기존 예시들과 정합 유지. 작업 디렉토리 `/Users/dongjin/Dropbox/workplace/HyperConnect/poc/qa-skills`.

**현재 기준선:** 테스트 68개 PASS, `sync_shared.py --check` exit 0, 스킬 9종 출시.

---

### Task 1: `qa-exploratory-charter` 번들

**Files:**
- Create: `skills/qa-exploratory-charter/SKILL.md`
- Create: `skills/qa-exploratory-charter/examples/sample-charters.md`
- Create: `skills/qa-exploratory-charter/reference/risk-taxonomy.md` (placeholder→sync)

- [ ] **Step 1: SKILL.md 작성**

````markdown
---
name: qa-exploratory-charter
description: 리스크 분석 리포트(또는 PRD)를 바탕으로 탐색적 테스트 세션 차터(목표·범위·비범위·타임박스·기록 항목)를 생성. 스크립트 TC가 못 잡는 복합 상태 전이·비정상 입력·타이밍 영역에 집중. 트리거 — "탐색적 테스트", "차터 만들어", "익스플로러토리 세션", "/qa:exploratory-charter".
---

# qa:exploratory-charter

스크립트 TC의 사각지대를 탐색하는 세션 차터를 만든다.

## 입력
- 리스크 분석 리포트 (`qa:risk-analysis` 출력, 강력 권장) 또는 PRD/변경 요약 (필수)
- 세션 가능 시간·인원 (옵션 — 기본: 세션당 60분, 릴리즈당 차터 3~5개)

## 워크플로우

### 1. 차터 대상 선정
`reference/risk-taxonomy.md` 영역 중 **스크립트 TC로 커버하기 어려운 것**을 우선:
- 복합 상태 전이 (로그인 상태 × Remote Config × 네트워크 품질 조합)
- 비정상 입력·중단 (백그라운드 전환, 콜 중 전화 수신, 빠른 연타, 화면 회전)
- 타이밍·동시성 (동시 요청, 타임아웃 경계, 푸시 수신 타이밍)
이미 TC로 잘 커버되는 정상 플로우는 차터 **비범위**로 명시한다.

### 2. 차터 작성
차터 1개 = 세션 1개. 각 차터:
- **목표**: 한 문장 — "~상태에서 ~를 탐색한다"
- **범위 / 비범위**: 어디까지 건드리고 어디는 안 건드리는지
- **시작 지점**: 첫 화면·계정 상태·플래그 설정
- **타임박스**: 30~90분 (기본 60)
- **기록 항목**: 발견 이슈, 예상 밖 동작, 후속 TC 후보

### 3. 출력 (md)
```markdown
## 탐색적 테스트 차터 — <기능/릴리즈>
### 차터 요약
| # | 목표 | 연계 리스크 | 타임박스 |
### 차터 N: <제목>
(목표/범위/비범위/시작 지점/타임박스/기록 항목)
```

### 4. 다음 액션 안내
"발견한 이슈는 `qa:bug-report`로 리포트하고, 반복 가치가 있는 발견은 `qa:generate-tc`로 정식 TC화하세요."

## 비목표
- 스크립트 TC 작성 (그건 `qa:generate-tc`), 리스크 식별 자체 (그건 `qa:risk-analysis`)
- 세션 실행·결과 기록 대행

## 예시
`examples/sample-charters.md` 참조.
````

- [ ] **Step 2: 예시 작성** — `examples/sample-charters.md`: "라운지 선물하기" 리스크 리포트(risk-analysis 예시의 Blocker 결제 이중 차감 / Major 플래그 off·iOS 권한)를 입력으로 받은 차터 3개: ① 결제 중단·재시도 탐색(연타·네트워크 끊김·백그라운드 전환 — 이중 차감 리스크 연계, 60분) ② `enableLoungeGift` 플래그 토글 타이밍 탐색(사용 중 off 전환, 45분) ③ iOS 권한 상태 전이 탐색(거부→설정 변경→복귀, 45분). 섹션 3 형식 그대로, 40줄 내외, 기존 예시 톤.

- [ ] **Step 3: placeholder + sync + 검증 + 커밋**

```bash
mkdir -p skills/qa-exploratory-charter/{reference,examples}
touch skills/qa-exploratory-charter/reference/risk-taxonomy.md
uv run python scripts/sync_shared.py && uv run python scripts/sync_shared.py --check
git add skills/qa-exploratory-charter
git commit -m "feat(skill): add qa-exploratory-charter bundle"
```

### Task 2: `qa-automation-candidates` 번들

**Files:**
- Create: `skills/qa-automation-candidates/SKILL.md`
- Create: `skills/qa-automation-candidates/examples/sample-candidates.md`
- Create: `skills/qa-automation-candidates/scripts/{extract_tc_table,inspect_master,parse_results}.py` (placeholder→sync)

- [ ] **Step 1: SKILL.md 작성**

````markdown
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
````

- [ ] **Step 2: 예시 작성** — `examples/sample-candidates.md`: 가상 라운지 탭(TC 12건: All 5 / Skip 4 / 공란 2 / 이미 자동화 1)에서 후보 5건 추출, 우선순위 표(1~5위, 표준 TC_ID 형식, 근거에 4기준 반영, Fail 이력 1건은 "안정화 후 전환" 비고), 분류 미정 2건 + Skip 사유 분포. 섹션 3 형식 그대로, 35줄 내외.

- [ ] **Step 3: placeholder + sync + 검증 + 커밋**

```bash
mkdir -p skills/qa-automation-candidates/{scripts,examples}
touch skills/qa-automation-candidates/scripts/{extract_tc_table,inspect_master,parse_results}.py
uv run python scripts/sync_shared.py && uv run python scripts/sync_shared.py --check
uv run python skills/qa-automation-candidates/scripts/extract_tc_table.py tests/fixtures/sample_tc_with_issues.xlsx --tab TabA | head -3
git add skills/qa-automation-candidates
git commit -m "feat(skill): add qa-automation-candidates bundle"
```

### Task 3: `qa-bug-report` 번들

**Files:**
- Create: `skills/qa-bug-report/SKILL.md`
- Create: `skills/qa-bug-report/reference/bug-template.md`
- Create: `skills/qa-bug-report/examples/sample-bug-report.md`

- [ ] **Step 1: SKILL.md 작성**

````markdown
---
name: qa-bug-report
description: Fail/Block된 TC와 보충 정보(환경·재현 빈도·로그)를 표준 버그 리포트(제목/환경/재현 단계/기대·실제 결과/심각도)로 변환. 옵션으로 Atlassian MCP로 Jira 이슈 초안 생성 — 반드시 사용자 컨펌 후. 트리거 — "버그 리포트 써줘", "이거 지라 올려", "/qa:bug-report".
---

# qa:bug-report

테스트에서 발견한 결함을 개발자가 바로 착수할 수 있는 리포트로 만든다.

## 입력
- Fail/Block된 TC 행 (xlsx 경로+탭+TC_ID, 또는 내용 직접 붙여넣기) (필수)
- 보충 정보: 발생 환경(기기·OS 버전·앱 버전), 재현 빈도(N회 중 M회), 실제 관찰 결과, 로그·스크린샷 유무
- 빠진 필수 정보(환경, 실제 결과)는 **추정하지 말고 사용자에게 묻는다**.

## 워크플로우

### 1. 리포트 작성
`reference/bug-template.md` 형식대로:
- 제목: `[영역] 증상 — 발생 조건` 한 줄
- 재현 단계: TC의 Test Step을 기반으로 하되, 실제 재현에 필요한 세부(계정 상태·플래그 값)를 보충
- 기대 결과: TC의 Expected Result 기반 / 실제 결과: 사용자 보고 그대로
- 심각도: Blocker/Major/Minor + 근거 (`risk-taxonomy` 영역 기준 — 결제·신고·핵심 플로우면 상향)
- 관련 TC_ID, 재현 빈도, 첨부 목록 명시

### 2. Jira 초안 (옵션)
- Atlassian MCP 연결 감지 (도구명에 `Jira`/`atlassian` 포함 여부).
- **컨펌 게이트 (절대 규칙)**: 작성된 리포트 전문을 사용자에게 보여주고, 프로젝트 키·이슈 타입을 확인받고, 명시적 동의("올려줘", "생성해")를 받은 후에만 `createJiraIssue` 호출. 동의 없이 생성 금지.
- 생성 후: 이슈 키를 보고하고 "마스터 xlsx의 해당 TC `Jira no.` 컬럼에 기입하세요"라고 안내 (xlsx 직접 수정은 하지 않음).
- MCP 미연결: md 리포트만 출력 + "Jira에 수동 등록 후 이슈 키를 Jira no. 컬럼에 기입하세요" 안내.

### 3. 다음 액션 안내
"수정 배포 후 해당 TC를 재실행하고, 결과는 `qa:test-result-report`로 집계하세요."

## 비목표
- 버그 수정·원인 분석 (개발 영역), xlsx 직접 수정
- 컨펌 없는 Jira 이슈 생성 (절대 금지)

## 예시
`examples/sample-bug-report.md` 참조.
````

- [ ] **Step 2: `reference/bug-template.md` 작성** — 표준 양식: 제목 규칙(`[영역] 증상 — 조건`), 필드 정의 표(환경/사전조건/재현 단계/기대·실제 결과/심각도+근거/재현 빈도/관련 TC_ID/첨부), 심각도 판정 기준(risk-taxonomy 영역 연계: 결제·신고·핵심 플로우 = Blocker~Major 상향), 좋은 제목 vs 나쁜 제목 예시 2쌍. 30줄 내외.

- [ ] **Step 3: 예시 작성** — `examples/sample-bug-report.md`: R2 서사 재사용 — "라운지 추천 섹션 딥링크 진입 시 스크롤 위치 이상" (JIRA-2202, 관련 TC `1-4`, Major). 환경(iOS 17.5 / 앱 ver118), 재현 빈도 5회 중 5회, 재현 단계 4개, 기대/실제 결과, 심각도 근거(핵심 플로우 인접이나 우회 가능 → Major), 첨부(스크린 레코딩). 마지막에 "Jira 초안 생성 전 컨펌" 대화 모습 2~3줄 포함. 35줄 내외.

- [ ] **Step 4: 검증 + 커밋**

```bash
rg "컨펌 게이트|동의 없이 생성 금지" skills/qa-bug-report/SKILL.md   # 안전장치 존재 확인
uv run python scripts/sync_shared.py --check   # exit 0 (이 번들은 shared 파일 없음)
git add skills/qa-bug-report
git commit -m "feat(skill): add qa-bug-report bundle"
```

### Task 4: Round 3 최종 검증 + README + 로드맵 완결

**Files:**
- Modify: `README.md`

- [ ] **Step 1:** `uv run pytest -q` → 68 passed (신규 테스트 없음 — 회귀만 확인). `sync_shared.py --check` → exit 0.
- [ ] **Step 2: fresh subagent smoke 3회**
  1. `qa-exploratory-charter`: qa-risk-analysis 예시 리포트(`skills/qa-risk-analysis/examples/sample-risk-report.md`)를 입력으로 → 차터 3개 형식·리스크 연계·비범위 명시 확인.
  2. `qa-automation-candidates`: `sample_tc_with_issues.xlsx` TabA(번들 스크립트로 추출 — 경로는 번들 기준임을 명시) → Automation Check 필터링(Skip 제외, 빈 값 "분류 미정" 분리), 우선순위 근거 확인.
  3. `qa-bug-report`: Fail TC 1건을 **내용 붙여넣기 방식**으로 제공 (1-5, JIRA-2202 서사 — TC 행 텍스트를 smoke 지시문에 직접 포함) + 가상 보충 정보 → 템플릿 준수 + **Jira 미연결 상황에서 생성 시도 없이 수동 등록 안내**하는지, 컨펌 게이트 문구를 인지하는지 확인. (실제 Jira 생성은 smoke에서 금지 — Atlassian MCP 호출 자체를 하지 말 것을 smoke 지시에 명시)
- [ ] **Step 3: README 갱신** — 스킬 목록 3줄 추가:

```markdown
- `qa-exploratory-charter` — 탐색적 테스트 세션 차터 (Round 3, 출시 ✅)
- `qa-automation-candidates` — 자동화 전환 후보 우선순위 (Round 3, 출시 ✅)
- `qa-bug-report` — 표준 버그 리포트 + Jira 초안(컨펌 필수) (Round 3, 출시 ✅)
```

검증 이력에 `### Round 3 검증 (2026-06-11)` — Step 1·2 실제 결과만 기록. 마지막 줄에 "확장 로드맵(R0~R3) 완결 — 스킬 12종" 명시.

추가로 `skills/qa-test-result-report/SKILL.md` 비목표의 "버그 리포트 작성 (Round 3 `qa:bug-report`)"에서 출시 후 어색해진 "Round 3 " 표기를 제거 (→ "버그 리포트 작성 (그건 `qa:bug-report`)") — 같은 커밋에 포함.

- [ ] **Step 4:** 커밋 `docs: record round 3 verification — expansion roadmap complete` → `git status --short` clean.

---

## 로드맵 완결

이 계획으로 v2 설계의 4개 라운드가 모두 출시된다. 후속 후보(별도 논의): 실제 마스터 xlsx의 Result 값 실물 검증, Figma MCP 연결 후 generate-tc v2 실전 검증, qa-minimal-coverage Next Best 시트에 forced_overflow 표면화.
