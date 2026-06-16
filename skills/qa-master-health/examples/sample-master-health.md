# 예시: qa:master-health 출력 (Azar 마스터, 8탭)

`master_health.py` JSON을 받아 합성한 리포트 형태.

## 마스터 헬스 체크 — azar-tc-master.xlsx (2026-06-16)

### 요약
TC 탭 **6개** 중 attention **2개**, 전체 포맷 위반 **14건**. 우선 정리: **Shop**, **More**, (노후 의심) **login**.

### 탭별 대시보드

| 탭 | 템플릿 | TC 수 | 포맷 위반 | 탭내 중복 | 미실행(%) | 등급 |
|---|---|---|---|---|---|---|
| Lounge | single | 42 | 0 | 0 | 12% | clean |
| in Match | mutual | 31 | 1 | 0 | 6% | minor |
| Shop | single | 28 | 9 | 2 | 39% | **attention** |
| More | single | 15 | 3 | 1 | 20% | **attention** |
| login | single | 24 | 0 | 0 | 8% | clean |
| Setting | single | 0 | 0 | 0 | — | empty |

### 정리 우선순위
1. **Shop** — attention — 포맷 위반 9건(필수 누락 6·enum 위반 3) + 탭내 중복 2건. 위반율 0.39로 최고. `qa:review-tc Shop`으로 정밀 검수 권장
2. **More** — attention — 위반 3건 + 중복 1건(위반율 0.27)
3. **login** — clean(결정론) 이지만 **노후 의심**(LLM 추정): sample_rows에 "미러" 대신 구 용어 "프리뷰"가 남아 있고 종결어미가 격식체("~합니다")로 다른 탭과 혼재. 도메인 용어 업데이트 검토 — 추정이므로 담당자 확인 필요

### 비-TC 탭 (스캔 제외)

| 탭 | 사유 |
|---|---|
| Summary | Summary 탭 |
| Changelog | Priority 헤더 없음 |

### 권고
- Shop·More는 `qa:review-tc <탭> --patch`로 TC_ID 중복부터 자동 정리, 필수 누락·enum은 리포트 확인 후 수동
- Setting 탭(empty)은 폐기 또는 작성 대상인지 PM 확인
- 탭 간 중복이 의심되면 해당 탭에 `qa:review-tc`(cross-tab 기본 ON)
