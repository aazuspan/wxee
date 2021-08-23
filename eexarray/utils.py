import datetime
import itertools
import os
import re
import tempfile
import warnings
from typing import Any, List, Tuple, Union
from zipfile import ZipFile

import ee  # type: ignore
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
    file_size = int(r.headers.get("content-length", 0))

    with open(filename, "w+b") as dst, tqdm(
        total=file_size,
        unit="iB",
        unit_scale=True,
        unit_divisor=1024,
        desc="Downloading image",
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


def _dataset_from_files(files: List[str]) -> xr.Dataset:
    """Create an xarray.Dataset from a list of raster files."""
    das = [_dataarray_from_file(file) for file in files]

    return xr.merge(das)


def _dataarray_from_file(file: str) -> xr.DataArray:
    """Create an xarray.DataArray from a single file by parsing datetimes and variables from the file name.

    The file name must follow the format "{dimension}.{coordinate}.{variable}.{extension}".
    """
    da = xr.open_rasterio(file)
    dim, coord, variable = _parse_filename(file)

    da = da.expand_dims({dim: [coord]}).rename(variable).squeeze("band").drop("band")

    return da


def _parse_filename(file: str) -> Tuple[str, Union[str, int, datetime.datetime], str]:
    """Parse the dimension, coordinate, and variable from a filename following the format
    {id}.{dimension}.{coordinate}.{variable}.{extension}. Return as a tuple.
    """
    coord: Union[str, int, datetime.datetime]

    basename = os.path.basename(file)
    dim, coord_name, variable = basename.split(".")[1:4]
    if dim == "time":
        try:
            coord = datetime.datetime.strptime(coord_name, "%Y%m%dT%H%M%S")
        except ValueError:
            coord = coord_name
            warnings.warn(
                f"The time coordinate '{coord}' could not be parsed into a valid datetime. Setting as raw value instead."
            )
    else:
        coord = int(coord_name)

    return (dim, coord, variable)


def _replace_if_null(val: Union[ee.String, ee.Number], replacement: Any) -> Any:
    """Take an Earth Engine object and return either the original non-null object or the given replacement if it is null."""
    is_null = ee.Algorithms.IsEqual(val, None)
    return ee.Algorithms.If(is_null, replacement, val)


def _format_date(d: ee.Date) -> ee.String:
    """Format a date using a consistent pattern."""
    return ee.Date(d).format("yyyyMMdd'T'HHmmss")
