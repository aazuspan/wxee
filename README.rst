wxee
====================================

.. image:: https://readthedocs.org/projects/wxee/badge/?version=latest&style=flat
   :target: https://wxee.readthedocs.io/en/latest/?badge=latest
.. image:: https://img.shields.io/badge/code%20style-black-000000.svg
   :target: https://github.com/psf/black
.. image:: https://img.shields.io/badge/License-GPLv3-blue.svg
   :target: https://www.gnu.org/licenses/gpl-3.0


.. image:: https://raw.githubusercontent.com/aazuspan/wxee/main/docs/_static/demo_001.gif
  :alt: Demo downloading weather data to xarray using wxee.


What is wxee?
-------------
`wxee <https://github.com/aazuspan/wxee>`_ was built to make processing gridded, mesoscale time series weather and climate data quick 
and easy by integrating the data catalog and processing power of `Google Earth Engine <https://earthengine.google.com/>`_ with the 
flexibility of `xarray <https://github.com/pydata/xarray>`_, with no complicated setup required. To accomplish this, wxee implements 
convenient methods for data processing, aggregation, downloading, and ingestion.


Features
--------
* Time series image collections to xarray, NetCDF, or GeoTIFF in one line of code
* Climatological means and temporal aggregation
* Parallel processing for fast downloads


Installation
------------

:code:`wxee` is coming soon to PyPI and conda-forge. Until then, it can be installed from source.

.. code-block:: bash

   git clone https://github.com/aazuspan/wxee
   cd wxee
   make install


Quickstart
----------

Setup
~~~~~
Once you have access to Google Earth Engine, just import and initialize :code:`ee` and :code:`wxee`.

.. code-block:: python
   
   import ee
   import wxee

   ee.Initialize()

Converting to xarray and GeoTIFF
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Methods for :code:`xarray` and :code:`tif` conversion are extended to :code:`ee.Image` and :code:`ee.ImageCollection` using the 
:code:`wx` accessor. Just :code:`import wxee` and use the :code:`wx` accessor.

.. code-block:: python

   ee.ImageCollection("IDAHO_EPSCOR/GRIDMET").wx.to_xarray()

Creating a Time Series
~~~~~~~~~~~~~~~~~~~~~~

Additional methods for processing image collections in the time dimension are available through the :code:`TimeSeries` subclass.
A :code:`TimeSeries` can be created from an existing :code:`ee.ImageCollection`...

.. code-block:: python

   col = ee.ImageCollection("IDAHO_EPSCOR/GRIDMET")
   ts = col.wx.to_time_series()

Or instantiated directly just like you would an :code:`ee.ImageCollection`!

.. code-block:: python

   ts = wxee.TimeSeries("IDAHO_EPSCOR/GRIDMET")


Aggregating Daily to Monthly
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Many weather datasets are in daily or hourly resolution. These can be aggregated to coarser resolutions using the :code:`aggregate_time`
method of the :code:`TimeSeries` class.

.. code-block:: python

   ts = wxee.TimeSeries("IDAHO_EPSCOR/GRIDMET")
   monthly_max = ts.aggregate_time(frequency="month", reducer=ee.Reducer.max())

Climatological Means
~~~~~~~~~~~~~~~~~~~~

Long-term climatological means can be calculated using the :code:`climatology_mean` method of the :code:`TimeSeries` class.

.. code-block:: python

   ts = wxee.TimeSeries("IDAHO_EPSCOR/GRIDMET")
   mean_clim = ts.climatology_mean(frequency="month")

Contributing
------------
Bugs or feature requests are always appreciated! They can be submitted `here <https://github.com/aazuspan/wxee/issues>`_. 

Code contributions are also welcome! Please open an `issue <https://github.com/aazuspan/wxee/issues>`_ to discuss implementation, 
then follow the steps below. Developer setup instructions can be found `in the docs <https://wxee.readthedocs.io/en/latest/contributing.html>`_.