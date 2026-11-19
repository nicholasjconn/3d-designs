"""Flat vented box for the frozen T-key stand. X axle, Y up, Z outward."""

import math

import cadquery as cq
import numpy as np

from direct_interfaces import box, one
from desiccant_interface import INNER, OUTER, SEAT_Z, THREAD, WIDTH, cylinder, helix, place_at_port
from spindle import thread_profiles

HALF = WIDTH / 2
WALL, FLOOR, ROOF = 1.6, 1.8, 1.8
AXIS_Y, ROOF_RADIUS = 104.0, 106.0


def roof(z, depth=0):
    # Concentric true circular roof, then a short flat which removes the outer tip.
    radius = ROOF_RADIUS
    cap = AXIS_Y - math.sqrt(radius**2 - 92.0**2) - depth
    return min(AXIS_Y - math.sqrt((radius + depth) ** 2 - z * z), cap)


def roof_edges(z0, z1, x, depth=0, reverse=False):
    radius = ROOF_RADIUS + depth
    cap = roof(OUTER, depth)
    transition = math.sqrt(radius**2 - (AXIS_Y - cap) ** 2)
    zs = [z0] + ([transition] if z0 < transition < z1 else []) + [z1]
    if reverse:
        zs = zs[::-1]
    edges = []
    for a, b in zip(zs, zs[1:]):
        v = lambda z: cq.Vector(x, roof(z, depth), z)
        if min(a, b) >= transition - 1e-8:
            edges.append(cq.Edge.makeLine(v(a), v(b)))
        else:
            edges.append(cq.Edge.makeThreePointArc(v(a), v((a + b) / 2), v(b)))
    return edges


def roof_prism(z0, z1, x0, x1, top_depth=0, bottom_y=0, bottom_depth=None):
    # Depth is a normal offset on the arc, and vertical on its outer flat.
    bottom = lambda z: bottom_y if bottom_depth is None else roof(z, bottom_depth)
    v = lambda z, y: cq.Vector(x0, y, z)
    edges = (
        [cq.Edge.makeLine(v(z0, bottom(z0)), v(z1, bottom(z1)))]
        if bottom_depth is None
        else roof_edges(z0, z1, x0, bottom_depth)
    )
    edges.append(cq.Edge.makeLine(v(z1, bottom(z1)), v(z1, roof(z1, top_depth))))
    edges += roof_edges(z0, z1, x0, top_depth, True)
    edges.append(cq.Edge.makeLine(v(z0, roof(z0, top_depth)), v(z0, bottom(z0))))
    return cq.Solid.extrudeLinear(cq.Wire.assembleEdges(edges), [], cq.Vector(x1 - x0, 0, 0))


def prism_yz(points, x0, x1):
    w = cq.Workplane('YZ').polyline([(y, z) for z, y in points]).close().val()
    return cq.Solid.extrudeLinear(w, [], cq.Vector(x1 - x0, 0, 0)).translate((x0, 0, 0))


def hex_slot_face_x(x0, x1, z, y, width, height):
    return prism_yz(
        [
            (z - width / 2, y - height / 2 + width / 2),
            (z, y - height / 2),
            (z + width / 2, y - height / 2 + width / 2),
            (z + width / 2, y + height / 2 - width / 2),
            (z, y + height / 2),
            (z - width / 2, y + height / 2 - width / 2),
        ],
        x0,
        x1,
    )


def mounting_key(x):
    # The mating key dimensions match the frozen sockets in direct_stand.py.
    tip, shoulder, end = 59.8, 62.0, 67.2
    head, neck = 5.0, 3.0
    wire = (
        cq.Workplane('XZ')
        .polyline(
            [
                (x - head, tip),
                (x + head, tip),
                (x + head, shoulder),
                (x + neck, shoulder),
                (x + neck, end),
                (x - neck, end),
                (x - neck, shoulder),
                (x - head, shoulder),
            ]
        )
        .close()
        .val()
    )
    return cq.Solid.extrudeLinear(wire, [], cq.Vector(0, 2.4, 0))


def vent_profile(plane, x, center, length):
    start, end = center - length / 2, center + length / 2
    return (
        cq.Workplane(plane)
        .polyline(
            [
                (x - 1, start + 1),
                (x, start),
                (x + 1, start + 1),
                (x + 1, end - 1),
                (x, end),
                (x - 1, end - 1),
            ]
        )
        .close()
        .val()
    )


def build():
    envelope = roof_prism(INNER, OUTER, -HALF, HALF)
    cavity = roof_prism(INNER + WALL, OUTER - WALL, -HALF + WALL, HALF - WALL, ROOF, FLOOR)
    body = envelope.cut(cavity)
    for x in [-18, 18]:
        body = body.fuse(mounting_key(x))
    # Pocket opens through the upper edge so fingers can reach the cap.
    # Add material inside the shell first so the pocket only communicates through the port.
    port_web = envelope.intersect(box(-14.3, 14.3, 0, 45, INNER, SEAT_Z + 1.8))
    collar = place_at_port(cylinder(10.25, -0.4, 4.75)).intersect(envelope)
    body = body.fuse(port_web, collar)
    body = body.cut(box(-12.5, 12.5, 1.9, 45, INNER - 0.1, SEAT_Z))
    _, female_profile, bore_r = thread_profiles(THREAD)
    bore = cylinder(bore_r, -0.2, 5.3)
    groove = helix(female_profile, -0.2, 4.75)
    lead = cq.Solid.makeCone(8.55, bore_r, 1.42, cq.Vector(0, 0, -0.12))
    body = body.cut(place_at_port(bore.fuse(groove, lead)))

    slots = []
    for z in np.arange(69, 93, 3.2):
        for y in np.arange(7, roof(z - 1, ROOF) - 4, 9.5):
            slots.append(hex_slot_face_x(-HALF - 0.2, HALF + 0.2, float(z), float(y), 2, 8))
    # A uniform grid leaves an uninterrupted flat rim for the refill stance.
    for x in np.linspace(-36.8, 36.8, 24):
        for y, length in [(8, 8), (17.5, 8), (27, 8), (36.5, 8), (46, 6)]:
            profile = vent_profile('XY', float(x), y, length)
            slot = cq.Solid.extrudeLinear(profile, [], cq.Vector(0, 0, WALL + 0.4))
            slots.append(slot.translate((0, 0, OUTER - WALL - 0.2)))
    # Short-face slots open above the eight-millimeter rail. Leave the entire
    # cap web and the lower key land intact.
    for x in [s * a for s in [-1, 1] for a in np.arange(17, HALF - 2, 3.2)]:
        profile = vent_profile('XY', x, 13.6, 8)
        slot = cq.Solid.extrudeLinear(profile, [], cq.Vector(0, 0, WALL + 0.4))
        slots.append(slot.translate((0, 0, INNER - 0.2)))

    # Roof slots open into the chamber. The inner row stops either side of the
    # threaded collar. The outer row stops short of the outer wall.
    for x in np.arange(-35.2, 35.3, 3.2):
        for start, end in [(70.0, 79.8), (82.0, 90.0)]:
            if start < 75 and abs(x) < 16:
                # Resume the short row once the collar and its rim are behind it.
                start = 76.0
            z = (start + end) / 2
            low = roof(start, ROOF) - 1
            profile = vent_profile('XZ', float(x), z, end - start)
            slot = cq.Solid.extrudeLinear(profile, [], cq.Vector(0, 56 - low, 0))
            slots.append(slot.translate((0, low, 0)))
    body = one(body.cut(cq.Compound.makeCompound(slots)), 'threaded desiccant box')
    return body
