# 커버리지·일관성 체크리스트 (qa:review-tc 카테고리 D·E)

LLM이 PRD와 TC를 비교해서 검출하는 항목.

## D. 커버리지 검사 (PRD 제공 시)

PRD를 같이 읽고 다음을 점검:

1. **언급된 기능 X가 TC에 없음** — PRD §N의 기능이 어느 행도 다루지 않음.
2. **Remote Config 한 상태만 테스트** — 플래그 ON 동작만 있고 OFF는 없음 (또는 그 반대).
3. **OS-specific인데 All로 표기** — PRD가 "iOS 전용"이라고 명시했는데 TC OS=All.
4. **mutual 시나리오인데 mutual 템플릿 미사용** — PRD에 양방향 키워드 (`매치`, `메시지`, `콜`, `라이브매치`)가 있는데 TC가 single 템플릿.
5. **네거티브/엣지 빈약** — P1/P2만 잔뜩, P3/P4가 없음. PRD에 에러 케이스가 명시되어 있는데 TC에 없음.

## E. 톤·도메인 검사

기존 시트의 sample_rows를 참고해서:

1. **톤 불일치** — 격식체/구어체 혼용 (예: "확인하시오" vs "확인해").
2. **도메인 용어 오용** — 라운지를 "lounge"로 영문 표기, 매치를 "matching"으로 표기 등.
3. **불필요한 long-form** — Test Step이 5문장 넘게 길어짐 (관찰 가능성 저하).

## 자동 패치 가능 여부
**모두 불가**. 사람 판단 필요. 리포트에 제안만 명시.

## 심각도 매핑
- 핵심 기능 누락 (Coverage 1번) → Major
- Remote Config 양분기 누락 (Coverage 2번) → Major
- OS-specific 불일치 (Coverage 3번) → Major
- mutual 미사용 (Coverage 4번) → Minor (제안)
- 엣지 빈약 (Coverage 5번) → Minor
- 톤 불일치 (Tone 1번) → Minor
- 도메인 오용 (Tone 2번) → Minor
- long-form (Tone 3번) → Info
