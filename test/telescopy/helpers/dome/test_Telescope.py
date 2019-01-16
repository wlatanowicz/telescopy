import unittest
from datetime import datetime
from ddt import ddt, data, unpack

from telescopy.helpers import dome
from telescopy.helpers import geometry


@ddt
class TestTelescope(unittest.TestCase):

    centers = [
        (
            20.5,
            dome.Mount(10, z_offset=20),
            (16, 52),  # lat, lon
            (0, 0),  # ra, dec
            datetime(2019, 1, 14, 22, 30, 00),
            geometry.Point(1, 2, 3),  # center
        ),
    ]

    axis = [
        (
            20.5,
            dome.Mount(10, z_offset=20),
            (16, 52),  # lat, lon
            (0, 0),  # ra, dec
            datetime(2019, 1, 14, 22, 30, 00),
            geometry.Vector(1, 2, 3),  # axis
        ),
    ]

    @data(*centers)
    @unpack
    def test_optical_center(self, radius, mount, lat_lon, ra_dec, date, expected_center):
        mount.ra, mount.dec = ra_dec
        mount.latitude, mount.longitude = lat_lon
        mount.date = date

        telescope = dome.Telescope(radius, mount)

        center = telescope.optical_center

        self.assertAlmostEqual(center.x, expected_center.x, delta=1)
        self.assertAlmostEqual(center.y, expected_center.y, delta=1)
        self.assertAlmostEqual(center.z, expected_center.z, delta=1)

    @data(*axis)
    @unpack
    def test_optical_axis(self, radius, mount, lat_lon, ra_dec, date, expected_axis):
        mount.ra, mount.dec = ra_dec
        mount.latitude, mount.longitude = lat_lon
        mount.date = date

        telescope = dome.Telescope(radius, mount)

        axis = telescope.optical_axis

        self.assertAlmostEqual(axis.x, expected_axis.x, delta=1)
        self.assertAlmostEqual(axis.y, expected_axis.y, delta=1)
        self.assertAlmostEqual(axis.z, expected_axis.z, delta=1)
