"""Generate tests/fixtures/sample_tc_executed.xlsx (Result column filled)."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "shared"))
from new_workbook import write_workbook  # noqa: E402

RESULTS = ["Pass", "Pass", "pass", "Pass", "Fail", "Block", "N/T", "성공", "N/A", ""]
JIRA = {4: "JIRA-2202", 5: "JIRA-2203"}

rows = [
    {"section": "1. 실행 샘플", "Priority": "P2", "Test Item": "실행 샘플",
     "Test Summary": f"샘플 케이스 {i + 1}", "Test Step": "1. 실행",
     "Expected Result": "정상", "Result": result, "Jira no.": JIRA.get(i, "")}
    for i, result in enumerate(RESULTS)
]
out = Path(__file__).parent.parent / "tests" / "fixtures" / "sample_tc_executed.xlsx"
out.unlink(missing_ok=True)  # write_workbook은 충돌 시 (2) 접미사를 붙이므로 재생성 시 선삭제
actual = write_workbook(rows, "TabExec", out)
print(actual)
