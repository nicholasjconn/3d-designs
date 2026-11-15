#!/usr/bin/env python3
"""One native concept stand: tangent A frames, open cradles, integral drive wings.
Bambu PLA Basic fit prototype selected; no manufacturing preset or fabrication approval.
"""
from pathlib import Path
import json,math
import cadquery as cq
HERE=Path(__file__).resolve().parent

def one(s,name):
 if not s.isValid() or len(s.Solids())!=1:raise ValueError(f'{name}: invalid or not one solid ({len(s.Solids())})')
 return s

def join(shapes):
 s=shapes[0]
 for a in shapes[1:]:s=s.fuse(a)
 return one(s.clean(),'union')

def box(x0,x1,y0,y1,z0,z1):return cq.Solid.makeBox(x1-x0,y1-y0,z1-z0,cq.Vector(x0,y0,z0))
def cylinder_x(r,x0,length,y,z=0):return cq.Solid.makeCylinder(r,length,cq.Vector(x0,y,z),cq.Vector(1,0,0))
def volume(s):return sum(a.Volume() for a in s.Solids())
def overlap(a,b):return volume(a.intersect(b))
def wire_zy(points):return cq.Workplane('YZ').polyline([(y,z) for z,y in points]).close().val()
def rounded_wire(w,r):return cq.Face.makeFromWires(w).fillet2D(r,w.Vertices()).outerWire()
def extrude(w,x0,thickness,holes=[]):return cq.Solid.extrudeLinear(w,holes,cq.Vector(thickness,0,0)).translate((x0,0,0))

def make_base(c):
 b=c['base'];w,d=b['width']/2,b['depth']/2;i,j=b['opening']/2,d-b['crossbeam_depth']
 # XZ plane profile; positive global Y extrusion.
 outer=cq.Workplane('XZ').rect(2*w,2*d).val();outer=rounded_wire(outer,b['outer_corner_radius'])
 inner=cq.Workplane('XZ').rect(2*i,2*j).val();inner=rounded_wire(inner,b['inner_corner_radius'])
 return one(cq.Solid.extrudeLinear(outer,[inner],cq.Vector(0,b['height'],0)),'open base')

def a_outline(c):
 p=c['frame_profile'];zfoot,yfoot=p['foot_centers_zy'][1];rf=p['foot_radius'];zh,yh=p['head_center_zy'];rh=p['head_radius']
 # Exact common tangent to foot/head circles, mirrored about Z0.
 dz,dy=zh-zfoot,yh-yfoot;length=math.hypot(dz,dy);uz,uy=dz/length,dy/length
 k=(rf-rh)/length;v=math.sqrt(1-k*k)
 nz,ny=uy*v+uz*k,-uz*v+uy*k
 foot=(zfoot+rf*nz,yfoot+rf*ny);head=(zh+rh*nz,yh+rh*ny)
 wp=cq.Workplane('YZ').moveTo(yfoot-rf,-zfoot).lineTo(yfoot-rf,zfoot)
 wp=wp.threePointArc((yfoot,zfoot+rf),(foot[1],foot[0])).lineTo(head[1],head[0])
 wp=wp.threePointArc((yh+rh,0),(head[1],-head[0])).lineTo(foot[1],-foot[0])
 return wp.threePointArc((yfoot,-zfoot-rf),(yfoot-rf,-zfoot)).close().val()

def wing(c,side):
 # One smooth broad curved load path from bearing-head/leg junction to nose.
 # It is part of the same X-thick frame, not a thin axial stub or flexure.
 wp=cq.Workplane('YZ').moveTo(90,side*9)
 wp=wp.bezier([(100,side*22),(109,side*40),(110,side*47)],includeCurrent=True)
 wp=wp.threePointArc((104,side*51),(98,side*47))
 wp=wp.bezier([(95,side*37),(84,side*29),(80,side*23)],includeCurrent=True).close()
 return extrude(wp.val(),35,c['wall_stops']['wing_thickness_x'])

def make_frame(c,x,drive=False):
 p=c['frame_profile'];b=c['bearings'];t=p['thickness'];x0=x-t/2
 hole=rounded_wire(wire_zy(p['window_vertices_zy']),p['window_corner_radius'])
 frame=extrude(a_outline(c),x0,t,[hole])
 if drive:frame=join([frame,wing(c,1),wing(c,-1)])
 # The 7 mm bearing occupies the central 7.4 mm pocket. The side shoulders
 # lie outside its faces; a fully open vertical slot permits upward service.
 tools=[cylinder_x(b['shoulder_open_radius'],x0-.1,t+.2,b['axis_y']),
        box(x0-.1,x0+t+.1,b['axis_y'],135,-b['shoulder_open_radius'],b['shoulder_open_radius']),
        cylinder_x(b['seat_radius'],x-b['pocket_width']/2,b['pocket_width'],b['axis_y']),
        box(x-b['pocket_width']/2,x+b['pocket_width']/2,b['axis_y'],135,-b['seat_radius'],b['seat_radius'])]
 for tool in tools:frame=frame.cut(tool)
 return one(frame.clean(),'A frame')

