#!/usr/bin/env python3
"""Build individual print-orientation views from a checked drybox print proposal.

Requires the Castle Harker shared house renderer as an explicit tool dependency.
The print input is produced by cad/stand_prepare.py; no scratch files are inputs.
Support display samples every fourth body layer and all interface paths.
"""
import argparse
import importlib.util
import json
import math
from pathlib import Path
import shutil
import struct

INFO = {
 'fixed-stand': ('Grey frame', 'actuator_rear', 'Base flat on the bed; bearing seats upright.',
  'Angled guard underside and side struts landing on the legs remove guard scaffolding; free upper tips are shortened. Bearing seats, original wall contact and future-screw pilots retained. One manifold fabrication mesh.',
  'Remove bearing-holder supports; check bearing seating, jaw release, free rotation and container stability.'),
 'rotating-core': ('Green axle/core', 'printed_green', 'Axle horizontal, parallel to the bed. Layers run along the axle.',
  'Tangent rib/tube connection repaired with 0.2 mm positive overlap. All three air bores and thrust reliefs are clear of the selected support roads.',
  'Clean journal undersides and accessible cage supports; check both bearing fits, spool grip and clip-head retention. Print empty; bead containment is unfinished.'),
 'drive-rotor': ('Blue drive disc', 'actuator_output', 'Broad closed magnet-cover face down; magnet pockets face upward.',
  'Magnet skins, keyed connection and clip seating web retained. Counterbore-roof supports are reached through the open front and radial channel.',
  'Clear counterbore supports completely; check keyed seating, clip seating, magnet insertion and free rotation.'),
 'retaining-clip': ('Purple retaining clip', 'tpu', 'Broad flat face on the bed; clip flex stays in the layer plane.',
  'One manifold 2 mm printed clip. No support generated; mouth and inner curves remain in the slice.',
  'Check insertion, full seating, axial retention and removal without cracking or unintended backing out.'),
}


def load_mesh(path):
    raw = path.read_bytes(); count = struct.unpack_from('<I', raw, 80)[0]
    if len(raw) != 84+50*count:
        raise ValueError('Expected binary fabrication STL: '+str(path))
    vertices, triangles, ids = [], [], {}
    for row in struct.iter_unpack('<12fH', raw[84:]):
        face = []
        for k in (3, 6, 9):
            point = tuple(row[k:k+3])
            if point not in ids:
                ids[point] = len(vertices); vertices.append(point)
            face.append(ids[point])
        triangles.append(face)
    return {'vertices': vertices, 'triangles': triangles}


def write_stl(path, vertices, faces):
    with path.open('wb') as handle:
        handle.write(b'Display context only'.ljust(80, b'\0'));handle.write(struct.pack('<I', len(faces)))
        for f in faces:
            handle.write(struct.pack('<12fH', 0, 0, 0, *(v for i in f for v in vertices[i]), 0))


def boxes_mesh(boxes):
    vertices, faces = [], []
    triangles = ((0,2,1),(0,3,2),(4,5,6),(4,6,7),(0,1,5),(0,5,4),(1,2,6),(1,6,5),(2,3,7),(2,7,6),(3,0,4),(3,4,7))
    for corners in boxes:
        start=len(vertices);vertices.extend(corners);faces.extend(tuple(start+i for i in f) for f in triangles)
    return vertices, faces


def road_boxes(rows):
    boxes=[]
    for x,y,z,xx,yy,zz,width,role in rows:
        length=math.hypot(xx-x,yy-y)
        if length<=1e-10:
            raise ValueError('Zero-length support display segment')
        dx,dy=-(yy-y)*width/(2*length),(xx-x)*width/(2*length)
        boxes.append([(x+dx,y+dy,z-.2),(xx+dx,yy+dy,zz-.2),(xx-dx,yy-dy,zz-.2),(x-dx,y-dy,z-.2),
                      (x+dx,y+dy,z),(xx+dx,yy+dy,zz),(xx-dx,yy-dy,zz),(x-dx,y-dy,z)])
    return boxes_mesh(boxes)


