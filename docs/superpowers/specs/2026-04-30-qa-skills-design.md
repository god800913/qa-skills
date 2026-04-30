# QA Skills — 디자인 명세

> Hyperconnect (Azar) QA 팀이 PRD/피그마/기존 TC를 입력으로 받아 (1) 표준 테스트케이스 xlsx 생성, (2) 작성된 TC 리뷰, (3) PRD 모호점 추출을 수행하는 Claude Skill 묶음. 출력은 **xlsx 파일 전용** (Google Sheets API 사용 안 함).

- 작성일: 2026-04-30
- 작성자: dongjin (god800913@gmail.com)
- 상태: 초안 v3 (3-skill, Desktop-first)
- **타겟 환경**: Claude Desktop (claude.ai) 우선, Claude Code는 옵션

---

## 1. 배경 & 목적

### 현행 워크플로우
- Azar 릴리즈 마스터 시트(예: `[ver117] Release QA_Testcase`)에 30개 가까운 탭(`login`, `Lounge`, `Shop`, `in Match`, ...)으로 TC를 누적.
- PRD 1건이 들어오면 QA가 PRD/Figma를 읽고 표준 컬럼(Priority / OS / Automation Check / Test Item / TC_ID / Test Summary / Remote Config·Admin / Pre-condition / Test Step / Expected Result / Result / Jira no. / Comment)을 사람 손으로 채움.
- 변경의 성격에 따라:
  - 작은 변경 → 기존 탭에 행 append
  - 큰 신규 피처 → 새 탭 또는 별도 시트 생성

### 목적 (3개 스킬)
- **`qa:prd-clarify`** — PRD를 QA 관점으로 읽고 모호점·누락 엣지·미정의 상태를 Q&A 리스트로 뽑아 PM에게 돌려보냄. *Shift-left.*
- **`qa:generate-tc`** — 명확해진 PRD + 임베드된 Figma → 표준 TC xlsx 초안. append/신규 모드.
- **`qa:review-tc`** — 작성된 TC xlsx → 포맷·커버리지·일관성·중복 검사 → 심각도별 리뷰 리포트.

세 스킬은 워크플로우상 자연스러운 순서 (clarify → generate → review)로 이어지지만 **서로 호출하지 않고 독립**. 사용자가 시나리오에 맞춰 각각 호출.

### 비목표
- TC 자동 실행 / 자동 검증(automation runner) — 자동화 여부 컬럼만 표기.
- Jira 이슈 자동 등록 — `Jira no.` 컬럼 비움.
- 마스터 시트 Summary/리포트 탭 자동 갱신.
- Figma REST API/MCP 직접 접근.
- Google Sheets API 직접 쓰기 — **영구 제외**. 출력은 xlsx 파일만, QA가 시트에 수동 업로드 또는 가져오기.

---

## 2. 인프라 결정 (브레인스토밍 합의)

| 항목 | 결정 | 이유 |
|---|---|---|
| 타겟 환경 | Claude Desktop 우선, Claude Code 옵션 | QA 팀 사용 도구 |
| 스킬 구성 | 3개 — `qa:prd-clarify`, `qa:generate-tc`, `qa:review-tc`. 보조는 각 스킬 내부 스크립트 | Desktop은 단일 진입 패턴. 워크플로우 상 시작/생성/검토 3단계 |
| 운영 모드 (생성) | append + 신규 시트 둘 다 지원 | 현행 워크플로우 |
| Figma 입력 | PRD 임베드 이미지/링크만 | 권한·셋업 비용 0 |
| Notion 입력 | Notion MCP (양 환경 모두 설정) | 두 환경 모두 동작 |
| 파일 입력 (xlsx) | Desktop: 업로드 / Code: 로컬 경로 | 환경별 자연스러운 패턴 |
| 출력 (생성) | xlsx 파일 전용 (Desktop 다운로드, Code 로컬 저장). Sheets API 안 씀 | 단순함, 인증 셋업 0 |
| 출력 (리뷰/clarify) | 마크다운 리포트 (대화창 인라인 + 옵션 파일) | 사람 검토용 |
| 사람 컨펌 | xlsx 생성 *전* 마크다운 미리보기 필수 | 환각 방지 |
| 마스터 파일 변경 | 절대 in-place 금지, 항상 새 파일 산출 | 데이터 안전 |

---

## 3. 시스템 아키텍처

### 3.1 스킬 구성 (3개, 워크플로우 순서)

