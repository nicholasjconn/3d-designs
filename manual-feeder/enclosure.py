"""Generate the hardware-free enclosure for the 608 manual-feeder insert."""
import argparse
import json
from pathlib import Path
import sys

import manifold3d as m
import numpy as np
import trimesh

ROOT = Path(__file__).resolve().parents[1]
TUBE_Z = -4.025
FEET_Z, FLOOR_Z = -30.55, -32.30
SEAM_Z, TUBE_STOP, PORT_FACE = 4.8, 17.133, 28.92
PORT_TIP = PORT_FACE - 7
GROOVE_WIDTH, GROOVE_DEPTH = 3.90, 2.05
FLOOR_RADIUS, EDGE_BREAK = .30, .18
TRACK = (53.50, 32.80, 12.60)
INNER_LAND, OUTER_LAND = 1.50, 1.60
SNAP_NOSE = -6.75


def box(x0, y0, z0, x1, y1, z1):
    return m.Manifold.cube([x1-x0, y1-y0, z1-z0]).translate([x0,y0,z0])

def cylinder(radius, lower, upper, upper_radius=-1, sides=96):
    return m.Manifold.cylinder(upper-lower, radius, upper_radius, sides).translate([0,0,lower])

def port(radius, start, end, end_radius=-1, sides=96):
    return cylinder(radius,start,end,end_radius,sides).rotate([0,90,0]).translate([0,0,TUBE_Z])

def paired(shape, axis):
    return shape + shape.mirror(axis)

def opposite_tabs(shape):
    return shape+shape.rotate([0,0,180])

def outline(width, depth, radius):
    points = []
    for quarter, (xsign, ysign) in enumerate([(1,1),(-1,1),(-1,-1),(1,-1)]):
        angles = np.linspace(quarter*np.pi/2, (quarter+1)*np.pi/2, 17)
        points.extend(zip(xsign*(width/2-radius)+radius*np.cos(angles),
                          ysign*(depth/2-radius)+radius*np.sin(angles)))
    return np.asarray(points)

def loft(stations):
    rings = [np.c_[outline(width,depth,radius),np.full(68,z)] for z,width,depth,radius in stations]
    vertices = np.vstack([*rings,[0,0,stations[0][0]],[0,0,stations[-1][0]]])
    triangles = []
    last = (len(rings)-1)*68
    for i in range(68):
        j = (i+1)%68
        triangles.extend([(len(vertices)-2,j,i),(len(vertices)-1,last+i,last+j)])
        for bottom in range(0,last,68):
            a,b = bottom+i,bottom+j
            triangles.extend([(a,b,b+68),(a,b+68,a+68)])
    return m.Manifold(m.Mesh(vertices.astype(np.float32),np.asarray(triangles,dtype=np.uint32)))

def track(offset):
    width, depth, radius = TRACK
    return width+2*offset, depth+2*offset, radius+offset

def groove():
    half = GROOVE_WIDTH/2
    bottom = SEAM_Z-GROOVE_DEPTH
    fillet = [(bottom+FLOOR_RADIUS*(1-np.cos(a)), half-FLOOR_RADIUS*(1-np.sin(a)))
              for a in np.linspace(0,np.pi/2,10)]
    radial_stations = fillet+[(SEAM_Z-EDGE_BREAK,half),(SEAM_Z,half+EDGE_BREAK),
                             (SEAM_Z+.1,half+EDGE_BREAK)]
    inside = [(z,*track(-offset)) for z,offset in radial_stations]
    inside.insert(0,(bottom-.1,*inside[0][1:]))
    inside.append((SEAM_Z+.2,*inside[-1][1:]))
    outside = [(z,*track(offset)) for z,offset in radial_stations]
    return loft(outside)-loft(inside)

def yz_prism(points, x0, x1):
    return (m.CrossSection([points],m.FillRule.NonZero).extrude(x1-x0)
            .transform([[0,0,1,x0],[1,0,0,0],[0,1,0,0]]))

