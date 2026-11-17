#!/usr/bin/env python3
"""Drybox spool holder: spoked frame with four anchor branches (glue pockets for the outside X's paired magnets),
two removable bearing carriers, printed spindle and threaded collar, magnetic disc and clip, plus two 608s.

The spindle and collar (cad/spindle.py) clamp the spool by its bore-end chamfers.
Bearing-seat and clip insertion require elastic movement; native fit checks do not establish
snap force, strength, creep, carrier retention or printability.
"""
from pathlib import Path
import json,math
import cadquery as cq
HERE=Path(__file__).resolve().parent


def datums(c):
 e=c['envelopes'];f=c['frame_profile'];b=c['bearings'];p=c['base']['expansion_pilots']
 inner=e['spool_width']/2+e['spool_side_clearance'];outer=inner+f['thickness']
 rotor_front=c['disc']['front_x'];contact=rotor_front+e['inner_air'];pad=p['diameter']+2*p['wall']
 if min(p['diameter'],p['depth'],p['wall'])<=0:raise ValueError('Pilot dimensions must be positive')
 if c['base']['depth']/2<p['center_z']+pad/2-1e-7:raise ValueError('Pilot pads exceed base depth')
 if not 0<b['mouth_width']<b['od']:raise ValueError('C-seat mouth must retain the bearing OD')
 return {'frame_inner':inner,'frame_outer':outer,'base_width':2*outer,'base_opening':2*inner,
  'wall_contact':contact,
  'pilot_pad_size':pad,'pilot_axis_y':pad/2,'pilot_entry_x':-outer,
  'pilot_bottom_x':-outer+p['depth'],'pilot_pad_end_x':-outer+p['depth']+p['wall'],
  'minimum_wall_span':contact+max(outer,b['left_carrier_outer_x'])}

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

def extrude(w,x0,thickness,holes=()):return cq.Solid.extrudeLinear(w,list(holes),cq.Vector(thickness,0,0)).translate((x0,0,0))

def make_base(c):
 b=c['base'];v=datums(c);w,d=v['base_width']/2,b['depth']/2;i,j=v['base_opening']/2,d-b['crossbeam_depth']
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

def expansion_pilot_pads(c):
 """Two plain blind bores with material reserved for future printed screws."""
 p=c['base']['expansion_pilots'];v=datums(c);size=v['pilot_pad_size'];pads=[]
 for side in [-1,1]:
  z=side*p['center_z']
  pad=box(v['pilot_entry_x'],v['pilot_pad_end_x'],0,size,z-size/2,z+size/2)
  bore=cylinder_x(p['diameter']/2,v['pilot_entry_x']-.1,p['depth']+.1,v['pilot_axis_y'],z)
  pads.append(one(pad.cut(bore).clean(),'plain future expansion-screw pilot pad'))
 return pads

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

def jaw_flat(c):
 """Spoke datum: the former flattened bearing-jaw top height and the Z of its outer corner."""
 b=c['bearings'];y=b['axis_y'];R=b['carrier_radius']
 flat=y+math.sqrt(R**2-(b['mouth_width']/2)**2)-b['mouth_tip_trim']
 return flat,math.sqrt(R**2-(flat-y)**2)

