"""Outside drive: fixed diagonal X with integral axle, handwheel on an extra 608, printed 608 retention.

Millimetres; axle along X. x=0 is the container wall's outside face (+X away from the wall),
the bearing axis is y=z=0. cad/drybox.py places this frame on the holder across the nominal wall.
The X's four anchor pockets pair with the gray frame's glue pockets (stand.py, same stand.json "mount").
Purchased magnets are excluded. Concept CAD, not released or tolerance-qualified fabrication geometry.
"""
import math
import json
from pathlib import Path

import cadquery as cq
from OCP.BRepExtrema import BRepExtrema_DistShapeShape

PARAMETERS = json.loads(Path(__file__).with_name('wheel.json').read_text())
STAND = json.loads(Path(__file__).with_name('stand.json').read_text())
# The magnet pattern and cups must match the disc's, so both read stand.json's shared magnet spec.
MAGNETS = STAND['magnets']
MOUNT = STAND['mount']


def cylinder(radius, start, length, y=0, z=0):
    return cq.Solid.makeCylinder(radius, length, cq.Vector(start, y, z), cq.Vector(1, 0, 0))


def annulus(inner, outer, start, length, y=0, z=0):
    return cylinder(outer, start, length, y, z).cut(cylinder(inner, start - .1, length + .2, y, z))


def box(x0, x1, y0, y1, z0, z1):
    return cq.Solid.makeBox(x1 - x0, y1 - y0, z1 - z0, cq.Vector(x0, y0, z0))


def one(shape, name, *, merge_faces=True):
    if merge_faces:
        shape = shape.clean()
    if not shape.isValid() or len(shape.Solids()) != 1:
        raise ValueError(f'{name}: expected one valid solid, got {len(shape.Solids())}')
    return shape


def volume(shape):
    return sum(s.Volume() for s in shape.Solids())


def gap(a, b):
    return BRepExtrema_DistShapeShape(a.wrapped, b.wrapped).Value()


def magnet_centers():
    m = MAGNETS
    if m['count'] != PARAMETERS['spoke_count']:
        raise ValueError('wheel spokes run through the magnet cups: spoke_count must equal the magnet count')
    return [(m['pitch_radius'] * math.cos(i * 2 * math.pi / m['count']),
             m['pitch_radius'] * math.sin(i * 2 * math.pi / m['count'])) for i in range(m['count'])]


def anchors():
    r = MOUNT['anchor_radius']
    return [(r * math.sin(math.radians(a)), r * math.cos(math.radians(a))) for a in MOUNT['anchor_angles_deg']]


def stations():
    """Axial stations (x from the wall's outside face) derived once from the mount spec."""
    o, b, r, k = MOUNT['outside'], MOUNT['bearing'], MOUNT['retainer'], MOUNT['axle_clip']
    wheel_back = o['crossing_thickness'] + o['running_gap']
    groove = (wheel_back + r['back_wall'], wheel_back + r['back_wall'] + r['thickness'] + r['groove_extra'])
    b0 = groove[1] + MOUNT['axial_play']                      # 608 inboard faces (running pose: inner ring on the shoulder)
    b1 = b0 + b['width']
    clip_groove = (b1 + MOUNT['axial_play'], b1 + MOUNT['axial_play'] + k['thickness'] + k['groove_extra'])
    return {'crossing_front': o['crossing_thickness'], 'cup_front': o['cup_thickness'], 'wheel_back': wheel_back,
            'retainer_groove': groove, 'bearing': (b0, b1), 'lip': (b1, b1 + MOUNT['lip_thickness']),
            'clip_groove': clip_groove, 'journal_end': clip_groove[1] + k['end_beyond_groove']}


