"""One removable crank, integral shaft and deeper rounded-square socket."""
from direct_interfaces import cyl,box,one

def build(c):
    p=c['port'];y=c['bearings']['axis_y'];a,b=p['crank_shaft_x'];h0,h1=p['crank_hub_x'];u,v=p['crank_arm_x'];g0,g1=p['crank_grip_x'];s0,s1=p['crank_socket_x']
    n0,n1=p['crank_neck_x'];radius=p['crank_running_radius']
    import cadquery as cq
    neck=cq.Solid.makeCone(5,radius,n1-n0,cq.Vector(n0,y,0),cq.Vector(1,0,0))
    s=cyl(5,a,n0).fuse(neck,cyl(radius,n1,b),cyl(8,h0,h1),box(u,v,y-4,y+30,-4,4),cyl(5,g0,g1).translate((0,30,0)))
    socket=cyl(4.15,s0-.1,s1).intersect(box(s0-.2,s1+.1,y-3.35,y+3.35,-3.35,3.35))
    return one(s.cut(socket),'removable crank')