def wheel_guard(c):
 """Open U-rim guard with two upper spokes, small junction rounds, a central brace and 45-degree rim undersides at the brace and legs, carried by the right A-frame legs."""
 d=datums(c);b=c['bearings'];r=c['drive_support'];y=b['axis_y'];x0=d['frame_inner'];x1=d['wall_contact']
 inner=r['rotor_clear_radius'];depth=x1-x0
 # Straight U-shaped guard; no added underside ramps.
 rim=cylinder_x(r['rim_outer_radius'],x0,depth,y).cut(cylinder_x(inner,x0-.1,depth+.2,y))
 rim=rim.cut(box(x0-.1,x1+.1,y,y+80,-inner,inner))
 # Two straight upper spokes: top edge runs from the flattened jaw corner to the rim's outer corner at the cap height.
 # The rim arm above that line is trimmed so the spoke top and rim top form one face.
 cap=128.;R=r['rim_outer_radius'];t=c['frame_profile']['thickness'];w=r['spoke_width'];flat,zj=jaw_flat(c);zc=math.sqrt(R**2-(cap-y)**2)
 # Right-side geometry relative to the axis (z, y-axis_y); the left side is its mirror.
 p0=(zj,flat-y);p1=(zc,cap-y);L=math.hypot(p1[0]-p0[0],p1[1]-p0[1]);u=((p1[0]-p0[0])/L,(p1[1]-p0[1])/L);n=(u[1],-u[0])
 a=p0[0]*u[0]+p0[1]*u[1];S=(p0[0]-a*u[0],p0[1]-a*u[1]);E=(p1[0]+20*u[0],p1[1]+20*u[1])
 quad=lambda k:[S,E,(E[0]+k*n[0],E[1]+k*n[1]),(S[0]+k*n[0],S[1]+k*n[1])]
 # Small concave round where each spoke underside meets the leg's outer edge (same radius as the frame window corners).
 def meet(p,d,q,e):
  k=((q[0]-p[0])*e[1]-(q[1]-p[1])*e[0])/(d[0]*e[1]-d[1]*e[0]);return (p[0]+k*d[0],p[1]+k*d[1])
 leg=[e for e in a_outline(c).Edges() if e.geomType()=='LINE' and min(v.Z for v in e.Vertices())>0][0]
 (fz,fy),(hz,hy)=sorted(((v.Z,v.Y-y) for v in leg.Vertices()),key=lambda q:q[1]);ll=math.hypot(hz-fz,hy-fy);ld=((hz-fz)/ll,(hy-fy)/ll)
 P=(p0[0]+w*n[0],p0[1]+w*n[1]);A=meet(P,u,(fz,fy),ld);e2=(-ld[0],-ld[1])
 bis=(u[0]+e2[0],u[1]+e2[1]);bl=math.hypot(*bis);bis=(bis[0]/bl,bis[1]/bl);half=math.acos(u[0]*e2[0]+u[1]*e2[1])/2
 rr=c['frame_profile']['window_corner_radius'];tl=rr/math.tan(half);cl=rr/math.sin(half)
 T1=(A[0]+tl*u[0],A[1]+tl*u[1]);T2=(A[0]+tl*e2[0],A[1]+tl*e2[1]);M=(A[0]+(cl-rr)*bis[0],A[1]+(cl-rr)*bis[1]);A0=(A[0]-bis[0],A[1]-bis[1])
 members=[]
 for s in [1,-1]:
  m=lambda pts:wire_zy([(s*z,y+v) for z,v in pts])
  rim=rim.cut(extrude(m(quad(-80)),x0-.1,depth+.2))
  g=lambda q:(y+q[1],s*q[0])
  round_=cq.Workplane('YZ').moveTo(*g(A0)).lineTo(*g(T1)).threePointArc(g(M),g(T2)).close().val()
  members+= [extrude(m(quad(w)),x0,t).intersect(cylinder_x(R,x0,t,y)),extrude(round_,x0,t)]
 # Central vertical brace, spoke width, from the base crossbeam into the bottom of the rim band.
 p=c['frame_profile'];brace=box(x0,x0+t,p['foot_centers_zy'][1][1]-p['foot_radius'],y-(inner+R)/2,-w/2,w/2)
 # One 45-degree axial underside below the rim's bottom projection, in line with the brace.
 xb=x0+t;bot=y-R;top=y-(inner+R)/2
 sec=cq.Workplane('XY').polyline([(xb-.1,bot-(x1-xb+.1)),(x1,bot),(x1,top),(xb-.1,top)]).close().val()
 wedge=cq.Solid.extrudeLinear(sec,[],cq.Vector(0,0,w)).translate((0,0,-w/2))
 # 45-degree axial undersides where the rim projects past the two legs: the rim's lower band swept down at 45 degrees
 # from its outer face to the frame face, kept inside the existing leg outlines.
 ring=[cq.Wire.makeCircle(k,cq.Vector(x1,y,0),cq.Vector(1,0,0)) for k in (R,inner)]
 sweep=cq.Solid.extrudeLinear(ring[0],[ring[1]],cq.Vector(xb-x1,xb-x1,0))
 hole=rounded_wire(wire_zy(p['window_vertices_zy']),p['window_corner_radius'])
 legs=extrude(a_outline(c),xb-.1,x1-xb+.1,[hole]).intersect(box(xb-.1,x1,0,y,-70,70))
 return join([rim,*members,brace,wedge,sweep.intersect(legs)])


def anchors(c):
 """Anchor magnet axes (y, z) of the outside X and the matching frame pockets."""
 m=c['mount'];y=c['bearings']['axis_y'];r=m['anchor_radius']
 return [(y+r*math.sin(math.radians(a)),r*math.cos(math.radians(a))) for a in m['anchor_angles_deg']]

def strip(p,q,w,x0,x1):
 """Straight strip of width w in the YZ plane from p=(y,z) to q=(y,z), from x0 to x1."""
 dy,dz=q[0]-p[0],q[1]-p[1];L=math.hypot(dy,dz);ny,nz=-dz/L*w/2,dy/L*w/2
 pts=[(p[1]+nz,p[0]+ny),(q[1]+nz,q[0]+ny),(q[1]-nz,q[0]-ny),(p[1]-nz,p[0]-ny)]
 return extrude(wire_zy(pts),x0,x1-x0)

def anchor_branches(c):
 """Four integral branches from the drive guard to the anchor pads, front face on the wall-contact plane (pockets cut in frame())."""
 m=c['mount'];i=m['inside'];y=c['bearings']['axis_y'];x1=datums(c)['wall_contact'];x0=x1-i['depth'];rr=i['root_radius']
 lower=c['envelopes']['rotor_radius']+i['lower_root_disc_clearance']+rr
 parts=[]
 for ay,az in anchors(c):
  s=1 if az>0 else -1
  root=(y+i['upper_root_zy'][1],s*i['upper_root_zy'][0]) if ay>y else (y-lower*math.sqrt(.5),s*lower*math.sqrt(.5))
  parts.append(join([strip(root,(ay,az),m['arm_width'],x0,x1),cylinder_x(rr,x0,i['depth'],*root),cylinder_x(m['anchor_pad_radius'],x0,i['depth'],ay,az)]))
 return cq.Compound.makeCompound(parts)

def anchor_pockets(c,x_face,inward):
 """Glue pockets for the anchor magnets, open at x_face; inward=-1 deepens toward -X (frame), +1 toward +X (outside X)."""
 m=c['mount'];r=c['magnets']['pocket_radius'];d=m['anchor_pocket_depth']
 return [cylinder_x(r,x_face-d-.1 if inward<0 else x_face-.1,d+.2,ay,az) for ay,az in anchors(c)]

