from typing import Any, List, Optional, Union

import ee  # type: ignore
import pandas as pd  # type: ignore
import plotly.express as px  # type: ignore
import plotly.graph_objects as go  # type: ignore

from wxee.climatology import Climatology, ClimatologyFrequencyEnum
from wxee.exceptions import MissingPropertyError
from wxee.interpolation import InterpolationMethodEnum
from wxee.params import ParamEnum
from wxee.utils import _millis_to_datetime, _normalize


class TimeFrequencyEnum(ParamEnum):
    """Parameters defining generic time frequnecies."""

    year = "year"
    month = "month"
    week = "week"
    day = "day"
    hour = "hour"
    minute = "minute"


class WindowAlignEnum(ParamEnum):
    """Parameters defining rolling window alignment options."""

    left = "left"
    center = "center"
    right = "right"


class TimeSeries(ee.imagecollection.ImageCollection):
    """An image collection of chronological images."""

    def __init__(self, *args: Any) -> None:
        super().__init__(*args)

    @property
    def start_time(self) -> ee.Date:
        """The :code:`system:time_start` of first chronological image in the collection.

        Returns
        -------
        ee.Date
            The start time of the collection.
        """
        return ee.Date(self.aggregate_min("system:time_start"))

    @property
    def end_time(self) -> ee.Date:
        """The :code:`system:time_start` of last chronological image in the collection.

        Returns
        -------
        ee.Date
            The end time of the collection.
        """
        return ee.Date(self.aggregate_max("system:time_start"))

    def interval(self, unit: str = "day") -> ee.Number:
        """Compute the mean time interval between images in the time series.

        Parameters
        ----------
        unit : str, default "day"
            The unit to return the time interval in. One of "minute", "hour", "day", "week", "month", "year".

        Returns
        -------
        ee.Number
            The mean time interval between images.

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
        return self.end_time.difference(self.start_time, unit=unit).divide(
            self.size().subtract(1)
        )

    def describe(self, unit: str = "day") -> None:  # pragma: no cover
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
        size = self.size().getInfo()

        # Pulling min and max out of the stats is slightly faster than using `aggregate_min` and `aggregate_max` separately
        stats = self.aggregate_stats("system:time_start")
        start_millis = ee.Date(stats.get("min"))
        end_millis = ee.Date(stats.get("max"))

        start = start_millis.format("yyyy-MM-dd HH:mm:ss z").getInfo()
        end = end_millis.format("yyyy-MM-dd HH:mm:ss z").getInfo()

        mean_interval = self.interval().getInfo()

        id = self.get("system:id").getInfo()

        print(
            f"\033[1m{id}\033[0m"
            f"\n\tImages: {size:,}"
            f"\n\tStart date: {start}"
            f"\n\tEnd date: {end}"
            f"\n\tMean interval: {mean_interval:.2f} {unit}s"
        )

    def dataframe(self, props: Union[None, List[str], ee.List] = None) -> pd.DataFrame:
        """Generate a Pandas dataframe describing properties of each image in the time series.

        Parameters
        ----------
        props : Union[List[str], ee.List], optional
            A list of property names to aggregate from all images into the dataframe. If none is
            provided, all non-system properties of the first image in the time series will be used.

        Returns
        -------
        pd.DataFrame
            A Pandas dataframe where each row represents an image and columns represent system properties.
        """
        if props is None:
            props = self.first().propertyNames().getInfo()
            props = [
                p
                for p in props
                if not p.startswith("system:")
                or p in ["system:time_start", "system:id"]
            ]
        elif isinstance(props, ee.List):
            props = props.getInfo()

        df_dict = {}
        n = self.size().getInfo()
        for prop in set(props):
            vals = self.aggregate_array(prop).getInfo()
            if len(vals) == 0:
                raise MissingPropertyError(
                    f"The property `{prop}` is missing from all images!"
                )
            elif len(vals) < n:
                raise MissingPropertyError(
                    f"The property `{prop}` is missing from some images!"
                )
            if prop.startswith("system:time"):
                vals = map(_millis_to_datetime, vals)

            df_dict[prop] = vals

        collection_id = self.get("system:id").getInfo()
        df = pd.DataFrame.from_dict(df_dict)
        df.index.id = collection_id
        return df

    def timeline(self) -> go.Figure:  # pragma: no cover
        """Generate an interactive plot showing the acquisition time of each image in the time series.

        Returns
        -------
        go.Figure
            A Plotly graph object interactive plot showing the acquisition time of each image in the time series.
        """
        df = self.dataframe(props=["system:id", "system:time_start"])
        df["y"] = 0

        fig = px.line(
            df,
            x="system:time_start",
            y="y",
            hover_name="system:id",
            markers=True,
            labels={"system:time_start": ""},
        )

        fig.update_traces(
            customdata=df[["system:id", "system:time_start"]],
            hovertemplate="<b>%{customdata[0]}</b>"
            + "<br>%{customdata[1]|%Y-%m-%d %H:%M:%S}",
            line=dict(width=2, color="black"),
            marker=dict(
                size=12,
                symbol="line-ns-open",
                color="grey",
                line=dict(width=1, color="black"),
            ),
        )

        # Add circles for each image
        fig.add_trace(
            go.Scatter(
                x=df["system:time_start"],
                y=df.y,
                mode="markers",
                hoverinfo="skip",
                marker=dict(
                    size=6,
                    symbol="circle",
                    color="white",
                    line=dict(width=1, color="black"),
                ),
            )
        )

        fig.update_layout(
            plot_bgcolor="white",
            height=200,
            hoverlabel=dict(bgcolor="white"),
            showlegend=False,
        )

        fig.update_yaxes(visible=False)
        fig.update_xaxes(linecolor="black", ticks="outside")

        return fig

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

        TimeFrequencyEnum.get_option(frequency)

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
        TimeFrequencyEnum.get_option(frequency)

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

        freq = ClimatologyFrequencyEnum.get_option(frequency)
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

        Examples
        --------
        >>> ts = wxee.TimeSeries("IDAHO_EPSCOR/GRIDMET")
        >>> target_date = ee.Date("2020-09-08T03")

        Interpolate weather data at the target date using cubic interpolation.

        >>> filled = ts.interpolate(target_date, "cubic")
        """
        method_func = InterpolationMethodEnum.get_option(method)

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

    def rolling_time(
        self,
        window: int,
        unit: str,
        align: str = "left",
        min_observations: int = 1,
        reducer: Optional[Any] = None,
        keep_bandnames: bool = True,
    ) -> "TimeSeries":
        """Apply a rolling reducer over the time dimension. Rolling windows are calculated around each image,
        so if images are irregularly spaced in time, the windows will be as well. As long as the minimum
        observations are met in each window, the output time series will contain the same number of images as
        the input, with each image reduced over its surrounding window.

        Parameters
        ----------
        window : int
            The number of time units to include in each rolling period.
        unit : str
            The time frequency of the window. One of "hour", "day", "week", "month", "year".
        align : str, default "left"
            The start location of the rolling window, relative to the primary image time. One of "left", "center",
            "right". For example, a 3-day left-aligned window will include all images up to (but not including)
            3 days prior to the primary image. Date ranges are exclusive in the alignment direction and inclusive
            in the opposite direction, so each primary image will be included in its own window.
        min_observations : int, default 1
            The minimum number of images to include in the rolling window (counting the primary image). If the
            minimum observations are not met, the primary image will be dropped. For example, a monthly time series
            reduced with a 10 day window and :code:`min_observations==3` would be empty because none of the
            windows would include enough observations.
        reducer : Optional[ee.Reducer]
            The reducer to apply to each rolling window. If none is given, ee.Reducer.mean will be used.
        keep_bandnames : bool, default True
            If true, the band names of the input images will be kept in the reduced images. If false, the name of the
            reducer will be appended to the band names, e.g. SR_B4 will become SR_B4_mean.

        Returns
        -------
        wxee.time_series.TimeSeries
            The time series with the rolling reducer applied to each image.

        Example
        -------
        >>> ts = wxee.TimeSeries("MODIS/006/MOD13A2)
        >>> ts_smooth = ts.rolling_time(90, "day", "center", reducer=ee.Reducer.median())
        """
        reducer = ee.Reducer.mean() if not reducer else reducer

        def roll_image(img: ee.Image) -> ee.Image:
            """Apply a rolling reducer to a single image using its temporal neighbors"""
            center = ee.Date(img.get("system:time_start"))
            neighbors = self._get_window(center, window, unit, align)
            smooth = neighbors.reduce(reducer)

            props = {
                "wx:window_size": window,
                "wx:window_unit": unit,
                "wx:window_align": align,
                "wx:window_includes": neighbors.size(),
            }
            smooth = ee.Image(
                smooth.copyProperties(img, img.propertyNames()).set(props)
            )

            if keep_bandnames:
                smooth = smooth.rename(img.bandNames())

            return ee.Algorithms.If(neighbors.size().lt(min_observations), None, smooth)

        return self.map(roll_image, opt_dropNulls=True)

    def fill_gaps(
        self,
        window: int,
        unit: str,
        align: str = "center",
        reducer: Optional[Any] = None,
        fill_value: Optional[float] = None,
    ) -> "TimeSeries":
        """Apply gap-filling using a moving window reducer through time. Each image is unmasked using its reduced temporal neighbors.
        If the window is not wide enough to include an unmasked value (e.g. if clouds occur in the same location in all images),
        masked values will remain unless a :code:`fill_value` is specified.

        Parameters
        ----------
        window : int
            The number of time units to include in each rolling period.
        unit : str
            The time frequency of the window. One of "hour", "day", "week", "month", "year".
        align : str, default "center"
            The start location of the rolling window, relative to the primary image time. One of "left", "center",
            "right". For example, a 3-day left-aligned window will include all images up to (but not including)
            3 days prior to the primary image. Date ranges are exclusive in the alignment direction and inclusive
            in the opposite direction, so each primary image will be included in its own window.
        reducer : Optional[ee.Reducer]
            The reducer to apply to each rolling window. If none is given, ee.Reducer.mean will be used.
        fill_value : float
            The value to fill any masked values with after applying initial gap-filling. If none is given, masked
            values may remain if the window size is not large enough.

        Returns
        -------
        wxee.time_series.TimeSeries
            The time series with each image unmasked using its reduced neighbors.

        Example
        -------
        >>> ts = wxee.TimeSeries("MODIS/006/MOD13A2)
        >>> ts_filled = ts.fill_gaps(90, "day", "center", reducer=ee.Reducer.median())
        """
        reducer = ee.Reducer.mean() if not reducer else reducer

        def fill_image(img: ee.Image) -> ee.Image:
            """Unmask a single image by applying a rolling reducer to its temporal neighbors."""
            center = ee.Date(img.get("system:time_start"))
            neighbors = self._get_window(center, window, unit, align)
            filler = neighbors.reduce(reducer)

            filled = img.unmask(filler)
            filled = filled.unmask(fill_value) if fill_value else filled

            return filled

        return self.map(fill_image)

    def _get_window(
        self, time: ee.Date, window: int, unit: str, align: str = "left"
    ) -> "TimeSeries":
        """Get all images within a window around a target date.

        Parameters
        ----------
        time : ee.Date
            The center date of the window.
        window : int
            The number of time units to include in the window.
        unit : str
            The time frequency of the window. One of "hour", "day", "week", "month", "year".
        align : str, default "left"
            The start location of the window, relative to the center time. One of "left", "center", "right". Date
            ranges are exclusive in the alignment direction and inclusive in the opposite direction, so the center
            date of the window is always included.

        Returns
        -------
        wxee.time_series.TimeSeries
            A time series containing all images in the window.
        """
        WindowAlignEnum.get_option(align)

        offset = 1 if align == "left" else 0.5 if align == "center" else 0
        nudge = 1 if align == "left" else 0 if align == "center" else -1

        # The windows need to be nudged slightly to set the correct exclusive/inclusive order.
        # For example, a left aligned window should exclude the left and include the right,
        # and vice-versa for a right aligned window.
        left = time.advance(window * offset * -1, unit).advance(nudge, "second")
        right = left.advance(window, unit)

        return self.filterDate(left, right)
