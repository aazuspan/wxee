from typing import Any

import ee  # type: ignore


class Climatology(ee.imagecollection.ImageCollection):
    """An image collection of climatological statistics such as means or standard deviations.

    Attributes
    ----------
    statistic : str
        The statistic of the climatology, e.g. a mean climatology or standard deviation climatology.
    frequency : wxee.constants._ClimatologyFrequency
        The time frequency of the climatology.
    reducer : ee.Reducer
        The reducer used to aggregate the climatology.
    start : int
        The start coordinate in the time frequency included in the climatology, e.g. 1 for January if the
        frequency is "month".
    end : int
        The end coordinate in the time frequency included in the climatology, e.g. 8 for August if the
        frequency is "month".
    """

    def __init__(self, *args: Any) -> None:
        super().__init__(*args)

    def describe(self) -> None:
        """Generate and print descriptive statistics about the Climatology such as the ID, number of images, and frequency.
        This requires pulling data from the server, so it may run slowly.

        Returns
        -------
        None
        """

        size = self.size().getInfo()
        id = self.get("system:id").getInfo()

        print(
            f"\033[1m{id}\033[0m"
            f"\n\t{self.statistic.title()} Climatology"
            f"\n\tImages: {size}"
            f"\n\tFrequency: {self.frequency.name}"
            f"\n\tStart {self.frequency.name}: {self.start}"
            f"\n\tEnd {self.frequency.name}: {self.end}"
        )
