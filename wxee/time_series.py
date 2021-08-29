from typing import Any, Optional, Union

import ee  # type: ignore

from wxee.climatology import ClimatologyMean, _ClimatologyFrequency


class TimeSeries(ee.imagecollection.ImageCollection):
    """An image collection of chronological images."""

    def __init__(self, *args: Any) -> None:
        super().__init__(*args)

    def _get_times(self) -> ee.List:
        """Return the the :code:`system:time_start` of each image in the collection"""
        imgs = self.toList(self.size())
        return imgs.map(lambda img: ee.Image(img).get("system:time_start"))

    @property
    def start_time(self) -> ee.Date:
        """The :code:`system:time_start` of first chronological image in the collection.

        Returns
        -------
        ee.Date
            The start time of the collection.
        """
        times = self._get_times()
        return ee.Date(times.reduce(ee.Reducer.min()))

    @property
    def end_time(self) -> ee.Date:
        """The :code:`system:time_start` of last chronological image in the collection.

        Returns
        -------
        ee.Date
            The end time of the collection.
        """
        times = self._get_times()
        return ee.Date(times.reduce(ee.Reducer.max()))

    def aggregate_time(
        self, frequency: str, reducer: Optional[Any] = None, keep_bandnames: bool = True
    ) -> ee.ImageCollection:
        """Aggregate the collection over the time dimension to a specified frequency. This method can only be used to go from
        small time frequencies to larger time frequencies, such as hours to days, not vice-versa. If the resampling frequency is smaller
        than the time between images, un-aggregated images will be returned.

        Parameters
        ----------
        frequency : str
            The time frequency to aggregate to. One of 'year', 'month' 'week', 'day', 'hour'.
        reducer : ee.Reducer, optional
            The reducer to apply when aggregating over time. If none is provided, ee.Reducer.mean() will be used.
        keep_bandnames : bool, default True
            If true, the band names of the input images will be kept in the aggregated images. If false, the name of the
            reducer will be appended to the band names, e.g. SR_B4 will become SR_B4_mean.

        Returns
        -------
        ee.ImageCollection
            The input image collection aggregated to the specified time frequency.

        Raises
        ------
        ValueError
            If an invalid frequency is passed.

        Example
        -------
        >>> ts_hourly = wxee.TimeSeries("NOAA/NWS/RTMA")
        >>> daily_max = ts_hourly.aggregate_time(frequency="day", reducer=ee.Reducer.max())
        """
        # ee.Reducer can't be used without initializing ee (see https://github.com/google/earthengine-api/issues/164),
        # so set the default reducer explicitly. This is also why the type hint above is set to Any.
        reducer = ee.Reducer.mean() if not reducer else reducer

        frequencies = ["year", "month", "week", "day", "hour"]
        if frequency.lower() not in frequencies:
            raise ValueError(
                f"Frequency must be one of {frequencies}, not '{frequency.lower()}''."
            )

        def resample_step(start: ee.Date) -> ee.Image:
            """Resample one time step in the given unit from a specified start time."""
            start = ee.Date(start)
            end = start.advance(1, frequency)
            imgs = self.filterDate(start, end)
            resampled = imgs.reduce(reducer)
            resampled = resampled.copyProperties(
                imgs.first(), imgs.first().propertyNames()
            )
            resampled = resampled.set(
                {
                    "system:time_start": imgs.first().get("system:time_start"),
                    "system:time_end": imgs.wx.last().get("system:time_end"),
                }
            )

            if keep_bandnames:
                resampled = ee.Image(resampled).rename(imgs.first().bandNames())

            # If the resampling step falls between images, just return null
            return ee.Algorithms.If(imgs.size().gt(0), resampled, None)

        n_steps = self.end_time.difference(self.start_time, frequency).ceil()
        steps = ee.List.sequence(0, n_steps.subtract(1))
        start_times = steps.map(lambda x: self.start_time.advance(x, frequency))

        resampled = ee.ImageCollection(start_times.map(resample_step, dropNulls=True))

        return resampled

    def climatology_mean(
        self,
        frequency: str,
        reducer: Optional[Any] = None,
        start: Optional[int] = None,
        end: Optional[int] = None,
        keep_bandnames: bool = True,
    ) -> ClimatologyMean:
        """Calculate a mean climatology image collection with a given frequency.

        Parameters
        ----------
        frequency : str
            The name of the time frequency. One of "day", "month".
        reducer : Optional[ee.Reducer]
            The reducer to apply when aggregating over time, e.g. aggregating hourly data to daily for a daily
            climatology. If the data is already in the temporal scale of the climatology, e.g. creating a daily
            climatology from daily data, the reducer will have no effect.
        start : Optional[int]
            The start coordinate in the time frequency to include in the climatology, e.g. 1 for January if the
            frequency is "month". If none is provided, the default will be 1 for both "day" and "month".
        end : Optional[int]
            The end coordinate in the time frequency to include in the climatology, e.g. 8 for August if the
            frequency is "month". If none is provided, the default will be 366 for "day" or 12 for "month"
        keep_bandnames : bool, default True
            If true, the band names of the input images will be kept in the aggregated images. If false, the name of the
            reducer will be appended to the band names, e.g. SR_B4 will become SR_B4_mean.

        Returns
        -------
        wxee.climatology.ClimatologyMean
            The climatological mean collection.

        Example
        -------
        >>> collection = ee.ImageCollection("IDAHO_EPSCOR/GRIDMET")
        >>> collection = collection.filterDate("1980", "2000")
        >>> ts = wxee.TimeSeries(collection)
        >>> daily_max = ts.climatology_mean(frequency="day", reducer=ee.Reducer.max())
        >>> daily_max.size().getInfo()
        366
        """
        reducer = ee.Reducer.mean() if not reducer else reducer

        freq = _ClimatologyFrequency.get(frequency)
        start = freq.start if not start else start
        end = freq.end if not end else end
        prop = f"wx:{frequency}"

        def reduce_frequency(x: ee.String) -> Union[None, ee.Image]:
            """Apply a mean reducer over a time frequency, returning None if no images fall within the time window.

            Parameters
            ----------
            x : ee.String
                The time coordinate to reduce, such as "1" for January.
            """
            imgs = collection.filterMetadata(prop, "equals", x)
            reduced = imgs.reduce(ee.Reducer.mean())
            # Retrieve the time from the image instead of using x because I need a formatted
            # string for concatenating into the system:id later.
            coord = ee.Date(imgs.first().get("system:time_start")).format(
                freq.date_format
            )
            reduced = reduced.set("wx:dimension", frequency, "wx:coordinate", coord)
            # Reducing makes images unbounded which causes issues
            reduced = reduced.clip(collection.geometry().bounds())

            if keep_bandnames:
                reduced = ee.Image(reduced).rename(imgs.first().bandNames())

            return ee.Algorithms.If(imgs.size().gt(0), reduced, None)

        collection = self.aggregate_time(freq.name, reducer, keep_bandnames)
        collection = collection.map(
            lambda img: img.set(
                prop,
                ee.Number.parse(
                    ee.Date(ee.Image(img).get("system:time_start")).format(
                        freq.date_format
                    )
                ),
            )
        )
        coord_list = ee.List.sequence(start, end)

        clim = ClimatologyMean(
            coord_list.map(lambda x: reduce_frequency(x), dropNulls=True)
        )

        clim.frequency = freq.name
        clim.start = start
        clim.end = end

        return clim
