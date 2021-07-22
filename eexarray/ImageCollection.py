import ee  # type: ignore
import functools
import multiprocessing as mp
import rasterio  # type: ignore
import tempfile
from tqdm import tqdm  # type: ignore
from typing import Optional, List
import xarray as xr

from eexarray.accessors import eex_accessor
from eexarray.utils import _flatten_list, _set_nodata, _unpack_file, _dataset_from_files
from eexarray import constants


@eex_accessor(ee.imagecollection.ImageCollection)
class ImageCollection:
    """Extends the ee.imagecollection.ImageCollection class indirectly through an accessor."""

    def __init__(self, obj: ee.imagecollection.ImageCollection):
        """
        Parameters
        ----------
        obj : ee.ImageCollection
            The Image Collection instance extended by this class.
        """
        self._obj = obj

    def to_xarray(
        self,
        region: Optional[ee.Geometry] = None,
        scale: Optional[int] = None,
        crs: str = "EPSG:4326",
        masked: bool = True,
        nodata: int = -32_768,
        num_cores: Optional[int] = None,
        progress: bool = True,
    ) -> xr.Dataset:
        """Convert an image collection to an xarray.Dataset. The :code:`system:time_start` property of each image in the
        collection is used to arrange the time dimension, and each image variable is loaded as a separate array in
        the dataset.

        Parameters
        ----------
        region : ee.Geometry, optional
            The region to download the images within. If none is provided, the :code:`geometry` of the image collection
            will be used. If geometry varies between images in the collection, the region will encompass all images
            which may lead to very large arrays and download limits.
        scale : int, optional
            The scale to download the array at in the CRS units. If none is provided, the :code:`projection.nominalScale`
            of the images will be used.
        crs : str, default "EPSG:4326"
            The coordinate reference system to download the array in.
        masked : bool, default True
            If true, nodata pixels in the array will be masked.
        nodata : int, default -32,768
            The value to set as nodata in the array. Any masked pixels will be filled with this value.
        num_cores : int, optional
            The number of CPU cores to use for parallel operations. If none is provided, all detected CPU cores will be
            used.
        progress : bool, default True
            If true, a progress bar will be displayed to track download progress.

        Returns
        -------
        xarray.Dataset
            A dataset containing all images in the collection with an assigned time dimension and variables set from
            each image.

        Examples
        --------
        >>> import ee, eexarray
        >>> ee.Initialize()
        >>> col = ee.ImageCollection("IDAHO_EPSCOR/GRIDMET").filterDate("2020-09-08", "2020-09-15")
        >>> col.eex.to_xarray(scale=40000, crs="EPSG:5070", nodata=-9999)
        """

        with tempfile.TemporaryDirectory(prefix=constants.TMP_PREFIX) as tmp:
            collection = self._rename_by_date()

            files = collection.eex.to_tif(
                out_dir=tmp,
                region=region,
                scale=scale,
                crs=crs,
                file_per_band=True,
                masked=masked,
                nodata=nodata,
                num_cores=num_cores,
                progress=progress,
            )

            ds = _dataset_from_files(files)

        if nodata == 0:
            nodata == 1e-8
        # Mask the nodata values. This will convert int datasets to float.
        if masked:
            ds = ds.where(ds != nodata)

        return ds

    def to_tif(
        self,
        out_dir: str = ".",
        prefix: Optional[str] = None,
        region: Optional[ee.Geometry] = None,
        scale: Optional[int] = None,
        crs: str = "EPSG:4326",
        file_per_band: bool = False,
        masked: bool = True,
        nodata: int = -32_768,
        num_cores: Optional[int] = None,
        progress: bool = True,
    ) -> List[str]:
        """Download all images in the collection to geoTIFF. Image file names will be the :code:`system:id` of each image
        after replacing invalid characters with underscores, with an optional user-defined prefix.

        Parameters
        ----------
        out_dir : str, default "."
            The directory to save the images to.
        prefix : str, optional
            A description to prefix to all image file names. If none is provided, no prefix will be added.
        region : ee.Geometry, optional
            The region to download the image within. If none is provided, the :code:`geometry` of each image will be used.
        scale : int, optional
            The scale to download each image at in the CRS units. If none is provided, the :code:`projection.nominalScale`
            of each image will be used.
        crs : str, default "EPSG:4326"
            The coordinate reference system to download each image in.
        file_per_band : bool, default False
            If true, one file will be downloaded per band per image. If false, one multiband file will be downloaded per
            image instead.
        masked : bool, default True
            If true, the nodata value of each image will be set in the image metadata.
        nodata : int, default -32,768
            The value to set as nodata in each image. Any masked pixels in the images will be filled with this value.
        num_cores : int, optional
            The number of CPU cores to use for parallel operations. If none is provided, all detected CPU cores will be
            used.
        progress : bool, default True
            If true, a progress bar will be displayed to track download progress.

        Returns
        -------
        list[str]
            Paths to downloaded images.

        Example
        -------
        >>> import ee, eexarray
        >>> ee.Initialize()
        >>> col = ee.ImageCollection("IDAHO_EPSCOR/GRIDMET").filterDate("2020-09-08", "2020-09-15")
        >>> col.eex.to_tif(scale=40000, crs="EPSG:5070", nodata=-9999)
        """
        if prefix:
            self._obj = self._obj.map(
                lambda img: img.set(
                    "system:id", ee.String(prefix).cat(img.get("system:id"))
                )
            )

        with tempfile.TemporaryDirectory(prefix=constants.TMP_PREFIX) as tmp:
            zips = self._download(
                tmp,
                region,
                scale,
                crs,
                file_per_band,
                nodata,
                num_cores,
                progress,
            )

            tifs = _flatten_list([_unpack_file(zipped, out_dir) for zipped in zips])

        if masked:
            for tif in tifs:
                _set_nodata(tif, nodata)

        # TODO: Clean this up to avoid repition with the other to_tif method.
        if not file_per_band:
            bandnames = self._obj.first().bandNames().getInfo()
            for tif in tifs:
                with rasterio.open(tif, mode="r+") as img:
                    for i, band in enumerate(bandnames):
                        img.set_band_description(i + 1, band)

        return tifs

    def _rename_by_date(self: ee.ImageCollection) -> ee.ImageCollection:
        def rename_img_by_date(img: ee.Image) -> ee.Image:
            date = ee.Date(ee.Image(img).get("system:time_start"))
            date_string = date.format("YMMdd'T'hhmmss")
            return img.set("system:id", date_string)

        return self._obj.map(lambda img: rename_img_by_date(img))

    def _download(
        self,
        out_dir: str = ".",
        region: Optional[ee.Geometry] = None,
        scale: Optional[int] = None,
        crs: str = "EPSG:4326",
        file_per_band: bool = False,
        nodata: int = -32_768,
        num_cores: Optional[int] = None,
        progress: bool = True,
    ) -> List[str]:
        """Download all images in a collection as ZIPs"""
        num_cores = mp.cpu_count() if not num_cores else num_cores
        n = self._obj.size().getInfo()

        with mp.Pool(num_cores) as p:
            params = functools.partial(
                self._download_image_at_index,
                out_dir=out_dir,
                region=region,
                scale=scale,
                crs=crs,
                file_per_band=file_per_band,
                nodata=nodata,
            )
            zips = list(
                tqdm(
                    p.imap(params, range(n)),
                    total=n,
                    disable=not progress,
                    desc="Downloading collection",
                )
            )
        return zips

    def _download_image_at_index(
        self,
        index: int,
        out_dir: str = ".",
        region: Optional[ee.Geometry] = None,
        scale: Optional[int] = None,
        crs: str = "EPSG:4326",
        file_per_band: bool = False,
        nodata: int = -32_768,
    ) -> List[str]:
        """Get an image from a collection at a specific index and download it."""
        img = ee.Image(self._obj.toList(index + 1).get(index))
        return img.eex._download(out_dir, region, scale, crs, file_per_band, nodata)
