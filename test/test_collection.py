import os

import ee
import numpy as np
import pytest

import wxee


@pytest.mark.ee
def test_to_image_list():
    """Test that a list of images can be converted to a collection and back to a list"""
    test_list = [
        ee.Image("IDAHO_EPSCOR/GRIDMET/19790101"),
        ee.Image("IDAHO_EPSCOR/GRIDMET/19790102"),
        ee.Image("IDAHO_EPSCOR/GRIDMET/19790103"),
    ]
    test_ids = [img.get("system:id").getInfo() for img in test_list]

    collection = ee.ImageCollection(test_list)

    result_list = collection.wx._to_image_list()
    result_ids = [img.get("system:id").getInfo() for img in result_list]

    assert test_ids == result_ids


@pytest.mark.ee
def test_get_image_at_index():
    """Test that _get_image returns the correct image from a collection"""
    index = 1

    test_list = [
        ee.Image("IDAHO_EPSCOR/GRIDMET/19790101"),
        ee.Image("IDAHO_EPSCOR/GRIDMET/19790102"),
        ee.Image("IDAHO_EPSCOR/GRIDMET/19790103"),
    ]
    test_id = test_list[index].get("system_id").getInfo()

    collection = ee.ImageCollection(test_list)

    result_id = collection.wx.get_image(index).get("system_id").getInfo()

    assert test_id == result_id


@pytest.mark.ee
def test_last():
    """Test that last returns the correct image from a collection"""
    test_list = [
        ee.Image("IDAHO_EPSCOR/GRIDMET/19790101"),
        ee.Image("IDAHO_EPSCOR/GRIDMET/19790102"),
        ee.Image("IDAHO_EPSCOR/GRIDMET/19790103"),
    ]
    test_id = test_list[-1].get("system_id").getInfo()

    collection = ee.ImageCollection(test_list)

    result_id = collection.wx.last().get("system_id").getInfo()

    assert test_id == result_id


@pytest.mark.ee
def test_to_time_series():
    """Test that converting an Image Collection to a Time Series returns the same
    result as insantiating a Time Series.
    """
    collection_id = "IDAHO_EPSCOR/GRIDMET"

    converted_time_series = ee.ImageCollection(collection_id).wx.to_time_series()
    instantiated_time_series = wxee.TimeSeries(collection_id)

    assert (
        converted_time_series.size().eq(instantiated_time_series.size()).getInfo() == 1
    )


@pytest.mark.ee
def test_to_xarray():
    """Test that a collection of images converted to an xarray.Dataset have the correct
    CRS, times, and values.
    """
    test_list = [
        ee.Image.constant(0)
        .set("system:id", "first_image", "system:time_start", ee.Date("2020-01-01"))
        .rename("band"),
        ee.Image.constant(1)
        .set("system:id", "first_image", "system:time_start", ee.Date("2020-01-02"))
        .rename("band"),
        ee.Image.constant(2)
        .set("system:id", "first_image", "system:time_start", ee.Date("2020-01-03"))
        .rename("band"),
    ]
    region = ee.Geometry.Point(0, 0).buffer(10).bounds()
    crs = "epsg:3857"

    collection = ee.ImageCollection(test_list)
    ds = collection.wx.to_xarray(region=region, scale=20, crs=crs, progress=False)

    assert crs in ds.crs
    assert all(
        ds.time.values
        == [
            np.datetime64("2020-01-01"),
            np.datetime64("2020-01-02"),
            np.datetime64("2020-01-03"),
        ]
    )
    assert all(ds.band.mean(["x", "y"]).values == [0.0, 1.0, 2.0])


@pytest.mark.ee
def test_to_netcdf():
    """Test that to_xarray saves a NetCDF when a path is given"""
    test_list = [
        ee.Image.constant(0)
        .set("system:id", "first_image", "system:time_start", ee.Date("2020-01-01"))
        .rename("band"),
        ee.Image.constant(1)
        .set("system:id", "first_image", "system:time_start", ee.Date("2020-01-02"))
        .rename("band"),
        ee.Image.constant(2)
        .set("system:id", "first_image", "system:time_start", ee.Date("2020-01-03"))
        .rename("band"),
    ]
    region = ee.Geometry.Point(0, 0).buffer(10).bounds()
    crs = "epsg:3857"

    collection = ee.ImageCollection(test_list)
    out_path = os.path.join("test", "test_data", "test.nc")

    collection.wx.to_xarray(
        path=out_path, region=region, scale=20, crs=crs, progress=False
    )

    assert os.path.isfile(out_path)

    os.remove(out_path)


@pytest.mark.ee
def test_download_with_prefix():
    """Test that prefixes are added to file IDs with to_tif"""
    test_list = [
        ee.Image.constant(0)
        .set("system:id", "first_image", "system:time_start", ee.Date("2020-01-01"))
        .rename("band"),
        ee.Image.constant(1)
        .set("system:id", "first_image", "system:time_start", ee.Date("2020-01-02"))
        .rename("band"),
        ee.Image.constant(2)
        .set("system:id", "first_image", "system:time_start", ee.Date("2020-01-03"))
        .rename("band"),
    ]
    region = ee.Geometry.Point(0, 0).buffer(10).bounds()
    crs = "epsg:3857"

    collection = ee.ImageCollection(test_list)
    out_path = os.path.join("test", "test_data")

    prefix = "PREFIX"
    files = collection.wx.to_tif(
        prefix=prefix,
        out_dir=out_path,
        region=region,
        scale=20,
        crs=crs,
        progress=False,
    )

    for file in files:
        assert os.path.basename(file).startswith(prefix)
        os.remove(file)