def fitted_socket(drybox):
    # Use the thread already modeled for these same purchased push-fits.
    sys.path.insert(0, str(drybox))
    from outlet import load_config, purchased_socket_tool

    cfg = load_config()
    solid = purchased_socket_tool(cfg)
    verts, triangles = solid.tessellate(.018,.135)
    clean = trimesh.Trimesh([vertex.toTuple() for vertex in verts],triangles)
    if not clean.is_watertight:
        raise ValueError("Thread tessellation produced a non-watertight mesh")
    vertices, faces = clean.vertices, clean.faces
    shoulder = cfg["purchased_interfaces"]["shoulder_stop_z_mm"]
    def mesh_thread(points):
        return (m.Manifold(m.Mesh(points.astype(np.float32),faces.astype(np.uint32)))
                .rotate([0,90,0]).translate([PORT_FACE-shoulder,0,TUBE_Z]))
    male_preview = vertices.copy()
    radii = np.linalg.norm(vertices[:,:2],axis=1)
    nonzero = radii>0
    male_preview[nonzero,:2] *= (1-.1/radii[nonzero])[:,None]
    socket, reference_thread = mesh_thread(vertices), mesh_thread(male_preview)
    if any(p.is_empty() or p.status()!=m.Error.NoError for p in (socket,reference_thread)):
        raise ValueError("Unable to mesh the HANGLIFE socket")
    return socket, reference_thread

def base_enclosure(outlet_dir):
    rim_outside = track(GROOVE_WIDTH/2+OUTER_LAND)
    rim_opening = track(-GROOVE_WIDTH/2-INNER_LAND)
    outer = [(FLOOR_Z-3.20,46,25,6.5),(FLOOR_Z-2.20,51,29,7),(FLOOR_Z+.05,54,33.4,8),
             (-9,57.3,35.7,8.5),(SEAM_Z-3.5,*rim_outside),(SEAM_Z,*rim_outside)]
    cavity = [(FLOOR_Z,42,23,5.5),(FLOOR_Z+.90,45,24.4,5.8),
              (-25,48,26.8,6.2),(-1,48,26.8,6.2),(SEAM_Z-1.7,*rim_opening),
              (SEAM_Z+.10,*rim_opening)]
    tray = loft(outer)-loft(cavity)
    port_boss = port(6.12,PORT_TIP,PORT_FACE,6.15)
    facing = yz_prism([(PORT_FACE,-11),(31.5,-11),(31.5,4.55),(PORT_FACE,1.97)],
                      -6.42,6.42).rotate([0,0,-90])
    tray = (tray-paired(facing,[1,0,0]))+paired(port_boss,[1,0,0])
    thread_socket, male_thread = fitted_socket(outlet_dir)
    port_cut = thread_socket + port(4.38,PORT_TIP-.13,PORT_TIP+.43)
    port_cut += port(4.27,PORT_FACE-.63,PORT_FACE+.18,5.27)
    tray -= paired(port_cut,[1,0,0])

    cover = loft([(SEAM_Z,*rim_outside),(6.9,*rim_outside),(7.9,43,32,8.3),
                  (9.4,37,27,8),(14.8,34,23,7.6),(20.6,29,20.2,7.1),(24.2,23.4,17.4,6.6)])
    cover -= loft([(SEAM_Z-.1,*rim_opening),(6.4,41,25.9,6.2),(8,31,23.5,6.1),
                   (14.7,28.4,20.7,6.0),(19.2,25,17.7,6),(22.15,17.5,13,5.4)])
    gland = groove()

    # Lowered straight into two blind internal channels. The guide cheeks carry
    # side load. The ramped fingers flex away from the feeder only while it moves.
    guide_profile = [(11.9,-20.3),(14.85,-20.3),(14.85,3.12),(7.35,3.12),
                     (7.14,2.65),(7.14,-13.55)]
    guide_side = yz_prism(guide_profile,7.97,10.22)+yz_prism(guide_profile,14.98,17.23)
    guide_side -= (yz_prism([(7.05,2.20),(7.05,3.27),(12.9,3.27),(12.9,2.20)],9.94,10.32)
                   +yz_prism([(7.05,2.20),(7.05,3.27),(12.9,3.27),(12.9,2.20)],14.88,15.26))
    anchor = box(10.64,9.97,-24.3,14.56,14.75,-21.44)
    tray += opposite_tabs(guide_side+anchor)
    root_fillet = [(9.98+.90*np.cos(a),-20.6+.90*np.sin(a))
                   for a in np.linspace(-np.pi/2,0,10)]
    back_fillet = [(13.31-.90*np.cos(a),-20.6+.90*np.sin(a))
                   for a in np.linspace(0,-np.pi/2,10)]
    blade = yz_prism(root_fillet+[(10.88,-7.95),(10.26,SNAP_NOSE),(10.88,-5.76),
                                 (10.93,-4.70),(12.06,-4.70)]+back_fillet+
                    [(13.45,-21.68),(9.98,-21.68)],11.25,13.95)

    fingers = opposite_tabs(blade)

    # Two flat pads take the downward load. They leave the center free for the tread.
    front_pad = box(-5.3,3.88,FLOOR_Z-.18,5.3,7.65,FEET_Z)
    supports = paired(front_pad,[0,1,0])
    tray = (tray+supports)-gland

    tail = male_thread
    hex_body = port(5.7735,PORT_FACE,PORT_FACE+6.1,sides=6)
    nose = port(4.15,PORT_FACE+6.1,PORT_FACE+9.3)
    collet = port(4.92,PORT_FACE+9.3,PORT_FACE+11)-port(2.1,PORT_FACE+9.2,PORT_FACE+11.1)
    fitting = tail+hex_body+nose-port(2.12,PORT_FACE-7.1,PORT_FACE+9.5)
    right_tube = port(2,TUBE_STOP,46)-port(1.25,TUBE_STOP-.1,46.1)
    left_tube = right_tube.mirror([1,0,0])

    return {"tray":tray,"cover":cover,"fingers":fingers,
            "fitting":paired(fitting,[1,0,0]),"collet":paired(collet,[1,0,0]),
            "leftTube":left_tube,"rightTube":right_tube}