```
   [PRD가 들어옴]
        │
        ▼
┌────────────────────────┐
│  qa:prd-clarify        │  ← shift-left: PM에게 보낼 Q 리스트
│  PRD → 모호점 Q&A      │
│                        │
│  입력: Notion PRD URL  │
│  출력: 마크다운 Q&A    │
└────────────────────────┘
        │
        ▼ (QA가 PM 답변 받고 PRD 보강)
        │
┌────────────────────────┐
│  qa:generate-tc        │  ← 본 작업: TC xlsx 초안 생성
│  PRD → TC xlsx         │
│                        │
│  입력: Notion PRD URL  │
│        + (옵션) 마스터  │
│        + (옵션) 모드/탭 │
│  출력: TC가 든 xlsx    │
└────────────────────────┘
        │
        ▼ (생성 직후 또는 며칠 뒤)
        │
┌────────────────────────┐
│  qa:review-tc          │  ← 품질 게이트: 검수
│  TC → 리뷰 리포트      │
│                        │
│  입력: TC xlsx (업로드/ │
│         경로) + 탭     │
│         + (옵션) PRD   │
│  출력: 마크다운 리포트  │
│        (이슈 + 패치 제안)│
└────────────────────────┘
```

각 스킬은 **자체 완결적 번들** (Anthropic Skills 표준). 서로 호출 안 함.

### 3.2 책임 경계 원칙
- **스킬 = 워크플로우 + 도메인 판단**, **스크립트 = 결정론적 I/O·검증**.
- `qa:prd-clarify`는 외부 파일 의존 없음 (PRD 텍스트만).
- `qa:generate-tc`, `qa:review-tc`는 xlsx 처리 스크립트를 내부에 포함.
- 같은 `inspect_master.py`가 generate/review 양쪽에 들어감 — PoC 단계에서는 복제. Phase 3 (플러그인화) 시점에 공통 라이브러리로 분리 검토.

### 3.3 환경별 동작 차이

| 단계 | Claude Desktop | Claude Code |
|---|---|---|
| PRD 가져오기 | Notion MCP (데스크탑 설정) | Notion MCP (`~/.claude.json` 설정) |
| xlsx 입력 | 사용자가 첨부 업로드 → 샌드박스 경로 | 사용자가 로컬 경로 인자로 전달 |
| 미리보기·리포트 | 어시스턴트가 마크다운 출력 (인라인) | 동일 |
| 결과 xlsx | 샌드박스 생성 → 사용자 다운로드 | 로컬 경로 저장 |
| Python 실행 | 샌드박스 코드 실행 (pip 가능) | 로컬 Python (uv/pip) |

**핵심**: SKILL.md는 환경 자동 분기 ("로컬 경로 주어졌으면 그걸 사용, 아니면 업로드 요청"). Python 스크립트는 환경 무관 (CLI args).

### 3.4 외부 의존성

| 의존성 | 용도 | 대체 |
|---|---|---|
| Notion MCP | PRD 페이지·이미지 fetch | 사용자 본문 직접 붙여넣기 |
| python-calamine | xlsx 읽기 (openpyxl 깨짐 대응) | 없음 |
| openpyxl | xlsx 쓰기 (스타일) | xlsxwriter |
| Claude vision | 피그마 캡처 이미지 해석 | 사용자 텍스트 설명 |

---

## 4. 데이터 흐름

### 4.1 `qa:prd-clarify` 흐름

**Step 1. PRD 수집** — Notion MCP fetch → `{prd_text, figma_links[], image_urls[]}`.

**Step 2. 모호점 분석 (도메인 휴리스틱)**:
- Remote Config 플래그 언급되었지만 OFF 상태 동작 미정의?
- "iOS/Android 모두" 또는 "지원 OS" 명시 없음?
- 신규 화면 진입 경로가 한 가지만 기술됨? (다른 진입점은?)
- 에러/타임아웃/네트워크 실패 케이스 누락?
- 정량 기준 (`최대 N명`, `M초 후`) 모호?
- 결제·KYC·연령제한 등 정책성 문구 누락?
- mutual 시나리오인데 상대방 측 동작 미기술?
- 권한 요청·약관 변경 영향 없음?
- 분석 이벤트·로깅 명세 누락?
- A/B 테스트 셋업·롤아웃 단계 미정의?

**Step 3. Q&A 리포트 생성**:
- 각 항목: `[심각도] [영역] 질문 — 왜 중요한지 1줄 — PRD 인용`.
- 심각도: `Blocker / Major / Minor`. Blocker = TC 작성 불가능, Major = TC 품질 저하, Minor = 명확성 향상.
- 사용자가 그대로 PM에게 복붙 가능한 톤.

**Step 4. 출력**: 마크다운 (인라인) + 옵션으로 `prd-clarify-report-<날짜>.md` 파일 저장.

### 4.2 `qa:generate-tc` 흐름

**Step 1. PRD 수집** — `qa:prd-clarify`와 동일.

**Step 2. 컨텍스트 보강**
- **신규 시트 모드**: 사용자에게 신규 탭 이름 확인 → 표준 14컬럼 가이드.
- **append 모드**: 내장 `inspect_master.py` 실행 → `{tabs: [...], target_tab_meta: {columns, last_tc_id_per_section, sections, sample_rows[3]}}`.

**Step 3. TC 초안 생성** (휴리스틱):
- 핵심=P1, 일반=P2, 부가=P3, 엣지=P4
- Remote Config 플래그 → on/off 양쪽 TC 분기
- OS-specific 키워드 → OS 컬럼 명시
- mutual 키워드 (`매치`, `메시지`, `콜`, `라이브매치`) → mutual 템플릿 제안
- 한국어 작성, 기존 톤(짧은 명령형) 매칭
- 자동화 추정: 단순 UI=All, 결제·실시간=Skip

