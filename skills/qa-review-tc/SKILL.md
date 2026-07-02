---
name: qa-review-tc
description: 작성된 QA 테스트케이스 xlsx를 검수해서 포맷 위반·탭 내 일관성·탭 간 중복·커버리지 갭·톤 이슈를 심각도별 마크다운 리포트로 출력. 옵션 --patch로 자동 수정 가능 이슈만 새 xlsx 생성. 트리거 — "TC 리뷰", "테스트케이스 검토", "TC 문제점 찾아", "/qa:review-tc".
---

# qa:review-tc

작성된 TC xlsx의 품질을 5개 카테고리로 검수한다:
- A. 포맷 (스크립트, 결정론적)
- B. 탭 내 일관성 (스크립트, 결정론적)
- C. 탭 간 중복 (스크립트, 결정론적)
- D. 커버리지 (LLM, PRD 제공 시)
- E. 톤·도메인 (LLM)

## 입력
- TC xlsx 파일 (Code: 로컬 경로 / Desktop: 업로드)
- `--tab <name>`: 1차 검토 탭 (필수). 미지정 시 전체 탭 목록 보여주고 선택.
- `--prd-url <url>`: PRD 참조 → 카테고리 D 활성화 (옵션)
- `--severity <level>`: blocker|major|minor|all (기본 major) — 상세 목록에 표시할 하한 필터. 요약 카운트는 항상 전체 집계
- `--patch <out.xlsx>`: 자동 수정 가능 이슈만 패치 (TC_ID 중복만 — `reference/format-rules.md` 자동 패치 표 참조)
- 탭 간 중복 스캔 기본 ON, `--no-cross-tab`로 비활성
- `--save <path>`: 리포트를 파일로 저장 (옵션, 기본은 인라인 마크다운)

## 워크플로우

### 1. 입력 수집
- xlsx 경로 또는 업로드 받기
- 탭 미지정 시 `scripts/inspect_master.py`로 전체 탭 목록 보여주고 사용자 선택 받기
- (옵션) PRD URL 받기 → Notion MCP fetch

### 2. 결정론적 검사 (카테고리 A·B·C)

**카테고리 A — 포맷**:
```bash
uv run scripts/validate_format.py <xlsx> --tab <name>
```
JSON 결과: 필수 누락, enum 위반, TC_ID 중복.

**카테고리 B·C — 중복**:
```bash
uv run scripts/find_duplicates.py <xlsx> --tab <name>
```
JSON 결과: 탭 내 (Test Summary/Step 반복) + 탭 간 (다른 탭의 동일 항목).

### 3. LLM 분석 (카테고리 D·E, 옵션)

**TC 데이터 평탄화**:
```bash
uv run scripts/extract_tc_table.py <xlsx> --tab <name>
```
JSON 행 리스트를 받아서 `reference/coverage-checklist.md`의 항목별로 점검:
- PRD 제공 시 카테고리 D (커버리지)
- 항상 카테고리 E (톤·도메인)

### 4. 리포트 합성
모든 결과를 심각도별로 그룹화한 마크다운:

```markdown
## TC 리뷰 리포트 — <탭 이름>

### 요약
- 총 TC: N
- Blocker: 0 / Major: M / Minor: m / Info: i

### Blocker
1. [카테고리] 행 N (TC_ID X-Y) — 문제 — 수정 제안

### Major
...

### Minor
...

### (선택) 자동 패치 미리보기
다음 이슈는 `--patch` 옵션으로 자동 수정 가능:
- TC_ID 중복 N건 → 두 번째 이후에 -dup-N 접미사
```

### 5. (옵션) 패치 적용
사용자가 "자동 수정해줘" 또는 `--patch <out>` 지정 시:

```bash
uv run scripts/patch_tc_ids.py <xlsx> --tab <name> --output <out.xlsx>
```

- TC_ID 중복만 자동 패치: 두 번째 이후 등장 ID에 `-dup-N` 접미사 (예: `1-2` → `1-2-dup-2`)
- stdout 마지막 라인이 실제 출력 경로 (collision 시 `(2)` 접미사 자동)
- 원본 xlsx는 절대 수정 안 함
- 필수 누락·enum 위반·커버리지·톤 이슈는 패치 안 함, 리포트에만 남김 (사람 판단)

### 6. 결과 보고
- 출력 형식: 인라인 마크다운 (또는 `--save <path>` 시 파일)
- 패치 출력 경로 (있는 경우)

## 비목표
- TC 자체 작성 (그건 `qa:generate-tc`)
- PRD 분석 (그건 `qa:prd-clarify`)

## 트러블슈팅
- 검토 대상 탭 없음 → 사용 가능 탭 목록 제공
- PRD 미제공 → 카테고리 D 스킵, 리포트에 명시
- 포맷 위반이 너무 많음 (>30%) → "포맷 먼저 정리하세요" + 위반만 리포트 (LLM 분석 스킵)

## 예시
`examples/sample-review-report.md` 참조.
