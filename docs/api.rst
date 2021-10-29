.. currentmodule:: wxee

#############
API Reference
#############

This page contains auto-generated documentation for :code:`wxee` modules and classes.

Earth Engine Classes
====================

Base Earth Engine classes have additional functionality available through the :code:`wx` accessor. These methods are also 
accessible to :class:`TimeSeries` and :class:`Climatology` objects, and are the primary interface for
exporting and downloading Earth Engine data in :code:`wxee`.


The wx Accessor
---------------

To use methods extended by :code:`wxee`, just import the package and use the :code:`wx` accessor. 

.. code-block:: python

   import ee
   import wxee

   ee.Image("MODIS/006/MOD13Q1/2000_02_18").wx.to_xarray()


ee.Image
--------

.. currentmodule:: wxee.image

.. autosummary::
   :toctree: generated/

   Image.to_xarray
   Image.to_tif

ee.ImageCollection
------------------

.. currentmodule:: wxee.collection

.. autosummary::
   :toctree: generated/

   ImageCollection.to_xarray
   ImageCollection.to_tif
   ImageCollection.to_time_series
   ImageCollection.get_image
   ImageCollection.last


Time Series
===========

Time series are image collections with added functionality for processing in the time dimension.

.. note::

   A :code:`TimeSeries` can be converted to :code:`xarray` and :code:`tif` using the :code:`wx` accessor, just like an 
   :code:`ee.ImageCollection`.

Creating a Time Series
----------------------

Time series can be instantiated in two ways:

From an ID
~~~~~~~~~~

.. code-block:: python

   import ee
   import wxee

   ts = wxee.TimeSeries("IDAHO_EPSCOR/GRIDMET")

From a Collection
~~~~~~~~~~~~~~~~~

See :meth:`ImageCollection.to_time_series`.

.. code-block:: python

   import ee
   import wxee

   col = ee.ImageCollection("IDAHO_EPSCOR/GRIDMET")
   ts = col.wx.to_time_series()

Describing a Time Series 
------------------------

.. currentmodule:: wxee.time_series

There are a number of properties and methods that describe the characteristics of a time series.

.. autosummary::
   :toctree: generated/

   TimeSeries.start_time
   TimeSeries.end_time
   TimeSeries.interval
   TimeSeries.describe

Modifying a Time Series
-----------------------

Processing can be applied in the time dimension to modify a time series or create new time series.

.. autosummary::
   :toctree: generated/

   TimeSeries.aggregate_time
   TimeSeries.interpolate_time
   TimeSeries.rolling_time
   TimeSeries.fill_gaps
   TimeSeries.insert_image

Calculating Climatologies
-------------------------

Time series of weather data can be transformed into climatologies.

.. autosummary::
   :toctree: generated/

   TimeSeries.climatology_mean
   TimeSeries.climatology_std
   TimeSeries.climatology_anomaly


Climatology
===========

Climatologies are image collections where images represent long-term climatological normals at specific time steps.

Creating a Climatology
----------------------

Climatologies are created using :meth:`TimeSeries.climatology_mean` or :meth:`TimeSeries.climatology_std`.

.. currentmodule:: wxee.climatology

.. warning::

   The :class:`Climatology` class should never be instantiated directly.

.. code-block:: python

   import ee
   import wxee

   ts = wxee.TimeSeries("IDAHO_EPSCOR/GRIDMET").select("pr")
   monthly_mean_rainfall = ts.climatology_mean("month", reducer=ee.Reducer.sum())

.. note::

   The :code:`reducer` argument defines how the raw data will be aggregated before calculating the climatological mean.
   In this case, we use :code:`ee.Reducer.sum()` to aggregate the daily rainfall measurements into monthly totals. If the
   data were already monthly, the reducer would have no effect.


Describing a Climatology
------------------------

In addition to having all the methods extended with the :code:`wx` accessor, there are methods for describing the characteristics of a climatology.

.. autosummary::
   :toctree: generated/

   Climatology.describe