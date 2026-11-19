#!/usr/bin/env python3
"""Build the canonical through-wall direct-drive drybox and its native fit checks.

No scratch or earlier STEP inputs. Optional outlet/clip builds remain separate;
these interfaces are unchanged. This command never slices or sends a print.
"""
from pathlib import Path
import argparse,hashlib,json,platform,subprocess,sys,time
import cadquery as cq
import numpy as np
import manifold3d as m
import direct_stand,bearing_carrier,direct_spindle,wall_fitting,inside_nut,sealing_cap,direct_crank
import spindle
from direct_interfaces import config,cyl,box,one

HERE=Path(__file__).resolve().parent
PART_MODULES={'stand':direct_stand,'axle':direct_spindle,'inside-nut':inside_nut,
              'fitting':wall_fitting,'cap':sealing_cap,'crank':direct_crank}

def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()

def mesh(s):
    v,f=s.tessellate(.02,.14)
    v,ix=np.unique(np.round([a.toTuple() for a in v],4),axis=0,return_inverse=True)
    q=m.Manifold(m.Mesh(vert_properties=v.astype(np.float32),tri_verts=ix[np.asarray(f)].astype(np.uint32)))
    if q.status()!=m.Error.NoError:raise ValueError('Native triangulation: '+str(q.status()))
    return q

def context(c):
    y=c['bearings']['axis_y'];p=c['port'];s=c['spool'];a=s['hub_width']/2;b=s['flange_width']/2
    w=cq.Workplane('XY').polyline([(-a,s['bore_radius']),(-a,s['recess_radius']),(-b,s['recess_radius']),(-b,s['outer_radius']),(b,s['outer_radius']),(b,s['recess_radius']),(a,s['recess_radius']),(a,s['bore_radius'])]).close().val()
    spool=cq.Solid.revolve(cq.Face.makeFromWires(w),360,cq.Vector(0,0,0),cq.Vector(1,0,0)).translate((0,y,0))
    wi=p['wall_inner_x'];wo=wi+p['wall_thickness']
    parts={'spool':spool,'wall':box(wi,wo,y-43,y+43,-43,43).cut(cyl(p['hole_diameter']/2,wi-.1,wo+.1))}
    for side in ['left','right']:
        x0,x1=c['bearings'][side+'_x'];parts[side+'-bearing']=cyl(11,x0,x1).cut(cyl(4,x0-.1,x1+.1))
    return parts

