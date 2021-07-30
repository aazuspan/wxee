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

.. autoclass:: eexarray.ImageCollection
   :members: