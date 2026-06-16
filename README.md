# qa-skills

Hyperconnect Azar QA 팀용 Claude Skills 모음 (PoC).

PRD 검토부터 테스트케이스 작성·검수, 실행 계획, 결과 집계, 릴리즈 sign-off까지 QA 업무 생애주기 전반을 14개 스킬로 커버한다. 각 스킬은 Claude가 자연어 트리거(예: "리스크 분석해줘", "TC 만들어")로 자동 호출하며, 결정론이 중요한 부분(xlsx 파싱·포맷 검증·집계)은 Python 스크립트가, 판단이 필요한 부분(리스크 등급·커버리지·톤)은 LLM이 맡는 하이브리드 구조다.

> **운영 환경**: 팀의 TC 마스터는 14컬럼 표준 xlsx(Google Sheets). PRD는 Notion, 디자인은 Figma, 버그 트래킹은 Jira. 각 외부 시스템은 MCP로 연결되며, Figma·Jira는 미연결 시 해당 단계만 건너뛰고 진행한다. 단 Notion PRD가 **필수 입력**인 스킬은 건너뛸 수 없으므로 본문 직접 붙여넣기를 요청하고 중단한다 (`shared-reference/notion-fetch-policy.md`).

---

## 워크플로우 — 14개 스킬이 맞물리는 방식

```
① PRD 분석            ② TC 작성·검수         ③ 실행 계획              ④ 실행·릴리즈            ⑤ 유지보수
─────────────         ─────────────         ─────────────           ─────────────           ─────────────
qa-prd-clarify   ──┐  qa-generate-tc   ──┐  qa-regression-scope ─┐  qa-test-result-report ┐  qa-prd-diff
qa-risk-analysis ──┴─▶ qa-review-tc    ──┴─▶ qa-minimal-coverage ─┼─▶ qa-bug-report        ┼─▶ qa-result-diff
                                            qa-exploratory-charter┘  qa-release-checklist  ┘  qa-escaped-defect
                                                                                              qa-master-health
```

각 스킬은 끝에서 **다음에 쓸 스킬**을 안내한다. 예: `qa-prd-clarify` → `qa-generate-tc` → `qa-review-tc` → `qa-minimal-coverage` → 실행 → `qa-test-result-report` → `qa-release-checklist`. PRD가 개정되면 `qa-prd-diff`로 영향 범위를 잡아 ②로 되돌아온다.

---

## 스킬 목록

각 스킬의 트리거 문구·전체 워크플로우는 해당 `skills/<name>/SKILL.md`에, 출력 예시는 `examples/`에 있다.

### ① PRD 분석 — TC를 짜기 *전*

#### `qa-prd-clarify` — PRD 모호점 → PM 질문 리스트
PRD를 QA 관점으로 검수해 모호점·누락 엣지·미정의 상태를 뽑아 PM에게 돌려보낼 질문 리스트로 만든다.
- **입력**: Notion PRD URL 또는 본문 붙여넣기
- **처리**: `reference/ambiguity-checklist.md`의 10개 카테고리 점검 + `domain-glossary.md`(라운지/매치/미러/Pre-screening 등 Azar 용어) 참조, 심각도(Blocker/Major/Minor) 분류
- **출력**: 심각도별 모호점 md + **PM에게 그대로 복붙할 메모**
- **부수효과**: PRD 본문을 `./prd-snapshots/<기능명>-<YYYYMMDD>.md`로 저장 → 나중에 `qa-prd-diff`가 비교 기준으로 사용
- **트리거**: "PRD 검토해줘", "PRD에서 모호한 부분 찾아", "PM에게 물어볼 거 정리"

#### `qa-risk-analysis` — 리스크 매트릭스 (md + xlsx)
릴리즈/기능의 고위험 영역을 식별해 테스트 집중 범위를 제안한다.
- **입력**: PRD(Notion URL/본문) 또는 변경 요약 (필수), 도메인 노트·이전 장애 이력 (옵션)
- **처리**: `reference/risk-taxonomy.md` 영역별로 영향도 × 발생가능성 = 등급(Blocker/Major/Minor/Info). PRD에 없는 내용은 "가정"으로 분리
- **출력**: 리스크 매트릭스 md + (원하면) 요약 xlsx(`summary_xlsx.py`)
- **연계**: 출력 리포트가 `qa-regression-scope`·`qa-exploratory-charter`의 강력 권장 입력
- **트리거**: "리스크 분석", "어디가 위험해", "테스트 어디에 집중"

### ② TC 작성·검수

#### `qa-generate-tc` — PRD(+Figma) → 표준 14컬럼 TC xlsx
PRD를 표준 TC 표로 변환한다. **신규 시트 모드**(빈 워크북에 새 탭 생성) / **append 모드**(기존 마스터의 특정 탭에 행 삽입, 원본은 절대 미수정) 두 가지.
- **입력**: PRD (필수), Figma 링크/임베드 (옵션), clarify·prd-diff 리포트 (옵션 — 모호점을 핸드오프 규약으로 TC에 반영), append 시 마스터 xlsx + 타겟 탭
- **처리**: `inspect_master.py`로 타겟 탭 메타(컬럼·섹션·템플릿 타입·샘플 행) 학습 → 휴리스틱(`prioritization-guide.md`)으로 P1~P4·OS·mutual 분기 → **사용자 컨펌 루프**(xlsx 만들기 전 md 미리보기) → `new_workbook.py` 또는 `append_to_master.py`
- **출력**: 14컬럼 TC xlsx (충돌 시 `(2)` 접미사 자동)
- **부수효과**: fetch 시 PRD 스냅샷 저장 (prd-clarify와 동일 규약)
- **트리거**: "테스트 케이스 생성", "TC 만들어", "PRD에서 TC 뽑아"

#### `qa-review-tc` — TC xlsx 품질 검수 (+ 옵션 자동 패치)
작성된 TC를 5개 카테고리로 검수한다: A.포맷 / B.탭 내 일관성 / C.탭 간 중복 (셋 다 결정론 스크립트) / D.커버리지 (LLM, PRD 제공 시) / E.톤·도메인 (LLM).
- **입력**: TC xlsx + `--tab` (필수), `--prd-url`(D 활성화)·`--severity`·`--patch` (옵션)
- **처리**: `validate_format.py`(필수 누락·enum 위반·TC_ID 중복) + `find_duplicates.py`(탭 내·탭 간) + `extract_tc_table.py` → LLM이 `coverage-checklist.md`로 D·E 점검
- **출력**: 심각도별 마크다운 리포트. `--patch` 시 **TC_ID 중복만** `patch_tc_ids.py`로 자동 수정해 새 xlsx로 (두 번째 이후 등장에 `-dup-N` 접미사, 원본 미수정. 필수 누락·enum·커버리지·톤은 사람 판단 영역이라 패치 안 함)
- **트리거**: "TC 리뷰", "테스트케이스 검토", "TC 문제점 찾아"

### ③ 실행 계획

#### `qa-regression-scope` — 회귀 범위 결정 (md + xlsx)
이번 변경에서 기존 TC 중 무엇을 다시 돌릴지 탭·섹션 단위로 판정한다.
- **입력**: PRD/변경 요약 + 기존 TC xlsx (필수), 리스크 분석 리포트 (강력 권장)
- **처리**: `reference/scope-rules.md` 적용 → Required(직접 영향 + Blocker 영역) / Optional / Skipped(생략 근거·잔여 리스크 기록 필수) / Open Questions
- **출력**: 4분류 md + (원하면) 요약 xlsx
- **트리거**: "회귀 범위", "리그레션 어디까지"

