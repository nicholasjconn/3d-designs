#!/usr/bin/env python3
"""Native concept CAD for the purchased PC4-M10 outlet.

NOT fabrication-ready: purchased fitting thread forms remain unknown.
M16x1.5 and M26x2 retention threads are true helical solids; the purchased
fitting interfaces remain smooth unfinished pilots. Native coordinates are mm.
"""

from __future__ import annotations

import json
import math
from pathlib import Path

import cadquery as cq

HERE = Path(__file__).resolve().parent
CONFIG_PATH = HERE / "outlet.json"

# Display meshes are for the viewer, not for fabrication or metrology.
MESH_TOLERANCE_MM = 0.15
MESH_ANGULAR_RAD = 0.35
UNINTENDED_VOLUME_MM3 = 0.05
# Axial opening of each flank of a female groove cutter. Printed-pair allowance
# only; not an ISO fit class. Male teeth stay on the basic profile.
GROOVE_FLANK_WIDEN_MM = 0.10


def load_config():
    with CONFIG_PATH.open() as handle:
        return json.load(handle)


def basic_height(pitch):
    """Radial height of the ISO 68-1 basic profile: 5/8 of the fundamental triangle."""
    fundamental = pitch * math.sqrt(3) / 2
    return 5 * fundamental / 8


def minor_diameter(major, pitch):
    return major - 2 * basic_height(pitch)


def cylinder(radius, z0, z1):
    if z1 < z0:
        z0, z1 = z1, z0
    height = z1 - z0
    if height <= 0:
        raise ValueError("cylinder height must be positive")
    return cq.Solid.makeCylinder(radius, height, cq.Vector(0, 0, z0), cq.Vector(0, 0, 1))


def cone(r0, r1, z0, z1):
    """Cone with radius r0 at z0 and r1 at z1. z1 must be above z0."""
    if z1 <= z0:
        raise ValueError("cone requires z1 > z0")
    return cq.Solid.makeCone(r0, r1, z1 - z0, cq.Vector(0, 0, z0), cq.Vector(0, 0, 1))


def hex_prism(across_flats, z0, z1):
    """Regular hex prism. across_flats is the distance between parallel faces."""
    if z1 < z0:
        z0, z1 = z1, z0
    across_corners = across_flats / math.cos(math.radians(30))
    return (
        cq.Workplane("XY")
        .polygon(6, across_corners)
        .extrude(z1 - z0)
        .val()
        .translate((0, 0, z0))
    )


def fuse(solids):
    acc = solids[0]
    for solid in solids[1:]:
        acc = acc.fuse(solid)
    try:
        cleaned = acc.clean()
    except Exception:
        cleaned = acc
    if not cleaned.isValid() or len(cleaned.Solids()) != 1:
        raise ValueError("fuse did not produce one valid solid")
    return cleaned


def cut(base, tools):
    acc = base
    for tool in tools:
        acc = acc.cut(tool)
    try:
        cleaned = acc.clean()
    except Exception:
        cleaned = acc
    if not cleaned.isValid() or len(cleaned.Solids()) != 1:
        raise ValueError("cut did not produce one valid solid")
    return cleaned


def tube(outer_radius, inner_radius, z0, z1):
    return cylinder(outer_radius, z0, z1).cut(cylinder(inner_radius, z0 - 0.2, z1 + 0.2))


def thread_tooth(major, pitch, z0, z1, radial_shift=0.0, widen=0.0, phase_origin=None):
    """One helical ISO 68-1 basic tooth occupying [z0, z1].

    CadQuery's Frenet sweep follows the helix only when the profile sits on the
    path start. Building the helix at an absolute Z above the profile leaves
    the tooth near Z = 0, and the minor-diameter core still fills the bounding
    box, so the tooth is built from local Z = 0 and then translated.
    phase_origin is the male thread's z0 in this same frame. A female cutter
    passes it so the groove, not the cutter tooth, lines up with the male tooth.
    """
    height = basic_height(pitch)
    minor_r = major / 2 - height + radial_shift
    crest = pitch / 8
    overlap = 0.12
    half_root = crest / 2 + (height + overlap) * math.tan(math.radians(30))
    outer = major / 2 + radial_shift + (0.05 if radial_shift else 0.0)
    half_crest = crest / 2 + widen
    half_base = half_root + widen
    profile = [
        (minor_r - overlap, -half_base),
        (outer, -half_crest),
        (outer, half_crest),
        (minor_r - overlap, half_base),
    ]
    # CadQuery's Frenet sweep only follows the helix when the profile sits on
    # the path start. Build the tooth from local Z=0, then translate it.
    length = z1 - z0
    if length <= 0:
        raise ValueError("thread tooth length must be positive")
    shift = 0.0 if phase_origin is None else (phase_origin - z0) % pitch
    if shift > pitch / 2:
        shift -= pitch
    start = -pitch / 2 + shift
    while start > -0.2:
        start -= pitch
    path = cq.Wire.makeHelix(
        pitch,
        (length + pitch / 2) - start,
        minor_r,
        center=(0, 0, start),
        dir=(0, 0, 1),
    )
    swept = cq.Workplane("XZ").polyline(profile).close().sweep(path, isFrenet=True).val()
    slab = cylinder(outer + 0.3, 0, length)
    tooth = swept.intersect(slab)
    if not tooth.isValid():
        raise ValueError("thread tooth is invalid")
    return tooth.translate((0, 0, z0))


