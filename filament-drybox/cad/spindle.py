#!/usr/bin/env python3
"""Two printed center parts: a slender spindle and one threaded clamping collar.

The spindle carries both 608 journals (the drive journal keeps the disc key and
clip groove), a slender central shaft, an external thread near the refill end
and a fixed 45-degree centering cone at the drive end. The collar screws onto
that thread and carries the matching cone at the refill end. The two cones seat
in the spool's bore-end chamfers and clamp the hub between them; the clamp force
stays inside spindle, collar and spool, so the 608s carry no axial preload.

The collar is locked against turning on the spindle in both directions: a key on a
compliant arm in the collar wall drops into one of the slots cut through the
spindle's thread crests (the thread root stays whole). Lifting the arm's paddle
frees the collar to turn.

Geometry is along X (the axle), with the axle at Y = bearings.axis_y and Z = 0.
All values come from stand.json: `axle` (journals and key/groove interfaces),
`bearings` and `spindle` (this module's parts).
"""
import math
import cadquery as cq


def _cyl(r, x0, x1, y):
    return cq.Solid.makeCylinder(r, x1 - x0, cq.Vector(x0, y, 0), cq.Vector(1, 0, 0))


def _box(x0, x1, y0, y1, z0, z1):
    return cq.Solid.makeBox(x1 - x0, y1 - y0, z1 - z0, cq.Vector(x0, y0, z0))


def _one(shape, name):
    if not shape.isValid() or len(shape.Solids()) != 1:
        raise ValueError(f'{name}: invalid or not one solid ({len(shape.Solids())})')
    return shape


def _join(shapes, name):
    shape = shapes[0]
    for other in shapes[1:]:
        shape = shape.fuse(other)
    return _one(shape.clean(), name)


def _revolve(points, y, angle=360):
    """Solid of revolution about the axle from a closed (x, r) profile; partial angles start at +Y toward +Z."""
    wire = cq.Workplane('XY').polyline([(x, r) for x, r in points]).close().val()
    face = cq.Face.makeFromWires(wire)
    return cq.Solid.revolve(face, angle, cq.Vector(0, 0, 0), cq.Vector(1, 0, 0)).translate((0, y, 0))


def _sector(r0, r1, x0, x1, a0, a1, y):
    """Annular sector between angles a0..a1 (degrees, +Y toward +Z about +X)."""
    return _revolve([(x0, r0), (x1, r0), (x1, r1), (x0, r1)], y, a1 - a0).rotate((0, y, 0), (1, y, 0), a0)


def _radial_box(x0, x1, r0, r1, width, angle, y):
    """Box spanning radii r0..r1 along the direction at `angle`, `width` wide tangentially."""
    return _box(x0, x1, y + r0, y + r1, -width / 2, width / 2).rotate((0, y, 0), (1, y, 0), angle)


def _helical(profile, pitch, x0, x1, phase_x, y, lefthand):
    """Sweep a closed (r, axial) profile along a helix and trim it to x0..x1.

    The helix starts at an axial position congruent to phase_x (mod pitch), so a
    male tooth and a female cutter built from the same phase_x line up.
    """
    r0 = min(r for r, _ in profile)
    start = phase_x - math.ceil((phase_x - (x0 - pitch)) / pitch) * pitch
    height = x1 + pitch - start
    path = cq.Wire.makeHelix(pitch, height, r0, lefthand=lefthand)
    swept = cq.Workplane('XZ').polyline(profile).close().sweep(path, isFrenet=True).val()
    outer = max(r for r, _ in profile) + 0.5
    slab = cq.Solid.makeCylinder(outer, x1 - x0, cq.Vector(0, 0, x0 - start))
    tooth = swept.intersect(slab)
    if not tooth.isValid():
        raise ValueError('helical thread solid is invalid')
    # Local Z (helix axis) -> global X; then move to the axle.
    return tooth.translate((0, 0, start)).rotate((0, 0, 0), (0, 1, 0), 90).translate((0, y, 0))


def thread_profiles(t):
    """Truncated 60-degree tooth (male) and the matching clearance groove (female)."""
    tan30 = math.tan(math.radians(30))
    depth = t['major_radius'] - t['root_radius']
    root_width = t['crest_width'] + 2 * depth * tan30
    lo = t['root_radius'] - 0.1  # overlaps the boss so the tooth fuses
    male = [(lo, -(root_width / 2 + 0.1 * tan30)), (t['major_radius'], -t['crest_width'] / 2),
            (t['major_radius'], t['crest_width'] / 2), (lo, root_width / 2 + 0.1 * tan30)]
    bore = t['root_radius'] + t['radial_clearance']
    groove_root = t['major_radius'] + t['radial_clearance']
    half = lambda r: (t['crest_width'] / 2 + (t['major_radius'] - r) * tan30) + t['flank_clearance']
    glo = bore - 0.1
    female = [(glo, -half(glo)), (groove_root, -half(groove_root)), (groove_root, half(groove_root)), (glo, half(glo))]
    return male, female, bore


def _journal(c, side):
    """608 journal, shoulder, root fillet and inner-race thrust sleeve (one side)."""
    a = c['axle']; y = c['bearings']['axis_y']
    s = side
    end = a['right_end_x'] if s > 0 else a['left_end_x']
    radius = a['journal_radius'] if s > 0 else a['left_journal_radius']
    inner = a['shoulder_end_x'] - a['shoulder_length']
    shoulder = _cyl(a['shoulder_radius'], inner, a['shoulder_end_x'], y)
    shoulder = shoulder if s > 0 else shoulder.mirror('YZ')
    pin = _cyl(radius, min(s * a['shoulder_end_x'], end), max(s * a['shoulder_end_x'], end), y)
    body = shoulder.fuse(pin).clean()
    root = [e for e in body.Edges() if e.geomType() == 'CIRCLE' and abs(e.radius() - radius) < 1e-6
            and abs(e.Center().x - s * a['shoulder_end_x']) < 1e-6]
    if len(root) != 1:
        raise ValueError(('journal root edge', len(root)))
    body = body.fillet(a['journal_root_radius'], root)
    x0, x1 = s * a['shoulder_end_x'], s * a['thrust_face_x']
    length = abs(x1 - x0); direction = cq.Vector(s, 0, 0); base = cq.Vector(x0, y, 0)
    sleeve = cq.Solid.makeCone(a['sleeve_outer_root_radius'], a['sleeve_outer_face_radius'], length, base, direction).cut(
        cq.Solid.makeCone(a['sleeve_inner_root_radius'], a['sleeve_inner_face_radius'], length, base, direction))
    body = body.fuse(sleeve).clean()
    if s > 0:
        for angle in range(0, 360, 60):
            body = body.cut(_box(a['key_start_x'], a['right_end_x'] + 0.1, y + a['key_apothem'], y + 8, -8, 8)
                            .rotate((0, y, 0), (1, y, 0), angle))
        groove = _cyl(a['journal_radius'] + 0.1, a['groove_start_x'], a['groove_end_x'], y).cut(
            _cyl(a['groove_radius'], a['groove_start_x'] - 0.1, a['groove_end_x'] + 0.1, y))
        body = body.cut(groove)
    return body


def _cone_ring(sp, y, side):
    """45-degree centering/clamping cone that seats in the spool bore-end chamfer."""
    x_in, x_out = sp['ring_x']
    seat = lambda x: sp['seat_bore_radius'] + (x - sp['seat_start_x']) - sp['seat_radial_gap']
    pts = [(x_in, sp['ring_inner_radius']), (x_out, sp['ring_inner_radius']), (x_out, seat(x_out)), (x_in, seat(x_in))]
    ring = _revolve(pts, y)
    return ring if side > 0 else ring.mirror('YZ')


def _spider(sp, y, side, arm_x, hub_radius):
    """Radial arms at arm_x plus axial struts into the cone ring (drive side; mirrored for the refill side).

    The struts share the ring's inner radius and run 0.5 mm into it, so each joins the full ring section."""
    parts = []
    w = sp['arm_width']
    s0, s1 = sp['strut_radii']
    for i in range(sp['arm_count']):
        angle = i * 360 / sp['arm_count']
        arm = _box(arm_x[0], arm_x[1], y + hub_radius - 0.5, y + s1, -w / 2, w / 2)
        strut = _box(arm_x[0], sp['ring_x'][0] + 0.5, y + s0, y + s1, -w / 2, w / 2)
        for piece in (arm, strut):
            piece = piece.rotate((0, y, 0), (1, y, 0), angle)
            parts.append(piece if side > 0 else piece.mirror('YZ'))
    return parts


def lock_slots(c):
    """Crest-only lock slots along the thread; each slot floor is a plane tangent to the thread root."""
    sp = c['spindle']; t = sp['thread']; k = sp['lock']; y = c['bearings']['axis_y']
    step = 360 / k['slot_count']; phase = k['key_angle_deg'] % step
    return [_radial_box(t['thread_x'][0] - 0.2, t['thread_x'][1] + 0.2, t['root_radius'] + 0.01, t['major_radius'] + 0.5,
                        k['slot_width'], phase + i * step, y) for i in range(k['slot_count'])]


def lock_positions(c):
    """Collar travel between neighbouring lock positions (one slot pitch of rotation)."""
    k = c['spindle']['lock']
    return c['spindle']['thread']['pitch'] / k['slot_count']


