"""Round608 holder with a thin rectangular captured sliding locator; open upward."""
from direct_interfaces import box,cyl,one

def build(c,side):
    y=c['bearings']['axis_y'];f=c['frame']; x1=f['carrier_face_x']
    b=c['bearings']['right_x'] if side>0 else [-v for v in c['bearings']['left_x'][::-1]]
    x0=b[0]-1.5
    s=cyl(14,x0,x1,y).intersect(box(x0-.1,x1+.1,f['carrier_floor_y'],f['top_y'],-14.1,14.1))
    s=s.fuse(box(f['upright_inner_x'],x1,f['carrier_floor_y'],f['top_y'],-14,14))
    s=s.cut(cyl(11.2,b[0]-.1,b[1]+.1,y)).cut(cyl(9.8,x0-.1,x1+.1,y))
    s=s.cut(box(x0-.1,x1+.1,y,f['top_y']+1,-10.8,10.8))
    a,b=f['tongue_x']
    for za,zb in [(-14.2,-12),(12,14.2)]:
        s=s.cut(box(a-.2,b+.2,f['carrier_floor_y']-.1,f['top_y']+1,za,zb))
    return one(s if side>0 else s.mirror('YZ'),'bearing carrier')
