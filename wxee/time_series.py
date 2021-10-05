from typing import Any, List, Optional, Union

import ee  # type: ignore

from wxee.climatology import Climatology
from wxee.constants import (
    get_climatology_frequency,
    get_interpolation_method,
    get_time_frequency,
)
from wxee.utils import _normalize


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

    def interval(self, unit: str = "day", reducer: Optional[Any] = None) -> ee.Number:
        """Compute and reduce time intervals between images in the collection. By default, the mean interval will be returned,
        but you could also calculate the minimum or maximum time between images, for example.

        Parameters
        ----------
        unit : str, default "day"
            The unit to return the time interval in. One of "minute", "hour", "day", "week", "month", "year".

        reducer : ee.Reducer, optional
            The reducer to apply to the list of image intervals. If none is provided, ee.Reducer.mean() will be used.

        Returns
        -------
        ee.Number
            The reduced time interval between images.

        Warning
        -------
        Calculating the interval of very large collections may exceed memory limits. If this happens, try selecting only
        a portion of the collection dates.

        Example
        -------
        >>> ts = wxee.TimeSeries("COPERNICUS/S2_SR")
        >>> imgs = ts.filterBounds(ee.Geometry.Point([-105.787, 38.753]))
        >>> imgs.interval("day").getInfo()
        5.03
        """

        def iterate_diffs(time: ee.Date, old_diffs: ee.List) -> ee.List:
            """Iterate through one step, calculating the time interval between two images and adding it to the working list."""
            old_diffs = ee.List(old_diffs)
            last_idx = old_diffs.size().subtract(1)
            last_time = times.get(last_idx)
            diff = ee.Date(time).difference(last_time, unit=unit)
            return old_diffs.add(diff)

        reducer = ee.Reducer.mean() if not reducer else reducer

        times = self._get_times()
        diffs = ee.List(times.iterate(iterate_diffs, ee.List([]))).slice(1)

        return diffs.reduce(reducer)

    def describe(self, unit: str = "day") -> None:
        """Generate and print descriptive statistics about the Time Series such as the ID, start and end dates, and time between images.
        This requires pulling data from the server, so it may run slowly.

        Parameters
        ----------
        unit : str, default "day"
            The unit to return the time interval in. One of "second", "minute", "hour", "day", "week", "month", "year".

        Returns
        -------
        None
        """

        start = self.start_time.format("yyyy-MM-dd HH:mm:ss z").getInfo()
        end = self.end_time.format("yyyy-MM-dd HH:mm:ss z").getInfo()
        mean_interval = self.interval(unit).getInfo()
        size = self.size().getInfo()
        id = self.get("system:id").getInfo()

        print(
            f"\033[1m{id}\033[0m"
            f"\n\tImages: {size}"
            f"\n\tStart date: {start}"
            f"\n\tEnd date: {end}"
            f"\n\tMean interval: {mean_interval:.2f} {unit}s"
        )

    def aggregate_time(
        self, frequency: str, reducer: Optional[Any] = None, keep_bandnames: bool = True
    ) -> "TimeSeries":
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
        TimeSeries
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
        original_id = self.get("system:id")

        get_time_frequency(frequency)

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

        start_times = self._generate_steps_at_frequency(frequency)

        return TimeSeries(start_times.map(resample_step, dropNulls=True)).set(
            "system:id", original_id
        )

    def _generate_steps_at_frequency(self, frequency: str) -> "ee.List[ee.Date]":
        """Generate a list of start dates that would split the time series into a given frequency. For example, a time series of daily
        data at monthly frequency would return the start date of monthly periods starting from the first day.

        In the example above, this is done by calculating the number of months that cover the time series and iteratively advancing
        that many steps from the start time of the time series. This means that if the time series does not start on the first day of
        a month, the steps will not line up with calendar months but will instead represent month-long groups of contiguous days.

        A minimum of 1 step will be returned even if the time series period is smaller than the frequency.
        """
        get_time_frequency(frequency)

        n_steps = self.end_time.difference(self.start_time, frequency).floor()
        steps = ee.List.sequence(0, n_steps)

        return steps.map(lambda x: self.start_time.advance(x, frequency))

    def _calculate_climatology(
        self,
        climatology_reducer: Optional[Any],
        frequency: str,
        reducer: Optional[Any] = None,
        start: Optional[int] = None,
        end: Optional[int] = None,
        keep_bandnames: bool = True,
    ) -> Climatology:
        """Calculate a climatology image collection with a given frequency and reducer.

        Parameters
        ----------
        climatology_reducer: Optional[ee.Reducer]
            The climatological reducer to apply to aggregated images. In most cases, this will be ee.Reducer.mean
            or ee.Reducer.stdDev for generating climatological means and standard deviations, respectively.
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
        wxee.climatology.Climatology
            The climatological collection.
        """
        reducer = ee.Reducer.mean() if not reducer else reducer

        freq = get_climatology_frequency(frequency)
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
            reduced = imgs.reduce(climatology_reducer)
            # Retrieve the time from the image instead of using x because I need a formatted
            # string for concatenating into the system:id later.
            coord = ee.Date(imgs.first().get("system:time_start")).format(
                freq.date_format
            )
            reduced = reduced.set("wx:dimension", frequency, "wx:coordinate", coord)

            geom = collection.geometry()
            # Reducing makes images unbounded, so re-clip bounded images
            reduced = ee.Algorithms.If(geom.isUnbounded(), reduced, reduced.clip(geom))

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

        clim = Climatology(
            coord_list.map(lambda x: reduce_frequency(x), dropNulls=True)
        )

        clim = clim.set("system:id", self.get("system:id"))
        clim.frequency = freq
        clim.start = start
        clim.end = end
        clim.reducer = reducer

        return clim

    def climatology_mean(
        self,
        frequency: str,
        reducer: Optional[Any] = None,
        start: Optional[int] = None,
        end: Optional[int] = None,
        keep_bandnames: bool = True,
    ) -> Climatology:
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
        wxee.climatology.Climatology
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
        mean_clim = self._calculate_climatology(
            ee.Reducer.mean(), frequency, reducer, start, end, keep_bandnames
        )
        mean_clim.statistic = "mean"

        return mean_clim

    def climatology_std(
        self,
        frequency: str,
        reducer: Optional[Any] = None,
        start: Optional[int] = None,
        end: Optional[int] = None,
        keep_bandnames: bool = True,
    ) -> Climatology:
        """Calculate a standard deviation climatology image collection with a given frequency.

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
            reducer will be appended to the band names, e.g. SR_B4 will become SR_B4_stdDev.

        Returns
        -------
        wxee.climatology.Climatology
            The climatological standard deviation collection.

        Example
        -------
        >>> collection = ee.ImageCollection("IDAHO_EPSCOR/GRIDMET")
        >>> collection = collection.filterDate("1980", "2000")
        >>> ts = wxee.TimeSeries(collection)
        >>> daily_max = ts.climatology_std(frequency="day", reducer=ee.Reducer.max())
        >>> daily_max.size().getInfo()
        366
        """
        mean_clim = self._calculate_climatology(
            ee.Reducer.stdDev(), frequency, reducer, start, end, keep_bandnames
        )
        mean_clim.statistic = "standard deviation"

        return mean_clim

    def climatology_anomaly(
        self,
        mean: Climatology,
        std: Optional[Climatology] = None,
        keep_bandnames: bool = True,
    ) -> "TimeSeries":
        """Calculate climatological anomalies for the time series. The frequency and reducer will be the same as those
                used in the :code:`mean` climatology. Standardized anomalies can be calculated by providing a climatological standard
                deviation as :code:`std`.

                A climatological anomaly is calculated as the difference between the climatological mean and a given observation.
                For standardized anomalies, that difference is divided by the climatological standard deviation. Standardized
                anomalies represent unitless measurements of how many standard deviations an observation was from the climatological
                mean, and therefore allow easy comparisons between variables.

                Note
                ----
                Climatological anomalies are generally calculated using long-term climatological normals (e.g. 30 years). If
                the climatological mean and standard deviation represent a shorter period, interpretation of results may vary.
        y1 and image y2.
                Parameters
                ----------
                mean : Climatology
                    The long-term climatological mean to calculate anomalies from. The climatological frequency and reducer will
                    be determined from this climatology.
                std : Optional[Climatology]
                    The long-term climatological standard deviation to calculate anomalies from. If provided, standardized
                    climatological anomalies will be calculated. The climatological standard deviation frequency and reducer must
                    match the frequency and reducer used by the climatological mean.
                keep_bandnames : bool, default True
                    If true, the band names of the input images will be kept in the aggregated images. If false, the name of the
                    reducer will be appended to the band names, e.g. SR_B4 will become SR_B4_mean.

                Returns
                -------
                wxee.time_series.TimeSeries
                    Climatological anomalies within the TimeSeries period.

                Raises
                ------
                ValueError
                    If the :code:`std` frequency or reducer do not match the :code:`mean` frequency or reducer. Only applies if
                    a :code:`std` is provided.

                Example
                -------
                >>> collection = wxee.TimeSeries("IDAHO_EPSCOR/GRIDMET")
                >>> reference = collection.filterDate("1980", "2010")
                >>> mean = reference.climatology_mean("month")
                >>> std = reference.climatology_std("month")
                >>> observation = collection.filterDate("2020", "2021")
                >>> anomaly = observation.climatology_anomaly(mean, std)
        """
        reducer = mean.reducer
        freq = mean.frequency

        if std:
            if std.frequency != freq:
                raise ValueError(
                    f"Mean frequency '{mean.frequency.name}' does not match std frequency '{std.frequency.name}'."
                )
            if std.reducer != mean.reducer:
                # There is no way to determine the type of reducer used after the fact, or else I would list them.
                raise ValueError(f"Mean reducer does not match std reducer.")

        def image_anomaly(img: ee.Image) -> ee.Image:
            """Identify the climatological mean and std deviation for a given image
            and use them to calculate and return the anomaly.
            """
            # Get the climatological coordinate of the image
            coord = ee.Date(ee.Image(img).get("system:time_start")).format(
                freq.date_format
            )

            # Get the climatological mean at that coordinate
            coord_mean = mean.filterMetadata("wx:coordinate", "equals", coord)

            anom = img.subtract(coord_mean.first())

            # If a standard deviation is provided, standardize the anomalies
            if std:
                coord_std = std.filterMetadata("wx:coordinate", "equals", coord)
                anom = anom.divide(coord_std.first())

            anom = anom.copyProperties(img, img.propertyNames())

            # This permits sparse mean and std climatologies, e.g. those with a start and end set.
            return ee.Algorithms.If(coord_mean.size().gt(0), anom, None)

        collection = self.aggregate_time(freq.name, reducer, keep_bandnames)

        return collection.map(image_anomaly, opt_dropNulls=True)

    def interpolate_time(self, time: ee.Date, method: str = "linear") -> ee.Image:
        """Use interpolation to synthesize data at a given time within the time series. Based on the
        interpolation method chosen, a certain number of images must be present in the time series
        before and after the target date.

        Nearest and linear interpolation require 1 image before and after the selected time while
        cubic interpolation requires 2 images before and after the selected time.

        Parameters
        ----------
        date : ee.Date
            The target date to interpolate data at. This must be within the time series period.
        method : str, default linear
            The interpolation method to use, one of "nearest", "linear", or "cubic".

        Returns
        -------
        ee.Image
            Data interpolated to the target time from surrounding data in the time series.

        Example
        -------
        >>> ts = wxee.TimeSeries("IDAHO_EPSCOR/GRIDMET")
        >>> target_date = ee.Date("2020-09-08T03")
        >>> filled = ts.interpolate(target_date, "cubic")
        """
        method_func = get_interpolation_method(method)

        y1, y0 = self._get_n_images_before(time, 2)
        y2, y3 = self._get_n_images_after(time, 2)

        x1, x2 = [ee.Number(img.get("system:time_start")) for img in [y1, y2]]
        mu = _normalize(time.millis(), ee.Date(x1).millis(), ee.Date(x2).millis())

        if method in ["nearest", "linear"]:
            interpolated = method_func(y1, y2, mu)
        elif method == "cubic":
            interpolated = method_func(y0, y1, y2, y3, mu)

        interpolated = interpolated.set("system:time_start", time.millis())

        return interpolated

    def _get_n_images_before(self, date: ee.Date, n: int) -> List[ee.Image]:
        """Get n images before a given date (inclusive) in the time series. The images will be selected
        and returned in a list in order of their proximity to the target date."""
        before_imgs = self.filterDate(self.start_time, date.advance(1, "second")).sort(
            "system:time_start", opt_ascending=False
        )
        before_list = before_imgs.toList(n)

        return [ee.Image(before_list.get(i)) for i in range(n)]

    def _get_n_images_after(self, date: ee.Date, n: int) -> List[ee.Image]:
        """Get n images after a given date (inclusive) in the time series. The images will be selected
        and returned in order of their proximity to the target date."""
        after_imgs = self.filterDate(date, self.end_time.advance(1, "second")).sort(
            "system:time_start", opt_ascending=True
        )
        after_list = after_imgs.toList(n)

        return [ee.Image(after_list.get(i)) for i in range(n)]

    def insert_image(self, img: ee.Image) -> "TimeSeries":
        """Insert an image into the time series and sort it by :code:`system:time_start`.

        Parameters
        ----------
        img : ee.Image
            The image to insert.

        Returns
        -------
        wxee.TimeSeries
            The time series with the image inserted in time order
        """
        merged = self.merge(ee.ImageCollection(img)).sort("system:time_start")
        merged = ee.ImageCollection(merged.copyProperties(self, self.propertyNames()))
        return merged.wx.to_time_series()
