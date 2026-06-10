# QA Skills 확장 설계 v2 (2026-06-11)

> 2026-06-02 `qa-skills-expansion-design.md`를 대체한다. 스코프를 4개 → 9개 스킬 + 기존 스킬 강화 1건으로 확장하고, 이전 문서의 open decision을 전부 확정했다.

## 목표

PRD → TC 작성 → 실행 → 릴리즈 판정에 이르는 QA 사이클 전체를 스킬로 커버한다. 기존 출시 3종(`qa-prd-clarify`, `qa-generate-tc`, `qa-review-tc`)이 "PRD에서 TC 품질까지"를 담당하고, 이번 확장은 **테스트 전략 · 실행 결과 · 릴리즈 의사결정 · 변경 대응** 레이어를 추가한다.

## 확정된 결정사항

| 항목 | 결정 |
|---|---|
| Result 컬럼 enum | `Pass / Fail / Block / N/T / N/A` 고정. enum 외 값은 `unknown`으로 분류하고 리포트에 경고 |
| `qa-prd-diff` 입력 | 스냅샷 md + 현재 Notion URL 비교. `qa-prd-clarify`·`qa-generate-tc` 실행 시 PRD를 md 스냅샷으로 저장하는 규약 신설 (기본 `./prd-snapshots/<기능>-<YYYYMMDD>.md`, 사용자 지정 가능) |
| `qa-risk-analysis`·`qa-regression-scope` 출력 | md 리포트 + 요약 xlsx (공용 exporter 사용) |
| `qa-minimal-coverage` 서식 | 원본 셀 값만 보존(plain value), 원본 TC_ID 유지 + 별도 실행 순서 컬럼 추가 |
| Figma 접근 | Figma MCP (공식 Dev Mode MCP 또는 framelink 계열). 미연결 시 연결 안내를 SKILL.md에 포함 |
| 진행 방식 | Round 0 → 1 → 2 → 3 순차 출시. 라운드마다 smoke 검증 + README 갱신 + 커밋으로 완결 |

## Round 0 — `qa-generate-tc` v2: Notion PRD + Figma

기존 출시 스킬의 입력 확장. 새 스킬 의존성이 없어 단독 출시 가능하므로 최우선 작업.

- **입력**: Notion PRD URL (기존) + Figma 파일/프레임 URL (신규, 옵션)
- **동작**: Figma MCP로 프레임 구조·텍스트·UI 상태를 읽어 Test Step과 Expected Result를 화면 기준으로 구체화한다. 디자인에만 있고 PRD에 없는 상태(빈 상태, 에러, 로딩 등)는 Comment에 "PRD 미정의, 디자인 기준" 으로 기록한다.
- **Figma MCP 미연결 시**: TC 생성을 막지 않는다. PRD 단독 모드로 진행하되 "Figma 연결 시 UI 상태 커버리지가 좋아진다"는 안내를 출력한다.
- **변경 파일**: `skills/qa-generate-tc/SKILL.md` 워크플로우 확장, `reference/figma-usage.md` 신규. 결정론 스크립트 변경 없음.

## Round 1 — 전략 코어 4종 (2026-06-02 설계 순서 유지)

### 1. `qa-risk-analysis`

- **입력**: PRD 또는 변경 요약, 옵션 도메인 노트
- **출력**: 리스크 매트릭스 md (Blocker/Major/Minor/Info 섹션) + 요약 xlsx (영역, 영향도, 발생가능성, 등급, 권장 테스트 포커스)
- **참조**: `shared-reference/risk-taxonomy.md` (신규, 아래 공용 인프라 참조)
- LLM 중심. xlsx 출력만 공용 exporter 사용.

### 2. `qa-regression-scope`

- **입력**: PRD/변경 요약 + 기존 TC xlsx (`extract_tc_table` 재사용), 옵션 이전 릴리즈 노트
- **출력**: 회귀 범위 md (Required/Optional/Skipped/Open Questions) + 요약 xlsx (탭·섹션 단위 포함 여부와 근거)
- 생략(Skipped) 범위는 반드시 근거와 잔여 리스크를 기록한다.

### 3. `qa-minimal-coverage`

2026-06-02 설계를 그대로 계승한다. 핵심만 요약:

- **입력**: TC xlsx + 탭 + 옵션 제약(`--max-cases`, 시간 제약)
- **출력**: 5시트 xlsx — `Selected TC` / `Coverage Summary` / `Excluded TC` / `Next Best` / `Assumptions`
- **스코어링** (결정론, `shared/select_minimal_coverage.py`):
  `score = risk_score + coverage_gain - execution_cost - redundancy_penalty`
  - P1·blocker 리스크·핵심 플로우(결제, 신고, 매치, 실시간 콜, 권한, Remote Config)는 강제 포함
  - 모든 미선택 TC는 제외 사유 + 잔여 리스크 기록
- **내보내기** (결정론, `shared/export_minimal_coverage.py`): 원본 14컬럼 값 보존 + 분석 컬럼(선택 사유, 커버 리스크, 점수) 추가
- LLM은 태깅·사유 문장에만 관여. 추출·스코어링·생성은 스크립트.

### 4. `qa-release-checklist`

- **입력**: PRD/릴리즈 요약, TC 결과 요약(Round 2의 `qa-test-result-report` 출력과 연결), known issues, 옵션 리스크 리포트
- **출력**: sign-off 체크리스트 md — ready / conditional / blocked 판정 + blocker 조건 + rollout·rollback·모니터링 항목
- **참조**: `reference/release-gates.md` (blocker, major, known issue, rollout, rollback, monitoring, owner 확인 게이트)

