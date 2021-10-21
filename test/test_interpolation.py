import ee
import pytest

import wxee.interpolation


@pytest.mark.ee
def test_nearest():
    y1 = ee.Number(3)
    y2 = ee.Number(14)

    assert wxee.interpolation.nearest(y1, y2, ee.Number(0.7)).getInfo() == 14
    assert wxee.interpolation.nearest(y1, y2, ee.Number(0.3)).getInfo() == 3


@pytest.mark.ee
def test_linear():
    y1 = ee.Number(0)
    y2 = ee.Number(10)

    assert wxee.interpolation.linear(y1, y2, ee.Number(0.5)).getInfo() == 5
    assert wxee.interpolation.linear(y1, y2, ee.Number(0.9)).getInfo() == 9


@pytest.mark.ee
def test_cubic():
    y0 = ee.Number(-2)
    y1 = ee.Number(3)
    y2 = ee.Number(9)
    y3 = ee.Number(15)

    assert (
        wxee.interpolation.cubic(y0, y1, y2, y3, ee.Number(0.34)).getInfo() == 5.322744
    )
