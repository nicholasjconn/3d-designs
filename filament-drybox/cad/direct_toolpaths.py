"""Decision-critical bead/support checks for the current direct-drive fit plate."""
from pathlib import Path
import bisect,json,xml.etree.ElementTree as ET,zipfile
import numpy as np

def grouped_paths(output,engineering_root):
    import sys
    sys.path.insert(0,str(Path(engineering_root).resolve()))
    from shared.manufacturing import read_paths
    from stand_print import sha
    out=Path(output);job=out/'direct-drive-fit';gcode=job/'out/plate_1.gcode'
    parts=json.loads((out/'plate-parts.json').read_text());ns={'m':'http://schemas.microsoft.com/3dmanufacturing/core/2015/02'}
    with zipfile.ZipFile(job/'direct-drive-fit.3mf') as z:
        model=ET.fromstring(z.read('3D/3dmodel.model'));settings=ET.fromstring(z.read('Metadata/model_settings.config'))
    labels={int(e.find("metadata[@key='identify_id']").attrib['value']):int(e.find("metadata[@key='object_id']").attrib['value']) for e in settings.findall('.//model_instance')}
    order=[int(e.attrib['objectid']) for e in model.find('m:build',ns)]
    label_parts={label:parts[order.index(obj)]['id'] for label,obj in labels.items()}
    transitions=[(i,label_parts[int(line.rsplit(' ',1)[-1])]) for i,line in enumerate(gcode.read_text().splitlines(),1) if line.startswith('; start printing object, unique label id: ')]
    ix=[i for i,n in transitions];group={p['id']:[] for p in parts}
    for road in read_paths(gcode,arc_step_mm=.2):
        if road['feature']=='Custom':continue
        k=bisect.bisect_right(ix,road['line'])-1
        if k<0:raise ValueError('Unassigned deposition')
        group[transitions[k][1]].append(road)
    return parts,group,gcode