def count_inside(solid, radius, z, samples=36):
    from OCP.BRepClass3d import BRepClass3d_SolidClassifier
    from OCP.gp import gp_Pnt
    from OCP.TopAbs import TopAbs_IN

    classifier = BRepClass3d_SolidClassifier(solid.wrapped)
    count = 0
    for index in range(samples):
        angle = 2 * math.pi * index / samples
        classifier.Perform(
            gp_Pnt(radius * math.cos(angle), radius * math.sin(angle), z),
            1e-6,
        )
        count += int(classifier.State() == TopAbs_IN)
    return count


def crest_span(solid, major, pitch, z0, z1, samples=36):
    """Crest material at both ends and the middle.

    A helix crosses every height, so the station is fixed rather than searched:
    a search would report a crest from the middle of a truncated tooth. A full
    collar would mark every angle. The minor-diameter core does not reach this
    radius, so a bounding box cannot make this pass.
    """
    if z1 <= z0:
        raise ValueError("crest span requires z1 > z0")
    radius = major / 2 - 0.15
    inset = min(0.45, 0.2 * (z1 - z0))
    found = []
    for z in (z0 + inset, (z0 + z1) / 2, z1 - inset):
        hits = count_inside(solid, radius, z, samples)
        found.append({"z_mm": round(z, 3), "hits": hits, "samples": samples})
        if hits < 1 or hits >= samples:
            raise ValueError(
                f"thread {major}x{pitch} crest span failed at z={z:.3f}: "
                f"{hits}/{samples} at r={radius:.3f}"
            )
    return found


def external_thread(major, pitch, z0, z1):
    height = basic_height(pitch)
    minor_r = major / 2 - height
    core = cylinder(minor_r, z0, z1)
    solid = fuse([core, thread_tooth(major, pitch, z0, z1)])
    box = solid.BoundingBox()
    reached = max(abs(box.xmin), abs(box.xmax), abs(box.ymin), abs(box.ymax))
    if abs(reached - major / 2) > 0.05 or box.zmin < z0 - 0.05 or box.zmax > z1 + 0.05:
        raise ValueError(
            f"external thread {major}x{pitch} bbox r={reached:.3f} z={box.zmin:.3f}..{box.zmax:.3f}"
        )
    # Raises if the helix died before the far end. The bbox check above cannot.
    crest_span(solid, major, pitch, z0, z1)
    return solid


def internal_cutter(major,pitch,z0,z1,clearance,phase_origin,flank_allowance=GROOVE_FLANK_WIDEN_MM):
    """Full-phase female groove, extended before cropping so its entry is complete.

    A sweep started exactly at the mouth omitted one entry quadrant. Seated
    overlap was zero but +0.5 mm/+90deg unscrewing collided near that mouth.
    One extra pitch at either end preserves right-hand phase and completes the
    cutter at all angles; clipping keeps it out of the smooth seal region.
    """
    minor_r=major/2-basic_height(pitch)
    bore=cylinder(minor_r+clearance,z0,z1)
    groove=thread_tooth(major,pitch,z0-pitch,z1+pitch,
                        radial_shift=clearance,widen=flank_allowance,
                        phase_origin=phase_origin)
    groove=groove.intersect(cylinder(major/2+clearance+.5,z0,z1))
    return fuse([bore,groove])


