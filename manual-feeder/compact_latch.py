"""Captive compression cam with a tapered pivot and a closed stop."""
import manifold3d as m
import numpy as np

from geometry import box, cylinder, yz_prism

SCALE = .82
PIVOT_Y = 24.0
PARKED = 101
THRUST = .537


def build(seam):
    origin = [0, PIVOT_Y, seam-4.8*SCALE]

    def place(shape):
        return shape.scale([SCALE]*3).translate(origin)

    def xz_prism(points, low, high):
        return yz_prism(points, -high, -low).rotate([0,0,-90])

    post = (cylinder(3.15,.62,8.70) + cylinder(3.15,8.68,10.38,4.85)
            + cylinder(4.85,10.38,11.36)
            + cylinder(3.15,3.25,4.10,4.00) + cylinder(4.0,4.10,4.95,3.15))
    base = cylinder(3.10,-2.12,.80,5.29)
    base -= cylinder(5.70,.12,.88)-cylinder(4.00,.10,.90)
    support = yz_prism([(18.0,seam-14),(19.1,seam-14),(25.7,seam-5.69),
                        (25.7,seam-4.9),(19.2,seam-1.5),(18.0,seam-1.5)],-3.0,3.0)

    support -= cylinder(4.72,seam-3.37,seam-1.43).translate([0,PIVOT_Y,0])

    stations = [(-54,8.77),(-43,8.56),(-25,7.93),(-11,7.48),(3,7.55),(27,7.71)]
    radii = [4.75,5.28,6.10,7.22,7.75,7.75,4.75]
    vertices = []
    faces = []
    for degrees, height in stations:
        a = np.radians(degrees)
        section = [height-1.23,height-.82,height,height,height+.54,11.4,11.4]
        vertices.extend((r*np.sin(a),-r*np.cos(a),z) for r,z in zip(radii,section))
    sides = len(radii)
    for offset in range(0,len(vertices)-sides,sides):
        for j in range(sides):
            a,b = offset+j,offset+(j+1)%sides
            faces.extend([(a,a+sides,b+sides),(a,b+sides,b)])
    last = len(vertices)-sides
    for j in range(1,sides-1):
        faces.extend([(0,j,j+1),(last,last+j+1,last+j)])
    cam = m.Manifold(m.Mesh(np.asarray(vertices,dtype=np.float32), np.asarray(faces,dtype=np.uint32)))
    ring = (cylinder(5.16,1.36,1.72,5.32)+cylinder(5.32,1.72,7.23)
            + cylinder(5.32,7.19,10.14,6.0))
    thumb = xz_prism([(4.8,4.2),(5.3,4.2),(8.8,8.3),(8.8,11.55),
                      (7.9,12.15),(4.8,8.75)],-2.65,2.65)
    # Keep the compact handle and restore the clearance lost when scaling
    # the tested pivot down. The cone still carries axial load.
    bore = (cylinder(3.68,1.20,8.55)+cylinder(4.47,1.20,1.36)
            + cylinder(4.47,1.36,2.45,3.68)+cylinder(3.68,8.54,11.58,6.72)
            + cylinder(3.68,3.11,3.96,4.53)+cylinder(4.53,3.958,4.16)
            + cylinder(4.53,4.158,5.01,3.68))
    rotor = (ring+thumb+cam)-bore

    def pose(angle, thrust=THRUST):
        return place(rotor.rotate([0,0,angle]).translate([0,0,thrust]))

    # The catch matches the tested cam profile. The region between it and
    # the pin is open so the parked quarter-turn clears the removable lid.
    crown = [(x,8.10-.074*x*x) for x in np.linspace(2.75,-2.75,21)]
    catch = xz_prism([(-2.75,6.38),(2.75,6.38),*crown],-7.8,-6.25)
    catch = place(catch) + box(-2.35,16.68,seam+.61,2.35,18.25,seam+1.45)
    stop = yz_prism([(18.0,seam-4.6),(19.1,seam-4.6),(21.62,seam-.85),
                     (21.62,seam+3.64),(19.78,seam+3.64),(19.78,seam-.14),
                     (18.0,seam-.4)],6.24,7.85)
    return place(post+base)+support+stop, catch, pose
