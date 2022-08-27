class DownloadError(Exception):
    """Raised when a download fails."""

    pass


class MissingPropertyError(Exception):
    """Raised when an Earth Engine object is missing a required property."""

    pass
