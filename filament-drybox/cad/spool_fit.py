#!/usr/bin/env python3
"""Spool fit of the spindle and collar against Bambu's published printable spool model.

Inputs: a cad/stand.py build directory (stand-display.json) and a directory with
bambulab_spool_narrow.stl / bambulab_spool_wide.stl (Bambu's printable reference
spool; download it separately and keep it out of this repository). The printable
model is a stand-in: molded Bambu spool dimensions are unmeasured.

Checks, using display tessellations (0.1 mm chord tolerance):
- seated: spool overlap with spindle and collar lies only in the bore-end chamfer
  contact bands, and every other surface keeps a gap;
- installation: the spool slides on from the refill (-X) end over the bare spindle,
  and the collar runs in from the left with the spool seated on the drive cone;
- the seated spool clears the frame and lifts out with the spindle.
"""
from pathlib import Path
import argparse, json, struct
import numpy as np
import manifold3d as m3

AXIS_Y = 104.0


def manifold(vertices, triangles):
    # Weld coincident vertices (per-face tessellations repeat their shared edge points).
    v, inv = np.unique(np.round(np.asarray(vertices, float), 4), axis=0, return_inverse=True)
    f = inv.reshape(-1)[np.asarray(triangles)]
    m = m3.Manifold(m3.Mesh(vert_properties=np.asarray(v, np.float32), tri_verts=np.asarray(f, np.uint32)))
    if m.status() != m3.Error.NoError:
        raise ValueError(f'mesh is not a closed manifold: {m.status()}')
    return m


def stl(path):
    b = path.read_bytes(); n = struct.unpack_from('<I', b, 80)[0]
    t = np.frombuffer(b, dtype=np.dtype([('n', '<3f4'), ('v', '<9f4'), ('a', '<u2')]), count=n, offset=84)['v'].reshape(-1, 3)
    return manifold(t + [0, AXIS_Y, 0], np.arange(len(t)).reshape(-1, 3))


def x_band(x0, x1):
    return m3.Manifold.cube([x1 - x0, 400, 400]).translate([x0, AXIS_Y - 200, -200])


def turned(m, travel, pitch, lefthand):
    """Collar moved `travel` along the thread (+ inboard) with the matching helix rotation."""
    angle = 360 * travel / pitch * (-1 if lefthand else 1)
    return m.translate([0, -AXIS_Y, 0]).rotate([angle, 0, 0]).translate([travel, AXIS_Y, 0])