#### `qa-minimal-coverage` — 최소 실행 TC 세트 (5시트 xlsx)
검수가 끝난 워크북에서 리스크 커버리지를 최대화하는 실행 부분집합을 결정론 스코어링으로 고른다.
- **입력**: TC xlsx + 탭 (필수), `--max-cases N`·시간 제약·`--next-best N` (옵션)
- **처리**: `select_minimal_coverage.py` — P1·고위험 키워드 강제 포함 후 greedy 커버 확대 (`scoring-rules.md`)
- **출력**: 5시트 xlsx (Selected / Coverage / Excluded / Next Best / Assumptions) + 잔여 리스크 경고
- **트리거**: "최소 TC", "시간 없는데 뭐 돌려", "TC 줄여줘"

#### `qa-exploratory-charter` — 탐색적 테스트 세션 차터
스크립트 TC가 못 잡는 복합 상태 전이·비정상 입력·타이밍 영역을 탐색하는 세션 차터를 만든다.
- **입력**: 리스크 분석 리포트 (강력 권장) 또는 PRD/변경 요약 (필수), 세션 시간·인원 (옵션, 기본 60분/3~5개 차터)
- **처리**: `risk-taxonomy.md`에서 **스크립트로 커버 어려운 영역** 우선 선정 (이미 TC로 커버되는 정상 플로우는 비범위로 명시)
- **출력**: 차터별 목표/범위/비범위/시작 지점/타임박스/기록 항목 md
- **연계**: 발견 이슈 → `qa-bug-report`, 반복 가치 → `qa-generate-tc`로 정식 TC화
- **트리거**: "탐색적 테스트", "차터 만들어", "익스플로러토리 세션"

### ④ 실행·릴리즈

#### `qa-test-result-report` — 실행 결과 집계 리포트
실행이 끝난 워크북의 `Result` 컬럼을 집계해 통과율·Fail/Block 목록·잔여 리스크를 정리한다.
- **입력**: 실행 완료 TC xlsx + 탭 (필수), 릴리즈/기능 이름 (옵션)
- **처리**: `parse_results.py` — total, enum별 counts, pass_rate(=Pass/(Pass+Fail+Block)), 섹션·Priority별 분포, Fail/Block 목록(Jira 링크). **unknown(표준 enum 외 값)이 1건이라도 있으면 리포트 전에 사용자 확인** (임의 재분류 금지)
- **출력**: 총괄 표 + Fail/Block 상세 + 미실행·잔여 리스크 + 데이터 품질 경고 md
- **연계**: 출력이 `qa-release-checklist`의 입력
- **트리거**: "테스트 결과 정리", "결과 리포트", "통과율 뽑아"

#### `qa-bug-report` — 표준 버그 리포트 (+ 옵션 Jira 초안)
Fail/Block된 TC를 개발자가 바로 착수할 수 있는 표준 버그 리포트로 변환한다.
- **입력**: Fail/Block TC 행 (필수) + 환경·재현 빈도·실제 결과·로그 (빠진 필수 정보는 **추정 없이 질문**)
- **처리**: `reference/bug-template.md` 형식 — 제목/환경/재현 단계/기대·실제 결과/심각도. 결제·신고·핵심 플로우면 심각도 상향
- **출력**: 버그 리포트 md. Atlassian MCP 연결 시 **컨펌 게이트 통과 후에만** Jira 이슈 생성 (프로젝트 키·이슈 타입 확인 + 명시적 동의 필수)
- **트리거**: "버그 리포트 써줘", "이거 지라 올려"

#### `qa-release-checklist` — 릴리즈 sign-off 체크리스트
QA 증거를 모아 릴리즈 판정(ready / conditional / blocked)을 내린다.
- **입력**: 릴리즈 요약/PRD + TC 실행 결과 요약 (필수, `qa-test-result-report` 출력 권장), known issue·리스크 분석 (옵션)
- **처리**: `reference/release-gates.md`의 7개 게이트(Blocker/Major/known issue/rollout/rollback/monitoring/owner) 대조. 정보 없는 게이트는 "확인 불가" (추정 통과 금지)
- **출력**: 판정 + 게이트별 통과/실패/확인불가 표 + blocker 조건 + rollout/rollback 체크 md
- **트리거**: "릴리즈 체크리스트", "출시해도 돼?", "sign-off"

### ⑤ 유지보수

