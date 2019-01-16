import math


class Point:
    def __init__(self, x, y, z):
        self.x = x
        self.y = y
        self.z = z

    def add_vector(self, vector):
        return Point(self.x + vector.x, self.y + vector.y, self.z + vector.z)


class Vector(Point):
    @classmethod
    def by_angles(cls, a, b, length):
        x = length * math.cos(b) * math.sin(a)
        y = length * math.cos(b) * math.cos(a)
        z = length * math.sin(b)
        return cls(x, y, z)

    @classmethod
    def by_points(cls, p1, p2):
        return cls(
            p2.x - p1.x,
            p2.y - p1.y,
            p2.z - p1.z,
        )

    @property
    def length(self):
        return math.sqrt(self.x ** 2 + self.y ** 2 + self.z ** 2)

    def normalize(self):
        l = self.length
        return Vector(
            self.x / l,
            self.y / l,
            self.z / l
        )


class Line:
    def __init__(self, point, vector):
        self.point = point
        self.vector = vector

    @property
    def second_point(self):
        return self.point.add_vector(self.vector)


class Angle:
    def __init__(self, vector1, vector2):
        self.vector1 = vector1
        self.vector2 = vector2

    def to_radians(self):
        v1 = self.vector1
        v2 = self.vector2
        cos = (v1.x * v2.x + v1.y * v2.y + v1.z * v2.z) / (v1.length * v2.length)
        return math.acos(cos)

    def to_abs_radians(self):
        rads = abs(self.to_radians())
        if rads > math.pi:
            rads = 2 * math.pi - rads
        return rads


class Sphere:
    def __init__(self, center, radius):
        self.center = center
        self.radius = radius

    def intersect_with_line(self, line):
        A = line.vector.x ** 2 + line.vector.y ** 2 + line.vector.z ** 2
        B = 2.0 * (line.point.x * line.vector.x
                   + line.point.y * line.vector.y
                   + line.point.z * line.vector.z
                   - line.vector.x * self.center.x
                   - line.vector.y * self.center.y
                   - line.vector.z * self.center.z)
        C = line.point.x ** 2 \
            - 2 * line.point.x * self.center.x \
            + self.center.x ** 2 \
            + line.point.y ** 2 \
            - 2 * line.point.y * self.center.y\
            + self.center.y ** 2 \
            + line.point.z ** 2 \
            - 2 * line.point.z * self.center.z \
            + self.center.z ** 2 \
            - self.radius ** 2

        D = B * B - 4 * A * C

        if abs(D) < 0:
            return ()

        t1 = (-B - math.sqrt(D)) / (2.0 * A)

        p1 = Point(line.point.x * (1 - t1) + t1 * line.second_point.x,
                   line.point.y * (1 - t1) + t1 * line.second_point.y,
                   line.point.z * (1 - t1) + t1 * line.second_point.z
                   )

        if abs(D) <= 0.000001:
            return p1,

        t2 = (-B + math.sqrt(D)) / (2.0 * A)

        p2 = Point(line.point.x * (1 - t2) + t2 * line.second_point.x,
                   line.point.y * (1 - t2) + t2 * line.second_point.y,
                   line.point.z * (1 - t2) + t2 * line.second_point.z
                   )

        return p1, p2
