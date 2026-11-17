#!/usr/bin/env python3
"""Offline print preparation for the spindle pair or complete current holder.

Inputs: a checked cad/stand.py build directory (part STEP files and stand-build.json),
the Castle Harker checkout providing the shared manufacturing tools, and the
installed Bambu Studio. Default scope: spindle drive end down and collar outer
ring face down. --scope holder includes the frame base-down, both carriers outer
face down, disc cover-down and clip flat, on the same plate. Exports exact meshes and slices with the factory
H2D 0.4 / Bambu PLA Basic / Textured PEI / 0.20mm Standard presets plus the listed
support overrides. It never controls a printer, approves settings or authorizes
fabrication. Existing output is rejected; keep prior evidence in its own directory.
"""
from pathlib import Path
import argparse
import json
import sys

import cadquery as cq

from stand_print import bounds, mesh_integrity, sha
from stand_prepare import analyze, placement_proof, write

STUDIO = '02.09.01.70'
# Native axes: X axle, Y up, Z fore/aft. Both parts print with the axle vertical.
#   spindle: rotate +90 deg about Y, native X -> bed -Z (drive journal end on the bed);
#   collar:  rotate -90 deg about Y, native X -> bed +Z (outboard stop-ring face on the bed).
PARTS = (
    ('spindle', 'drive-end-down', 'Y', 90, (105, 120)),
    ('collar', 'stop-face-down', 'Y', -90, (195, 120)),
)
HOLDER_PARTS = (
    ('fixed-stand', 'base-down', 'X', 90, (45, 50)),
    ('drive-rotor', 'magnet-cover-down', 'Y', 90, (175, 50)),
    ('spindle', 'drive-end-down', 'Y', 90, (175, 165)),
    ('collar', 'stop-face-down', 'Y', -90, (250, 165)),
    ('left-carrier', 'outboard-face-down', 'Y', -90, (175, 245)),
    ('right-carrier', 'outboard-face-down', 'Y', 90, (220, 245)),
    ('retaining-clip', 'broad-face-down', 'Y', 90, (265, 245)),
)
ROTATION = {('X', 90): ((1, 0, 0), (0, 0, -1), (0, 1, 0)),
            ('Y', 90): ((0, 0, 1), (0, 1, 0), (-1, 0, 0)),
            ('Y', -90): ((0, 0, -1), (0, 1, 0), (1, 0, 0))}
VARIANTS = {
    # Previously approved offline baseline: support on, critical regions only.
    'critical': {'enable_support': '1', 'support_critical_regions_only': '1'},
    # The founder printed the disc and clip with Studio's tree slim support style.
    'critical-tree-slim': {'enable_support': '1', 'support_critical_regions_only': '1', 'support_style': 'tree_slim'},
}


