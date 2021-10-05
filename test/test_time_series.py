import ee
import pytest

import wxee


@pytest.mark.ee
def test_climatology_mean():
    """Test that a climatology produces the right number of images."""
    start = ee.Date("2000-01")
    imgs = wxee.TimeSeries(
        [
            ee.Image.constant(1).set("system:time_start", start.advance(i, "month"))
            for i in range(48)
        ]
    )
    clim = imgs.climatology_mean("month")

    assert clim.size().getInfo() == 12


@pytest.mark.ee
def test_climatology_mean_limited_range():
    """Test that a climatology with limited start and end steps produces the right number of images."""
    start = ee.Date("2000-01")
    imgs = wxee.TimeSeries(
        [
            ee.Image.constant(1).set("system:time_start", start.advance(i, "month"))
            for i in range(48)
        ]
    )
    clim = imgs.climatology_mean("month", start=3, end=8)

    assert clim.size().getInfo() == 6


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


@pytest.mark.ee
def test_climatology_anomaly():
    """Test that a climatology anomaly returns the correct number of images with sparse input climatologies"""
    ts = wxee.TimeSeries("IDAHO_EPSCOR/GRIDMET").select("tmmx")
    ref = ts.filterDate("1990", "1992")
    obs = ts.filterDate("2020", "2021")

    mean = ref.climatology_mean("month", start=2, end=4)
    std = ref.climatology_std("month", start=2, end=4)

    anom = obs.climatology_anomaly(mean, std)

    assert anom.size().getInfo() == 3


@pytest.mark.ee
def test_dataset_conflicting_masked_value():
    """If two images in a time series have conflicting values (same coordinates and band with different values) and
    one is masked, they should be merged successfully and the unmasked value should be taken.
    """
    pt = ee.Geometry.Point([-118.2, 43.1]).buffer(20)

    img1 = (
        ee.Image.constant(0)
        .set("system:time_start", ee.Date("2020").millis())
        .set("system:id", "test2")
        .selfMask()
    )
    img2 = (
        ee.Image.constant(42)
        .set("system:time_start", ee.Date("2020").millis())
        .set("system:id", "test1")
    )

    imgs = wxee.TimeSeries([img1, img2])

    ds = imgs.wx.to_xarray(region=pt)

    assert ds.constant.values.item() == 42


@pytest.mark.ee
def test_dataset_conflicting_unmasked_value():
    """If two images in a time series have conflicting values (same coordinates and band with different values) and
    neither is masked, they should be merged successfully, the first value should be taken, and a warning should be thrown.
    """
    pt = ee.Geometry.Point([-118.2, 43.1]).buffer(20)

    img1 = (
        ee.Image.constant(3)
        .set("system:time_start", ee.Date("2020").millis())
        .set("system:id", "test2")
    )
    img2 = (
        ee.Image.constant(42)
        .set("system:time_start", ee.Date("2020").millis())
        .set("system:id", "test1")
    )

    imgs = wxee.TimeSeries([img1, img2])

    with pytest.warns(UserWarning):
        ds = imgs.wx.to_xarray(region=pt)

    assert ds.constant.values.item() == 3
