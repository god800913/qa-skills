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
- `qa-prd-clarify` — PRD 모호점 추출 (Phase 1)
- `qa-generate-tc` — TC xlsx 생성 (Phase 2, TBD)
- `qa-review-tc` — TC xlsx 리뷰 (Phase 3, TBD)
