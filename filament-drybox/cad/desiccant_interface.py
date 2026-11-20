"""Shared geometry for the desiccant refill parts."""

import cadquery as cq

from spindle import _helical

WIDTH = 80.4
INNER, OUTER = 65.35, 95.7
VENT_WIDTH_MM = 2.0
STANDARD_VENT_LENGTH_MM = 8.0
PORT_Y, SEAT_Z = 11.5, 69.5
PITCH = 2.4
THREAD = dict(
    root_radius=6.85,
    major_radius=8.05,
    radial_clearance=0.28,
    crest_width=0.48,
    flank_clearance=0.15,
)


def vent_profile(plane, x, center, length=STANDARD_VENT_LENGTH_MM):
    half = VENT_WIDTH_MM / 2
    start, end = center - length / 2, center + length / 2
    points = [(x-half, start+half), (x, start), (x+half, start+half),
              (x+half, end-half), (x, end), (x-half, end-half)]
    return cq.Workplane(plane).polyline(points).close().val()


def cylinder(radius, z0, z1):
    return cq.Solid.makeCylinder(radius, z1 - z0, cq.Vector(0, 0, z0))


def place_at_port(shape):
    return shape.translate((0, PORT_Y, SEAT_Z))


def helix(profile, z0, z1):
    return _helical(profile, PITCH, z0, z1, 0, 0, False).rotate((0, 0, 0), (0, 1, 0), -90)
