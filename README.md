# eexarray
[![Documentation Status](https://readthedocs.org/projects/eexarray/badge/?version=latest&style=flat)](https://eexarray.readthedocs.io/en/latest/?badge=latest)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
[![License: GPL v3](https://img.shields.io/badge/License-GPLv3-blue.svg)](https://www.gnu.org/licenses/gpl-3.0)

A Python interface between Earth Engine and xarray

![demo](docs/_static/demo_001.gif)

## Description
eexarray was built to make processing gridded, mesoscale time series data quick and easy by integrating the data catalog and processing power of Google Earth Engine with the n-dimensional array functionality of xarray, with no complicated setup required.

## Features
- Time series image collections to xarray in one line of code
- Images and image collections to GeoTIFF
- Support for masked nodata values
- Parallel processing for fast downloads
- Temporal resampling in EE (hourly to daily, daily to monthly, etc.)

### Features Coming Soon
- Basic weather and climate processing implemented in EE
- Automated splitting of download requests that exceed size limits (no promises here...)

## Installation

Pip and Conda coming soon...

### From source
```bash
git clone https://github.com/aazuspan/eexarray
cd eexarray
make install
```

## Quickstart

Check out the [full documentation](https://eexarray.readthedocs.io/en/latest/) here.

### Using the eex Accessor

eexarray uses the `eex` accessor to extend Earth Engine classes. Just import eexarray and use `.eex` to access eexarray methods.

```python
import ee, eexarray
ee.Initialize()

ee.Image( ... ).eex
ee.ImageCollection( ... ).eex
```

### Converting an Image Collection xarray

```python
import ee, eexarray
ee.Initialize()

# Load hourly wind data from RTMA
hourly = ee.ImageCollection("NOAA/NWS/RTMA").filterDate("2020-09-08", "2020-09-15").select("WIND")
# Aggregate hourly winds to daily max winds
daily_max = hourly.resample_time(unit="day", reducer=ee.Reducer.max())
# Download the daily winds to an xarray dataset
arr = daily_max.eex.to_xarray(scale=40_000, crs="EPSG:5070")
```

### Downloading Images to GeoTIFF
```python
import ee, eexarray
ee.Initialize()

img = ee.Image("COPERNICUS/S2_SR/20200803T181931_20200803T182946_T11SPA")
img.eex.to_tif(out_dir="data", scale=200, crs="EPSG:5070")
```

## Limitations
eexarray avoids the hassle of Google Drive, Google Cloud, and service accounts by using Earth Engine's URL download system. The upside is one-liner downloads with no setup required. The downside is strict size limits for image requests. If you run into download issues, try using a larger scale or splitting images into smaller regions.

If eexarray is too limiting (i.e. high-volume users or embedded web apps), check out [restee](https://github.com/KMarkert/restee).

Aside from download limits, eexarray is in early, active development. There may be bugs or code-breaking changes (but I'll try to keep them to a minimum).

### Known Bugs
Downloading imagery from Earth Engine can fail due to communication issues with Google's servers. eexarray will automatically retry failed downloads, but if downloads continue to fail you can try 1) setting the `max_attempts` argument to a higher value or 2) waiting a few minutes and re-running your download.

## Contributing
Bugs or feature requests are always appreciated! They can be submitted [here](https://github.com/aazuspan/eexarray/issues). 

Code contributions are also welcome! Please open an [issue](https://github.com/aazuspan/eexarray/issues) to discuss implementation, then follow the steps below.

### Developer Setup
1. Create a fork of eexarray.

2. Download and install the package and developer dependencies from your fork.
```bash
git clone https://github.com/{username}/eexarray
cd eexarray
make install-dev
```

3. Install pre-commit hooks to automate formatting and type-checking.
```bash
make install-hooks
```

4. Create a new feature branch.
```bash
git checkout -b {feature-name}
```

5. Write features and tests and commit them (all pre-commit checks must pass). Add NumPy-style docstrings and type hints for any new functions, methods, or classes.

```bash
git add {modified file(s)}
git commit -m "{commit message}"
```

6. Rebuild documentation when docstrings are added or changed.
```bash
make docs
make view-docs
```
