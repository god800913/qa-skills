# 스코어링 규칙 (scoring-rules)

> 진실의 원천은 `shared/select_minimal_coverage.py`. 이 문서는 해당 코드의 동작을 사람이 읽을 수 있게 요약한 것이다. 코드와 충돌하면 코드가 우선한다.

## 스코어 공식

```
score = risk_score + coverage_gain - execution_cost - redundancy_penalty
```

- **risk_score** = PRIORITY_BASE[Priority] + 1.0 (고위험 키워드 포함 시)
- **coverage_gain** = 0.5 × 아직 커버되지 않은 신규 리스크 태그 수
- **execution_cost** = 0.1 × Test Step 줄 수 (최소 1줄 취급) + 0.5 (Remote Config 셋업 있으면)
- **redundancy_penalty** = 이미 커버된 태그 비율 (0.0 ~ 1.0, 태그 없는 행은 0.0)

## PRIORITY_BASE 표

| Priority | 기본 점수 |
|----------|-----------|
| P1       | 3.0       |
| P2       | 2.0       |
| P3       | 1.0       |
| P4       | 0.5       |
| (미입력)  | 1.0       |

## HIGH_RISK_KEYWORDS 목록

결제, 구매, 환불, 구독, 신고, 차단, 매치, 콜, 라이브, 권한, 로그인, 탈퇴, remote config, 어드민

검색 대상 컬럼: `Test Summary`, `Test Item`, `Remote Config / Admin`, `Pre-condition` (소문자 변환 후 부분 문자열 매칭).

## 강제 포함 조건

Priority == "P1" **또는** 위 HIGH_RISK_KEYWORDS 중 하나라도 텍스트에 포함.  
강제 포함 행은 greedy 전에 먼저 선발되며(risk_score 내림차순, 동점 시 원본 순서), max-cases 한도에 포함된다.

## Greedy 종료 조건

다음 중 하나가 되면 greedy 루프가 멈춘다:
1. 남은 후보가 없음
2. `max_cases` 한도 도달
3. `coverage_gain > 0`이면서 `score > 0`인 후보가 없음 (신규 태그를 추가하는 TC가 없거나, 있어도 실행 비용 대비 점수가 0 이하)

## Excluded 사유 3종 (+ forced-overflow)

| 사유 코드 | 설명 |
|-----------|------|
| 중복 | 선택된 TC가 동일 리스크를 이미 커버 (중복) |
| max-cases 도달 | max-cases=N 도달 |
| 점수 미달 | 점수 미달 (리스크 대비 실행 비용) |
| 강제 포함 대상 초과 | 강제 포함 대상이나 max-cases 초과로 제외 — 직접 검토 권장 (`강제 대상` 컬럼 = "Y") |

## Next Best 위치

Next Best는 **Excluded가 아니다**. 점수 상위 N개를 별도 시트로 추천하는 목록이므로,  
제외 사유·잔여 리스크 대신 점수와 추가 커버 태그를 기록한다.  
강제 포함 대상이 한도에 밀려 Next Best로 넘어온 행은 `강제 대상` 컬럼에 "Y"로 표시된다 (Excluded와 동일 규약).  
여유 시간이 생기면 Next Best 상위 항목부터 추가 실행을 권장한다.
