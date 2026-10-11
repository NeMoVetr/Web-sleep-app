"""Format-independent sleep import contracts."""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from os import PathLike
from typing import Callable

import pandas as pd


ProgressCallback = Callable[[int, int, str], None]


def ignore_progress(current: int, total: int, description: str = "") -> None:
    """Default progress callback for imports outside Celery."""


@dataclass(frozen=True)
class ParsedSleepData:
    records: pd.DataFrame
    segments: pd.DataFrame
    heart_rates: pd.DataFrame


class SleepDataParser(ABC):
    @abstractmethod
    def parse(self, source: str | PathLike | pd.DataFrame,
              *, progress: ProgressCallback = ignore_progress) -> ParsedSleepData | None:
        """Return normalized data, or None for an unsupported file."""
        raise NotImplementedError


class CurrentCsvSleepParser(SleepDataParser):
    def parse(self, source: str | PathLike | pd.DataFrame,
              *, progress: ProgressCallback = ignore_progress) -> ParsedSleepData | None:
        from .csv_data_extraction import _extract_sleep_data

        frame = source if isinstance(source, pd.DataFrame) else pd.read_csv(source, encoding="utf-8")
        result = _extract_sleep_data(frame, progress)
        if result is None:
            return None
        records, segments, heart_rates = result
        for data in (records, segments, heart_rates):
            data.index = pd.to_datetime(data.index, utc=True)
        for data, columns in (
            (records, ("device_bedtime", "device_wake_up_time", "bedtime", "wake_up_time")),
            (segments, ("start_time", "end_time")),
        ):
            for column in columns:
                if column in data.columns:
                    data[column] = pd.to_datetime(data[column], utc=True)
        return ParsedSleepData(records, segments, heart_rates)
