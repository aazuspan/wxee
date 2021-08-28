API
================

wx accessors
-------------

wxee extends Earth Engine objects using the `wx` accessor. Import wxee and use the `wx` accessor to access 
custom methods.

.. code-block:: python

   import ee
   import wxee

   ee.Image( ... ).wx.to_tif( ... )

ee.Image.wx
------------------------

.. autoclass:: wxee.Image
   :members:

ee.ImageCollection.wx
------------------------

Time Series
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
A time series is a collection of images where each image represents conditions over a specific time. 
All :code:`ee.ImageCollection` objects are treated as time series in wxee, and it is assumed that each image
has a specific :code:`system:time_start` property.

.. autoclass:: wxee.TimeSeriesCollection
   :inherited-members:
   :members:


Climatology
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
A climatology is a collection of images where each image represents multi-year statistics over a general unit of time, 
such as maximum monthly precipitation over 30 years. Unlike a time series, an image in a climatology collection does
not have a specific time (e.g. October 20, 1989) but instead represents a generalized time (e.g. October).

.. autoclass:: wxee.ClimatologyCollection
   :inherited-members:
   :members:
