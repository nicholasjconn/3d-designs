#!/usr/bin/env python3
# SUPERSEDED 17 Nov 2026: high-flow center cartridge, replaced by the spindle and locking collar
# (spindle.py / stand.json). Kept for history; not a current print input. See ../README.md.
"""Native journal/cup additions for the private reference-cartridge adaptation.

This source is original adapter geometry. The separately downloaded third-party
reference and every combined mesh/3MF remain private. This is an unqualified
empty-fit prototype, not a released storage cartridge.
"""
from pathlib import Path
import argparse
import json
import cadquery as cq

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--output', type=Path, required=True)
args = parser.parse_args()
P = args.output.resolve()
P.mkdir(parents=True, exist_ok=False)
Y = 104
C = {'axle': {'key_start_x': 36.1, 'right_end_x': 43.2, 'key_apothem': 3.75, 'groove_start_x': 39.6, 'groove_end_x': 41.800000000000004, 'groove_radius': 3.2}}

def one(shape, name):
    if not shape.isValid() or len(shape.Solids()) != 1:
        raise ValueError(f'{name}: expected one valid solid')
    return shape

def join(shapes):
    shape = shapes[0]
    for other in shapes[1:]:
        shape = shape.fuse(other)
    return one(shape.clean(), 'union')

def box(x0,x1,y0,y1,z0,z1):
    return cq.Solid.makeBox(x1-x0,y1-y0,z1-z0,cq.Vector(x0,y0,z0))

def cylinder_x(radius, x0, length, y):
    return cq.Solid.makeCylinder(radius,length,cq.Vector(x0,y,0),cq.Vector(1,0,0))

def cy(r,z,h):return cq.Solid.makeCylinder(r,h,cq.Vector(0,0,z))
def ann(ro,ri,z,h):return cy(ro,z,h).cut(cy(ri,z-.01,h+.02))
def spoke(end,z,h,a):
 w=cq.Workplane('XY').moveTo(0,-2.5).lineTo(end-2.5,-2.5).threePointArc((end,0),(end-2.5,2.5)).lineTo(0,2.5).close().extrude(h).val().translate((0,0,z))
 return w.rotate((0,0,0),(0,0,1),a)

def journal(drive):
 # Local Z points into desiccant from the recessed end plane.
 end=23 if drive else 16.6
 s=join([cy(7,-.2,3.4),cy(4,-(16.2 if drive else 9.2),16.4 if drive else 9.4),*[spoke(end,0,3,a)for a in [90,210,330]]])
 edges=[e for e in s.Edges()if e.geomType()=='CIRCLE'and abs(e.radius()-4)<1e-6 and abs(e.Center().z+.2)<1e-6]
 if len(edges)!=1:raise ValueError(('journal root',len(edges)))
 s=s.fillet(1.4,edges)
 sleeve=cq.Solid.makeCone(7,5.8,1.6,cq.Vector(0,0,-.2),cq.Vector(0,0,-1)).cut(cq.Solid.makeCone(5.8,4.2,1.6,cq.Vector(0,0,-.2),cq.Vector(0,0,-1)))
 s=join([s,sleeve])
 # Map directly to the unchanged legacy shaft journal/end/key coordinates.
 if drive:s=s.rotate((0,0,0),(0,1,0),-90).translate((27,Y,0))
 else:s=s.rotate((0,0,0),(0,1,0),90).translate((-27,Y,0))
 if drive:
  a=C['axle']
  for angle in range(0,360,60):s=s.cut(box(a['key_start_x'],a['right_end_x']+.1,Y+a['key_apothem'],Y+8,-8,8).rotate((0,Y,0),(1,Y,0),angle))
  gr=cylinder_x(4.1,a['groove_start_x'],a['groove_end_x']-a['groove_start_x'],Y).cut(cylinder_x(a['groove_radius'],a['groove_start_x']-.1,a['groove_end_x']-a['groove_start_x']+.2,Y))
  s=s.cut(gr)
 return one(s.clean(),'legacy-position journal')

# End containment cups, in original reference source coordinates.
# Clear R14 stationary carrier with R15.2 bore; leave original outer flange.
body_wall=ann(16.6,15.2,0,8.4)
body_floor=cy(16.6,7,1.4)
cap_wall=ann(16.6,15.2,59.6,8.4)
cap_floor=cy(16.6,59.6,1.4)
# Three short radial ribs join the cap cup to the original threaded rim.
cap_ribs=[]
for a in [90,210,330]:
 s=spoke(21.2,65,3,a).cut(cy(15.2,64.9,3.2));cap_ribs.append(s)
cap_cup=join([cap_wall,*cap_ribs])
# Union reinforcement with original normal mesh, then replace its floor
# infill only in new void-filling regions. Original duct walls stay structural.
parts = {
    'body-journal': journal(True), 'cap-journal': journal(False),
    'body-wall': body_wall, 'body-floor': body_floor,
    'cap-wall': cap_cup, 'cap-floor': cap_floor,
}
for name, shape in parts.items():
    one(shape, name)
    cq.exporters.export(shape, str(P / (name + '.stl')), tolerance=.04,
                        angularTolerance=.15)
    cq.exporters.export(shape, str(P / (name + '.step')))
(P / 'native-checks.json').write_text(json.dumps({
    name: {'valid': shape.isValid(), 'solids': len(shape.Solids()),
           'volume_mm3': shape.Volume()} for name, shape in parts.items()
}, indent=2) + '\n')
