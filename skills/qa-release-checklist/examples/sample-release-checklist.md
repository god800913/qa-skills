# 예시: qa:release-checklist 출력

이 파일은 LLM이 출력 톤·구조를 학습하는 few-shot. "라운지 선물하기" 기능 릴리즈를 동일 가상 기능의 시점 차이로 3가지 판정(blocked → conditional → ready)을 보여준다.

---

## 사례 A — 판정: blocked

> 시점: QA 1차 사이클 완료 직후. 결제 이중 차감 Blocker 발견.

### 릴리즈 판정 — 라운지 선물하기 v1.0.0

**판정: BLOCKED**
결제 이중 차감(BUG-1042, Blocker)이 미결 상태. 수정·검증 완료 전 릴리즈 불가.

### 게이트 점검표

| # | 게이트 | 결과 | 근거 |
|---|--------|------|------|
| G1 | Blocker 결함 0건 | **실패** | BUG-1042 (결제 이중 차감) — Open 상태. 재현 100%. |
| G2 | Major 결함 해결 또는 risk-accept 서명 | 통과 | Major 2건 모두 Fix verified. |
| G3 | known issue 문서화 + CS 공유 | 확인 불가 | known issue 문서 링크 미제공. |
| G4 | rollout 계획 수립 | 통과 | 5% → 30% → 100% 단계 문서 확인. |
| G5 | rollback 절차 확보 | 통과 | 크래시율 2% 초과 시 즉시 롤백 — 담당자 명시. |
| G6 | 모니터링 준비 | 확인 불가 | 알람 임계값 설정 여부 미확인. |
| G7 | owner sign-off | 실패 | 개발 책임자 미서명. QA·PM 서명만 확인. |

### Blocker 조건
- BUG-1042 Fix + Regression 검증 완료 후 재점검 필수.
- G6(모니터링), G7(개발 sign-off) 정보 보완 요.

### 잔여 known issue
없음 (1차 사이클 기준).

---

## 사례 B — 판정: conditional

> 시점: BUG-1042 수정 완료 후 재테스트. iOS 권한 이슈(BUG-1055, Major) risk-accept 검토 중.

### 릴리즈 판정 — 라운지 선물하기 v1.0.1

**판정: CONDITIONAL**
Blocker 소거 완료. iOS 권한 거부 시 크래시(BUG-1055, Major)에 대해 PM risk-accept 서명 대기 중.

릴리즈 조건:
1. BUG-1055에 대한 PM·개발 책임자 risk-accept 서명(날짜·사유 포함) 확보.
2. known issue로 BUG-1055 CS 공유 완료 확인.

### 게이트 점검표

| # | 게이트 | 결과 | 근거 |
|---|--------|------|------|
| G1 | Blocker 결함 0건 | **통과** | BUG-1042 Fix verified (2026-06-09). |
| G2 | Major 결함 해결 또는 risk-accept 서명 | **실패** | BUG-1055 (iOS 권한 거부 크래시) — risk-accept 서명 미확보. |
| G3 | known issue 문서화 + CS 공유 | **실패** | BUG-1055 CS 공유 미완료 (내일 예정). |
| G4 | rollout 계획 수립 | 통과 | 5% → 30% → 100% 단계 문서 확인. |
| G5 | rollback 절차 확보 | 통과 | 크래시율 2% 초과 시 즉시 롤백 — 담당자 명시. |
| G6 | 모니터링 준비 | 통과 | Datadog 알람 — 결제 성공률 95% 미만, 크래시율 2% 초과 설정 확인. |
| G7 | owner sign-off | **실패** | PM·QA 서명 완료. 개발 책임자 서명 대기 중. |

### rollout / rollback 체크
- rollout: 5%(2026-06-12) → 30%(2026-06-14) → 100%(2026-06-17) — Remote Config `enableLoungeGift` 기본값 off 확인.
- rollback: 크래시율 2% 초과 또는 결제 성공률 95% 미만 → 플래그 즉시 off. 담당 개발자: 홍길동(010-xxxx-xxxx).

### 잔여 known issue
| ID | 내용 | 심각도 | CS 공유 |
|----|------|--------|---------|
| BUG-1055 | iOS 마이크 권한 거부 후 선물 수신 콜 진입 시 크래시 | Major | 미완료 (내일 예정) |

---

## 사례 C — 판정: ready

> 시점: risk-accept 서명 + CS 공유 완료. 전 게이트 통과.

### 릴리즈 판정 — 라운지 선물하기 v1.0.1

**판정: READY**
7개 게이트 전부 통과. 릴리즈 승인.

### 게이트 점검표

| # | 게이트 | 결과 | 근거 |
|---|--------|------|------|
| G1 | Blocker 결함 0건 | 통과 | BUG-1042 Fix verified (2026-06-09). |
| G2 | Major 결함 해결 또는 risk-accept 서명 | 통과 | BUG-1055 risk-accept 서명 확보 (PM 김철수 2026-06-10, 개발 홍길동 2026-06-10). |
| G3 | known issue 문서화 + CS 공유 | 통과 | BUG-1055 known issue 문서 등록 + CS팀 공유 완료 (2026-06-10). |
| G4 | rollout 계획 수립 | 통과 | 5% → 30% → 100% 단계 문서 확인. Remote Config 기본값 off 확인. |
| G5 | rollback 절차 확보 | 통과 | 크래시율 2% 초과 또는 결제 성공률 95% 미만 → 플래그 즉시 off. 담당자 명시. |
| G6 | 모니터링 준비 | 통과 | Datadog 알람 2종 설정 완료. 릴리즈 당일 QA 온콜 배정. |
| G7 | owner sign-off | 통과 | QA 리드·PM·개발 책임자 3자 서명 완료 (2026-06-10). |

### rollout / rollback 체크
- rollout: 5%(2026-06-12) → 30%(2026-06-14) → 100%(2026-06-17).
- rollback: 크래시율 2% 초과 또는 결제 성공률 95% 미만 → 즉시 플래그 off. 담당 개발자: 홍길동(010-xxxx-xxxx).

### 잔여 known issue
| ID | 내용 | 심각도 | CS 공유 |
|----|------|--------|---------|
| BUG-1055 | iOS 마이크 권한 거부 후 선물 수신 콜 진입 시 크래시 | Major | 완료 (2026-06-10) |
