#!/usr/bin/env python3
"""One-piece side-loading PLA filament clip, printed in its open pose.

The circular leaf changes curvature in XY; this is a kinematic geometry and
bounded strain screen, not contact mechanics or PLA strength qualification.
Only the open pose is a fabrication input. The nominal closed reference has
touching latch faces and a deliberately interfering filament gap.
"""

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path

import cadquery as cq

HERE = Path(__file__).resolve().parent
CONFIG_PATH = HERE / "clip.json"


def load_config(path=CONFIG_PATH):
    with Path(path).open() as handle:
        config = json.load(handle)
    with (HERE / "outlet.json").open() as handle:
        outlet = json.load(handle)
    for label, actual, expected in (
        ("cap bore diameter", config["interfaces"]["cap_bore_diameter_mm"],
         outlet["cap"]["bore_diameter_mm"]),
        ("filament diameter", config["filament_diameter_mm"],
         outlet["tail"]["filament_diameter_mm"]),
        ("clip axial height", config["axial_width_mm"],
         outlet["tail"]["clip_height_mm"]),
    ):
        if actual != expected:
            raise ValueError(
                f"Clip {label} {actual} mm differs from canonical outlet.json "
                f"{expected} mm; reconcile the interface before rebuilding the clip."
            )
    return config


def _geometry(c, opening_deg):
    h = c["hinge"]
    yc = (c["jaw_gap_mm"] + c["jaw_thickness_mm"]) / 2
    radius = h["closed_neutral_radius_mm"]
    if not 0 < yc < radius or not 0 <= opening_deg <= h["opening_deg"]:
        raise ValueError("Invalid jaw/hinge radius or opening angle")
    a0 = -math.asin(yc / radius)
    closed_sweep = 2 * math.pi + 2 * a0
    length = radius * closed_sweep
    sweep = closed_sweep - math.radians(opening_deg)
    r = length / sweep
    start = (c["jaw_root_x_mm"], -yc)
    center = (start[0] - r * math.cos(a0), start[1] - r * math.sin(a0))
    end = (center[0] + r * math.cos(a0 - sweep),
           center[1] + r * math.sin(a0 - sweep))
    return {"yc": yc, "a0": a0, "sweep": sweep, "radius": r,
            "length": length, "center": center, "end": end,
            "closed_root": (c["jaw_root_x_mm"], yc)}


def _polygon(points, width):
    return cq.Workplane("XY").polyline(points).close().extrude(width).val()


def _box(x0, x1, y0, y1, width):
    return cq.Solid.makeBox(x1 - x0, y1 - y0, width, cq.Vector(x0, y0, 0))


def _join(parts):
    shape = parts[0]
    for part in parts[1:]:
        shape = shape.fuse(part)
    shape = shape.clean()
    if not shape.isValid() or len(shape.Solids()) != 1:
        raise ValueError("Clip must be one valid native solid")
    return shape


