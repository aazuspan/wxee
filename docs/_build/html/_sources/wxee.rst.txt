API
================

wx accessor
-------------

wxee adds functionality such as :code:`xarray` and :code:`tif` conversion to base Earth Engine objects using the :code:`wx` accessor. 
Just :code:`import wxee` and use the :code:`wx` accessor to access those methods.

.. code-block:: python

   import ee
   import wxee

   ee.Image( ... ).wx.to_tif( ... )

ee.Image.wx
~~~~~~~~~~~

.. autoclass:: wxee.Image
   :members:

ee.ImageCollection.wx
~~~~~~~~~~~~~~~~~~~~~

.. autoclass:: wxee.ImageCollection
   :members:

Time Series
-----------
Time series are image collections with added functionality for processing in the time dimension. They can be instantiated in two ways:

From a Collection ID
~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   import ee
   import wxee

   ts = wxee.TimeSeries("IDAHO_EPSCOR/GRIDMET")

From an Existing Collection
~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   import ee
   import wxee

   col = ee.ImageCollection("IDAHO_EPSCOR/GRIDMET")
   ts = col.wx.to_time_series()

Methods and Properties
~~~~~~~~~~~~~~~~~~~~~~

Once instantiated, a :code:`TimeSeries` has all of the methods of :code:`ee.ImageCollection` plus additional methods and 
properties for processing in the time dimension.

.. note::

   A :code:`TimeSeries` can be converted to :code:`xarray` and :code:`tif` using the :code:`wx` accessor, just like an 
   :code:`ee.ImageCollection`.

.. autoclass:: wxee.time_series.TimeSeries
   :members:

Climatology
-----------

A climatology describes long-term trends in weather over multiple years. The frequency of the climatology defines the time unit
of the climatology (e.g. months or days). For example, a monthly mean climatology of daily rainfall data over 30 years would
have 12 images, with each image describing the mean total rainfall in each month over those 30 years.

Creating a Climatology
~~~~~~~~~~~~~~~~~~~~~~

Climatologies are created from a :code:`TimeSeries` using the :code:`climatology_mean` and :code:`climatology_std` methods.

.. warning::

   The :code:`Climatology` class should never be instantiated directly.

.. code-block:: python

   import ee
   import wxee

   ts = wxee.TimeSeries("IDAHO_EPSCOR/GRIDMET").select("pr")
   monthly_mean_rainfall = ts.climatology_mean("month", reducer=ee.Reducer.sum())

.. note::

   The :code:`reducer` argument defines how the raw data will be aggregated before calculating the climatological mean.
   In this case, we use :code:`ee.Reducer.sum()` to aggregate the daily rainfall measurements into monthly totals. If the
   data were already monthly, the reducer would have no effect.


Methods and Properties
~~~~~~~~~~~~~~~~~~~~~~

Once instantiated, a :code:`Climatology` has all of the methods of :code:`ee.ImageCollection` (including those extended by the
:code:`wx` accessor) plus additional properties describing the climatology.

.. autoclass:: wxee.climatology.Climatology
   :members: