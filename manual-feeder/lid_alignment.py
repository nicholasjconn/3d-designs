"""Four tapered lid locators with clearance for a straight lift."""
import manifold3d as m

from geometry import box, paired, yz_prism

GUIDE_X = 17.8
GUIDE_Y = 11.86
GUIDE_HALF_WIDTH = 1.75
GUIDE_HALF_DEPTH = 1.24
GUIDE_CLEARANCE = .16


def repeated(shape):
    return paired(paired(shape,[1,0,0]),[0,1,0])


def loft_rect(seam, stations):
    sections = [
        box(GUIDE_X-w,GUIDE_Y-d,seam+z-.012,GUIDE_X+w,GUIDE_Y+d,seam+z+.012)
        for z,w,d in stations
    ]
    return m.Manifold.batch_boolean([
        m.Manifold.batch_hull([lower,upper])
        for lower,upper in zip(sections,sections[1:])
    ],m.OpType.Add)


def build(seam):
    """Return the solid posts, pocket cutters, and pocket backing in the lid."""
    base = yz_prism([(13.02,seam-3.4),(14.9,seam-3.4),(14.9,seam-.05),
                     (10.7,seam-.05),(10.7,seam-.63)],15.85,19.75)
    w, d = GUIDE_HALF_WIDTH, GUIDE_HALF_DEPTH
    post = loft_rect(seam,[(-.13,w,d),(2.20,w,d),(2.79,1.30,.84)])
    pw, pd = w+GUIDE_CLEARANCE, d+GUIDE_CLEARANCE
    pocket = loft_rect(seam,[
        (-.04,pw+.32,pd+.32),(.41,pw,pd),(3.04,pw,pd),
    ])
    backing = box(GUIDE_X-2.95,GUIDE_Y-2.45,seam-.1,GUIDE_X+2.95,17,seam+4)
    return repeated(base+post), repeated(pocket), repeated(backing)
