import functools
import multiprocessing as mp
import tempfile
from typing import List, Optional

import ee  # type: ignore
import xarray as xr
from tqdm import tqdm  # type: ignore

from eexarray import constants
from eexarray.accessors import eex_accessor
from eexarray.utils import _dataset_from_files, _flatten_list


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
        max_attempts: int, default 5
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
        >>> import ee, eexarray
        >>> ee.Initialize()
        >>> col = ee.ImageCollection("IDAHO_EPSCOR/GRIDMET").filterDate("2020-09-08", "2020-09-15")
        >>> col.eex.to_xarray(scale=40000, crs="EPSG:5070", nodata=-9999)
        """
        with tempfile.TemporaryDirectory(prefix=constants.TMP_PREFIX) as tmp:
            collection = self._rename_by_time()

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
        max_attempts: int, default 5
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
        >>> import ee, eexarray
        >>> ee.Initialize()
        >>> col = ee.ImageCollection("IDAHO_EPSCOR/GRIDMET").filterDate("2020-09-08", "2020-09-15")
        >>> col.eex.to_tif(scale=40000, crs="EPSG:5070", nodata=-9999)
        """
        num_cores = mp.cpu_count() if not num_cores else num_cores

        if prefix:
            self._obj = self._obj.map(lambda img: img.eex._prefix_id(prefix))

        imgs = self._to_image_list()
        n = len(imgs)

        with mp.Pool(num_cores) as p:
            params = functools.partial(
                _image_to_tif_alias,
                out_dir=out_dir,
                region=region,
                scale=scale,
                crs=crs,
                file_per_band=file_per_band,
                masked=masked,
                nodata=nodata,
                max_attempts=max_attempts,
            )
            tifs = list(
                tqdm(
                    p.imap(params, imgs),
                    total=n,
                    disable=not progress,
                    desc="Downloading collection",
                )
            )

        return _flatten_list(tifs)

    def _rename_by_time(self) -> ee.ImageCollection:
        """Set each image's :code:`system:id` to its formatted :code:`system:time_start`."""
        return self._obj.map(lambda img: img.eex._rename_by_time())

    def _to_image_list(self) -> List[ee.Image]:
        """Convert an image collection to a Python list of images."""
        return [
            ee.Image(self._obj.toList(self._obj.size()).get(i))
            for i in range(self._obj.size().getInfo())
        ]

    def _get_times(self) -> ee.List:
        """Return the the :code:`system:time_start` of each image in the collection"""
        imgs = self._obj.toList(self._obj.size())
        return imgs.map(lambda img: ee.Image(img).get("system:time_start"))

    @property
    def start_time(self) -> ee.Date:
        """The :code:`system:time_start` of first chronological image in the collection.

        Returns
        -------
        ee.Date
            The start time of the collection.
        """
        times = self._get_times()
        return ee.Date(times.reduce(ee.Reducer.min()))

    @property
    def end_time(self) -> ee.Date:
        """The :code:`system:time_start` of last chronological image in the collection.

        Returns
        -------
        ee.Date
            The end time of the collection.
        """
        times = self._get_times()
        return ee.Date(times.reduce(ee.Reducer.max()))

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

    def resample_time(
        self,
        unit: str,
        reducer: ee.Reducer = ee.Reducer.mean(),
        keep_bandnames: bool = True,
    ) -> ee.ImageCollection:
        """Aggregate the collection over the time dimension to a specified unit. This method can only be used to go from
        small time units to larger time units, such as hours to days, not vice-versa.

        Parameters
        ----------
        unit : str
            The unit of time to resample to. One of 'year', 'month' 'week', 'day', 'hour', 'minute', or 'second'.
        reducer : ee.Reducer, default ee.Reducer.mean
            The reducer to apply when aggregating over time.
        keep_bandnames : bool, default True
            If true, the band names of the input images will be kept in the aggregated images. If false, the name of the
            reducer will be appended to the band names, e.g. SR_B4 will become SR_B4_mean.

        Returns
        -------
        ee.ImageCollection
            The input image collection aggregated to the specified time unit.

        Raises
        ------
        ValueError
            If an invalid unit is passed.

        Example
        -------
        >>> collection_hourly = ee.ImageCollection("NOAA/NWS/RTMA")
        >>> daily_max = collection_hourly.resample_time(unit="day", reducer=ee.Reducer.max())
        """
        units = ["year", "month", "week", "day", "hour", "minute", "second"]
        if unit.lower() not in units:
            raise ValueError(f"Unit must be one of {units}, not '{unit.lower()}''.")

        def resample_step(start: ee.Date) -> ee.Image:
            """Resample one time step in the given unit from a specified start time."""
            start = ee.Date(start)
            end = start.advance(1, unit)
            imgs = self._obj.filterDate(start, end)
            resampled = imgs.reduce(reducer)
            resampled = resampled.copyProperties(
                imgs.first(), imgs.first().propertyNames()
            )
            resampled = resampled.set(
                {
                    "system:time_start": imgs.first().get("system:time_start"),
                    "system:time_end": imgs.eex.last().get("system:time_end"),
                }
            )

            if keep_bandnames:
                resampled = ee.Image(resampled).rename(imgs.first().bandNames())
            return resampled

        delta_millis = (
            self.start_time.advance(1, unit)
            .difference(self.start_time, "second")
            .multiply(1000)
        )

        start_times = ee.List.sequence(
            self.start_time.millis(), self.end_time.millis(), step=delta_millis
        )

        resampled = ee.ImageCollection(start_times.map(resample_step))

        return resampled


def _image_to_tif_alias(
    img: ee.Image,
    out_dir: str = ".",
    description: Optional[str] = None,
    region: Optional[ee.Geometry] = None,
    scale: Optional[int] = None,
    crs: str = "EPSG:4326",
    file_per_band: bool = False,
    masked: bool = True,
    nodata: int = -32_768,
    max_attempts: int = 10,
) -> List[str]:
    """A pickleable wrapper around the ee.Image.eex.to_tif instance method, allowing it to be used in multiprocessing.
    See https://stackoverflow.com/questions/27318290/why-can-i-pass-an-instance-method-to-multiprocessing-process-but-not-a-multipro
    """
    return img.eex.to_tif(
        out_dir,
        description,
        region,
        scale,
        crs,
        file_per_band,
        masked,
        nodata,
        max_attempts,
    )