def extent(m):
    if m.is_empty():
        return None
    mesh = m.to_mesh(); v = np.asarray(mesh.vert_properties)[:, :3]
    r = np.hypot(v[:, 1] - AXIS_Y, v[:, 2])
    return {'x': [round(float(v[:, 0].min()), 3), round(float(v[:, 0].max()), 3)], 'r': [round(float(r.min()), 3), round(float(r.max()), 3)]}


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--native', type=Path, required=True, help='cad/stand.py output directory')
    ap.add_argument('--spool', type=Path, required=True, help='directory with bambulab_spool_narrow.stl / _wide.stl')
    ap.add_argument('--output', type=Path, required=True, help='JSON result file')
    a = ap.parse_args()
    build = json.loads((a.native / 'stand-build.json').read_text())
    display = json.loads((a.native / 'stand-display.json').read_text())
    if not build['checks']['pass']:
        raise ValueError('Native holder checks failed: ' + build['checks']['summary'])
    c = build['config']; sp = c['spindle']; t = sp['thread']; lefthand = t['hand'] == 'left'
    part = {n: manifold(display['components'][n]['vertices'], display['components'][n]['triangles']) for n in ['spindle', 'collar', 'fixed-stand', 'left-carrier', 'right-carrier']}
    spool = stl(a.spool / 'bambulab_spool_narrow.stl') + stl(a.spool / 'bambulab_spool_wide.stl')
    spindle, collar = part['spindle'], part['collar']
    # Contact bands: the cone length outboard of the bore cylinder, on each side.
    band = (sp['seat_start_x'] - 0.1, sp['ring_x'][1] + 0.1)
    contact = x_band(*band) + x_band(-band[1], -band[0])
    free = lambda m: m - contact
    tol = 0.05  # display tessellation chord error allowance for coincident seat surfaces
    out = {'scope': 'Fit against the printable reference spool only; molded spool dimensions, clamp force and twist-lock loads are unverified.',
           'tessellation_tolerance_mm': 0.1, 'seated': {}, 'install_spool_slide_mm': {}, 'install_collar_run_in_mm': {}, 'lift_spool_frame_overlap_mm3': {}, 'failures': []}
    for name, m in [('spindle', spindle), ('collar', collar)]:
        hit = spool ^ m
        out['seated'][name] = {
            'overlap_mm3': round(hit.volume(), 3), 'overlap_extent': extent(hit),
            'gap_outside_contact_bands_mm': round(spool.min_gap(free(m), 10), 3)}
        e = extent(hit)
        if e and (min(abs(e['x'][0]), abs(e['x'][1])) < band[0] - tol or e['r'][0] < sp['seat_bore_radius'] - tol):
            out['failures'].append(f'{name} overlaps the spool outside the chamfer contact band')
        if out['seated'][name]['gap_outside_contact_bands_mm'] <= 0:
            out['failures'].append(f'{name} touches the spool outside the chamfer contact band')
    out['seated']['frame_gap_mm'] = round(spool.min_gap(part['fixed-stand'], 10), 3)
    fl = build['checks']['axial_float_mm']['total']
    out['seated']['frame_gap_after_axial_float_mm'] = round(min(spool.translate([d, 0, 0]).min_gap(part['fixed-stand'], 10) for d in (-fl, fl)), 3)
    out['seated']['carrier_gap_mm'] = round(min(spool.min_gap(part[n], 10) for n in ['left-carrier', 'right-carrier']), 3)
    if min(out['seated']['frame_gap_after_axial_float_mm'], out['seated']['carrier_gap_mm']) <= 0:
        out['failures'].append('Seated spool touches the frame or a carrier')
    # The spool approaches from -X over the bare spindle and stops on the drive cone.
    for d in [0.5, 1, 2, 5, 10, 20, 40, 70]:
        moved = spool.translate([-d, 0, 0])
        out['install_spool_slide_mm'][str(d)] = {'overlap_mm3': round((moved ^ spindle).volume(), 4), 'gap_mm': round(moved.min_gap(spindle, 10), 3)}
        if out['install_spool_slide_mm'][str(d)]['overlap_mm3'] > 1e-4:
            out['failures'].append(f'Spool collides with the spindle {d} mm before seating')
    # The collar runs in from the refill side with the spool already seated on the drive cone.
    for d in [0.5, 1, 2, 4, 8, 12, 20]:
        moved = turned(collar, -d, t['pitch'], lefthand)
        out['install_collar_run_in_mm'][str(d)] = {'spool_overlap_mm3': round((moved ^ spool).volume(), 4), 'spool_gap_mm': round(moved.min_gap(spool, 10), 3)}
        if out['install_collar_run_in_mm'][str(d)]['spool_overlap_mm3'] > 1e-4:
            out['failures'].append(f'Collar collides with the spool {d} mm before seating')
    for lift in [0.2, 1, 5, 20, 40, 80, 120]:
        out['lift_spool_frame_overlap_mm3'][str(lift)] = round((spool.translate([0, lift, 0]) ^ part['fixed-stand']).volume(), 4)
        if out['lift_spool_frame_overlap_mm3'][str(lift)] > 1e-4:
            out['failures'].append(f'Spool collides with the frame at lift {lift} mm')
    travel = build['checks']['collar_travel_mm']
    box = spool.bounding_box(); width = box[3] - box[0]
    out['clamp_range'] = {
        'reference_hub_width_mm': round(width, 3),
        'condition': 'With 45-degree bore-end chamfers, the collar seats when 2*d(bore radius + chamfer) - d(hub width) lies within [-outboard, +inboard] travel, relative to the reference spool. Joint condition, not independent ranges.',
        'collar_travel_mm': travel,
        'hub_width_mm_at_reference_bore': [round(width - travel['inboard'], 2), round(width + travel['outboard'], 2)]}
    out['pass'] = not out['failures']
    a.output.parent.mkdir(parents=True, exist_ok=True)
    a.output.write_text(json.dumps(out, indent=2) + '\n')
    print(json.dumps(out, indent=2))
    if not out['pass']:
        raise SystemExit(1)


if __name__ == '__main__':
    main()
