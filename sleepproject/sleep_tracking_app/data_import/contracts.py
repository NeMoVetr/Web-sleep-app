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
