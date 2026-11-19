#!/usr/bin/env python3
"""Nominal lip/flange strip screen for gentle first fit; no printed strength rating."""
from pathlib import Path
import argparse,hashlib,json,math
from direct_interfaces import config

def screen(c):
    p=c['port'];t=p['dock_outer_x']-p['dock_channel_x'][1];length=p['dock_channel_radius']-p['dock_lip_radius'];width=5;modulus=1000
    rows=[]
    for total,patches in [(10,1),(20,2),(20,1)]:
        force=total/patches;inertia=width*t**3/12
        rows.append({'total_axial_load_N':total,'contact_patches':patches,'force_each_N':force,'patch_width_mm':width,'lip_length_mm':length,'plate_thickness_mm':t,'nominal_bending_MPa':6*force*length/(width*t*t),'nominal_shear_MPa':1.5*force/(width*t),'tip_deflection_mm':force*length**3/(3*modulus*inertia)})
    flange=[{'patch_load_N':force,'thickness_mm':p['flange_thickness'],'nominal_bending_MPa':6*force*length/(width*p['flange_thickness']**2)} for force in [5,10,20]]
    engaged=p['wall_inner_x']-p['fitting_tip_x'];area=math.pi*17*engaged*.5
    return {'purpose':'Local lip/flange and thread order-of-magnitude screen for a gentle first fit print; not strength qualification. Earlier frame FE results do not apply.',
        'assumptions':{'modulus_MPa':modulus,'modulus_basis':'screening assumption, not measured printed material','strip_width_mm':width,'load_basis':'10N gentle handling and20N asymmetric sensitivity, not measured service loads','model':'Unfilleted cantilever strip. Omits curved-ring sharing, stress concentrations, layer defects and creep. Nominal stresses only.'},
        'lip_cases':rows,'nut_flange_cases':flange,
        'thread_proxy':{'diameter_mm':17,'engaged_length_mm':engaged,'engaged_turns':engaged/p['thread_pitch'],'effective_shear_area_mm2':area,'shear_at_20N_MPa':20/area,'shear_at_60N_MPa':60/area},
        'limitations':'No measured allowable, safety factor, tightening torque or lifetime rating. The1.6mm nut flange is thinner than the2.2mm lip. Finger-snug nut only; do not pry on the flange or force bound threads. Physical full-load rotation, retention and sealing checks remain.'}

if __name__=='__main__':
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--output',type=Path,required=True);a=ap.parse_args();r=screen(config());r['source_sha256']={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in [Path(__file__),Path(__file__).with_name('direct_drive.json')]};a.output.write_text(json.dumps(r,indent=2)+'\n');print(a.output)