def strip(p, q, w, x0, x1):
    """Straight strip of width w in the YZ plane from p=(y, z) to q, from x0 to x1."""
    dy, dz = q[0] - p[0], q[1] - p[1]
    n = math.hypot(dy, dz)
    ny, nz = -dz / n * w / 2, dy / n * w / 2
    pts = [(p[0] + ny, p[1] + nz), (q[0] + ny, q[1] + nz), (q[0] - ny, q[1] - nz), (p[0] - ny, p[1] - nz)]
    wire = cq.Wire.makePolygon([cq.Vector(x0, y, z) for y, z in pts], close=True)
    return cq.Solid.extrudeLinear(cq.Face.makeFromWires(wire), cq.Vector(x1 - x0, 0, 0))


def mount_x():
    """Stationary outside X: hub, four 3 mm arms, 4 mm anchor cups with glue pockets open to the wall, inner-ring shoulder and journal."""
    o, st, k = MOUNT['outside'], stations(), MOUNT['axle_clip']
    body = cylinder(o['hub_radius'], 0, o['crossing_thickness'])
    for y, z in anchors():
        body = body.fuse(strip((0, 0), (y, z), MOUNT['arm_width'], 0, o['crossing_thickness']))
        body = body.fuse(cylinder(MOUNT['anchor_pad_radius'], 0, o['cup_thickness'], y, z))
    b0 = st['bearing'][0]
    body = body.fuse(cylinder(MOUNT['shaft_contact_diameter'] / 2, o['crossing_thickness'] - .1, b0 - o['crossing_thickness'] + .1))
    body = body.fuse(cylinder(MOUNT['journal_radius'], b0 - .1, st['journal_end'] - b0 + .1))
    g0, g1 = st['clip_groove']
    body = body.cut(annulus(k['groove_radius'], MOUNT['journal_radius'] + 1, g0, g1 - g0))
    for y, z in anchors():
        body = body.cut(cylinder(MAGNETS['pocket_radius'], -.1, MOUNT['anchor_pocket_depth'] + .1, y, z))
    return one(body, 'outside X')


def wheel():
    """Handwheel: canonical spokes, rim, magnet cups and knob, now with a 608 hub (pocket open to the wall, outboard lip, retainer groove)."""
    p, m, st = PARAMETERS, MAGNETS, stations()
    x0 = st['wheel_back']
    radius = p['outside_diameter_mm'] / 2
    thickness = p['structural_thickness_mm']
    body = annulus(radius - p['rim_radial_width_mm'], radius, x0, thickness)
    hub_end = st['lip'][1]
    body = body.fuse(cylinder(MOUNT['hub_outer_radius'], x0, hub_end - x0))
    for i, (y, z) in enumerate(magnet_centers()):
        spoke = cq.Solid.makeBox(thickness, p['spoke_end_radius_mm'], p['spoke_width_mm'], cq.Vector(x0, 0, -p['spoke_width_mm'] / 2))
        body = body.fuse(spoke.rotate((0, 0, 0), (1, 0, 0), i * 360 / m['count']))
        body = body.fuse(cylinder(m['cup_outer_radius'], x0, p['cup_back_mm'], y, z))
    body = body.fuse(cylinder(p['knob_radius_mm'], x0 + p['knob_front_mm'], p['knob_length_mm'], p['knob_center_radius_mm'], 0))
    for y, z in magnet_centers():
        # Wall-facing blind glue pockets: magnets sit flush, without a skin
        # between their faces and the wall. The spoke provides the backing.
        body = body.cut(cylinder(m['pocket_radius'], x0 - .1, m['drive_pocket_depth'] + .1, y, z))
    bore = MOUNT['bearing']['od'] / 2 + MOUNT['pocket_radial_clearance']
    body = body.cut(cylinder(bore, x0 - .1, st['lip'][0] - x0 + .1))
    g0, g1 = st['retainer_groove']
    body = body.cut(cylinder(MOUNT['retainer']['groove_radius'], g0, g1 - g0))
    body = body.cut(cylinder(MOUNT['housing_contact_diameter'] / 2, x0 - .1, hub_end - x0 + .2))
    # One notch through the lip lets the axle clip enter radially once the notch is turned to it.
    k = MOUNT['axle_clip']
    half = MOUNT['shaft_contact_diameter'] / 2 + k['notch_clearance']
    notch = box(st['lip'][0] - .1, hub_end + .1, 0, MOUNT['hub_outer_radius'] + 1, -half, half)
    body = body.cut(notch.rotate((0, 0, 0), (1, 0, 0), k['notch_angle_deg']))
    # Keep the boolean face partitions: merging the large back face causes
    # OCCT to omit that face during STL meshing. This changes no solid volume.
    return one(body, 'wheel', merge_faces=False)


