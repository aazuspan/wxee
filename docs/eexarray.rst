eexarray package
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
   :undoc-members:
   :show-inheritance:

ee.ImageCollection.eex
------------------------

.. autoclass:: eexarray.ImageCollection
   :members:
   :undoc-members:
   :show-inheritance: