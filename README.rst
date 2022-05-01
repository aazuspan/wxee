.. image:: https://raw.githubusercontent.com/aazuspan/wxee/main/docs/_static/wxee.png
   :alt: wxee .-- -..-
   :width: 200
   :target: https://github.com/aazuspan/wxee

|

.. image:: https://img.shields.io/badge/Earth%20Engine%20API-Python-green
   :alt: Earth Engine Python
   :target: https://developers.google.com/earth-engine/tutorials/community/intro-to-python-api
.. image:: https://img.shields.io/pypi/v/wxee
   :alt: PyPI
   :target: https://pypi.org/project/wxee/
.. image:: https://img.shields.io/conda/vn/conda-forge/wxee.svg
   :alt: conda-forge
   :target: https://anaconda.org/conda-forge/wxee
.. image:: https://colab.research.google.com/assets/colab-badge.svg
   :alt: Open in Colab
   :target: https://colab.research.google.com/github/aazuspan/wxee/blob/main/docs/examples/image_collection_to_xarray.ipynb
.. image:: https://readthedocs.org/projects/wxee/badge/?version=latest&style=flat
   :alt: Read the Docs
   :target: https://wxee.readthedocs.io/en/latest/?badge=latest
.. image:: https://github.com/aazuspan/wxee/actions/workflows/tests.yml/badge.svg
   :alt: Build status
   :target: https://github.com/aazuspan/wxee
.. image:: https://codecov.io/gh/aazuspan/wxee/branch/main/graph/badge.svg?token=OeSeq4b7NF
   :alt: Code coverage
   :target: https://codecov.io/gh/aazuspan/wxee

------------

.. image:: https://raw.githubusercontent.com/aazuspan/wxee/main/docs/_static/demo_001.gif
  :alt: Demo downloading weather data to xarray using wxee.


What is wxee?
-------------
`wxee <https://github.com/aazuspan/wxee>`_ was built to make processing gridded, mesoscale time series data quick 
and easy by integrating the data catalog and processing power of `Google Earth Engine <https://earthengine.google.com/>`_ with the 
flexibility of `xarray <https://github.com/pydata/xarray>`_, with no complicated setup required. To accomplish this, wxee implements 
convenient methods for data processing, aggregation, downloading, and ingestion.

`wxee <https://github.com/aazuspan/wxee>`_ can be found in the `Earth Engine Developer Resources <https://developers.google.com/earth-engine/tutorials/community/developer-resources#python>`_!


Features
--------
* Time series image collections to `xarray <https://wxee.readthedocs.io/en/latest/examples/image_collection_to_xarray.html>`_, `NetCDF <https://wxee.readthedocs.io/en/latest/examples/image_collection_to_xarray.html>`_, or `GeoTIFF <https://wxee.readthedocs.io/en/latest/examples/downloading_images_and_collections.html>`_ in one line of code
* `Climatological anomalies <https://wxee.readthedocs.io/en/latest/examples/climatology_anomaly.html>`_ and temporal `aggregation <https://wxee.readthedocs.io/en/latest/examples/temporal_aggregation.html>`_, `interpolation <https://wxee.readthedocs.io/en/latest/examples/temporal_interpolation.html>`_, `smoothing <https://wxee.readthedocs.io/en/latest/generated/wxee.time_series.TimeSeries.rolling_time.html>`_, and `gap-filling <https://wxee.readthedocs.io/en/latest/generated/wxee.time_series.TimeSeries.fill_gaps.html>`_ in Earth Engine
* `Color composite plots <https://wxee.readthedocs.io/en/latest/examples/color_composites.html>`_ from **xarray** datasets
* Parallel processing for fast downloads


To see some of the capabilities of wxee and try it yourself, check out the interactive notebooks `here <https://wxee.readthedocs.io/en/latest/examples.html>`_!

Install
------------

Pip
~~~

.. code-block:: bash

   pip install wxee

Conda
~~~~~

.. code-block:: bash

    conda install -c conda-forge wxee

From Source
~~~~~~~~~~~

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

   wxee.Initialize()


Download Images
~~~~~~~~~~~~~~~

Download and conversion methods are extended to :code:`ee.Image` and :code:`ee.ImageCollection` using the 
:code:`wx` accessor. Just :code:`import wxee` and use the :code:`wx` accessor.

xarray
^^^^^^

.. code-block:: python

   ee.ImageCollection("IDAHO_EPSCOR/GRIDMET").wx.to_xarray()

NetCDF
^^^^^^

.. code-block:: python

   ee.ImageCollection("IDAHO_EPSCOR/GRIDMET").wx.to_xarray(path="data/gridmet.nc")

GeoTIFF
^^^^^^^

.. code-block:: python

   ee.ImageCollection("IDAHO_EPSCOR/GRIDMET").wx.to_tif()


Create a Time Series
~~~~~~~~~~~~~~~~~~~~

Additional methods for processing image collections in the time dimension are available through the :code:`TimeSeries` subclass.
A :code:`TimeSeries` can be created from an existing :code:`ee.ImageCollection`...

.. code-block:: python

   col = ee.ImageCollection("IDAHO_EPSCOR/GRIDMET")
   ts = col.wx.to_time_series()

Or instantiated directly just like you would an :code:`ee.ImageCollection`!

.. code-block:: python

   ts = wxee.TimeSeries("IDAHO_EPSCOR/GRIDMET")


Aggregate Daily Data
~~~~~~~~~~~~~~~~~~~~

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


