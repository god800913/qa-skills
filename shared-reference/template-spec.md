# 표준 TC 템플릿 스펙

## Single 템플릿 (14 컬럼)

| 컬럼 | 타입 | 의미 | LLM 작성 가이드 |
|---|---|---|---|
| Priority | enum P1~P4 | 중요도 | 핵심=P1, 일반=P2, 부가=P3, 엣지=P4 |
| OS | enum iOS/And/All/공란 | 플랫폼 한정 | PRD에 명시 없으면 공란 |
| Automation Check | enum All/iOS/Android/Skip | 자동화 가능성 | 단순 UI=All, 복잡=Skip |
| Test Item | str | 시나리오 그룹명 | 섹션 내 서브카테고리 |
| Automation TC_ID | str | 자동화 ID 매핑 | LLM은 비워둠 |
| TC_ID | `<섹션>-<순번>` | 식별자 | 자동 증분 |
| Test Summary | str (1줄) | 무엇을 검증하나 | 짧은 명사구 |
| Remote Config / Admin | str | 플래그·어드민 조건 | PRD에 있으면 명시 |
| Pre-condition | str (multiline) | 사전조건 | 국가/계정/설정 |
| Test Step | str (multiline) | 실행 절차 | 명령형 한 줄씩 |
| Expected Result | str (multiline) | 기대 결과 | 관찰 가능한 사실 |
| Result | str | 실행 결과 | 비움 (사람 채움) |
| Jira no. | str | 버그 티켓 | 비움 (사람 채움) |
| Comment | str (multiline) | 보충/의문 | a/b/c 서브케이스, 가정 명시 |

옵션 컬럼 (일부 시트만): `Policy : URL`, `Policy_page` — 마스터에 있으면 매핑하고 비워둠.

## Mutual 템플릿 (in Match 류)

위 14컬럼 + `A`, `B` 컬럼 추가, `Test Step`이 `Test Reproduce`로 변경. 두 디바이스로 양방향 동작 검증.

자동 감지: 마스터의 해당 탭에 `A`, `B` 컬럼 존재 시 mutual.

## 컬럼 인덱스 주의

마스터 시트는 탭마다 leading 빈 컬럼 인덱스 0이 있는 탭(`login`, `More`)과 없는 탭(`Lounge`, `Shop`)이 섞여 있다. 헤더명 → 실제 셀 인덱스 매핑은 매번 `inspect_master.parse_tab_meta`가 만들어낸다. 위 표의 순서는 *논리 순서*이지 셀 인덱스 아님.

## 줄바꿈·서식 규칙

- `Test Step`, `Expected Result`, `Pre-condition`, `Comment`는 multiline. `\n` 사용.
- 셀에 wrap_text=True 적용.
- `Comment`의 a/b/c 서브케이스는 다음 형식:
  ```
  a: 첫 번째 서브케이스 설명
  b: 두 번째 서브케이스 설명
  c: ...
  ```
