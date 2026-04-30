# 예시: qa:prd-clarify 출력

이 파일은 LLM이 출력 톤·구조를 학습하는 few-shot. `tests/fixtures/sample_prd.md` (라운지 신규 추천 알고리즘)를 입력으로 받았을 때 기대되는 리포트.

---

## PRD 모호점 분석 — 라운지 신규 추천 알고리즘

### Blocker (TC 작성 불가)
1. [Remote Config] `enableNewLoungeRecommendation` 플래그가 OFF일 때 동작 미정의. 기존 알고리즘으로 폴백되는가, 아예 추천 섹션이 안 노출되는가?
   > "`enableNewLoungeRecommendation` 플래그가 활성화되면 신규 알고리즘이 동작."

### Major (TC 품질 저하)
1. [에러 케이스] 추천 데이터 fetch 실패 / 빈 결과일 때의 fallback UI 미기술. 빈 화면? 에러 메시지? 기본 추천?
2. [OS 플랫폼] iOS/Android 양쪽 동일한 동작인지 명시 없음. 한쪽만 우선 출시인지?

### Minor (명확성)
1. [정량 기준] 가로 스크롤 카드의 표시 개수·크기 미정의. 디자인 시안에서 확인 가능한가?

---

**PM에게 보내는 메모 (복붙 가능)**

안녕하세요, 라운지 신규 추천 알고리즘 PRD 검토 중 다음 부분이 모호해서 답변 부탁드립니다:

1. (Blocker) `enableNewLoungeRecommendation` 플래그 OFF 시 동작 — 기존 알고리즘으로 폴백되나요, 추천 섹션이 안 노출되나요?
2. (Major) 추천 데이터 fetch 실패/빈 결과 시 fallback UI는 어떻게 되나요?
3. (Major) iOS/Android 동시 출시인지, 한쪽 우선인지 알려주세요.
4. (Minor) 가로 스크롤 카드 개수·크기 디자인 시안 위치 부탁드립니다.

감사합니다.