def retainer():
    """Printed internal split ring seated in the hub groove; bears on the 608 outer ring's inboard face."""
    r = MOUNT['retainer']
    g0, g1 = stations()['retainer_groove']
    ring = annulus(MOUNT['housing_contact_diameter'] / 2, r['groove_radius'] - r['radial_clearance'], g1 - r['thickness'], r['thickness'])
    return one(ring.cut(box(g0 - 1, g1 + 1, -r['groove_radius'] - 1, 0, -r['gap'] / 2, r['gap'] / 2)), 'retainer ring')


def axle_clip():
    """Printed radial U clip in the journal groove; bears on the 608 inner ring's outboard face only."""
    k = MOUNT['axle_clip']
    g0 = stations()['clip_groove'][0]
    clip = annulus(k['bore_radius'], MOUNT['shaft_contact_diameter'] / 2, g0, k['thickness'])
    mouth = box(g0 - .1, g0 + k['thickness'] + .1, 0, MOUNT['shaft_contact_diameter'], -k['mouth_width'] / 2, k['mouth_width'] / 2)
    return one(clip.cut(mouth.rotate((0, 0, 0), (1, 0, 0), k['notch_angle_deg'])), 'axle clip')


def bearing_rings():
    """The extra 608 as three coaxial bodies at its running position: inner ring, shield zone, outer ring (catalogue lands)."""
    b = MOUNT['bearing']
    b0, b1 = stations()['bearing']
    r_in, r_out = b['inner_land_diameter'] / 2, b['outer_land_diameter'] / 2
    return {'inner': annulus(b['id'] / 2, r_in, b0, b1 - b0), 'shield': annulus(r_in, r_out, b0, b1 - b0),
            'outer': annulus(r_out, b['od'] / 2, b0, b1 - b0)}


def build():
    """Printed outside-drive parts plus the 608 envelope, in the outside frame."""
    b = MOUNT['bearing']
    b0, b1 = stations()['bearing']
    return {'mount-x': mount_x(), 'wheel': wheel(), 'hub-retainer': retainer(), 'axle-clip': axle_clip(),
            'outer-bearing': one(annulus(b['id'] / 2, b['od'] / 2, b0, b1 - b0), '608 envelope')}