def build_enclosure(out, outlet_dir):
    out.mkdir(parents=True, exist_ok=True)
    shapes = base_enclosure(outlet_dir)
    pivot_y = 26.05
    maximum_angle = 105
    rotor_bottom = 1.36
    # The nominal axial gap on the cone is .54 mm. Leave .003 mm in
    # the sweep so the triangulated surfaces can rotate without artifacts.
    seat_lift = .537
    free_ring_rise = .54
    catch_height = 8.1

    def opposite(part):
        return part.rotate([0,0,180])

    def pair(part):
        return part + opposite(part)

    def anchored(part):
        return part.translate([0,pivot_y,0])

    def overlap(part, obstacle):
        return abs((part ^ obstacle).volume())

    def xz_prism(points, lo, hi):
        return yz_prism(points,-hi,-lo).rotate([0,0,-90])

    # The load from the cam runs through the conical shoulder and into this
    # solid post. Both posts and the stop blocks are integral to the tray.
    post = cylinder(3.15,.62,8.70) + cylinder(3.15,8.68,10.38,4.85)
    post += cylinder(4.85,10.38,11.36,4.85)
    # A second matching seat limits rocking when the cam is loaded off-axis.
    post += cylinder(3.15,3.25,4.10,4.00) + cylinder(4.0,4.10,4.95,3.15)
    pedestal = cylinder(3.10,-2.12,.80,5.29)
    # One rounded brace starts in the tray wall and lands under the
    # whole pedestal. Both ends are joined by the same sloping faces.
    lower_z, upper_z = -17.70, -2.08
    lower_y, upper_y = 16.475, 22.50
    shift = (upper_y-lower_y)/(upper_z-lower_z)
    gusset = loft([(lower_z,4.65,1.65,.78),(upper_z,6.48,13.44,3.20)])
    gusset = gusset.transform([[1,0,0,0],[0,1,shift,lower_y-shift*lower_z],[0,0,1,0]])
    first_pedestal_layer = anchored(cylinder(3.10,-2.12,-2.10))
    if abs((first_pedestal_layer-gusset).volume()) > .003:
        raise ValueError("The rounded brace does not reach the entire pedestal")
    stop = yz_prism([(16.4,-4.1),(18.5,-3.45),(23.90,3.42),
                     (23.90,8.25),(20.65,8.25),(19.38,5.6),
                     (18.03,1.08),(16.4,.26)],8.05,10.42)
    # At this X position keep the stop below the removable flange.
    stop -= box(7.9,15.0,4.55,10.6,19.98,8.35)
    tray = shapes["tray"] + pair(anchored(post+pedestal)+gusset+stop)
    # Grow the underside of each interior socket from its wall.
    # The cylindrical keepout exceeds the entire threaded bore.
    ramp = xz_prism([(21.92,-10.23),(24.48,-13.52),(25.12,-13.52),
                     (25.12,-8.32),(21.92,-8.32)],-3.30,3.30)
    thread_keepout = cylinder(5.36,21.86,25.24).rotate([0,90,0]).translate([0,0,-4.025])
    port_ramps = pair(ramp-thread_keepout)
    if overlap(port_ramps,box(-21.,-12.,-30.,21.,12.,5.)) > .001:
        raise ValueError("Socket ramp enters the feeder clearance")
    tray += port_ramps

    # Blend the wider bed face into the original profile below the cavity.
    blend = 2.15/2.25
    tray += loft([(-35.5,50.4,29.8,7.0),
                  (-32.35,51+3*blend,29+4.4*blend,7+blend)])

    lid_rib = loft([(6.65,*track(3.55)),(7.65,*track(3.55)),(8.04,*track(3.1))])
    lid_rib -= loft([(6.60,*track(-.1)),(8.12,*track(-.1))])
    crown = [(x,catch_height-.074*x*x) for x in np.linspace(2.75,-2.75,33)]
    catch = xz_prism([(-2.75,6.38),(2.75,6.38),*crown],18.25,19.80)
    lid = shapes["cover"] + lid_rib + pair(catch)

    # Angle stations are measured from the inward-pointing position.
    # The slight rise after the low point biases the cam toward its stop.
    profile = [(-54,8.77),(-43,8.56),(-25,7.93),(-11,7.48),(3,7.55),(27,7.71)]
    radii = [4.75,5.28,6.10,7.22,7.75,7.75,4.75]
    vertices = []
    faces = []
    for degrees, height in profile:
        angle = np.radians(degrees)
        zh = [height-1.23,height-.82,height,height,height+.54,11.40,11.40]
        vertices.extend((r*np.sin(angle),-r*np.cos(angle),z) for r,z in zip(radii,zh))
    sides = len(radii)
    for offset in range(0,len(vertices)-sides,sides):
        for j in range(sides):
            k = (j+1)%sides
            a,b = offset+j,offset+k
            faces.extend(((a,a+sides,b+sides),(a,b+sides,b)))
    last = len(vertices)-sides
    # Triangulate the two end profiles, including the sloped underside.
    for j in range(1,sides-1):
        faces.extend(((0,j,j+1),(last,last+j+1,last+j)))
    cam = m.Manifold(m.Mesh(np.asarray(vertices,dtype="float32"),np.asarray(faces,dtype="uint32")))

    # Start over the breakaway ribs with a narrower annulus, then
    # grow the outer rim and inner lead-in toward the full section.
    ring = cylinder(5.16,rotor_bottom,1.72,5.32)+cylinder(5.32,1.72,7.23)
    ring += cylinder(5.32,7.19,10.14,6.0)
    grip_profile = [(4.80,2.00),(5.10,2.00),(13.55,11.42),(13.55,13.72),
                    (12.63,14.42),(10.05,12.49),(4.80,7.65)]
    lever = xz_prism(grip_profile,-2.15,2.15)
    # Widen the part pressed by the thumb beyond the fixed stop.
    lever += xz_prism([(10.57,9.63),(12.93,10.82),(13.55,11.42),
                        (13.55,13.72),(12.63,14.42),(10.57,12.82)],-3.1,3.1)
    rotor_bore = cylinder(3.55,1.20,8.55)
    rotor_bore += cylinder(4.34,1.20,rotor_bottom)
    rotor_bore += cylinder(4.34,rotor_bottom,2.45,3.55)
    rotor_bore += cylinder(3.55,8.54,11.58,6.59)
    rotor_bore += cylinder(3.55,3.11,3.96,4.40)
    rotor_bore += cylinder(4.40,3.958,4.16)
    rotor_bore += cylinder(4.40,4.158,5.01,3.55)
    rotor = (ring + lever + cam) - rotor_bore

    def pose(angle, lift):
        return anchored(rotor.rotate([0,0,angle])).translate([0,0,lift])

    # Solve the maximum lid rise at each angle with the rotor on its thrust
    # seat. A negative value shows how much elastic give the cam requires.
    frames = []
    worst = {"rotor_tray_mm3":0.0,"rotor_fixed_ports_mm3":0.0}
    collision_at = {}
    ports = shapes["fitting"]+shapes["collet"]+shapes["leftTube"]+shapes["rightTube"]
    for angle in np.linspace(0,maximum_angle,106):
        moving = pose(angle,seat_lift)
        limits = {"rotor_tray_mm3":tray,"rotor_fixed_ports_mm3":ports}
        for name, solid in limits.items():
            common = moving ^ solid
            hit = abs(common.volume())
            if hit > worst[name]:
                worst[name] = hit
                if hit > .001:
                    collision_at[name] = {"angle":float(angle),"bounds":common.bounding_box()}
        low, high = -.3, free_ring_rise
        if overlap(moving,lid.translate([0,0,high])) < .001:
            lid_rise = high
        else:
            for _ in range(13):
                middle = (low+high)/2
                if overlap(moving,lid.translate([0,0,middle])) < .001:
                    low = middle
                else:
                    high = middle
            lid_rise = low
        frames.append([float(angle), lid_rise])

    open_rotors = pair(pose(maximum_angle,0))
    parked = tray+open_rotors+ports
    clearance = 0.
    for rise in np.linspace(free_ring_rise,32,65):
        common = lid.translate([0,0,rise]) ^ parked
        hit = abs(common.volume())
        if hit > clearance:
            clearance = hit
            if hit > .001:
                collision_at["parked_lid"] = {"rise":float(rise),"bounds":common.bounding_box()}
    closed = pose(0,seat_lift)
    envelope = (tray+lid+pair(closed)).bounding_box()
    seal_band = loft([(SEAM_Z-.12,*track(2.3)),(SEAM_Z+.12,*track(2.3))])
    seal_band -= loft([(SEAM_Z-.2,*track(-2.3)),(SEAM_Z+.2,*track(-2.3))])

    # Eight narrow, accessible ribs start each rotating ring. Their stems
    # neck down at the underside and break free when the lever is worked.
    breakaway = m.Manifold()
    for angle in range(0,360,45):
        foot = box(4.35,-.37,.75,5.16,.37,1.18)
        neck = box(4.47,-.225,1.14,5.11,.225,rotor_bottom+.17)
        breakaway += (foot+neck).rotate([0,0,angle])
    tabs = pair(anchored(breakaway))
    printable_tray = tray + shapes["fingers"] + open_rotors + tabs
    axial_sweep = max(overlap(pose(a,z),tray) for a in (0,26,53,79,105)
                      for z in np.linspace(0,seat_lift,11))
    checks = {
        "nominal_vertical_free_play_mm": .54,
        "pin_diameter_mm": 6.3,
        "radial_print_gap_per_side_mm": .4,
        "closed_lid_height_delta_mm": round(frames[0][1],4),
        "over_center_min_lid_delta_mm": round(min(f[1] for f in frames),4),
        "over_center_angle_deg": min(frames,key=lambda f:f[1])[0],
        "parked_lid_lift_overlap_mm3": round(clearance,6),
        "port_ramp_hardware_overlap_mm3": round(overlap(port_ramps,ports),6),
        "closed_cam_blocks_lid_lift_mm3": round(overlap(closed,lid.translate([0,0,.22])),5),
        "negative_stop_interference_mm3": round(overlap(pose(-2,seat_lift),tray),5),
        "printed_tab_connections":len(printable_tray.decompose()),
        "tray_components_after_breakaway":len((tray+shapes["fingers"]+open_rotors).decompose()),
        "rotor_components":len(rotor.decompose()),
        "cover_components":len(lid.decompose()),
        "rotor_unloaded_tray_overlap_mm3":round(overlap(open_rotors,tray),5),
        "axial_seats_per_post":2,
        "axial_total_overlap_mm3":round(axial_sweep,6),
        "pivot_retains_cam_mm3":round(overlap(pose(0,seat_lift+.20),tray),6),
        "added_material_in_gland_mm3":round(overlap(seal_band,
            (tray-shapes["tray"])+(lid-shapes["cover"])),7),
        "worst_interference":{name:round(value,6) for name,value in worst.items()},
        "collision_at":collision_at,
        "closed_size_mm":[round(hi-lo,2) for lo,hi in zip(envelope[:3],envelope[3:])],
    }
    print(json.dumps(checks,indent=2),flush=True)
    (out/"checks.json").write_text(json.dumps(checks,indent=2)+"\n")
    if max(clearance, axial_sweep, *worst.values(), checks["added_material_in_gland_mm3"],
           checks["port_ramp_hardware_overlap_mm3"])>.025:
        raise ValueError("An operating position intersects the enclosure")
    if (checks["printed_tab_connections"],checks["tray_components_after_breakaway"],
        checks["rotor_components"],checks["cover_components"]) != (1,3,1,1):
        raise ValueError("The printable breakaway assembly has the wrong connectivity")
    if not (abs(frames[0][1])<.06 and min(f[1] for f in frames)<frames[0][1]-.025
            and checks["closed_cam_blocks_lid_lift_mm3"]>.05
            and checks["pivot_retains_cam_mm3"]>.05
            and checks["negative_stop_interference_mm3"]>.05):
        raise ValueError("The cam does not draw over center and block lid lift")

    for name,part in {"tray-with-captive-cams":printable_tray,"lid":lid}.items():
        bounds = part.bounding_box()
        part = part.translate([0,0,-bounds[2]])
        raw = part.to_mesh64()
        mesh = trimesh.Trimesh(raw.vert_properties[:,:3],raw.tri_verts,process=False)
        if not mesh.is_watertight or mesh.volume<=0:
            raise ValueError(f"{name} export is not watertight")
        mesh.export(out/f"{name}.stl")
    return printable_tray, lid


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=ROOT/"build"/"manual-feeder")
    parser.add_argument("--outlet-dir", type=Path, default=ROOT/"filament-drybox"/"cad")
    args = parser.parse_args()
    build_enclosure(args.output, args.outlet_dir)


if __name__ == "__main__":
    main()