def spool_relief(c):
 """The 0.5 mm recess of both plate inner faces, only where the spool flanges sweep (annulus about the axle)."""
 d=datums(c);r=c['frame_profile']['spool_relief'];y=c['bearings']['axis_y'];x=d['frame_inner']
 cut=[]
 for side in [-1,1]:
  ring=cylinder_x(r['outer_radius'],x-2,2+r['depth'],y).cut(cylinder_x(r['inner_radius'],x-2.1,2.2+r['depth'],y))
  cut.append(ring if side>0 else ring.mirror('YZ'))
 return cq.Compound.makeCompound(cut)


def frame(c):
 """Two continuous A-frames with keyed seats for the removable bearing carriers, an open U-rim guard and four anchor branches."""
 d=datums(c);t=c['frame_profile']['thickness']
 hole=rounded_wire(wire_zy(c['frame_profile']['window_vertices_zy']),c['frame_profile']['window_corner_radius'])
 left=extrude(a_outline(c),-d['frame_outer'],t,[hole]);right=extrude(a_outline(c),d['frame_inner'],t,[hole])
 body=join([make_base(c),left,right,*expansion_pilot_pads(c),wheel_guard(c),anchor_branches(c)])
 for pocket in anchor_pockets(c,d['wall_contact'],-1):body=body.cut(pocket)
 body=body.cut(spool_relief(c))
 p=c['base']['expansion_pilots']
 for side in [-1,1]:body=body.cut(cylinder_x(p['diameter']/2,d['pilot_entry_x']-.1,p['depth']+.1,d['pilot_axis_y'],side*p['center_z']))
 # Keyed seats for the removable carriers: a vertical slot down to the carrier's flat bottom, with the two guide
 # edges thinned to a tongue that runs in each carrier's axial grooves. Nothing stationary enters the spool bore.
 k=c['carriers'];y=c['bearings']['axis_y'];top=y+80;zs=k['slot_half_width'];zg=k['guide_half_width'];x0=d['frame_inner']-.01;x1=d['frame_outer']+.1
 seat=[box(x0,x1,k['floor_y'],top,-zs,zs)]+[box(xa,xb,k['floor_y'],y+c['bearings']['carrier_radius'],z0,z1) for z0,z1 in [(-zg,-zs+.01),(zs-.01,zg)] for xa,xb in [(x0,k['tongue_x'][0]),(k['tongue_x'][1],x1)]]
 for side in [-1,1]:
  for cut in seat:body=body.cut(cut if side>0 else cut.mirror('YZ'))
 return one(body.clean(),'screwless frame with removable-carrier seats and anchor branches')


def drive_rotor(c):
 d=c['disc'];a=c['axle'];m=c['magnets'];y=c['bearings']['axis_y'];front=d['front_x']
 pieces=[cylinder_x(d['thrust_radius'],d['thrust_start_x'],d['hub_start_x']-d['thrust_start_x'],y),cylinder_x(d['hub_radius'],d['hub_start_x'],front-d['hub_start_x'],y),cylinder_x(c['envelopes']['rotor_radius'],d['web_back_x'],front-d['web_back_x'],y)]
 for i in range(m['count']):
  angle=i*2*math.pi/m['count'];pieces.append(cylinder_x(m['cup_outer_radius'],m['cup_back_x'],front-m['cup_back_x'],y+m['pitch_radius']*math.cos(angle),m['pitch_radius']*math.sin(angle)))
 disc=join(pieces)
 for i in range(m['count']):
  angle=i*2*math.pi/m['count'];disc=disc.cut(cylinder_x(m['pocket_radius'],m['cup_back_x']-.1,front-m['front_cover']-m['cup_back_x']+.1,y+m['pitch_radius']*math.cos(angle),m['pitch_radius']*math.sin(angle)))
 bore=cylinder_x(a['journal_radius']+d['key_radial_clearance'],d['key_bore_start_x'],front-d['key_bore_start_x']+.2,y)
 for i in range(a['key_flats']):bore=bore.intersect(box(d['key_bore_start_x']-.1,front+.2,y-2*a['journal_radius'],y+a['key_apothem']+d['key_radial_clearance'],-2*a['journal_radius'],2*a['journal_radius']).rotate((0,y,0),(1,y,0),i*360/a['key_flats']))
 disc=disc.cut(bore).cut(cylinder_x(d['counterbore_radius'],d['counterbore_back_x'],front-d['counterbore_back_x']+.1,y))
 channel=box(d['counterbore_back_x'],front+.1,y,y+d['clip_channel_reach'],-d['clip_channel_width']/2,d['clip_channel_width']/2).rotate((0,y,0),(1,y,0),d['clip_channel_angle_deg'])
 return one(disc.cut(channel).clean(),'keyed magnetic disc with radial clip access')


def retaining_clip(c):
 p=c['clip'];d=c['disc'];y=c['bearings']['axis_y'];x=p['start_x']
 clip=cylinder_x(p['outer_radius'],x,p['thickness'],y).cut(cylinder_x(p['bore_radius'],x-.1,p['thickness']+.2,y))
 mouth=box(x-.1,x+p['thickness']+.1,y-d['counterbore_radius'],y,-p['mouth_width']/2,p['mouth_width']/2).rotate((0,y,0),(1,y,0),d['clip_channel_angle_deg'])
 return one(clip.cut(mouth).clean(),'single radial U retaining clip')


def bearing_pair(c):
 b=c['bearings'];parts={};y=b['axis_y']
 for side,name in [(-1,'left-bearing'),(1,'right-bearing')]:
  x=side*b['center_x']-b['width']/2
  parts[name]=cylinder_x(b['od']/2,x,b['width'],y).cut(cylinder_x(b['id']/2,x-.1,b['width']+.2,y))
 return parts


