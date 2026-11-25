"""Generate the compact drybox feeder and its cassette for a bare 693 idler."""
import argparse
import json
from pathlib import Path
import sys

import manifold3d as m
import numpy as np

from compact_latch import PARKED, PIVOT_Y, build as build_cam
from drybox_mount import (
    BUSHING_LIP_BORE, BUSHING_STEM_BORE, BUSHING_STEM_RADIUS, LINER_SEAT_RADIUS,
    build as wall_mount, mesh,
)
from geometry import (TUBE_Z, box, cylinder, export_indexed_tray, loft, overlap, paired,
                      port, print_mesh, to_mesh, yz_prism)
from insert import FLOAT_MAX, FLOAT_MIN, TUBE_STOP, axle, foot_ramp, build as feeder_insert
from lid_alignment import GUIDE_CLEARANCE, GUIDE_X, GUIDE_Y, build as build_alignment
from printer_outlet import (
    CAP_BORE, CAP_FACE, CAP_GLAND_INNER_LIP, CAP_GLAND_OUTER_LIP,
    CAP_PITCH, COLLET, FITTING_SEAT, SOCKET_RADIUS,
    build as build_outlet,
)

ROOT = Path(__file__).resolve().parents[1]
FLOOR = -22.58
SEAM = 12.6
TRACK = (52.6,32.6,8.0)
RECESS = 1.36
TPU_HEIGHT = 1.86


def track(offset):
    width, depth, radius = TRACK
    return width+2*offset, depth+2*offset, radius+offset


def band(stations):
    return loft([(z,*track(offset)) for z,offset in stations]) - loft(
        [(stations[0][0]-.01,*track(-stations[0][1]))]
        + [(z,*track(-offset)) for z,offset in stations]
        + [(stations[-1][0]+.01,*track(-stations[-1][1]))])


def lid_seal():
    bottom = SEAM-RECESS
    root = [(bottom+.25*(1-np.cos(a)),1.95-.25*(1-np.sin(a)))
            for a in np.linspace(0,np.pi/2,9)]
    gland = band(root+[(SEAM-.16,1.95),(SEAM,2.11),(SEAM+.01,2.11)])
    gasket = band([(bottom+h, width) for h,width in (
        (0,1.48),(.16,1.63),(.59,1.63),(.75,1.47),(.76,1.05),
        (1.26,.98),(1.58,.81),(1.76,.62),(TPU_HEIGHT,.34))])
    return gland, gasket


def tray_and_lid(pocket_backing):
    tray = loft([(FLOOR,52,29,7.6),(-20.4,57.5,34,8.5),(-14,59,37,9.5),
                 (1,59,39,10.0),(SEAM,59,39,10.0)])
    tray -= loft([(-20.65,48.2,26.6,5.7),(-17.75,49.0,28.6,6.5),
                  (-7,49.0,29.2,6.9),(SEAM-2.4,48,27.0,6.0),(SEAM+.2,46.6,26.6,5.8)])
    lid = loft([(SEAM,59,39,10),(SEAM+1.32,59,39,10),
                (SEAM+2.10,52,32.6,8.6),(19,39,25.0,6.0),(24.35,29.5,19.9,5)])
    lid -= (loft([(SEAM-.15,46.6,26.6,5.8),(SEAM+1.75,45.2,26.3,5.8),
                  (19.0,35.0,21.0,5.2),(22.15,26.3,12.5,3.8)])-pocket_backing)
    pad = box(10.25,5.1,SEAM,12.45,7.0,22.45)
    lid += paired(paired(pad,[1,0,0]),[0,1,0])
    return tray,lid


def cradle():
    # Feet and pockets are outboard of the inlet's open-top assembly path.
    block = box(10.65,9.62,-21.5,15.15,13.12,-13.98)
    block -= box(11.28,9.69,-16.00,14.52,12.30,-13.92)
    block -= yz_prism([(9.5,-13.99),(9.5,-14.62),(9.9,-14.62),(9.9,-13.99)],11.25,14.55)
    cradle = paired(paired(block,[1,0,0]),[0,1,0])
    for x in (11.5,-14.3):
        ramp = foot_ramp(x)
        relief = m.Manifold.batch_hull([
            ramp.translate([dx,dy,z]) for dx in (-.23,.23)
            for dy in (-.23,.23) for z in (0,4)
        ])
        cradle -= paired(relief,[0,1,0])
    return cradle


