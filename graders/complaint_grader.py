from __future__ import annotations


def grade_complaint(action: str, expected_department: str) -> float:
    return 1.0 if str(action).strip().lower() == expected_department.strip().lower() else 0.0
