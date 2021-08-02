eexarray
====================================

.. image:: https://readthedocs.org/projects/eexarray/badge/?version=latest&style=flat
   :target: https://eexarray.readthedocs.io/en/latest/?badge=latest
.. image:: https://img.shields.io/badge/code%20style-black-000000.svg
   :target: https://github.com/psf/black
.. image:: https://img.shields.io/badge/License-GPLv3-blue.svg
   :target: https://www.gnu.org/licenses/gpl-3.0

| *A Python interface between Earth Engine and xarray*
| https://github.com/aazuspan/eexarray

Description
-----------
eexarray was built to make processing gridded, mesoscale time series data quick and easy by integrating the data catalog 
and processing power of Google Earth Engine with the flexibility of xarray and numpy, with no complicated setup required.

Quickstart
----------

eexarray uses the :code:`eex` accessor to extend Earth Engine classes. Just import eexarray and use :code:`.eex` to access 
eexarray methods.

.. code-block:: python

   import ee, eexarray
   ee.Initialize()

   ee.Image( ... ).eex
   ee.ImageCollection( ... ).eex

eexarray can quickly resample hourly data from Earth Engine to daily averages and download to an xarray Dataset for further
processing in Python.

.. code-block:: python

   import ee, eexarray
   ee.Initialize()

   hourly = ee.ImageCollection("NOAA/NWS/RTMA").filterDate("2020-09-08", "2020-09-15")
   daily_max = hourly.eex.resample_daily(reducer=ee.Reducer.max())
   arr = daily_max.eex.to_xarray(scale=40_000, crs="EPSG:5070")

Contents
--------

.. toctree::
   :maxdepth: 2

   eexarray
   examples

* :ref:`genindex`