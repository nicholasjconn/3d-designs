#!/usr/bin/env python3
"""Prepare four oriented fabrication meshes and one-plate placement inputs.

No slicing, printer control, manufacturing-setting approval or fabrication.
Consumes native STEP exports of the same four-part CAD build. Geometry axes
are X axle, Y up, Z fore/aft; output meshes use print XYZ with Z up.
"""
import argparse
import hashlib
import json
import math
import struct
from collections import Counter
from pathlib import Path

import cadquery as cq
from OCP.BRepBndLib import BRepBndLib
from OCP.Bnd import Bnd_Box

PARTS = (
    ('fixed-stand', 'upright', 'X', 90, (80, 95)),
    ('rotating-core', 'horizontal', 'X', 90, (190, 95)),
    ('drive-rotor', 'frontdown', 'Y', 90, (185, 175)),
    ('retaining-clip', 'flat', 'Y', 90, (280, 195)),
)
ROTATIONS = {
    'X': ((1, 0, 0), ((1, 0, 0), (0, 0, -1), (0, 1, 0))),
    'Y': ((0, 1, 0), ((0, 0, 1), (0, 1, 0), (-1, 0, 0))),
}


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def bounds(shape):
    box = Bnd_Box()
    BRepBndLib.AddOptimal_s(shape.wrapped, box, False, False)
    values = box.Get()
    return [list(values[:3]), list(values[3:])]


def mesh_integrity(path):
    """Inspect binary STL using exact float-coordinate welding; never repair it."""
    data = path.read_bytes()
    if len(data) < 84:
        raise ValueError(f'{path}: truncated binary STL')
    count = struct.unpack_from('<I', data, 80)[0]
    if not count or len(data) != 84 + 50 * count:
        raise ValueError(f'{path}: unexpected binary STL length or triangle count')
    vertices, edges, winding, owners = {}, Counter(), Counter(), {}
    parents = list(range(count))

    def root(i):
        while parents[i] != i:
            parents[i] = parents[parents[i]]
            i = parents[i]
        return i

    finite, degenerate, volumes = True, 0, []
    low, high = [math.inf] * 3, [-math.inf] * 3
    for i in range(count):
        values = struct.unpack_from('<12fH', data, 84 + 50 * i)
        points = [tuple(values[j:j + 3]) for j in (3, 6, 9)]
        ids = []
        for point in points:
            finite = finite and all(math.isfinite(v) for v in point)
            for j, value in enumerate(point):
                low[j], high[j] = min(low[j], value), max(high[j], value)
            if point not in vertices:
                vertices[point] = len(vertices)
            ids.append(vertices[point])
        a, b, c = points
        u, v = [b[j] - a[j] for j in range(3)], [c[j] - a[j] for j in range(3)]
        cross = (u[1]*v[2]-u[2]*v[1], u[2]*v[0]-u[0]*v[2], u[0]*v[1]-u[1]*v[0])
        degenerate += sum(q*q for q in cross) <= 1e-24
        volumes.append((a[0]*(b[1]*c[2]-b[2]*c[1]) + a[1]*(b[2]*c[0]-b[0]*c[2]) + a[2]*(b[0]*c[1]-b[1]*c[0]))/6)
        for first, second in zip(ids, (ids[1], ids[2], ids[0])):
            edge = tuple(sorted((first, second)))
            edges[edge] += 1
            winding[edge] += 1 if first < second else -1
            if edge in owners:
                parents[root(i)] = root(owners[edge])
            else:
                owners[edge] = i
    report = {
        'triangles': count, 'welded_vertices': len(vertices),
        'finite_coordinates': finite, 'boundary_edges': sum(n == 1 for n in edges.values()),
        'nonmanifold_edges': sum(n != 2 for n in edges.values()),
        'inconsistent_edge_winding': sum(n != 0 for n in winding.values()),
        'degenerate_triangles': degenerate,
        'connected_components': len({root(i) for i in range(count)}),
        'signed_volume_mm3': math.fsum(volumes),
        'bounds_mm': [low, high], 'mesh_repaired': False,
    }
    report['watertight'] = finite and not report['nonmanifold_edges']
    report['passed'] = (report['watertight'] and not report['inconsistent_edge_winding']
                        and not degenerate and report['connected_components'] == 1
                        and report['signed_volume_mm3'] > 0)
    return report


