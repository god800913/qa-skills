# QA Skills Expansion Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Add four QA strategy and release-support skills: `qa-risk-analysis`, `qa-regression-scope`, `qa-minimal-coverage`, and `qa-release-checklist`.

**Architecture:** Reuse the existing skill layout under `skills/<skill-name>/` with concise `SKILL.md`, optional `reference/`, optional `examples/`, and deterministic scripts where workbook behavior is required. Reuse shared workbook parsing code from `shared/` for TC extraction and add new shared scripts only where deterministic xlsx output or scoring is needed.

**Tech Stack:** Python, openpyxl, pytest, existing `shared/` utilities, Markdown skill definitions, xlsx fixtures.

---

### Task 1: Add `qa-risk-analysis` Skill Shell

**Files:**
- Create: `skills/qa-risk-analysis/SKILL.md`
- Create: `skills/qa-risk-analysis/reference/risk-taxonomy.md`
- Create: `skills/qa-risk-analysis/examples/sample-risk-report.md`
- Modify: `README.md`

**Step 1: Write the skill definition**

Create `skills/qa-risk-analysis/SKILL.md` with frontmatter:

```yaml
---
name: qa-risk-analysis
description: PRD나 변경 요약을 QA 관점으로 분석해 고위험 영역, 테스트 집중 범위, 릴리즈 리스크를 심각도별 리스크 매트릭스로 정리. TC 작성 전 또는 회귀 범위 결정 전에 사용.
---
```

Include workflow sections for input collection, risk taxonomy application, output format, and non-goals.

**Step 2: Add risk taxonomy reference**

Create `reference/risk-taxonomy.md` with risk categories:

- Core user flow
- Payment or monetization
- Match, chat, call, realtime behavior
- Safety, report, block, moderation
- Auth, permission, privacy
- Remote Config, rollout, experiment
- Cross-platform or OS-specific behavior
- Data migration or backward compatibility

**Step 3: Add a sample report**

Create `examples/sample-risk-report.md` showing Blocker, Major, Minor, and Info risk sections.

**Step 4: Update README**

Add `qa-risk-analysis` to the skill list as planned or beta.

**Step 5: Verify**

Run:

```bash
rg "qa-risk-analysis|risk-taxonomy" skills README.md
```

Expected: new skill files and README entry are found.

**Step 6: Commit**

```bash
git add skills/qa-risk-analysis README.md
git commit -m "feat: add qa risk analysis skill"
```

### Task 2: Add `qa-regression-scope` Skill Shell

**Files:**
- Create: `skills/qa-regression-scope/SKILL.md`
- Create: `skills/qa-regression-scope/reference/scope-rules.md`
- Create: `skills/qa-regression-scope/examples/sample-regression-scope.md`
- Modify: `README.md`

**Step 1: Write the skill definition**

Create `skills/qa-regression-scope/SKILL.md` with frontmatter:

```yaml
---
name: qa-regression-scope
description: PRD, 변경 요약, 기존 TC를 바탕으로 이번 릴리즈에서 필수로 봐야 할 회귀 범위와 생략 가능한 범위를 근거와 함께 정리. 릴리즈 회귀 테스트 계획 수립 시 사용.
---
```

Include workflow sections for change understanding, impacted area mapping, required and optional scope, skipped scope, and rationale.

**Step 2: Add scope rules reference**

Create `reference/scope-rules.md` with rules for forced inclusion, optional inclusion, and safe omission.

**Step 3: Add a sample scope report**

Create `examples/sample-regression-scope.md` with Required, Optional, Skipped, and Open Questions sections.

**Step 4: Update README**

Add `qa-regression-scope` to the skill list.

**Step 5: Verify**

Run:

```bash
rg "qa-regression-scope|scope-rules" skills README.md
```

Expected: new skill files and README entry are found.

**Step 6: Commit**

```bash
git add skills/qa-regression-scope README.md
git commit -m "feat: add qa regression scope skill"
```

### Task 3: Add Minimal Coverage Scoring Tests

**Files:**
- Create: `tests/test_select_minimal_coverage.py`
- Create: `shared/select_minimal_coverage.py`

**Step 1: Write the failing tests**

Create tests for these behaviors:

```python
def test_force_includes_p1_and_high_risk_cases():
    ...

def test_prefers_case_with_higher_unique_risk_coverage():
    ...

def test_penalizes_redundant_cases():
    ...

def test_returns_next_best_and_excluded_cases_with_reasons():
    ...
```

Use small in-memory row dictionaries instead of xlsx fixtures for scoring tests.

**Step 2: Run tests to verify failure**

Run:

```bash
uv run pytest tests/test_select_minimal_coverage.py -v
```

Expected: FAIL because `shared.select_minimal_coverage` does not exist yet.

**Step 3: Commit failing tests**

```bash
git add tests/test_select_minimal_coverage.py
git commit -m "test: define minimal coverage scoring behavior"
```

### Task 4: Implement Minimal Coverage Scoring

**Files:**
- Modify: `shared/select_minimal_coverage.py`
- Modify: `tests/test_select_minimal_coverage.py`

**Step 1: Add typed row model and scoring result**

Implement small dataclasses or typed dictionaries for:

- `TcCandidate`
- `SelectionResult`
- `SelectionReason`

**Step 2: Implement force include logic**

Force include rows with P1 priority or explicit high-risk tags.

**Step 3: Implement greedy risk coverage selection**

