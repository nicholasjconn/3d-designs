"""Rebuild the compact removable feeder around the original lower axle."""
from hashlib import sha256
from xml.etree import ElementTree as ET
from zipfile import ZipFile

import manifold3d as m
import numpy as np
import trimesh

from geometry import box, cylinder, overlap, paired, port, yz_prism

SOURCE_SHA256 = "f63fc4309f90cd398fc375f8893881788ced82a32e456bac3c86a73bda76dc13"
NS = "{http://schemas.microsoft.com/3dmanufacturing/core/2015/02}"
PATH = "{http://schemas.microsoft.com/3dmanufacturing/production/2015/06}path"

TUBE_STOP = 17.133
FRAME_END = 20.65
AXLE_X = -.000214
AXLE_Z = -9.526536
WHEEL_Z = 8.1
FLOAT_MIN, FLOAT_MAX = 6.483, 9.064


def import_stock(path):
    if sha256(path.read_bytes()).hexdigest() != SOURCE_SHA256:
        raise ValueError("Expected the verified MakerWorld pneumatic latch profile 3740072")
    with ZipFile(path) as archive:
        settings = ET.fromstring(archive.read("Metadata/model_settings.config"))
        root = ET.fromstring(archive.read("3D/3dmodel.model"))
        frame = next(item for item in settings.findall("object")
                     if item.find("metadata[@key='name']").get("value").startswith("41-"))
        obj = root.find(f".//{NS}object[@id='{frame.get('id')}']")
        component = obj.find(f".//{NS}component")
        if component is not None:
            child = ET.fromstring(archive.read(component.get(PATH).lstrip("/")))
            obj = child.find(f".//{NS}object[@id='{component.get('objectid')}']")
        mesh = obj.find(f"{NS}mesh")
    vertices = [[float(vertex.get(axis)) for axis in "xyz"] for vertex in mesh.find(NS+"vertices")]
    triangles = [[int(face.get(axis)) for axis in ("v1", "v2", "v3")]
                 for face in mesh.find(NS+"triangles")]
    merged = trimesh.Trimesh(vertices, triangles)
    solid = m.Manifold(m.Mesh64(merged.vertices, merged.faces.astype(np.uint64)))
    if solid.status() != m.Error.NoError or len(solid.decompose()) != 1:
        raise ValueError("Original feeder frame is not a single closed solid")
    return solid


def axle(radius, start, end, z=0, tip=-1):
    return cylinder(radius, start, end, tip).rotate([-90, 0, 0]).translate([0, 0, z])


def foot_ramp(start):
    """Grow the foot from the frame in its X-up print orientation."""
    root = box(start-6.15,4.24,-9.93,start-6.11,6.25,-7.52)
    # Keep the ramp inboard of the foot's outer wall to avoid coincident
    # edges at the union that collapse when exported to STL.
    leg = box(start,9.9,-16.,start+.05,12.03,-8.05)
    head = box(start,4.2,-9.5,start+.05,12.03,-7.5)
    return m.Manifold.batch_hull([root,leg,head])


def build(source):
    stock = import_stock(source)
    frame = stock ^ box(-FRAME_END,-12,-20,FRAME_END,12,20)

    # Fill just the retired fitting pockets. Leave the original guides and
    # both PTFE stops at the exact source positions.
    socket = port(3.32,17.22,FRAME_END)
    tube_passage = (port(2.48,17.20,17.60,2.20)
                    + port(2.20,17.58,20.12)
                    + port(2.20,20.10,FRAME_END+.02,2.50))
    frame = (frame + paired(socket,[1,0,0])) - paired(tube_passage ^ socket,[1,0,0])

    def upper_track(radius, start, end):
        return (axle(radius,start,end,FLOAT_MIN) + axle(radius,start,end,FLOAT_MAX)).hull()

    # The previously printed upper 608 hardware and TPU wheel fit this track.
    frame = (frame + upper_track(6.53,-6.95,-5.20)) - upper_track(4.62,-8.8,-4.96)
    # Support the steel axle at both cheeks and keep the outer race clear.
    # Countersunk M3 × 16 and DIN 934 nut are already in the Harker hardware.
    shoulder = axle(2.12,2.08,3.45,AXLE_Z) ^ box(-3,2,-13,3,4,-7.55)
    frame += paired(shoulder,[0,1,0]).translate([AXLE_X,0,0])
    nut_boss = axle(3.65,5.85,6.65,AXLE_Z).translate([AXLE_X,0,0])
    frame += nut_boss
    pilot = axle(1.57,-7.4,7.4,AXLE_Z)+axle(3.12,-7.4,-6.65,AXLE_Z)
    pilot += axle(3.12,-6.67,-4.95,AXLE_Z,1.57)
    frame -= pilot.translate([AXLE_X,0,0])
    bearing = (axle(4,-2,2,AXLE_Z)-axle(1.5,-2.01,2.01,AXLE_Z)).translate([AXLE_X,0,0])
    screw = (axle(3.,-6.65,-4.95,AXLE_Z,1.5)+axle(1.5,-4.96,9.35,AXLE_Z)).translate([AXLE_X,0,0])
    nut = (cylinder(3.175,6.65,9.05,sides=6).rotate([-90,0,0])
           .translate([AXLE_X,0,AXLE_Z]) - axle(1.5,6.64,9.06,AXLE_Z).translate([AXLE_X,0,0]))
    # Raised contact pads are outside the wheel's sweep. The lid limits
    # vertical movement without adding a tight press fit to the cradle.
    grip = box(10.25,5.15,5.6,12.45,6.9,12.30)
    frame += paired(paired(grip,[1,0,0]),[0,1,0])

    # Four feet seat into the tray below the original guides.
    foot = box(11.5,9.9,-16.,14.3,12.05,-8.05)
    foot += yz_prism([(4.2,-10.0),(10.4,-10.4),(12.05,-8.0),(12.05,-7.5),
                     (4.2,-7.5)],11.5,14.3)
    frame += paired(paired(foot,[1,0,0]),[0,1,0])
    frame += paired(foot_ramp(11.5)+foot_ramp(-14.3),[0,1,0])
    protected = box(-17.219,-2.5,-7.45,17.219,2.5,-.5)
    guide_change = overlap((frame-stock)+(stock-frame),protected)
    installed_ptfe = paired(port(2,TUBE_STOP,FRAME_END+.05),[1,0,0])
    result = {
        "protected_contact_geometry_change_mm3":round(guide_change,7),
        "tube_against_frame_mm3":round(overlap(installed_ptfe,frame),7),
        "bare_693_against_frame_mm3":round(overlap(bearing,frame),7),
        "drop_in_bearing_path_mm3":round(max(
            overlap(bearing.translate([0,0,delta]),frame)
            for delta in np.linspace(0,26,66)),7),
        "bare_693_top_tangent_mm":round(AXLE_Z+4,6),
        "lower_axle_bore_mm":3.14,
        "axle_interference_mm3":round(overlap(screw+nut,frame),6),
    }
    if len(frame.decompose()) != 1 or max(
        guide_change, overlap(installed_ptfe,frame), overlap(bearing,frame),
        result["drop_in_bearing_path_mm3"], result["axle_interference_mm3"]
    ) > .025:
        raise ValueError(f"Compact insert failed the guide or bearing checks: {result}")
    return frame, screw, nut, bearing, result