**Step 4. 사용자 컨펌 루프** — 마크다운 표 미리보기 → 수정 반영 → "OK" 받으면 진행.

**Step 5. xlsx 생성** — 내장 `new_workbook.py` 또는 `append_to_master.py` 실행.

**Step 6. 결과 보고** — 파일 경로 + TC 수 + 다음 액션.

### 4.3 `qa:review-tc` 흐름

**Step 1. TC 수집**
- 입력: xlsx 파일(업로드 또는 경로) + 탭 이름. 옵션: 참조 PRD URL.
- 내장 `inspect_master.py`로 탭 컬럼 매핑 + 행 데이터 로드.

**Step 2. 검사 항목** (4 카테고리):

**A) 포맷 검사 (스크립트 — `validate_format.py`)** — 결정론적
- 필수 컬럼 미입력 (Priority/TC_ID/Test Summary/Test Step/Expected Result)
- TC_ID 형식 (`<섹션>-<순번>`), 중복 ID
- Priority 범위 (P1~P4)
- OS enum (iOS/And/All/공란)
- Automation Check enum
- 빈 행, 섹션 헤더 누락

**B) 탭 내 일관성 검사 (스크립트 — 결정론적)**
- 같은 Test Summary가 여러 행에 반복됨
- 같은 Test Step (정규화 후) 여러 행에 반복됨
- Pre-condition에 언급된 객체가 Test Step에 등장하지 않음 (단어 매칭 휴리스틱, 권고 수준)
- Comment에 a/b/c 서브케이스가 있는데 Test Step은 단일

**C) 탭 간 중복 검사 (스크립트 — 결정론적)** — 같은 xlsx 파일 내 다른 탭들과 비교
- 다른 탭에 동일한 Test Summary 존재 → "Lounge 탭 1-12 ↔ More 탭 3-4: 동일 Test Summary"
- 다른 탭에 동일한 Test Step (정규화: 공백·줄바꿈·기호 제거 후 비교) 존재
- (LLM 옵션, 비활성 기본): 의미적으로 유사한 TC를 다른 탭에서 발견 (embedding 유사도 → LLM 판단). PoC에서는 정확 매칭만, 의미 유사는 후속.
- Summary/리포트 탭은 비교 대상에서 자동 제외.
- 탭 간 중복은 **자동 패치 대상 아님** (어느 쪽을 남길지 사람 판단 필요). 리포트만.

**D) 커버리지 검사 (LLM 판단, PRD 제공 시)** — 휴리스틱
- PRD에 언급된 기능 X가 어느 TC에도 없음
- Remote Config 플래그가 한 상태만 테스트됨
- OS-specific 명시인데 `All`로 표기됨
- mutual 시나리오인데 mutual 템플릿 미사용
- 네거티브/엣지 케이스 빈약

**E) 톤·도메인 검사 (LLM 판단)** — 휴리스틱
- 기존 시트 톤과 어긋나는 행 (격식체/구어체 혼용 등)
- Azar 도메인 용어 오용 (예: 라운지를 lounge로 영문 표기)

**Step 3. 리포트 생성**
- 심각도별 그룹: `Blocker / Major / Minor / Info`
- 각 이슈: `[심각도] 행 N (TC_ID X-Y) — 문제 — 수정 제안`
- 마지막에 요약 통계 (총 TC, 이슈 수, 카테고리 분포).

**Step 4. (옵션) 패치 제안**
- 사용자가 "자동 수정해줘" 요청 시 → 자동 패치 가능한 이슈(포맷 위반·TC_ID 중복)만 수정한 새 xlsx 생성 (원본은 그대로). 커버리지 갭·톤 문제는 리포트에 제안만 남기고 패치 안 함.
- 기본은 리포트만, 패치는 명시적 요청 시.

### 4.4 시퀀스 다이어그램 (qa:generate-tc append 모드)

```
QA       qa:generate-tc       Notion MCP    inspect_master.py   append_to_master.py
 │              │                    │              │                  │
 │─/qa:gen-tc──▶│                    │              │                  │
 │              │──fetch PRD─────────▶              │                  │
 │              │◀─prd_text+links────│              │                  │
 │              │──python inspect────────────────────▶                 │
 │              │◀─tab meta+samples─────────────────│                  │
 │              │ (draft TCs internally)            │                  │
 │◀──preview md─│                    │              │                  │
 │──"수정: …"──▶│                    │              │                  │
 │              │ (revise)                                              │
 │◀──preview md─│                                                       │
 │──"OK"───────▶│                                                       │
 │              │──python append─────────────────────────────────────────▶│
 │              │◀─output xlsx path─────────────────────────────────────│
 │◀─결과 보고──│                                                       │
```

---

## 5. 컴포넌트 명세

### 5.1 `qa:prd-clarify`
**목적**: PRD 모호점을 QA 관점에서 추출.

