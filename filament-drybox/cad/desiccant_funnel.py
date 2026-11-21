"""Screw-in funnel for the desiccant refill port."""

import cadquery as cq

from desiccant_interface import refill_stem
from direct_interfaces import one

SEAT_HEIGHT_MM = 28.0
THROAT_RADIUS_MM = 5.65
THREAD_LEAD_START_MM = 5.5


def build():
    # Wide mouth down. The flat shoulder seats against the box like its cap.
    outside = [
        (0, 0), (28, 0), (28, 1), (8.4, 23), (8.4, 26.8),
        (9.3, 27.7), (9.3, SEAT_HEIGHT_MM), (0, SEAT_HEIGHT_MM),
    ]
    passage = [
        (0, -0.1), (26.75, -0.1), (26.75, 0), (7.15, 22.7),
        (THROAT_RADIUS_MM, 27.5), (THROAT_RADIUS_MM, 35), (0, 35),
    ]
    body = cq.Workplane('XZ').polyline(outside).close().revolve(360, (0, 0), (0, 1)).val()
    opening = cq.Workplane('XZ').polyline(passage).close().revolve(360, (0, 0), (0, 1)).val()
    # Reach through the port's entrance taper before the shoulder seats.
    # Keep the same pitch and tooth as the existing box and cap.
    stem = refill_stem(lead_start=THREAD_LEAD_START_MM).translate((0, 0, SEAT_HEIGHT_MM))
    return one(body.fuse(stem).cut(opening).clean(), 'threaded refill funnel')