def supported_nose(c,y,z):
 """Retain the rounded contact; grow its underside from the existing wing.

 The lower outside end tapers fore/aft so no full-width strip starts in air.
 Wall-contact point and upper circular patch are retained, without extra ribs.
 """
 s=c['wall_stops'];p=s['nose_underside'];side=1 if z>0 else -1
 nose=cq.Solid.makeCylinder(s['nose_radius'],s['nose_depth_z'],cq.Vector(s['nose_center_x'],y,z-s['nose_depth_z']/2),cq.Vector(0,0,1))
 y0=p['start_y'];y1=p['tangent_y'];x0=p['start_outer_x'];x1=p['tangent_outer_x'];zi=p['inner_z'];z0=p['start_outer_z'];z1=z0+y1-y0
 def section(yy,xx,zz):
  return cq.Wire.makePolygon([cq.Vector(35,yy,side*zi),cq.Vector(xx,yy,side*zi),cq.Vector(xx,yy,side*zz),cq.Vector(35,yy,side*zz)],close=True)
 apron=cq.Solid.makeLoft([section(y0,x0,z0),section(y1,x1,z1)],ruled=True)
 # Keep positive-side Z <= Y + z0-y0, mirrored on the other nose.
 keep=extrude(wire_zy([(side*30,90),(side*(z0+90-y0),90),(side*(z0+120-y0),120),(side*30,120)]),30,30)
 return one(nose.intersect(keep).fuse(apron).clean(),'supported rounded nose')

def build(c):
 base=make_base(c);left=make_frame(c,-40);right=make_frame(c,40,True)
 s=c['wall_stops'];noses=[supported_nose(c,y,z) for y,z in s['nose_centers_yz']]
 stand=join([base,left,right,*noses])
 return stand,{'base':base,'left-frame':left,'drive-frame':right,'noses':noses}

def mesh(shape):
 if __package__:
  from .cad_helpers import absolute_tessellation
 else:
  from cad_helpers import absolute_tessellation
 verts,tris=absolute_tessellation(shape,tolerance=.1,angular_tolerance=.25)
 return {'vertices':[[round(v.x,5),round(v.y,5),round(v.z,5)] for v in verts],'triangles':[list(t) for t in tris]}

def bounds(s):
 from OCP.BRepBndLib import BRepBndLib
 from OCP.Bnd import Bnd_Box
 b=Bnd_Box();BRepBndLib.AddOptimal_s(s.wrapped,b,False,False)
 x0,y0,z0,x1,y1,z1=b.Get()
 return {'x':[x0,x1],'y':[y0,y1],'z':[z0,z1]}


def parameters(c):
 b,f,br,ws,e=(c[k] for k in ['base','frame_profile','bearings','wall_stops','envelopes'])
 positive_bearing=max(br['centers_x'])
 return {'baseWidth':b['width'],'baseDepth':b['depth'],'baseHeight':b['height'],
         'baseOpening':b['opening'],'baseOffsetX':0,'crossBeamDepth':b['crossbeam_depth'],
         'axisY':br['axis_y'],'bearingX':positive_bearing,'bearingW':br['width'],
         'bearingOD':br['od'],'bearingID':br['id'],'postW':f['thickness'],
         'spoolD':2*e['spool_radius'],'spoolW':e['spool_width'],
         'driveBack':e['rotor_x'][0],'driveFront':e['drive_face_x'],'driveR':e['rotor_radius'],
         'airGap':e['inner_air'],'stopZ':max(abs(z) for y,z in ws['nose_centers_yz']),
         'stopNoseR':ws['nose_radius'],'wallContactX':ws['max_x'],
         'frameThickness':f['thickness'],'cradleRadius':br['seat_radius'],
         'frameOpeningNominalX':2*(positive_bearing-f['thickness']/2)}


def load_config(path=None):
 return json.loads(Path(path or HERE/'stand.json').read_text())


def main():
 """Small CLI adapter; geometry is built independently by build(config)."""
 import argparse
 if __package__:
  from .cad_helpers import export_step
 else:
  from cad_helpers import export_step
 parser=argparse.ArgumentParser(description=__doc__)
 parser.add_argument('--config',type=Path,default=HERE/'stand.json')
 parser.add_argument('--output',type=Path,default=HERE.parents[1]/'build/filament-drybox')
 args=parser.parse_args();out=args.output.resolve();out.mkdir(parents=True,exist_ok=True)
 config=load_config(args.config);stand,_=build(config)
 export_step(stand,out/'stand.step')
 result={'units':'mm','valid':stand.isValid(),'solid_count':len(stand.Solids()),'volume_mm3':stand.Volume(),'bbox_mm':bounds(stand),'config':config,'scope':'Source portability and geometry identity only; not new fit, strength or fabrication qualification'}
 (out/'stand-build.json').write_text(json.dumps(result,indent=2)+'\n')
 (out/'stand-display.json').write_text(json.dumps({'units':'mm','full':mesh(stand)},separators=(',',':')))
 print(json.dumps({key:result[key] for key in ['valid','solid_count','volume_mm3','bbox_mm']}))


if __name__=='__main__':
 main()
