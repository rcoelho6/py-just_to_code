from __future__ import annotations

from dataclasses import dataclass


class TaskValidationError(ValueError):
    """Raised when task data violates a domain invariant."""


@dataclass(frozen=True, slots=True)
class Task:
    description: str
    priority: int
    id: int | None = None

    def __post_init__(self) -> None:
        if self.id is not None and self.id <= 0:
            raise TaskValidationError("Id cannot be null or less than or equals 0")
        if not isinstance(self.description, str) or not self.description.strip():
            raise TaskValidationError("Description cannot be null or blank")
        if isinstance(self.priority, bool) or not isinstance(self.priority, int) or self.priority < 0:
            raise TaskValidationError("Priority cannot be null or negative")
