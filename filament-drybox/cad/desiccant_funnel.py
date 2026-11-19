"""Small funnel for the drybox's Ø14.26 mm refill port."""

import cadquery as cq


def build():
    # Wide mouth on the bed. At use the 1.1 mm locating tip points down.
    profile = [
        (22.0, 0),
        (22.0, 1),
        (8.4, 17.0),
        (8.4, 22.0),
        (6.75, 22.0),
        (6.75, 23.1),
        (5.65, 23.1),
        (5.65, 21.5),
        (7.15, 16.7),
        (20.75, 0),
    ]
    return cq.Workplane('XZ').polyline(profile).close().revolve(360, (0, 0), (0, 1)).val()
