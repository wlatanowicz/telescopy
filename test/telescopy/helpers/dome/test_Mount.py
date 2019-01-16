import unittest
from datetime import datetime
from ddt import ddt, data, unpack

from telescopy.helpers import dome
from telescopy.helpers import geometry


@ddt
class TestMount(unittest.TestCase):

    coords = [
        (
            (11.9000, -17.9864),  # ra, dec
            (52.40692, 16.92993),  # lat, lon
            datetime(2019, 1, 16, 16, 30, 00),
            (19.30003, 189.2214),  # expected alt, az
        ),
    ]

    @data(*coords)
    @unpack
    def test_coord_conversion(self, ra_dec, lat_lon, date, expected_alt_az):
        mount = dome.Mount(0)
        mount.ra, mount.dec = ra_dec
        mount.latitude, mount.longitude = lat_lon
        mount.date = date

        alt, az = mount.get_alt_az()

        ex_alt, ex_az = expected_alt_az

        self.assertAlmostEqual(alt, ex_alt, delta=0.2)
        self.assertAlmostEqual(az, ex_az, delta=0.2)