def build(print_input, native_input, house, output):
    # Legacy four-part recipe only: refuse current-holder builds before doing any work.
    if 'carriers' in json.loads((Path(native_input)/'stand-build.json').read_text()).get('config', {}) or not (Path(native_input)/'rotating-core.step').is_file():
        raise ValueError(f'prepare_print_view.build: superseded four-part recipe (old frame + green axle/core); '
                         f'{native_input} is not a legacy four-part build. The current holder (removable carriers, '
                         'high-flow cartridge) has no print/section recipe yet; see README.md#holder.')
    if output.exists():raise FileExistsError(output)
    output.mkdir(parents=True);(output/'downloads').mkdir();(output/'display').mkdir()
    recipe=json.loads((print_input/'stand-print.json').read_text());analysis=json.loads((print_input/'final-print-analysis.json').read_text())
    integrity=json.loads((print_input/'mesh-integrity.json').read_text())
    if not all(p['watertight'] and p['connected_components']==1 for p in integrity.values()):raise ValueError('Fabrication mesh audit did not pass')
    native=json.loads((native_input/'stand-build.json').read_text())
    if not native['checks']['pass'] or analysis['warnings']:raise ValueError('Native or slicer checks did not pass')
    spec=importlib.util.spec_from_file_location('house_render', house/'render.py');render=importlib.util.module_from_spec(spec);spec.loader.exec_module(render)
    look=json.loads((house/'look.json').read_text());scene={'title':'Four-part holder print orientations','groups':[{'id':'parts','label':'Printed parts'},{'id':'context','label':'Display bed/support paths'}],'parts':[],'stills':[]}
    parts=[]
    for part in recipe['parts']:
        name=part['id'];label,material,orientation,audit,first_fit=INFO[name]
        stl=print_input/part['stl'];shutil.copyfile(stl,output/'downloads'/stl.name)
        mesh=load_mesh(stl);rows=json.loads((print_input/(name+'-supports.json')).read_text())['segments']
        sampled=[r for r in rows if r[7]==1 or round(r[2]/.2)%4==0 or r[2]<=.4]
        xyz=mesh['vertices']+[p for r in rows for p in (r[:3],r[3:6])]
        lo=[min(p[i] for p in xyz)-7 for i in range(3)];hi=[max(p[i] for p in xyz)+7 for i in range(3)]
        bed=output/'display'/(name+'-bed.stl');support=output/'display'/(name+'-supports.stl')
        corners=[(lo[0],lo[1],-.8),(hi[0],lo[1],-.8),(hi[0],hi[1],-.8),(lo[0],hi[1],-.8),(lo[0],lo[1],0),(hi[0],lo[1],0),(hi[0],hi[1],0),(lo[0],hi[1],0)]
        write_stl(bed,*boxes_mesh([corners]));ids=[name,name+'-bed']
        scene['parts'] += [{'id':name,'group':'parts','label':label,'material':material,'mesh':str(stl)}, {'id':name+'-bed','group':'context','material':'neutral','mesh':str(bed)}]
        if sampled:
            write_stl(support,*road_boxes(sampled));scene['parts'].append({'id':name+'-supports','group':'context','material':'band','mesh':str(support)});ids.append(name+'-supports')
        scene['stills'].append({'name':name,'title':label,'arrangement':'assembled','direction':[1,-1,.85],'parts':ids,'long_px':900})
        bb=part['bbox_bed_mm'];size=[bb['max'][i]-bb['min'][i] for i in range(3)]
        parts.append({'id':name,'label':label,'orientation':orientation,'audit':audit,'first_fit':first_fit,'color':look['materials'][material]['color'],'mesh':mesh,'size_mm':size,'context_bounds_mm':[lo,hi],
                      'support_segments':[[r[:3],r[3:6]] for r in sampled], 'support_note':('Supports required. Beige scaffolding samples every fourth support-body layer and all interface paths from this slice; actual removal must be checked.' if rows else 'No support generated. The flat clip stays in the layer plane.'),
                      'stl':'./print-assets/downloads/'+stl.name,'stl_sha256':part['stl_sha256'],'still':'./print-assets/renders/'+name+'.png','useful_part_g':analysis['useful_part_g'][name]})
    view=render.render_scene(scene,output/'renders')
    for part,still in zip(parts,view['stills']):part['camera']=still['camera']
    job=print_input/'four-part-critical';project=job/'four-part-critical.3mf';sliced=job/'out/four-part-critical-sliced.3mf'
    if not sliced.is_file():raise FileNotFoundError(sliced)
    shutil.copyfile(project,output/'downloads'/project.name);shutil.copyfile(sliced,output/'downloads'/sliced.name)
    useful=sum(analysis['useful_part_g'].values());support_mass=sum(v for k,v in analysis['removed_g'].items() if k in ('Support','Support interface'));seconds=round(analysis['estimate_seconds']);hours,rem=divmod(seconds,3600);minutes,sec=divmod(rem,60)
    data={'schema':'drybox-print-review-v1','status':'Nubbins removed. Four components audited and prepared together for an empty first fit print; support-setting approval and fabrication release remain pending.',
          'summary':'Four printed parts, one H2D plate. Assembly wall span 82.2 mm / 3.236″; base width 75 mm / 2.953″. Each view uses the same oriented STL as the prepared plate.',
          'settings':'Proposal: H2D right 0.4 mm, Bambu PLA Basic, factory 0.20 mm Standard, Textured PEI. Two changes from the factory process: support enabled (0 → 1), and support critical regions only (0 → 1). These changes require approval before fabrication. One filament color; actual feed assignment and calibration remain to be checked.',
          'estimate':f'Slice estimate: {hours} h {minutes} m {sec} s; {analysis["slicer_total_g"]:.2f} g reported. Useful parts {useful:.2f} g; supports/interface {support_mass:.2f} g; brim {analysis["removed_g"].get("Brim",0):.3f} g. No purge tower or color changes. Startup positive extrusion is separately about 0.183 g; loading/purge/calibration consumption remains unknown. Estimates are not weighed consumption.',
          'project':'./print-assets/downloads/'+project.name,'sliced':'./print-assets/downloads/'+sliced.name,'parts':parts,'look':{'lights':view['lights']},'source_step_sha256':{p['id']:p['source_step_sha256'] for p in recipe['parts']}}
    (output/'print-review.json').write_text(json.dumps(data,separators=(',',':'))+'\n')
    return data


if __name__=='__main__':
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--print-input',type=Path,required=True);ap.add_argument('--native-input',type=Path,required=True);ap.add_argument('--house-renderer',type=Path,required=True);ap.add_argument('--output',type=Path,required=True);args=ap.parse_args();build(args.print_input.resolve(),args.native_input.resolve(),args.house_renderer.resolve(),args.output.resolve())
