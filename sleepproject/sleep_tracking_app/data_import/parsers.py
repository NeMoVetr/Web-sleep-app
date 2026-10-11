"""Parsers for supported sleep data formats."""

from os import PathLike

import pandas as pd

from .contracts import ParsedSleepData, ProgressCallback, SleepDataParser, ignore_progress


class CurrentCsvSleepParser(SleepDataParser):
    def parse(self, source: str | PathLike | pd.DataFrame,
              *, progress: ProgressCallback = ignore_progress) -> ParsedSleepData | None:
        from .csv import _extract_sleep_data

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
