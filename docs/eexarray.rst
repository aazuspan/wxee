API
================

eex accessors
-------------

eexarray extends Earth Engine objects using the `eex` accessor. Import eexarray and use the `eex` accessor to access 
custom methods.

.. code-block:: python

   import ee
   import eexarray

   ee.Image( ... ).eex.to_tif( ... )

ee.Image.eex
------------------------

.. autoclass:: eexarray.Image
   :members:

ee.ImageCollection.eex
------------------------

Time Series
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
A time series is a collection of images where each image represents conditions over a specific time. 
All :code:`ee.ImageCollection` objects are treated as time series in eexarray, and it is assumed that each image
has a specific :code:`system:time_start` property.

.. autoclass:: eexarray.TimeSeriesCollection
   :inherited-members:
   :members:


Climatology
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
A climatology is a collection of images where each image represents multi-year statistics over a general unit of time, 
such as maximum monthly precipitation over 30 years. Unlike a time series, an image in a climatology collection does
not have a specific time (e.g. October 20, 1989) but instead represents a generalized time (e.g. October).

.. autoclass:: eexarray.ClimatologyCollection
   :inherited-members:
   :members:
