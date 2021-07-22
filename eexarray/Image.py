import ee  # type: ignore
import rasterio  # type: ignore
import tempfile
from typing import Optional, List

from eexarray.accessors import eex_accessor
from eexarray.utils import _set_nodata, _unpack_file, _download_url, _clean_filename
from eexarray import constants


@eex_accessor(ee.image.Image)
class Image:
    def __init__(self, obj: ee.image.Image):
        self._obj = obj

    def to_tif(
        self,
        out_dir: str = ".",
        description: Optional[str] = None,
        region: Optional[ee.Geometry] = None,
        scale: Optional[int] = None,
        crs: str = "EPSG:4326",
        file_per_band: bool = False,
        masked: bool = True,
        nodata: int = -32_768,
    ) -> List[str]:
        """Download an image to geoTIFF.

        Parameters
        ----------
        description : str, optional
            The name to save the file to, with no file extension. If none is provided, the system:id of the image will be
            used after replacing invalid characters with underscores.

        Returns
        -------
        list[str]
            Paths to downloaded images.
        """
        img = self._obj.set("system:id", description) if description else self._obj

        with tempfile.TemporaryDirectory(prefix=constants.TMP_PREFIX) as tmp:
            zipped = self._download(tmp, region, scale, crs, file_per_band, nodata)
            tifs = _unpack_file(zipped, out_dir)

        if masked:
            for tif in tifs:
                _set_nodata(tif, nodata)

        if not file_per_band:
            bandnames = img.bandNames().getInfo()
            for tif in tifs:
                with rasterio.open(tif, mode="r+") as img:
                    for i, band in enumerate(bandnames):
                        img.set_band_description(i + 1, band)

        return tifs

    def _download(
        self,
        out_dir: str = ".",
        region: Optional[ee.Geometry] = None,
        scale: Optional[int] = None,
        crs: str = "EPSG:4326",
        file_per_band: bool = False,
        nodata: int = -32_768,
    ) -> str:
        """Download an image as a ZIP"""
        # Unmasking without sameFootprint (below) makes images unbounded, so store the bounded geometry before unmasking.
        region = self._obj.geometry() if not region else region

        # Set nodata values. If sameFootprint is true, areas outside of the image bounds will not be set.
        img = self._obj.unmask(nodata, sameFootprint=False)

        url = img.getDownloadURL(
            params=dict(
                name=_clean_filename(img.get("system:id").getInfo()),
                scale=scale,
                crs=crs,
                region=region,
                filePerBand=file_per_band,
            )
        )

        zip = _download_url(url, out_dir)

        return zip
