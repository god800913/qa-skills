# qa-skills

Hyperconnect Azar QA 팀용 Claude Skills (PoC).

상세 디자인: [`docs/superpowers/specs/2026-04-30-qa-skills-design.md`](docs/superpowers/specs/2026-04-30-qa-skills-design.md)

## 설치

```bash
uv sync
```

## 테스트

```bash
uv run pytest
```

## 스킬 목록
- `qa-prd-clarify` — PRD 모호점 추출 (Phase 1, 출시 ✅)
- `qa-generate-tc` — Notion PRD(+옵션 Figma)로 TC xlsx 생성 (Phase 2 + R0 강화, 출시 ✅)
- `qa-review-tc` — TC xlsx 리뷰 (Phase 3, 출시 ✅)
- `qa-risk-analysis` — 리스크 매트릭스 md+xlsx (Round 1, 출시 ✅)
- `qa-regression-scope` — 회귀 범위 결정 md+xlsx (Round 1, 출시 ✅)
- `qa-minimal-coverage` — 최소 실행 TC 세트 5시트 xlsx (Round 1, 출시 ✅)
- `qa-release-checklist` — 릴리즈 sign-off 체크리스트 (Round 1, 출시 ✅)

## Claude Code에서 사용

프로젝트 루트의 `.claude/skills/`가 `skills/`를 가리키는 심볼릭 링크라 Claude Code는 자동으로 스킬을 인식한다. 다른 환경에서 사용하려면 `skills/qa-prd-clarify/` 디렉토리를 통째로 zip해서 Anthropic Skills 마켓플레이스에 업로드하거나, `~/.claude/skills/`로 복사한다.

## 검증 이력

### Phase 1 검증 (2026-04-30)
- [x] **`qa:prd-clarify` ↔ `tests/fixtures/sample_prd.md`** smoke test PASS — fresh agent가 의도된 4개 모호점(1 Blocker / 2 Major / 1 Minor) 모두 정확히 분류, 추가 Minor 2건은 체크리스트 기반 합리적 발견 (false positive 아님)
- [x] `shared/inspect_master.py` 11개 단위 테스트 전부 통과, 커버리지 83%
- [x] CLI smoke test on 실제 마스터 xlsx (`[ver117] Release QA_Testcase`) — 28개 탭 인식, Lounge 탭 4개 섹션 + last_tc_id 정확히 추출
- [ ] (선택) 실제 Notion PRD URL로 검수 — 환경에 Notion MCP 연결되어 있는 사용자가 직접 수행

### Phase 2 검증 (2026-04-30)
- [x] **단위 테스트 30개** 전부 통과 (Phase 1 13개 + tc_row 4 + new_workbook 4 + append_to_master 5 + _find_section 4)
- [x] **`qa:generate-tc` 신규 시트 모드 smoke** — sample_rows.json 입력으로 14컬럼 헤더 + 섹션 행 + TC 행 (TC_ID 자동 부여) 정상 생성
- [x] **`qa:generate-tc` append 모드 smoke** — 마스터 복사본에 새 행 append, **원본 md5 불변 확인**, 두 탭 모두 보존, 새 섹션 인덱스(`3-1`) 자동 부여
- [x] **Fresh subagent SKILL.md workflow simulation** PASS — sample_prd.md → 8개 TC (P1:2/P2:2/P3:2/P4:2), Remote Config ON/OFF 양분기, PRD 모호점 Comment 명시, 한국어 톤 일관, 할루시네이션 없음
- [x] `shared/` ↔ `skills/qa-generate-tc/scripts·reference/` 자동 동기화 (`scripts/sync_shared.py`)

### Phase 3 검증 (2026-04-30)
- [x] **단위 테스트 14개 추가** 전부 통과 (validate_format 6 + find_duplicates 5 + extract_tc_table 3) — 누적 **44개 PASS**
- [x] **`qa:review-tc` 결정론 스크립트 smoke** — `sample_tc_with_issues.xlsx`에서 missing_required (Priority/Expected Result), invalid_enum (OS=MacOS), duplicate_tc_id (1-2), intra-tab Test Summary dup (메인 진입), cross-tab dup (TabA 1-6 ↔ TabB 1-3 차단 사용자 제외) 전건 검출
- [x] `shared/` ↔ `skills/qa-review-tc/` 자동 동기화 (`scripts/sync_shared.py --check` 0 exit)

### Round 0 검증 (2026-06-11)
- [x] **`qa:generate-tc` v2 fresh subagent smoke PASS** — sample_prd.md → 9 TC (P1:2/P2:3/P3:2/P4:2), Remote Config ON/OFF 양분기, 모호점 Comment 명시 유지
- [x] PRD 스냅샷 단계 — `prd-snapshots/라운지-신규-추천-알고리즘-20260611.md` 명명 규칙(제목 추출·하이픈·date 명령) 준수 확인
- [x] Figma MCP 미연결 graceful fallback — 진행 차단 없이 한 줄 안내 후 PRD 단독 모드, 디자인 확인 필요 항목은 TC Comment에 기록

### Round 1 검증 (2026-06-11)
- [x] **단위 테스트 14개 추가** 전부 통과 (summary_xlsx 4 + select_minimal_coverage 7 + export_minimal_coverage 3) — 누적 **60개 PASS**
- [x] `scripts/sync_shared.py --check` exit 0 — 신규 번들 3종(risk-analysis, regression-scope, minimal-coverage)의 placeholder 동기화 무결
- [x] **`qa:minimal-coverage` CLI smoke** — sample_tc_with_issues.xlsx TabA에서 `--max-cases 3` 실행, 원본 md5 불변, 5시트(Selected/Coverage/Excluded/Next Best/Assumptions) 생성, forced-overflow는 Excluded `강제 대상` 컬럼으로 표면화
- [x] **`qa:risk-analysis` fresh subagent smoke PASS** — sample_prd.md → Blocker 1(차단 사용자 추천 노출)/Major 4/Minor 2 매트릭스, 가정 5건 PM 확인 필요 분리, taxonomy 등급 정의 일관
- [x] **`qa:regression-scope` fresh subagent smoke PASS** — 번들 스크립트(inspect/extract) 직접 호출로 탭 인벤토리, Required 5/Optional 4/Skipped 2(잔여 리스크 명시)/OQ 5, 픽스처의 의도된 TC 품질 이슈(TC_ID 중복·Expected Result 공란)까지 검출
- [x] **`qa:release-checklist` fresh subagent smoke PASS** — 정보 없는 게이트 4개를 추정 없이 "확인 불가" 처리, 미검증 차단 영역(Block 1건)을 G1 실패로 판정해 BLOCKED 출력