## Round 2 — 변경·결과 처리 2종

### 5. `qa-prd-diff`

- **입력**: 과거 PRD 스냅샷 md + 현재 Notion URL
- **출력**: 변경점 md — 변경 요약(추가/수정/삭제) + 기존 TC 영향 분류(수정 필요 / 신규 필요 / 폐기 후보), TC xlsx가 제공되면 TC_ID 단위로 매핑
- **전제 규약**: `qa-prd-clarify`·`qa-generate-tc` SKILL.md에 "PRD 읽은 직후 스냅샷 저장" 단계 추가 (Round 2에서 함께 수정)
- 텍스트 diff는 보조 신호일 뿐, 의미 비교는 LLM이 수행한다.

### 6. `qa-test-result-report`

- **입력**: 실행 완료된 TC xlsx (Result·Jira no. 컬럼이 채워진 상태)
- **출력**: 실행 결과 md — 탭·섹션·Priority별 통과율, Fail/Block 목록(Jira 링크 포함), 실패 패턴, 잔여 리스크. `qa-release-checklist`의 입력으로 바로 사용 가능한 형식.
- **결정론 스크립트**: `shared/parse_results.py` — Result enum 파싱·집계. enum 외 값은 `unknown` 분류 + 경고 목록 출력.

## Round 3 — 보조 3종 (md 중심)

### 7. `qa-exploratory-charter`

- **입력**: 리스크 리포트(권장) 또는 PRD
- **출력**: 탐색적 테스트 차터 md — 차터별 목표 / 범위 / 비범위 / 타임박스 / 기록 항목. 스크립트 TC가 못 잡는 영역(복합 상태 전이, 비정상 네트워크 등)에 집중.

### 8. `qa-automation-candidates`

- **입력**: TC xlsx (`Automation Check` 컬럼) + 옵션 실행 결과 리포트
- **출력**: 자동화 후보 우선순위 md — 반복 실행 빈도, 수동 실행 비용, 안정성(스크립트화 적합성) 기준. `Automation TC_ID`가 이미 있는 행은 제외.

### 9. `qa-bug-report`

- **입력**: Fail/Block TC 행 + 사용자 보충(재현 빈도, 환경, 로그)
- **출력**: 표준 버그 리포트 md (제목 / 환경 / 재현 단계 / 기대·실제 결과 / 심각도 / 첨부)
- **Jira 연동**: Atlassian MCP(`createJiraIssue`)로 초안 생성 가능. **반드시 리포트 내용을 사용자에게 보여주고 컨펌받은 후 생성한다** (외부 시스템 쓰기 액션).

## 공용 인프라

| 신규 | 용도 | 사용 스킬 |
|---|---|---|
| `shared/summary_xlsx.py` | 시트 스펙 리스트(`[{title, headers, rows}]`) → 요약 워크북 생성 (범용) | risk-analysis, regression-scope |
| `shared/parse_results.py` | Result enum 파싱·탭/섹션/Priority 집계 | test-result-report, automation-candidates |
| `shared/select_minimal_coverage.py` | TC 후보 스코어링·선정 | minimal-coverage |
| `shared/export_minimal_coverage.py` | 5시트 워크북 생성 | minimal-coverage |
| `shared-reference/risk-taxonomy.md` | 리스크 분류 체계 (핵심 플로우, 결제, 매치·콜·실시간, 신고·차단, 인증·권한, Remote Config·실험, 크로스플랫폼, 마이그레이션) | risk-analysis, regression-scope, minimal-coverage, exploratory-charter |
| `shared-reference/format-rules.md` 갱신 | Result enum 5값 추가 | review-tc, test-result-report |
| `tests/fixtures/sample_tc_executed.xlsx` + `scripts/make_executed_fixture.py` | Result 값이 채워진 실행 완료 픽스처 | parse_results 테스트 |

기존 규약 유지: 스킬 구조(`SKILL.md` + `reference/` + `examples/` + `scripts/`), `scripts/sync_shared.py` 동기화, 원본 xlsx 절대 수정 금지.

## 테스트·검증 전략

- **결정론 스크립트** (summary_xlsx, parse_results, select/export_minimal_coverage): pytest TDD (RED → GREEN), 기존 44개 테스트에 누적.
- **md-only 스킬**: fresh-subagent SKILL.md 워크플로우 시뮬레이션 smoke test (기존 Phase 1~3 검증 관행).
- **라운드 완료 기준**: 단위 테스트 전부 통과 + `sync_shared.py --check` 0 exit + smoke PASS + README 검증 이력 갱신.

## Non-goals

- 원본 워크북 in-place 수정 금지 (전 스킬 공통).
- 사용자 컨펌 없는 Jira 이슈 생성 금지.
- Figma 디자인 자체의 QA(픽셀 검증, 디자인-구현 일치 검사)는 비범위. Figma는 TC 작성의 입력일 뿐이다.
- TestRail/Zephyr 등 외부 TC 관리 도구 연동 비범위.
- 실행 시간만을 목표로 한 최적화는 사용자가 명시적으로 요청할 때만.

## 남은 open decision

없음. 2026-06-02 문서의 open decision 3건(서식 보존, TC_ID 유지, 출력 형식)은 위 표에서 확정했다.
