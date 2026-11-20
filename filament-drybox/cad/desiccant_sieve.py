"""Cup-top sieve with matching box vents and a spout for the retained beads."""

import cadquery as cq

from desiccant_interface import STANDARD_VENT_LENGTH_MM, VENT_WIDTH_MM, vent_profile
from direct_interfaces import one

FLOOR_HEIGHT_MM = 1.6
LIP_DIAMETER_MM = 109.0
HEIGHT_MM = 23.1
SPOUT_EXIT_X_MM = 66.5
SPOUT_WIDTH_MM = 16.0


def crosswise_prism(points, half_width):
    wire = cq.Workplane('XZ').polyline(points).close().val()
    return cq.Solid.extrudeLinear(wire, [], cq.Vector(0, 2*half_width, 0)).translate((0,-half_width,0))


def pour_spout(cup):
    # Continue the inside wall's 45° slope through one opening in the rim.
    inner_floor = lambda x: x - (33.5 - FLOOR_HEIGHT_MM)
    start, end = 53.1, SPOUT_EXIT_X_MM
    a, b = inner_floor(start), inner_floor(end)
    half_width = SPOUT_WIDTH_MM/2
    ramp = crosswise_prism([(start,a-1.5), (end,b-1.5), (end,b+3.2), (start,a+3.2)],
                           half_width+2.2)
    cut_start, cut_end = start-5, end+.2
    channel = crosswise_prism([(cut_start,inner_floor(cut_start)), (cut_end,inner_floor(cut_end)),
                              (cut_end,b+5), (cut_start,b+5)], half_width)
    return cup.fuse(ramp).cut(channel)


def screen_slots():
    # Keep the slot tips away from the floor-wall junction. Stagger the rows
    # and run the length of each slot toward the pouring spout.
    openings = []
    half_width = VENT_WIDTH_MM/2
    half_length = STANDARD_VENT_LENGTH_MM/2
    for row in range(-10, 11):
        y = row*3.2
        for column in range(-4, 5):
            x = (column+.5*(row % 2))*9.5
            tip = (abs(x)+half_length)**2 + y*y
            corner = (abs(x)+half_length-half_width)**2 + (abs(y)+half_width)**2
            if max(tip,corner) > 32.0**2:
                continue
            wire = vent_profile('XY', y, -x).rotate((0,0,0),(0,0,1),90)
            openings.append(cq.Solid.extrudeLinear(wire,[],cq.Vector(0,0,FLOOR_HEIGHT_MM+.2))
                            .translate((0,0,-.1)))
    return cq.Compound.makeCompound(openings)


def build():
    # The 45° underside of the broad lip centers on a range of cup openings.
    # The perforated floor remains below the rim when the sieve is seated.
    lip_radius = LIP_DIAMETER_MM / 2
    cup_profile = [
        (0, 0), (35, 0), (35, FLOOR_HEIGHT_MM), (lip_radius, 21.1),
        (lip_radius, HEIGHT_MM), (lip_radius - 1.5, HEIGHT_MM),
        (lip_radius - 1.5, 21.1), (33.5, FLOOR_HEIGHT_MM), (0, FLOOR_HEIGHT_MM),
    ]
    cup = cq.Workplane('XZ').polyline(cup_profile).close().revolve(360, (0, 0), (0, 1)).val()
    return one(pour_spout(cup).cut(screen_slots()), 'desiccant bead sieve')
