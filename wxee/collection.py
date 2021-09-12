import functools
import multiprocessing as mp
import tempfile
from multiprocessing.pool import ThreadPool
from typing import List, Optional, Tuple

import ee  # type: ignore
import xarray as xr
from tqdm.auto import tqdm  # type: ignore

from wxee import constants
from wxee.accessors import wx_accessor
from wxee.time_series import TimeSeries
from wxee.utils import _dataset_from_files, _download_url, _flatten_list


@wx_accessor(ee.imagecollection.ImageCollection)
class ImageCollection:
    def __init__(self, obj: ee.imagecollection.ImageCollection):
        """
        Parameters
        ----------
        obj : ee.ImageCollection
            The Image Collection instance extended by this class.
        """
        self._obj = obj

    def _to_image_list(self) -> List[ee.Image]:
        """Convert an image collection to a Python list of images."""
        return [
            ee.Image(self._obj.toList(self._obj.size()).get(i))
            for i in range(self._obj.size().getInfo())
        ]

    def get_image(self, index: int) -> ee.Image:
        """Return the image at the specified index in the collection. A negative index counts backwards from the end of
        the collection.

        Parameters
        ----------
        index : int
            The index of the image in the collection.

        Returns
        -------
        ee.Image
            The image at the given index.
        """
        return ee.Image(self._obj.toList(self._obj.size()).get(index))

    def last(self) -> ee.Image:
        """Return the last image in the collection.

        Returns
        -------
        ee.Image
            The last image in the collection.
        """
        return self.get_image(self._obj.size().subtract(1))

    def to_xarray(
        self,
        path: Optional[str] = None,
        region: Optional[ee.Geometry] = None,
        scale: Optional[int] = None,
        crs: str = "EPSG:4326",
        masked: bool = True,
        nodata: int = -32_768,
        num_cores: Optional[int] = None,
        progress: bool = True,
        max_attempts: int = 10,
    ) -> xr.Dataset:
        """Convert an image collection to an xarray.Dataset. The :code:`system:time_start` property of each image in the
        collection is used to arrange the time dimension, and each image variable is loaded as a separate array in
        the dataset.

        Parameters
        ----------
        path : str, optional
            The path to save the dataset to as a NetCDF. If none is given, the dataset will be stored in memory.
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
            If true, nodata pixels in the array will be masked by replacing them with numpy.nan. This will silently
            cast integer datatypes to float.
        nodata : int, default -32,768
            The value to set as nodata in the array. Any masked pixels will be filled with this value.
        num_cores : int, optional
            The number of CPU cores to use for parallel operations. If none is provided, all detected CPU cores will be
            used.
        progress : bool, default True
            If true, a progress bar will be displayed to track download progress.
        max_attempts: int, default 10
            Download requests to Earth Engine may intermittently fail. Failed attempts will be retried up to
            max_attempts. Must be between 1 and 99.

        Returns
        -------
        xarray.Dataset
            A dataset containing all images in the collection with an assigned time dimension and variables set from
            each image.

        Raises
        ------
        DownloadError
            Raised if the image cannot be successfully downloaded after the maximum number of attempts.

        Examples
        --------
        >>> import ee, wxee
        >>> ee.Initialize()
        >>> col = ee.ImageCollection("IDAHO_EPSCOR/GRIDMET").filterDate("2020-09-08", "2020-09-15")
        >>> col.wx.to_xarray(scale=40000, crs="EPSG:5070", nodata=-9999)
        """
        with tempfile.TemporaryDirectory(prefix=constants.TMP_PREFIX) as tmp:

            files = self._obj.wx.to_tif(
                out_dir=tmp,
                region=region,
                scale=scale,
                crs=crs,
                file_per_band=True,
                masked=masked,
                nodata=nodata,
                num_cores=num_cores,
                progress=progress,
                max_attempts=max_attempts,
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
        prefix: Optional[str] = None,
        region: Optional[ee.Geometry] = None,
        scale: Optional[int] = None,
        crs: str = "EPSG:4326",
        file_per_band: bool = False,
        masked: bool = True,
        nodata: int = -32_768,
        num_cores: Optional[int] = None,
        progress: bool = True,
        max_attempts: int = 10,
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
        max_attempts: int, default 10
            Download requests to Earth Engine may intermittently fail. Failed attempts will be retried up to
            max_attempts. Must be between 1 and 99.

        Returns
        -------
        list[str]
            Paths to downloaded images.

        Raises
        ------
        DownloadError
            Raised if the image cannot be successfully downloaded after the maximum number of attempts.

        Example
        -------
        >>> import ee, wxee
        >>> ee.Initialize()
        >>> col = ee.ImageCollection("IDAHO_EPSCOR/GRIDMET").filterDate("2020-09-08", "2020-09-15")
        >>> col.wx.to_tif(scale=40000, crs="EPSG:5070", nodata=-9999)
        """
        num_cores = mp.cpu_count() if not num_cores else num_cores

        if prefix:
            self._obj = self._obj.map(lambda img: img.wx._prefix_id(prefix))

        imgs = self._to_image_list()
        n = len(imgs)

        if num_cores > 1:
            # Use ThreadPool instead of Pool to avoid issues with pickling local functions
            # https://stackoverflow.com/questions/8804830/python-multiprocessing-picklingerror-cant-pickle-type-function
            with ThreadPool(num_cores) as p:
                kwargs = dict(
                    region=region,
                    scale=scale,
                    crs=crs,
                    file_per_band=file_per_band,
                    nodata=nodata,
                    max_attempts=max_attempts,
                )
                params = functools.partial(_image_get_url_alias, **kwargs)
                urls = list(
                    tqdm(
                        p.imap_unordered(params, imgs),
                        total=n,
                        disable=not progress,
                        desc="Requesting",
                        leave=True,
                    )
                )

                # Images and URLS both need to be passed to url_to_tif. To do that
                # in parallel, we need to zip them and pass each as one argument.
                img_urls = list(zip(imgs, urls))

                kwargs = dict(
                    out_dir=out_dir,
                    file_per_band=file_per_band,
                    masked=masked,
                    nodata=nodata,
                    progress=False,
                    max_attempts=max_attempts,
                )
                params = functools.partial(_image_url_to_tif_alias, **kwargs)
                tifs = list(
                    tqdm(
                        p.imap_unordered(params, img_urls),
                        total=n,
                        disable=not progress,
                        desc="Downloading",
                    )
                )

        # Non-parallel implementaion
        else:
            urls = [
                img.wx._get_url(region, scale, crs, file_per_band, nodata, max_attempts)
                for img in tqdm(imgs, disable=not progress, desc="Retrieving data")
            ]
            tifs = [
                img.wx._url_to_tif(
                    url, out_dir, file_per_band, masked, nodata, False, max_attempts
                )
                for img, url in tqdm(
                    list(zip(imgs, urls)), disable=not progress, desc="Downloading data"
                )
            ]

        return _flatten_list(tifs)

    def to_time_series(self) -> TimeSeries:
        """Convert to a :code:`wxee.TimeSeries` collection with associated methods."""
        return TimeSeries(self._obj)


def _image_get_url_alias(
    img: ee.Image,
    region: Optional[ee.Geometry] = None,
    scale: Optional[int] = None,
    crs: str = "EPSG:4326",
    file_per_band: bool = False,
    nodata: int = -32_768,
    max_attempts: int = 10,
) -> List[str]:
    """A pickleable wrapper around the ee.Image.wx._get_url instance method, allowing it to be used in multiprocessing.
    See https://stackoverflow.com/questions/27318290/why-can-i-pass-an-instance-method-to-multiprocessing-process-but-not-a-multipro
    """
    return img.wx._get_url(region, scale, crs, file_per_band, nodata, max_attempts)


def _image_url_to_tif_alias(
    img_url: Tuple[ee.Image, str],
    out_dir: str,
    masked: bool,
    file_per_band: bool = False,
    nodata: int = -32_768,
    progress: bool = True,
    max_attempts: int = 10,
) -> List[str]:
    """A pickleable wrapper around the ee.Image.wx._url_to_tif instance method, allowing it to be used in multiprocessing.
    See https://stackoverflow.com/questions/27318290/why-can-i-pass-an-instance-method-to-multiprocessing-process-but-not-a-multipro
    """
    # We had to zip these together to pass them as a single argument
    img, url = img_url

    return img.wx._url_to_tif(
        url, out_dir, file_per_band, masked, nodata, progress, max_attempts
    )
