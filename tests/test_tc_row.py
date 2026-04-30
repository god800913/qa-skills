"""Tests for shared/tc_row.py."""
import pytest

from shared.tc_row import validate_row


class TestValidateRow:
    def test_valid_row_no_errors(self):
        row = {
            "Priority": "P1",
            "OS": "All",
            "Automation Check": "All",
            "Test Summary": "라운지 진입",
            "Pre-condition": "...",
            "Test Step": "1. 앱 실행",
            "Expected Result": "라운지 노출",
        }
        assert validate_row(row) == []

    def test_missing_required_key(self):
        row = {"Priority": "P1"}
        errors = validate_row(row, source_label="row 5")
        # Should report missing Test Summary, Pre-condition, Test Step, Expected Result
        assert any("Test Summary" in e for e in errors)
        assert any("Pre-condition" in e for e in errors)
        assert all("row 5" in e for e in errors)

    def test_invalid_priority(self):
        row = {
            "Priority": "PX",
            "Test Summary": "x", "Pre-condition": "x",
            "Test Step": "x", "Expected Result": "x",
        }
        errors = validate_row(row)
        assert any("Priority" in e for e in errors)

    def test_blank_os_is_valid(self):
        row = {
            "Priority": "P1", "OS": "",
            "Test Summary": "x", "Pre-condition": "x",
            "Test Step": "x", "Expected Result": "x",
        }
        assert validate_row(row) == []