def carrier(c,side):
 """Removable keyed C-seat carrier. It lifts out with the spindle and bearing; gravity alone seats it."""
 b=c['bearings'];k=c['carriers'];y=b['axis_y'];x0=b['carrier_inner_x'];x1=datums(c)['frame_outer'];R=b['carrier_radius']
 pocket=b['center_x']-b['width']/2-b['axial_seat_clearance']
 s=cylinder_x(R,x0,x1-x0,y).cut(box(x0-.1,x1+.1,y-R-10,k['floor_y'],-R-1,R+1))
 s=s.cut(cylinder_x(b['od']/2+b['radial_seat_clearance'],pocket,b['width']+2*b['axial_seat_clearance'],y))
 s=s.cut(cylinder_x(b['lip_open_radius'],x0-.1,x1-x0+.2,y)).cut(box(x0-.1,x1+.1,y,y+R+1,-b['mouth_width']/2,b['mouth_width']/2))
 g=k['groove_half_width'];zg=k['guide_half_width'];gx=k['groove_x']
 for z0,z1 in [(-zg,-g),(g,zg)]:s=s.cut(box(gx[0],gx[1],k['floor_y']-.1,y+R+2,z0,z1))
 s=one(s.clean(),'keyed removable carrier')
 return s if side>0 else s.mirror('YZ')


def spindle_module():
 if __package__:from . import spindle
 else:import spindle
 return spindle


def assembly_parts(c):
 sp=spindle_module()
 return {'fixed-stand':frame(c),'left-carrier':carrier(c,-1),'right-carrier':carrier(c,1),'spindle':sp.spindle(c),'collar':sp.collar(c),'drive-rotor':drive_rotor(c),'retaining-clip':retaining_clip(c),**bearing_pair(c)}


def min_gap(a,b):
 from OCP.BRepExtrema import BRepExtrema_DistShapeShape
 return BRepExtrema_DistShapeShape(a.wrapped,b.wrapped).Value()


def axial_float(c):
 """Axial play of the rotating unit relative to the frame, each way: thrust-sleeve gap + 608 seat clearance + carrier tongue/groove play."""
 a=c['axle'];b=c['bearings'];k=c['carriers']
 parts={'thrust_sleeve_gap':b['center_x']-b['width']/2-a['thrust_face_x'],'bearing_seat':b['axial_seat_clearance'],
  'carrier_tongue':((k['groove_x'][1]-k['groove_x'][0])-(k['tongue_x'][1]-k['tongue_x'][0]))/2}
 return {**{n:round(v,4) for n,v in parts.items()},'total':round(sum(parts.values()),4)}


def collar_travel(c):
 """Allowed collar travel (+ inboard): full collar hub on the thread; after full float and the thread flank clearance
 (the clamp pushes the collar outboard through it) the stop ring keeps min_running_gap to the frame and the hub to the left carrier."""
 sp=c['spindle'];t=sp['thread'];h=sp['collar']['hub_x'];run=axial_float(c)['total']+t['flank_clearance']+sp['min_running_gap']
 # Travel limits are whole lock positions (the key rests in a slot at each end).
 step=t['pitch']/sp['lock']['slot_count'];lock=lambda v:round(math.floor(v/step+1e-9)*step,4)
 return {'inboard':lock(t['thread_x'][1]-h[1]),'outboard':lock(min(h[0]-t['thread_x'][0],datums(c)['frame_inner']-sp['ring_x'][1]-run,h[0]+c['bearings']['carrier_inner_x']-run))}