def orient(native, output, scope='spindle'):
    parts, objects = [], []
    for name, pose, axis, angle, placement in HOLDER_PARTS if scope == 'holder' else PARTS:
        source = native / (name + '.step')
        shape = cq.importers.importStep(str(source)).val()
        if not shape.isValid() or len(shape.Solids()) != 1:
            raise ValueError(f'{source}: expected one valid solid')
        direction = (1, 0, 0) if axis == 'X' else (0, 1, 0)
        shape = shape.rotate((0, 0, 0), direction, angle)
        shift = [-v for v in bounds(shape)[0]]
        shape = shape.translate(tuple(shift))
        mesh = output / f'{name}-{pose}.stl'
        if not shape.exportStl(str(mesh), tolerance=.02, angularTolerance=.1, relative=False):
            raise RuntimeError('Fabrication mesh export failed: ' + str(mesh))
        cq.exporters.export(shape, str(output / f'{name}-{pose}.step'))
        box = bounds(shape)
        matrix = ROTATION[(axis, angle)]
        transform = [list(matrix[i]) + [shift[i] + (placement[i] if i < 2 else 0)] for i in range(3)] + [[0, 0, 0, 1]]
        parts.append({'id': name, 'orientation': pose, 'source_step': str(source), 'source_step_sha256': sha(source),
                      'stl': str(mesh), 'stl_sha256': sha(mesh), 'rotation_axis': axis, 'rotation_degrees': angle,
                      'minimum_corner_translation_mm': shift, 'placement_xy_mm': placement, 'native_to_bed': transform,
                      'bbox_bed_mm': {'min': [box[0][i] + (placement[i] if i < 2 else 0) for i in range(3)],
                                      'max': [box[1][i] + (placement[i] if i < 2 else 0) for i in range(3)]}})
        objects.append({'path': str(mesh), 'count': 1, 'filaments': [1], 'pos_x': [placement[0]], 'pos_y': [placement[1]],
                        'pos_z': [0], 'print_params': {}})
    integrity = {p['id']: mesh_integrity(Path(p['stl'])) for p in parts}
    write(output / 'mesh-integrity.json', integrity)
    if any(not r['passed'] for r in integrity.values()):
        raise ValueError('Fabrication mesh integrity failed; see mesh-integrity.json')
    return parts, objects


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--engineering-root', type=Path, required=True, help='Castle Harker checkout (shared manufacturing tools)')
    ap.add_argument('--native-input', type=Path, required=True, help='cad/stand.py output directory')
    ap.add_argument('--output', type=Path, required=True)
    ap.add_argument('--bambu', type=Path, required=True, help='Bambu Studio executable')
    ap.add_argument('--scope', choices=['spindle', 'holder'], default='spindle',
                    help='Spindle/collar pair, or all seven current holder parts on one plate')
    ap.add_argument('--variant', action='append', choices=list(VARIANTS), help='slice only these variants (default: all)')
    a = ap.parse_args()
    sys.path.insert(0, str(a.engineering_root.resolve()))
    from shared.manufacturing import make_project
    from systems.test_fixture.manufacturing.factory import load_factory, check_factory_settings
    output, native = a.output.resolve(), a.native_input.resolve()
    variants = a.variant or list(VARIANTS)
    if output.exists():
        raise FileExistsError(f'Retain existing evidence and choose a new --output: {output}')
    output.mkdir(parents=True)
    build = native / 'stand-build.json'
    build_hash = sha(build)
    config = json.loads(build.read_text())['config']
    parts, objects = orient(native, output, a.scope)
    write(output / 'plate-parts.json', parts)
    recipe = {'status': 'Offline proposed print configuration; fabrication not approved', 'studio_version': STUDIO,
              'presets': {'machine': 'Bambu Lab H2D 0.4 nozzle', 'process': '0.20mm Standard @BBL H2D',
                          'filament': 'Bambu PLA Basic @BBL H2D'},
              'scope': a.scope, 'plate': 'Textured PEI Plate', 'filament_map': '2', 'variants': {v: VARIANTS[v] for v in variants},
              'mesh_export': {'absolute_linear_tolerance_mm': .02, 'angular_tolerance_radians': .1}}
    write(output / 'spindle-print.json', recipe)
    profiles, factory = load_factory(a.bambu, recipe, output / 'factory')
    reports = {}
    for job_name, overrides in ((v, VARIANTS[v]) for v in variants):
        process = dict(profiles['process'], **overrides)
        job = output / job_name
        receipt = make_project(a.bambu, job, job_name, profiles['machine'], process, [profiles['filament']], objects,
                               filament_map='2', slice_from_project=True,
                               source_inputs={'parts': parts, 'process_overrides': overrides,
                                              'scope': 'Offline proposal only; no fabrication approval'})
        settings = json.loads((job / 'out/settings.json').read_text())
        check_factory_settings(settings, dict(profiles, process=process), enable_support=True)
        for key, value in overrides.items():
            if settings.get(key) != value:
                raise ValueError(f'{job_name}: Studio did not retain {key}={value} (got {settings.get(key)!r})')
        write(job / 'receipt.json', receipt)
        # stand_prepare.analyze reads <dir>/<job>/out and writes its reports into <dir>; keep each variant's reports apart.
        variant = output / ('analysis-' + job_name)
        variant.mkdir()
        (variant / job_name).symlink_to(Path('..') / job_name)
        reports[job_name] = analyze(variant, [dict(p) for p in parts], config, job_name=job_name,
                                    guard_support_required=False)
    if sha(build) != build_hash or any(sha(Path(p['source_step'])) != p['source_step_sha256'] for p in parts):
        raise ValueError('Native input changed during preparation')
    retained = [p for p in output.rglob('*') if p.is_file() and not any(q.is_symlink() for q in p.relative_to(output).parents if q != Path('.') and (output / q).is_symlink()) and p.suffix in ('.json', '.stl', '.step', '.3mf', '.gcode')
                and '/cache/' not in str(p) and '/tmp/' not in str(p) and '/upstream/' not in str(p)]
    write(output / 'manifest.json', {
        'scope': 'Offline print preparation only; no printer actions or fabrication approval.',
        'native_build': str(build), 'native_build_sha256': build_hash,
        'producer_sha256': {n: sha(Path(__file__).with_name(n)) for n in ('spindle_print.py', 'stand_prepare.py', 'stand_print.py')},
        'factory': factory,
        'artifacts': {str(p.relative_to(output)): {'sha256': sha(p), 'bytes': p.stat().st_size} for p in sorted(retained)}})
    print(json.dumps({k: {f: r[f] for f in ('estimate_seconds', 'slicer_total_g', 'useful_part_g', 'removed_g', 'warnings')}
                      for k, r in reports.items()}, indent=2, default=float))


if __name__ == '__main__':
    main()