def elliptical_ring(mean_radius, axial_height, radial_width, z_center):
    """Torus of the volume-preserving compressed ellipse. Not a contact result."""
    wire = (
        cq.Workplane("XZ")
        .center(mean_radius, z_center)
        .ellipse(radial_width / 2, axial_height / 2)
        .val()
    )
    face = cq.Face.makeFromWires(wire)
    solid = cq.Solid.revolve(face, 360, cq.Vector(0, 0, 0), cq.Vector(0, 0, 1))
    if not solid.isValid() or len(solid.Solids()) != 1:
        raise ValueError("O-ring solid is invalid")
    return solid


def require_one(solid, name):
    if not solid.isValid() or len(solid.Solids()) != 1:
        raise ValueError(f"{name}: expected one valid native solid, got {len(solid.Solids())}")
    return solid


def make_body(c):
    print("Building body helical retention threads", flush=True)
    st, ct, fl, nk = (c[k] for k in ("stem_thread","cap_thread","flange","seal_neck"))
    base = fuse([external_thread(st["major_diameter_mm"], st["pitch_mm"], *st["z_mm"]),
                 cylinder(fl["diameter_mm"]/2, *fl["z_mm"]),
                 external_thread(ct["major_diameter_mm"], ct["pitch_mm"], *ct["z_mm"]),
                 cylinder(nk["diameter_mm"]/2, *nk["z_mm"])])
    pi, tu = c["purchased_interfaces"],c["tube"]
    oz=pi["outer_pilot_z_mm"]
    tools = [cq.Solid.makeBox(30,50,fl["z_mm"][1]-fl["z_mm"][0],cq.Vector(fl["across_flats_mm"]/2,-25,fl["z_mm"][0])),
             cq.Solid.makeBox(30,50,fl["z_mm"][1]-fl["z_mm"][0],cq.Vector(-30-fl["across_flats_mm"]/2,-25,fl["z_mm"][0])),
             cylinder(tu["body_clearance_bore_mm"]/2,tu["body_clearance_z_mm"][0]-.1,tu["body_clearance_z_mm"][1]),
             cylinder(pi["diameter_mm"]/2,oz[0],oz[1]+.1)]
    rg, wg = c["radial_ring"], c["wall_ring"]
    tools.append(tube(nk["diameter_mm"]/2+1, rg["root_diameter_mm"]/2, *rg["gland_z_mm"]))
    tools.append(tube(wg["gland_outer_radius_mm"], wg["gland_inner_radius_mm"], -.1, wg["gland_depth_mm"]))
    solid=cut(base,tools)
    root_edges=[]
    for edge in solid.Edges():
        bb=edge.BoundingBox()
        if edge.geomType()=="CIRCLE" and abs(bb.zmax-bb.zmin)<1e-6:
            z=(bb.zmin+bb.zmax)/2
            if abs(edge.radius()-rg["root_diameter_mm"]/2)<1e-5 and any(abs(z-target)<1e-5 for target in rg["gland_z_mm"]):
                root_edges.append(edge)
    if len(root_edges)!=2:
        raise ValueError(f"Expected two radial gland root corners, found {len(root_edges)}")
    rounded=solid.fillet(rg["root_corner_radius_mm"],root_edges)
    face_edges=[]
    for edge in rounded.Edges():
        bb=edge.BoundingBox()
        if edge.geomType()=="CIRCLE" and abs(bb.zmax-bb.zmin)<1e-6:
            z=(bb.zmin+bb.zmax)/2
            if abs(z-wg["gland_depth_mm"])<1e-5 and any(abs(edge.radius()-target)<1e-5 for target in [wg["gland_inner_radius_mm"],wg["gland_outer_radius_mm"]]):
                face_edges.append(edge)
    if len(face_edges)!=2:
        raise ValueError(f"Expected two face gland floor corners, found {len(face_edges)}")
    rounded=rounded.fillet(wg["root_corner_radius_mm"],face_edges)
    return require_one(rounded,"body with both glands root radii")


def make_nut(c):
    t, n, st = c["wall_thickness_mm"], c["wall_nut"], c["stem_thread"]
    # Same full sweep domain as the male, then clipped by the nut blank. The
    # inherited fractional phase_origin helper did not preserve actual phase.
    major,pitch = st["major_diameter_mm"],st["pitch_mm"]
    z0,z1=st["z_mm"]
    groove=thread_tooth(major,pitch,z0,z1,radial_shift=c["female_radial_allowance_mm"],
                        widen=c["female_flank_axial_allowance_mm"])
    cutter=fuse([cylinder(minor_diameter(major,pitch)/2+c["female_radial_allowance_mm"],z0,z1),groove])
    return cut(hex_prism(n["across_flats_mm"],-t-n["thickness_mm"],-t),[cutter])


