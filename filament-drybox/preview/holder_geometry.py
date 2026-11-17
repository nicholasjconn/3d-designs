#!/usr/bin/env python3
"""Assembly preview payload for the holder, from native CAD only.

Inputs: a `cad/stand.py` build directory (stand-display.json, stand-build.json and,
when present, the `cad/spool_fit.py` result spool-fit.json); optionally the
`cad/drybox.py` output (wheel, outlet and filament clip, inventory and system checks),
a `cad/spindle_print.py` output, and a directory holding Bambu's published printable
spool STLs as a transparent fit reference. The output directory receives geometry.json,
the authored holder/ viewer and the pinned Three.js runtime from preview/node_modules
(`npm ci` in preview/). With --spool the output contains third-party meshes: keep it private.
"""
from pathlib import Path
import argparse,hashlib,json,math,shutil,struct
import numpy as np

HERE=Path(__file__).resolve().parent


def stl(path):
    b=path.read_bytes();n=struct.unpack_from('<I',b,80)[0]
    t=np.frombuffer(b,dtype=np.dtype([('n','<3f4'),('v','<9f4'),('a','<u2')]),count=n,offset=84)['v'].reshape(-1,3)
    u,inv=np.unique(np.round(t,4),axis=0,return_inverse=True);return u,inv.reshape(-1,3)


def part(name,vertices,triangles,offset):
    """Mesh with Y measured from `offset` (the bearing axis for rotating parts, 0 for fixed ones)."""
    v=np.asarray(vertices,float)-[0,offset,0]
    return {'id':name,'vertices':np.round(v,3).tolist(),'triangles':np.asarray(triangles).tolist()}


def annotations(build):
    """Labelled dimensions for the spindle/collar view, in axle coordinates (x, radius)."""
    c=build['config'];a=c['axle'];sp=c['spindle'];t=sp['thread'];h=sp['collar']['hub_x'];k=build['checks']
    travel=k['collar_travel_mm'];seat=sp['seat_start_x']
    return [
        {'id':'A','label':f"A  Custom thread Ø{2*t['major_radius']:g} × {t['pitch']:g} pitch, {k['thread']['engaged_turns']:.1f} turns engaged; {c['spindle']['lock']['slot_count']} lock slots",'from':[t['thread_x'][0],-t['major_radius']],'to':[t['thread_x'][1],-t['major_radius']],'offset':-5},
        {'id':'B','label':f"B  Collar travel {travel['inboard']:g} mm inboard / {travel['outboard']:g} mm outboard",'from':[h[1],sp['collar']['hub_outer_radius']],'to':[h[1]+travel['inboard'],sp['collar']['hub_outer_radius']],'offset':3},
        {'id':'C','label':f"C  Cone seats: 45° chamfers at X±{seat:g}–{sp['ring_x'][1]:g}",'from':[-sp['ring_x'][1],sp['seat_bore_radius']],'to':[sp['ring_x'][1],sp['seat_bore_radius']],'offset':6},
        {'id':'D','label':f"D  Shaft Ø{2*sp['shaft_radius']:g}",'from':[0,-sp['shaft_radius']],'to':[0,sp['shaft_radius']],'offset':0,'radial':True},
        {'id':'E','label':f"E  608 journals: drive Ø{2*a['journal_radius']:g}, left Ø{2*a['left_journal_radius']:g} slip fit",'from':[a['left_end_x'],a['journal_radius']],'to':[a['right_end_x'],a['journal_radius']],'offset':-24},
    ]


def lock_labels(build):
    """Label points for the lock slice view (x along the axle; y, z about the axis)."""
    c=build['config'];k=c['spindle']['lock'];t=c['spindle']['thread'];h0=c['spindle']['collar']['hub_x'][0]
    x=h0+k['key_x_from_hub'][1]-0.6;step=360/k['slot_count']
    at=lambda r,deg:[x,r*math.cos(math.radians(deg)),r*math.sin(math.radians(deg))]
    mid=(k['arm_root_angle_deg']+k['key_angle_deg'])/2
    return [{'label':'Key in a slot','at':at(k['pocket_radii'][1]+2.5,k['key_angle_deg'])},
            {'label':'Compliant arm (paddle at its tip, outboard face)','at':at(k['pocket_radii'][1]+2.5,mid)},
            {'label':f"{k['slot_count']} crest slots",'at':at(4,k['key_angle_deg']+4*step)}]


