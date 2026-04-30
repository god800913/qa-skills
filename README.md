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
- `qa-generate-tc` — TC xlsx 생성 (Phase 2, TBD)
- `qa-review-tc` — TC xlsx 리뷰 (Phase 3, TBD)

## Claude Code에서 사용

프로젝트 루트의 `.claude/skills/`가 `skills/`를 가리키는 심볼릭 링크라 Claude Code는 자동으로 스킬을 인식한다. 다른 환경에서 사용하려면 `skills/qa-prd-clarify/` 디렉토리를 통째로 zip해서 Anthropic Skills 마켓플레이스에 업로드하거나, `~/.claude/skills/`로 복사한다.

## 검증 이력

### Phase 1 검증 (2026-04-30)
- [x] **`qa:prd-clarify` ↔ `tests/fixtures/sample_prd.md`** smoke test PASS — fresh agent가 의도된 4개 모호점(1 Blocker / 2 Major / 1 Minor) 모두 정확히 분류, 추가 Minor 2건은 체크리스트 기반 합리적 발견 (false positive 아님)
- [x] `shared/inspect_master.py` 11개 단위 테스트 전부 통과, 커버리지 83%
- [x] CLI smoke test on 실제 마스터 xlsx (`[ver117] Release QA_Testcase`) — 28개 탭 인식, Lounge 탭 4개 섹션 + last_tc_id 정확히 추출
- [ ] (선택) 실제 Notion PRD URL로 검수 — 환경에 Notion MCP 연결되어 있는 사용자가 직접 수행
