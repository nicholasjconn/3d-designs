"""Stationary threaded wall fitting with face seals and finger counterholds."""
from math import hypot

from direct_interfaces import box, cyl, tube, tooth, thread_profiles, one


def fitting_flange(c, wall_face, cap_face):
    """Keep both seal faces coplanar with the grip tabs."""
    axis_y = c['bearings']['axis_y']
    dimensions = c['port']['counterhold_tabs']
    flange_radius = 16
    half_width = dimensions['width'] / 2
    tip_center = dimensions['tip_reach'] - half_width
    flange = cyl(flange_radius, wall_face, cap_face, axis_y)
    tab = box(wall_face, cap_face, axis_y-half_width, axis_y+half_width,
              flange_radius-half_width, tip_center)
    tab = tab.fuse(cyl(half_width, wall_face, cap_face, axis_y).translate((0, 0, tip_center)))
    opposite = tab.rotate((0, axis_y, 0), (1, axis_y, 0), 180)
    flange = flange.fuse(tab, opposite).clean()

    roots = []
    for edge in flange.Edges():
        if edge.geomType() != 'LINE':
            continue
        center = edge.Center()
        if (abs(edge.Length() - (cap_face-wall_face)) < 1e-6
                and abs(hypot(center.y-axis_y, center.z) - flange_radius) < 1e-6):
            roots.append(edge)
    if len(roots) != 4:
        raise ValueError(f'Counterhold flange: expected four tab roots, found {len(roots)}')
    return flange.fillet(dimensions['root_fillet'], roots)


def cut_face_groove(solid, face, direction, ring_id, dimensions):
    inner = (ring_id + dimensions['shoulder_diameter_allowance']) / 2
    outer = inner + dimensions['width']
    floor = face + direction * dimensions['depth']
    x0, x1 = sorted((face - direction * .1, floor))
    solid = solid.cut(tube(outer, inner, x0, x1))

    def round_edges(shape, x, radii, fillet_radius):
        edges = [edge for edge in shape.Edges()
                 if edge.geomType() == 'CIRCLE'
                 and abs(edge.Center().x - x) < 1e-6
                 and any(abs(edge.radius() - radius) < 1e-6 for radius in radii)]
        if len(edges) != len(radii):
            raise ValueError(f'Face groove: expected {len(radii)} circular edges at X={x}')
        return shape.fillet(fillet_radius, edges)

    solid = round_edges(solid, floor, (inner, outer), dimensions['floor_radius'])
    return round_edges(solid, face, (inner,), dimensions['entry_radius'])


def build(c):
    p=c['port'];a=p['fitting_tip_x'];b,d=p['fitting_flange_x'];e=p['fitting_end_x']
    male,_,_=thread_profiles(p['thread_profile'])
    s=cyl(8.3,a,e).fuse(fitting_flange(c,b,d),tooth(c,male,a,b,a),tooth(c,male,d,e,d))
    s=s.cut(cyl(p['bore_radius'],a-.1,e+.1))
    s = cut_face_groove(s, b, 1, p['wall_oring_id_cs'][0], p['face_groove'])
    s = cut_face_groove(s, d, -1, p['cap_oring_id_cs'][0], p['face_groove'])
    return one(s, 'wall fitting')
