"""Finger-tight threaded closure for the desiccant box."""

from direct_interfaces import box, one
from desiccant_interface import THREAD, cylinder, helix, place_at_port
from spindle import thread_profiles
import cadquery as cq


def build():
    male_profile, _, _ = thread_profiles(THREAD)
    # Cap seats on a flat annulus. Three radial ribs stand proud of the cap into the recess.
    core = cylinder(THREAD['root_radius'], -0.11, 4.5)
    tooth = helix(male_profile, 0.35, 4.5)
    tip = cq.Solid.makeCone(8.15, 6.35, 1.05, cq.Vector(0, 0, 3.45))
    core = core.fuse(tooth).intersect(cylinder(8.2, -0.2, 3.46).fuse(tip))
    cap = cylinder(9.3, -1.72, 0).fuse(core)
    for angle in [0, 120, 240]:
        rib = box(0, 8.6, -1.05, 1.05, -3.58, -1.62).rotate((0, 0, 0), (0, 0, 1), angle)
        cap = cap.fuse(rib)
    cap = one(cap.clean(), 'three-spoke refill cap')
    return place_at_port(cap)
