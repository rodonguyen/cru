from dataclasses import dataclass
from datetime import date
from typing import Optional


@dataclass(frozen=True)
class Position:
    """Represents a job position like Supervisor, Welder, Fitter."""

    id: int
    name: str

    def __str__(self) -> str:
        return self.name


@dataclass(frozen=True)
class Worker:
    """Represents a worker assigned to a position."""

    id: int
    name: str
    position_id: int
    position_name: Optional[str] = None

    def __str__(self) -> str:
        if self.position_name:
            return f"{self.name} ({self.position_name})"
        return self.name


@dataclass(frozen=True)
class Task:
    """Represents a task with duration and date, assigned to a position."""

    id: int
    position_id: int
    duration: int  # Duration in hours
    date: str  # Date in YYYY-MM-DD format

    @property
    def date_obj(self) -> date:
        """Convert date string to date object."""
        year, month, day = map(int, self.date.split("-"))
        return date(year, month, day)

    def __str__(self) -> str:
        return f"Task {self.id} for position {self.position_id} on {self.date}"


@dataclass(frozen=True)
class Assignment:
    """Represents assignment of a task to a specific worker."""

    task_id: int
    worker_id: int

    def __str__(self) -> str:
        return f"Task {self.task_id} -> Worker {self.worker_id}"
