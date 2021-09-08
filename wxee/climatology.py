from typing import Any

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
