"""Single base-down stand with open lift-out guides and integrated nut channel."""
import cadquery as cq
from direct_interfaces import box,one

def wire(points):
    return cq.Workplane('YZ').polyline([(y,z) for z,y in points]).close().val()

def rounded(w,r):
    return cq.Face.makeFromWires(w).fillet2D(r,w.Vertices()).outerWire()

def upright(c,side):
    f=c['frame']; half=f['right_top_half_z'] if side>0 else f['left_top_half_z']
    apex=f['right_window_apex_y'] if side>0 else f['left_window_apex_y']
    outline=wire([(-52,6),(52,6),(half,f['top_y']),(-half,f['top_y'])])
    hole=rounded(wire([(-35,18),(35,18),(0,apex)]),f['window_radius'])
    x0,x1=f['upright_inner_x'],f['upright_outer_x']
    s=cq.Solid.extrudeLinear(outline,[hole],cq.Vector(x1-x0,0,0)).translate((x0,0,0))
    a,b=f['tongue_x']
    for half,xa,xb in [(14.2,x0-.1,a),(12.2,a,b),(14.2,b,x1+.1)]:
        s=s.cut(box(xa,xb,f['carrier_floor_y'],f['top_y']+1,-half,half))
    return s if side>0 else s.mirror('YZ')

def build(c):
    f,p=c['frame'],c['port']
    outer=rounded(cq.Workplane('XZ').rect(f['base_x'],f['base_z']).val(),2)
    inner=rounded(cq.Workplane('XZ').rect(f['base_x']-4,106).val(),2)
    base=cq.Solid.extrudeLinear(outer,[inner],cq.Vector(0,f['base_height'],0))
    # Preserve the approved old upright union and widened drive-side head exactly.
    legacy=dict(c,frame=dict(f,right_top_half_z=f['left_top_half_z'],right_window_apex_y=f['left_window_apex_y']))
    stand=base.fuse(upright(c,-1),upright(legacy,1),upright(c,1))
    uc,top=p['dock_center_y'],p['dock_top_y']
    def u(r,xa,xb):
        return box(xa,xb,uc,top+1,-r,r).fuse(cq.Solid.makeCylinder(r,xb-xa,cq.Vector(xa,uc,0),cq.Vector(1,0,0)))
    # Ramp before clipping at the upright face; one45-degree continuous underside.
    x0,x1=36.1,p['dock_outer_x']; y0=72.7
    w=cq.Workplane('XY').polyline([(x0,y0),(36.2,y0),(x1,y0+x1-36.2),(x1,top),(x0,top)]).close().val()
    dock=cq.Solid.extrudeLinear(w,[],cq.Vector(0,0,2*p['dock_half_z'])).translate((0,0,-p['dock_half_z']))
    dock=dock.cut(box(36,37.2,86,top+1,-16.2,16.2)).cut(box(37.1,40.2,90.6,top+1,-14.2,14.2))
    dock=dock.cut(u(17.8,40,42)).cut(u(15.2,41.9,x1+.1))
    dock=dock.intersect(box(f['upright_inner_x'],60,0,112,-30,30))
    return one(stand.fuse(dock),'direct-drive stand')
