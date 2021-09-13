Developer Guide
===============

Setup
-----

#. Create a fork of wxee.

#. Download and install the package and developer dependencies from your fork.

    .. code-block:: bash

        git clone https://github.com/{username}/wxee
        cd wxee
        make install-dev

#. Create a new feature branch.

    .. code-block:: bash

        git checkout -b {feature-name}

#. Write features and tests and commit them (all pre-commit checks must pass). Add NumPy-style docstrings and type hints for any new functions, methods, or classes.

    .. code-block:: bash

        git add {modified file(s)}
        git commit -m "{commit message}"

#. Rebuild documentation when docstrings are added or changed.

    .. code-block:: bash

        make docs
        make view-docs


Tests
-----

Writing Tests
^^^^^^^^^^^^^

All new functionality should be tested. Tests that require Earth Engine to be initialized should use the :code:`@pytest.mark.ee` decorator which allows them
to be easily skipped in case of connection issues.

For example:

.. code-block:: python

    import pytest

    @pytest.mark.ee
    def test_number_is_10():
        num = ee.Number(10)
        assert num.getInfo() == 10

Running Tests
^^^^^^^^^^^^^

To run all tests, use :code:`make tests`. If you cannot connect to Earth Engine or would like to skip slower tests, use :code:`make tests-local`.