def check(output,engineering_root):
    from stand_print import sha
    out=Path(output)
    parts,group,gcode=grouped_paths(output,engineering_root)
    # Check the channel-floor top skin, not an arbitrary point in permitted sparse infill.
    probes={'stand':[(43.1,87,0),(43.1,105,18),(43.1,105,-18),(38.8,100,13.1),(41,85.4,0)],
            'right-carrier':[(27.4,93,0)],'left-carrier':[(-30.8,93,0)],
            'inside-nut':[(41,104,16.2)],'crank':[(55,107.7,0)],
            'fitting':[(49,118.5,0)],'cap':[(57.2,104,0)]}
    results={};support_hits={}
    for p in parts:
        name=p['id'];tr=np.array(p['native_to_bed']);rot=tr[:3,:3];shift=tr[:3,3];roads=group[name]
        model=[r for r in roads if not r['feature'].startswith('Support') and r['feature']!='Brim']
        rows=[]
        for probe in probes.get(name,[]):
            bed=rot@np.array(probe)+shift;layer=min({r['z'] for r in model},key=lambda z:abs(z-bed[2]));best=float('inf')
            count=0
            for r in model:
                if abs(r['z']-layer)>.0001:continue
                a=np.array(r['p']);d=np.array(r['q'])-a;t=np.clip((bed[:2]-a)@d/(d@d),0,1)
                distance=float(np.linalg.norm(bed[:2]-a-t*d)-r['width']/2)
                if distance<best:best=distance
                if distance<.05:count+=1
            rows.append({'native_probe_mm':probe,'bed_layer_z':layer,'probe_layer_offset_mm':abs(layer-bed[2]),'nearest_bead_envelope_signed_distance_mm':best,'roads_within_0p05_mm':count})
        results[name]=rows
        if name=='crank':
            hits=[]
            for r in roads:
                if not r['feature'].startswith('Support'):continue
                a=rot.T@(np.array([*r['p'],r['z']])-shift);b=rot.T@(np.array([*r['q'],r['z']])-shift)
                # Exact interval along the road within working socket axial limits.
                dx=b[0]-a[0];lo,hi=0.,1.
                if abs(dx)<1e-12:
                    if not 35.4<a[0]<40.2:continue
                else:
                    u,v=sorted([(35.4-a[0])/dx,(40.2-a[0])/dx]);lo=max(lo,u);hi=min(hi,v)
                    if hi<lo:continue
                a,b=a+(b-a)*lo,a+(b-a)*hi;delta=b-a;rad=a[1:]-[104,0];d=delta[1:];t=np.clip(-rad@d/max(d@d,1e-20),0,1);v=rad+t*d
                if np.linalg.norm(v)-r['width']/2<4.15 and np.all(abs(v)-r['width']/2<3.35):hits.append(r['line'])
            support_hits[name]={'support_road_envelopes_intersecting_working_socket':len(hits),'gcode_lines':hits[:20]}
    # Conservative central working voids, independent of the thread tooth/seat profiles.
    voids={}
    for p in parts:
        name=p['id']
        if name not in ['inside-nut','left-carrier','right-carrier','crank','fitting','cap']:continue
        tr=np.array(p['native_to_bed']);rot=tr[:3,:3];shift=tr[:3,3]
        radius={'inside-nut':8.2,'left-carrier':9.5,'right-carrier':9.5,'crank':3.1,'fitting':4.9,'cap':8.2}[name]
        minimum=float('inf');hits=0
        for road in group[name]:
            if road['feature']=='Brim':continue
            aa=rot.T@(np.array([*road['p'],road['z']])-shift);bb=rot.T@(np.array([*road['q'],road['z']])-shift)
            if name=='crank' and not (35.8<aa[0]<39.9 and 35.8<bb[0]<39.9):continue
            if name=='cap' and not (51.7<aa[0]<55.3 and 51.7<bb[0]<55.3):continue
            v=aa[1:]-[104,0];delta=bb[1:]-aa[1:];t=np.clip(-v@delta/max(delta@delta,1e-20),0,1)
            edge=float(np.linalg.norm(v+t*delta)-road['width']/2);minimum=min(minimum,edge)
            hits+=edge<radius
        voids[name]={'checked_central_void_radius_mm':radius,'minimum_road_envelope_radius_mm':minimum,'intruding_model_or_support_segments':hits,'support_segments_total':sum(r['feature'].startswith('Support') for r in group[name])}
    report_void={'scope':'Current direct-drive central working voids. Conservative circular subregions only; thread-tooth accuracy and bearing-lip deposition are checked separately in saved layer evidence. The fitting through-bore is checked throughout; the cap working cavity is checked ahead of its deliberately closed end. Width/2 bead envelopes, not measured printed tolerance.', 'gcode_sha256':sha(gcode),'bores':voids}
    (out/'bore-bead-clearance.json').write_text(json.dumps(report_void,indent=2)+'\n')
    if any(row['intruding_model_or_support_segments'] for row in voids.values()):raise ValueError('Deposition blocks a central working void: '+str(voids))
    report={'gcode_sha256':sha(gcode),'scope':'Finite critical solid probes and complete support-road socket test; not exhaustive toolpath or printed-fit qualification. Bead width/2 used as a conservative radial envelope.', 'critical_solid_probes':results,'support_checks':support_hits}
    (out/'functional-toolpaths.json').write_text(json.dumps(report,indent=2)+'\n')
    if any(v['support_road_envelopes_intersecting_working_socket'] for v in support_hits.values()):raise ValueError('Support enters crank socket')
    missing=[(n,row) for n,rows in results.items() for row in rows if row['nearest_bead_envelope_signed_distance_mm']>.1]
    if missing:raise ValueError('Critical solid probe lacks deposition: '+str(missing))
    return report

if __name__=='__main__':
    import argparse
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--output',type=Path,required=True);ap.add_argument('--engineering-root',type=Path,required=True);a=ap.parse_args();r=check(a.output,a.engineering_root);print(json.dumps(r,indent=2))
