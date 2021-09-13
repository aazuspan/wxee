import pytest

import wxee.constants


def test_valid_time_frequency() -> None:
    """Test that a valid time frequency is retrieved."""
    test_name = "day"

    assert wxee.constants.get_time_frequency(test_name).name == test_name


def test_invalid_time_frequency() -> None:
    """Test that an invalid time frequency throws an error."""
    test_name = "invalid"

    with pytest.raises(ValueError):
        wxee.constants.get_time_frequency(test_name)


def test_valid_climatology_frequency() -> None:
    """Test that a valid climatology frequency is retrieved."""
    test_name = "month"

    assert wxee.constants.get_climatology_frequency(test_name).name == test_name


def test_invalid_climatology_frequency() -> None:
    """Test that an invalid climatology frequency throws an error."""
    test_name = "invalid"

    with pytest.raises(ValueError):
        wxee.constants.get_climatology_frequency(test_name)
