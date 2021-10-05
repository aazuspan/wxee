import ee  # type: ignore


def nearest(y1: ee.Image, y2: ee.Image, mu: ee.Number) -> ee.Image:
    """Apply nearest neighbour interpolation at fractional point mu between image y1 and image y2."""
    return ee.Image(ee.Algorithms.If(mu.lt(0.5), y1, y2))


def linear(y1: ee.Image, y2: ee.Image, mu: ee.Number) -> ee.Image:
    """Apply linear interpolation at fractional point mu between image y1 and image y2."""
    return y1.multiply(mu.multiply(-1).add(1)).add(y2.multiply(mu))


def cubic(
    y0: ee.Image, y1: ee.Image, y2: ee.Image, y3: ee.Image, mu: ee.Number
) -> ee.Image:
    """Apply cubic interpolation at fractional point mu between images y0, y1, y2, and y3."""
    mu2 = mu.pow(2)
    a0 = y3.subtract(y2).subtract(y0).add(y1)
    a1 = y0.subtract(y1).subtract(a0)
    a2 = y2.subtract(y0)
    a3 = y1

    return (
        a0.multiply(mu).multiply(mu2).add(a1).multiply(mu2).add(a2).multiply(mu).add(a3)
    )
