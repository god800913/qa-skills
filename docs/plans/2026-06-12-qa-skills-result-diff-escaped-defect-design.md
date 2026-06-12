# QA Skills 확장 설계 — qa-result-diff · qa-escaped-defect (2026-06-12)

> 11종 체제(automation-candidates 제거 후)의 갭 분석에서 도출된 2종 추가.
> 갭: ④ 실행·릴리즈가 **단일 회차** 전용이라 회차 간 비교가 불가하고,
> 릴리즈 후 **유출 결함을 TC로 되먹이는 개선 루프**가 없다.

## 확정된 결정사항

| 항목 | 결정 |
|---|---|
| result-diff 비교 범위 | **N회차 (N≥2)**. 입력 2개면 직전-이번 쌍 비교와 동일하게 동작 (N=2가 degenerate case). flaky 점수화는 N≥3에서 활성 |
| result-diff 매칭 키 | **TC_ID** (탭 내). TC_ID 없는 행은 제외+경고. 동일 ID인데 Test Summary 불일치 시 "ID 재사용 의심" 경고 |
| escaped-defect 버그 입력 | 텍스트 기본 + Atlassian MCP 연결 시 Jira 이슈 키 fetch (bug-report와 동일 패턴, 미연결 시 텍스트 폴백) |
| README 배치 | 둘 다 ⑤ 유지보수 (11 → 13종). result-diff는 test-result-report의 후속 연계 명시 |
| Result enum·unknown 정책 | parse_results.py와 동일 — 대소문자 무시·trim, enum 외 unknown 경고, 임의 재분류 금지 |
| blameless 원칙 | escaped-defect는 갭 분석이지 책임 추궁이 아님을 SKILL.md에 명시 |

## 1. `qa-result-diff` — 회차 간 실행 결과 비교

- **입력**: 회차 순서대로 `(xlsx 경로, 탭)` 쌍 2개 이상 (같은 파일의 다른 탭 허용), 회차 라벨 (옵션, 기본 파일명)
- **결정론**: `shared/diff_results.py` 신규 (PEP 723, TDD)
  - 회차별 행을 `extract_tc_table`로 평탄화, `parse_results.normalize_result` 재사용
  - TC별 이력 행렬 `[r1…rN]` (각 원소: enum 값 / `"unknown"` / `null`=미입력 / `"-"`=해당 회차 미존재)
  - **"직전 유효 결과"** = 마지막 회차 이전 이력에서 N/T·N/A·미입력·unknown·미존재를 건너뛴 마지막 실측값({Pass, Fail, Block}). 없으면 "없음". (flaky와 동일한 skip 규칙)
  - **분류는 상호 배제 — 아래 우선순위로 정확히 하나 부여** (마지막 회차 기준, 전체 케이스를 빠짐없이 커버):
    1. `removed_tc` — 마지막 회차에 없음 (이전 회차엔 있었음)
    2. `new_tc` — **이전 모든 회차에 미존재**, 마지막 회차에 처음 등장 (Fail이어도 new_tc — 이력 행렬과 리포트에서 "신규 중 Fail"로 표시)
    3. `not_run` — 이번 회차 N/T·N/A·미입력·unknown
    4. `persistent_fail` — 직전 유효 결과 {Fail, Block} → 이번 Fail/Block (예: `[Fail, N/T, Fail]`)
    5. `new_fail` — 직전 유효 결과 Pass 또는 없음 → 이번 Fail/Block (예: `[Pass, N/T, Fail]`, `[-, Pass, Fail]`)
    6. `recovered` — 직전 유효 결과 {Fail, Block} → 이번 Pass (예: `[Fail, N/T, Pass]`)
    7. `still_pass` — 직전 유효 결과 Pass 또는 없음 → 이번 Pass
    (이번 회차 실측값은 Pass 아니면 Fail/Block 둘뿐이므로 4~7이 나머지 전부를 분할 — 모든 이력이 정확히 한 분류에 떨어진다. 테스트에서 totality 검증)
  - **`flaky`는 분류가 아니라 직교 boolean 플래그**: 이력에서 N/T·N/A·미입력·unknown·미존재를 제거한 뒤 {Pass} ↔ {Fail, Block} 인접 전환 횟수 ≥ 2.
    예: `[P,F,P]`=전환2→flaky / `[P,F,F,P]`=전환2→flaky / `[P,F]`=전환1→아님 / `[P,N/T,F]`=전환1→아님 (N/T 건너뜀)
  - **경고는 JSON `warnings` 필드에 구조화**: TC_ID 없는 행 제외 건수, ID 재사용 의심(`{tc_id, first_summary, last_summary}` — Test Summary trim 후 정확 일치 기준, 회차 간 동일 TC_ID 비교이므로 탭 이름 차이는 무관)
  - 회차별 pass rate 추이 — `pass_rate = Pass / (Pass + Fail + Block)`, N/T·N/A·미입력·unknown 분모 제외 (parse_results 공식 동일)
  - CLI: `uv run scripts/diff_results.py <xlsx1> <tab1> <xlsx2> <tab2> [...] [--labels a,b,...]` → JSON stdout. 탭을 모르면 SKILL.md 플로우에서 `inspect_master.py`로 탭 목록을 먼저 제시
