# QA Skills Expansion Design

## Goal

Extend the current QA skill set beyond PRD clarification, TC generation, and TC review so QA engineers can decide what to test, how much to test, and whether a release is ready.

## Current Baseline

The repository already provides three released skills:

- `qa-prd-clarify`: finds PRD ambiguity before TC writing.
- `qa-generate-tc`: generates standard 14-column QA TC workbooks.
- `qa-review-tc`: reviews TC workbooks for format, duplication, coverage, and tone issues.

These cover the core production flow from PRD to TC quality review. The missing layer is test strategy and release decision support.

## Expansion Tracks

### Pre-release QA Strategy

1. `qa-risk-analysis`
   - Purpose: identify high-risk behavior from PRD or change summaries before detailed test selection.
   - Inputs: PRD, change summary, optional domain notes.
   - Outputs: risk matrix, high-risk areas, recommended test focus, assumptions.

2. `qa-regression-scope`
   - Purpose: decide which existing areas should be included in regression for the current change.
   - Inputs: PRD or change summary, existing TC workbook, optional previous release notes.
   - Outputs: required regression scope, optional scope, skipped scope, rationale.

3. `qa-minimal-coverage`
   - Purpose: select the smallest practical TC set that maximizes risk coverage.
   - Inputs: existing TC workbook, PRD or change summary, optional time or staffing constraint.
   - Outputs: a new xlsx workbook containing selected TC, coverage summary, excluded TC, next-best candidates, and assumptions.

### Release and Operations QA

4. `qa-release-checklist`
   - Purpose: convert QA evidence into a release sign-off checklist.
   - Inputs: PRD or release summary, TC result summary, known issues, optional risk report.
   - Outputs: release readiness checklist, blocker conditions, known issue notes, rollout and rollback checks.

## Recommended Delivery Order

1. `qa-risk-analysis`
2. `qa-regression-scope`
3. `qa-minimal-coverage`
4. `qa-release-checklist`

This order mirrors the QA decision flow: identify risk, choose regression scope, optimize the executable TC set, then prepare release sign-off.

## `qa-minimal-coverage` Design

`qa-minimal-coverage` should be a first-class xlsx-producing skill, not a markdown-only report.

### Optimization Policy

Default objective: maximize risk coverage.

Selection priority:

1. Force include P1, blocker-risk, core user flows, and high-risk domains such as payment, report, match, realtime call, permission, and Remote Config behavior.
2. Prefer TC that cover multiple risk tags, platforms, branches, or user states.
3. Penalize duplicate steps, duplicate expected results, low-risk copy checks, and TC fully covered by higher-value TC.
4. Exclude lower-value TC only with a recorded reason and residual risk.

### Workbook Output

The generated workbook should include these sheets:

- `Selected TC`: final execution set, preserving the source TC columns and adding selection reason, covered risks, coverage gain, execution cost, and score.
- `Coverage Summary`: risk, feature, platform, Remote Config, and priority coverage.
- `Excluded TC`: skipped TC with exclusion reason and residual risk.
- `Next Best`: additional TC ranked by marginal value if more time is available.
- `Assumptions`: selection rules, input constraints, forced-include conditions, and known gaps.

### Scoring Model

The first implementation should keep scoring transparent and deterministic enough for QA review:

- Risk score: impact and likelihood inferred from priority, domain keywords, PRD risk, and change area.
- Coverage gain: new unique risk or feature tags covered by the TC.
- Execution cost: estimated from TC type, required environment, setup burden, and manual complexity.
- Redundancy penalty: overlap with already selected TC.

Final score:

```text
score = risk_score + coverage_gain - execution_cost - redundancy_penalty
```

The skill may use LLM judgment for tagging and rationale, but workbook extraction, workbook creation, and row copying should use deterministic scripts.

## Non-goals

- Do not modify source workbooks in place.
- Do not hide excluded TC.
- Do not optimize only for execution time unless the user explicitly asks.
- Do not replace `qa-review-tc`; this skill chooses a subset after TC quality is acceptable.
- Do not require Jira, production dashboard, or internal monitoring integrations in the first release.

## Open Decisions for Implementation

- Whether `qa-minimal-coverage` should copy original row formatting or only preserve values.
- Whether selected TC should keep original TC_ID values or get a separate execution order column only.
- Whether `qa-risk-analysis` and `qa-regression-scope` should produce markdown only in phase 1, or also write summary workbooks.