def drive_key(c,parts):
 """Square drive key, disc socket and clip, from the exported parts: torsion stop, 608 and disc slide paths, clip snap at any key angle, axial hold both ways."""
 a=c['axle'];d=c['disc'];p=c['clip'];b=c['bearings'];y=b['axis_y'];R=a['journal_radius'];k=a['key_apothem'];sock=k+d['key_radial_clearance']
 end=parts['spindle'].intersect(box(35,a['right_end_x']+1,y-12,y+12,-12,12));disc=parts['drive-rotor'];clip=parts['retaining-clip'];brg=parts['right-bearing']
 rot=lambda s,deg:s.rotate((0,y,0),(1,y,0),deg);fail=[];r={}
 # Torsion: the Ø8 corner arcs reach past the socket flats; the key turns freely until a corner meets a flat.
 free=math.degrees(math.acos(k/R)-math.acos(sock/R))
 r['flats']=a['key_flats'];r['key_across_flats_mm']=2*k;r['socket_across_flats_mm']=2*sock;r['corner_diameter_mm']=2*R
 r['engagement_mm']=round(R-sock,3);r['free_turn_deg']=round(free,2)
 r['turn_overlap_mm3']={f'{s*t:+.2f}':round(overlap(rot(end,s*t),disc),4) for s in (1,-1) for t in (free-.5,free+1)}
 if R-sock<a['key_min_engagement']:fail.append('Drive key engages the disc socket less than key_min_engagement')
 if any(v>1e-5 for n,v in r['turn_overlap_mm3'].items() if abs(abs(float(n))-(free-.5))<.01) or any(v<.01 for n,v in r['turn_overlap_mm3'].items() if abs(abs(float(n))-(free+1))<.01):
  fail.append('Drive key does not stop the disc within free turn + 1 deg both ways')
 # The groove neck must stay a full circle so the clip snap does not depend on the key angle.
 g0,g1,gr=a['groove_start_x']+.05,a['groove_end_x']-.05,a['groove_radius']
 neck=overlap(end,cylinder_x(gr,g0,g1-g0,y));outside=overlap(end,cylinder_x(R+.5,g0,g1-g0,y).cut(cylinder_x(gr,g0-.1,g1-g0+.2,y)))
 r['groove_neck']={'diameter_mm':2*gr,'round_fraction':round(neck/(math.pi*gr*gr*(g1-g0)),4),'material_outside_neck_mm3':round(outside,5)}
 if r['groove_neck']['round_fraction']<.999 or outside>1e-5:fail.append('Clip groove neck is not a full circle')
 # Assembly: the 608 slides over the key from the drive end; the disc slides on and off past the groove and tip.
 r['bearing_slide_overlap_mm3']={f'{t:g}':round(overlap(brg.translate((t,0,0)),end),5) for t in (.5,2,4,7,10,15)}
 r['disc_slide_overlap_mm3']={f'{t:g}':round(overlap(disc.translate((t,0,0)),end),5) for t in (.5,2,3.5,5,7.5)}
 if max(r['bearing_slide_overlap_mm3'].values())>1e-4:fail.append('608 cannot slide over the drive key')
 if max(r['disc_slide_overlap_mm3'].values())>1e-5:fail.append('Disc cannot slide over the drive key')
 # Clip: radial path through the disc channel; it must clear the disc, and its jaws must spread over the neck at any key angle.
 th=math.radians(d['clip_channel_angle_deg']);u=(0,math.cos(th),math.sin(th));path=(.2,.5,1,1.5,2,3,4.5,6,9,13)
 move=lambda s,t:s.translate((0,u[1]*t,u[2]*t))
 r['clip_path_disc_overlap_mm3']=round(max(overlap(move(clip,t),disc) for t in path),5)
 r['clip_snap_each_jaw_mm']=round((2*gr-p['mouth_width'])/2,3)
 r['clip_extraction_neck_overlap_mm3']={f'key turned {deg} deg':round(max(overlap(move(clip,t),rot(end,deg)) for t in path),4) for deg in (0,90/a['key_flats'],180/a['key_flats'])}
 if r['clip_path_disc_overlap_mm3']>1e-5:fail.append('Clip path through the disc channel is blocked')
 if r['clip_snap_each_jaw_mm']<.15 or min(r['clip_extraction_neck_overlap_mm3'].values())<.01:fail.append('Clip does not snap over the groove neck at every key angle')
 # Axial hold. Outward (the wheel magnets pull the disc toward the wall): disc -> clip -> corner lugs outboard of the groove.
 out_play=(a['groove_end_x']-p['start_x']-p['thickness'])+(p['start_x']-d['counterbore_back_x'])
 lead=p['start_x']-d['counterbore_back_x']  # the disc moves this far before it pushes the clip
 pair=lambda t:overlap(clip.translate((max(0,t-lead),0,0)),end)+overlap(disc.translate((t,0,0)),end)
 r['outward_play_mm']=round(out_play,3);r['outward_overlap_mm3']={'play-0.05':round(pair(out_play-.05),5),'play+0.1':round(pair(out_play+.1),4)}
 # Bearing area: the actual clip (mouth included) pushed 0.1 mm into the lug faces.
 lug=overlap(clip.translate((a['groove_end_x']-p['start_x']-p['thickness']+.1,0,0)),end)/.1
 r['outboard_clip_bearing_area_mm2']=round(lug,2)
 if r['outward_overlap_mm3']['play-0.05']>1e-5 or r['outward_overlap_mm3']['play+0.1']<.01:fail.append('Clip does not hold the disc outward within its play')
 # Inward: the disc thrust ring stops on the 608 inner ring; the clip cannot leave the groove inboard.
 in_gap=d['thrust_start_x']-b['center_x']-b['width']/2
 r['inward_gap_to_608_mm']=round(in_gap,3);r['inward_overlap_mm3']={'disc to 608 at gap+0.1':round(overlap(disc.translate((-in_gap-.1,0,0)),brg),4),'clip inboard 0.1':round(overlap(clip.translate((-.1,0,0)),end),4)}
 if min(r['inward_overlap_mm3'].values())<.01:fail.append('Disc or clip not stopped inward')
 return r,fail