**구조**:
```
qa-prd-clarify/
├── SKILL.md
├── reference/
│   ├── ambiguity-checklist.md      # 10가지 검사 카테고리 + 각각 예시
│   └── domain-glossary.md          # Azar 용어 — qa-generate-tc/reference/와 동일 파일을 복제 (PoC 정책, §3.2 inspect_master.py와 동일)
└── examples/
    └── sample-clarify-report.md    # 톤 학습용
```

**SKILL.md frontmatter**:
- `name: qa-prd-clarify`
- `description: Notion PRD를 QA 관점에서 읽고 모호점·누락 엣지·미정의 상태를 PM에게 돌려보낼 질문 리스트로 뽑음. TC 작성 전 단계.`
- 트리거: "PRD 검토", "모호점 찾아", "PM에게 물어볼 거", `/qa:prd-clarify`

**입력 인자**:
- `prd_url` (필수): Notion 페이지 URL.
- `--save <path>` (옵션): 리포트를 마크다운 파일로 저장.

**출력 형식**:
```markdown
## PRD 모호점 분석 — <PRD 제목>

### Blocker (TC 작성 불가)
1. [Remote Config] `enableNewLoungeRecommendation` 플래그가 OFF일 때 동작 미정의.
   > PRD 인용: "신규 추천 알고리즘이 활성화되면..."

### Major (TC 품질 저하)
1. [Error case] 추천 데이터 fetch 실패 시 fallback UI 미기술.

### Minor (명확성)
1. [Wording] "충분한 시간 후"의 정량 기준 미정의.
```

### 5.2 `qa:generate-tc`
**목적**: PRD → 표준 TC xlsx 초안.

**구조**:
```
qa-generate-tc/
├── SKILL.md
├── scripts/
│   ├── inspect_master.py           # append 모드용
│   ├── new_workbook.py             # 신규 시트 모드
│   └── append_to_master.py         # append 모드
├── reference/
│   ├── template-spec.md            # 컬럼별 의미·작성 규칙
│   ├── domain-glossary.md          # Azar 용어
│   └── prioritization-guide.md     # P1~P4 판단 기준
└── examples/
    └── sample-tcs.md               # 톤 학습용 few-shot
```

**SKILL.md frontmatter**:
- `name: qa-generate-tc`
- `description: Notion PRD를 분석해서 표준 QA 테스트케이스 xlsx를 생성. 신규 시트 또는 기존 마스터에 append.`
- 트리거: "테스트 케이스 생성", "TC 만들어", `/qa:generate-tc`

**입력 인자**:
- `prd_url` (필수): Notion URL.
- `--append-to <path>` (옵션): 마스터 xlsx 경로 (Code) 또는 업로드 ID (Desktop). 없으면 신규 모드.
- `--target-tab <name>` (옵션): append 시 타겟 탭. 없으면 묻기.

**`inspect_master.py` 인터페이스**:
```bash
python inspect_master.py <xlsx_path> [--tab <tab_name>]
```
- `--tab` 미지정: 모든 탭 + 컬럼 수 + Summary 자동 제외 표시. JSON 출력.
- `--tab` 지정: 컬럼 매핑(헤더명→인덱스), 섹션 리스트, 섹션별 마지막 TC_ID, 샘플 행 3개. JSON 출력.

**`new_workbook.py` 인터페이스**:
```bash
python new_workbook.py --rows <rows.json> --output <out.xlsx> [--tab-name <name>] [--template single|mutual]
```

**`append_to_master.py` 인터페이스**:
```bash
python append_to_master.py --master <master.xlsx> --tab <tab_name> --rows <rows.json> --output <out.xlsx>
```
- 항상 새 파일에 저장. 원본 절대 수정 안 함.
- TC_ID 자동 증분 (지정 섹션의 last_tc_id에서 +1).
- 셀 병합·줄바꿈 스타일 보존.
- 같은 출력 경로 충돌 시 `(2)`, `(3)` 접미사.

**`rows.json` 스키마** (생성 스킬 두 스크립트 공통):
```json
{
  "rows": [
    {
      "section": "1. 라운지 메인",
      "Priority": "P1",
      "OS": "All",
      "Automation Check": "All",
      "Test Item": "메인 화면 UI",
      "Test Summary": "라운지 진입 시 추천 카드 노출",
      "Remote Config / Admin": "enableNewLoungeRecommendation: true",
      "Pre-condition": "...",
      "Test Step": "...",
      "Expected Result": "...",
      "Comment": "a: ...\nb: ..."
    }
  ]
}
```

각 행의 `section` 필드가 위치 결정. CLI에 별도 `--section` 인자 없음.

### 5.3 `qa:review-tc`
**목적**: 작성된 TC xlsx를 검수 → 마크다운 리포트.

