import math
from datetime import datetime, timezone

from . import geometry


class Telescope:
    def __init__(self, diameter, mount):
        self.diameter = diameter
        self.mount = mount

    @property
    def optical_center(self):
        ra_vector = geometry.Vector.by_angles(self.mount.ra, self.mount.latitude, self.diameter/2 + self.mount.ra_axis_offset)
        center = self.mount.center.add_vector(ra_vector)
        return center

    @property
    def optical_axis(self):
        alt, az = self.mount.get_alt_az()
        return geometry.Vector.by_angles(az, alt, 1)


class Mount:
    def __init__(self, ra_axis_offset, x_offset=0, y_offset=0, z_offset=0):
        self.center = geometry.Point(x_offset, y_offset, z_offset)
        self.ra_axis_offset = ra_axis_offset

        self.latitude = 0
        self.longitude = 0
        self.ra = 0
        self.dec = 0
        self.date = datetime.utcnow()

    @property
    def lst(self):
        utcdate = self.date.replace(tzinfo=timezone.utc)
        lon = self.longitude
        j2000 = datetime(year=2000, month=1, day=1, hour=12)
        time_diff = abs(utcdate.timestamp() - j2000.timestamp())
        day_offset = math.ceil(time_diff / (3600 * 24))
        lst = (100.46 + (0.985647 * day_offset) + lon + (15 * (utcdate.hour + (utcdate.minute / 60.0))) + 360) % 360
        return lst

    def get_alt_az(self):
        lat = self.latitude
        Dec = self.dec
        RA = self.ra

        HA = (self.lst - RA + 360) % 360

        x = math.cos(HA * (math.pi / 180.0)) * math.cos(Dec * (math.pi / 180.0))
        y = math.sin(HA * (math.pi / 180.0)) * math.cos(Dec * (math.pi / 180.0))
        z = math.sin(Dec * (math.pi / 180.0))

        xhor = x * math.cos((90.0 - lat) * (math.pi / 180.0)) - z * math.sin((90.0 - lat) * (math.pi / 180.0))
        yhor = y
        zhor = x * math.sin((90.0 - lat) * (math.pi / 180.0)) + z * math.cos((90.0 - lat) * (math.pi / 180.0))

        az = math.atan2(yhor, xhor) * (180.0 / math.pi) + 180.0
        alt = math.asin(zhor) * (180.0 / math.pi)

        return alt, az


class Dome:
    north = geometry.Vector(0, 1, 0)

    def __init__(self, radius, telescope, x_offset=0, y_offset=0, z_offset=0):
        self.center = geometry.Point(x_offset, y_offset, z_offset)
        self.radius = radius
        self.telescope = telescope

    def get_azimuth(self):
        sphere = geometry.Sphere(self.center, self.radius)
        axis = self.telescope.optical_axis
        intersections = sphere.intersect_with_line(axis)

        angles = (
            geometry.Angle(
                axis,
                geometry.Vector.by_points(self.center, intersection)
            )
            for intersection in intersections
        )

        dome_vector = angles[0].vector2 if angles[0].to_abs_radians() < angles[1].to_abs_radians() else angles[1].vector2
        north_vector = self.center.add_vector(self.north)

        dome_angle = geometry.Angle(dome_vector, north_vector)

        return dome_angle.to_radians()
