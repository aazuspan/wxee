import contextlib
import datetime
import itertools
import os
import tempfile
import warnings
from typing import Any, List, Tuple, Union
from zipfile import ZipFile

import ee  # type: ignore
import joblib  # type: ignore
import rasterio  # type: ignore
import requests
import xarray as xr
from requests.adapters import HTTPAdapter
from tqdm.auto import tqdm  # type: ignore
from urllib3.util.retry import Retry  # type: ignore


def _set_nodata(file: str, nodata: Union[float, int]) -> None:
    """Set the nodata value in the metadata of an image file.

    Parameters
    ----------
    file : str
        The path to the raster file to set.
    nodata : Union[float, int]
        The value to set as nodata.
    """
    with rasterio.open(file, "r+") as img:
        img.nodata = nodata


def _flatten_list(a: List[Any]) -> List[Any]:
    """Flatten a nested list."""
    return list(itertools.chain.from_iterable(a))


def _unpack_file(file: str, out_dir: str) -> List[str]:
    """Unpack a ZIP file to a directory.

    Parameters
    ----------
    file : str
        The path to a ZIP file.
    out_dir : str
        The path to a directory to unpack files within.

    Returns
    -------
    List[str]
        Paths to the unpacked files.
    """
    unzipped = []

    with ZipFile(file, "r") as zipped:
        unzipped += zipped.namelist()
        zipped.extractall(out_dir)

    return [os.path.join(out_dir, file) for file in unzipped]


def _download_url(url: str, out_dir: str, progress: bool, max_attempts: int) -> str:
    """Download a file from a URL to a specified directory.

    Parameters
    ----------
    url : str
        The URL address of the element to download.
    out_dir : str
        The directory path to save the temporary file to.
    progress : bool
        If true, a progress bar will be displayed to track download progress.
    max_attempts : int
        The maximum number of times to retry a connection.

    Returns
    -------
    str
        The path to the downloaded file.
    """
    filename = tempfile.NamedTemporaryFile(mode="w+b", dir=out_dir, delete=False).name
    r = _create_retry_session(max_attempts).get(url, stream=True)

    try:
        r.raise_for_status()
    except Exception as e:
        # Delete the tempfile if it could not be downloaded
        os.remove(filename)
        raise e

    file_size = int(r.headers.get("content-length", 0))

    with open(filename, "w+b") as dst, tqdm(
        total=file_size,
        unit="iB",
        unit_scale=True,
        unit_divisor=1024,
        desc="Downloading",
        disable=not progress,
    ) as bar:
        for data in r.iter_content(chunk_size=1024):
            size = dst.write(data)
            bar.update(size)

    return filename


def _create_retry_session(max_attempts: int) -> requests.Session:
    """Create a session with automatic retries.

    https://www.peterbe.com/plog/best-practice-with-retries-with-requests
    """
    session = requests.Session()
    retry = Retry(
        total=max_attempts, read=max_attempts, connect=max_attempts, backoff_factor=0.1
    )

    adapter = HTTPAdapter(max_retries=retry)

    session.mount("http://", adapter)
    session.mount("https://", adapter)

    return session


def _dataset_from_files(files: List[str], masked: bool, nodata: int) -> xr.Dataset:
    """Create an xarray.Dataset from a list of raster files."""
    das = [_dataarray_from_file(file, masked, nodata) for file in files]

    try:
        # Allow conflicting values if one is null, take the non-null value
        merged = xr.merge(das, compat="no_conflicts")
    except xr.core.merge.MergeError:
        # If non-null conflicting values occur, take the first value and warn the user
        merged = xr.merge(das, compat="override")
        warnings.warn(
            "Different non-null values were encountered for the same variable at the same time coordinate. The first value was taken."
        )

    return merged


def _dataarray_from_file(file: str, masked: bool, nodata: int) -> xr.DataArray:
    """Create an xarray.DataArray from a single file by parsing datetimes and variables from the file name.

    The file name must follow the format "{dimension}.{coordinate}.{variable}.{extension}".
    """
    da = xr.open_rasterio(file)
    dim, coord, var = _parse_filename(file)

    da = da.expand_dims({dim: [coord]}).rename(var).squeeze("band").drop_vars("band")

    # Mask the nodata values. This will convert int datasets to float.
    if masked:
        da = da.where(da != nodata)

    return da


def _parse_filename(file: str) -> Tuple[str, Union[str, int, datetime.datetime], str]:
    """Parse the dimension, coordinate, and variable from a filename following the format
    {id}.{dimension}.{coordinate}.{variable}.{extension}. Return as a tuple.
    """
    coord: Union[str, int, datetime.datetime]

    basename = os.path.basename(file)
    dim, coord_name, variable = basename.split(".")[1:4]
    if dim == "time":
        coord = _parse_time(coord_name)
    else:
        coord = int(coord_name)

    return (dim, coord, variable)


def _parse_time(time: str) -> Union[datetime.datetime, str]:
    """Parse a time string as it is exported from Earth Engine and return as a datetime.
    If the time cannot be parsed, it is returned as a string.
    """
    try:
        return datetime.datetime.strptime(time, "%Y%m%dT%H%M%S")
    except ValueError:
        warnings.warn(
            f"The time coordinate '{time}' could not be parsed into a valid datetime. Setting as raw value instead."
        )
        return time


def _replace_if_null(val: Union[ee.String, ee.Number], replacement: Any) -> Any:
    """Take an Earth Engine object and return either the original non-null object or the given replacement if it is null."""
    is_null = ee.Algorithms.IsEqual(val, None)
    return ee.Algorithms.If(is_null, replacement, val)


def _format_date(d: ee.Date) -> ee.String:
    """Format a date using a consistent pattern."""
    return ee.Date(d).format("yyyyMMdd'T'HHmmss")


@contextlib.contextmanager
def parallel_tqdm(tqdm_object: tqdm) -> tqdm:
    """Context manager to patch joblib to report into tqdm progress bar given as argument

    Reference
    ---------
    https://stackoverflow.com/questions/24983493/tracking-progress-of-joblib-parallel-execution

    Example
    -------
    >>> with Parallel(n_jobs=-1) as p:
    >>>     with parallel_tqdm(tqdm(desc="Progress", total=10)):
    >>>         urls = p(delayed(f)(x) for x in range(10))
    """

    class TqdmBatchCompletionCallback(joblib.parallel.BatchCompletionCallBack):
        def __init__(self, *args: Any, **kwargs: Any) -> None:
            super().__init__(*args, **kwargs)

        def __call__(self, *args: Any, **kwargs: Any) -> None:
            tqdm_object.update(n=self.batch_size)
            return super().__call__(*args, **kwargs)

    old_batch_callback = joblib.parallel.BatchCompletionCallBack
    joblib.parallel.BatchCompletionCallBack = TqdmBatchCompletionCallback
    try:
        yield tqdm_object
    finally:
        joblib.parallel.BatchCompletionCallBack = old_batch_callback
        tqdm_object.close()


def _normalize(x: ee.Number, minx: ee.Number, maxx: ee.Number) -> ee.Number:
    return ee.Number(x).subtract(minx).divide(ee.Number(maxx).subtract(minx))