def build(source, outlet_dir):
    sys.path.insert(0,str(outlet_dir))
    import clip
    import outlet

    cfg = outlet.load_config()
    frame, screw, nut, bearing, checks = feeder_insert(source)
    mount = wall_mount(port,box,yz_prism,TUBE_Z,TUBE_STOP)
    boss, port_cut, cap, fitting, land, cap_ring, cap_blind, cap_gland_volume = build_outlet(
        outlet,cfg,FLOOR,TUBE_STOP)
    guides, lid_pockets, pocket_backing = build_alignment(SEAM)
    tray, lid = tray_and_lid(pocket_backing)
    gland,gasket = lid_seal()
    pivot, catch, cam = build_cam(SEAM)

    def both(shape):
        return shape+shape.rotate([0,0,180])

    # The bulkhead enters from above and slides into its existing keyed seat.
    drop_channel = box(-24.9,-9.59,-20.13,8.50,9.59,3.0)
    # Trim the pre-existing flange flat to the same plane as the tray.
    mount_outer = mount["mount"] ^ box(-50,-25,FLOOR,0,25,20)
    tray = (tray+mount_outer+boss)-mount["passage"]-port_cut-drop_channel
    supports = cradle()
    cam_relief = cylinder(5.12,SEAM-3.4,SEAM+.05).translate([0,PIVOT_Y,0])
    tray = (tray+supports+guides-both(cam_relief)+both(pivot))-gland
    cam_mount_recess = box(-7.2,17.10,SEAM+.72,7.2,30,SEAM+8.5)
    lip_relief = box(-3.6,18.82,SEAM-.01,3.6,25,SEAM+5.8)
    lid = (lid-both(cam_mount_recess+lip_relief)-lid_pockets)+both(catch)
    rotors = both(cam(PARKED,0))
    printable_tray = tray+rotors
    body = tray+lid+both(cam(0))

    tube = port(2,TUBE_STOP,COLLET+10)
    center_assembly = frame+screw+nut+bearing
    insert_travel = max(overlap(center_assembly.translate([0,0,z]),tray+mount["bulkhead"])
                        for z in np.linspace(.03,35,50))
    inlet = mount["bulkhead"]
    inlet_travel = (
        max(overlap(inlet.translate([x,0,0]),tray) for x in np.linspace(0,30.15,61)),
        max(overlap(inlet.translate([30.15,0,z]),tray) for z in np.linspace(0,38,63)),
    )
    # Conservative envelope includes the first-drive TPU wheel at any phase.
    wheel = m.Manifold.batch_hull([axle(12.43,-4.51,4.51,FLOAT_MIN),
                                  axle(12.43,-4.51,4.51,FLOAT_MAX)])
    rotor_collisions = max(overlap(cam(angle),tray) for angle in np.linspace(0,PARKED,43))
    parked_cam_lid = overlap(both(cam(PARKED)),lid)
    clamped_lid_lift = overlap(both(cam(0)),lid.translate([0,0,.22]))
    operating_lid = overlap(cam(0),lid)

    def lid_rise(angle):
        low, high = -.4, .4
        moving = cam(angle)
        for _ in range(12):
            mid = (low+high)/2
            if overlap(moving,lid.translate([0,0,mid]))>.001:
                high = mid
            else:
                low = mid
        return low

    over_center = lid_rise(0)-lid_rise(9)
    negative_stop = overlap(cam(-4),tray)
    rotor_capture = overlap(cam(0).translate([0,0,.20]),tray)

    parked = tray+both(cam(PARKED))+center_assembly
    lid_path = max(overlap(lid.translate([0,0,z]),parked)
                   for z in np.linspace(0,30,151))
    unlocked_rise = TPU_HEIGHT-RECESS
    posts = [
        guides ^ box(x-1.8,y-1.3,SEAM+.03,x+1.8,y+1.3,SEAM+3)
        for x in (-GUIDE_X,GUIDE_X)
        for y in (-GUIDE_Y,GUIDE_Y)
    ]
    guide_travel = GUIDE_CLEARANCE+.02
    # All four posts limit travel in both axes before the cams engage.
    guide_stop = min(
        overlap(lid.translate([dx,dy,z]),post)
        for z in (0,unlocked_rise)
        for dx,dy in ((guide_travel,0),(-guide_travel,0),(0,guide_travel),(0,-guide_travel))
        for post in posts
    )
    # The catalog fitting mesh uses a plain cone in place of male teeth.
    # Only sweep the exposed body to check access without false thread collisions.
    exposed = fitting ^ box(FITTING_SEAT+.002,-8,TUBE_Z-8,COLLET+.1,8,TUBE_Z+8)
    fitting_path = max(overlap(exposed.translate([distance,0,0]),tray)
                       for distance in np.linspace(0,14,30))
    socket_wall = (port(SOCKET_RADIUS-.01,FITTING_SEAT-6.8,FITTING_SEAT-.04)
                   -port(5.25,FITTING_SEAT-6.81,FITTING_SEAT-.03))
    bead = gasket ^ box(-35,-24,SEAM,35,24,SEAM+TPU_HEIGHT)
    ring = cfg["wall_ring"]
    tail = cfg["tail"]
    depth = ring["gland_depth_mm"]
    # Approximate loss of free section at the installed mean diameter.
    stretch = ring["gland_inner_radius_mm"]*2/ring["nominal_id_mm"]
    stretched_cs = ring["cross_section_mm"]/np.sqrt(stretch)
    ring_fill = ring["nominal_free_volume_mm3"]/cap_gland_volume
    ring_throat = (ring["gland_outer_radius_mm"]-ring["gland_inner_radius_mm"]
                   -CAP_GLAND_INNER_LIP-CAP_GLAND_OUTER_LIP)
    # Cross-sectional area conservation estimates the bore in the press-fit
    # section. Axial flow and printed dimensions still need a fit check.
    seated_stem_bore = 2*np.sqrt(
        (BUSHING_STEM_BORE/2)**2+LINER_SEAT_RADIUS**2-BUSHING_STEM_RADIUS**2)
    cap_depth = cap_blind-COLLET
    tail_headroom = cap_depth-tail["exposed_tail_mm"]
    barrel = mesh(clip.build(clip.load_config(),cfg)).rotate([0,90,0]).translate([COLLET,0,TUBE_Z])
    barrel_clearance = barrel.min_gap(cap,12.)
    barrel_headroom = cap_blind-barrel.bounding_box()[3]
    fitting_clearance = fitting.min_gap(cap,12.)
    parked_tail = port(tail["filament_diameter_mm"]/2,COLLET,COLLET+tail["exposed_tail_mm"])
    tail_collision = overlap(parked_tail,cap)
    turned_cap = cap.translate([0,0,-TUBE_Z])
    storage = tray+fitting+barrel+parked_tail
    cap_path = max(
        overlap(turned_cap.rotate([angle,0,0]).translate([angle*CAP_PITCH/360,
                                                       0,TUBE_Z]),storage)
        for angle in np.linspace(0,1600,81)
    )
    checks.update({
        "parked_cam_clearance_mm":round(rotors.min_gap(tray,1.),4),
        "lid_unlatched_height_mm":round(unlocked_rise,4),
        "lid_guide_nominal_clearance_per_side_mm":GUIDE_CLEARANCE,
        "lid_guide_stop_overlap_per_post_mm3":round(guide_stop,5),
        "storage_cap_usable_depth_mm":round(cap_depth,2),
        "storage_cap_tail_headroom_mm":round(tail_headroom,2),
        "storage_cap_fitting_clearance_mm":round(fitting_clearance,2),
        "storage_cap_barrel_wing_clearance_mm":round(barrel_clearance,2),
        "storage_cap_barrel_headroom_mm":round(barrel_headroom,2),
        "storage_cap_oring_stretch_percent":round(100*(stretch-1),2),
        "storage_cap_oring_face_squeeze_percent":round(100*(1-depth/stretched_cs),2),
        "storage_cap_oring_gland_fill_percent":round(100*ring_fill,2),
        "storage_cap_oring_retention_throat_mm":round(ring_throat,3),
        "storage_cap_parked_tail_overlap_mm3":round(tail_collision,6),
        "center_capture_at_0_45_mm3":round(overlap(frame.translate([0,0,.45]),lid),6),
        "lid_rim_height_above_print_bed_mm":round(abs(SEAM-lid.bounding_box()[2]),6),
        "tray_components_with_captive_cam":len(printable_tray.decompose()),
        "closed_case_size_mm":np.round(np.array(body.bounding_box()[3:])-body.bounding_box()[:3],2).tolist(),
        "wall_bulkhead_insertion_mm3":np.round(inlet_travel,6).tolist(),
        "frame_against_case_mm3":round(overlap(center_assembly,tray+lid),6),
        "frame_placement_mm3":round(insert_travel,6),
        "upper_drive_against_case_mm3":round(overlap(wheel,tray+lid),6),
        "ptfe_through_the_case_mm3":round(overlap(tube,tray+fitting+frame),6),
        "inlet_guide_through_case_mm3":round(overlap(mount["linerSolid"],tray+inlet+frame),6),
        "inlet_bushing_stem_bore_mm":BUSHING_STEM_BORE,
        "inlet_bushing_seated_stem_bore_estimate_mm":round(seated_stem_bore,3),
        "inlet_bushing_lip_bore_mm":BUSHING_LIP_BORE,
        "outlet_fitting_install_sweep_mm3":round(fitting_path,6),
        "outlet_socket_wall_fraction":round(overlap(socket_wall,tray)/socket_wall.volume(),6),
        "storage_cap_bore_mm":CAP_BORE,
        "outlet_collet_x_mm":round(COLLET,2),
        "wall_to_cap_tip_mm":round(cap.bounding_box()[3]-mount["wallX"],2),
        "cap_assembly_sweep_mm3":round(cap_path,6),
        "cap_face_land_fraction":round(overlap(land,tray)/land.volume(),6),
        "lid_gasket_nominal_compression_mm":round(TPU_HEIGHT-RECESS,2),
        "lid_gasket_volume_fill_fraction":round(gasket.volume()/gland.volume(),4),
        "lid_gasket_free_inside_tray_mm3":round(overlap(gasket,tray),6),
        "lid_gasket_bead_contact_fraction":round(overlap(bead,lid)/bead.volume(),6),
        "unlatching_lid_path_mm3":round(lid_path,6),
        "cam_sweep_against_tray_mm3":round(rotor_collisions,6),
        "printed_cam_overlap_mm3":round(overlap(rotors,tray),6),
        "parked_cam_lid_clearance_mm3":round(parked_cam_lid,6),
        "cam_nominal_contact_interference_mm3":round(operating_lid,6),
        "cam_over_center_draw_mm":round(over_center,5),
        "cam_closed_stop_overlap_mm3":round(negative_stop,6),
        "cam_upward_capture_overlap_mm3":round(rotor_capture,6),
        "closed_cam_blocks_lid_lift_mm3":round(clamped_lid_lift,6),
    })
    collision_checks = (
        "frame_against_case_mm3","frame_placement_mm3","upper_drive_against_case_mm3",
        "ptfe_through_the_case_mm3","inlet_guide_through_case_mm3",
        "outlet_fitting_install_sweep_mm3","cap_assembly_sweep_mm3",
        "lid_gasket_free_inside_tray_mm3","unlatching_lid_path_mm3",
        "cam_sweep_against_tray_mm3","printed_cam_overlap_mm3","parked_cam_lid_clearance_mm3",
        "storage_cap_parked_tail_overlap_mm3",
    )
    if max(*inlet_travel, *(checks[name] for name in collision_checks)) > .01:
        raise ValueError(f"Unexpected assembly interference: {checks}")
    if (checks["tray_components_with_captive_cam"] != 3 or len(lid.decompose()) != 1
            or min(checks[name] for name in ("cap_face_land_fraction","lid_gasket_bead_contact_fraction",
                                            "outlet_socket_wall_fraction")) < .995
            or checks["lid_gasket_volume_fill_fraction"] > .85
            or not .70 < ring_fill < .85
            or not .85*stretched_cs < ring_throat < stretched_cs
            or seated_stem_bore < cfg["tube"]["od_mm"]+.16):
        raise ValueError(f"Invalid captive tray or seal seat: {checks}")
    if (checks["parked_cam_clearance_mm"] < .324
            or guide_stop < .012
            or min(cap_depth,tail_headroom) < 2.5
            or fitting_clearance < 1.25
            or barrel_clearance < 1.2
            or checks["center_capture_at_0_45_mm3"] < .05
            or checks["lid_rim_height_above_print_bed_mm"] > .001):
        raise ValueError(f"Insufficient lid location, cap clearance or print-in-place gap: {checks}")
    if (max(operating_lid-.05,.015-over_center) > 0
            or min(negative_stop,rotor_capture,clamped_lid_lift) < .05):
        raise ValueError(f"The captive cams do not retain the lid: {checks}")
    return {
        "tray":tray, "lid":lid, "lid-guides":guides^box(-21,-16,SEAM-.001,21,16,SEAM+4),
        "lid-pockets":lid_pockets^box(-21,-16,SEAM-.001,21,16,SEAM+4),
        "cam":both(cam(0)), "parked_cam":both(cam(PARKED)), "gasket":gasket,
        "cap-o-ring":cap_ring,
        "barrel-stop":barrel,
        "tray-with-cam":printable_tray,
        "fit-test-receiver":tray^box(18.6,-22,FLOOR-.1,FITTING_SEAT+.1,22,SEAM+.04),
        "storage-cap":cap, "frame":frame, "axle":screw, "axle-nut":nut,
        "bearing":bearing, "fitting":fitting, "inlet":inlet, "locknut":mount["locknut"],
        "inlet-bushing":mount["bushing"], "wall-o-ring":mount["wallSeal"],
        "inlet-tube":mount["leftTube"],
        "outlet-tube":tube-port(1.25,TUBE_STOP-.1,COLLET+10.1),
    },checks


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source",type=Path,required=True,help="MakerWorld 3740072 pneumatic latch 3MF")
    parser.add_argument("--output",type=Path,default=ROOT/"build"/"manual-feeder")
    parser.add_argument("--outlet-dir",type=Path,default=ROOT/"filament-drybox"/"cad")
    args = parser.parse_args()
    args.output.mkdir(parents=True,exist_ok=True)
    parts, checks = build(args.source,args.outlet_dir)
    (args.output/"checks.json").write_text(json.dumps(checks,indent=2)+"\n")
    print(json.dumps(checks,indent=2),flush=True)

    print_parts = {"tray-with-cam":(0,0,0), "lid":(0,0,0),"storage-cap":(0,90,0),
                   "fit-test-receiver":(0,0,0), "gasket":(0,0,0),
                   "frame":(0,-90,0),
                   "inlet":(0,90,0),"inlet-bushing":(0,-90,0)}
    for name,rotation in print_parts.items():
        generated = print_mesh(parts[name],rotation)
        if name == "tray-with-cam":
            export_indexed_tray(args.output/f"{name}.3mf",generated)
        else:
            generated.export(args.output/f"{name}.stl")
    assembly = args.output/"assembly"
    assembly.mkdir(exist_ok=True)
    for name,part in parts.items():
        if name not in ("tray-with-cam","fit-test-receiver"):
            to_mesh(part).export(assembly/f"{name}.stl")


if __name__ == "__main__":
    main()
