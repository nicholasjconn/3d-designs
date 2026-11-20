"""Stationary screw cap that compresses the fitting's static face seal."""
from direct_interfaces import box, cyl, tooth, thread_profiles, one

def build(c):
    p = c['port']
    a, b = p['cap_x']
    axis_y = c['bearings']['axis_y']
    _, female, bore = thread_profiles(p['thread_profile'])
    cap = cyl(14, a, b, axis_y).cut(cyl(bore, a-.1, a+4, axis_y))
    cap = cap.cut(tooth(c, female, a-.1, a+3.8, a))

    # Rounded grip spokes share the closed face so they print flat on the bed.
    spoke_start = a + 1.2
    tip_radius = 2.8
    tip_center = axis_y + 19.2
    spoke = box(spoke_start, b, axis_y+11.5, tip_center, -tip_radius, tip_radius)
    spoke = spoke.fuse(cyl(tip_radius, spoke_start, b, tip_center))
    spokes = [spoke.rotate((0, axis_y, 0), (1, axis_y, 0), angle)
              for angle in range(0, 360, 60)]
    return one(cap.fuse(*spokes), 'sealing cap')
