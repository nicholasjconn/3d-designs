#!/usr/bin/env python3
"""Build and check the whole current filament drybox from its canonical sources.

This is the single entry point. It runs each part's own producer (stand.py for the
holder, outlet.py, clip.py; wheel.py in-process for the outside drive: fixed X, wheel,
608 retainer and axle clip), then checks the interfaces between systems (drive and
anchor magnets, locked axial endpoints, unchanged printed parts) and writes
manifest.json with source and output SHA-256 digests. A producer
whose sources are unchanged since the last run into the same --output is reused.
Inventory, print states and the locked axial endpoints come from drybox.json. Container
dimensions are not measured: the outside drive is placed across outlet.json's nominal wall and the outlet is not
placed on the container. Nothing here slices, prints or approves fabrication.
"""
from pathlib import Path
import argparse
import hashlib
import json
import math
import platform
import subprocess
import sys

import cadquery as cq
from OCP.BRepExtrema import BRepExtrema_DistShapeShape

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
sys.path.insert(0, str(HERE))  # part modules (wheel, outlet, clip) import from here

# Each producer: sources it reads, the command that builds it, and the outputs it must leave.
PRODUCERS = {
    'holder': {'sources': ['stand.py', 'stand.json', 'spindle.py', 'cad_helpers.py'],
               'command': ['stand.py', '--output', '{out}'],
               'outputs': ['fixed-stand.step', 'left-carrier.step', 'right-carrier.step', 'spindle.step', 'collar.step',
                           'drive-rotor.step', 'retaining-clip.step', 'left-bearing.step', 'right-bearing.step',
                           'stand-build.json', 'stand-display.json']},
    'outlet': {'sources': ['outlet.py', 'outlet.json'],
               'command': ['outlet.py', '--output', '{out}'],
               'outputs': ['body-native.step', 'nut-native.step', 'cap-native.step', 'export-receipt.json']},
    'clip': {'sources': ['clip.py', 'clip.json', 'outlet.json', 'cad_helpers.py'],
             'command': ['clip.py', '--output', '{out}'],
             'outputs': ['fixed.step', 'gate.step', 'checks.json']},
    'wheel': {'sources': ['wheel.py', 'wheel.json', 'stand.json'], 'command': None,
              'outputs': ['mount-x.step', 'wheel.step', 'hub-retainer.step', 'axle-clip.step', 'outer-bearing.step', 'checks.json']},
}
# Holder parts already printed or sent and kept unchanged by the outside-drive change; compared with --reference-build.
# The gray frame is excluded on purpose: it gained the four anchor branches and glue pockets (baseline commit 7f54693).
REFERENCE_PARTS = ['left-carrier', 'right-carrier', 'spindle', 'collar', 'drive-rotor', 'retaining-clip', 'left-bearing', 'right-bearing']


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def volume(shape):
    return sum(s.Volume() for s in shape.Solids())


def gap(a, b):
    return BRepExtrema_DistShapeShape(a.wrapped, b.wrapped).Value()


def step(path):
    shape = cq.importers.importStep(str(path)).val()
    if not shape.isValid():
        raise ValueError(f'{path}: invalid solid')
    return shape


def run_producers(out, previous):
    records = {}
    for name, p in PRODUCERS.items():
        target = out / name
        digests = {s: sha(HERE / s) for s in p['sources']}
        old = previous.get(name, {})
        reused = (old.get('sources_sha256') == digests and
                  all((target / o).exists() and sha(target / o) == old.get('outputs_sha256', {}).get(o) for o in p['outputs']))
        if not reused:
            target.mkdir(parents=True, exist_ok=True)
            if p['command']:
                cmd = [sys.executable, str(HERE / p['command'][0])] + [a.format(out=target) for a in p['command'][1:]]
                done = subprocess.run(cmd, capture_output=True, text=True)
                (target / 'producer.log').write_text(done.stdout + done.stderr)
                if done.returncode:
                    raise SystemExit(f'{name} producer failed ({done.returncode}); see {target / "producer.log"}')
            else:
                import wheel
                parts = wheel.build()
                for n, shape in parts.items():
                    cq.exporters.export(shape, str(target / f'{n}.step'))
                (target / 'checks.json').write_text(json.dumps(wheel.checks(parts), indent=2) + '\n')
        missing = [o for o in p['outputs'] if not (target / o).exists()]
        if missing:
            raise SystemExit(f'{name}: producer did not write {missing}')
        records[name] = {'reused': reused, 'sources_sha256': digests,
                         'outputs_sha256': {o: sha(target / o) for o in p['outputs']}}
    return records