Select cases by:

```text
score = risk_score + coverage_gain - execution_cost - redundancy_penalty
```

Stop when all known high and medium risks are covered, or when an optional limit is reached.

**Step 4: Implement excluded and next-best outputs**

Every unselected case must have an exclusion reason. Keep ranked next-best candidates separately.

**Step 5: Verify**

Run:

```bash
uv run pytest tests/test_select_minimal_coverage.py -v
```

Expected: all tests pass.

**Step 6: Commit**

```bash
git add shared/select_minimal_coverage.py tests/test_select_minimal_coverage.py
git commit -m "feat: implement minimal coverage scoring"
```

### Task 5: Add Minimal Coverage Workbook Export

**Files:**
- Create: `tests/test_export_minimal_coverage.py`
- Create: `shared/export_minimal_coverage.py`
- Create: `skills/qa-minimal-coverage/scripts/select_minimal_coverage.py`
- Create: `skills/qa-minimal-coverage/SKILL.md`
- Create: `skills/qa-minimal-coverage/reference/scoring-rules.md`
- Create: `skills/qa-minimal-coverage/examples/sample-selection-summary.md`
- Modify: `README.md`

**Step 1: Write failing workbook export test**

Test that an output workbook contains:

- `Selected TC`
- `Coverage Summary`
- `Excluded TC`
- `Next Best`
- `Assumptions`

Also assert that original TC_ID values are preserved and the source workbook is not modified.

**Step 2: Run test to verify failure**

Run:

```bash
uv run pytest tests/test_export_minimal_coverage.py -v
```

Expected: FAIL because exporter does not exist.

**Step 3: Implement workbook exporter**

Use openpyxl to write the five sheets. Preserve source TC values as plain values, and add analysis columns after the original 14 columns.

**Step 4: Add CLI wrapper**

Create `skills/qa-minimal-coverage/scripts/select_minimal_coverage.py` that accepts:

```bash
uv run python scripts/select_minimal_coverage.py \
  --source <tc.xlsx> \
  --tab <tab-name> \
  --output <out.xlsx> \
  [--max-cases N] \
  [--constraint "2 hours"]
```

**Step 5: Write the skill definition**

Create `skills/qa-minimal-coverage/SKILL.md` with frontmatter:

```yaml
---
name: qa-minimal-coverage
description: 기존 QA TC xlsx를 분석해 리스크 커버를 최대화하는 최소 실행 TC 세트를 골라 새 xlsx로 저장. 제한된 테스트 시간에 어떤 TC를 실행할지 결정할 때 사용.
---
```

Document that the default optimization objective is risk coverage maximization.

**Step 6: Verify**

Run:

```bash
uv run pytest tests/test_select_minimal_coverage.py tests/test_export_minimal_coverage.py -v
uv run python skills/qa-minimal-coverage/scripts/select_minimal_coverage.py --help
```

Expected: tests pass and CLI help exits 0.

**Step 7: Commit**

```bash
git add shared/export_minimal_coverage.py shared/select_minimal_coverage.py tests/test_export_minimal_coverage.py skills/qa-minimal-coverage README.md
git commit -m "feat: add minimal coverage workbook skill"
```

### Task 6: Add `qa-release-checklist` Skill Shell

**Files:**
- Create: `skills/qa-release-checklist/SKILL.md`
- Create: `skills/qa-release-checklist/reference/release-gates.md`
- Create: `skills/qa-release-checklist/examples/sample-release-checklist.md`
- Modify: `README.md`

**Step 1: Write the skill definition**

Create `skills/qa-release-checklist/SKILL.md` with frontmatter:

```yaml
---
name: qa-release-checklist
description: PRD, TC 결과, known issue, 리스크 분석을 바탕으로 릴리즈 전 QA sign-off 체크리스트와 blocker 조건을 정리. 릴리즈 승인 전 최종 점검에 사용.
---
```

**Step 2: Add release gate reference**

Create `reference/release-gates.md` with blocker, major, known issue, rollout, rollback, monitoring, and owner confirmation gates.

**Step 3: Add sample checklist**

Create `examples/sample-release-checklist.md` with ready, conditional, and blocked examples.

**Step 4: Update README**

Add `qa-release-checklist` to the skill list.

**Step 5: Verify**

Run:

```bash
rg "qa-release-checklist|release-gates" skills README.md
```

Expected: new skill files and README entry are found.

**Step 6: Commit**

```bash
git add skills/qa-release-checklist README.md
git commit -m "feat: add qa release checklist skill"
```

### Task 7: Run Full Verification

**Files:**
- Verify: all changed files

**Step 1: Run unit tests**

```bash
uv run pytest
```

Expected: all tests pass.

**Step 2: Verify shared script sync if new shared scripts are copied into skills**

```bash
uv run python scripts/sync_shared.py --check
```

Expected: exits 0, or reports no sync requirement for new scripts.

**Step 3: Smoke-test the minimal coverage CLI**

Use an existing fixture workbook:

```bash
uv run python skills/qa-minimal-coverage/scripts/select_minimal_coverage.py \
  --source tests/fixtures/sample_tc_with_issues.xlsx \
  --tab TabA \
  --output /tmp/minimal-coverage-smoke.xlsx
```

Expected: output xlsx exists with five sheets.

**Step 4: Final commit if needed**

```bash
git status --short
```

Expected: clean working tree.
