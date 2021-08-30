from typing import Any, List

import ee  # type: ignore


class ClimatologyMean(ee.imagecollection.ImageCollection):
    """An image collection of climatological means.

    Must be instantiated through :code:`wxee.time_series.TimeSeries.mean_climatology`.

    Attributes
    ----------
    frequency : str
        The time frequency of the climatology. One of "day", "month".
    reducer : ee.Reducer
        The reducer used to aggregate the climatology.
    start : int
        The start coordinate in the time frequency included in the climatology, e.g. 1 for January if the
        frequency is "month".
    end : int
        The end coordinate in the time frequency included in the climatology, e.g. 8 for August if the
        frequency is "month".
    """

    def __init__(self, *args: Any) -> None:
        super().__init__(*args)


class _ClimatologyFrequency:
    """An internal class for storing and retrieving valid climatological frequency
    attributes.
    """

    options: List["_ClimatologyFrequency"] = []

    def __init__(self, name: str, date_format: str, start: int, end: int):
        self.name = name
        self.date_format = date_format
        self.start = start
        self.end = end
        self.options.append(self)

    @classmethod
    def option_names(cls) -> List[str]:
        """Get all valid names"""
        return [option.name for option in cls.options]

    @classmethod
    def get(cls, name: str) -> "_ClimatologyFrequency":
        """Retrieve a Frequency by name if it exists."""
        for option in cls.options:
            if option.name == name.lower():
                return option

        raise ValueError(f"Frequency must be in {cls.option_names()}, not '{name}'.")


_MONTH = _ClimatologyFrequency("month", "M", 1, 12)
_DAY = _ClimatologyFrequency("day", "D", 1, 366)
