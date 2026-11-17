#!/usr/bin/env python3
"""Export planar review sections from the checked stand STEP exports.

The CAD intersection is native; sampled curved outlines are display paths,
not metrology. No projected geometry from outside each plane is included.
"""
import argparse
import hashlib
import json
from pathlib import Path

import cadquery as cq

PARTS = {
    'frame': 'fixed-stand', 'core': 'rotating-core', 'disc': 'drive-rotor',
    'clip': 'retaining-clip', 'left-bearing': 'left-bearing',
    'right-bearing': 'right-bearing',
}
DISPLAY_DEFLECTION_MM = 0.01


def area(points):
    return abs(sum(a[0]*b[1]-b[0]*a[1]
                   for a, b in zip(points, points[1:]+points[:1])))/2


def export_sections(build_dir, output):
    receipt = json.loads((build_dir/'stand-build.json').read_text())
    # Legacy four-part recipe only: refuse current-holder builds before doing any work.
    if 'carriers' in receipt.get('config', {}) or not (Path(build_dir)/'rotating-core.step').is_file():
        raise ValueError(f'stand_sections.export_sections: superseded four-part recipe (old frame + green axle/core); '
                         f'{build_dir} is not a legacy four-part build. The current holder (removable carriers, '
                         'high-flow cartridge) has no print/section recipe yet; see README.md#holder.')
    if not receipt['checks']['pass']:
        raise ValueError('Stand source must have a passing concept geometry receipt')
    cfg = receipt['config']
    sections = [
        {'id': 'shaft', 'label': 'A–A · Through axle', 'plane': 'XY', 'offset_mm': 0,
         'description': 'Vertical cut at Z = 0 mm, through the axle center. Look from +Z toward −Z; X runs left to right and Y runs upward.',
         'note': 'Only material intersected by this plane is filled. The front/rear base crossbars are outside this cut. The wall-side tapered roof is cut below the disc. Its side struts lie outside this plane.',
         'detail_box_mm': [25, 90, 48, 119]},
        {'id': 'stops', 'label': 'B–B · Through guard lip', 'plane': 'XY',
         'offset_mm': (cfg['drive_support']['outer_radius']+cfg['drive_support']['rotor_clear_radius'])/2,
         'description': 'Vertical cut through the +Z guard lip. Look from +Z toward −Z; X runs left to right and Y runs upward.',
         'note': 'The blue disc is absent because this cut is outside its radius. The guard lip alone reaches the drive-wall plane. The old rounded noses and their support wings have been removed.',
         'detail_box_mm': [32, 92, 48, 121]},
        {'id': 'top', 'label': 'C–C · At axle height', 'plane': 'XZ',
         'offset_mm': cfg['bearings']['axis_y'],
         'description': 'Horizontal cut at axle height. Look down from +Y toward −Y; X runs left to right and +Z runs upward on this drawing.',
         'note': 'This cut shows the straight lip bands around both sides of the blue disc. The rounded noses and their support wings are removed; the lip remains continuous around the sides and bottom of the disc. The base is below this plane and is absent.',
         'detail_box_mm': [32, 36, 48, 55]},
        {'id': 'base', 'label': 'D–D · Through base crossbar', 'plane': 'XY',
         'offset_mm': cfg['base']['expansion_pilots']['center_z'],
         'description': 'Vertical cut through the +Z base crossbar and future-screw pilot. Look from +Z toward −Z; X runs left to right and Y runs upward.',
         'note': 'The base crossbar spans its actual outside edges. The axle and upper frames are outside this cut. The bore is a smooth future-screw pilot.',
         'detail_box_mm': [-40, -2, -14, 15]},
    ]
    shapes = {}
    identities = {}
    for alias, name in PARTS.items():
        path = build_dir/(name+'.step')
        shapes[alias] = cq.importers.importStep(str(path)).val()
        identities[name+'.step'] = hashlib.sha256(path.read_bytes()).hexdigest()
    for spec in sections:
        origin = (0, 80, spec['offset_mm']) if spec['plane']=='XY' else (0, spec['offset_mm'], 0)
        plane = cq.Face.makeFromWires(cq.Workplane(spec['plane'], origin=origin).rect(180, 180).val())
        spec['components'] = {}
        for name, shape in shapes.items():
            faces = shape.intersect(plane).Faces()
            display_faces = []
            for face in faces:
                loops = []
                imprints = []
                for wire in [face.outerWire(), *face.innerWires()]:
                    if not wire.IsClosed():
                        # OCCT Common retains a single internal LINE where the
                        # plane is tangent to a surface. It has zero enclosed
                        # area: export it as an imprint, never as a filled hole.
                        edges = wire.Edges()
                        if wire.isSame(face.outerWire()) or len(edges)!=1 or edges[0].geomType()!='LINE':
                            raise ValueError(f'Unexpected open section wire: {spec["id"]}/{name}')
                        points, _ = edges[0].sample(DISPLAY_DEFLECTION_MM)
                        imprints.append([[round(p.x, 6), round(p.y if spec['plane']=='XY' else p.z, 6)] for p in points])
                        continue
                    points, _ = wire.sample(DISPLAY_DEFLECTION_MM)
                    uv = [[p.x, p.y if spec['plane']=='XY' else p.z] for p in points]
                    if len(uv)<3:
                        raise ValueError(f'Invalid display loop: {spec["id"]}/{name}')
                    loops.append([[round(a, 6), round(b, 6)] for a,b in uv])
                display_area = area(loops[0])-sum(area(loop) for loop in loops[1:])
                display_faces.append({'loops_mm': loops, 'imprint_paths_mm': imprints, 'native_area_mm2': face.Area(),
                                      'display_area_mm2': display_area})
            spec['components'][name] = display_faces
    wall = receipt['dimensions_mm']['right_wall_x']
    contacts = []
    for face in shapes['frame'].Faces():
        bb = face.BoundingBox()
        if abs(bb.xmin-wall)<1e-5 and abs(bb.xmax-wall)<1e-5:
            contacts.append({'area_mm2': face.Area(), 'x_mm': wall,
                             'y_mm': [bb.ymin, bb.ymax], 'z_mm': [bb.zmin, bb.zmax]})
    if not contacts:
        raise ValueError('No planar frame contact face at the documented drive wall')
    result = {'schema': 'stand-native-sections-v1', 'units': 'mm',
              'method': 'Native STEP solid/plane intersections; only intersected material is shown. Curved display outlines sampled at 0.01 mm requested deflection.',
              'bearing_scope': '608 references are plain 8 × 22 × 7 mm annular envelopes. Shields, balls and races are not modeled.',
              'dimensions_mm': receipt['dimensions_mm'], 'parameters': receipt['parameters'],
              'source_step_sha256': identities, 'wall_contact_faces': contacts,
              'sections': sections}
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(result, separators=(',', ':'))+'\n')
    return result


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--build', type=Path, required=True, help='Checked stand STEP export directory')
    ap.add_argument('--output', type=Path, required=True, help='Derived section JSON payload')
    args = ap.parse_args()
    data = export_sections(args.build, args.output)
    print(json.dumps({'sections': len(data['sections']), 'output': str(args.output),
                      'wall_contact_faces': data['wall_contact_faces']}, indent=2))


if __name__ == '__main__':
    main()