#### `qa-prd-diff` — PRD 변경 → 기존 TC 영향 분류
과거 PRD 스냅샷과 현재 PRD를 비교해 변경점을 뽑고, 기존 TC 영향을 분류한다.
- **입력**: 과거 스냅샷 md (필수, 미지정 시 `./prd-snapshots/`에서 기능명 매칭 제안) + 현재 PRD (Notion URL/붙여넣기), 기존 TC xlsx (옵션 — TC_ID 단위 매핑)
- **처리**: `difflib`은 보조 신호, **의미 비교는 LLM**. 변경점을 추가/수정/삭제로, "문구만 바뀜"은 별도. TC 영향은 수정 필요/신규 필요/폐기 후보 (폐기는 후보일 뿐, 삭제는 사람이 결정)
- **출력**: 변경점 표 + TC 영향 표 + Open Questions md
- **트리거**: "PRD 뭐 바뀌었어", "스펙 변경 영향", "PRD 디프"

#### `qa-result-diff` — 회차 간 실행 결과 비교
실행 완료된 회차들을 TC_ID 기준으로 비교해 "이번에 뭐가 새로 깨졌는지"를 골라낸다.
- **입력**: 회차 순서대로 (xlsx, 탭) 쌍 2개 이상 (필수), 회차 라벨 (옵션)
- **처리**: `diff_results.py` — 상호 배제 7분류(`new_fail`/`persistent_fail`/`recovered`/`still_pass`/`not_run`/`new_tc`/`removed_tc`) + flaky 직교 플래그(실측값 전환 2회 이상) + pass rate 추이. 공통 영역 가설만 LLM (추정 명시)
- **출력**: 분류별 md 리포트 + (원하면) 요약 xlsx. ID 재사용 의심·TC_ID 없는 행은 경고로
- **연계**: `new_fail` → `qa-bug-report`, 릴리즈 판단 → `qa-release-checklist`
- **트리거**: "결과 비교", "지난 회차랑 비교", "뭐가 새로 깨졌어", "flaky 찾아"

#### `qa-escaped-defect` — 유출 결함 역추적 → TC 갭 분석
QA를 통과해 프로덕션으로 나간 버그가 "어느 단계에서 새어나갔는지"를 판정하고 보강 TC 후보를 만든다. **blameless** — 책임 추궁이 아니라 갭 분석.
- **입력**: 버그 증상·환경·영역 (필수, 부족하면 추정 없이 질문) + 당시 실행 TC xlsx + 탭 (필수), Jira 키·PRD (옵션)
- **처리**: 관련 TC 추적 후 갭 유형 판정 — A.미작성 / B.미실행 / C.실행했으나 못 잡음(빠진 조건 명시) / D.Fail인데 릴리즈(프로세스 갭)
- **출력**: 갭 분석 md + 보강 TC 후보 표 (핸드오프 규약 — `qa-generate-tc`에 바로 입력 가능)
- **트리거**: "이 버그 왜 못 잡았지", "유출 버그 분석", "TC 갭 분석"

#### `qa-master-health` — 마스터 워크북 전체 헬스체크
수십 개 탭이 쌓인 마스터 전체를 가로로 스캔해 "어느 탭부터 정리할지"를 등급으로 판정한다. `qa-review-tc`가 탭 하나를 깊게 본다면 이건 전 탭을 얕게 훑는 가로 스캔이다.
- **입력**: 마스터 xlsx 한 개 (탭 지정 없이 전체), `--exclude` 제외 탭 (옵션)
- **처리**: `master_health.py` — TC 탭 자동 선별(Priority+TC_ID 헤더, Summary·비-TC 제외) 후 탭마다 `validate_format`·`find_duplicates`·`parse_results` 재사용. 등급 `empty`/`clean`/`minor`(위반율 ≤ 0.1)/`attention`. 노후 의심·탭 간 일관성만 LLM(추정 명시)
- **출력**: 탭별 헬스 대시보드 md + 정리 우선순위(attention 위반율 내림차순) + 비-TC 탭 목록
- **연계**: attention 탭 → `qa-review-tc`로 정밀 검수
- **트리거**: "마스터 건강 체크", "전체 탭 점검", "어느 탭부터 정리"

