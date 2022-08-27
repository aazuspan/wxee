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

    result_interval = ts.interval("day").getInfo()

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

    result_interval = ts.interval("hour").getInfo()

    assert result_interval == test_interval


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

    anom = obs.climatology_anomaly(mean)
    assert anom.size().getInfo() == 3


@pytest.mark.ee
def test_climatology_anomaly_with_inconsistent_inputs():
    """Test that a climatology anomaly throws an error if the frequency or reducer of the mean and std do not match"""
    ts = wxee.TimeSeries("IDAHO_EPSCOR/GRIDMET").select("tmmx")
    ref = ts.filterDate("1990", "1992")
    obs = ts.filterDate("2020", "2021")

    mean = ref.climatology_mean("month")
    std = ref.climatology_std("day")

    with pytest.raises(ValueError):
        obs.climatology_anomaly(mean, std)

    mean = ref.climatology_mean("month", ee.Reducer.mean())
    std = ref.climatology_std("month", ee.Reducer.max())

    with pytest.raises(ValueError):
        obs.climatology_anomaly(mean, std)


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


@pytest.mark.ee
def test_insert_image():
    """Test that an image is correctly inserted into a time series"""
    start_date = ee.Date("2020-01-01")
    imgs = [
        ee.Image.constant(0).set("system:time_start", start_date),
        ee.Image.constant(0).set("system:time_start", start_date.advance(1, "day")),
        ee.Image.constant(0).set("system:time_start", start_date.advance(2, "day")),
    ]

    ts = wxee.TimeSeries(imgs)

    next_img = ee.Image.constant(0).set(
        "system:time_start", start_date.advance(3, "day")
    )

    ts = ts.insert_image(next_img)

    assert ts.size().getInfo() == 4


@pytest.mark.ee
def test_interpolate_time():
    """Test that values are correctly interpolated"""
    pt = ee.Geometry.Point([-118.2, 43.1]).buffer(20)

    start_date = ee.Date("2020-01-01")
    imgs = [
        ee.Image.constant(-2).set("system:time_start", start_date),
        ee.Image.constant(3).set("system:time_start", start_date.advance(1, "day")),
        ee.Image.constant(9).set("system:time_start", start_date.advance(2, "day")),
        ee.Image.constant(15).set("system:time_start", start_date.advance(3, "day")),
    ]

    ts = wxee.TimeSeries(imgs)

    nearest = ts.interpolate_time(start_date.advance(1.9, "day"), method="nearest")
    assert (
        nearest.reduceRegion(
            ee.Reducer.mean(), pt, scale=100, crs="EPSG:3857"
        ).getInfo()["constant"]
        == 9
    )

    linear = ts.interpolate_time(start_date.advance(1.5, "day"), method="linear")
    assert (
        linear.reduceRegion(
            ee.Reducer.mean(), pt, scale=100, crs="EPSG:3857"
        ).getInfo()["constant"]
        == 6
    )

    cubic = ts.interpolate_time(start_date.advance(1.5, "day"), method="cubic")
    assert (
        cubic.reduceRegion(ee.Reducer.mean(), pt, scale=100, crs="EPSG:3857").getInfo()[
            "constant"
        ]
        == 5.875
    )


