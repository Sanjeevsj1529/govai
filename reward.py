from __future__ import annotations

from dataclasses import dataclass


@dataclass(slots=True)
class RewardBreakdown:
    completion: int = 0
    early_completion: int = 0
    progress: int = 0
    idle: int = 0
    delay: int = 0
    repeated_bad_decision: int = 0

    def total(self) -> int:
        return (
            self.completion * 10
            + self.early_completion * 5
            + self.progress
            - self.idle * 5
            - self.delay * 10
            - self.repeated_bad_decision * 20
        )

    def reason(self) -> str:
        parts: list[str] = []
        if self.completion:
            parts.append(f"+{self.completion * 10} completion")
        if self.early_completion:
            parts.append(f"+{self.early_completion * 5} early completion")
        if self.progress:
            parts.append(f"+{self.progress} progress")
        if self.idle:
            parts.append(f"-{self.idle * 5} idle employees")
        if self.delay:
            parts.append(f"-{self.delay * 10} delays")
        if self.repeated_bad_decision:
            parts.append(f"-{self.repeated_bad_decision * 20} repeated bad decisions")
        return ", ".join(parts) if parts else "No meaningful change this step."

    def as_dict(self) -> dict[str, int | str]:
        return {
            "completion": self.completion,
            "early_completion": self.early_completion,
            "progress": self.progress,
            "idle": self.idle,
            "delay": self.delay,
            "repeated_bad_decision": self.repeated_bad_decision,
            "reason": self.reason(),
            "total": self.total(),
        }


def calculate_reward(breakdown: RewardBreakdown) -> int:
    return breakdown.total()