**구조**:
```
qa-review-tc/
├── SKILL.md
├── scripts/
│   ├── inspect_master.py           # generate-tc와 동일 (PoC: 복제)
│   ├── validate_format.py          # 결정론적 포맷 검사 (카테고리 A)
│   ├── find_duplicates.py          # 탭 내 + 탭 간 중복 스캔 (카테고리 B 탭내·C 탭간)
│   └── extract_tc_table.py         # 탭의 TC를 JSON으로 평탄화 (LLM 분석용 — 카테고리 D·E)
├── reference/
│   ├── format-rules.md             # 결정론적 검사 항목 정의
│   ├── coverage-checklist.md       # LLM 휴리스틱 검사 카테고리
│   └── domain-glossary.md
└── examples/
    └── sample-review-report.md
```

**SKILL.md frontmatter**:
- `name: qa-review-tc`
- `description: 작성된 QA 테스트케이스 xlsx를 검수해서 포맷·커버리지·일관성·중복 이슈를 심각도별 리포트로 출력.`
- 트리거: "TC 리뷰", "테스트케이스 검토", "TC 문제점 찾아", `/qa:review-tc`

**입력 인자**:
- `xlsx_path` (필수, Code) 또는 업로드 (Desktop): 검토 대상 xlsx.
- `--tab <name>` (필수): 1차 검토할 탭. 미지정 시 전체 탭 목록 보여주고 선택 받기. **탭 간 중복 검사(C)는 항상 파일 내 모든 탭을 스캔**하여 `--tab` 행과 비교.
- `--prd-url <url>` (옵션): PRD 참조 → 커버리지 검사 활성화.
- `--severity <level>` (옵션): `blocker|major|minor|all` (기본 `major`).
- `--patch <out.xlsx>` (옵션): 자동 수정 가능한 이슈만 패치해서 새 xlsx 생성. 자동 패치 대상: **포맷 카테고리(A) 위반 + 같은 탭 내 TC_ID 중복 재할당**만. 탭 간 중복(C)·커버리지 갭(D)·톤 이슈(E)는 리포트에만 남기고 패치 안 함 (사람 판단 필요).
- `--cross-tab-scan <bool>` (옵션, 기본 `true`): 탭 간 중복 검사 on/off. 큰 마스터에서 시간 줄이려면 off.

**`validate_format.py` 인터페이스**:
```bash
python validate_format.py <xlsx_path> --tab <tab_name>
```
- 출력 (JSON): 각 행에 대한 포맷 위반 리스트.
- 결정론적, LLM 호출 없음.

**`extract_tc_table.py` 인터페이스**:
```bash
python extract_tc_table.py <xlsx_path> --tab <tab_name>
```
- 출력 (JSON): 헤더 매핑 적용된 TC 행 리스트 (LLM이 커버리지·일관성 분석용).

**`find_duplicates.py` 인터페이스**:
```bash
python find_duplicates.py <xlsx_path> --tab <tab_name> [--no-cross-tab]
```
- 출력 (JSON):
  ```json
  {
    "intra_tab": [
      {"row_a": 14, "row_b": 27, "field": "Test Summary", "value": "라운지 진입"}
    ],
    "cross_tab": [
      {"focus_tab": "Lounge", "focus_row": 12, "focus_tc_id": "1-12",
       "other_tab": "More", "other_row": 4, "other_tc_id": "3-4",
       "field": "Test Summary", "value": "..."}
    ]
  }
  ```
- 정규화 규칙: Test Step 비교 시 공백·줄바꿈·기호(`·`, `-`, ` `) 정규화 후 비교.
- `--no-cross-tab` 플래그로 탭 간 스캔 비활성.
- Summary/리포트 탭은 자동 제외 (`inspect_master.py`의 제외 룰 재사용).

**리포트 출력 예시**:
```markdown
## TC 리뷰 리포트 — Lounge 탭

### 요약
- 총 TC: 87
- Blocker: 0 / Major: 5 / Minor: 12 / Info: 3

### Blocker
(없음)

### Major
1. [포맷] 행 14 (TC_ID 1-12) — Expected Result 비어 있음.
2. [커버리지] PRD §3.2 "다국어 지원" 관련 TC 없음. 권장: KR/JP/EN 진입 TC 3개 추가.
3. [탭 내 중복] 행 23, 24 (TC_ID 2-1, 2-2) — Test Summary 동일 ("라운지 진입").
   제안: 2-2를 "라운지 진입 — 신규 가입자" 등으로 차별화.
4. [탭 간 중복] Lounge 1-12 ↔ More 3-4 — Test Summary 동일 ("내 프로필 진입").
   제안: 어느 탭이 정본인지 결정 후 다른 쪽 삭제 또는 컨텍스트 차별화.

### Minor
...
```

---

## 6. 표준 TC 템플릿

### 6.1 Single 템플릿 (기본 14컬럼)

> **컬럼 인덱스 주의**: 실제 마스터 시트는 탭마다 leading 빈 컬럼(인덱스 0)이 있는 경우(`login`, `More`)와 없는 경우(`Lounge`, `Shop`)가 섞여 있다. `inspect_master.py`가 헤더 행을 보고 *논리적 컬럼명 → 실제 인덱스* 매핑을 매번 만들어내므로, 아래 표의 # 컬럼은 **논리 순서**(개념)지 셀 인덱스가 아니다. 쓰기 스크립트는 항상 매핑을 입력으로 받아 셀 인덱스를 결정한다.

