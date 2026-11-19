#!/usr/bin/env python3
"""Offline print preparation for the current holder and outside drive.

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
import zipfile

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
OUTSIDE_PARTS = (
    ('mount-x', 'wall-face-down', 'Y', -90, (40, 30)),
    ('wheel', 'wall-face-down', 'Y', -90, (190, 30)),
    ('hub-retainer', 'broad-face-down', 'Y', -90, (195, 175)),
    ('axle-clip', 'broad-face-down', 'Y', -90, (240, 175)),
)
OVERNIGHT_PARTS = (
    ('mount-x', 'wall-face-down', 'Y', -90, (25, 25)),
    ('wheel', 'wall-face-down', 'Y', -90, (180, 25)),
    ('drive-rotor', 'wall-face-down', 'Y', 90, (185, 180)),
    ('hub-retainer', 'broad-face-down', 'Y', -90, (35, 195)),
    ('axle-clip', 'broad-face-down', 'Y', -90, (85, 195)),
    ('retaining-clip', 'broad-face-down', 'Y', 90, (115, 195)),
)
HOLDER_PARTS = (
    ('fixed-stand', 'base-down', 'X', 90, (45, 50)),
    ('drive-rotor', 'wall-face-down', 'Y', 90, (175, 50)),
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


def orient(native, output, scope='spindle', holder_native=None):
    parts, objects = [], []
    recipes = {'spindle': PARTS, 'holder': HOLDER_PARTS, 'outside': OUTSIDE_PARTS, 'overnight': OVERNIGHT_PARTS,
               'remaining': tuple(p for p in HOLDER_PARTS if p[0] not in ('spindle', 'collar'))}
    for name, pose, axis, angle, placement in recipes[scope]:
        source_dir = holder_native if scope == 'overnight' and name in ('drive-rotor', 'retaining-clip') else native
        source = source_dir / (name + '.step')
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


def retain_process_overrides(project, overrides):
    """Keep approved deltas visible when the GUI resolves the factory preset."""
    with zipfile.ZipFile(project) as archive:
        entries = [(info, archive.read(info.filename)) for info in archive.infolist()]
    config_name = 'Metadata/project_settings.config'
    config = json.loads(next(data for info, data in entries if info.filename == config_name))
    deltas = config['different_settings_to_system']
    deltas[0] = ';'.join(sorted(set(filter(None, deltas[0].split(';'))) | set(overrides)))
    config['different_settings_to_system'] = deltas
    temporary = project.with_suffix('.packaged.3mf')
    with zipfile.ZipFile(temporary, 'w') as archive:
        for info, data in entries:
            archive.writestr(info, json.dumps(config, indent=2).encode() if info.filename == config_name else data)
    temporary.replace(project)
    return {'process_delta_keys': deltas[0].split(';'),
            'reason': 'Studio GUI reverts unlisted deltas when resolving a named factory preset.'}


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--engineering-root', type=Path, required=True, help='Castle Harker checkout (shared manufacturing tools)')
    ap.add_argument('--native-input', type=Path, required=True, help='cad/stand.py output directory')
    ap.add_argument('--output', type=Path, required=True)
    ap.add_argument('--bambu', type=Path, required=True, help='Bambu Studio executable')
    ap.add_argument('--scope', choices=['spindle', 'holder', 'remaining', 'outside', 'overnight'], default='spindle',
                    help='Spindle pair, complete holder, holder excluding the pair, or four outside-drive parts')
    ap.add_argument('--holder-native', type=Path,
                    help='Checked holder build supplying the shared configuration when --scope outside')
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
    outside_scope = a.scope in ('outside', 'overnight')
    if outside_scope and not a.holder_native:
        raise ValueError('Outside/overnight scope requires --holder-native with the matching checked holder build')
    build = (a.holder_native.resolve() if outside_scope else native) / 'stand-build.json'
    build_hash = sha(build)
    holder_build = json.loads(build.read_text())
    if not holder_build['checks']['pass']:
        raise ValueError('Holder native checks failed')
    config = holder_build['config']
    outside_checks = None
    if outside_scope:
        outside_checks = native / 'checks.json'
        if not json.loads(outside_checks.read_text())['pass']:
            raise ValueError('Outside drive native checks failed')
        outside_checks_hash = sha(outside_checks)
    parts, objects = orient(native, output, a.scope, a.holder_native.resolve() if a.holder_native else None)
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
                               edit_project=lambda project: retain_process_overrides(project, overrides),
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
        if outside_scope:
            for name in ('hub-retainer', 'axle-clip'):
                if reports[job_name]['checks'][name]['support_segments']:
                    raise ValueError(f'{name}: flat retainer unexpectedly needs supports')
    if sha(build) != build_hash or any(sha(Path(p['source_step'])) != p['source_step_sha256'] for p in parts):
        raise ValueError('Native input changed during preparation')
    if outside_checks and sha(outside_checks) != outside_checks_hash:
        raise ValueError('Outside drive checks changed during preparation')
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