def spool_fit(out, holder_outputs, spool, spool_python, previous):
    """Spool fit evidence bound to the holder files it read, the spool meshes and spool_fit.py.

    Reused when those are unchanged. Without --spool, earlier evidence is kept only if it is bound to the
    current holder files (the spool meshes cannot be rechecked); otherwise the fit is omitted.
    """
    fit = out / 'holder' / 'spool-fit.json'
    binding = {'holder_sha256': {f: holder_outputs[f] for f in ['stand-build.json', 'stand-display.json']},
               'spool_fit_sha256': sha(HERE / 'spool_fit.py')}
    old = previous or {}
    same_holder = all(old.get(k) == v for k, v in binding.items()) and fit.exists() and sha(fit) == old.get('output_sha256')
    if not spool:
        return dict(old, reused=True, spool_files_rechecked=False) if same_holder else None
    binding['spool_sha256'] = {n: sha(Path(spool) / f'bambulab_spool_{n}.stl') for n in ['narrow', 'wide']}
    if same_holder and old.get('spool_sha256') == binding['spool_sha256']:
        return dict(old, reused=True, spool_files_rechecked=True)
    done = subprocess.run([str(spool_python), str(HERE / 'spool_fit.py'), '--native', str(out / 'holder'),
                           '--spool', str(spool), '--output', str(fit)], capture_output=True, text=True)
    if done.returncode:
        raise SystemExit('spool_fit.py failed:\n' + done.stdout[-2000:] + done.stderr[-2000:])
    return dict(binding, output_sha256=sha(fit), reused=False, spool_files_rechecked=True)


def magnet(m, x0, x1, y, z):
    return cq.Solid.makeCylinder(m['diameter'] / 2, x1 - x0, cq.Vector(x0, y, z), cq.Vector(1, 0, 0))