---

## 공통 개념

여러 스킬이 공유하는 규약. 처음 보면 여기서 시작하면 빠르다.

- **표준 14컬럼 TC 포맷**: `Priority / OS / Automation Check / Test Item / Automation TC_ID / TC_ID / Test Summary / Remote Config·Admin / Pre-condition / Test Step / Expected Result / Result / Jira no. / Comment`. 매치류 탭은 `A`·`B` 컬럼이 추가되고 `Test Step`이 `Test Reproduce`가 되는 **mutual 템플릿** (마스터 탭에 `A`/`B` 컬럼 존재 시 자동 감지). 상세: `shared-reference/template-spec.md`.
- **Result enum (팀 고정)**: `Pass / Fail / Block / N/T / N/A` (대소문자 무시·trim 매칭, 빈 셀 = 미입력). 이외 값은 `unknown`으로 집계되어 리포트에 경고. 이 컬럼은 실행 결과를 다루는 `qa-test-result-report`·`qa-result-diff`만 검사한다 (작성 시점엔 비어 있는 게 정상이므로 `qa-review-tc`는 미검사).
- **Notion 수집 정책**: PRD fetch 시 본문 내 내부 링크를 **1-depth follow**하고 인라인 DB도 포함한다. 분석 리포트 머리에 **소스 매니페스트**(포함/제외 소스) 필수. 첨부 PDF·임베드 이미지는 fetch가 못 읽으므로 로컬 파일/스크린샷을 요청하며, 사용자가 준 스크린샷(PRD 캡처·Figma 화면)은 직접 분석한다. 상세: `shared-reference/notion-fetch-policy.md`.
- **PRD 스냅샷 규약**: PRD를 fetch한 스킬(`prd-clarify`·`generate-tc`·`prd-diff`)은 본문을 `./prd-snapshots/<슬러그>-<YYYYMMDD>.md`로 저장한다. Notion이 버전 히스토리 MCP를 안 주므로, 이 스냅샷이 `qa-prd-diff`의 "과거 버전" 대체물이다. **fetch 원문을 verbatim 보존** (LLM 재서술 금지 — diff 노이즈 방지), 메타헤더에 URL·날짜·소스 기록. 슬러그·충돌 규칙 상세: `shared-reference/snapshot-convention.md`.
- **모호점 핸드오프 규약**: clarify 리포트·prd-diff Open Questions를 `generate-tc`에 넘기면 — Blocker는 Expected Result에 고정 문자열 `TBD (PM 확인 필요)` + Comment 첫 줄 `(Blocker) <질문 요약>`, Major는 가정을 Expected Result에 쓰고 Comment에 `가정: …`. 임의 동작을 지어내지 않는다.
- **원본 불변 (immutability)**: xlsx를 쓰는 스킬은 원본 마스터를 절대 수정하지 않고 항상 새 파일로 출력한다 (collision 시 `(2)`·`(3)` 접미사). `Result`·`Jira no.`·`Automation Check`·`Automation TC_ID` 같은 사람-소관 컬럼은 스킬이 채우지 않고 안내만 한다.
- **컨펌 게이트**: 되돌리기 어렵거나 외부로 나가는 행위(`generate-tc`의 xlsx 생성, `bug-report`의 Jira 이슈 생성)는 미리보기 후 명시적 동의를 받고서야 실행한다.
- **결정론 / LLM 분리**: 파싱·검증·집계·스코어링은 `shared/`의 Python 스크립트(테스트로 보장)가, 등급·커버리지·톤 판단은 LLM이 맡는다.

---

## 아키텍처

