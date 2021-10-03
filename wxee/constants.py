from typing import Any, Callable, List

from wxee import interpolation

TMP_PREFIX = "wxee_tmp"


class _Frequency:
    """An internal class for storing and retrieving attributes for frequency units
    like day, hour, month, etc.
    """

    options: List["_Frequency"] = []

    def __init__(self, name: str):
        self.name = name
        self.options.append(self)


class _ClimatologyFrequency(_Frequency):
    """An internal class for storing and retrieving valid climatological frequency
    attributes. Unlike the base _Frequency class, climatology frequencies contain
    additional attributes used to set default climatology parameters.
    """

    def __init__(self, name: str, date_format: str, start: int, end: int):
        self.date_format = date_format
        self.start = start
        self.end = end
        super().__init__(name)


TIME_FREQUENCIES = {
    "year": _Frequency("year"),
    "month": _Frequency("month"),
    "week": _Frequency("week"),
    "day": _Frequency("day"),
    "hour": _Frequency("hour"),
    "minute": _Frequency("minute"),
}


CLIMATOLOGY_FREQUENCIES = {
    "month": _ClimatologyFrequency("month", "M", 1, 12),
    "day": _ClimatologyFrequency("day", "D", 1, 366),
}


INTERPOLATION_METHODS = {
    "nearest": interpolation.nearest,
    "linear": interpolation.linear,
    "cubic": interpolation.cubic,
}


def get_time_frequency(name: str) -> _Frequency:
    """Get a valid time frequency by name, e.g. hour."""
    return _get_option(name, TIME_FREQUENCIES, "Frequency")


def get_climatology_frequency(name: str) -> _ClimatologyFrequency:
    """Get a valid climatology frequency by name, e.g. month."""
    return _get_option(name, CLIMATOLOGY_FREQUENCIES, "Frequency")


def get_interpolation_method(name: str) -> Callable:
    """Get a valid interpolation method function by name, e.g. cubic."""
    return _get_option(name, INTERPOLATION_METHODS, "Method")


def _get_option(name: str, options: dict, label: str = "Option") -> Any:
    """Attempt to retrieve an value by name from a dictionary of options. If the
    name key is not in the dictionary, raise a helpful ValueError.
    """
    try:
        return options[name.lower()]
    except KeyError:
        raise ValueError(f"{label} must be in {sorted(options.keys())}, not '{name}'.")
