wxee
====================================

.. image:: https://img.shields.io/pypi/v/wxee
    :target: https://pypi.org/project/wxee/
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
* |:floppy_disk:| Time series image collections to xarray, NetCDF, or GeoTIFF in one line of code
* |:date:| Climatological means and temporal aggregation
* |:zap:| Parallel processing for fast downloads


Install
-------

.. content-tabs::

    .. tab-container:: tab1
      :title: Pip

      .. code-block:: bash

         pip install wxee

    .. tab-container:: tab2
      :title: Conda

      Coming soon to `conda-forge <https://conda-forge.org/>`_!

    .. tab-container:: tab3
      :title: Source

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

Download Images
~~~~~~~~~~~~~~~

Download and conversion methods are extended to :code:`ee.Image` and :code:`ee.ImageCollection` using the 
:code:`wx` accessor. Just :code:`import wxee` and use the :code:`wx` accessor.

.. content-tabs::

    .. tab-container:: tab1
      :title: xarray

      .. code-block:: python

         ee.ImageCollection("IDAHO_EPSCOR/GRIDMET").wx.to_xarray()

    .. tab-container:: tab2
      :title: NetCDF

      .. code-block:: python

         ee.ImageCollection("IDAHO_EPSCOR/GRIDMET").wx.to_xarray(path="data/gridmet.nc")

    .. tab-container:: tab3
      :title: GeoTIFF

      .. code-block:: python

         ee.ImageCollection("IDAHO_EPSCOR/GRIDMET").wx.to_tif()


Create a Time Series
~~~~~~~~~~~~~~~~~~~~

Additional methods for processing image collections in the time dimension are available through the :code:`TimeSeries` subclass.
A :code:`TimeSeries` can be created in two ways...


.. content-tabs::

    .. tab-container:: tab1
      :title: 1. Existing ImageCollection

      An existing :code:`ee.ImageCollection` can be converted into a :code:`wxee.TimeSeries` using the :code:`wx.to_time_series` method.

      .. code-block:: python

         col = ee.ImageCollection("IDAHO_EPSCOR/GRIDMET")
         ts = col.wx.to_time_series()

    .. tab-container:: tab2
      :title: 2. From Scratch!

      A :code:`wxee.TimeSeries` can be instantiated from an ID or list of :code:`ee.Images` just like an :code:`ee.ImageCollection`. 

      .. code-block:: python

         ts = wxee.TimeSeries("IDAHO_EPSCOR/GRIDMET")


Aggregate Daily to Monthly
~~~~~~~~~~~~~~~~~~~~~~~~~~

Many weather datasets are in daily or hourly resolution. These can be aggregated to coarser resolutions using the :code:`aggregate_time`
method of the :code:`TimeSeries` class.

.. code-block:: python

   ts = wxee.TimeSeries("IDAHO_EPSCOR/GRIDMET")
   monthly_max = ts.aggregate_time(frequency="month", reducer=ee.Reducer.max())

Calculate Climatological Means
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Long-term climatological means can be calculated using the :code:`climatology_mean` method of the :code:`TimeSeries` class.

.. code-block:: python

   ts = wxee.TimeSeries("IDAHO_EPSCOR/GRIDMET")
   mean_clim = ts.climatology_mean(frequency="month")

Contribute
----------

Bugs or feature requests are always appreciated! They can be submitted `here <https://github.com/aazuspan/wxee/issues>`_. 

Code contributions are also welcome! Please open an `issue <https://github.com/aazuspan/wxee/issues>`_ to discuss implementation, 
then follow the steps below. Developer setup instructions can be found `in the docs <https://wxee.readthedocs.io/en/latest/contributing.html>`_.