def system_checks(out, reference, previous, holder_outputs):
    stand = json.loads((HERE / 'stand.json').read_text())
    outlet_c = json.loads((HERE / 'outlet.json').read_text())
    clip_c = json.loads((HERE / 'clip.json').read_text())
    build = json.loads((out / 'holder' / 'stand-build.json').read_text())
    m, axis_y = stand['magnets'], stand['bearings']['axis_y']
    disc = step(out / 'holder' / 'drive-rotor.step')
    wall_x = build['dimensions_mm']['right_wall_x']
    t_wall = outlet_c['wall_thickness_mm']
    checks, failures, placed = {}, [], {}
    if not build['checks']['pass']:
        failures.append('holder: ' + build['checks']['summary'])
    # Each producer's own validity checks count toward the system pass.
    clip_report = json.loads((out / 'clip' / 'checks.json').read_text())
    if not all(clip_report['valid_solids'].values()):
        failures.append('clip: invalid solid')
    if clip_report['closed_part_intersection_mm3'] > 1e-4:
        failures.append(f"clip: closed bodies overlap {clip_report['closed_part_intersection_mm3']:.4f} mm³")
    receipt = json.loads((out / 'outlet' / 'export-receipt.json').read_text())
    for n in ['body', 'nut', 'cap']:
        r = receipt['parts'].get(n, {})
        if r.get('valid') is not True or r.get('solid_count') != 1:
            failures.append(f'outlet {n}: export receipt is not one valid solid')

    # Outside drive (wheel.py frame: x=0 on the wall's outside face, axis at y=z=0) placed across the nominal wall.
    import wheel as drive
    outside = {n: step(out / 'wheel' / f'{n}.step') for n in ['mount-x', 'wheel', 'hub-retainer', 'axle-clip', 'outer-bearing']}
    drive_report = json.loads((out / 'wheel' / 'checks.json').read_text())
    if not drive_report['pass']:
        failures.append('outside drive: ' + '; '.join(drive_report['failures']))
    st = drive.stations()
    shift = (wall_x + t_wall, axis_y, 0)
    for n, shape in outside.items():
        placed[n] = shape.translate(shift)

    # Disc ↔ wheel: a purchased magnet fits each pocket of both parts, on the same axes across the wall.
    front = stand['disc']['front_x']
    pockets = []
    for i in range(m['count']):
        a = 2 * math.pi * i / m['count']
        y, z = m['pitch_radius'] * math.cos(a), m['pitch_radius'] * math.sin(a)
        in_disc = magnet(m, front - m['front_cover'] - m['thickness'], front - m['front_cover'], axis_y + y, z)
        x0 = st['wheel_back'] + m['front_cover']
        in_wheel = magnet(m, x0, x0 + m['thickness'], y, z)
        pockets.append({'disc_overlap_mm3': round(volume(disc.intersect(in_disc)), 4),
                        'wheel_overlap_mm3': round(volume(outside['wheel'].intersect(in_wheel)), 4)})
        if pockets[-1]['disc_overlap_mm3'] > 1e-4 or pockets[-1]['wheel_overlap_mm3'] > 1e-4:
            failures.append(f'magnet {i} does not fit its disc or wheel pocket')
    # Wheel magnet faces sit wheel_back + front_cover outside the wall; the disc's magnet faces sit behind its front cover.
    face_gap = {f'{w:g} mm wall': round((wall_x - (front - m['front_cover'])) + w + st['wheel_back'] + m['front_cover'], 3)
                for w in outlet_c['wall_thickness_checks_mm']}
    checks['magnet_coupling'] = {'pockets': pockets, 'magnet_face_to_face_gap_mm': face_gap,
                                 'baseline_gap_mm_at_nominal_wall': round((wall_x - (front - m['front_cover'])) + t_wall + m['front_cover'], 3),
                                 'disc_front_to_wall_mm': round(wall_x - front, 3),
                                 'basis': 'Disc magnet front face to wheel magnet front face through the drive wall; wall thickness unmeasured; coupling torque not evaluated.'}
    # Anchor pairs: a magnet fits each frame glue pocket and each X pocket, coaxial, faces separated only by the wall.
    frame = step(out / 'holder' / 'fixed-stand.step')
    mount = stand['mount']
    anchor = []
    for (y, z), (yo, zo) in zip(json.loads((out / 'holder' / 'stand-build.json').read_text())['checks']['anchor_branches']['anchor_centers_yz'], drive.anchors()):
        inside = magnet(m, wall_x - m['thickness'], wall_x, y, z)
        outside_mag = magnet(m, wall_x + t_wall, wall_x + t_wall + m['thickness'], axis_y + yo, zo)
        row = {'center_yz': [round(y, 3), round(z, 3)], 'axis_offset_mm': round(math.hypot(y - axis_y - yo, z - zo), 4),
               'frame_pocket_overlap_mm3': round(volume(frame.intersect(inside)), 4),
               'x_pocket_overlap_mm3': round(volume(placed['mount-x'].intersect(outside_mag)), 4),
               'face_gap_mm': round(gap(inside, outside_mag), 3)}
        anchor.append(row)
        if row['axis_offset_mm'] > 1e-3 or row['frame_pocket_overlap_mm3'] > 1e-4 or row['x_pocket_overlap_mm3'] > 1e-4 or abs(row['face_gap_mm'] - t_wall) > 1e-3:
            failures.append(f'anchor pair at {row["center_yz"]} misaligned or does not fit')
    checks['anchor_pairs'] = {'pairs': anchor, 'wall_mm': t_wall,
                              'basis': 'Pocket magnets flush with the frame contact plane and the X wall face; holding force, glue and tilt stiffness unqualified.'}
    # The outside drive stays outside the wall: nothing reaches the frame or the disc closer than the wall thickness.
    near = min(gap(placed[n], h) for n in outside for h in [frame, disc])
    checks['outside_drive_to_holder_gap_mm'] = round(near, 3)
    if near < t_wall - 1e-6:
        failures.append('outside drive intrudes on the wall or holder')
    checks['outside_drive'] = {k: drive_report[k] for k in drive_report if k != 'failures'}

    # Locked axial endpoints and base (drybox.json axial_limits_mm); exact to 0.001 mm.
    limits = json.loads((HERE / 'drybox.json').read_text())['axial_limits_mm']
    # Measured from the exported solids, not from declared dimensions.
    solids = {n: frame if n == 'fixed-stand' else step(out / 'holder' / f'{n}.step') for n in build['checks']['parts']}
    box = {n: s.BoundingBox() for n, s in solids.items()}
    holder = [min(b.xmin for b in box.values()), max(b.xmax for b in box.values())]
    full = [holder[0], max(holder[1], max(placed[n].BoundingBox().xmax for n in outside))]
    # Base footprint: the frame cut by a 1 mm slab on the floor (the anchor branches above do not count).
    floor_y = box['fixed-stand'].ymin
    foot = frame.intersect(cq.Solid.makeBox(1000, 1, 1000, cq.Vector(-500, floor_y, -500))).BoundingBox()
    measured = {'holder': holder, 'spindle': [box['spindle'].xmin, box['spindle'].xmax], 'full_nominal_wall': full,
                'base': [foot.xlen, foot.zlen]}
    checks['axial_limits_mm'] = {k: {'locked': limits[k], 'measured': [round(a, 4) for a in v]} for k, v in measured.items()}
    for k, v in measured.items():
        if any(abs(a - b) > 1e-3 for a, b in zip(v, limits[k])):
            failures.append(f'{k} endpoints {[round(a, 3) for a in v]} differ from the locked {limits[k]}')

    # Outlet: printing configuration (PTFE lead in, no cap) and storage configuration (cap on, clip on the tail).
    import outlet, clip
    o = outlet.build(outlet_c)
    for n in ['body', 'nut', 'cap']:
        native = step(out / 'outlet' / f'{n}-native.step')
        if abs(volume(native) - volume(o[n])) > 0.05:
            failures.append(f'outlet {n}: export differs from source build')
    printing = {}
    for a, b in [('continuous-tube', 'body'), ('continuous-tube', 'outer-fitting'), ('continuous-tube', 'nut'),
                 ('filament', 'continuous-tube'), ('body', 'nut'), ('body', 'wall'), ('nut', 'wall')]:
        printing[f'{a} / {b}'] = {'overlap_mm3': round(volume(o[a].intersect(o[b])), 4), 'gap_mm': round(gap(o[a], o[b]), 3)}
        if printing[f'{a} / {b}']['overlap_mm3'] > 1e-4:
            failures.append(f'outlet printing configuration: {a} overlaps {b}')
    # clip.build() already puts the nominal filament axis at x = y = 0, the outlet's filament axis; only lift it to its station.
    clip_parts = clip.build(clip.load_config())
    z0 = outlet_c['tail']['clip_center_z_mm'] - clip_c['axial_height_mm'] / 2
    clip_placed = {n: s.translate((0, 0, z0)) for n, s in clip_parts.items()}
    storage = {}
    for n, s in clip_placed.items():
        for t in ['cap', 'body', 'outer-fitting']:
            storage[f'clip {n} / {t}'] = {'overlap_mm3': round(volume(s.intersect(o[t])), 4), 'gap_mm': round(gap(s, o[t]), 3)}
            if storage[f'clip {n} / {t}']['overlap_mm3'] > 1e-4:
                failures.append(f'outlet storage configuration: clip {n} overlaps {t}')
        storage[f'clip {n} / filament'] = {'overlap_mm3': round(volume(s.intersect(o['filament'])), 4),
                                           'note': 'Closed empty-stop pose; any overlap is the nominal grip on the filament.'}
    storage['cap / body'] = {'overlap_mm3': round(volume(o['cap'].intersect(o['body'])), 4), 'gap_mm': round(gap(o['cap'], o['body']), 3)}
    if storage['cap / body']['overlap_mm3'] > 1e-4:
        failures.append('outlet storage configuration: cap overlaps body')
    checks['outlet_printing'] = printing
    checks['outlet_storage'] = storage

    # Geometry preserved: current parts against a reference build (e.g. the build the running print was sliced from).
    # The comparison is reused when neither the holder outputs nor the reference files changed.
    if reference:
        files = [Path(reference) / f'{n}.step' for n in REFERENCE_PARTS]
        missing = [f.name for f in files if not f.exists() or not (out / 'holder' / f.name).exists()]
        if missing:
            raise SystemExit(f'reference build comparison: {missing} missing in {reference} or the holder output')
        key = {'holder_sha256': {f.name: holder_outputs[f.name] for f in files}, 'reference_sha256': {f.name: sha(f) for f in files}}
        old = previous.get('reference_build', {})
        if old.get('key') == key:
            same, reused = old['symmetric_difference_mm3'], True
        else:
            same, reused = {}, False
            for f in files:
                a, b = step(out / 'holder' / f.name), step(f)
                same[f.stem] = round(volume(a.cut(b)) + volume(b.cut(a)), 4)
        failures += [f'{n}: geometry differs from the reference build' for n, v in same.items() if v > 1e-3]
        checks['reference_build'] = {'directory': Path(reference).name, 'symmetric_difference_mm3': same, 'reused': reused, 'key': key,
                                     'scope': 'Printed or sent holder parts kept unchanged: ' + ', '.join(REFERENCE_PARTS) +
                                              '. The gray frame is not compared: it changed (anchor branches and glue pockets).'}
    checks['failures'] = failures
    checks['pass'] = not failures
    return checks, placed, o, clip_placed


