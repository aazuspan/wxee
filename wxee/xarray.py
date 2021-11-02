from typing import Any, List, Optional

import xarray as xr


@xr.register_dataset_accessor("wx")
class DatasetAccessor:
    def __init__(self, obj: xr.Dataset):
        self._obj = obj

    def rgb(
        self,
        bands: Optional[List[str]] = None,
        stretch: float = 1.0,
        interactive: bool = False,
        **kwargs: Any,
    ) -> Any:
        """Generate an RGB color composite plot of the Dataset.

        Parameters
        ----------
        bands : List[str], optional
            A list of 3 data variable names to use as the red, green, and blue channels. If none is provided, the
            first three data variables will be used in order.
        stretch : float, default 1.0
            A percentile stretch to apply to pixel values, between 0.0 and 1.0.
        interactive : bool, default False
            If False, a static plot is returned, faceted over the time dimension. If True, an interactive plot is
            returned over the time dimension. interactive plots require the `hvplot` library to be installed
            independently.
        **kwargs
            Keyword arguments passed to the plotting function. For static plots, arguments are passed to
            :code:`xarray.Dataset.plot.imshow`. For interactive plots, arguments are passed to :code:`xarray.Dataset.hvplot.rgb`.

        Returns
        -------
        Union[xarray.plot.facetgrid.FacetGrid, HoloViews object]
            The RGB plot, either static or interactive.

        Raises
        ------
        ValueError
            If an incorrect number of bands are found, whether explicitly passed through the `bands` argument or
            implicitly identified from the data variables.

        ImportError
            If the `interactive` argument is True and the `hvplot` package is not installed.

        Examples
        --------
        Download one month of Sentinel-2 imagery over a point.

        >>> pt = ee.Geometry.Point([5.40432,44.11541])
        >>> ts = wxee.TimeSeries("COPERNICUS/S2_SR")
        >>> ts = ts.filterDate("2020-07", "2020-08").filterBounds(pt)
        >>> ds = ts.wx.to_xarray(region=pt.buffer(1000), scale=20)

        Generate a static plot of the images as a true color composite. The col_wrap argument will be passed to
        the plotting function.

        >>> ds.wx.rgb(bands=["B4", "B3", "B2"], stretch=0.85, col_wrap=4)

        Generate an interactive plot using a near-infrared false color composite. The aspect argument will be passed
        to the plotting function.

        >>> ds.wx.rgb(bands=["B8", "B4", "B3"], stretch=0.85, interactive=True, aspect=1.2)
        """
        if bands:
            if len(bands) != 3:
                raise ValueError(f"Bands must be a list with exactly 3 names.")
        else:
            bands = list(self._obj.var())[:3]

            # Raise a different error if the bands were identified implicitly to avoid confusion
            if len(bands) != 3:
                raise ValueError(
                    f"The Dataset must contain at least 3 data variables for RGB plotting."
                )

        da = self._obj[bands].to_array(name="rgb")

        da = da.wx.normalize(stretch)

        if interactive:
            try:
                import hvplot.xarray  # type: ignore
            except ImportError:
                raise ImportError(
                    "The `hvplot` package is required for interactive plots. Run `pip install hvplot`."
                )

            default_kwargs = {"widget_location": "bottom", "widget_type": "scrubber"}

            for k, v in default_kwargs.items():
                if k not in kwargs:
                    kwargs[k] = v

            return da.hvplot.rgb(x="x", y="y", bands="variable", **kwargs)

        return da.plot.imshow(col="time", **kwargs)


@xr.register_dataarray_accessor("wx")
class DataArrayAccessor:
    def __init__(self, obj: xr.DataArray):
        self._obj = obj

    def normalize(self, stretch: float = 1.0) -> xr.DataArray:
        """Normalize a Dataset's values between 0 and 1.

        Parameters
        ----------
        stretch : float, default 1.0
            A percentile stretch to apply before normalization between 0.0 and 0.1.

        Returns
        -------
        xarray.DataArray
            The dataset with normalized values.

        Raises
        ------
        ValueError
            If the stretch value is outside the valid range.
        """
        da = self._obj

        if stretch < 0 or stretch > 1:
            raise ValueError("Stretch value must be in the range [0.0, 1.0].")

        min_val = da.quantile(1 - stretch)
        max_val = da.quantile(stretch)

        return ((da - min_val) / (max_val - min_val)).clip(0, 1)