def lock_key(c, lift=0.0):
    """Key with its pull-out paddle, raised radially by `lift` (0 = resting in a slot)."""
    sp = c['spindle']; k = sp['lock']; h0 = sp['collar']['hub_x'][0]; y = c['bearings']['axis_y']
    kx = (h0 + k['key_x_from_hub'][0], h0 + k['key_x_from_hub'][1])
    key = _radial_box(kx[0], kx[1], k['key_tip_radius'] + lift, k['arm_radii'][0] + 0.7 + lift, k['key_width'], k['key_angle_deg'], y)
    paddle = _radial_box(h0, h0 + k['paddle_length_x'], k['arm_radii'][1] - 0.3 + lift, k['paddle_outer_radius'] + lift,
                         k['key_width'], k['key_angle_deg'], y)
    return key.fuse(paddle).clean()


def spindle(c):
    sp = c['spindle']; a = c['axle']; t = sp['thread']; y = c['bearings']['axis_y']
    male, _, _ = thread_profiles(t)
    shaft = _cyl(sp['shaft_radius'], t['boss_x'][1] - 0.5, sp['drive_arm_x'][0] + 0.5, y)
    boss = _cyl(t['root_radius'], -a['shoulder_end_x'], t['boss_x'][1], y)
    tooth = _helical(male, t['pitch'], t['thread_x'][0], t['thread_x'][1], t['phase_x'], y, t['hand'] == 'left')
    drive_hub = _cyl(a['shoulder_radius'], sp['drive_arm_x'][0], a['shoulder_end_x'] - a['shoulder_length'] + 0.1, y)
    # Ramp from the boss's inboard face to the shaft (printed drive end down, so that face would otherwise need support).
    xb, run = t['boss_x'][1], (t['root_radius'] - sp['shaft_radius']) / math.tan(math.radians(sp['boss_ramp_angle_deg']))
    inner = sp['shaft_radius'] - 0.5
    ramp = _revolve([(xb - 0.1, inner), (xb - 0.1, t['root_radius'] - 0.1), (xb, t['root_radius']), (xb + run, sp['shaft_radius']),
                     (xb + run + 0.1, inner)], y)
    pieces = [_journal(c, 1), _journal(c, -1), shaft, boss, tooth, drive_hub, ramp, _cone_ring(sp, y, 1),
              *_spider(sp, y, 1, sp['drive_arm_x'], a['shoulder_radius'])]
    body = _join(pieces, 'spindle')
    for slot in lock_slots(c):
        body = body.cut(slot)
    return _one(body.clean(), 'spindle with lock slots')


def collar(c, travel=0.0, lift=0.0, lock=True):
    """Threaded collar; travel > 0 moves it inboard (+X) along the thread, rotating with the helix.

    `lift` raises the lock key radially (a rigid stand-in for the arm's bending) to model the released state;
    lock=False leaves out the arm and key (for clearance checks of the key against the collar body).
    """
    sp = c['spindle']; t = sp['thread']; col = sp['collar']; k = sp['lock']; y = c['bearings']['axis_y']
    _, female, bore = thread_profiles(t)
    hub_x = col['hub_x']; h0 = hub_x[0]
    hub = _cyl(col['hub_outer_radius'], hub_x[0], hub_x[1], y).cut(_cyl(bore, hub_x[0] - 0.1, hub_x[1] + 0.1, y))
    groove = _helical(female, t['pitch'], hub_x[0] - 0.2, hub_x[1] + 0.2, t['phase_x'], y, t['hand'] == 'left')
    hub = hub.cut(groove)
    # Lock: a pocket in the outer hub wall holds the compliant arm; a guide hole through the threaded wall holds the key.
    # The pocket runs through the whole hub so it has no roof over the arm (printed axis-vertical, a roof would bridge
    # one layer above the arm); the hole roof stays closed, key_hole_roof_gap above the key, to tie the hub together.
    hub = hub.cut(_sector(k['pocket_radii'][0], k['pocket_radii'][1], hub_x[0] - 0.1, hub_x[1] + 0.1,
                          k['arm_root_angle_deg'], k['pocket_end_angle_deg'], y))
    kx = (h0 + k['key_x_from_hub'][0], h0 + k['key_x_from_hub'][1])
    hub = hub.cut(_radial_box(kx[0] - 0.15, kx[1] + k['key_hole_roof_gap'], bore - 0.5, k['pocket_radii'][0] + 0.1,
                              k['key_width'] + 2 * k['hole_clearance'], k['key_angle_deg'], y))
    arm = _sector(k['arm_radii'][0], k['arm_radii'][1], h0, h0 + k['arm_length_x'], k['arm_root_angle_deg'] - 1.0, k['key_angle_deg'], y)
    pieces = [hub, _cone_ring(sp, y, -1), *_spider(sp, y, -1, col['arm_x'], col['hub_outer_radius'])] + ([arm, lock_key(c, lift)] if lock else [])
    part = _join(pieces, 'collar')
    if travel:
        turn = 360 * travel / t['pitch'] * (-1 if t['hand'] == 'left' else 1)
        part = part.translate((travel, 0, 0)).rotate((0, y, 0), (1, y, 0), turn)
    return part