def display(placed, o, clip_placed, out):
    """Meshes for the system preview, in holder coordinates (X axle, Y up). The outlet is set aside, not placed."""
    def mesh(shape, tol=.06):
        v, f = shape.tessellate(tol, .25)
        return {'vertices': [[round(c, 3) for c in p.toTuple()] for p in v], 'triangles': [list(t) for t in f]}
    # Outlet frame: +Z outward from the wall's outside face. Turn it so +Z points along -Z of the holder view and set it
    # in front of the holder, with the printing configuration on the left and storage on the right.
    def aside(shape, x):
        return shape.rotate((0, 0, 0), (0, 1, 0), 180).translate((x, 40, 140))
    # Outside drive and all purchased magnets, absolute holder coordinates; the viewer turns the drive-wheel set with the disc.
    import wheel as drive
    stand = json.loads((HERE / 'stand.json').read_text())
    m, axis_y = stand['magnets'], stand['bearings']['axis_y']
    x_wall = placed['mount-x'].BoundingBox().xmin
    rings = {k: v.translate((x_wall, axis_y, 0)) for k, v in drive.bearing_rings().items()}
    parts = {f'drive-{n}': mesh(placed[n]) for n in ['mount-x', 'wheel', 'hub-retainer', 'axle-clip']}
    parts['drive-608-outer'] = mesh(rings['outer'].fuse(rings['shield']))
    parts['drive-608-inner'] = mesh(rings['inner'])
    st = drive.stations()
    def mags(centers, x0):
        s = [magnet(m, x0, x0 + m['thickness'], axis_y + y, z) for y, z in centers]
        return cq.Compound.makeCompound(s)
    front = stand['disc']['front_x']
    parts['drive-magnets-wheel'] = mesh(mags(drive.magnet_centers(), x_wall + st['wheel_back'] + m['front_cover']))
    parts['drive-magnets-disc'] = mesh(mags(drive.magnet_centers(), front - m['front_cover'] - m['thickness']))
    parts['drive-magnets-x'] = mesh(mags(drive.anchors(), x_wall))
    parts['drive-magnets-frame'] = mesh(mags(drive.anchors(), front + stand['envelopes']['inner_air'] - m['thickness']))
    for n in ['body', 'nut', 'wall-ring', 'outer-fitting', 'wall', 'continuous-tube', 'filament']:
        parts[f'kit-print-{n}'] = mesh(aside(o[n], -45))
    for n in ['body', 'nut', 'wall-ring', 'cap-ring', 'outer-fitting', 'wall', 'cap', 'filament']:
        parts[f'kit-store-{n}'] = mesh(aside(o[n], 45))
    for n, s in clip_placed.items():
        parts[f'kit-store-clip-{n}'] = mesh(aside(s, 45), .03)
    (out / 'system-display.json').write_text(json.dumps({'schema': 'drybox-system-display-v1', 'parts': parts},
                                                        separators=(',', ':')))


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--output', type=Path, default=REPO / 'build/filament-drybox/current')
    ap.add_argument('--spool', type=Path, help="directory with Bambu's printable spool STLs (private) for spool_fit.py")
    ap.add_argument('--reference-build', type=Path,
                    help='holder build directory to compare part geometry against (e.g. the one a print was sliced from)')
    ap.add_argument('--spool-python', type=Path, default=Path(sys.executable),
                    help='interpreter with manifold3d for spool_fit.py (default: this one; requirements.txt installs both)')
    a = ap.parse_args()
    out = a.output.resolve()
    out.mkdir(parents=True, exist_ok=True)
    old = json.loads((out / 'manifest.json').read_text()) if (out / 'manifest.json').exists() else {}
    previous = old.get('producers', {})

    def incomplete(producers, fit):
        # Written before and between steps: a failed run never leaves an earlier complete pass in place,
        # while the producer and spool-fit records stay available for reuse.
        (out / 'manifest.json').write_text(json.dumps({'schema': 'drybox-current-build-v1', 'incomplete': True,
                                                       'producers': producers, 'spool_fit': fit}, indent=2) + '\n')
    incomplete(previous, old.get('spool_fit'))
    producers = run_producers(out, previous)
    incomplete(producers, old.get('spool_fit'))
    fit = spool_fit(out, producers['holder']['outputs_sha256'], a.spool, a.spool_python, old.get('spool_fit'))
    incomplete(producers, fit)
    old_checks = json.loads((out / 'system-checks.json').read_text()) if (out / 'system-checks.json').exists() else {}
    checks, placed, o, clip_placed = system_checks(out, a.reference_build, old_checks, producers['holder']['outputs_sha256'])
    display(placed, o, clip_placed, out)
    (out / 'system-checks.json').write_text(json.dumps(checks, indent=2) + '\n')
    inventory = json.loads((HERE / 'drybox.json').read_text())
    for p in inventory['parts']:
        f = out / p['output']
        if not f.exists():
            raise SystemExit(f"inventory part {p['id']}: {f} missing")
        p['output_sha256'] = sha(f)
    git = subprocess.run(['git', '-C', str(REPO), 'rev-parse', 'HEAD'], capture_output=True, text=True).stdout.strip()
    dirty = subprocess.run(['git', '-C', str(REPO), 'status', '--porcelain', '--', 'filament-drybox'],
                           capture_output=True, text=True).stdout.strip()
    manifest = {
        'schema': 'drybox-current-build-v1', 'scope': 'Native CAD and interface checks only; not a release or fabrication approval.',
        'git_head': git, 'working_tree_changes_under_filament_drybox': bool(dirty),
        'environment': {'python': platform.python_version(), 'cadquery': cq.__version__},
        'sources_sha256': {f: sha(HERE / f) for f in sorted({s for p in PRODUCERS.values() for s in p['sources']}
                                                             | {'drybox.py', 'drybox.json', 'spool_fit.py'})},
        'producers': producers, 'spool_fit': fit, 'inventory': inventory,
        'outputs_sha256': {'system-checks.json': sha(out / 'system-checks.json'), 'system-display.json': sha(out / 'system-display.json')},
        'checks': {'holder': {'pass': json.loads((out / 'holder' / 'stand-build.json').read_text())['checks']['pass']},
                   'system': {'pass': checks['pass'], 'failures': checks['failures']}}}
    (out / 'manifest.json').write_text(json.dumps(manifest, indent=2) + '\n')
    print(json.dumps({'output': str(out), 'reused': {n: r['reused'] for n, r in producers.items()},
                      'pass': checks['pass'], 'failures': checks['failures']}, indent=2))
    if not checks['pass']:
        raise SystemExit(1)


if __name__ == '__main__':
    main()