```
qa-skills/
├── skills/<name>/          # 배포 단위 — 각 스킬은 자기완결적 번들
│   ├── SKILL.md            #   트리거·워크플로우 (Claude가 읽는 본체)
│   ├── reference/          #   체크리스트·룰·용어집 (shared-reference에서 동기화, 스킬에 따라 없기도)
│   ├── scripts/            #   결정론 스크립트 (shared에서 동기화, LLM-only 스킬엔 없음)
│   └── examples/           #   출력 예시
├── shared/                 # 결정론 스크립트의 단일 진실원천 (SoT)
├── shared-reference/       # 참조 문서의 단일 진실원천
├── scripts/sync_shared.py  # shared → 각 스킬 번들로 복사 동기화
├── tests/                  # 단위 테스트 186개 — shared/ + sync 정책 + 스킬 메타
└── docs/plans/             # 설계·구현 플랜 기록
```

**왜 복사인가**: 각 스킬 번들은 zip 하나로 어디든 배포돼야 하므로 자기완결적이어야 한다. 그래서 `shared/`·`shared-reference/`를 **단일 진실원천**으로 두고, `scripts/sync_shared.py`가 각 번들로 **복사**한다 (심볼릭 링크 아님). 동기화는 번들에 **이미 존재하는** 동일 이름 파일만 덮어쓴다 — 무관한 스킬에 파일이 새어 들어가지 않는다. 새 공유 파일을 어떤 번들에 넣으려면 그 번들에 빈 placeholder를 먼저 만든다.

```bash
uv run python scripts/sync_shared.py            # shared → 번들 동기화 적용
uv run python scripts/sync_shared.py --check    # 드리프트만 보고 (있으면 exit 1) — 커밋 전 검사용
```

---

## 설치

```bash
uv sync
```

의존성: `openpyxl`(xlsx 쓰기), `python-calamine`(빠른 xlsx 읽기). 개발용: `pytest`, `pytest-cov`. (`pyproject.toml`)

## 테스트

```bash
uv run pytest          # 186개 — shared/ 스크립트 전부 + sync_shared 정책 + 스킬 번들 메타(frontmatter·참조 실존·README 목록 일치)
```

---

## 사용

### Claude Code에서

프로젝트 루트의 `.claude/skills/`가 `skills/`를 가리키는 심볼릭 링크라 Claude Code가 자동으로 스킬을 인식한다. 클론 후 `uv sync`만 하면 트리거 문구로 바로 호출된다.

### Claude Desktop / 다른 환경에서

각 스킬 번들은 자기완결적이라 디렉토리째 옮기면 된다.

```bash
# 단일 스킬을 zip으로 패키징 (scripts·reference·examples 모두 포함)
cd skills && zip -r qa-generate-tc.zip qa-generate-tc/

# 또는 사용자 스킬 디렉토리로 복사
cp -r skills/qa-generate-tc ~/.claude/skills/
```

- Anthropic Skills 마켓플레이스에 업로드하거나 `~/.claude/skills/`로 복사한다.
- 모든 CLI 스크립트는 **PEP 723 인라인 메타데이터**를 갖고 있어 `uv run scripts/<name>.py`로 실행하면 uv가 의존성(`openpyxl`·`python-calamine`)을 자동 해결한다 — 어느 cwd에서든 `uv`만 설치돼 있으면 동작. 단 `uv run python scripts/<name>.py` 형식은 인라인 메타데이터를 **무시**하므로 쓰지 않는다.
- Figma·Atlassian(Jira) 연동은 해당 MCP 연결을 전제로 하되, 미연결 시 그 단계만 건너뛰고 나머지는 동작한다. Notion PRD가 필수 입력인 스킬은 Notion MCP 미연결 시 본문 직접 붙여넣기를 요청한다.

---

## 개발 메모

- `shared/`·`shared-reference/`를 고치면 **반드시** `scripts/sync_shared.py`를 돌려 번들에 반영하고, `--check`로 드리프트가 없는지 확인한 뒤 커밋한다.
- 테스트 픽스처 생성기는 `scripts/make_*.py`.
- 설계·라운드별 구현 기록은 `docs/plans/`. (R0~R3 출시 완료. qa-automation-candidates는 R3에서 출시 후 제거됨 — 컬럼은 표준 포맷에 유지)
