# QA Skills 확장 설계 — qa-master-health (2026-06-16)

> 13종 체제의 갭: `qa-review-tc`는 **탭 하나**를 깊게 검수하지만, 수십 개 탭이 쌓인
> 마스터 워크북 **전체의 건강 상태**를 한눈에 볼 도구가 없다. 정기 점검·인수인계·
> 대청소 시점에 "어느 탭부터 정리해야 하나"를 판정하는 가로 스캔이 master-health.

## 확정된 결정사항

| 항목 | 결정 |
|---|---|
| 탭 선별 | **TC 탭만 자동 선별**. `parse_tab_meta`가 Priority 헤더를 찾고 + `TC_ID` 컬럼이 있으면 TC 탭. 못 찾으면(ValueError) 또는 TC_ID 컬럼 없으면 "비-TC 탭"으로 분류해 스캔 제외(목록엔 표시). Summary 탭(`is_summary`)도 제외 |
| 노후 판정 | **LLM 정성 판단만**. 마스터엔 수정일·작성일 메타가 없으므로 "노후"는 낡은 용어·톤·구조 불일치 같은 신호로 LLM이 의심만 제기. 결정론 점수는 객관 지표만 |
| cross-tab 중복 | master-health는 **intra-tab(탭 내 중복)만** 집계. 전 탭 쌍 cross 검사는 무겁고 노이즈 큼 — 의심 탭은 `qa-review-tc`로 깊게 보라고 안내 |
| 미실행 비율 | 정보로 노출하되 건강 점수 페널티에선 제외. 작성 시점엔 Result 비어있는 게 정상이므로(format-rules 규약), 미실행은 맥락 의존 정보 |
| 출력 | 탭별 헬스 대시보드 md + (원하면) 요약 xlsx (`summary_xlsx.py` 재사용) |
| README 배치 | ⑤ 유지보수 (13 → 14종) |

## 결정론 스크립트 `shared/master_health.py` (신규, PEP 723, TDD)

기존 스크립트를 전 탭에 루프 돌리는 집계기. **신규 검증 로직 없음 — 재사용만.**

- `inspect_master.list_tabs(xlsx)` → 전 탭 목록 (`{name, is_summary, column_count}`)
- 각 탭 분류 (순서대로 평가, 처음 맞는 사유로 확정):
  - `is_summary == True` → 제외 (사유: "Summary 탭")
  - `parse_tab_meta` 호출이 ValueError(Priority 헤더 없음) → 제외 (사유: "Priority 헤더 없음")
  - 성공했으나 `"TC_ID" not in columns` → 제외 (사유: "TC_ID 컬럼 없음")
  - 성공 + `TC_ID` 컬럼 존재 → **TC 탭** (single/mutual은 `template_type`으로 판별. mutual은 inspect_master가 `Test Reproduce`→`Test Step`으로 canonical화하므로 validate_format/find_duplicates가 그대로 처리)
- TC 탭마다 (재사용 — 실제 시그니처 기준):
  - `validate_format(xlsx, tab)` → `["summary"]["issue_count"]` = `format_violations`. `["issues"]`를 category별(missing_required/invalid_enum/duplicate_tc_id)로 카운트
  - `find_duplicates._load_tc_rows(xlsx, tab)` → `(rows, columns)` — rows는 `list[tuple[int, dict]]`
  - `find_duplicates._find_intra_tab(rows)` → 중복 리스트, `len()` = `intra_dup_count`
  - `extract_tc_table(xlsx, tab)` → `list[dict]` → `parse_results(...)` → `total`(=tc_count), `counts["미입력"]`
  - `blank_ratio = counts["미입력"] / tc_count` (tc_count>0일 때만; master_health가 직접 계산 — parse_results는 비율을 반환하지 않음)
- **탭 건강 점수 (결정론) — empty 먼저 평가**:
  - `tc_count == 0` → `empty` (defect_rate 계산 생략)
  - 그 외:
    - `defects = format_violations + intra_dup_count`
    - `defects == 0` → `clean`
    - `defects / tc_count ≤ 0.1` → `minor`
    - 그 외 → `attention`
- **마스터 요약**: 총 탭 수, TC 탭 수, 비-TC 탭 수, 전체 TC 수, 전체 위반 수, 등급별 탭 수, 정리 우선순위 후보(attention 등급 defect_rate 내림차순)
- CLI: `uv run scripts/master_health.py <xlsx> [--exclude 탭1,탭2]` → JSON stdout. 입력 불변

## LLM 역할 (SKILL.md 워크플로우)

스크립트 JSON을 받아:
- **노후 의심**: TC 탭의 sample_rows(이미 parse_tab_meta가 제공)를 보고 낡은 용어·격식체 혼재·구조 불일치 의심 제기 (추정임을 명시, 단정 금지)
- **정리 우선순위 해석**: 결정론 점수 + 노후 신호를 종합해 "이 탭부터" 순위와 이유
- **탭 간 일관성**: 같은 도메인인데 컬럼 구성·톤이 다른 탭 지적

## 출력 (md)

```markdown
## 마스터 헬스 체크 — <파일명> (<날짜>)
### 요약
(한 줄: TC 탭 N개 중 attention M개, 전체 위반 K건, 우선 정리 대상 top 3)
### 탭별 대시보드
| 탭 | 템플릿 | TC 수 | 포맷 위반 | 탭내 중복 | 미실행(%) | 등급 |
### 정리 우선순위
1. <탭> — <등급> — <결정론 사유 + LLM 노후 의심>
### 비-TC 탭 (스캔 제외)
(탭명 + 제외 사유 — Priority 헤더 없음 / TC_ID 컬럼 없음 / Summary)
### 권고
(attention 탭은 qa:review-tc로 깊게, cross-tab 중복 의심 시도 안내)
```

## 번들 구성

- scripts = master_health(신규)·inspect_master·validate_format·find_duplicates·parse_results·extract_tc_table·tc_row·summary_xlsx (placeholder 후 sync)
  - master_health가 직접 호출: inspect_master·validate_format·find_duplicates·parse_results·extract_tc_table
  - sibling import 의존: validate_format→inspect_master·tc_row, find_duplicates→inspect_master, parse_results→extract_tc_table
- reference = format-rules.md (등급·enum 규약 참조)
- examples = sample-master-health.md

## 비목표

- 마스터 자동 수정·정리 (진단만 — 수정은 `qa:review-tc --patch` 또는 사람)
- cross-tab 전수 중복 검사 (review-tc 영역)
- 노후 판정의 결정론화 (날짜 메타 부재)

## 진행 순서

1. `master_health.py` TDD (RED → GREEN) — 탭 선별·등급·집계·CLI
2. SKILL.md·examples 작성, placeholder + sync, README 갱신(14종)
3. 전체 테스트 + `--check` + `~/.claude/skills` 설치 + 커밋·푸시

## 테스트 커버 (test_master_health.py)

- TC 탭 선별: Priority 헤더 있음/없음, TC_ID 컬럼 유무, Summary 탭 제외
- 등급: clean/minor/attention/empty 경계 (defect_rate 0.1 전후)
- 집계: 위반·중복 카테고리 합산, blank_ratio
- 우선순위 정렬: attention defect_rate 내림차순
- CLI: 정상 + --exclude + 비-TC 탭만 있는 파일
