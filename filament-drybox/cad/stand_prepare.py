#!/usr/bin/env python3
"""Prepare and check an offline four-part holder print candidate.

Requires sibling stand_print.py, native stand STEP exports + stand-build.json,
and the Castle Harker engineering Python environment. Uses installed factory
Bambu presets with only support enabled and critical-regions-only enabled.
It never controls a printer, approves settings or authorizes fabrication.
Existing output is rejected; retain prior outputs under distinct directories.
"""
from pathlib import Path
import argparse
import hashlib
import json
import math
import bisect
import sys
import xml.etree.ElementTree as ET
import zipfile

from stand_print import prepare


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def write(path, data, *, compact=False):
    def scalar(value):
        return value.item()
    path.write_text(json.dumps(data, indent=None if compact else 2, default=scalar) + '\n')


def placement_proof(project, parts, output):
    """Check actual 3MF vertices against the declared fabrication STL placement."""
    import struct
    import numpy as np
    from scipy.spatial import cKDTree
    namespace = {'m': 'http://schemas.microsoft.com/3dmanufacturing/core/2015/02'}
    rows = []
    with zipfile.ZipFile(project) as archive:
        model = ET.fromstring(archive.read('3D/3dmodel.model'))
        objects = {o.attrib['id']: o for o in model.findall('m:resources/m:object', namespace)}
        items = list(model.find('m:build', namespace))
        if len(items) != len(parts):
            raise ValueError('3MF object count differs from the four-part recipe')
        for part, item in zip(parts, items):
            if item.attrib.get('transform', '1 0 0 0 1 0 0 0 1 0 0 0') != '1 0 0 0 1 0 0 0 1 0 0 0':
                raise ValueError('Unexpected 3MF build transform; placement proof must be extended')
            component = objects[item.attrib['objectid']].find('m:components/m:component', namespace)
            path = next(v for k, v in component.attrib.items() if k.endswith('path')).lstrip('/')
            mesh = ET.fromstring(archive.read(path)).find('m:resources/m:object/m:mesh', namespace)
            vertices = np.array([[float(v.attrib[a]) for a in ('x', 'y', 'z')]
                                 for v in mesh.find('m:vertices', namespace)])
            transform = np.array(list(map(float, component.attrib['transform'].split())))
            world = vertices @ transform[:9].reshape(3, 3) + transform[9:]
            data = Path(part['stl']).read_bytes()
            count = struct.unpack_from('<I', data, 80)[0]
            stl = np.array([struct.unpack_from('<12fH', data, 84 + i*50)[3:12]
                            for i in range(count)]).reshape(-1, 3)
            stl[:, :2] += part['placement_xy_mm']
            distance = float(cKDTree(stl).query(world)[0].max())
            if distance > 1e-5:
                raise ValueError(f"{part['id']}: 3MF placement differs from declared STL")
            rows.append({'part': part['id'], 'placement_verified': True,
                         'maximum_3mf_to_placed_stl_vertex_distance_mm': distance,
                         '3mf_world_bounds_mm': [world.min(axis=0).tolist(), world.max(axis=0).tolist()]})
    write(output / 'placement-proof.json', rows)