| # | 컬럼 | 타입 | 의미 | LLM 작성 가이드 |
|---|---|---|---|---|
| 1 | Priority | enum: P1~P4 | 중요도 | 핵심=P1, 일반=P2, 부가=P3, 엣지=P4 |
| 2 | OS | enum: iOS/And/All/공란 | 플랫폼 한정 | PRD에 명시 없으면 공란 |
| 3 | Automation Check | enum: All/iOS/Android/Skip | 자동화 가능성 | 단순 UI=All, 복잡=Skip |
| 4 | Test Item | str | 시나리오 그룹명 | 섹션 내 서브카테고리 |
| 5 | Automation TC_ID | str | 자동화 ID 매핑 | LLM 작성 안 함 (사람이 채움) |
| 6 | TC_ID | str (`<섹션>-<순번>`) | 식별자 | 자동 증분 |
| 7 | Test Summary | str (1줄) | 무엇을 검증하나 | 짧은 명사구 |
| 8 | Remote Config / Admin | str | 플래그·어드민 조건 | PRD에 있으면 명시 |
| 9 | Pre-condition | str (multiline) | 사전조건 | 국가/계정/설정 |
| 10 | Test Step | str (multiline) | 실행 절차 | 명령형 한 줄씩 |
| 11 | Expected Result | str (multiline) | 기대 결과 | 관찰 가능한 사실 |
| 12 | Result | str | 실행 결과 (사람 채움) | 비움 |
| 13 | Jira no. | str | 버그 티켓 (사람 채움) | 비움 |
| 14 | Comment | str (multiline) | 보충/의문 | a/b/c 서브케이스, 가정 명시 |

추가 옵션 컬럼(일부 시트에만 존재): `Policy : URL`, `Policy_page` — 마스터에 있으면 매핑하고 비워둠.

### 6.2 Mutual 템플릿 (in Match 류)

위 14컬럼 + `A`, `B` 컬럼 추가, `Test Step`이 `Test Reproduce`로 바뀜. 두 디바이스로 양방향 동작 검증.

자동 감지: 마스터의 해당 탭에 `A`, `B` 컬럼이 있으면 mutual 템플릿으로 분류.

---

## 7. 에러 처리 정책

### 7.1 입력 단계
| 케이스 | 행동 |
|---|---|
| Notion URL 권한 없음 | Notion MCP 인증 안내, 중단 |
| PRD 본문 < 50단어 | "PRD가 비어있는 듯, 본문 직접 붙여줄래?" |
| Figma 링크 있는데 이미지 없음 | "스크린샷 첨부 가능? 없으면 텍스트만으로 진행" |
| 마스터 xlsx 경로 오타 (Code) | cwd부터 최대 2단계 하위까지 `*.xlsx` 글롭, 후보 제안 |
| Desktop에서 xlsx 미업로드 | "파일 첨부해주세요" 안내, 중단 |

### 7.2 파싱 단계
| 케이스 | 행동 |
|---|---|
| 마스터 컬럼이 표준과 다름 | 발견된 컬럼 표시 + 매핑 직접 묻기 |
| mutual/single 모호 | A/B 컬럼 존재 여부로 판정, 모호하면 묻기 |

### 7.3 TC 생성 단계 (`qa:generate-tc`)
| 케이스 | 행동 |
|---|---|
| PRD 모호 | 가정을 명시적으로 나열 + "이 가정으로 진행?" 묻기. (또는 사용자에게 `qa:prd-clarify` 먼저 돌리라고 권유) |
| PRD-Figma 충돌 | 양쪽 차이 보고, 어느 쪽 따를지 묻기 |

### 7.4 리뷰 단계 (`qa:review-tc`)
| 케이스 | 행동 |
|---|---|
| 검토 대상 탭 없음 | 사용 가능한 탭 리스트 제공 |
| PRD 미제공 | 커버리지 검사 스킵, 포맷·일관성 검사만 수행 (리포트에 명시) |
| 포맷 위반이 너무 많아서 (>30%) LLM 분석이 의미 없음 | "포맷 먼저 정리하세요" + 위반만 리포트. (30% 임계는 경험적, 운영하면서 조정) |

### 7.5 출력 단계
| 케이스 | 행동 |
|---|---|
| 출력 파일 충돌 | `(2)`, `(3)` 접미사 자동 부여 |
| append 시 마스터 수정 시도 | 절대 금지. 항상 복사본에 작업. |
| TC_ID 충돌 (이미 존재) | 멈추고 사용자에게 보고 |

### 7.6 전반 정책
- **Fail loud**: 모호한 입력은 추측 금지, 묻기.
- **Idempotency**: 같은 PRD 두 번 → 중복 추가 방지 (TC_ID 충돌 감지).
- **Data safety**: 마스터 in-place 수정 절대 금지.
- **Read-only by default**: `qa:review-tc`는 패치 제안 시에도 새 파일 생성, 원본 안 건드림.

