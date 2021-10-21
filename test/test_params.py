import pytest

from wxee import params


class MockParamEnum(params.ParamEnum):
    first = 1
    second = 2


def test_getting_good_param():
    """Test that a correct parameter is successfully retrieved"""
    param = "second"
    result = MockParamEnum.get_option(param)
    assert result == 2


def test_getting_bad_param():
    """Test that an incorrect parameter throws an error"""
    param = "lobster"

    with pytest.raises(ValueError):
        MockParamEnum.get_option(param)


def test_closest_param_with_close():
    """Test that the correct closest parameter is identified"""
    param = "seqonde"
    result = MockParamEnum._get_closest_option(param)
    assert result == "second"


def test_closest_param_without_close():
    """Test that nothing is returned when there is no close parameter"""
    param = "dfjalksjfalekjf"
    result = MockParamEnum._get_closest_option(param)
    assert result is None