def analyze(output, parts, config, *, job_name='four-part-critical', guard_support_required=True):
    import numpy as np
    from shared.manufacturing import read_paths
    from systems.test_fixture.analysis.print_geometry import slice_mass_properties
    job = output / job_name
    gcode = job / 'out/plate_1.gcode'
    project = job / (job_name + '.3mf')
    paths = read_paths(gcode, arc_step_mm=.2)
    ns = {'m': 'http://schemas.microsoft.com/3dmanufacturing/core/2015/02'}
    with zipfile.ZipFile(project) as archive:
        model = ET.fromstring(archive.read('3D/3dmodel.model'))
        settings = ET.fromstring(archive.read('Metadata/model_settings.config'))
    labels = {int(e.find("metadata[@key='identify_id']").attrib['value']):
              int(e.find("metadata[@key='object_id']").attrib['value'])
              for e in settings.findall('.//model_instance')}
    order = [int(e.attrib['objectid']) for e in model.find('m:build', ns)]
    label_parts = {label: parts[order.index(obj)]['id'] for label, obj in labels.items()}
    transitions = []
    for line, text in enumerate(gcode.read_text().splitlines(), 1):
        if text.startswith('; start printing object, unique label id: '):
            transitions.append((line, label_parts[int(text.rsplit(' ', 1)[-1])]))
    indices = [line for line, _ in transitions]
    single_object = len(parts) == 1 and len(order) == 1
    if not transitions and single_object:
        # Studio omits per-object labels for a one-object plate. The verified
        # project build order identifies its sole deposited model/support set.
        transitions = [(0, parts[0]['id'])]
        indices = [0]
    grouped = {p['id']: [] for p in parts}
    for road in paths:
        if road['feature'] == 'Custom':
            continue
        index = bisect.bisect_right(indices, road['line']) - 1
        if index < 0:
            raise ValueError('Deposited feature lacks an actual G-code object label')
        grouped[transitions[index][1]].append(road)
    axle, bearing, disc = config['axle'], config['bearings'], config['disc']
    axis_y = bearing['axis_y']
    checks, support_files, bore_envelopes = {}, {}, []
    for part in parts:
        name, xy = part['id'], part['placement_xy_mm']
        supports = [r for r in grouped[name] if r['feature'].startswith('Support')]
        segments = [[r['p'][0]-xy[0], r['p'][1]-xy[1], r['z'],
                     r['q'][0]-xy[0], r['q'][1]-xy[1], r['z'], r['width'],
                     int(r['feature'] == 'Support interface')] for r in supports]
        support_file = output / (name + '-supports.json')
        write(support_file, {'schema': 'actual-slicer-support-roads-v1',
              'source_gcode_sha256': sha(gcode), 'part': name, 'units': 'mm',
              'coordinates': 'Same oriented local XYZ as fabrication STL, Z up.',
              'plate_translation_mm': [*xy, 0], 'roles': ['Support', 'Support interface'],
              'columns': ['x1', 'y1', 'z1', 'x2', 'y2', 'z2', 'width', 'role_index'],
              'segments': segments}, compact=True)
        support_files[name] = support_file.name
        box = part['bbox_bed_mm']
        for road in grouped[name]:
            if road['feature'].startswith('Support') or road['feature'] == 'Brim':
                continue
            for point in (road['p'], road['q']):
                if (any(point[i] < box['min'][i]-.25 or point[i] > box['max'][i]+.25
                        for i in range(2)) or road['z'] < box['min'][2]-.25
                        or road['z'] > box['max'][2]+.25):
                    raise ValueError(f'{name}: model deposition outside declared envelope')
        transform = np.array(part['native_to_bed'])
        rotation, shift = transform[:3, :3], transform[:3, 3]
        native = [(r, rotation.T @ (np.array([*(np.mean([r['p'], r['q']], axis=0)), r['z']])-shift))
                  for r in supports]
        detail = {'model_paths_in_declared_envelope': True, 'support_segments': len(supports),
                  'support_native_bounds_mm': [np.min([v for _, v in native], axis=0).tolist(),
                                               np.max([v for _, v in native], axis=0).tolist()]
                  if supports else None}
        if name == 'rotating-core':
            bore_hits = []
            for i in range(axle['air_count']):
                angle = i*math.tau/axle['air_count']
                center = np.array([axis_y+axle['air_pitch']*math.cos(angle),
                                   axle['air_pitch']*math.sin(angle)])
                bore_hits.append(sum(abs(v[0]) < axle['barrel_end_x'] and
                                     np.linalg.norm(v[1:]-center) < axle['air_bore_radius']-.1
                                     for _, v in native))
                if not segments:
                    raise ValueError('Horizontal core lacks required support roads')
                roads = np.array(segments)
                local_shift = np.array(part['minimum_corner_translation_mm'])
                start = (roads[:, :3]-local_shift) @ rotation
                end = (roads[:, 3:6]-local_shift) @ rotation
                delta = end-start
                radial = start[:, 1:]-center
                direction = delta[:, 1:]
                denominator = (direction*direction).sum(axis=1)
                t = np.divide(-(radial*direction).sum(axis=1), denominator,
                              out=np.zeros(len(radial)), where=denominator > 1e-20)
                t = np.clip(t, 0, 1)
                nearest = start+delta*t[:, None]
                mask = abs(nearest[:, 0]) < axle['barrel_end_x']
                radius = np.linalg.norm(nearest[:, 1:]-center, axis=1)-roads[:, 6]/2
                clearance = float(radius[mask].min()-axle['air_bore_radius'])
                bore_envelopes.append({'bore': i,
                    'minimum_support_road_envelope_clearance_from_bore_void_mm': clearance,
                    'support_road_envelopes_intruding_nominal_bore': int((radius[mask] < axle['air_bore_radius']).sum())})
            sleeve_start, sleeve_end = axle['shoulder_end_x'], axle['thrust_face_x']
            def in_sleeve(v):
                x, radius = abs(v[0]), math.hypot(v[1]-axis_y, v[2])
                inner = axle['sleeve_inner_root_radius'] + (x-sleeve_start)/(sleeve_end-sleeve_start)*(axle['sleeve_inner_face_radius']-axle['sleeve_inner_root_radius'])
                return sleeve_start < x < sleeve_end and axle['journal_radius'] < radius < inner
            detail['support_centerlines_inside_air_bores'] = bore_hits
            detail['support_centerlines_inside_sleeve_reliefs'] = sum(in_sleeve(v) for _, v in native)
            if any(bore_hits) or detail['support_centerlines_inside_sleeve_reliefs']:
                raise ValueError('Support occupies core air passages or narrow sleeve reliefs')
        if name == 'fixed-stand':
            outer = config['envelopes']['spool_width']/2 + config['envelopes']['spool_side_clearance'] + config['frame_profile']['thickness']
            contact = disc['front_x']+config['envelopes']['inner_air']
            bottom = axis_y-config['drive_support']['outer_radius']
            detail['guard_bottom_support_interface_segments'] = sum(
                r['feature'] == 'Support interface' and outer < v[0] < contact+.1
                and abs(v[2]) < 9 and bottom-1 < v[1] < bottom+.01 for r, v in native)
            pilot = config['base']['expansion_pilots']
            center_y = (pilot['diameter']+2*pilot['wall'])/2
            detail['pilot_bore_support_segments'] = [sum(
                -outer < v[0] < -outer+pilot['depth'] and
                math.hypot(v[1]-center_y, v[2]-z) < pilot['diameter']/2-.1
                for _, v in native) for z in (-pilot['center_z'], pilot['center_z'])]
        if name == 'drive-rotor':
            detail['roof_support_interface_segments'] = sum(
                r['feature'] == 'Support interface' and disc['counterbore_back_x'] < v[0] < disc['counterbore_back_x']+.6
                and axle['journal_radius']+disc['key_radial_clearance']+.05 < math.hypot(v[1]-axis_y, v[2]) < disc['counterbore_radius']-.1
                for r, v in native)
        if name == 'fixed-stand' and ((guard_support_required and not detail['guard_bottom_support_interface_segments']) or any(detail['pilot_bore_support_segments'])):
            raise ValueError('Frame guard lacks underside support or support enters blind pilot bores')
        if name == 'drive-rotor' and not detail['roof_support_interface_segments']:
            raise ValueError('Disc counterbore roof lacks support interface roads')
        if name == 'retaining-clip' and supports:
            raise ValueError('Flat clip unexpectedly requires support')
        checks[name] = detail
    if any(b['support_road_envelopes_intruding_nominal_bore'] for b in bore_envelopes):
        raise ValueError('Support road envelope intrudes into a nominal core air bore')
    plate = json.loads((job / 'out/result.json').read_text())['sliced_plates'][0]
    # Float-rounded slicer bounds are appropriate for its own deposition ledger.
    for part, obj in zip(parts, plate['objects']):
        box = obj['bbox']
        part['bbox_bed_mm'] = {'min': [box['x'], box['y'], box['z']],
                              'max': [box['x']+box['width'], box['y']+box['depth'], box['z']+box['height']]}
    ledger = slice_mass_properties(gcode, parts)
    write(job / 'material-ledger.json', ledger)
    report = {'slicer_version': '02.09.01.70', 'warnings': plate['warning_message'],
              'estimate_seconds': plate['total_predication'],
              'slicer_total_g': plate['filaments'][0]['total_used_g'], 'checks': checks,
              'useful_part_g': {p['id']: p['mass_kg']*1000 for p in ledger['parts']},
              'removed_g': {k: v*1000 for k, v in ledger['removed_material_mass_by_feature_kg'].items()},
              'material_ledger': ledger['material_ledger'], 'support_files': support_files,
              'support_assignment': ('Sole object verified in 3MF build order; Studio omits object labels.'
                                     if single_object else
                                     'Actual G-code unique labels mapped through 3MF identify_id/build order.'),
              'scope': 'Offline fit-print candidate; physical cleanup, fit, strength and fabrication approval remain separate.'}
    write(output / 'final-print-analysis.json', report)
    write(output / 'bore-bead-clearance.json', {'scope': 'Road width/2 modeled as conservative radial bead radius; no physical tolerance qualification.', 'bores': bore_envelopes})
    placement_proof(project, parts, output)
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--engineering-root', type=Path, required=True,
                        help='Castle Harker checkout providing shared engineering APIs')
    parser.add_argument('--native-input', type=Path, required=True,
                        help='Native stand export directory including stand-build.json')
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--bambu', type=Path, required=True, help='Bambu Studio executable')
    args = parser.parse_args()
    engineering = args.engineering_root.resolve()
    if not (engineering / 'shared/manufacturing.py').is_file():
        parser.error('--engineering-root does not provide shared/manufacturing.py')
    sys.path.insert(0, str(engineering))
    from shared.manufacturing import make_project
    from systems.test_fixture.manufacturing.factory import load_factory, check_factory_settings
    output, native = args.output.resolve(), args.native_input.resolve()
    if output.exists():
        raise FileExistsError(f'Retain existing evidence and choose a new --output: {output}')
    config_path = native / 'stand-build.json'
    config_hash = sha(config_path)
    config = json.loads(config_path.read_text())['config']
    recipe = prepare(native, output)
    parts = recipe['parts']
    for part in parts:
        part['stl'] = str(output / part['stl'])
        part['source_step'] = str(native / part['source_step'])
    write(output / 'plate-parts.json', parts)
    profiles, factory = load_factory(args.bambu, recipe, output / 'factory')
    process = dict(profiles['process'], enable_support='1', support_critical_regions_only='1')
    objects = json.loads((output / 'plate.json').read_text())['plates'][0]['objects']
    job = output / 'four-part-critical'
    receipt = make_project(args.bambu, job, job.name, profiles['machine'], process,
                          [profiles['filament']], objects, filament_map='2', slice_from_project=True,
                          source_inputs={'parts': parts, 'process_overrides': recipe['process_overrides'],
                                         'scope': 'Offline proposal only; no fabrication approval'})
    imported = json.loads((job / 'out/settings.json').read_text())
    if imported['support_critical_regions_only'] != '1':
        raise ValueError('Studio did not retain critical-regions-only support')
    check_factory_settings(imported, profiles, enable_support=True)
    write(job / 'receipt.json', receipt)
    report = analyze(output, parts, config,
                     guard_support_required=not bool(config['drive_support'].get('underside_angle_degrees')))
    if sha(config_path) != config_hash or any(sha(p['source_step']) != p['source_step_sha256'] for p in parts):
        raise ValueError('Native input changed during preparation')
    retained = list(output.glob('*.json')) + list(output.glob('*.stl'))
    retained += [job / 'receipt.json', job / 'four-part-critical.3mf',
                 job / 'out/four-part-critical-sliced.3mf', job / 'out/plate_1.gcode',
                 job / 'out/settings.json', job / 'material-ledger.json',
                 output / 'factory/factory-inputs.json']
    write(output / 'manifest.json', {
        'scope': 'Offline print preparation only; no printer actions or fabrication approval.',
        'native_build_sha256': config_hash,
        'producer_sha256': {p.name: sha(p) for p in (Path(__file__), Path(__file__).with_name('stand_print.py'))},
        'factory': factory, 'source_mesh_identity': {p['id']: {
            'source_step_sha256': p['source_step_sha256'], 'stl_sha256': p['stl_sha256']} for p in parts},
        'artifacts': {str(p.relative_to(output)): {'sha256': sha(p), 'bytes': p.stat().st_size} for p in retained}})
    print(json.dumps({'output': str(output), 'estimate_seconds': report['estimate_seconds'],
                      'slicer_total_g': report['slicer_total_g'], 'fabrication_approved': False}, indent=2))


if __name__ == '__main__':
    main()
