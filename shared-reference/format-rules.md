# 포맷 규칙 (qa:review-tc 카테고리 A)

`validate_format.py`가 자동 검출하는 결정론적 위반 항목.

## 필수 컬럼 (missing_required)
다음 컬럼이 비어있으면 위반:
- Priority
- Test Summary
- Pre-condition
- Test Step
- Expected Result

## Enum 위반 (invalid_enum)

| 컬럼 | 허용 값 |
|---|---|
| Priority | P1, P2, P3, P4 |
| OS | iOS, And, Android, All, "" (공란) |
| Automation Check | All, iOS, Android, Skip, "" (공란) |

## TC_ID 중복 (duplicate_tc_id)
같은 탭 내에서 동일한 TC_ID가 두 번 이상 등장하면 위반.
자동 패치 가능 (`--patch`): 두 번째 이후 ID에 `-dup-N` 접미사 부여.

## 자동 패치 가능 여부

| 카테고리 | 자동 패치 |
|---|---|
| missing_required | 불가 (사람 판단) |
| invalid_enum | 불가 (사람 판단) |
| duplicate_tc_id | 가능 |

## 심각도 매핑
- 필수 컬럼 누락 → Major
- Priority enum 위반 → Major
- OS / Automation Check enum 위반 → Minor
- TC_ID 중복 → Major
