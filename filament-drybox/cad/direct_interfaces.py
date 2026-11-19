"""Shared current direct-drive datums. Millimetres; X axle, Y up, Z transverse."""
from pathlib import Path
import json
import cadquery as cq
from spindle import thread_profiles, _helical

def config():
    return json.loads(Path(__file__).with_name('direct_drive.json').read_text())

def box(x0,x1,y0,y1,z0,z1):
    return cq.Solid.makeBox(x1-x0,y1-y0,z1-z0,cq.Vector(x0,y0,z0))

def cyl(r,x0,x1,y=104):
    return cq.Solid.makeCylinder(r,x1-x0,cq.Vector(x0,y,0),cq.Vector(1,0,0))

def tube(ro,ri,x0,x1,y=104):
    return cyl(ro,x0,x1,y).cut(cyl(ri,x0-.1,x1+.1,y))

def tooth(c,profile,x0,x1,phase):
    return _helical(profile,c['port']['thread_pitch'],x0,x1,phase,c['bearings']['axis_y'],False)

def one(s,name):
    s=s.clean()
    if not s.isValid() or len(s.Solids())!=1:
        raise ValueError(name+': expected one valid native solid')
    return s