def components(config=None, opening_deg=None):
    """Return lower jaw, deformed circular leaf and rigid upper jaw reference.

    The root/tongue/jaw geometry is actual material, not rendered surfaces.
    Component separation serves collision checks; they overlap at their roots.
    """
    c = config or load_config()
    angle = c["hinge"]["opening_deg"] if opening_deg is None else opening_deg
    g = _geometry(c, angle)
    w, t, x0, x1 = (c[k] for k in
                    ("axial_width_mm", "jaw_thickness_mm", "jaw_root_x_mm", "jaw_end_x_mm"))
    yc, l = g["yc"], c["latch"]
    lower = _join([
        _box(x0, x1, -yc - t / 2, -yc + t / 2, w),
        cq.Solid.makeCylinder(c["root_blend_radius_mm"], w, cq.Vector(x0, -yc, 0)),
        _polygon([(l["stem_inner_x_mm"], -yc + t / 2),
                  (l["stem_outer_x_mm"], -yc + t / 2),
                  (l["stem_outer_x_mm"], l["catch_ramp_top_y_mm"]),
                  (l["catch_ramp_top_x_mm"], l["catch_ramp_top_y_mm"]),
                  (l["catch_tip_x_mm"], l["catch_tip_top_y_mm"]),
                  (l["catch_tip_x_mm"], l["catch_bottom_y_mm"]),
                  (l["stem_inner_x_mm"], l["catch_bottom_y_mm"])], w),
    ])
    outer = l["arm_inner_x_mm"] + l["arm_thickness_mm"]
    upper = _join([
        _box(x0, x1, yc - t / 2, yc + t / 2, w),
        cq.Solid.makeCylinder(c["root_blend_radius_mm"], w, cq.Vector(x0, yc, 0)),
        _box(x1 - t / 2, x1 + t / 2, yc - t / 2, l["arm_root_y_mm"] + t / 2, w),
        _box(x1 - t / 2, outer, l["arm_root_y_mm"] - t / 2, l["arm_root_y_mm"] + t / 2, w),
        _box(l["arm_inner_x_mm"], outer, l["hook_bottom_y_mm"], l["arm_root_y_mm"] + t / 2, w),
        _box(l["hook_inner_x_mm"], outer, l["hook_bottom_y_mm"], l["hook_top_y_mm"], w),
    ])
    root = g["closed_root"]
    upper = upper.rotate((root[0], root[1], 0), (root[0], root[1], 1), angle)
    upper = upper.translate((g["end"][0] - root[0], g["end"][1] - root[1], 0))
    ri = g["radius"] - c["hinge"]["thickness_mm"] / 2
    ro = g["radius"] + c["hinge"]["thickness_mm"] / 2
    if ri <= 0:
        raise ValueError("Hinge has nonpositive inside radius")
    def point(r, fraction):
        a = g["a0"] - g["sweep"] * fraction
        return (g["center"][0] + r * math.cos(a), g["center"][1] + r * math.sin(a))
    leaf = (cq.Workplane("XY").moveTo(*point(ro, 0))
            .threePointArc(point(ro, .5), point(ro, 1))
            .lineTo(*point(ri, 1)).threePointArc(point(ri, .5), point(ri, 0))
            .close().extrude(w).val())
    return {"lower": lower, "leaf": leaf, "upper": upper}


def build(config=None, *, pose="open"):
    """Build one native body. Use pose='open' for printing."""
    c = config or load_config()
    if pose not in ("open", "closed"):
        raise ValueError("pose must be 'open' or 'closed'")
    angle = 0 if pose == "closed" else c["hinge"]["opening_deg"]
    body = _join(list(components(c, angle).values()))
    g = _geometry(c, angle)
    roots = [(c["jaw_root_x_mm"], -g["yc"]), g["end"]]
    # Blend only the leaf/jaw root junctions. Keep latch engagement and the
    # straight smooth jaw faces unchanged; their dimensions define function.
    selected = []
    for edge in body.Edges():
        bb, mid = edge.BoundingBox(), edge.Center()
        if bb.zlen > c["axial_width_mm"] - .01 and bb.xlen < 1e-5 and bb.ylen < 1e-5:
            if min(math.hypot(mid.x - x, mid.y - y) for x, y in roots) < 1.0:
                selected.append(edge)
    if not selected:
        raise ValueError("No leaf/jaw root junctions found for filleting")
    body = cq.Workplane(obj=body).newObject(selected).fillet(c["root_junction_fillet_mm"]).val()
    if not body.isValid() or len(body.Solids()) != 1:
        raise ValueError("Root fillets did not retain one valid clip solid")
    return body