---

## 8. 테스트 전략

### 8.1 결정론적 스크립트 단위 테스트 (가장 중요)

**`new_workbook.py` / `append_to_master.py`** (qa:generate-tc 내부)
- 신규 워크북 → 14컬럼 + 줄바꿈 셀 + 섹션 헤더 행 정상 작성
- append → 기존 마스터 복사 + 지정 탭에 행 추가 + TC_ID 자동 증분 + 다른 탭 변화 없음
- mutual 시트에 single 행 추가 시도 → 명확한 에러
- 출력 경로 충돌 → 접미사 부여

**`inspect_master.py`** (양 스킬에 동일 복제, 한쪽에서만 테스트하면 충분)
- `[ver117]` 마스터 → 모든 탭 추출, Summary 자동 제외
- 각 탭의 컬럼 헤더 매핑 정확
- 섹션별 마지막 TC_ID 추출 (`1-23` → 다음은 `1-24`)
- mutual 템플릿 자동 감지

**`validate_format.py`** (qa:review-tc 내부)
- 필수 컬럼 누락 검출
- TC_ID 중복 검출 (탭 내)
- enum 위반 검출 (Priority, OS 등)
- Summary 탭에서 호출되면 무시

**`find_duplicates.py`** (qa:review-tc 내부)
- 탭 내: 같은 Test Summary 반복 검출
- 탭 내: 같은 Test Step (정규화 후) 반복 검출
- 탭 간: 다른 탭에 동일 Test Summary 존재 (Summary 탭 제외)
- 탭 간: 다른 탭에 동일 Test Step (정규화 후) 존재
- `--no-cross-tab` 플래그 동작 검증
- 픽스처 요건: `master_v117_minimal.xlsx`에 의도적 탭 내·탭 간 중복 행을 1쌍씩 심어둔다

**`extract_tc_table.py`** (qa:review-tc 내부)
- 헤더 매핑 적용된 행 리스트 정확

**픽스처**: `tests/fixtures/master_v117_minimal.xlsx` (제공받은 마스터에서 2~3개 탭만 추출한 mini). 픽스처 요건: **leading 빈 컬럼이 있는 탭과 없는 탭을 모두 포함**해야 함 (§6.1 컬럼 인덱스 주의 참조). 그래야 `inspect_master.py` 매핑 로직이 단위 테스트로 커버됨. `tests/fixtures/sample_tc_with_issues.xlsx` (의도적 포맷 위반 + 중복 + 빈 셀 포함).

### 8.2 LLM 워크플로우 통합 테스트 (수동, PoC 단계)

**`qa:prd-clarify`**:
- 픽스처 PRD (의도적 모호점 포함) → Blocker/Major/Minor 분류 정확 (사람 검수)
- PRD 깨끗한 경우 → "이슈 없음" 정확히 보고

**`qa:generate-tc`**:
- 픽스처 PRD (가짜 라운지 신기능) → TC 표가 품질 기준 충족
- "Remote Config 플래그 X" PRD → on/off 양쪽 TC 자동 생성
- mutual 키워드 PRD → mutual 템플릿 사용 제안
- 회귀: 같은 PRD 두 번 → 의미 동일

**`qa:review-tc`**:
- `sample_tc_with_issues.xlsx` → 모든 의도적 이슈 검출 + 잘못된 false-positive 없음
- 탭 내 중복 + 탭 간 중복 모두 정확히 지적
- PRD 함께 줬을 때 커버리지 갭 정확히 지적

LLM-judge 자동 평가 루프는 PoC 범위 밖. Phase 3 (플러그인화) 이후 검토.

### 8.3 E2E
- 환경별로 1회 수동 검증:
  - Claude Code: 로컬 마스터 xlsx + Notion URL → 3개 스킬 순차 실행
  - Claude Desktop: 마스터 업로드 + Notion URL → 3개 스킬 순차 실행
- CI는 스크립트 단위 테스트만 자동화. LLM 호출은 수동.

---

## 9. 패키징 & 배포

### 9.1 디렉토리 구조 (PoC, 모노레포)
```
/Users/dongjin/Dropbox/workplace/HyperConnect/poc/qa-skills/
├── skills/                              # 각 스킬 = 독립 번들
│   ├── qa-prd-clarify/
│   │   ├── SKILL.md
│   │   ├── reference/
│   │   │   ├── ambiguity-checklist.md
│   │   │   └── domain-glossary.md
│   │   └── examples/sample-clarify-report.md
│   ├── qa-generate-tc/
│   │   ├── SKILL.md
│   │   ├── scripts/
│   │   │   ├── inspect_master.py
│   │   │   ├── new_workbook.py
│   │   │   └── append_to_master.py
│   │   ├── reference/
│   │   │   ├── template-spec.md
│   │   │   ├── domain-glossary.md
│   │   │   └── prioritization-guide.md
│   │   └── examples/sample-tcs.md
│   └── qa-review-tc/
│       ├── SKILL.md
│       ├── scripts/
│       │   ├── inspect_master.py        # generate-tc와 동일 (복제)
│       │   ├── validate_format.py
│       │   └── extract_tc_table.py
│       ├── reference/
│       │   ├── format-rules.md
│       │   ├── coverage-checklist.md
│       │   └── domain-glossary.md
│       └── examples/sample-review-report.md
├── tests/
│   ├── fixtures/
│   │   ├── master_v117_minimal.xlsx
│   │   ├── sample_prd.md
│   │   └── sample_tc_with_issues.xlsx
│   └── test_*.py                        # 스크립트별 단위 테스트
├── docs/
│   └── superpowers/specs/
│       └── 2026-04-30-qa-skills-design.md   # 이 문서
├── pyproject.toml                       # uv/pip 의존성
└── README.md
```

