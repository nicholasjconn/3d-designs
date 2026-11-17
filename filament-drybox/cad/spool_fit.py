#!/usr/bin/env python3
"""Spool fit of the spindle and collar against the measured spool envelope.

Inputs: a cad/stand.py build directory (stand-display.json, stand-build.json) and a
directory with bambulab_spool_narrow.stl / bambulab_spool_wide.stl (Bambu's printable
reference spool; download it separately and keep it out of this repository).

The spool is a solid of revolution from stand.json envelopes.measured_spool: the
measured overall width A and hub-face width D, with the bore, the radius where the
flange face begins and the rim taken from the reference model's radial profile
(assumed: they cannot be measured). The reference model itself has flush 67.4 mm hub
faces; it is only read for that radial profile and recorded separately.

Checks, using display tessellations (0.1 mm chord tolerance):
- seated: both flat stop faces bear on the hub faces (moving the spool 0.1 mm into
  either face collides) and nothing else touches it;
- installation: the spool slides on from the refill (-X) end over the bare spindle,
  and the collar runs in from the left with the spool on the drive stop;
- the seated spool clears the frame and carriers through the axial float, and lifts
  out with the spindle;
- the collar travel clamps hub widths around the measured one.
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


def turned(m, travel, pitch, lefthand):
    """Collar moved `travel` along the thread (+ inboard) with the matching helix rotation."""
    angle = 360 * travel / pitch * (-1 if lefthand else 1)
    return m.translate([0, -AXIS_Y, 0]).rotate([angle, 0, 0]).translate([travel, AXIS_Y, 0])


def envelope(ms):
    """Measured-envelope spool about the axle: hub between the hub faces, flanges and filament out to the rim."""
    rb, ro, rr = ms['assumed_bore_diameter'] / 2, ms['assumed_recess_opening_diameter'] / 2, ms['assumed_outer_diameter'] / 2
    d, a = ms['hub_face_width'] / 2, ms['overall_width'] / 2
    section = m3.CrossSection([[(rb, -d), (ro, -d), (ro, -a), (rr, -a), (rr, a), (ro, a), (ro, d), (rb, d)]])
    return m3.Manifold.revolve(section, 360).rotate([0, 90, 0]).translate([0, AXIS_Y, 0])


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
    c = build['config']; sp = c['spindle']; t = sp['thread']; lefthand = t['hand'] == 'left'; ms = c['envelopes']['measured_spool']
    part = {n: manifold(display['components'][n]['vertices'], display['components'][n]['triangles']) for n in ['spindle', 'collar', 'fixed-stand', 'left-carrier', 'right-carrier']}
    spindle, collar = part['spindle'], part['collar']
    spool = envelope(ms)
    tol = 0.05  # display tessellation allowance for the coincident stop-face contacts
    out = {'scope': 'Measured spool envelope: A and D are measured; bore, flange-face radius and rim are assumed from the reference model radial profile. First fit, not qualification.',
           'tessellation_tolerance_mm': 0.1, 'spool_envelope_mm': {k: ms[k] for k in ['overall_width', 'hub_face_width', 'assumed_bore_diameter', 'assumed_recess_opening_diameter', 'assumed_outer_diameter']},
           'seated': {}, 'install_spool_slide_mm': {}, 'install_collar_run_in_mm': {}, 'lift_spool_frame_overlap_mm3': {}, 'failures': []}
    # Reference model: recorded separately; only its radial profile informs the assumed envelope.
    ref = stl(a.spool / 'bambulab_spool_narrow.stl') + stl(a.spool / 'bambulab_spool_wide.stl')
    v = np.asarray(ref.to_mesh().vert_properties)[:, :3]; r = np.hypot(v[:, 1] - AXIS_Y, v[:, 2])
    bb = ref.bounding_box(); lip = float(r.min())
    face_level = (np.abs(v[:, 0]) > bb[3] - 2.2) & (r > lip + 3)
    out['reference_model'] = {'flush_hub_width_mm': round(bb[3] - bb[0], 3), 'bore_diameter_mm': round(2 * lip, 2),
                              'flange_face_starts_diameter_mm': round(2 * float(r[face_level].min()), 1),
                              'note': 'Printable reference only; its flush hub faces are not the measured spool and set no datum.'}
    if out['reference_model']['flange_face_starts_diameter_mm'] < 2 * sp['stop_outer_radius'] + 2:
        out['failures'].append('Stop face OD does not clear the reference recess opening')
    for name, m in [('spindle', spindle), ('collar', collar)]:
        side = 1 if name == 'spindle' else -1
        out['seated'][name] = {'overlap_mm3': round((spool ^ m).volume(), 4),
                               'pressed_0.1mm_overlap_mm3': round((spool.translate([side * 0.1, 0, 0]) ^ m).volume(), 3)}
        if out['seated'][name]['overlap_mm3'] > tol:
            out['failures'].append(f'{name} overlaps the seated spool')
        if out['seated'][name]['pressed_0.1mm_overlap_mm3'] < 1:
            out['failures'].append(f'{name} stop face does not bear on the hub face')
    out['seated']['frame_gap_mm'] = round(spool.min_gap(part['fixed-stand'], 10), 3)
    fl = build['checks']['axial_float_mm']['total']
    out['seated']['frame_gap_after_axial_float_mm'] = round(min(spool.translate([d, 0, 0]).min_gap(part['fixed-stand'], 10) for d in (-fl, fl)), 3)
    out['seated']['carrier_gap_mm'] = round(min(spool.min_gap(part[n], 10) for n in ['left-carrier', 'right-carrier']), 3)
    if min(out['seated']['frame_gap_after_axial_float_mm'], out['seated']['carrier_gap_mm']) < sp['min_running_gap']:
        out['failures'].append('Seated spool closer than min_running_gap to the frame or a carrier within the axial float')
    # The spool approaches from -X over the bare spindle and stops on the drive stop face.
    for d in [0.5, 1, 2, 5, 10, 20, 40, 70]:
        moved = spool.translate([-d, 0, 0])
        out['install_spool_slide_mm'][str(d)] = {'overlap_mm3': round((moved ^ spindle).volume(), 4), 'gap_mm': round(moved.min_gap(spindle, 10), 3)}
        if out['install_spool_slide_mm'][str(d)]['overlap_mm3'] > 1e-4:
            out['failures'].append(f'Spool collides with the spindle {d} mm before seating')
    # The collar runs in from the refill side with the spool already on the drive stop.
    for d in [0.5, 1, 2, 4, 8, 12, 20]:
        moved = turned(collar, -d, t['pitch'], lefthand)
        out['install_collar_run_in_mm'][str(d)] = {'spool_overlap_mm3': round((moved ^ spool).volume(), 4), 'spool_gap_mm': round(moved.min_gap(spool, 10), 3)}
        if out['install_collar_run_in_mm'][str(d)]['spool_overlap_mm3'] > 1e-4:
            out['failures'].append(f'Collar collides with the spool {d} mm before seating')
    for lift in [0.2, 1, 5, 20, 40, 80, 120]:
        out['lift_spool_frame_overlap_mm3'][str(lift)] = round((spool.translate([0, lift, 0]) ^ part['fixed-stand']).volume(), 4)
        if out['lift_spool_frame_overlap_mm3'][str(lift)] > 1e-4:
            out['failures'].append(f'Spool collides with the frame at lift {lift} mm')
    travel = build['checks']['collar_travel_mm']; face = sp['ring_x'][0] + sp['pilot_length']
    out['clamp_range'] = {'measured_hub_face_width_mm': ms['hub_face_width'], 'collar_travel_mm': travel,
                          'clamped_hub_width_mm': [round(2 * face - travel['inboard'], 2), round(2 * face + travel['outboard'], 2)],
                          'condition': 'Flat faces: the clamp depends on hub-face width only; collar face at -(D - 29.8).'}
    out['pass'] = not out['failures']
    a.output.parent.mkdir(parents=True, exist_ok=True)
    a.output.write_text(json.dumps(out, indent=2) + '\n')
    print(json.dumps(out, indent=2))
    if not out['pass']:
        raise SystemExit(1)


if __name__ == '__main__':
    main()
