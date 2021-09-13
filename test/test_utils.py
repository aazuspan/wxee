import datetime
import warnings

import ee
import pytest

import wxee.utils

ee.Initialize()


def test_ee_replace_if_null_with_null():
    """Test that a null value is correctly replaced."""
    null = None
    replace = "test_string"

    result = wxee.utils._replace_if_null(null, replace).getInfo()

    assert result == replace


def test_ee_replace_if_null_with_string():
    """Test that a non-null string is not replaced."""
    not_null = "not null"
    replace = "test_string"

    result = wxee.utils._replace_if_null(not_null, replace).getInfo()

    assert result == not_null


def test_ee_replace_if_null_with_num():
    """Test that a non-null number is not replaced."""
    not_null = 42
    replace = 12

    result = wxee.utils._replace_if_null(not_null, replace).getInfo()

    assert result == not_null


def test_parse_filename():
    """Test that dimensions, coordinates, and variables are correctly parsed from a filename"""
    test_id = "image_id"
    test_dim = "dim"
    test_coord = "100"
    test_var = "temp"
    test_ext = "tif"
    test_filename = ".".join([test_id, test_dim, test_coord, test_var, test_ext])

    result_dim, result_coord, result_var = wxee.utils._parse_filename(test_filename)

    assert (result_dim, result_coord, result_var) == (
        test_dim,
        int(test_coord),
        test_var,
    )


def test_parse_filename_time():
    """Test that a time coordinate is correctly decoded from a filename"""
    Y = 2020
    M = 9
    D = 2
    H = 16
    m = 43
    s = 1

    time_str = f"{Y}{M}{D}T{H}{m}{s}"
    test_datetime = datetime.datetime(
        year=Y, month=M, day=D, hour=H, minute=m, second=s
    )

    test_filename = f"id.time.{time_str}.var.ext"

    _, result_coord, _ = wxee.utils._parse_filename(test_filename)

    assert result_coord == test_datetime


def test_parse_invalid_time_warns():
    """Test that an invalid time coordinate is noticed and raises a warning"""
    invalid_time_str = "1"

    with pytest.warns(UserWarning):
        wxee.utils._parse_time(invalid_time_str)


def test_ee_formatted_date_parsed():
    """Test that a time formatted in Earth Engine can be parsed in Python."""
    Y = 2020
    M = 9
    D = 2
    H = 16
    m = 43
    s = 1

    test_date = ee.Date(f"{Y}-{M}-{D}T{H}:{m}:{s}")
    test_datetime = datetime.datetime(
        year=Y, month=M, day=D, hour=H, minute=m, second=s
    )

    formatted_result = wxee.utils._format_date(test_date).getInfo()
    parsed_result = wxee.utils._parse_time(formatted_result)

    assert parsed_result == test_datetime
