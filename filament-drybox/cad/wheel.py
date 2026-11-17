"""One-piece proposed external handwheel; millimetres, axle along X.

The wall-facing magnet-cup fronts are x=0. Purchased magnets are excluded.
This is concept CAD, not released or tolerance-qualified fabrication geometry.
"""
import math
import json
from pathlib import Path

import cadquery as cq

PARAMETERS = json.loads(Path(__file__).with_name('wheel.json').read_text())
# The magnet pattern and cups must match the disc's, so both read stand.json's shared magnet spec.
MAGNETS = json.loads(Path(__file__).with_name('stand.json').read_text())['magnets']


def cylinder(radius, start, length, y=0, z=0):
    return cq.Solid.makeCylinder(radius, length, cq.Vector(start, y, z), cq.Vector(1, 0, 0))


def annulus(inner, outer, start, length, y=0, z=0):
    return cylinder(outer, start, length, y, z).cut(cylinder(inner, start, length, y, z))


def magnet_centers():
    m = MAGNETS
    if m['count'] != PARAMETERS['spoke_count']:
        raise ValueError('wheel spokes run through the magnet cups: spoke_count must equal the magnet count')
    return [(m['pitch_radius'] * math.cos(i * 2 * math.pi / m['count']),
             m['pitch_radius'] * math.sin(i * 2 * math.pi / m['count'])) for i in range(m['count'])]


def build():
    p = PARAMETERS
    radius = p['outside_diameter_mm'] / 2
    start, thickness = p['structural_front_offset_mm'], p['structural_thickness_mm']
    body = annulus(radius - p['rim_radial_width_mm'], radius, start, thickness)
    body = body.fuse(cylinder(p['hub_radius_mm'], 0, p['cup_back_mm']))
    for i, (y, z) in enumerate(magnet_centers()):
        spoke = cq.Solid.makeBox(thickness, p['spoke_end_radius_mm'], p['spoke_width_mm'],
                                cq.Vector(start, 0, -p['spoke_width_mm'] / 2))
        spoke = spoke.rotate((0, 0, 0), (1, 0, 0), i * 360 / MAGNETS['count'])
        body = body.fuse(spoke)
        body = body.fuse(cylinder(MAGNETS['cup_outer_radius'], 0, p['cup_back_mm'], y, z))
    body = body.fuse(cylinder(p['knob_radius_mm'], p['knob_front_mm'], p['knob_length_mm'],
                              p['knob_center_radius_mm'], 0))
    # Cut after union so spokes never obstruct a magnet pocket.
    for y, z in magnet_centers():
        body = body.cut(cylinder(MAGNETS['pocket_radius'], MAGNETS['front_cover'],
                                  max(p['cup_back_mm'], start + thickness) - MAGNETS['front_cover'] + 1, y, z))
    return body.clean()