def check(c,parts):
    mm={k:mesh(v) for k,v in parts.items()}; overlaps={};stops={}
    def free(k,a,b):
        v=(a^b).volume();overlaps[k]=v
        if abs(v)>.001:raise ValueError('Interference '+k+': '+str(v))
    for n in ['inside-nut','fitting','cap','crank','right-carrier','left-carrier','axle','collar','spool','left-bearing','right-bearing','wall']:
        free('stand/'+n,mm['stand'],mm[n])
    for dx in [-.5,0,.5]:
        for dy in [0,1,2,3,5,10,20,30]:
            for n in ['inside-nut','fitting','stand']:
                for moving in ['axle','left-carrier','right-carrier','left-bearing','right-bearing','spool'] if dx==0 else ['axle']:
                    free(f'{moving}/float{dx}/lift{dy}/{n}',mm[moving].translate([dx,dy,0]),mm[n])
        for moving in ['axle','collar','spool']:
            for n in ['stand','left-carrier','right-carrier','inside-nut','fitting']:
                free(f'{moving}/float{dx}/{n}',mm[moving].translate([dx,0,0]),mm[n])
        for angle in range(0,360,30):
            for moving in ['axle','collar']:
                q=mm[moving].translate([0,-104,0]).rotate([angle,0,0]).translate([dx,104,0])
                for n in ['left-carrier','right-carrier','stand','inside-nut','fitting']:
                    free(f'rotate/{moving}/{dx}/{angle}/{n}',q,mm[n])
    for dx in [0,1,4,8,16,25]:
        for n in ['axle','fitting','inside-nut','stand']:
            free(f'crank/extract{dx}/{n}',mm['crank'].translate([dx,0,0]),mm[n])
    # Crank follows the key shoulder outward. At inward float its mouth can
    # seat on the rotating608 inner race, rather than entering the bearing.
    for dx in [-.5,0,.5]:
        crank_dx=max(dx,-.1)
        q=mm['crank'].translate([crank_dx,0,0])
        free(f'crank/coupled-float{dx}/axle',q,mm['axle'].translate([dx,0,0]))
        for n in ['fitting','inside-nut','stand','right-carrier','right-bearing']:
            free(f'crank/coupled-float{dx}/{n}',q,mm[n])
    for n in ['fitting','inside-nut','axle']:free('cap/'+n,mm['cap'],mm[n])
    for dx in [-3.2,-2,-1,0]:
        q=mm['inside-nut'].translate([0,-104,0]).rotate([360*dx/2,0,0]).translate([dx,104,0])
        free(f'nut/thread-run{dx}',q,mm['fitting'])
    for dy in [-.5,.5]:free('nut/vertical'+str(dy),mm['inside-nut'].translate([0,dy,0]),mm['stand'])
    for d in [-.3,.3]:
        for axis in [0,2]:
            move=[0,0,0];move[axis]=d;v=(mm['stand'].translate(move)^mm['inside-nut']).volume()
            stops[f'nut/axis{axis}/{d}']=v
            if v<.01:raise ValueError('Nut lacks positive transverse/axial capture')
    # Deeper bidirectional lock: displaced thread with tooth down must hit; released must clear.
    pitch=c['spindle']['thread']['pitch'];k=c['spindle']['lock']
    released=mesh(spindle.collar(c,lift=9+k['lift_clearance']-k['key_tip_radius']))
    for dx in [0,5]:
        for angle in [-5,5]:
            q=mm['collar'].translate([0,-104,0]).rotate([360*dx/pitch+angle,0,0]).translate([dx+angle*pitch/360,104,0])
            v=(q^mm['axle']).volume();stops[f'collar/travel{dx}/turn{angle}']=v
            if v<.1:raise ValueError('Collar lock fails to stop rotation')
    for dx in [.125,2.625,4.875]:
        q=released.translate([0,-104,0]).rotate([360*dx/pitch,0,0]).translate([dx,104,0])
        free('collar/released/'+str(dx),q,mm['axle'])
    return {'scope':'Nominal native geometry, reference spool and assumed2mm wall. Printed fit, strength, creep and sealing require physical checks.',
            'clearance_cases':len(overlaps),'clearance_overlap_mm3':overlaps,'positive_stops_mm3':stops,
            'dimensions_mm':{'marked_span':84.6,'stand_span':84.4,'upright_gap':74.8,'centered_spool_clearance_each_side':3.5,'minimum_spool_clearance_at_modeled_half_mm_float':3,'nut_length':4.2,'retaining_lip_thickness':2.2,'flange_radial_overlap':2.4,'nut_thread_engagement_at_2mm_wall':3,'carrier_nut_face_gap':0,'crank_key_overlap_nominal':3.8,'crank_key_min_overlap_at_modeled_float':3.4,'shaft_tip_to_nut':1},'pass':True}

def main():
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--output',type=Path,required=True);ap.add_argument('--with-outlet',action='store_true');ap.add_argument('--with-clip',action='store_true');args=ap.parse_args()
    out=args.output.resolve();out.mkdir(parents=True,exist_ok=True);start=time.monotonic();c=config()
    sources=[HERE/'drybox.py',HERE/'direct_drive.json',HERE/'direct_interfaces.py',HERE/'spindle.py',HERE/'bearing_carrier.py',*[Path(p.__file__) for p in PART_MODULES.values()]]
    binding={p.name:sha(p) for p in sources}
    parts={n:p.build(c) for n,p in PART_MODULES.items()}
    parts.update({'left-carrier':bearing_carrier.build(c,-1),'right-carrier':bearing_carrier.build(c,1),'collar':spindle.collar(c),**context(c)})
    outputs={}
    for n,s in parts.items():
        one(s,n);path=out/(n+'.step');cq.exporters.export(s,str(path));outputs[n]={'file':path.name,'sha256':sha(path),'volume_mm3':s.Volume()}
        parts[n]=cq.importers.importStep(str(path)).val()
    report=check(c,parts);(out/'checks.json').write_text(json.dumps(report,indent=2)+'\n')
    for enabled,name in [(args.with_outlet,'outlet'),(args.with_clip,'clip')]:
        if enabled:subprocess.run([sys.executable,str(HERE/(name+'.py')),'--output',str(out/name)],check=True)
    if {p.name:sha(p) for p in sources}!=binding:raise ValueError('Canonical sources changed during build')
    commit=subprocess.check_output(['git','-C',str(HERE.parents[1]),'rev-parse','HEAD'],text=True).strip()
    record={'system':'filament-drybox/direct-drive','source_commit':commit,'source_state':'working-tree candidate, not committed','source_sha256':binding,'outputs':outputs,'checks_sha256':sha(out/'checks.json'),'elapsed_seconds':time.monotonic()-start,'python':platform.python_version(),'cadquery':cq.__version__,'status':'geometry checked; slicing and review separate'}
    (out/'manifest.json').write_text(json.dumps(record,indent=2)+'\n')
    print(json.dumps({'parts':len(parts),'clearance_cases':report['clearance_cases'],'seconds':record['elapsed_seconds'],'output':str(out)},indent=2),flush=True)

if __name__=='__main__':main()
