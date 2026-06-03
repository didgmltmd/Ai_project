from math import acos, degrees, sqrt


Point = tuple[float, float]


def angle_degrees(a: Point, b: Point, c: Point) -> float:
    ba = (a[0] - b[0], a[1] - b[1])
    bc = (c[0] - b[0], c[1] - b[1])
    dot = ba[0] * bc[0] + ba[1] * bc[1]
    mag_ba = sqrt(ba[0] ** 2 + ba[1] ** 2)
    mag_bc = sqrt(bc[0] ** 2 + bc[1] ** 2)
    if mag_ba == 0 or mag_bc == 0:
        return 180.0
    cosine = max(-1.0, min(1.0, dot / (mag_ba * mag_bc)))
    return degrees(acos(cosine))
