"""Flush threaded closure with a blind coin slot."""

from direct_interfaces import box, one
from desiccant_interface import (
    CAP_HEAD_RADIUS_MM, CAP_HEAD_THICKNESS_MM, cylinder, place_at_port, refill_stem,
)

SLOT_LENGTH_MM = 12.8
SLOT_WIDTH_MM = 2.2
SLOT_DEPTH_MM = 1.65


def build():
    head_face = -CAP_HEAD_THICKNESS_MM
    cap = cylinder(CAP_HEAD_RADIUS_MM, head_face, 0).fuse(refill_stem())
    # The solid stem backs the entire floor of the slot.
    slot = box(
        -SLOT_LENGTH_MM / 2, SLOT_LENGTH_MM / 2,
        -SLOT_WIDTH_MM / 2, SLOT_WIDTH_MM / 2,
        head_face - 0.1, head_face + SLOT_DEPTH_MM,
    )
    return place_at_port(one(cap.cut(slot), 'coin-slot refill cap'))
