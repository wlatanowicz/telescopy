import unittest
import math

from ddt import ddt, data, unpack

from telescopy.helpers import geometry


@ddt
class TestVector(unittest.TestCase):

    vectors = [
        (
            0,
            0,
            1,
            geometry.Vector(0, 1, 0),
        ),
        (
            0,
            math.pi / 2,
            1,
            geometry.Vector(0, 0, 1),
        ),
        (
            0,
            math.pi / 2,
            1,
            geometry.Vector(0, 0, 1),
        ),
    ]

    @data(*vectors)
    @unpack
    def test_by_angle(self, a, b, l, expected_vector):
        vector = geometry.Vector.by_angles(a, b, l)

        self.assertAlmostEqual(vector.x, expected_vector.x, delta=0.01)
        self.assertAlmostEqual(vector.y, expected_vector.y, delta=0.01)
        self.assertAlmostEqual(vector.z, expected_vector.z, delta=0.01)