- **LLM**: 분류 해석 — 스크립트 JSON(섹션·Test Summary 포함)을 받아 `new_fail`·`flaky` 묶음을 섹션·키워드로 그룹핑해 공통 영역 가설 제시, 잔여 리스크, 다음 액션 (`new_fail` → `qa-bug-report`, 릴리즈 판단 → `qa-release-checklist`). 그룹핑 가설은 추정임을 명시
- **출력**: md 리포트 + (원하면) 요약 xlsx (`summary_xlsx.py` 재사용 — 분류별 목록 + pass rate 추이 시트)
- **번들**: scripts = diff_results, extract_tc_table, parse_results, inspect_master(탭 목록), summary_xlsx / reference = format-rules.md / examples = sample-result-diff.md
- **비목표**: 결과 입력 대행, flaky 코드 레벨 원인 분석, Jira 자동 갱신

## 2. `qa-escaped-defect` — 유출 결함 역추적 → TC 갭 분석

- **입력**:
  - 필수 (없으면 추정 없이 질문): 버그 증상·실제 동작, 발생 환경(기기·OS·앱 버전 대략), 영역 또는 재현 단계 중 하나, 당시 실행 TC xlsx + 탭
  - 옵션: Jira 이슈 키 (MCP 연결 시 fetch), PRD/스냅샷 (스펙 대조 정확도 상승)
- **워크플로우** (LLM 중심):
  1. 버그 정보 수집 — 필수 항목 체크, 부족하면 추정 없이 질문
  2. `extract_tc_table`로 탭 평탄화 → 버그 영역·키워드 관련 TC 추적
  3. 갭 유형 판정 (4분류):
     - **A. 미작성** — 커버 TC 없음
     - **B. 미실행** — TC 존재, Result N/T·미입력
     - **C. 실행했으나 못 잡음** — Pass였지만 스텝·조건이 버그 시나리오 미커버 (빠진 조건 명시)
     - **D. Fail이었는데 릴리즈** — 프로세스 갭 → release-checklist 게이트 점검 권고
  4. 보강 TC 후보 표 — 모호점 핸드오프 규약 그대로 (`TBD (PM 확인 필요)` + `(Blocker)` Comment) → `qa-generate-tc` 입력 호환
  5. blameless — SKILL.md에 독립 원칙 섹션으로: "누가 실수했나"가 아니라 "어느 단계에서 신호를 놓쳤나"를 찾는 도구. 갭 A~D는 전부 개선 기회이며 개인 귀속 표현(담당자·이름) 사용 금지
- **출력**: 갭 분석 md — 버그 요약 / 관련 TC 추적 표 / 갭 유형+근거 / 보강 TC 후보 / 프로세스 제안
- **번들**: scripts = extract_tc_table, inspect_master / reference = risk-taxonomy.md(영역·심각도 판단) / examples = sample-escaped-defect.md
- **비목표**: 버그 원인 코드 분석, TC 자동 추가 (후보 제안만), 책임 귀속

## 공용 인프라 변경

- `shared/diff_results.py` 신규 — 유일한 신규 결정론 스크립트. 단위 테스트 필수 커버: 분류 7종 각각 + 우선순위 배제 케이스(신규인데 Fail 등), flaky 전환 카운트 엣지(`[P,F,P]`·`[P,F,F,P]`·`[P,N/T,F]`·2회차), 경고 2종, pass rate 추이, CLI 파싱(홀수 인자 거부)
- 기존 스크립트 변경 없음 (재사용만). 동기화 대상 placeholder: qa-result-diff = extract_tc_table·parse_results·inspect_master·summary_xlsx·format-rules.md / qa-escaped-defect = extract_tc_table·inspect_master·risk-taxonomy.md
- README: 다이어그램·목록·개수(13종)·테스트 개수 갱신
- 번들 placeholder → `sync_shared.py`로 공유본 주입, 메타 테스트가 frontmatter·참조 실존·README 일치 자동 검증

## 진행 순서

1. `diff_results.py` TDD (RED → GREEN) + 번들 2종 생성
2. SKILL.md·examples 작성, sync, README 갱신
3. 전체 테스트 + `--check` + `~/.claude/skills` 설치 + 커밋·푸시