def verify(c,parts):
 """Native holder fit: frame, removable carriers, spindle, collar, bearings, disc and clip. Spool fit is checked by spool_fit.py."""
 expected={'fixed-stand','left-carrier','right-carrier','spindle','collar','drive-rotor','retaining-clip','left-bearing','right-bearing'}
 if set(parts)!=expected:raise ValueError('Expected frame, two carriers, spindle, collar, disc, clip and two bearing envelopes')
 b=c['bearings'];a=c['axle'];d=c['disc'];p=c['clip'];m=c['magnets'];v=datums(c)
 checks={'scope':'Native geometry only. Carriers seat by gravity; strength, retention, thread fit, clamp torque and printability are unqualified.','parts':{},'nominal_intersections_mm3':{},'lift_frame_overlap_mm3':{},'failures':[]}
 for name,shape in parts.items():
  checks['parts'][name]={'valid':shape.isValid(),'solids':len(shape.Solids()),'bounds_mm':bounds(shape),'volume_mm3':shape.Volume()}
  if not shape.isValid() or len(shape.Solids())!=1:checks['failures'].append('Invalid part: '+name)
 names=list(parts)
 for i,name in enumerate(names):
  for other in names[i+1:]:
   amount=overlap(parts[name],parts[other])
   if amount>1e-5:checks['nominal_intersections_mm3'][name+' / '+other]=amount
 if checks['nominal_intersections_mm3']:checks['failures'].append('Nominal assembled intersections')
 # Everything except the frame lifts out together.
 for lift in [.2,1,5,20,40,80,120]:
  hits={name:overlap(parts[name].translate((0,lift,0)),parts['fixed-stand']) for name in names if name!='fixed-stand'}
  checks['lift_frame_overlap_mm3'][str(lift)]=hits
  if max(hits.values())>1e-5:checks['failures'].append(f'Lift {lift} mm collides')
 # The spindle, collar, disc and clip turn together inside the stationary frame and carriers, with axial float either way.
 y=b['axis_y'];stationary=['fixed-stand','left-carrier','right-carrier'];fl=axial_float(c);need=c['spindle']['min_running_gap']
 checks['axial_float_mm']=fl;gaps={}
 # 0-110 deg is one period of the three-fold spindle and collar bodies. The single lock paddle breaks that symmetry; its
 # full-turn clearance is analytical (R<=14.5, X>=-25.75 worst case, >=1.25 mm axially from the left carrier face X-27.5, R<=14).
 for shift in [-fl['total'],0,fl['total']]:
  for angle in range(0,120,10):
   for r in ['spindle','collar']:
    turned=parts[r].rotate((0,y,0),(1,y,0),angle).translate((shift,0,0))
    for s in stationary:
     key=f'{r} / {s} @ float {shift:+.2f}';gaps[key]=min(gaps.get(key,1e9),min_gap(turned,parts[s]))
 checks['rotating_min_gap_mm']={k:round(v,3) for k,v in gaps.items()}
 if min(gaps.values())<need-1e-6:checks['failures'].append('Rotating spindle or collar closer than min_running_gap to a stationary part within the axial float')
 # Thread engagement: the collar follows the helix (translation plus matching rotation) across its travel.
 sp=spindle_module();t=c['spindle']['thread'];travel=collar_travel(c);h=c['spindle']['collar']['hub_x']
 checks['collar_travel_mm']=travel;checks['thread']={'hand':t['hand'],'removal_turns_at_nominal':(h[1]-t['thread_x'][0])/t['pitch'],'pitch':t['pitch'],'major_diameter':2*t['major_radius'],'engaged_length':h[1]-h[0],'engaged_turns':(h[1]-h[0])/t['pitch'],'cases':{}}
 for move in [-travel['outboard'],0,travel['inboard']]:
  moved=sp.collar(c,move);case={'spindle_overlap_mm3':overlap(parts['spindle'],moved),'spindle_gap_mm':min_gap(parts['spindle'],moved),'frame_gap_nominal_mm':min_gap(moved,parts['fixed-stand'])}
  case['frame_gap_after_float_mm']=min(min_gap(moved.translate((-fl['total'],0,0)),parts[n]) for n in stationary)
  case['frame_gap_after_float_and_flank_mm']=min(min_gap(moved.translate((-fl['total']-t['flank_clearance'],0,0)),parts[n]) for n in stationary)
  checks['thread']['cases'][f'{move:+.2f}']={k:round(v,4) for k,v in case.items()}
  if case['spindle_overlap_mm3']>1e-5 or case['frame_gap_after_float_and_flank_mm']<need-1e-6:checks['failures'].append(f'Collar travel {move:+.2f} mm collides')
 # Full-turn receipt at the outboard limit, float and flank play: the whole collar (paddle, arm, hub, stop ring) swept about
 # the axle. Its outboard-most point within the left carrier's radial reach must keep `need` to the carrier's inner face, and
 # its outboard-most point overall to the frame plate (which is plane at frame_inner for every radius the collar reaches).
 worst=sp.collar(c,-travel['outboard']).translate((-fl['total']-t['flank_clearance'],0,0))
 cb=parts['left-carrier'].BoundingBox();reach=max(math.hypot(yy-y,zz) for yy in (cb.ymin,cb.ymax) for zz in (cb.zmin,cb.zmax))
 near=worst.intersect(cylinder_x(reach,-v['frame_inner']-1,2*v['frame_inner']+2,y)).BoundingBox().xmin
 sweep={'carrier_reach_radius_mm':round(reach,2),'collar_min_x_within_reach':round(near,3),'collar_min_x':round(worst.BoundingBox().xmin,3),
  'carrier_gap_mm':round(near+c['bearings']['carrier_inner_x'],3),'frame_gap_mm':round(worst.BoundingBox().xmin+v['frame_inner'],3)}
 checks['collar_full_turn_outboard_mm']=sweep
 if min(sweep['carrier_gap_mm'],sweep['frame_gap_mm'])<need-1e-6:checks['failures'].append('Collar swept at its outboard limit is closer than min_running_gap to the left carrier or frame')
 # Collar lock: key in a slot at every lock position; turning either way past the key play collides; lifted, the collar turns freely.
 k=c['spindle']['lock'];step=sp.lock_positions(c);deg=360/k['slot_count'];lift=t['major_radius']+k['lift_clearance']-k['key_tip_radius']
 for limit in travel.values():
  if abs(limit/step-round(limit/step))>1e-6:checks['failures'].append('Collar travel limit is not a lock position')
 lk={'slot_count':k['slot_count'],'index_deg':deg,'index_travel_mm':step,'lift_required_mm':lift,'stop_overlap_mm3':{},'lifted_overlap_mm3':{}}
 for move in [0,travel['inboard']]:
  for turn in [-5,5]:
   hit=parts['spindle'].intersect(sp.collar(c,move+turn/360*t['pitch']));amount=volume(hit);bands=len(hit.Solids())
   lk['stop_overlap_mm3'][f'travel {move:+.2f}, turn {turn:+d} deg']={'mm3':round(amount,3),'crest_bands':bands}
   if amount<.1 or bands<2:checks['failures'].append(f'Lock does not stop a {turn:+d} deg turn on two crest bands at travel {move:+.2f}')
 for move in [step/2,travel['inboard']/2+step/2,travel['inboard']-step/2]:
  amount=overlap(parts['spindle'],sp.collar(c,move,lift=lift))
  lk['lifted_overlap_mm3'][f'{move:+.3f}']=round(amount,4)
  if amount>1e-5:checks['failures'].append(f'Lifted key still collides at travel {move:+.3f}')
 body=sp.collar(c,lock=False);key=sp.lock_key(c)
 lk['key_rest_gap_to_collar_mm']=round(min_gap(body,key),3);lk['key_rest_gap_to_spindle_mm']=round(min_gap(parts['spindle'],key),3)
 lk['key_lifted_gap_to_collar_mm']=round(min_gap(body,sp.lock_key(c,lift)),3)
 if min(lk['key_rest_gap_to_collar_mm'],lk['key_lifted_gap_to_collar_mm'],lk['key_rest_gap_to_spindle_mm'])<=0:checks['failures'].append('Lock key touches the collar body or spindle')
 # Hand screen for the compliant arm (straight cantilever along the arc, PLA E 2500 MPa assumed).
 r_arm=sum(k['arm_radii'])/2;L=math.radians(k['key_angle_deg']-k['arm_root_angle_deg'])*r_arm;th=k['arm_radii'][1]-k['arm_radii'][0]
 I=k['arm_length_x']*th**3/12
 lk['arm']={'length_mm':round(L,2),'thickness_mm':th,'strain_at_lift_pct':round(150*th*lift/L**2,2),'lift_force_N':round(3*2500*I*lift/L**3,2),
  'gaps_mm':{'radial_to_pocket_floor':k['arm_radii'][0]-k['pocket_radii'][0],'key_top_to_hole_roof':k['key_hole_roof_gap'],'pocket':'open through the hub inboard end'}}
 crest=2*math.degrees(math.asin(k['slot_width']/2/t['major_radius']))
 lk['thread_crest_remaining_pct']=round(100*(1-k['slot_count']*crest/360),1)
 checks['lock']=lk
 wrong=overlap(parts['spindle'],parts['collar'].translate((t['pitch']/2,0,0)))
 checks['thread']['half_pitch_unrotated_overlap_mm3']=round(wrong,2)
 if wrong<1:checks['failures'].append('Thread check is not discriminating: a half-pitch misphase does not collide')
 # Anchor branches: clear the turning disc, keep out of the disc's straight-up lift corridor, glue pockets hold a magnet flush.
 mt=c['mount'];br=anchor_branches(c);x1=v['wall_contact'];hw=mt['inside']['lift_corridor_half_width']
 disc_gap=min(min_gap(parts['drive-rotor'].rotate((0,y,0),(1,y,0),angle),br) for angle in range(0,360,30))
 corridor=overlap(br,box(x1-mt['inside']['depth']-1,x1+1,y,y+200,-hw,hw))
 fits=[]
 for ay,az in anchors(c):
  mag=cylinder_x(m['diameter']/2,x1-m['thickness'],m['thickness'],ay,az)
  fits.append(round(overlap(mag,parts['fixed-stand']),5))
 checks['anchor_branches']={'disc_min_gap_mm':round(disc_gap,3),'required_disc_gap_mm':mt['inside']['lower_root_disc_clearance'],'lift_corridor_overlap_mm3':round(corridor,5),
  'lift_corridor':f'|Z| < {hw} above Y{y:g}, X {x1-mt["inside"]["depth"]:g}..{x1:g}','pocket_magnet_overlap_mm3':fits,'magnet_face_x':x1,'pocket_depth':mt['anchor_pocket_depth'],
  'anchor_centers_yz':[[round(a,3),round(b,3)] for a,b in anchors(c)],'frame_top_y':round(bounds(parts['fixed-stand'])['y'][1],3)}
 if disc_gap<mt['inside']['lower_root_disc_clearance']-1e-6:checks['failures'].append('Anchor branch closer to the turning disc than lower_root_disc_clearance')
 if corridor>1e-6:checks['failures'].append('Anchor branch enters the disc lift corridor')
 if max(fits)>1e-5 or mt['anchor_pocket_depth']<m['thickness']:checks['failures'].append('Anchor magnet does not fit its glue pocket flush with the wall-contact plane')
 pocket_depth=d['front_x']-m['front_cover']-m['cup_back_x']
 checks['magnet_stack_mm']={'pocket_depth':pocket_depth,'magnet_thickness':m['thickness'],'front_cover':m['front_cover']}
 if pocket_depth<m['thickness']:checks['failures'].append('Magnet deeper than pocket')
 checks['bearing_jaw_deflection_each_mm']=(b['od']-b['mouth_width'])/2;checks['clip_jaw_deflection_each_mm']=(2*a['groove_radius']-p['mouth_width'])/2
 dk,fails=drive_key(c,parts);checks['drive_key']=dk;checks['failures']+=fails
 # Spool seat datum: both stop faces at half the measured hub-face width; collar travel covers D +-2 mm.
 sp=c['spindle'];ms=c['envelopes']['measured_spool'];face=sp['ring_x'][0]+sp['pilot_length'];tr=collar_travel(c)
 checks['spool_seat']={'stop_face_x':face,'measured_hub_face_width':ms['hub_face_width'],'stop_face_diameters':[2*sp['pilot_radius'],2*sp['stop_outer_radius']],
  'pilot_radial_clearance_to_assumed_bore':round(ms['assumed_bore_diameter']/2-sp['pilot_radius'],3),'clamped_hub_width_range':[round(2*face-tr['inboard'],3),round(2*face+tr['outboard'],3)],
  'face_inside_assumed_recess_opening_mm':round(ms['assumed_recess_opening_diameter']/2-sp['stop_outer_radius'],3)}
 if abs(2*face-ms['hub_face_width'])>1e-6:checks['failures'].append('Stop faces are not at the measured hub-face width')
 if checks['spool_seat']['clamped_hub_width_range'][0]>ms['hub_face_width']-2+1e-6 or checks['spool_seat']['clamped_hub_width_range'][1]<ms['hub_face_width']+2-1e-6:checks['failures'].append('Collar travel does not cover the measured hub width +-2 mm')
 # Flange-sweep relief: thinned only inside the annulus; analytic bound for the thinned members (PLA, section ratio only).
 r=c['frame_profile']['spool_relief'];t0=c['frame_profile']['thickness'];t1=t0-r['depth'];v=datums(c)
 removed=overlap(parts['fixed-stand'],spool_relief(c))
 checks['spool_relief']={'working_inner_faces_mm':2*(v['frame_inner']+r['depth']),'plate_thickness_mm':[t0,t1],'frame_material_in_relief_mm3':round(removed,5),
  'section_ratios':{'in_plane_stiffness_and_strength':round(t1/t0,3),'out_of_plane_strength':round((t1/t0)**2,3),'out_of_plane_stiffness':round((t1/t0)**3,3)},
  'gravity_bound':'Assumed 1.25 kg full spool (12.3 N) shared by two plates: 6.1 N in-plane per plate, so a relieved member w mm wide carries 6.1/(2.5 w) = 2.4/w MPa (0.5 MPa even at 5 mm), far below PLA strength. Out-of-plane loads (anchor magnet pull, hand loads) enter at the carrier heads and reach the base through the relieved legs: bending strength x0.694, stiffness x0.579 of the 3 mm section. The spool clamp closes internally through spindle, thread and collar, not through the frame. Section ratios only, not FE or qualification.'}
 if removed>1e-5:checks['failures'].append('Frame material left inside the flange-sweep relief')

 checks['dimensions_mm']={'wall_span':v['minimum_wall_span'],'base_width':v['base_width'],'base_depth':c['base']['depth']}
 checks['pass']=not checks['failures'];checks['summary']='Pass' if checks['pass'] else '; '.join(checks['failures'])
 return checks


