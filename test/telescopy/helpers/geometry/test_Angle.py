import unittest
import math

from ddt import ddt, data, unpack

from telescopy.helpers import geometry


@ddt
class TestAngle(unittest.TestCase):

    angles = [
        (
            geometry.Vector(1, 2, 4),
            geometry.Vector(1, 2, 4),
            0.0,  # expected angle in radians
        ),
        (
            geometry.Vector(1, 2, 4),
            geometry.Vector(-1, -2, -4),
            math.pi,  # expected angle in radians
        ),
        (
            geometry.Vector(0, 0, 1),
            geometry.Vector(1, 0, 0),
            math.pi / 2,  # expected angle in radians
        ),
    ]

    @data(*angles)
    @unpack
    def test_to_radians(self, v1, v2, expected_radians):
        angle = geometry.Angle(v1, v2)

        self.assertAlmostEqual(angle.to_radians(), expected_radians, delta=0.01)
