# 예시: qa:automation-candidates 출력

이 파일은 LLM이 출력 톤·구조를 학습하는 few-shot. "라운지 선물하기" 탭 TC 12건을 입력으로 받았을 때 기대되는 자동화 후보 리포트.

---

## 자동화 후보 — 라운지 선물하기 탭 (ver118)

**입력**: `master_tc.xlsx` 탭 `Lounge-Gift` (TC 12건) + `qa:test-result-report` 출력 md (ver117 실행 이력)

### 요약

후보 **5건** 추출 / 제외 7건 (Skip 4 · 이미 자동화 1 · 분류 미정 2) — P1·P2 결제·진입 플로우 중심으로 자동화 효과 높음.

### 우선순위

| 순위 | TC_ID | Test Summary | Automation Check | 근거 | 비고 |
|---|---|---|---|---|---|
| 1 | Lounge-1 | `enableLoungeGift` ON 시 선물하기 버튼 노출 | All | P1·반복 빈도 높음 / RC 셋업 필요(수동 비용 높음) / Expected Result 결정론적(버튼 노출 여부) / 이력 Pass 안정 | |
| 2 | Lounge-2 | `enableLoungeGift` OFF 시 선물하기 버튼 미노출 | All | P1·플래그 off 경계 검증 / RC 셋업 쌍 — 1과 묶어 자동화 효율 극대화 / 결정론적 | |
| 3 | Lounge-4 | 젬 잔액 충분 시 선물 발송 성공 | All | P1·결제 핵심 플로우 / Test Step 6줄(수동 비용 높음) / Expected Result(발송 완료 토스트·수신 알림) 결정론적 | |
| 4 | Lounge-5 | 선물 수신 확인 화면 정상 진입 | iOS | P2·수신 UX 커버 / Step 4줄 / 결정론적 / 이력 Pass | |
| 5 | Lounge-7 | 젬 잔액 부족 시 구매 유도 팝업 노출 | All | P2·결제 방어 분기 / Expected Result 결정론적(팝업 문구) / 단순 단계 |  안정화 후 전환 — ver117 이력 Fail 2회(팝업 렌더 타이밍 불안정) |

### 분류 미정 / 제외 요약

**분류 미정 (Automation Check 공란) — 2건**

| TC_ID | Test Summary | 권장 액션 |
|---|---|---|
| Lounge-10 | 선물 발송 중 네트워크 끊김 후 재시도 | 타이밍 의존 — flaky 위험 있어 PM·개발과 협의 후 Skip 또는 All 지정 |
| Lounge-11 | 빠른 연타로 선물 중복 발송 시도 | 동시성 TC — 자동화 적합성 판단 후 분류 필요 |

**제외 요약 — 7건**

| 분류 | 건수 | 대표 TC_ID | 사유 |
|---|---|---|---|
| Skip | 4 | Lounge-3, 6, 8, 9 | iOS 권한·매치 타이밍·실시간 추천 — 자동화 불가 또는 플랫폼 제약 |
| 이미 자동화 | 1 | Lounge-12 | `Automation TC_ID` = `AUTO-L-012` 존재 — 이미 스위트에 편입됨 |

---

다음 액션: 이 목록을 자동화 팀과 공유하고, 전환 확정되면 마스터의 `Automation TC_ID` 컬럼을 채우세요 (다음 실행부터 후보에서 자동 제외됩니다).
