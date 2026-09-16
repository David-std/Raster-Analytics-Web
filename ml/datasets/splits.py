"""Ordered temporal partitions for leakage-safe evaluation."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date


def _parse_month(period_id: str) -> date:
    try:
        year_text, month_text = period_id.split("-", 1)
        return date(int(year_text), int(month_text), 1)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"invalid monthly period id: {period_id!r}") from exc


@dataclass(frozen=True)
class DateWindow:
    name: str
    start: str
    end: str

    def __post_init__(self) -> None:
        start = _parse_month(self.start)
        end = _parse_month(self.end)
        if start > end:
            raise ValueError(f"window {self.name}: start must not be after end")

    def contains(self, period_id: str) -> bool:
        period = _parse_month(period_id)
        return _parse_month(self.start) <= period <= _parse_month(self.end)


@dataclass(frozen=True)
class TemporalSplit:
    train: DateWindow
    validation: DateWindow
    test: DateWindow

    def __post_init__(self) -> None:
        if _parse_month(self.train.end) >= _parse_month(self.validation.start):
            raise ValueError("train and validation windows must be ordered and non-overlapping")
        if _parse_month(self.validation.end) >= _parse_month(self.test.start):
            raise ValueError("validation and test windows must be ordered and non-overlapping")

    def partition_for(self, period_id: str) -> str | None:
        if self.train.contains(period_id):
            return self.train.name
        if self.validation.contains(period_id):
            return self.validation.name
        if self.test.contains(period_id):
            return self.test.name
        return None

    @classmethod
    def current_fatal_outcome_split(cls) -> "TemporalSplit":
        return cls(
            train=DateWindow("train", "2021-01", "2022-12"),
            validation=DateWindow("validation", "2023-01", "2023-12"),
            test=DateWindow("test", "2024-01", "2024-12"),
        )
