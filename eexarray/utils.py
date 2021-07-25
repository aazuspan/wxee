import datetime
import itertools
import os
import re
import tempfile
from typing import Any, List, Union
from zipfile import ZipFile

import rasterio  # type: ignore
import requests
import xarray as xr


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


def _clean_filename(s: str) -> str:
    """Convert a string into a safe-ish file path. This removes invalid characters but doesn't check for reserved or
    invalid names."""
    return re.sub(r"(?u)[^-\w]", "_", s)


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


def _download_url(url: str, out_dir: str) -> str:
    """Download a file from a URL to a specified directory.

    Parameters
    ----------
    url : str
        The URL address of the element to download.
    out_dir : str
        The directory path to save the temporary file to.

    Returns
    -------
    str
        The path to the downloaded file.
    """
    r = requests.get(url, stream=True)

    filename = tempfile.NamedTemporaryFile(mode="w+b", dir=out_dir, delete=False).name

    with open(filename, "w+b") as dst:
        dst.write(r.content)
    return filename


def _dataset_from_files(files: List[str]) -> xr.Dataset:
    """Create an xarray.Dataset from a list of raster files."""
    das = [_dataarray_from_file(file) for file in files]

    return xr.merge(das)


def _dataarray_from_file(file: str) -> xr.DataArray:
    """Create an xarray.DataArray from a single file by parsing datetimes and variables from the file name.

    The file name must follow the format "{datetime}.{variable}.{extension}".
    """
    da = xr.open_rasterio(file)
    dt = _datetime_from_filename(file)
    variable = _variable_from_filename(file)

    da = da.expand_dims({"time": [dt]}).rename(variable).squeeze("band").drop("band")

    return da


def _datetime_from_filename(file: str) -> datetime.datetime:
    """Extract a datetime from a filename that follows the format "{datetime}.{variable}.{extension}" """
    basename = os.path.basename(file).split(".")[0]
    return datetime.datetime.strptime(basename, "%Y%m%dT%H%M%S")


def _variable_from_filename(file: str) -> str:
    """Extract a variable name from a filename that follows the format "{datetime}.{variable}.{extension}" """
    return os.path.basename(file).split(".")[1]
