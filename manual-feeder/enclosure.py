"""Generate the drybox-mounted enclosure for the 608 manual-feeder insert."""
import argparse
import json
from pathlib import Path
import sys
from xml.etree import ElementTree as ET
from zipfile import ZIP_DEFLATED, ZipFile

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
TPU_RECESS_WIDTH, TPU_RECESS_DEPTH = 4.40, 1.36
TPU_BASE_WIDTH, TPU_BASE_HEIGHT, TPU_HEIGHT = 4.04, .75, 1.86


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
    half = TPU_RECESS_WIDTH/2
    bottom = SEAM_Z-TPU_RECESS_DEPTH
    fillet = [(bottom+FLOOR_RADIUS*(1-np.cos(a)), half-FLOOR_RADIUS*(1-np.sin(a)))
              for a in np.linspace(0,np.pi/2,10)]
    radial_stations = fillet+[(SEAM_Z-EDGE_BREAK,half),(SEAM_Z,half+EDGE_BREAK),
                             (SEAM_Z+.1,half+EDGE_BREAK)]
    inside = [(z,*track(-offset)) for z,offset in radial_stations]
    inside.insert(0,(bottom-.1,*inside[0][1:]))
    inside.append((SEAM_Z+.2,*inside[-1][1:]))
    outside = [(z,*track(offset)) for z,offset in radial_stations]
    return loft(outside)-loft(inside)

def gasket():
    bottom = SEAM_Z-TPU_RECESS_DEPTH
    half = TPU_BASE_WIDTH/2
    # Flat flange prints face-down. A narrow, rounded bead supplies the
    # compression against the lid without loading the entire flange.
    stations = [(0,half-.15),(.16,half),(.59,half),
                (TPU_BASE_HEIGHT,half-.16),(TPU_BASE_HEIGHT+.01,1.05),
                (1.26,.98),(1.58,.81),(1.76,.62),(TPU_HEIGHT,.34)]
    outer = loft([(bottom+z,*track(radius)) for z,radius in stations])
    inner = loft([(bottom+z,*track(-radius)) for z,radius in stations])
    return outer-inner

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
    from drybox_mount import build as build_mount
    mount = build_mount(port,box,yz_prism,TUBE_Z,TUBE_STOP)
    port_cut = thread_socket + port(4.38,PORT_TIP-.13,PORT_TIP+.43)
    port_cut += port(4.27,PORT_FACE-.63,PORT_FACE+.18,5.27)
    tray = (tray+mount["mount"])-port_cut-mount["passage"]

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
    return {**mount,"tray":tray,"cover":cover,"fingers":fingers,
            "fitting":fitting,"collet":collet,"rightTube":right_tube}


def short_outlet(original, report):
    """Add the tested socket and shorten the matching standard drybox outlet."""
    import outlet
    from drybox_mount import mesh

    face, boss_back, boss_radius = 38.5, 30.9, 17
    stem_length, socket_depth = 7, 7.5
    web_start, web_radius = 28.5, 7.35

    def on_axis(shape):
        return mesh(shape).rotate([0, 90, 0]).translate([face, 0, TUBE_Z])

    config = outlet.load_config()
    original_outlet = outlet.make_body(config)
    stem = config["stem_thread"]
    ring = config["wall_ring"]
    thread_back = -socket_depth
    major, pitch = stem["major_diameter_mm"], stem["pitch_mm"]
    radial = config["female_radial_allowance_mm"]
    # Use the same helical sweep domain as the original stem and matching
    # locknut. The round clearance beyond its rear end has no thread phase.
    teeth = outlet.thread_tooth(major, pitch, *stem["z_mm"], radial_shift=radial,
                               widen=config["female_flank_axial_allowance_mm"])
    teeth = teeth.intersect(outlet.cylinder(major/2 + radial + .5, thread_back, .08))
    thread = outlet.fuse([
        outlet.cylinder(outlet.minor_diameter(major, pitch)/2 + radial, thread_back, .08),
        teeth,
    ])

    # Spread the boss load into a broader area of the tray, with a solid
    # annular web behind the thread cavity and a bore through its center.
    root = (port(6.2, 21.8, 24.35)
            + port(6.2, 24.34, 26.7, 9.55)
            + port(9.55, 26.69, boss_back+.12, boss_radius))
    root -= box(21.7, -18, SEAM_Z-.12, boss_back, 18, 15)
    receiver = (root + port(boss_radius, boss_back, face)) - groove()
    guide = (port(2.65, 21.72, 22.2, 2.25)
             + port(2.25, 22.19, face+thread_back+.12))
    tray = (original + receiver) - guide - on_axis(thread)

    stem_tip = face-stem_length
    body_envelope = (port(outlet.minor_diameter(major, pitch)/2, stem_tip, stem_tip+.76, major/2+.05)
                     + port(19, stem_tip+.75, face+24))
    body = on_axis(original_outlet) ^ body_envelope

    # Require solid support on the entire nominal mounting gland footprint.
    land = (port(ring["gland_outer_radius_mm"], face-.025, face-.005)
            - port(ring["gland_inner_radius_mm"], face-.03, face))
    contact = (land ^ tray).volume() / land.volume()
    threaded_wall = (port(12, face+thread_back, face-.025)
                     - port(10, face+thread_back-.05, face))
    sleeve_fraction = (threaded_wall ^ tray).volume() / threaded_wall.volume()
    web = (port(web_radius, web_start, face+thread_back-.01)
           - port(2.252, web_start-.01, face+thread_back+.01))
    web_fraction = (web ^ tray).volume() / web.volume()
    protected = box(-40, -31, 2.0, 30.3, 31, SEAM_Z+.05)
    loss_under_lid = abs(((original-tray) ^ protected).volume())
    overlap = abs((body ^ tray).volume())
    if (len(tray.decompose()) != 1 or len(body.decompose()) != 1
            or min(contact, sleeve_fraction, web_fraction) < .999
            or loss_under_lid > .001 or overlap > .025):
        raise ValueError(f"Short outlet fit failed: land {contact}, sleeve {sleeve_fraction}, "
                         f"web {web_fraction}, lid relief {loss_under_lid}, overlap {overlap}")

    report.write_text(json.dumps({
        "nominal_face_seal_land_fraction": round(contact, 6),
        "thread_sleeve_coverage_fraction": round(sleeve_fraction, 6),
        "web_coverage_fraction": round(web_fraction, 6),
        "web_depth_mm": round(face+thread_back-web_start, 3),
        "green_stem_length_mm": stem_length,
        "green_body_axial_length_mm": round(body.bounding_box()[3]-body.bounding_box()[0], 3),
        "reused_body_tray_overlap_mm3": round(overlap, 6),
        "removed_tray_material_near_lid_mm3": round(loss_under_lid, 6),
        "nominal_mount_face_squeeze_mm": ring["cross_section_mm"]-ring["gland_depth_mm"],
        "seated_outlet_face_x_mm": face,
        "ptfe_insertion_to_original_stop_mm": round(face+config["tail"]["reference_release_z_mm"]-TUBE_STOP, 3),
        "physical_seal_status": "Untested",
    }, indent=2)+"\n")
    return tray, body


def export_indexed_tray(path, mesh):
    """Write a geometry-only 3MF so curved joints keep their vertex indices."""
    model = ET.Element("model", unit="millimeter",
                       xmlns="http://schemas.microsoft.com/3dmanufacturing/core/2015/02")
    resources = ET.SubElement(model, "resources")
    part = ET.SubElement(resources, "object", id="1", type="model",
                         name="Drybox feeder tray with captive cams")
    indexed = ET.SubElement(part, "mesh")
    vertices = ET.SubElement(indexed, "vertices")
    for x, y, z in mesh.vertices:
        ET.SubElement(vertices, "vertex", x=str(x), y=str(y), z=str(z))
    triangles = ET.SubElement(indexed, "triangles")
    for a, b, c in mesh.faces:
        ET.SubElement(triangles, "triangle", v1=str(a), v2=str(b), v3=str(c))
    ET.SubElement(ET.SubElement(model, "build"), "item", objectid="1")
    with ZipFile(path, "w", ZIP_DEFLATED) as archive:
        archive.writestr("3D/3dmodel.model", ET.tostring(model, encoding="utf-8",
                                                        xml_declaration=True))
        archive.writestr("[Content_Types].xml", """<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">
<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>
<Default Extension="model" ContentType="application/vnd.ms-package.3dmanufacturing-3dmodel+xml"/>
</Types>""")
        archive.writestr("_rels/.rels", """<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
<Relationship Target="/3D/3dmodel.model" Id="rel0" Type="http://schemas.microsoft.com/3dmanufacturing/2013/01/3dmodel"/>
</Relationships>""")


def build_enclosure(out, outlet_dir, *, insert_parts=None, review=None):
    out.mkdir(parents=True, exist_ok=True)
    shapes = base_enclosure(outlet_dir)
    if insert_parts:
        shapes.update({key:insert_parts[key] for key in (
            "frame","wheel","pin","clip","tires","outerRace","tread","shield","innerRace","sleeve","m4")})
    seam = SEAM_Z
    reduced_supports = True
    refined = True
    clean_braces = True
    fit_guides = True
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
    # Recess the annulus below each rotor so removable support has room
    # beneath the first ring and can be accessed from the outside.
    pedestal -= cylinder(5.70,.12,.88)-cylinder(4.00,.10,.90)
    gusset = yz_prism([(15.4,-9.65),(17.7,-9.65),(25.7,-2.08),
                       (27.35,-.45),(26.22,.69),(21.8,.75),(15.4,-.25)],
                     -4.18,4.18)
    if clean_braces:
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
    elif reduced_supports:
        # Carry the whole circular pedestal from the outer tray wall.
        # The underside advances 11.7 mm over a 15.3 mm vertical rise.
        gusset += yz_prism([(15.90,-17.48),(17.47,-17.48),(29.19,-2.18),
                            (29.19,-1.96),(26.70,-1.94),(15.90,-5.2)],-3.15,3.15)
    stop = yz_prism([(16.4,-4.1),(18.5,-3.45),(23.90,3.42),
                     (23.90,8.25),(20.65,8.25),(19.38,5.6),
                     (18.03,1.08),(16.4,.26)],8.05,10.42)
    # At this X position keep the stop below the removable flange.
    stop -= box(7.9,15.0,4.55,10.6,19.98,8.35)
    tray = shapes["tray"] + pair(anchored(post+pedestal)+gusset+stop)
    port_ramps = m.Manifold()
    if clean_braces:
        # Grow the underside of each interior socket from its wall.
        # The cylindrical keepout exceeds the entire threaded bore.
        ramp = xz_prism([(21.92,-10.23),(24.48,-13.52),(25.12,-13.52),
                         (25.12,-8.32),(21.92,-8.32)],-3.30,3.30)
        thread_keepout = cylinder(5.36,21.86,25.24).rotate([0,90,0]).translate([0,0,-4.025])
        port_ramps = (ramp-thread_keepout) + (ramp.mirror([1,0,0])-shapes["passage"])
        if overlap(port_ramps,box(-21.,-12.,-30.,21.,12.,5.)) > .001:
            raise ValueError("Socket ramp enters the feeder clearance")
        tray += port_ramps
    if refined:
        # Blend a wider bed face into the existing profile 0.05 mm
        # below the cavity floor. Everything here is below the cavity.
        blend = 2.15/2.25
        tray += loft([(-35.5,50.4,29.8,7.0),
                      (-32.35,51+3*blend,29+4.4*blend,7+blend)])

    lid_rib = loft([(6.65,*track(3.55)),(7.65,*track(3.55)),(8.04,*track(3.1))])
    lid_rib -= loft([(6.60,*track(-.1)),(8.12,*track(-.1))])
    crown = [(x,catch_height-.074*x*x) for x in np.linspace(2.75,-2.75,33)]
    catch = xz_prism([(-2.75,6.38),(2.75,6.38),*crown],18.25,19.80)
    lid = shapes["cover"] + lid_rib + pair(catch)
    if fit_guides:
        from fit_revision import refine_fit
        previous_fit = tray, lid, shapes["fingers"]
        tray, lid, fingers = refine_fit(tray,lid,shapes,loft,track,yz_prism,box,cylinder,seam)
        shapes = {**shapes,"fingers":fingers}
    # The stem passes the near cheek before the feeder insert is installed.
    # Leave the outer walls and the two snap fingers in their working position.
    tray -= box(-17.35,-9.68,-19.9,-7.84,-6.9,3.20)

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

    if refined:
        # Start with a narrower annulus, then grow the outer rim and
        # inner lead-in toward the full section.
        ring = cylinder(5.16,rotor_bottom,1.72,5.32)+cylinder(5.32,1.72,7.23)
    else:
        ring = cylinder(5.32,rotor_bottom,7.23)
    ring += cylinder(5.32,7.19,10.14,6.0)
    if refined:
        grip_profile = [(4.80,2.00),(5.10,2.00),(13.55,11.42),(13.55,13.72),
                        (12.63,14.42),(10.05,12.49),(4.80,7.65)]
    elif reduced_supports:
        # Start at the ring and grow the underside at about 41° from
        # vertical. The upper profile keeps the grip slim out at its tip.
        grip_profile = [(4.80,2.00),(5.10,2.00),(13.40,11.48),(13.40,12.10),
                        (12.65,12.63),(9.75,9.88),(4.80,6.35)]
    else:
        grip_profile = [(4.80,4.2),(5.42,4.2),(8.75,7.55),(12.85,9.03),
                        (13.85,9.89),(12.97,11.32),(4.8,11.32)]
    lever = xz_prism(grip_profile,-2.15,2.15)
    if refined:
        # Widen the part pressed by the thumb beyond the fixed stop.
        lever += xz_prism([(10.57,9.63),(12.93,10.82),(13.55,11.42),
                            (13.55,13.72),(12.63,14.42),(10.57,12.82)],-3.1,3.1)
    rotor_bore = cylinder(3.55,1.20,8.55)
    if refined:
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
    seal = gasket()
    bottom = SEAM_Z-TPU_RECESS_DEPTH
    seal_compressed = seal.warp(lambda p: (p[0],p[1],p[2]-
        (TPU_HEIGHT-TPU_RECESS_DEPTH)*max(0,p[2]-bottom-TPU_BASE_HEIGHT)/(TPU_HEIGHT-TPU_BASE_HEIGHT)))
    bead_above_seam = seal ^ box(-30,-20,SEAM_Z,30,20,SEAM_Z+.4)
    bulkhead = shapes["bulkhead"]
    slide_room = 30.15
    fixed = tray+shapes["fingers"]
    # Measure the key at the seating plane, where the nut draws it in.
    flange_zone = box(-24.93,-16,-24,-22.22,16,5)
    head = bulkhead^flange_zone
    pocket_wall = tray^flange_zone
    pivot = [0,0,shapes["mountZ"]]
    def turned(part,angle):
        return part.translate([0,0,-pivot[2]]).rotate([angle,0,0]).translate(pivot)
    wrong_orientation = min(overlap(turned(head,angle),pocket_wall) for angle in range(5,360,5))
    clocking_limits = []
    for sign in (-1,1):
        low, high = 0.,5.
        for _ in range(12):
            angle = (low+high)/2
            if overlap(turned(head,sign*angle),pocket_wall)>.001:
                high = angle
            else:
                low = angle
        clocking_limits.append(sign*low)
    def insertion_check(positions):
        worst = 0.
        for pos in positions:
            intersection = bulkhead.translate(pos)^fixed
            volume = abs(intersection.volume())
            if volume>worst:
                worst = volume
                bounds = intersection.bounding_box()
                if worst>.02:
                    print("Bulkhead path interference", np.round(pos,3).tolist(),
                          round(worst,4), np.round(bounds,3).tolist(),flush=True)
        return round(worst,6)
    mount_checks = {
        "wall_x_mm":shapes["wallX"],
        "upstream_liner_length_mm":shapes["linerLength"],
        "wall_to_lid_static_clearance_mm":round(lid.bounding_box()[0]-shapes["wallX"],3),
        "tray_wall_overlap_mm3":round(overlap(tray,shapes["panel"]),6),
        "tray_locknut_overlap_mm3":round(overlap(tray,shapes["locknut"]),6),
        "tray_liner_overlap_mm3":round(overlap(tray,shapes["linerSolid"]),6),
        "bulkhead_case_overlap_mm3":round(overlap(tray,bulkhead),6),
        "bulkhead_locknut_overlap_mm3":round(overlap(bulkhead,shapes["locknut"]),6),
        "bulkhead_wall_overlap_mm3":round(overlap(bulkhead,shapes["panel"]),6),
        "bulkhead_lid_overlap_mm3":round(overlap(bulkhead,lid),6),
        "bulkhead_liner_overlap_mm3":round(overlap(bulkhead,shapes["linerSolid"]),6),
        "minimum_wrong_angle_key_overlap_mm3":round(wrong_orientation,6),
        "centered_clocking_limits_deg":[round(angle,3) for angle in clocking_limits],
        "liner_overlap_at_clocking_limits_mm3":round(max(overlap(
            turned(bulkhead,angle),shapes["linerSolid"]) for angle in clocking_limits),6),
        "bulkhead_lateral_insertion_overlap_mm3":insertion_check(
            ([x,0,0] for x in np.linspace(0,slide_room,65))),
        "bulkhead_drop_in_overlap_mm3":insertion_check(
            ([slide_room,0,z] for z in np.linspace(0,36,73))),
        "pocket_gland_overlap_mm3":round(overlap(shapes["passage"],groove()),6),
        "nominal_bulkhead_seat_area_mm2":round(overlap(bulkhead.translate([-.02,0,0]),tray)/.02,2),
        "lid_lift_mount_overlap_mm3":round(max(overlap(lid.translate([0,0,z]),shapes["mount"])
            for z in np.linspace(0,32,65)),6),
        "bushing_liner_assembly_interference_mm3":round(overlap(shapes["bushing"],shapes["linerSolid"]),5),
    }
    if any(mount_checks[key]>.025 for key in (
        "tray_wall_overlap_mm3","tray_locknut_overlap_mm3","tray_liner_overlap_mm3",
        "lid_lift_mount_overlap_mm3","bulkhead_case_overlap_mm3","bulkhead_locknut_overlap_mm3",
        "bulkhead_wall_overlap_mm3","bulkhead_lid_overlap_mm3","bulkhead_liner_overlap_mm3",
        "bulkhead_lateral_insertion_overlap_mm3","bulkhead_drop_in_overlap_mm3",
        "pocket_gland_overlap_mm3","liner_overlap_at_clocking_limits_mm3")):
        raise ValueError(f"The drybox interface has an unintended collision: {mount_checks}")
    if wrong_orientation<.025:
        raise ValueError("The bulkhead key allows a second seating orientation")
    (out/"mount-checks.json").write_text(json.dumps(mount_checks,indent=2)+"\n")

    tray_with_guides, outlet_body = short_outlet(
        tray + shapes["fingers"], out/"outlet-checks.json")
    printable_tray = tray_with_guides + open_rotors
    # The cam drops on the lower cone before engaging the lid.
    axial_sweep = max(overlap(pose(a,z),tray) for a in np.linspace(0,maximum_angle,106)
                      for z in (-.45,-.3,-.15,0,.15,.3,.45,seat_lift))
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
        "printed_tray_components":len(printable_tray.decompose()),
        "rotor_components":len(rotor.decompose()),
        "cover_components":len(lid.decompose()),
        "rotor_unloaded_tray_overlap_mm3":round(overlap(open_rotors,tray),5),
        "axial_seats_per_post":2,
        "axial_total_overlap_mm3":round(axial_sweep,6),
        "pivot_retains_cam_mm3":round(overlap(pose(0,seat_lift+.20),tray),6),
        "added_material_in_gland_mm3":round(overlap(seal_band,
            (tray-shapes["tray"])+(lid-shapes["cover"])),7),
        "gasket_fill_percent":round(100*seal.volume()/groove().volume(),1),
        "gasket_bead_compression_mm":round(TPU_HEIGHT-TPU_RECESS_DEPTH,3),
        "gasket_compressed_tray_overlap_mm3":round(overlap(seal_compressed,tray),6),
        "gasket_missing_lid_contact_mm3":round(abs((bead_above_seam-lid).volume()),6),
        "worst_interference":{name:round(value,6) for name,value in worst.items()},
        "collision_at":collision_at,
        "closed_size_mm":[round(hi-lo,2) for lo,hi in zip(envelope[:3],envelope[3:])],
    }
    print(json.dumps(checks,indent=2),flush=True)
    (out/"checks.json").write_text(json.dumps(checks,indent=2)+"\n")
    if fit_guides and "frame" in shapes:
        from fit_revision import fit_audit
        result = fit_audit((*previous_fit,pair(closed)),(tray,lid,shapes["fingers"],pair(closed)),
                           shapes["frame"],box,seam)
        insert = shapes["frame"]
        for part in ("wheel","pin","clip","tires","outerRace","tread","shield","innerRace","sleeve","m4"):
            insert += shapes[part]
        new_guides = (tray-previous_fit[0]) ^ box(-21.,-16.,-32.40,21.,16.,4.6)
        result["after"]["new_guide_assembled_lift_peak_mm3"] = round(max(
            overlap(insert.translate([0,0,z]),new_guides) for z in np.linspace(0,38,77)),5)
        retracted = shapes["leftTube"].translate([-9.3,0,0])+shapes["rightTube"].translate([9.3,0,0])
        result["after"]["retracted_liner_insert_lift_peak_mm3"] = round(max(
            overlap(insert.translate([0,0,z]),retracted) for z in np.linspace(0,38,77)),5)
        result["after"]["bulkhead_insert_lift_peak_mm3"] = round(max(overlap(
            insert.translate([0,0,z]),shapes["bulkhead"]) for z in np.linspace(0,38,77)),5)
        print(json.dumps(result,indent=2),flush=True)
        (out/"fit-checks.json").write_text(json.dumps(result,indent=2)+"\n")
        for key in ("nominal_insert_fixed_collision_mm3","fixed_guide_lift_collision_mm3",
                    "new_guide_assembled_lift_peak_mm3","retracted_liner_insert_lift_peak_mm3",
                    "bulkhead_insert_lift_peak_mm3",
                    "finger_wall_collision_at_0_9_mm3"):
            if result["after"][key] > .025:
                raise ValueError(f"Fit verification failed: {key}")
    if max(clearance, axial_sweep, *worst.values(), checks["added_material_in_gland_mm3"],
           checks["port_ramp_hardware_overlap_mm3"],checks["gasket_compressed_tray_overlap_mm3"],
           checks["gasket_missing_lid_contact_mm3"])>.025:
        raise ValueError("An operating position intersects the enclosure")
    if (checks["printed_tray_components"],checks["rotor_components"],
        checks["cover_components"]) != (3,1,1):
        raise ValueError("The two rotors must be separate from the printed tray")
    if not (abs(frames[0][1])<.06 and min(f[1] for f in frames)<frames[0][1]-.025
            and checks["closed_cam_blocks_lid_lift_mm3"]>.05
            and checks["pivot_retains_cam_mm3"]>.05
            and checks["negative_stop_interference_mm3"]>.05):
        raise ValueError("The cam does not draw over center and block lid lift")

    if review:
        review(tray,lid,rotor,shapes,seal,seal_compressed,frames,pivot_y,seat_lift)
    print_parts = {
        "drybox-feeder-tray": printable_tray,
        "lid": lid,
        "bulkhead-threads-up": shapes["bulkhead"].rotate([0, 90, 0]),
        "short-outlet-neck-down": outlet_body.rotate([0, 90, 0]),
        "tpu-lid-gasket": seal,
        "tpu-liner-bushing": shapes["bushing"].rotate([0, -90, 0]),
    }
    for name, part in print_parts.items():
        bounds = part.bounding_box()
        part = part.translate([0,0,-bounds[2]])
        raw = part.to_mesh64()
        mesh = trimesh.Trimesh(raw.vert_properties[:,:3],raw.tri_verts,process=False)
        if not mesh.is_watertight or mesh.volume<=0:
            raise ValueError(f"{name} export is not watertight")
        mesh.export(out/f"{name}.stl")
        if name == "drybox-feeder-tray":
            export_indexed_tray(out/f"{name}.3mf", mesh)
    return printable_tray, lid


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=ROOT/"build"/"manual-feeder")
    parser.add_argument("--outlet-dir", type=Path, default=ROOT/"filament-drybox"/"cad")
    args = parser.parse_args()
    build_enclosure(args.output, args.outlet_dir)


if __name__ == "__main__":
    main()
