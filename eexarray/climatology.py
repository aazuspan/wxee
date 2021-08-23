from abc import ABC

import ee  # type: ignore

from eexarray.accessors import eex_accessor
from eexarray.collection import ImageCollection


class ClimatologyImageCollection(ee.ImageCollection):
    """An image collection of climatological statistics. Identical to an ee.ImageCollection but accessible through the
    ClimatologyCollection class (and more importantly, not accessible through the TimeSeriesCollection class).
    """

    pass


@eex_accessor(ClimatologyImageCollection)
class ClimatologyCollection(ImageCollection):
    """An image collection of climatological images."""

    pass
