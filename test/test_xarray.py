import os

import mock
import pytest
import xarray as xr


def test_rgb_with_explicit_bands():
    """Test that explicitly defined bands are correctly set in the static plot"""
    ds = xr.load_dataset(os.path.join("test", "test_data", "COPERNICUS_S2_SR_test.nc"))
    # Intentionally out of order
    bands = ["B2", "B3", "B4"]
    fig = ds.wx.rgb(bands=bands)

    assert isinstance(fig, xr.plot.facetgrid.FacetGrid)
    assert fig.data["variable"].values.tolist() == bands


def test_rgb_with_implicit_bands():
    """Test that implicitly identified bands are correctly set in the static plot"""
    ds = xr.load_dataset(os.path.join("test", "test_data", "COPERNICUS_S2_SR_test.nc"))
    bands = ["B4", "B3", "B2"]
    fig = ds.wx.rgb()

    assert isinstance(fig, xr.plot.facetgrid.FacetGrid)
    assert fig.data["variable"].values.tolist() == bands


def test_rgb_with_missing_explicit_bands():
    """Test that plotting fails if too few bands are explicitly set"""
    ds = xr.load_dataset(os.path.join("test", "test_data", "COPERNICUS_S2_SR_test.nc"))

    with pytest.raises(ValueError):
        ds.wx.rgb(bands=["B1"])


def test_rgb_with_missing_implicit_bands():
    """Test that plotting fails if too few bands are implicitly found"""
    ds = xr.load_dataset(os.path.join("test", "test_data", "COPERNICUS_S2_SR_test.nc"))

    with pytest.raises(ValueError):
        ds[["B4", "B3"]].wx.rgb()


def test_rgb_interactive():
    """Test that an interactive plot can be generated"""
    ds = xr.load_dataset(os.path.join("test", "test_data", "COPERNICUS_S2_SR_test.nc"))
    ds.wx.rgb(interactive=True, widget_location="top")


def test_rgb_interactive_without_hvplot():
    """Test that an interactive plot cannot be generated if hvplot is missing by mocking the missing package"""
    ds = xr.load_dataset(os.path.join("test", "test_data", "COPERNICUS_S2_SR_test.nc"))

    with pytest.raises(ImportError, match="pip install hvplot"):
        with mock.patch.dict("sys.modules", {"hvplot.xarray": None}):
            ds.wx.rgb(interactive=True, widget_location="top")


def test_normalize():
    """Test that a normalized DataArray is in the correct range"""
    ds = xr.load_dataset(os.path.join("test", "test_data", "COPERNICUS_S2_SR_test.nc"))
    da = ds.B4

    da_norm = da.wx.normalize(stretch=0.9)

    assert da_norm.max().values == 1.0
    assert da_norm.min().values == 0.0


def test_normalize_with_invalid_stretch():
    """Test that normalization fails if the stretch value is outside the correct range"""
    ds = xr.load_dataset(os.path.join("test", "test_data", "COPERNICUS_S2_SR_test.nc"))
    da = ds.B4

    for stretch in [-0.1, 1.1]:
        with pytest.raises(ValueError):
            da.wx.normalize(stretch=stretch)
