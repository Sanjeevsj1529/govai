from __future__ import annotations


def grade_complaint(action: str, expected_department: str) -> float:
    return 0.99 if str(action).strip().lower() == expected_department.strip().lower() else 0.01