def checks(parts):
    """Running clearance over a full turn, race-only contacts, positive retention both ways, assembly path and screens."""
    st, o = stations(), MOUNT['outside']
    rings = bearing_rings()
    out, failures = {'stations_mm': {k: v if isinstance(v, float) else [round(a, 3) for a in v] if isinstance(v, tuple) else v for k, v in st.items()}}, []
    turn = lambda s, a: s.rotate((0, 0, 0), (1, 0, 0), a)
    # Running: wheel and retainer (with the outer ring) turn; X, clip and inner ring stand still.
    run = {}
    for a in range(0, 360, 5):
        for r in ['wheel', 'hub-retainer']:
            for s in ['mount-x', 'axle-clip']:
                key = f'{r} / {s}'
                run[key] = min(run.get(key, 1e9), gap(turn(parts[r], a), parts[s]))
            run[f'{r} / 608 inner ring'] = min(run.get(f'{r} / 608 inner ring', 1e9), gap(turn(parts[r], a), rings['inner']))
    for s in ['mount-x', 'axle-clip']:
        run[f'608 outer ring / {s}'] = gap(rings['outer'], parts[s])
    out['running_min_gap_mm'] = {k: round(v, 3) for k, v in run.items()}
    if run['wheel / mount-x'] < o['running_gap'] - 1e-6:
        failures.append('wheel closer than running_gap to the X over a turn')
    if min(run.values()) <= 1e-6:
        failures.append('a turning part touches a stationary part')
    # Race-only contacts in the running pose (rings touching = 0 gap and no overlap; everything else > 0).
    contact = {}
    for n in ['wheel', 'hub-retainer', 'mount-x', 'axle-clip']:
        contact[n] = {f'608 {k} ring' if k != 'shield' else '608 shield zone': {'gap_mm': round(gap(parts[n], s), 3), 'overlap_mm3': round(volume(parts[n].intersect(s)), 5)}
                      for k, s in rings.items()}
    out['race_contacts'] = contact
    expect = {'wheel': '608 outer ring', 'mount-x': '608 inner ring'}
    for n, c in contact.items():
        if any(v['overlap_mm3'] > 1e-5 for v in c.values()):
            failures.append(f'{n} overlaps the 608')
        if c['608 shield zone']['gap_mm'] <= 1e-6:
            failures.append(f'{n} touches the 608 shield zone')
        if n in expect and c[expect[n]]['gap_mm'] > 1e-6:
            failures.append(f'{n} does not bear on the {expect[n]}')
        other = '608 inner ring' if n in ['wheel', 'hub-retainer'] else '608 outer ring'
        if c[other]['gap_mm'] <= 1e-6:
            failures.append(f'{n} touches the opposite ring ({other})')
    # Positive retention: each way the wheel or the inner ring moves, a printed face blocks it within the stated play.
    k, r = MOUNT['axle_clip'], MOUNT['retainer']
    float_outer = MOUNT['axial_play'] + r['groove_extra']
    float_inner = MOUNT['axial_play'] + k['groove_extra']
    block = {
        'wheel inward (magnet pull) stopped by the lip on the outer ring': volume(parts['wheel'].translate((-.05, 0, 0)).intersect(rings['outer'])),
        f'wheel outward (knob pull) stopped by the retainer on the outer ring within {float_outer:g} mm':
            volume(parts['hub-retainer'].translate((float_outer + .05, 0, 0)).intersect(rings['outer'])),
        'retainer held in its groove (outboard)': volume(parts['hub-retainer'].translate((.05, 0, 0)).intersect(parts['wheel'])),
        f'retainer held in its groove (inboard, {r["groove_extra"]:g} mm float)': volume(parts['hub-retainer'].translate((-r['groove_extra'] - .05, 0, 0)).intersect(parts['wheel'])),
        'inner ring inward stopped by the X shoulder': volume(rings['inner'].translate((-.05, 0, 0)).intersect(parts['mount-x'])),
        f'inner ring outward stopped by the axle clip within {MOUNT["axial_play"]:g} mm': volume(rings['inner'].translate((MOUNT['axial_play'] + .05, 0, 0)).intersect(parts['axle-clip'])),
        f'axle clip held in the journal groove ({k["groove_extra"]:g} mm float)': volume(parts['axle-clip'].translate((k['groove_extra'] + .05, 0, 0)).intersect(parts['mount-x'])),
    }
    out['retention_blocking_overlap_mm3'] = {n: round(v, 4) for n, v in block.items()}
    out['axial_float_mm'] = {'outer ring in the wheel': round(float_outer, 3), 'inner ring on the journal': round(float_inner, 3)}
    if min(block.values()) < 1e-3:
        failures.append('a retention direction is not blocked')
    # Assembly path: 608 into the hub from the wall side; wheel, 608 and retainer onto the journal; clip in radially through the notch.
    path = {}
    bearing = parts['outer-bearing']
    path['608 into the hub from the wall side'] = max(volume(bearing.translate((-d, 0, 0)).intersect(parts['wheel'])) for d in [x * .5 for x in range(0, 41)])
    sub = parts['wheel'].fuse(parts['hub-retainer']).fuse(bearing)
    path['wheel, 608 and retainer onto the journal'] = max(volume(sub.translate((d, 0, 0)).intersect(parts['mount-x'])) for d in [x * .5 for x in range(1, 41)])
    a = math.radians(k['notch_angle_deg'])
    clip_path = [volume(parts['axle-clip'].translate((0, d * math.cos(a), d * math.sin(a))).intersect(parts['wheel'])) for d in range(0, 21)]
    path['axle clip through the lip notch (wheel turned to the notch)'] = max(clip_path)
    path['axle clip with the notch turned away (blocked)'] = volume(parts['axle-clip'].translate((0, 10 * math.cos(a), 10 * math.sin(a))).intersect(turn(parts['wheel'], 90)))
    out['assembly_path_max_overlap_mm3'] = {n: round(v, 4) for n, v in path.items()}
    if max(v for n, v in path.items() if 'blocked' not in n) > 1e-5:
        failures.append('assembly path collides')
    # Elastic screens (assumed values; not a qualification).
    ring_w = r['groove_radius'] - r['radial_clearance'] - MOUNT['housing_contact_diameter'] / 2
    squeeze = r['groove_radius'] - r['radial_clearance'] - (MOUNT['bearing']['od'] / 2 + MOUNT['pocket_radial_clearance'])
    rm = (r['groove_radius'] - r['radial_clearance'] + MOUNT['housing_contact_diameter'] / 2) / 2
    out['retainer_install'] = {'radial_squeeze_mm': round(squeeze, 3), 'gap_closure_mm': round(2 * math.pi * squeeze, 2), 'free_gap_mm': r['gap'],
                               'bending_strain_pct': round(100 * (ring_w / 2) * squeeze / rm ** 2, 2),
                               'basis': 'Curved-beam estimate for squeezing the ring through the bore; printed PLA strain limit not measured.'}
    if 2 * math.pi * squeeze >= r['gap']:
        failures.append('retainer gap too small to squeeze it through the bore')
    out['axle_clip_jaw_deflection_each_mm'] = round((2 * k['groove_radius'] - k['mouth_width']) / 2, 3)
    out['cup_inner_edge_radius_mm'] = MOUNT['anchor_radius'] - MOUNT['anchor_pad_radius']
    out['wheel_radius_mm'] = PARAMETERS['outside_diameter_mm'] / 2
    if out['cup_inner_edge_radius_mm'] <= out['wheel_radius_mm']:
        failures.append('anchor cups inside the wheel sweep')
    out['knob'] = {'tip_x': round(st['wheel_back'] + PARAMETERS['knob_front_mm'] + PARAMETERS['knob_length_mm'], 3),
                   'exposed_grip_mm': round(PARAMETERS['knob_front_mm'] + PARAMETERS['knob_length_mm'] - PARAMETERS['structural_thickness_mm'], 3)}
    out['drive_magnet_pockets_mm'] = {'depth': MAGNETS['drive_pocket_depth'], 'front_cover': 0,
                                     'back_wall': PARAMETERS['structural_thickness_mm'] - MAGNETS['drive_pocket_depth'],
                                     'face_to_wall': st['wheel_back']}
    if PARAMETERS['structural_thickness_mm'] - MAGNETS['drive_pocket_depth'] < 1:
        failures.append('Wheel magnet pocket has less than 1 mm backing')
    for n, s in parts.items():
        if not s.isValid() or len(s.Solids()) != 1:
            failures.append(f'{n}: not one valid solid')
    out['failures'] = failures
    out['pass'] = not failures
    return out
