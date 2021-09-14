import ee


def pytest_sessionstart(session):
    """Initialize Earth Engine unless tests marked ee have been excluded.
    If Earth Engine needs to be initialized but can't be, raise an error.
    """
    if not is_ee_excluded(session):
        try:
            ee.Initialize()
        except Exception:
            raise ValueError(
                'Earth Engine could not be initialized. Use `pytest . -m "not ee"` to skip Earth Engine tests.'
            )


def is_ee_excluded(session):
    """Check if a marker filter was passed to the session to exclude tests marked `ee`."""
    markers = session.config.getoption("-m")
    return "not ee" in markers
