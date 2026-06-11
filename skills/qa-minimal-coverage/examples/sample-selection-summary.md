# 예시: qa:minimal-coverage 출력

이 파일은 LLM이 출력 톤·구조를 학습하는 few-shot. "라운지 선물하기" 탭(28 TC) 에서 `--max-cases 10` 옵션으로 실행한 결과 보고 모양.

---

## 최소 커버리지 선택 결과 — TabA (라운지 선물하기)

### 선택 요약

- **선택: 10 / 전체: 28**
- **커버된 리스크 태그:** 결제, 구매, 매치, 콜, remote-config, os:iOS, os:Android (7종)
- **출력 경로:** `/tmp/lounge-gift-minimal.xlsx`

```
Selected  3 / 28 TC   ← P1 강제 포함 2건 + 고위험 키워드 강제 포함 1건
Selected  7 / 28 TC   ← greedy 커버 확대 (신규 태그 추가)
------------------------------------------------------------------
Total:   10 / 28 TC   (max-cases=10 도달)
```

### 커버된 리스크 태그 (Coverage Summary)

| 리스크 태그     | 커버 TC 수 |
|----------------|-----------|
| 결제            | 3         |
| 구매            | 2         |
| 매치            | 4         |
| 콜              | 2         |
| remote-config   | 2         |
| os:iOS          | 5         |
| os:Android      | 4         |

### 잔여 리스크 경고

> **주의:** Excluded TC 중 `결제·환불` 키워드가 포함된 2건이 Blocker 영역에 해당합니다.  
> `next_best_count` 상위 1번 항목(TC_ID: SH-15)은 환불 예외 케이스로, 시간 여유가 있으면 우선 추가 실행을 권장합니다.

### Next Best 제안 (상위 2건)

| 순위 | TC_ID | Test Summary           | 추가 커버 태그 | 점수  |
|------|-------|------------------------|---------------|-------|
| 1    | SH-15 | 선물 결제 후 환불 처리   | 환불           | 2.10  |
| 2    | SH-22 | 구독 선물 만료 경계 케이스 | 구독          | 1.85  |

여유 시간이 생기면 Next Best 순서대로 추가 실행하면 커버리지가 확대됩니다.

### Forced-Overflow 경고

> **강제 포함 대상 1건 제외 (max-cases 초과):**  
> TC_ID `SH-07` (P1, 매치 콜 실패 복구) — max-cases=10 한도 도달로 선택에서 밀렸습니다.  
> Excluded 시트의 `강제 대상` 컬럼이 "Y"로 표시됩니다. 직접 실행 여부를 검토하세요.

### 가정 (Assumptions)

- `score = risk_score + coverage_gain - execution_cost - redundancy_penalty`
- 강제 포함: Priority P1 또는 고위험 키워드 (결제·신고·매치·콜·권한·Remote Config 등)
- `max-cases=10` 제한으로 강제 포함 대상 1건 제외 — 잔여 리스크 확인 필요