@pytest.mark.ee
def test_get_window():
    """Test getting images in a window around a given date with different alignment options"""

    start_date = ee.Date("2020-01-01")

    imgs = [
        ee.Image.constant(0).set("system:time_start", start_date.advance(-3, "day")),
        ee.Image.constant(0).set("system:time_start", start_date.advance(-2, "day")),
        ee.Image.constant(0).set("system:time_start", start_date.advance(-1, "day")),
        ee.Image.constant(0).set("system:time_start", start_date),
        ee.Image.constant(0).set("system:time_start", start_date.advance(1, "day")),
        ee.Image.constant(0).set("system:time_start", start_date.advance(2, "day")),
        ee.Image.constant(0).set("system:time_start", start_date.advance(3, "day")),
    ]

    ts = wxee.TimeSeries(imgs)

    window_center = ts._get_window(start_date, window=3, unit="day", align="center")

    assert window_center.size().getInfo() == 3
    assert window_center.start_time.getInfo() == start_date.advance(-1, "day").getInfo()
    assert window_center.end_time.getInfo() == start_date.advance(1, "day").getInfo()

    window_left = ts._get_window(start_date, window=3, unit="day", align="left")

    assert window_left.size().getInfo() == 3
    assert window_left.start_time.getInfo() == start_date.advance(-2, "day").getInfo()
    assert window_left.end_time.getInfo() == start_date.getInfo()

    window_right = ts._get_window(start_date, window=3, unit="day", align="right")

    assert window_right.size().getInfo() == 3
    assert window_right.start_time.getInfo() == start_date.getInfo()
    assert window_right.end_time.getInfo() == start_date.advance(2, "day").getInfo()


@pytest.mark.ee
def test_fill_gaps_with_images():
    """Test gap-filling with neighboring images."""
    pt = ee.Geometry.Point([-118.2, 43.1]).buffer(20)
    start_date = ee.Date("2020-01-01")

    imgs = [
        ee.Image.constant(1)
        .set("system:time_start", start_date.advance(-1, "day"))
        .int(),
        ee.Image.constant(0).set("system:time_start", start_date).selfMask().int(),
        ee.Image.constant(2)
        .set("system:time_start", start_date.advance(1, "day"))
        .int(),
    ]

    ts = wxee.TimeSeries(imgs)

    filled = ts.fill_gaps(
        window=3, unit="day", align="center", reducer=ee.Reducer.mean()
    )
    filled_img = filled.filterDate(start_date).first()

    assert (
        filled_img.reduceRegion(
            ee.Reducer.mean(), pt, scale=100, crs="EPSG:3857"
        ).getInfo()["constant"]
        == 1.5
    )


@pytest.mark.ee
def test_fill_gaps_with_value():
    """Test gap-filling with a value when there are no unmasked neighboring images."""
    pt = ee.Geometry.Point([-118.2, 43.1]).buffer(20)
    start_date = ee.Date("2020-01-01")

    imgs = [
        ee.Image.constant(0)
        .set("system:time_start", start_date.advance(-1, "day"))
        .selfMask()
        .int(),
        ee.Image.constant(0).set("system:time_start", start_date).selfMask().int(),
        ee.Image.constant(0)
        .set("system:time_start", start_date.advance(1, "day"))
        .selfMask()
        .int(),
    ]

    ts = wxee.TimeSeries(imgs)

    filled = ts.fill_gaps(
        window=3, unit="day", align="center", reducer=ee.Reducer.mean(), fill_value=5
    )
    filled_img = filled.filterDate(start_date).first()

    assert (
        filled_img.reduceRegion(
            ee.Reducer.mean(), pt, scale=100, crs="EPSG:3857"
        ).getInfo()["constant"]
        == 5
    )


@pytest.mark.ee
def test_dataframe():
    """Test that a time series dataframe contains the correct start and end times and IDs."""
    start_dates = ["2020-01-01", "2020-02-01", "2021-03-03"]
    ids = ["id1", "id2", "id3"]
    col_id = "test_time_series"

    imgs = [
        ee.Image.constant(1).set(
            "system:time_start",
            ee.Date(start_dates[i]).millis(),
            "system:id",
            ids[i],
        )
        for i in range(3)
    ]
    ts = wxee.TimeSeries(imgs).set("system:id", col_id)
    df = ts.dataframe(["system:time_start", "system:id"])

    assert df.index.id == col_id
    assert (
        df["system:time_start"].dt.strftime("%Y-%m-%d").values.tolist() == start_dates
    )
    assert df["system:id"].values.tolist() == ids
