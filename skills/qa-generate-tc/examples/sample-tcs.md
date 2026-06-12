# 예시: qa:generate-tc 출력 (Lounge 신규 추천 PRD)

LLM 톤·세분도 학습용 few-shot. `tests/fixtures/sample_prd.md`를 입력으로 받았을 때 기대되는 TC 표 (마크다운 미리보기 형태).

## 1. 라운지 메인 (신규 시트 모드 가정)

| Priority | OS | Automation | Test Item | TC_ID | Test Summary | Remote Config | Pre-condition | Test Step | Expected Result | Comment |
|---|---|---|---|---|---|---|---|---|---|---|
| P1 | All | All | 추천 섹션 | 1-1 | 라운지 진입 시 추천 섹션 노출 | enableNewLoungeRecommendation: true | 신규 사용자, KR | 1. 앱 실행<br>2. 라운지 탭 진입 | 상단에 "추천" 섹션 노출, 가로 스크롤 카드 | a: 카드 개수 확인<br>b: 첫 카드의 프로필 사진+닉네임 표시 |
| P1 | All | Skip | 추천 섹션 | 1-2 | Remote Config OFF 시 동작 | enableNewLoungeRecommendation: false | 신규 사용자 | 1. 앱 실행<br>2. 라운지 탭 진입 | TBD (PM 확인 필요) | (Blocker) RC OFF 시 동작 미정의 — 추천 섹션 비노출인지 기존 알고리즘 폴백인지 |
| P2 | All | Skip | 분석 이벤트 | 1-3 | lounge_recommendation_shown 발생 | enableNewLoungeRecommendation: true | 분석 로그 디버그 모드 | 1. 라운지 탭 진입 | 화면 진입 시 lounge_recommendation_shown 1회 발생 | 파라미터는 PRD 미정의 |
| P3 | All | Skip | 정책 | 1-4 | 차단한 상대 추천 제외 | enableNewLoungeRecommendation: true | A 사용자가 B 사용자 차단 상태 | 1. A로 라운지 진입 | 추천 카드에 B 미포함 | |
| P4 | All | Skip | 에러 케이스 | 1-5 | 추천 데이터 fetch 실패 | enableNewLoungeRecommendation: true, 네트워크 차단 | 비행기 모드 | 1. 라운지 탭 진입 | 에러 안내 노출, 네트워크 복구 후 재진입 시 정상 노출 | 가정: 별도 정의 없어 공통 에러 처리 패턴 적용 — PM 확인 시 갱신 |

## 비고
- TC_ID는 자동 증분 (1-1, 1-2, ...)
- 모호점 핸드오프 규약 (SKILL.md 4단계): 1-2가 Blocker 예시 (`TBD (PM 확인 필요)` + `(Blocker) ...`), 1-5가 Major 예시 (가정을 Expected Result에 + `가정: ...`)
- 한국어 톤: 짧은 명령형. 격식체 회피.
