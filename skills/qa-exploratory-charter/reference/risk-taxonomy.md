# 리스크 분류 체계 (risk taxonomy)

qa-risk-analysis · qa-regression-scope · qa-minimal-coverage · qa-exploratory-charter가 공유하는 분류. 영역별로 "무엇이 깨지면 어떤 피해인가"를 기준으로 영향도를 매긴다.

| 영역 | 대표 키워드 | 기본 영향도 | 비고 |
|---|---|---|---|
| 핵심 사용자 플로우 | 온보딩, 메인 진입, 매치 시작 | Blocker | 깨지면 서비스 사용 불가 |
| 결제·수익화 | 결제, 구매, 환불, 구독, 젬 | Blocker | 금전 피해·CS 폭증 |
| 매치·콜·실시간 | 매치, 콜, 라이브, 메시지, 영상 | Blocker~Major | 코어 가치. 양방향(mutual) 검증 필요 |
| 신고·차단·모더레이션 | 신고, 차단, 제재, 블라인드 | Blocker~Major | 안전·법적 리스크 |
| 인증·권한·프라이버시 | 로그인, 탈퇴, 권한, 개인정보 | Major | 데이터 유출·계정 피해 |
| Remote Config·롤아웃·실험 | remote config, 플래그, 실험, 어드민 | Major | on/off 양쪽 + 기본값 검증 |
| 크로스플랫폼·OS 분기 | iOS, Android, 버전 분기 | Major~Minor | 한쪽만 깨지는 회귀 빈발 |
| 마이그레이션·하위호환 | 마이그레이션, 구버전, 업그레이드 | Major | 기존 사용자 데이터 보존 |
| UI·카피 | 라벨, 문구, 정렬, 다크모드 | Minor | 기능 영향 없으면 Minor |

## 발생가능성 판단 힌트
- 이번 릴리즈에서 **변경된 코드 경로**에 가까울수록 높음.
- 상태 조합이 많을수록(로그인 상태 × OS × 플래그) 높음.
- 외부 의존(결제 모듈, 네트워크 품질)이 있으면 높음.

## 등급 = 영향도 × 발생가능성
- Blocker: 출시 차단. 즉시 보고.
- Major: 출시 전 수정 또는 명시적 risk-accept 필요.
- Minor: known issue로 출시 가능.
- Info: 관찰만.
