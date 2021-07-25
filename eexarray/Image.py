import tempfile
from typing import List, Optional

import ee  # type: ignore
import rasterio  # type: ignore
import xarray as xr

from eexarray import constants
from eexarray.accessors import eex_accessor
from eexarray.utils import (
    _clean_filename,
    _dataset_from_files,
    _download_url,
    _set_nodata,
    _unpack_file,
)


@eex_accessor(ee.image.Image)
class Image:
    def __init__(self, obj: ee.image.Image):
        self._obj = obj

    def to_xarray(
        self,
        path: Optional[str] = None,
        region: Optional[ee.Geometry] = None,
        scale: Optional[int] = None,
        crs: str = "EPSG:4326",
        masked: bool = True,
        nodata: int = -32_768,
    ) -> xr.Dataset:
        """Convert an image to an xarray.Dataset. The :code:`system:time_start` property of the image is used to set the
        time dimension, and each image variable is loaded as a separate array in the dataset.

        Parameters
        ----------
        path : str, optional
            The path to save the dataset to as a NetCDF. If none is given, the dataset will be stored in memory.
        region : ee.Geometry, optional
            The region to download the image within. If none is provided, the :code:`geometry` of the image will be used.
        scale : int, optional
            The scale to download the array at in the CRS units. If none is provided, the :code:`projection.nominalScale`
            of the image will be used.
        crs : str, default "EPSG:4326"
            The coordinate reference system to download the array in.
        masked : bool, default True
            If true, nodata pixels in the array will be masked by replacing them with numpy.nan. This will silently
            cast integer datatypes to float.
        nodata : int, default -32,768
            The value to set as nodata in the array. Any masked pixels will be filled with this value.

        Returns
        -------
        xarray.Dataset
            A dataset containing the image with variables set.

        Examples
        --------
        >>> import ee, eexarray
        >>> ee.Initialize()
        >>> col = ee.ImageCollection("IDAHO_EPSCOR/GRIDMET").filterDate("2020-09-08", "2020-09-15")
        >>> col.eex.to_xarray(scale=40000, crs="EPSG:5070", nodata=-9999)
        """
        with tempfile.TemporaryDirectory(prefix=constants.TMP_PREFIX) as tmp:
            self._obj = self._rename_by_date()

            files = self.to_tif(
                out_dir=tmp,
                region=region,
                scale=scale,
                crs=crs,
                file_per_band=True,
                masked=masked,
                nodata=nodata,
            )

            ds = _dataset_from_files(files)

        # Mask the nodata values. This will convert int datasets to float.
        if masked:
            ds = ds.where(ds != nodata)

        if path:
            ds.to_netcdf(path, mode="w")

        return ds

    def to_tif(
        self,
        out_dir: str = ".",
        description: Optional[str] = None,
        region: Optional[ee.Geometry] = None,
        scale: Optional[int] = None,
        crs: str = "EPSG:4326",
        file_per_band: bool = False,
        masked: bool = True,
        nodata: int = -32_768,
    ) -> List[str]:
        """Download an image to geoTIFF.

        Parameters
        ----------
        out_dir : str, default "."
            The directory to save the image to.
        description : str, optional
            The name to save the file as with no file extension. If none is provided, the :code:`system:id` of the image
            will be used after replacing invalid characters with underscores.
        region : ee.Geometry, optional
            The region to download the image within. If none is provided, the :code:`geometry` of the image will be used.
        scale : int, optional
            The scale to download the image at in the CRS units. If none is provided, the :code:`projection.nominalScale`
            of the image will be used.
        crs : str, default "EPSG:4326"
            The coordinate reference system to download the image in.
        file_per_band : bool, default False
            If true, one file will be downloaded per band. If false, one multiband file will be downloaded instead.
        masked : bool, default True
            If true, the nodata value of the image will be set in the image metadata.
        nodata : int, default -32,768
            The value to set as nodata in the image. Any masked pixels in the image will be filled with this value.

        Returns
        -------
        list[str]
            Paths to downloaded images.

        Example
        -------
        >>> import ee, eexarray
        >>> ee.Initialize()
        >>> img = ee.Image("COPERNICUS/S2_SR/20200803T181931_20200803T182946_T11SPA")
        >>> img.eex.to_tif(description="las_vegas", scale=200, crs="EPSG:5070", nodata=-9999)
        """
        img = self._obj.set("system:id", description) if description else self._obj

        with tempfile.TemporaryDirectory(prefix=constants.TMP_PREFIX) as tmp:
            zipped = self._download(tmp, region, scale, crs, file_per_band, nodata)
            tifs = _unpack_file(zipped, out_dir)

        if masked:
            for tif in tifs:
                _set_nodata(tif, nodata)

        if not file_per_band:
            bandnames = img.bandNames().getInfo()
            for tif in tifs:
                with rasterio.open(tif, mode="r+") as img:
                    for i, band in enumerate(bandnames):
                        img.set_band_description(i + 1, band)

        return tifs

    def _download(
        self,
        out_dir: str = ".",
        region: Optional[ee.Geometry] = None,
        scale: Optional[int] = None,
        crs: str = "EPSG:4326",
        file_per_band: bool = False,
        nodata: int = -32_768,
    ) -> str:
        """Download an image as a ZIP"""
        # Unmasking without sameFootprint (below) makes images unbounded, so store the bounded geometry before unmasking.
        region = self._obj.geometry() if not region else region

        # Set nodata values. If sameFootprint is true, areas outside of the image bounds will not be set.
        img = self._obj.unmask(nodata, sameFootprint=False)

        url = img.getDownloadURL(
            params=dict(
                name=_clean_filename(img.get("system:id").getInfo()),
                scale=scale,
                crs=crs,
                region=region,
                filePerBand=file_per_band,
            )
        )

        zip = _download_url(url, out_dir)

        return zip

    def _prefix_id(self, prefix: str) -> ee.Image:
        """Add a prefix to the image's system:id"""
        return self._obj.set(
            "system:id", ee.String(prefix).cat(self._obj.get("system:id"))
        )

    def _rename_by_date(self) -> ee.Image:
        """Set the image's :code:`system:id` to its formatted :code:`system:time_start`."""
        date = ee.Date(ee.Image(self._obj).get("system:time_start"))
        date_string = date.format("YMMdd'T'hhmmss")
        return self._obj.set("system:id", date_string)