def load_config(path=None):return json.loads(Path(path or HERE/'stand.json').read_text())


def main():
 import argparse
 if __package__:from .cad_helpers import export_step
 else:from cad_helpers import export_step
 ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--config',type=Path,default=HERE/'stand.json');ap.add_argument('--output',type=Path,default=HERE.parents[1]/'build/filament-drybox');args=ap.parse_args();out=args.output.resolve();out.mkdir(parents=True,exist_ok=True)
 c=load_config(args.config);parts=assembly_parts(c);checks=verify(c,parts)
 for name,shape in parts.items():export_step(shape,out/(name+'.step'))
 export_step(parts['fixed-stand'],out/'stand.step')
 d=datums(c);fb=bounds(parts['fixed-stand'])
 dimensions={'left_wall_x':fb['x'][0],'right_wall_x':d['wall_contact'],'wall_span':d['wall_contact']-fb['x'][0],'base_width':d['base_width'],'base_depth':c['base']['depth'],'frame_height':fb['y'][1],'scope':'Inside holder span from the leftmost frame face to the drive-wall contact plane; excludes the container wall and external handwheel.'}
 result={'units':'mm','config':c,'dimensions_mm':dimensions,'checks':checks,'scope':'Frame, removable carriers, spindle, collar, disc, clip and 608 envelopes. No strength, retention, thread-fit or manufacturing qualification.'}
 (out/'stand-build.json').write_text(json.dumps(result,indent=2)+'\n')
 # Half sections (Z<=0 kept) of the clamping parts, cut in CAD so the cut faces are real geometry.
 half=box(-60,60,40,170,-60,0);sections={name:mesh(parts[name].intersect(half)) for name in ['spindle','collar']}
 # Lock demonstration: 0.8 mm transverse slices through the key, inboard of the collar arms, resting and lifted.
 sp=spindle_module();k=c['spindle']['lock'];t=c['spindle']['thread'];h0=c['spindle']['collar']['hub_x'][0]
 xm=h0+k['key_x_from_hub'][1]-.6;slab=box(xm-.4,xm+.4,40,170,-60,60);lift=t['major_radius']+k['lift_clearance']-k['key_tip_radius']
 sections.update({'lock-spindle':mesh(parts['spindle'].intersect(slab)),'lock-collar':mesh(parts['collar'].intersect(slab)),'lock-collar-lifted':mesh(sp.collar(c,lift=lift).intersect(slab))})
 display={'schema':'drybox-holder-native-v2','units':'mm','components':{name:mesh(shape) for name,shape in parts.items()},'sections':sections,'dimensions_mm':dimensions,'checks':{'pass':checks['pass'],'summary':checks['summary']}}
 (out/'stand-display.json').write_text(json.dumps(display,separators=(',',':')))
 print(json.dumps({'pass':checks['pass'],'summary':checks['summary'],'dimensions_mm':dimensions},indent=2))
 if not checks['pass']:raise SystemExit(1)


if __name__=='__main__':main()
