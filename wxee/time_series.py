from typing import Any, List, Optional, Union

import ee  # type: ignore

from wxee.accessors import wx_accessor
from wxee.climatology import ClimatologyImageCollection
from wxee.collection import ImageCollection


@wx_accessor(ee.imagecollection.ImageCollection)
class TimeSeriesCollection(ImageCollection):
    """An image collection of chronological images."""

    def _get_times(self) -> ee.List:
        """Return the the :code:`system:time_start` of each image in the collection"""
        imgs = self._obj.toList(self._obj.size())
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

    def _resample_time(
        self,
        unit: str,
        reducer: Optional[Any] = None,
        keep_bandnames: bool = True,
    ) -> ee.ImageCollection:
        """Aggregate the collection over the time dimension to a specified unit. This method can only be used to go from
        small time units to larger time units, such as hours to days, not vice-versa. If the resampling unit is smaller
        than the time between images, un-aggregated images will be returned.

        Parameters
        ----------
        unit : str
            The unit of time to resample to. One of 'year', 'month' 'week', 'day', 'hour'.
        reducer : ee.Reducer, optional
            The reducer to apply when aggregating over time. If none is provided, ee.Reducer.mean() will be used.
        keep_bandnames : bool, default True
            If true, the band names of the input images will be kept in the aggregated images. If false, the name of the
            reducer will be appended to the band names, e.g. SR_B4 will become SR_B4_mean.

        Returns
        -------
        ee.ImageCollection
            The input image collection aggregated to the specified time unit.

        Raises
        ------
        ValueError
            If an invalid unit is passed.

        See Also
        --------
        TimeSeriesCollection.resample_hourly
        TimeSeriesCollection.resample_daily
        TimeSeriesCollection.resample_weekly
        TimeSeriesCollection.resample_monthly
        TimeSeriesCollection.resample_annually

        Example
        -------
        >>> collection_hourly = ee.ImageCollection("NOAA/NWS/RTMA")
        >>> daily_max = collection_hourly._resample_time(unit="day", reducer=ee.Reducer.max())
        """
        # ee.Reducer can't be used without initializing ee (see https://github.com/google/earthengine-api/issues/164),
        # so set the default reducer explicitly. This is also why the type hint above is set to Any.
        reducer = ee.Reducer.mean() if not reducer else reducer

        units = ["year", "month", "week", "day", "hour"]
        if unit.lower() not in units:
            raise ValueError(f"Unit must be one of {units}, not '{unit.lower()}''.")

        def resample_step(start: ee.Date) -> ee.Image:
            """Resample one time step in the given unit from a specified start time."""
            start = ee.Date(start)
            end = start.advance(1, unit)
            imgs = self._obj.filterDate(start, end)
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

        n_steps = self.end_time.difference(self.start_time, unit).ceil()
        steps = ee.List.sequence(0, n_steps.subtract(1))
        start_times = steps.map(lambda x: self.start_time.advance(x, unit))

        resampled = ee.ImageCollection(start_times.map(resample_step, dropNulls=True))

        return resampled

    def resample_hourly(
        self,
        reducer: Optional[Any] = None,
        keep_bandnames: bool = True,
    ) -> ee.ImageCollection:
        """Aggregate the collection over the time dimension hourly. This method can only be used with collections that
        are sub-hourly. If the time between images is greater than one hour, un-aggregated images will be returned.

        Parameters
        ----------
        reducer : ee.Reducer, optional
            The reducer to apply when aggregating over time. If none is provided, ee.Reducer.mean() will be used.
        keep_bandnames : bool, default True
            If true, the band names of the input images will be kept in the aggregated images. If false, the name of the
            reducer will be appended to the band names, e.g. SR_B4 will become SR_B4_mean.

        Returns
        -------
        ee.ImageCollection
            The input image collection aggregated hourly.

        See Also
        --------
        TimeSeriesCollection.resample_daily
        TimeSeriesCollection.resample_weekly
        TimeSeriesCollection.resample_monthly
        TimeSeriesCollection.resample_annually

        Example
        -------
        >>> collection_sub_hourly = ee.ImageCollection("NOAA/GOES/16/FDCC")
        >>> hourly_max = collection_sub_hourly.resample_hourly(reducer=ee.Reducer.max())
        """
        return self._resample_time("hour", reducer, keep_bandnames)

    def resample_daily(
        self,
        reducer: Optional[Any] = None,
        keep_bandnames: bool = True,
    ) -> ee.ImageCollection:
        """Aggregate the collection over the time dimension daily. This method can only be used with collections that
        are sub-daily. If the time between images is greater than one day, un-aggregated images will be returned.

        Parameters
        ----------
        reducer : ee.Reducer, optional
            The reducer to apply when aggregating over time. If none is provided, ee.Reducer.mean() will be used.
        keep_bandnames : bool, default True
            If true, the band names of the input images will be kept in the aggregated images. If false, the name of the
            reducer will be appended to the band names, e.g. SR_B4 will become SR_B4_mean.

        Returns
        -------
        ee.ImageCollection
            The input image collection aggregated daily.

        See Also
        --------
        TimeSeriesCollection.resample_hourly
        TimeSeriesCollection.resample_weekly
        TimeSeriesCollection.resample_monthly
        TimeSeriesCollection.resample_annually

        Example
        -------
        >>> collection_hourly = ee.ImageCollection("NOAA/NWS/RTMA")
        >>> daily_max = collection_hourly.resample_daily(reducer=ee.Reducer.max())
        """
        return self._resample_time("day", reducer, keep_bandnames)

    def resample_weekly(
        self,
        reducer: Optional[Any] = None,
        keep_bandnames: bool = True,
    ) -> ee.ImageCollection:
        """Aggregate the collection over the time dimension weekly. This method can only be used with collections that
        are sub-weekly. If the time between images is greater than one week, un-aggregated images will be returned.

        Parameters
        ----------
        reducer : ee.Reducer, optional
            The reducer to apply when aggregating over time. If none is provided, ee.Reducer.mean() will be used.
        keep_bandnames : bool, default True
            If true, the band names of the input images will be kept in the aggregated images. If false, the name of the
            reducer will be appended to the band names, e.g. SR_B4 will become SR_B4_mean.

        Returns
        -------
        ee.ImageCollection
            The input image collection aggregated weekly.

        See Also
        --------
        TimeSeriesCollection.resample_hourly
        TimeSeriesCollection.resample_daily
        TimeSeriesCollection.resample_monthly
        TimeSeriesCollection.resample_annually

        Example
        -------
        >>> collection_hourly = ee.ImageCollection("NOAA/NWS/RTMA")
        >>> weekly_max = collection_hourly.resample_weekly(reducer=ee.Reducer.max())
        """
        return self._resample_time("week", reducer, keep_bandnames)

    def resample_monthly(
        self,
        reducer: Optional[Any] = None,
        keep_bandnames: bool = True,
    ) -> ee.ImageCollection:
        """Aggregate the collection over the time dimension monthly. This method can only be used with collections that
        are sub-monthly. If the time between images is greater than one month, un-aggregated images will be returned.

        Parameters
        ----------
        reducer : ee.Reducer, optional
            The reducer to apply when aggregating over time. If none is provided, ee.Reducer.mean() will be used.
        keep_bandnames : bool, default True
            If true, the band names of the input images will be kept in the aggregated images. If false, the name of the
            reducer will be appended to the band names, e.g. SR_B4 will become SR_B4_mean.

        Returns
        -------
        ee.ImageCollection
            The input image collection aggregated monthly.

        See Also
        --------
        TimeSeriesCollection.resample_hourly
        TimeSeriesCollection.resample_daily
        TimeSeriesCollection.resample_weekly
        TimeSeriesCollection.resample_annually

        Example
        -------
        >>> collection_hourly = ee.ImageCollection("NOAA/NWS/RTMA")
        >>> monthly_max = collection_hourly.resample_monthly(unit="month", reducer=ee.Reducer.max())
        """
        return self._resample_time("month", reducer, keep_bandnames)

    def resample_annually(
        self,
        reducer: Optional[Any] = None,
        keep_bandnames: bool = True,
    ) -> ee.ImageCollection:
        """Aggregate the collection over the time dimension annually. This method can only be used with collections that
        are sub-annual. If the time between images is greater than one year, un-aggregated images will be returned.

        Parameters
        ----------
        reducer : ee.Reducer, optional
            The reducer to apply when aggregating over time. If none is provided, ee.Reducer.mean() will be used.
        keep_bandnames : bool, default True
            If true, the band names of the input images will be kept in the aggregated images. If false, the name of the
            reducer will be appended to the band names, e.g. SR_B4 will become SR_B4_mean.

        Returns
        -------
        ee.ImageCollection
            The input image collection aggregated annually.

        See Also
        --------
        TimeSeriesCollection.resample_hourly
        TimeSeriesCollection.resample_daily
        TimeSeriesCollection.resample_weekly
        TimeSeriesCollection.resample_monthly

        Example
        -------
        >>> collection_hourly = ee.ImageCollection("NOAA/NWS/RTMA")
        >>> annual_max = collection_hourly.resample_annually(reducer=ee.Reducer.max())
        """
        return self._resample_time("year", reducer, keep_bandnames)

    def _calculate_climatology_mean(
        self,
        unit: str,
        date_format: str,
        reducer: Any,
        start: int,
        end: int,
        keep_bandnames: bool,
    ) -> ee.ImageCollection:
        """Calculate a mean climatology image collection with a given unit, such as month or dayofyear.

        This method sets the :code:`wx:dimension` and :code:`wx:coordinate` properties of each image in the collection.

        Parameters
        ----------
        unit : str
            The name of the time unit, e.g. month or dayofyear. This will be set in the :code:`wx:dimension` unit.
        date_format : str
            The formatting string passed to ee.Date.format. See http://joda-time.sourceforge.net/apidocs/org/joda/time/format/DateTimeFormat.html.
        reducer : ee.Reducer
            The reducer to apply when aggregating over time, e.g. aggregating hourly data to daily for a daily
            climatology. If the data is already in the temporal scale of the climatology, e.g. creating a daily
            climatology from daily data, the reducer will have no effect.
        start : int
            The start coordinate in the given unit, e.g. month 1 will start in January.
        end : int
            The end coordinate in the given unit, e.g. month 12 will end in December.
        keep_bandnames : bool, default True
            If true, the band names of the input images will be kept in the aggregated images. If false, the name of the
            reducer will be appended to the band names, e.g. SR_B4 will become SR_B4_mean.

        Returns
        -------
        ee.ImageCollection
            The reduced collection.
        """
        prop = f"wx:{unit}"

        def reduce_unit(x: ee.String) -> Union[None, ee.Image]:
            """Apply a mean reducer over a time unit, returning None if no images fall within the time window.

            Parameters
            ----------
            x : ee.String
                The time coordinate to reduce, such as "1" for January.
            """
            imgs = col.filterMetadata(prop, "equals", x)
            reduced = imgs.reduce(ee.Reducer.mean())
            # Retrieve the time from the image instead of using x because I need a formatted
            # string for concatenating into the system:id later.
            coord = ee.Date(imgs.first().get("system:time_start")).format(date_format)
            reduced = reduced.set("wx:dimension", unit, "wx:coordinate", coord)
            # Reducing makes images unbounded which causes issues
            reduced = reduced.clip(col.geometry().bounds())

            if keep_bandnames:
                reduced = ee.Image(reduced).rename(imgs.first().bandNames())

            return ee.Algorithms.If(imgs.size().gt(0), reduced, None)

        if unit == "dayofyear":
            col = self._obj.wx.resample_daily(reducer, keep_bandnames)
        elif unit == "month":
            col = self._obj.wx.resample_monthly(reducer, keep_bandnames)

        col = self._obj
        col = col.map(
            lambda img: img.set(
                prop,
                ee.Number.parse(
                    ee.Date(ee.Image(img).get("system:time_start")).format(date_format)
                ),
            )
        )
        coord_list = ee.List.sequence(start, end)

        clim = ee.ImageCollection(
            coord_list.map(lambda x: reduce_unit(x), dropNulls=True)
        )

        return clim

    def climatology_mean_month(
        self,
        reducer: Optional[Any] = None,
        start: int = 1,
        end: int = 12,
        keep_bandnames: bool = True,
    ) -> ClimatologyImageCollection:
        """Calculate monthly mean climatology from a time series of data. This method works by aggregating raw data to
        monthly using a given reducer and then calculating per-month means over multiple years. The output will have
        one image for each month.

        Parameters
        ----------
        reducer : ee.Reducer, optional
            The reducer to apply when aggregating over time, e.g. aggregating daily data to monthly. If the data
            is already monthly, the reducer will have no effect. If none is provided, ee.Reducer.mean() will be used.
        start : int, default 1
            The number of the start month to include in the climatology.
        end : int, default 12
            The number of the end month to include in the climatology.
        keep_bandnames : bool, default True
            If true, the band names of the input images will be kept in the aggregated images. If false, the name of the
            reducer will be appended to the band names, e.g. SR_B4 will become SR_B4_mean.

        Returns
        -------
        ClimatologyImageCollection
            The image collection reduced to the number of months between start and end.

        Example
        -------
        >>> collection = ee.ImageCollection("IDAHO_EPSCOR/GRIDMET")
        >>> collection = collection.filterDate("1980", "2000")
        >>> monthly_max = collection.wx.climatology_month(ee.Reducer.max())
        >>> monthly_max.size().getInfo()
        12

        See Also
        --------
        TimeSeriesCollection.climatology_mean_dayofyear
        """
        # ee.Reducer can't be used without initializing ee (see https://github.com/google/earthengine-api/issues/164),
        # so set the default reducer explicitly. This is also why the type hint above is set to Any.
        reducer = ee.Reducer.mean() if not reducer else reducer

        monthly_clim = self._calculate_climatology_mean(
            "month", "M", reducer, start, end, keep_bandnames
        )

        return ClimatologyImageCollection(monthly_clim)

    def climatology_mean_dayofyear(
        self,
        reducer: Optional[Any] = None,
        start: int = 1,
        end: int = 366,
        keep_bandnames: bool = True,
    ) -> ClimatologyImageCollection:

        """Calculate day-of-year mean climatology from a time series of data. This method works by aggregating raw data to
        daily using a given reducer and then calculating per-day-of-year means over multiple years. The output will have
        one image for each day.

        Note
        ----
        Julian dates are used to calculate day-of-year means, so days after February 29 will be offset by one in leap years.
        For example, day-of-year 365 will represent December 31 in non-leap years and December 30 in leap years. Day 366
        will always represent December 31, but will be aggregated from 1/4 as many days as other days of the year.

        Parameters
        ----------
        reducer : ee.Reducer, optional
            The reducer to apply when aggregating over time, e.g. aggregating hourly data to daily. If the data
            is already daily, the reducer will have no effect. If none is provided, ee.Reducer.mean() will be used.
        start : int, default 1
            The number of the start day to include in the climatology.
        end : int, default 366
            The number of the end day to include in the climatology.
        keep_bandnames : bool, default True
            If true, the band names of the input images will be kept in the aggregated images. If false, the name of the
            reducer will be appended to the band names, e.g. SR_B4 will become SR_B4_mean.

        Returns
        -------
        ClimatologyImageCollection
            The image collection reduced to the number of days between start and end.

        Example
        -------
        >>> collection = ee.ImageCollection("IDAHO_EPSCOR/GRIDMET")
        >>> collection = collection.filterDate("1980", "2000")
        >>> daily_max = collection.wx.climatology_dayofyear(ee.Reducer.max())
        >>> daily_max.size().getInfo()
        366

        See Also
        --------
        TimeSeriesCollection.climatology_mean_month
        """
        # ee.Reducer can't be used without initializing ee (see https://github.com/google/earthengine-api/issues/164),
        # so set the default reducer explicitly. This is also why the type hint above is set to Any.
        reducer = ee.Reducer.mean() if not reducer else reducer

        daily_clim = self._calculate_climatology_mean(
            "dayofyear", "D", reducer, start, end, keep_bandnames
        )

        return ClimatologyImageCollection(daily_clim)