def print_plate(prep,job,limit=60000):
    """Oriented print meshes on the bed plus actual support roads (evenly sampled) from cad/spindle_print.py output."""
    parts=json.loads((prep/'plate-parts.json').read_text())
    report=json.loads((prep/f'analysis-{job}'/'final-print-analysis.json').read_text())
    meshes,roads=[],[]
    for p in parts:
        v,f=stl(Path(p['stl']))
        meshes.append({'id':p['id'],'orientation':p['orientation'],'vertices':np.round(v+[*p['placement_xy_mm'],0],3).tolist(),'triangles':f.tolist()})
        seg=np.array(json.loads((prep/f'analysis-{job}'/f"{p['id']}-supports.json").read_text())['segments'])
        seg[:,[0,3]]+=p['placement_xy_mm'][0];seg[:,[1,4]]+=p['placement_xy_mm'][1]
        roads.append(seg)
    roads=np.concatenate(roads);total=len(roads)
    if total>limit:roads=roads[np.linspace(0,total-1,limit).astype(int)]
    settings=json.loads((prep/job/'out/settings.json').read_text())
    return {'job':job,'meshes':meshes,'support_roads':np.round(roads[:,[0,1,2,3,4,5,7]],2).tolist(),'support_roads_total':total,
            'estimate_seconds':report['estimate_seconds'],'slicer_total_g':report['slicer_total_g'],'useful_part_g':report['useful_part_g'],
            'removed_g':report['removed_g'],'material_ledger':report['material_ledger'],
            'settings':{k:settings.get(k) for k in ['layer_height','wall_loops','sparse_infill_density','enable_support','support_type','support_style','support_critical_regions_only','curr_bed_type']},
            'downloads':{'project':f'print/{job}.3mf','sliced':f'print/{job}-sliced.3mf'}}


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--native',type=Path,required=True,help='cad/stand.py output directory')
    ap.add_argument('--spool',type=Path,help='directory with bambulab_spool_narrow.stl / _wide.stl')
    ap.add_argument('--output',type=Path,required=True)
    ap.add_argument('--print-prep',type=Path,help='cad/spindle_print.py output directory (optional print-plate view)')
    ap.add_argument('--print-job',default='critical-tree-slim',help='slicing variant to show from --print-prep')
    ap.add_argument('--system',type=Path,help='cad/drybox.py output directory (wheel, outlet, filament clip, inventory)')
    a=ap.parse_args();out=a.output.resolve();out.mkdir(parents=True,exist_ok=True)
    display=json.loads((a.native/'stand-display.json').read_text())
    build=json.loads((a.native/'stand-build.json').read_text())
    if display.get('schema')!='drybox-holder-native-v2':raise ValueError('Unexpected stand-display schema; rebuild with cad/stand.py')
    if not display['checks']['pass']:raise ValueError('Native holder checks failed: '+display['checks']['summary'])
    axis_y=build['config']['bearings']['axis_y']  # the viewer lifts every part except the frame about this height
    sha=lambda f:hashlib.sha256(Path(f).read_bytes()).hexdigest()
    manifest=json.loads((a.system/'manifest.json').read_text()) if a.system else None
    if manifest:
        if manifest.get('incomplete') or not manifest['checks']['system']['pass']:raise ValueError('cad/drybox.py build is incomplete or failed its checks')
        # Refuse a holder build other than the one the system manifest describes.
        recorded=manifest['producers']['holder']['outputs_sha256']
        native=a.native.resolve()
        mismatch=[f for f,h in recorded.items() if not (native/f).exists() or sha(native/f)!=h]
        if mismatch:raise ValueError(f'--native {native} is not the holder build recorded in {a.system}/manifest.json (differs: {mismatch})')
    parts=[part(n,m['vertices'],m['triangles'],0 if n=='fixed-stand' else axis_y) for n,m in display['components'].items()]
    parts+=[part('section-'+n,m['vertices'],m['triangles'],axis_y) for n,m in display['sections'].items()]
    if a.spool:
        for n in ['narrow','wide']:
            v,f=stl(a.spool/f'bambulab_spool_{n}.stl');parts.append(part('spool-'+n,v,f,0))
    # Show the spool fit only when the system manifest binds it to these holder files (not merely because a file exists).
    k=build['checks'];fit=a.native/'spool-fit.json';bound=(manifest or {}).get('spool_fit')
    fit_ok=bool(bound) and fit.exists() and sha(fit)==bound['output_sha256'] and all(recorded.get(f)==h for f,h in bound['holder_sha256'].items())
    checks={'lock':k['lock'],'rotating_min_gap_mm':k['rotating_min_gap_mm'],'axial_float_mm':k['axial_float_mm'],'collar_travel_mm':k['collar_travel_mm'],'thread':k['thread'],
            'volume_mm3':{n:k['parts'][n]['volume_mm3'] for n in ['spindle','collar']},
            'spool_fit':json.loads(fit.read_text()) if fit_ok else None}
    payload={'axis_y':axis_y,'parts':parts,'dimensions_mm':display['dimensions_mm'],'annotations':annotations(build),'lock_labels':lock_labels(build),'checks':checks}
    if a.system:
        system=json.loads((a.system/'system-display.json').read_text())
        if system.get('schema')!='drybox-system-display-v1':raise ValueError('Unexpected system-display schema; rebuild with cad/drybox.py')
        parts+=[part(n,m['vertices'],m['triangles'],0) for n,m in system['parts'].items()]
        payload['parts']=parts
        payload['system']={'inventory':manifest['inventory'],'checks':json.loads((a.system/'system-checks.json').read_text()),
                           'git_head':manifest['git_head'],'working_tree_changes':manifest['working_tree_changes_under_filament_drybox']}
    if a.print_prep:
        # The plate must have been prepared from geometry identical to this holder: its STEP inputs are the hash-checked
        # files of the reference build that drybox.py compared (0 mm³ symmetric difference) with these holder outputs.
        if not manifest:raise ValueError('--print-prep needs --system (its geometry is bound through the system reference comparison)')
        ref=json.loads((a.system/'system-checks.json').read_text()).get('reference_build')
        if not ref:raise ValueError('--print-prep needs a drybox.py run with --reference-build set to the build the plate was prepared from')
        prep=json.loads((a.print_prep/'plate-parts.json').read_text())
        artifacts=json.loads((a.print_prep/'manifest.json').read_text())['artifacts']
        for q in prep:
            step=Path(q['source_step']);name=step.name
            if step.parent.name!=ref['directory'] or ref['symmetric_difference_mm3'].get(step.stem)!=0:
                raise ValueError(f'print plate {q["id"]}: {step} is not a zero-difference reference part')
            if not (sha(step)==q['source_step_sha256']==ref['key']['reference_sha256'].get(name) and ref['key']['holder_sha256'].get(name)==recorded.get(name)):
                raise ValueError(f'print plate {q["id"]}: STEP input or holder output hash does not match the reference comparison')
            if sha(q['stl'])!=q['stl_sha256']:raise ValueError(f'print plate {q["id"]}: plate STL changed since preparation')
        for f in ['plate-parts.json',f'{a.print_job}/out/settings.json',f'{a.print_job}/out/plate_1.gcode',f'analysis-{a.print_job}/final-print-analysis.json']+[f'analysis-{a.print_job}/{q["id"]}-supports.json' for q in prep]:
            if sha(a.print_prep/f)!=artifacts[f]['sha256']:raise ValueError(f'print plate: {f} differs from its preparation manifest')
        payload['print']=print_plate(a.print_prep,a.print_job)
        # Offer only downloads that still match the preparation manifest; say why any other is withheld.
        (out/'print').mkdir(exist_ok=True)
        for key,f in [('project',f'{a.print_job}/{a.print_job}.3mf'),('sliced',f'{a.print_job}/out/{a.print_job}-sliced.3mf')]:
            target=out/'print'/Path(f).name
            if sha(a.print_prep/f)==artifacts[f]['sha256']:shutil.copy2(a.print_prep/f,target)
            else:
                payload['print']['downloads'].pop(key);target.unlink(missing_ok=True)
                payload['print'].setdefault('withheld',[]).append(f'{Path(f).name}: changed after preparation (file modified after the preparation manifest), so it is not offered')
    (out/'geometry.json').write_text(json.dumps(payload,separators=(',',':')))
    for f in ['index.html','viewer.js']:shutil.copy2(HERE/'holder'/f,out/f)
    three=HERE/'node_modules/three'
    if json.loads((three/'package.json').read_text())['version']!=json.loads((HERE/'package.json').read_text())['dependencies']['three']:
        raise ValueError('preview/node_modules/three does not match preview/package.json; run npm ci in preview/')
    (out/'vendor').mkdir(exist_ok=True)
    for src,dst in [('build/three.module.js','three.module.js'),('examples/jsm/controls/OrbitControls.js','OrbitControls.js'),('LICENSE','THREE-LICENSE')]:
        shutil.copy2(three/src,out/'vendor'/dst)
    print(json.dumps({'output':str(out),'parts':[p['id'] for p in parts],'bytes':(out/'geometry.json').stat().st_size}))


if __name__=='__main__':main()
