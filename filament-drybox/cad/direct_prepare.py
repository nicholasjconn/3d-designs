#!/usr/bin/env python3
"""Export and slice the current matching direct-drive fit-print plate; never send.

Uses the established H2D/PLA/Standard/Textured PEI single-material tree-slim
critical-support configuration. Engineering-root supplies retained factory,
slicing and G-code accounting helpers; geometry comes only from this repo.
"""
from pathlib import Path
import argparse,hashlib,json,sys
import cadquery as cq
import numpy as np
from stand_print import bounds,mesh_integrity,sha
from spindle_print import retain_process_overrides
from stand_prepare import analyze

RECIPES=[('stand','X',90,(40,40),'base down'),
         ('axle','Y',90,(150,45),'drive end down; thread boss ramp upward'),
         ('collar','Y',-90,(225,45),'outboard stop face down'),
         ('right-carrier','Y',90,(150,135),'flat rear locator face down'),
         ('left-carrier','Y',-90,(195,135),'flat rear locator face down'),
         ('inside-nut','Y',-90,(240,135),'wide flange down; thread vertical'),
         ('crank','Y',90,(150,200),'grip end down; square socket opens up'),
         ('fitting','Y',90,(205,200),'outside thread down; wall O-ring groove upward'),
         ('cap','Y',90,(250,200),'closed end down; threaded opening upward')]
ROT={('X',90):((1,0,0),((1,0,0),(0,0,-1),(0,1,0))),
     ('Y',90):((0,1,0),((0,0,1),(0,1,0),(-1,0,0))),
     ('Y',-90):((0,1,0),((0,0,-1),(0,1,0),(1,0,0)))}

def main():
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--native-input',type=Path,required=True);ap.add_argument('--engineering-root',type=Path,required=True);ap.add_argument('--bambu',type=Path,default=Path('/Applications/BambuStudio.app/Contents/MacOS/BambuStudio'));ap.add_argument('--output',type=Path,required=True);a=ap.parse_args()
    out=a.output.resolve();out.mkdir(parents=True,exist_ok=False);native=a.native_input.resolve()
    sys.path.insert(0,str(a.engineering_root.resolve()))
    from shared.manufacturing import make_project
    from systems.test_fixture.manufacturing.factory import load_factory,check_factory_settings
    manifest=json.loads((native/'manifest.json').read_text());parts=[];objects=[]
    for name,axis,angle,xy,description in RECIPES:
        src=native/(name+'.step')
        if sha(src)!=manifest['outputs'][name]['sha256']:raise ValueError('Native STEP changed: '+name)
        s=cq.importers.importStep(str(src)).val();direction,rotation=ROT[(axis,angle)]
        s=s.rotate((0,0,0),direction,angle);shift=[-v for v in bounds(s)[0]];s=s.translate(tuple(shift))
        target=out/(name+'.stl');s.exportStl(str(target),tolerance=.02,angularTolerance=.1,relative=False)
        check=mesh_integrity(target)
        if not check['passed']:raise ValueError('Invalid fabrication mesh '+name+': '+str(check))
        b=bounds(s)
        p={'id':name,'orientation':description,'source_step':str(src),'source_step_sha256':sha(src),'stl':str(target),'stl_sha256':sha(target),'native_volume_mm3':s.Volume(),'mesh_integrity':check,'placement_xy_mm':xy,'bbox_bed_mm':{'min':[b[0][i]+(xy[i] if i<2 else 0) for i in range(3)],'max':[b[1][i]+(xy[i] if i<2 else 0) for i in range(3)]},'native_to_bed':[list(rotation[i])+[shift[i]+(xy[i] if i<2 else 0)] for i in range(3)]+[[0,0,0,1]]}
        parts.append(p);objects.append({'path':str(target),'count':1,'filaments':[1],'pos_x':[xy[0]],'pos_y':[xy[1]],'pos_z':[0],'print_params':{}})
    (out/'plate-parts.json').write_text(json.dumps(parts,indent=2)+'\n')
    recipe={'studio_version':'02.09.01.70','presets':{'machine':'Bambu Lab H2D 0.4 nozzle','process':'0.20mm Standard @BBL H2D','filament':'Bambu PLA Basic @BBL H2D'},'plate':'Textured PEI Plate','filament_map':'2'}
    profiles,factory=load_factory(a.bambu,recipe,out/'factory')
    overrides={'enable_support':'1','support_critical_regions_only':'1','support_style':'tree_slim'}
    process=dict(profiles['process'],**overrides);job=out/'direct-drive-fit'
    print(f'Slicing {len(RECIPES)} matching parts; same established single-PLA tree-slim configuration',flush=True)
    receipt=make_project(a.bambu,job,job.name,profiles['machine'],process,[profiles['filament']],objects,filament_map='2',slice_from_project=True,edit_project=lambda p:retain_process_overrides(p,overrides),source_inputs={'native_manifest_sha256':sha(native/'manifest.json'),'canonical_source_sha256':manifest['source_sha256'],'part_recipe':parts,'process_overrides':overrides,'scope':'Offline first-fit preparation; no printer send'})
    settings=json.loads((job/'out/settings.json').read_text());check_factory_settings(settings,dict(profiles,process=process),enable_support=True)
    config=json.loads(Path(__file__).with_name('direct_drive.json').read_text());config['disc']={}
    report=analyze(out,parts,config,job_name=job.name,guard_support_required=False)
    from direct_toolpaths import check as check_functional
    check_functional(out,a.engineering_root)
    for p in parts:
        if sha(Path(p['source_step']))!=p['source_step_sha256']:raise ValueError('STEP changed during slicing '+p['id'])
    (out/'print-recipe.json').write_text(json.dumps({'recipe':recipe,'overrides':overrides,'receipt':receipt,'native_manifest_sha256':sha(native/'manifest.json'),'producer_sha256':{n:sha(Path(__file__).with_name(n)) for n in ['direct_prepare.py','stand_print.py','stand_prepare.py','spindle_print.py','direct_toolpaths.py']},'status':'Sliced fit-print candidate; independent review and source approval separate; no print sent'},indent=2)+'\n')
    print(json.dumps({k:v for k,v in report.items() if k in ['warnings','estimate_seconds','slicer_total_g','useful_part_g','removed_g']},indent=2),flush=True)

if __name__=='__main__':main()