def checks(config=None):
    """Geometry, interface and elementary strain screens; never a force result."""
    c = config or load_config()
    g = _geometry(c, 0)
    h, l = c["hinge"], c["latch"]
    delta = math.radians(h["opening_deg"])
    effective = g["length"] - 2 * h["root_exclusion_each_mm"]
    interference = c["filament_diameter_mm"] - c["jaw_gap_mm"]
    # Fixed-fixed center-deflection strain: 12*t*deflection/span^2.
    # Each jaw takes half the nominal diametral interference, assuming the
    # filament is rigid. This does not establish a contact or gripping force.
    span = c["jaw_end_x_mm"] - (c["jaw_root_x_mm"] + c["root_blend_radius_mm"])
    jaw_strain = 12 * c["jaw_thickness_mm"] * interference / 2 / span ** 2
    latch_length = l["arm_root_y_mm"] - l["hook_top_y_mm"]
    latch_deflection = l["catch_tip_x_mm"] - l["hook_inner_x_mm"] + l["snap_extra_clearance_mm"]
    latch_strain = 1.5 * l["arm_thickness_mm"] * latch_deflection / latch_length ** 2
    section_i = c["axial_width_mm"] * c["jaw_thickness_mm"] ** 3 / 12
    force_bounds = [factor * modulus * section_i * (interference / 2) / span ** 3
                    for factor in (48, 192) for modulus in (1500, 3500)]
    result = {"scope": "Geometry and elementary elastic screens only; no strength, fatigue, grip force or sustained retention qualification.",
              "neutral_leaf_length_mm": g["length"],
              "closed_leaf_sweep_deg": math.degrees(g["sweep"]),
              "hinge_uniform_curvature_strain": h["thickness_mm"] * delta / (2 * g["length"]),
              "hinge_shortened_active_length_screen_strain": h["thickness_mm"] * delta / (2 * effective),
              "hinge_screen_limit": "Local root strain can exceed both estimates; no PLA allowable is asserted.",
              "nominal_filament_interference_mm": interference,
              "jaw_fixed_fixed_rigid_filament_screen": {"span_mm": span, "each_deflection_mm": interference / 2, "outer_fiber_strain": jaw_strain},
              "jaw_force_sensitivity_only": {"assumed_E_MPa": [1500, 3500], "end_conditions": "Simply supported to fixed-fixed center load, each jaw",
                  "normal_force_N": [min(force_bounds), max(force_bounds)],
                  "limit": "Assumed modulus range, not sourced printed PLA properties; no contact/grip prediction. Filament compliance and joint flexibility lower load. TPU can indent or creep; inspect the first PLA sample for marks."},
              "latch_cantilever_screen": {"length_mm": latch_length, "tip_deflection_mm": latch_deflection, "outer_fiber_strain": latch_strain, "limit": "Straight beam estimate; ramp contact, root concentration and load direction unqualified."},
              "poses": {}, "motion_samples": []}
    cap_r = c["interfaces"]["cap_bore_diameter_mm"] / 2
    cap_cylinder = cq.Solid.makeCylinder(cap_r, c["axial_width_mm"] + 2, cq.Vector(0, 0, -1))
    for pose in ("open", "closed"):
        s = build(c, pose=pose)
        bb = s.BoundingBox()
        result["poses"][pose] = {"valid": s.isValid(), "solid_count": len(s.Solids()),
            "volume_mm3": s.Volume(), "bounds_mm": [[bb.xmin, bb.ymin, bb.zmin], [bb.xmax, bb.ymax, bb.zmax]]}
        if pose == "closed":
            outside = sum(v.Volume() for v in s.cut(cap_cylinder).Solids())
            result["poses"][pose]["outside_cap_bore_mm3"] = outside
            if outside > 1e-5:
                raise ValueError("Closed clip exceeds the cap bore")
    for angle in (25, 20, 15, 10, 5, 4, 3, 2, 1, 0):
        p = components(c, angle)
        overlap = sum(v.Volume() for v in p["lower"].intersect(p["upper"]).Solids())
        result["motion_samples"].append({"opening_deg": angle, "rigid_jaw_latch_overlap_mm3": overlap,
            "meaning": "Snap-contact overlap requires tongue deflection; roots remain joined by the flexing leaf."})
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, default=CONFIG_PATH)
    parser.add_argument("--output", type=Path, default=HERE.parents[1] / "build" / "filament-drybox" / "clip")
    args = parser.parse_args()
    c = load_config(args.config)
    args.output.mkdir(parents=True, exist_ok=True)
    result = checks(c)
    for pose in ("open", "closed"):
        s = build(c, pose=pose)
        cq.exporters.export(s, str(args.output / f"clip-{pose}.step"))
        if pose == "open":
            if not s.exportStl(str(args.output / "clip-open.stl"), tolerance=.02, angularTolerance=.1, relative=False):
                raise RuntimeError("Open clip STL export failed")
    (args.output / "checks.json").write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