def prepare(native_input, output):
    native_input, output = Path(native_input), Path(output)
    # Legacy four-part recipe only: refuse current-holder builds before doing any work.
    if 'carriers' in json.loads((native_input/'stand-build.json').read_text()).get('config', {}) or not (Path(native_input)/'rotating-core.step').is_file():
        raise ValueError(f'stand_print.prepare: superseded four-part recipe (old frame + green axle/core); '
                         f'{native_input} is not a legacy four-part build. The current holder (removable carriers, '
                         'high-flow cartridge) has no print/section recipe yet; see README.md#holder.')
    output.mkdir(parents=True, exist_ok=True)
    parts, objects = [], []
    for name, pose, axis, angle, placement in PARTS:
        source = native_input / (name + '.step')
        shape = cq.importers.importStep(str(source)).val()
        if not shape.isValid() or len(shape.Solids()) != 1:
            raise ValueError(f'{source}: expected one valid solid')
        direction, matrix = ROTATIONS[axis]
        shape = shape.rotate((0, 0, 0), direction, angle)
        shift = [-v for v in bounds(shape)[0]]
        shape = shape.translate(tuple(shift))
        mesh = output / (name + '-' + pose + '.stl')
        if not shape.exportStl(str(mesh), tolerance=.05, angularTolerance=.15, relative=False):
            raise RuntimeError('Fabrication mesh export failed: ' + str(mesh))
        cq.exporters.export(shape, str(output / (name + '-' + pose + '.step')))
        box = bounds(shape)
        transform = [list(matrix[i]) + [shift[i] + (placement[i] if i < 2 else 0)] for i in range(3)]
        transform.append([0, 0, 0, 1])
        parts.append({
            'id': name, 'orientation': pose,
            'source_step': source.name, 'source_step_sha256': sha(source),
            'stl': mesh.name, 'stl_sha256': sha(mesh),
            'rotation_axis': axis, 'rotation_degrees': angle,
            'minimum_corner_translation_mm': shift,
            'placement_xy_mm': placement, 'native_to_bed': transform,
            'bbox_bed_mm': {
                'min': [box[0][i] + (placement[i] if i < 2 else 0) for i in range(3)],
                'max': [box[1][i] + (placement[i] if i < 2 else 0) for i in range(3)],
            },
        })
        objects.append({'path': str(mesh.resolve()), 'count': 1, 'filaments': [1],
                        'pos_x': [placement[0]], 'pos_y': [placement[1]], 'pos_z': [0],
                        'print_params': {}})
    integrity = {p['id']: mesh_integrity(output / p['stl']) for p in parts}
    (output / 'mesh-integrity.json').write_text(json.dumps(integrity, indent=2) + '\n')
    if any(not report['passed'] for report in integrity.values()):
        raise ValueError('Fabrication mesh integrity failed; see mesh-integrity.json')
    recipe = {
        'status': 'Offline proposed fit-print configuration; fabrication not approved',
        'studio_version': '02.09.01.70',
        'presets': {'machine': 'Bambu Lab H2D 0.4 nozzle',
                    'process': '0.20mm Standard @BBL H2D',
                    'filament': 'Bambu PLA Basic @BBL H2D'},
        'plate': 'Textured PEI Plate', 'filament_map': '2',
        'process_overrides': {'enable_support': {'factory': '0', 'candidate': '1'},
                              'support_critical_regions_only': {'factory': '0', 'candidate': '1'}},
        'mesh_export': {'absolute_linear_tolerance_mm': .05, 'angular_tolerance_radians': .15},
        'parts': parts,
    }
    (output / 'stand-print.json').write_text(json.dumps(recipe, indent=2) + '\n')
    plate = {'plates': [{'plate_name': 'four-part-holder', 'need_arrange': False,
                         'plate_params': {'curr_bed_type': recipe['plate'],
                                          'filament_map_mode': 'Manual', 'filament_map': '2'},
                         'objects': objects}]}
    (output / 'plate.json').write_text(json.dumps(plate, indent=2) + '\n')
    return recipe


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--native-input', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(prepare(args.native_input, args.output), indent=2))
