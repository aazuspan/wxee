###############
Getting Started
###############


Install
=======

Pip
---

.. code-block:: bash

   pip install wxee

Conda
-----

.. code-block:: bash

    conda install -c conda-forge wxee

From Source
-----------

.. code-block:: bash

   git clone https://github.com/aazuspan/wxee
   cd wxee
   make install


Setup
=====

.. currentmodule:: wxee

Once you have access to Google Earth Engine, just import :code:`ee` and :code:`wxee` and initialize.

.. code-block:: python
   
   import ee
   import wxee

   wxee.Initialize()

.. note::

    The :func:`wxee.Initialize` function works similarly to :code:`ee.Initialize` but automatically connects to the 
    `high-volume Earth Engine endpoint <https://developers.google.com/earth-engine/cloud/highvolume>`_ 
    that should be used for all automated requests to Earth Engine, such as those made by :code:`wxee`.


Usage
=====

Basic Features
--------------

Basic :code:`wxee` functionality like downloading image collections to :code:`xarray`, :code:`GeoTiff`, and :code:`NetCDF`
are extended through the :code:`wx` accessor, like so:

.. code-block:: python

   collection = ee.ImageCollection("IDAHO_EPSCOR/GRIDMET").filterDate("2020", "2021")
   collection.wx.to_xarray()

See the example notebooks for details on the `xarray interface <https://wxee.readthedocs.io/en/latest/examples/image_collection_to_xarray.html>`_, 
`downloading images and collections <https://wxee.readthedocs.io/en/latest/examples/downloading_images_and_collections.html>`_, and 
`visualizing color composites <https://wxee.readthedocs.io/en/latest/examples/color_composites.html>`_.

Time Series Features
--------------------

More advanced functionality requires turning image collections into :class:`TimeSeries` objects. Check out this example notebook for and
`introduction to the TimeSeries class <https://wxee.readthedocs.io/en/latest/examples/time_series.html>`_

You can also find example notebooks on specific :class:`TimeSeries` methods like `temporal aggregation 
<https://wxee.readthedocs.io/en/latest/examples/temporal_aggregation.html>`_, `temporal interpolation 
<https://wxee.readthedocs.io/en/latest/examples/temporal_interpolation.html>`_, `climatological means 
<https://wxee.readthedocs.io/en/latest/examples/climatology_mean.html>`_, and `climatological anomalies 
<https://wxee.readthedocs.io/en/latest/examples/climatology_anomaly.html>`_.

Applied Examples
----------------

If you prefer, you can check out the applied example notebooks that use a variety of different methods to solve specific problems like
`fire progression mapping <https://wxee.readthedocs.io/en/latest/examples/fire_progressions.html>`_. 