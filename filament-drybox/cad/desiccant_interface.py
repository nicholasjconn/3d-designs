"""Dimensions shared by the printed desiccant box and its refill cap."""

import cadquery as cq

from spindle import _helical

WIDTH = 80.4
INNER, OUTER = 65.35, 95.7
PORT_Y, SEAT_Z = 11.5, 69.5
PITCH = 2.4
THREAD = dict(
    root_radius=6.85,
    major_radius=8.05,
    radial_clearance=0.28,
    crest_width=0.48,
    flank_clearance=0.15,
)


def cylinder(radius, z0, z1):
    return cq.Solid.makeCylinder(radius, z1 - z0, cq.Vector(0, 0, z0))


def place_at_port(shape):
    return shape.translate((0, PORT_Y, SEAT_Z))


def helix(profile, z0, z1):
    return _helical(profile, PITCH, z0, z1, 0, 0, False).rotate((0, 0, 0), (0, 1, 0), -90)
