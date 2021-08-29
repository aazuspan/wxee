Developer Setup
===============

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