**Code 사용 시 추가**: 프로젝트 루트에 `.claude/` 심볼릭 링크 또는 복사로 `skills/` 노출. 또는 사용자 글로벌 `~/.claude/skills/`로 설치.

**Desktop 사용 시**: 각 스킬 디렉토리를 zip → Anthropic Skills 업로드 (또는 향후 Skills 마켓플레이스).

### 9.2 의존성
- Python 3.11+
- `python-calamine` (read xlsx)
- `openpyxl` (write xlsx, 스타일)

### 9.3 단계별 배포

| Phase | 환경 | 대상 | 상세 |
|---|---|---|---|
| 1 (PoC) | Code 로컬 | 본인 | 프로젝트 `.claude/skills/`에서 검증 |
| 2 (PoC v2) | Desktop 수동 업로드 | 본인 + QA 1명 | zip 만들어서 Desktop에 직접 업로드, 손으로 onboard |
| 3 (팀 시범) | Desktop 마켓 | QA 2~3명 | Anthropic Skills 마켓플레이스 등록 (사내 공유 형태) |
| 4 (확장) | Desktop + Code 양쪽 | QA 팀 전원 | + Figma MCP 옵션 (Sheets API는 영구 제외) |

---

## 10. 미정 / 후속 결정

| 항목 | 현재 결정 | 후속 |
|---|---|---|
| 피그마 직접 접근 | PRD 임베드만 | REST API 또는 Figma Dev Mode MCP 추가 (권한 확인 후) |
| Sheets 직접 쓰기 | xlsx만 | **영구 제외** — 사용자 결정. QA가 시트에 수동 업로드 |
| 마스터 컬럼 표준화 | 시트마다 변형 허용, 매번 매핑 | 팀 합의로 표준 정착하면 단순화 |
| Summary 탭 자동 갱신 | 범위 밖 | 팀 요청 시 분리 스킬 (`qa:release-summary`) |
| 자동화 TC_ID 매핑 | 사람 수기 | 자동화 스크립트 인덱스와 자동 연결 |
| Jira 자동 등록 | 범위 밖 | 분리 스킬 (`qa:bug-report`), Jira MCP 활용 |
| `inspect_master.py` 중복 | generate/review에 복제 | Phase 3에서 공통 라이브러리로 분리 |
| PRD diff (`qa:diff-prd`) | 범위 밖 | 팀 요청 시 추가 |
| LLM-judge 자동 평가 | 범위 밖 | Phase 3+ 도입 검토 |

---

## 11. 변경 이력
- 2026-04-30: 초안 v1 작성 (브레인스토밍 직후, 3-skill `generate/read-master/write-xlsx`).
- 2026-04-30: spec-document-reviewer 권고 반영 — §6 컬럼 인덱스 주석 + Policy 옵션 컬럼 명시, §5.3 `rows.json` 스키마 추가, §7.1 `ls` 검색 범위 한정, §8.3 LLM-judge 범위 명시.
- 2026-04-30: v2 — Desktop-first 재구성. 환경별 동작 차이 §3.3 추가.
- 2026-04-30: v3 — 스킬을 워크플로우 단계별로 재정의: `qa:prd-clarify` (신규) + `qa:generate-tc` (재정의, 보조 스크립트 내부화) + `qa:review-tc` (신규). `qa:read-master`, `qa:write-xlsx`는 별도 스킬에서 내부 스크립트로 통합.
- 2026-04-30: v3 reviewer 권고 반영 — §5.3 `--patch` 자동 패치 카테고리 명시(포맷·TC_ID 중복만), §5.1 domain-glossary 복제 정책 명시, §8.1 픽스처 요건(leading-blank 탭 포함), §7.4 30% 임계 rationale.
- 2026-04-30: v3.1 — Google Sheets API 경로 영구 제외. 출력은 xlsx 파일 전용 (사용자 결정).
- 2026-04-30: v3.2 — `qa:review-tc`에 **탭 간 중복 검사**(카테고리 C) 명시 추가. `find_duplicates.py` 스크립트 신설 (탭 내·탭 간 통합). `--cross-tab-scan` 플래그, 리포트 예시·테스트 픽스처 요건 갱신. 탭 간 중복은 자동 패치 대상 아님.
