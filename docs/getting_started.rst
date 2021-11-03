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