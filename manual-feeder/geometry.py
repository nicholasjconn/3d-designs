"""Triangulated lofts and print export helpers."""
from xml.etree import ElementTree as ET
from zipfile import ZIP_DEFLATED, ZipFile

import manifold3d as m
import numpy as np
import trimesh

TUBE_Z = -4.025


def box(x0, y0, z0, x1, y1, z1):
    return m.Manifold.cube([x1-x0, y1-y0, z1-z0]).translate([x0,y0,z0])

def cylinder(radius, lower, upper, upper_radius=-1, sides=96):
    return m.Manifold.cylinder(upper-lower, radius, upper_radius, sides).translate([0,0,lower])

def port(radius, start, end, end_radius=-1, sides=96):
    return cylinder(radius,start,end,end_radius,sides).rotate([0,90,0]).translate([0,0,TUBE_Z])

def paired(shape, axis):
    return shape + shape.mirror(axis)

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

def yz_prism(points, x0, x1):
    return (m.CrossSection([points],m.FillRule.NonZero).extrude(x1-x0)
            .transform([[0,0,1,x0],[1,0,0,0],[0,1,0,0]]))

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


def overlap(first, second):
    return abs((first ^ second).volume())


def to_mesh(part):
    raw = part.to_mesh64()
    mesh = trimesh.Trimesh(raw.vert_properties[:, :3], raw.tri_verts, process=False)
    if not mesh.is_watertight or not mesh.is_winding_consistent or mesh.volume <= 0:
        raise ValueError("Invalid mesh export")
    return mesh


def print_mesh(part, rotation=(0, 0, 0)):
    posed = part.rotate(rotation)
    return to_mesh(posed.translate([0, 0, -posed.bounding_box()[2]]))
