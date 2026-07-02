---
name: qa-master-health
description: 마스터 TC 워크북 전체를 한 번에 스캔해 탭별 포맷 위반·중복·미실행·노후 의심을 등급(clean/minor/attention)으로 정리하고 "어느 탭부터 정리할지" 우선순위를 매긴다. 정기 점검·인수인계·대청소에 사용. 트리거 — "마스터 건강 체크", "전체 탭 점검", "어느 탭부터 정리", "TC 전수 검사", "/qa:master-health".
---

# qa:master-health

마스터 워크북의 모든 TC 탭을 가로로 스캔한다. `qa:review-tc`가 탭 하나를 깊게 본다면, 이 스킬은 "마스터 전체가 지금 얼마나 건강한가, 어느 탭이 썩고 있나"를 한 장으로 만든다.

## 입력
- 마스터 xlsx 한 개 (탭 지정 없이 전체)
- `--exclude` 스캔에서 뺄 탭, 쉼표 구분 (옵션)

## 워크플로우

### 1. 결정론 전수 스캔
```bash
uv run scripts/master_health.py <master>.xlsx [--exclude 탭1,탭2]
```
JSON 결과:
- **탭 선별** — Summary 탭 / Priority 헤더 없음 / TC_ID 컬럼 없음은 비-TC 탭으로 제외 (목록과 사유는 보고). single/mutual 자동 판별
- **탭별 지표** — `tc_count` / `format_violations`(카테고리별 분해) / `intra_dup_count`(탭 내 중복) / `blank_ratio`(미실행 비율, 정보용)
- **등급** — `empty`(TC 0건) / `clean`(위반 0) / `minor`(위반율 ≤ 0.1) / `attention`(그 외)
- **요약** — 탭 수·TC 수·전체 위반·등급별 분포 + `cleanup_priority`(attention 탭을 위반율 내림차순)

### 2. 노후·일관성 판단 (LLM)
스크립트가 제공하는 정보 + 각 탭 sample_rows를 보고:
- **노후 의심**: 낡은 용어·격식체 혼재·도메인 변화 미반영 같은 신호로 의심만 제기 (마스터엔 수정일 메타가 없으므로 **추정임을 명시, 단정 금지**)
- **탭 간 일관성**: 같은 도메인인데 컬럼 구성·톤이 다른 탭 지적
- 결정론 등급과 노후 신호를 종합해 정리 우선순위 해석

### 3. 리포트 합성 (md)
```markdown
## 마스터 헬스 체크 — <파일명> (<날짜>)
### 요약
(한 줄: TC 탭 N개 중 attention M개, 전체 위반 K건, 우선 정리 top 3)
### 탭별 대시보드
| 탭 | 템플릿 | TC 수 | 포맷 위반 | 탭내 중복 | 미실행(%) | 등급 |
### 정리 우선순위
1. <탭> — <등급> — <결정론 사유 + LLM 노후 의심>
### 비-TC 탭 (스캔 제외)
| 탭 | 사유 |
### 권고
(attention 탭은 `qa:review-tc`로 깊게 — 탭 간 중복 스캔은 기본 포함)
```
- 수치·등급은 스크립트 JSON 그대로 — LLM이 재집계하지 않는다.

### 4. 다음 액션 안내
- attention 탭 → `qa:review-tc <탭>`으로 정밀 검수 (+ `--patch`로 TC_ID 중복 자동 수정)
- 미실행 비율이 높은 탭이 실행 대상이면 → `qa:minimal-coverage`로 우선순위

## 비목표
- 마스터 자동 수정·정리 (진단만 — 수정은 `qa:review-tc --patch` 또는 사람)
- 탭 간(cross-tab) 전수 중복 검사 (무겁고 노이즈 큼 — `qa:review-tc` 영역)
- 노후 판정의 결정론화 (작성·수정일 메타 부재)
- 커버리지·톤 심층 검수 (그건 `qa:review-tc`)

## 트러블슈팅
- TC 탭이 0개로 나옴 → 헤더 행에 `Priority`·`TC_ID`가 있는지 확인 (마스터 헤더 변형은 `inspect_master`가 흡수하지만 완전히 다른 구조면 비-TC로 빠짐)
- 특정 탭만 보고 싶으면 이 스킬 대신 `qa:review-tc <탭>` 사용

## 예시
`examples/sample-master-health.md` 참조.
