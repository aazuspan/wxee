import os

import ee
import numpy as np
import pytest
import rasterio

import wxee


@pytest.mark.ee
def test_prefix_id():
    """Test that a prefix is correctly added to an image ID"""
    test_id = "test_id"
    test_prefix = "ford_prefix"
    img = ee.Image()
    img = img.set("system:id", test_id)

    result = img.wx._prefix_id(test_prefix)
    result_id = result.get("system:id").getInfo()
    assert result_id == "_".join([test_prefix, test_id])


@pytest.mark.ee
def test_get_download_id_complete():
    """Test that a download ID is correctly retrieved from an image with an ID, dimension, and coordinate set"""
    img = ee.Image()
    img = img.set(
        "system:id", "test_id", "wx:dimension", "month", "wx:coordinate", "11"
    )
    download_id = img.wx._get_download_id().getInfo()

    assert download_id == "test_id.month.11"


@pytest.mark.ee
def test_get_download_id_incomplete():
    """Test that a download ID is correctly retrieved from an image with no ID, dimension, or coordinate set.
    In this case, the ID should be set to "null", the dimension to "time", and the coordinate to the image's
    "system:time_start" value.
    """
    img = ee.Image()
    img = img.set("system:time_start", ee.Date("2020-01-01"))
    download_id = img.wx._get_download_id().getInfo()

    assert download_id == "null.time.20200101T000000"


@pytest.mark.ee
def test_get_download_id_dirty():
    """Test that a download ID is correctly retrieved from an image with an ID containing invalid characters"""
    img = ee.Image()

    dirty_id = r"""%m$o!os.?\\"""
    clean_id = "_m_o_os_"

    img = img.set(
        "system:id", dirty_id, "wx:dimension", "dim", "wx:coordinate", "coord"
    )
    download_id = img.wx._get_download_id().getInfo()

    assert download_id == clean_id + ".dim.coord"


@pytest.mark.ee
def test_to_xarray():
    """Test that to_xarray returns a valid xarray.DataArray with correct dimensions and coordinates"""
    img = (
        ee.Image.constant(42)
        .set("system:time_start", ee.Date("2000"))
        .rename("band_name")
    )
    region = ee.Geometry.Point(0, 0).buffer(10).bounds()
    da = img.wx.to_xarray(region=region, scale=20, progress=False)

    assert "time" in da.dims
    assert "band_name" in da.variables
    assert da.time.values[0] == np.datetime64("2000")
    assert da.band_name.mean().values.item() == 42.0


@pytest.mark.ee
def test_to_xarray_masked():
    """Test that to_xarray correctly masks nodata"""
    img = (
        ee.Image.constant(0)
        .set("system:time_start", ee.Date("2000"))
        .rename("band_name")
        .selfMask()
    )
    region = ee.Geometry.Point(0, 0).buffer(10).bounds()
    da = img.wx.to_xarray(region=region, scale=20, progress=False)

    assert np.isnan(da.band_name.mean().values.item())


@pytest.mark.ee
def test_to_xarray_unmasked():
    """Test that to_xarray correctly sets the fill value when masking is disabled"""
    img = (
        ee.Image.constant(0)
        .set("system:time_start", ee.Date("2000"))
        .rename("band_name")
        .selfMask()
    )
    region = ee.Geometry.Point(0, 0).buffer(10).bounds()
    da = img.wx.to_xarray(
        region=region, scale=20, progress=False, masked=False, nodata=-999
    )

    assert da.band_name.mean().values.item() == -999


@pytest.mark.ee
def test_to_netcdf():
    """Test that to_xarray saves a NetCDF when a path is given"""
    img = (
        ee.Image.constant(42)
        .set("system:time_start", ee.Date("2000"))
        .rename("band_name")
    )
    region = ee.Geometry.Point(0, 0).buffer(10).bounds()
    out_path = os.path.join("test", "test_data", "test.nc")
    img.wx.to_xarray(path=out_path, region=region, scale=20, progress=False)

    assert os.path.isfile(out_path)

    os.remove(out_path)


@pytest.mark.ee
def test_to_tif():
    """Check that file and band names are set correctly when downloading to GeoTIFF"""
    img = (
        ee.Image.constant(0)
        .set("system:time_start", ee.Date("2000"))
        .rename("band_name")
    )
    region = ee.Geometry.Point(0, 0).buffer(10).bounds()

    out_dir = os.path.join("test", "test_data")

    file = img.wx.to_tif(
        description="desc",
        out_dir=out_dir,
        region=region,
        scale=20,
        progress=False,
        file_per_band=False,
    )

    assert "desc.time.20000101" in file[0]

    with rasterio.open(file[0]) as src:
        assert src.descriptions == ("band_name",)

    os.remove(file[0])
