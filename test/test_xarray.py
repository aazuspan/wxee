import os

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


def test_normalize():
    """Test that a normalized DataArray is in the correct range"""
    ds = xr.load_dataset(os.path.join("test", "test_data", "COPERNICUS_S2_SR_test.nc"))
    da = ds.B4

    da_norm = da.wx.normalize(stretch=0.9)

    assert da_norm.max().values == 1.0
    assert da_norm.min().values == 0.0
