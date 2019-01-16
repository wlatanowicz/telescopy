import unittest
import math

from ddt import ddt, data, unpack

from telescopy.helpers import geometry


@ddt
class TestSphere(unittest.TestCase):

    cases = [
        (
            geometry.Sphere(
                geometry.Point(0, 0, 0),
                1
            ),
            geometry.Line(
                geometry.Point(0, 0, 0),
                geometry.Vector(0, 0, 1),
            ),
            (
                geometry.Point(0, 0, -1),
                geometry.Point(0, 0, 1),
            ),
        ),
    ]

    @data(*cases)
    @unpack
    def test_intersections(self, sphere, line, expected_intersections):
        intersections = sphere.intersect_with_line(line)
        self.assertEqual(len(intersections), len(expected_intersections))

        for i, ei in zip(intersections, expected_intersections):
            self.assertAlmostEqual(i.x, ei.x, delta=0.01)
            self.assertAlmostEqual(i.y, ei.y, delta=0.01)
            self.assertAlmostEqual(i.z, ei.z, delta=0.01)
