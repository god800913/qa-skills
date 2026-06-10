# Figma 입력 사용법

TC 작성 시 Figma 디자인을 보조 입력으로 쓰는 방법. Figma는 *TC 작성의 입력*일 뿐이다 — 디자인 자체의 QA(픽셀 검증, 디자인-구현 일치)는 비목표.

## MCP 감지 (런타임)

특정 서버를 하드코딩하지 않는다. 세션에서 사용 가능한 도구를 확인:

1. 도구 목록(또는 ToolSearch)에서 `figma` 키워드 검색.
2. 대표 계열:
   - **공식 Figma Dev Mode MCP** — 도구 예: `get_code`, `get_image`, `get_variable_defs`. Figma 데스크톱 앱에서 Dev Mode MCP 서버 활성화 필요.
   - **framelink (figma-developer-mcp)** — 도구 예: `get_figma_data`, `download_figma_images`. `FIGMA_API_KEY` 환경 변수 필요 (키를 명령에 하드코딩하지 말 것).
3. 둘 다 없으면 → **막지 않는다.** PRD 단독 모드로 진행하고 안내 한 줄:
   "Figma MCP를 연결하면 UI 상태 커버리지가 좋아집니다. 연결 방법: 공식 Dev Mode MCP(Figma 앱 설정) 또는 framelink MCP."

## URL 파싱

- `https://www.figma.com/design/<FILE_KEY>/<name>?node-id=<NODE_ID>` 형태.
- `FILE_KEY`와 `node-id`를 추출해 도구 인자로 사용. node-id의 `-`는 API에 따라 `:`로 바꿔야 할 수 있음.

## TC에 반영하는 정보

| Figma에서 읽는 것 | TC 반영 위치 |
|---|---|
| 프레임/화면 이름, 네비게이션 흐름 | Test Item, Test Step (화면 이동 단계 구체화) |
| 버튼·라벨 등 실제 텍스트 | Test Step·Expected Result (실제 문구 그대로) |
| 상태별 프레임 (빈 상태, 에러, 로딩, 비활성) | 상태별 TC 추가 |
| 분기 화면 (iOS/Android 별도 프레임) | OS 컬럼 |

## PRD ↔ 디자인 불일치 규칙

- 디자인에만 있고 PRD에 없는 상태/요소 → TC는 만들되 **Comment에 "PRD 미정의, 디자인 기준" 명시**.
- PRD에 있는데 디자인에 없는 흐름 → TC는 PRD 기준으로 만들고 Comment에 "디자인 미반영 — 확인 필요".
- 텍스트가 서로 다르면 → Expected Result는 PRD 우선, Comment에 디자인 문구 병기.
