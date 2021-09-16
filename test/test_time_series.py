import ee
import pytest

import wxee


@pytest.mark.ee
def test_aggregate_hourly_to_daily():
    """Test that aggregating an hourly time series to daily produces the correct number of images"""
    start = ee.Date("2020-01-01")
    imgs = wxee.TimeSeries(
        [
            ee.Image.constant(0).set("system:time_start", start.advance(i, "hour"))
            for i in range(48)
        ]
    )

    agg = imgs.aggregate_time("day")

    assert agg.size().getInfo() == 2


@pytest.mark.ee
def test_aggregate_daily_to_monthy():
    """Test that aggregating a daily time series to monthly produces the correct number of images"""
    start = ee.Date("2020-01-01")
    imgs = wxee.TimeSeries(
        [
            ee.Image.constant(0).set("system:time_start", start.advance(i, "day"))
            for i in range(350)
        ]
    )

    agg = imgs.aggregate_time("month")

    assert agg.size().getInfo() == 12


@pytest.mark.ee
def test_aggregate_invalid_frequencies():
    """Test that aggregating a time series works as expected, even in edge cases with invalid parameters"""
    start = ee.Date("2020-01-01")

    # If aggregation frequency is the same or smaller than the time series
    # interval, the original number of images should be returned
    imgs = wxee.TimeSeries(
        [
            ee.Image.constant(0).set("system:time_start", start.advance(i, "day"))
            for i in range(17)
        ]
    )
    agg_day = imgs.aggregate_time("day")
    agg_hour = imgs.aggregate_time("hour")
    assert (
        agg_day.size().getInfo() == agg_hour.size().getInfo() == imgs.size().getInfo()
    )


@pytest.mark.ee
def test_aggregate_band_names():
    """Test that aggregating correctly handles band names"""
    start = ee.Date("2020-01-01")
    imgs = wxee.TimeSeries(
        [ee.Image.constant(0).set("system:time_start", start).rename("test_band")]
    )

    # If keep_bandnames is False, the reducer statistic will be appended to band names.
    agg = imgs.aggregate_time("day", reducer=ee.Reducer.mean(), keep_bandnames=False)
    assert agg.first().bandNames().getInfo() == ["test_band_mean"]

    agg = imgs.aggregate_time("day", keep_bandnames=True)
    assert agg.first().bandNames().getInfo() == ["test_band"]


@pytest.mark.ee
def test_start_time():
    """Test that the start time for a time series is correctly identified, even if the images are out of chronological order"""
    imgs = [
        ee.Image.constant(0).set("system:time_start", ee.Date("2020-01-05")),
        ee.Image.constant(0).set("system:time_start", ee.Date("2020-01-10")),
        ee.Image.constant(0).set("system:time_start", ee.Date("2020-01-01")),
    ]

    ts = wxee.TimeSeries(imgs)

    assert ts.start_time.format("yyyy-MM-dd").getInfo() == "2020-01-01"


@pytest.mark.ee
def test_end_time():
    """Test that the end time for a time series is correctly identified, even if the images are out of chronological order"""
    imgs = [
        ee.Image.constant(0).set("system:time_start", ee.Date("2020-01-01")),
        ee.Image.constant(0).set("system:time_start", ee.Date("2020-01-10")),
        ee.Image.constant(0).set("system:time_start", ee.Date("2020-01-05")),
    ]

    ts = wxee.TimeSeries(imgs)

    assert ts.end_time.format("yyyy-MM-dd").getInfo() == "2020-01-10"


@pytest.mark.ee
def test_day_interval_mean():
    """Test that a mean interval in days is correctly identified"""
    start_date = ee.Date("2020-01-01")
    test_interval = 21

    imgs = [
        ee.Image.constant(0).set("system:time_start", start_date),
        ee.Image.constant(0).set(
            "system:time_start", start_date.advance(test_interval * 1, "day")
        ),
        ee.Image.constant(0).set(
            "system:time_start", start_date.advance(test_interval * 2, "day")
        ),
    ]

    ts = wxee.TimeSeries(imgs)

    result_interval = ts.interval("day", ee.Reducer.mean()).getInfo()

    assert result_interval == test_interval


@pytest.mark.ee
def test_hour_interval_mean():
    """Test that a mean interval in hours is correctly identified"""
    start_date = ee.Date("2020-01-01")
    test_interval = 13

    imgs = [
        ee.Image.constant(0).set("system:time_start", start_date),
        ee.Image.constant(0).set(
            "system:time_start", start_date.advance(test_interval * 1, "hour")
        ),
        ee.Image.constant(0).set(
            "system:time_start", start_date.advance(test_interval * 2, "hour")
        ),
    ]

    ts = wxee.TimeSeries(imgs)

    result_interval = ts.interval("hour", ee.Reducer.mean()).getInfo()

    assert result_interval == test_interval


@pytest.mark.ee
def test_hour_interval_min_max():
    """Test that min and max intervals in hours are correctly identified when the interval is irregular"""
    start_date = ee.Date("2020-01-01")
    test_interval = 13

    imgs = [
        ee.Image.constant(0).set("system:time_start", start_date),
        ee.Image.constant(0).set(
            "system:time_start", start_date.advance(test_interval * 1, "hour")
        ),
        ee.Image.constant(0).set(
            "system:time_start", start_date.advance(test_interval * 10, "hour")
        ),
    ]

    ts = wxee.TimeSeries(imgs)

    result_max_interval = ts.interval("hour", ee.Reducer.max()).getInfo()
    result_min_interval = ts.interval("hour", ee.Reducer.min()).getInfo()

    assert result_max_interval == test_interval * 9
    assert result_min_interval == test_interval
