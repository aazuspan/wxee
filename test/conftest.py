import os
import json

import ee


def pytest_sessionstart(session):
    """Initialize Earth Engine unless tests marked ee have been excluded.
    If Earth Engine needs to be initialized but can't be, raise an error.
    """
    if not is_ee_excluded(session):
        try:
            _init_ee_for_tests()
        except Exception:
            raise ValueError(
                'Earth Engine could not be initialized. Use `pytest . -m "not ee"` to skip Earth Engine tests.'
            )


def is_ee_excluded(session):
    """Check if a marker filter was passed to the session to exclude tests marked `ee`."""
    markers = session.config.getoption("-m")
    return "not ee" in markers


def _init_ee_for_tests():
    # Use the Github Service Account for CI tests
    if os.environ.get("GITHUB_ACTIONS"):
        key_data = os.environ.get("EE_SERVICE_ACCOUNT")
        project_id = json.loads(key_data).get("project_id")
        credentials = ee.ServiceAccountCredentials(None, key_data=key_data)
    # Use stored persistent credentials for local tests
    else:
        # Project should be parsed from credentials
        project_id = None
        credentials = "persistent"

    ee.Initialize(credentials, project=project_id)