def make_cap(c):
    print("Building cap with real female helix and smooth seal lead-in", flush=True)
    cap,ct=c["cap"],c["cap_thread"]
    z0,z1=ct["z_mm"]
    solid = cut(cylinder(cap["outside_diameter_mm"]/2,cap["mouth_z_mm"],cap["top_z_mm"]),[
        internal_cutter(ct["major_diameter_mm"],ct["pitch_mm"],z0,z1,
                        c["female_radial_allowance_mm"],z0,c["female_flank_axial_allowance_mm"]),
        cone(cap["lead_in_mouth_diameter_mm"]/2,cap["bore_diameter_mm"]/2,*cap["lead_in_z_mm"]),
        cylinder(cap["bore_diameter_mm"]/2,cap["lead_in_z_mm"][1],cap["blind_z_mm"])])

    edges=[]
    for edge in solid.Edges():
        bb=edge.BoundingBox()
        if edge.geomType()!="CIRCLE" or abs(bb.zmax-bb.zmin)>1e-6:
            continue
        radius=edge.radius(); z=(bb.zmin+bb.zmax)/2
        targets=zip(cap["lead_in_z_mm"],[cap["lead_in_mouth_diameter_mm"]/2,cap["bore_diameter_mm"]/2])
        if any(abs(z-tz)<1e-5 and abs(radius-tr)<1e-5 for tz,tr in targets):
            edges.append(edge)
    if len(edges)!=2:
        raise ValueError(f"Expected two cap lead-in circles, found {len(edges)}")
    rounded=solid.fillet(cap["lead_in_edge_radius_mm"],edges)
    return require_one(rounded,"cap with rounded seal entry")


def fitting_envelope(c):
    # Another-brand dimensioned drawing, never actual purchased fitting CAD.
    f=c["fitting_envelope"]; length=f["reference_thread_length_mm"]
    proud=f["reference_total_length_mm"]-length
    seat=c["purchased_interfaces"]["outer_pilot_z_mm"][1]
    # Undimensioned transitions are deliberately simple envelope assumptions.
    local=fuse([cylinder(f["purchased_thread_envelope_diameter_mm"]/2,-length,0),hex_prism(f["reference_hex_af_mm"],0,4),
                cylinder(4.5,4,proud-2),cylinder(f["reference_collet_diameter_mm"]/2,proud-2,proud)])
    local=cut(local,[cylinder(c["tube"]["fitting_envelope_passage_mm"]/2,-length-.1,proud+.1)])
    return local.translate((0,0,seat))


def build(c=None):
    """Rebuild the nine original concept solids without archived native caches.

    Returned fitting/ring/wall/tube/filament are reference geometry. The printed
    clamp remains an illustrative preview and is not fabricated by this module.
    Purchased female fitting threads remain unfinished smooth pilots.
    """
    c = c if c is not None else load_config()
    rg, wg = c["radial_ring"], c["wall_ring"]
    wall = cut(cq.Solid.makeBox(50, 50, c["wall_thickness_mm"],
                               cq.Vector(-25, -25, -c["wall_thickness_mm"])),
               [cylinder(c["panel_hole_diameter_mm"]/2, -5, .1)])
    parts = {
        "body":make_body(c), "nut":make_nut(c), "cap":make_cap(c),
        "wall-ring":elliptical_ring(wg["compressed_mean_radius_mm"],
                                    wg["compressed_axial_height_mm"],
                                    wg["compressed_radial_width_mm"],wg["gland_depth_mm"]/2),
        "cap-ring":elliptical_ring(rg["compressed_mean_radius_mm"],
                                   rg["compressed_axial_height_mm"],
                                   rg["compressed_radial_width_mm"],sum(rg["gland_z_mm"])/2),
        "outer-fitting":fitting_envelope(c), "wall":wall,
        "continuous-tube":tube(c["tube"]["od_mm"]/2,c["tube"]["id_mm"]/2,
                               c["tube"]["inside_tip_z_mm"],c["tube"]["shown_outside_end_z_mm"]),
        "filament":cylinder(c["tail"]["filament_diameter_mm"]/2,
                            c["tube"]["inside_tip_z_mm"],c["tail"]["tip_z_mm"]),
    }
    for name,shape in parts.items():
        require_one(shape,name)
    return parts
