#!/usr/bin/env python3
"""Actual deposition-layer evidence for critical fit surfaces; never changes a slice."""
from pathlib import Path
import argparse,json,collections
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.collections import LineCollection
from direct_toolpaths import grouped_paths
from stand_print import sha


def main():
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--print-input',type=Path,required=True);ap.add_argument('--engineering-root',type=Path,required=True);ap.add_argument('--output',type=Path,required=True);a=ap.parse_args();a.output.mkdir(exist_ok=True,parents=True)
    parts,roads,gcode=grouped_paths(a.print_input,a.engineering_root);parts={p['id']:p for p in parts};rows=[]
    cases=[('right-carrier',12.2,'Drive carrier: first bearing-stop ledge'),('left-carrier',8.8,'Left carrier: first bearing-stop ledge'),('crank',.2,'Crank: first layer and brim'),('crank',38.0,'Crank: socket wall loops'),('inside-nut',2.0,'Nut: printed female thread'),('stand',104,'Stand: open nut channel and guide tongue')]
    fig,axes=plt.subplots(3,2,figsize=(12,14),layout='constrained')
    palette={'Outer wall':'#245b85','Inner wall':'#338cb6','Bridge':'#d67e1d','Overhang wall':'#90663b','Brim':'#9b8b67','Support':'#b6b5a5','Support interface':'#a7a06d','Support transition':'#b9ad83'}
    for axis,(name,target,title) in zip(axes.flat,cases):
        p=parts[name];layers=sorted(set(r['z'] for r in roads[name]));z=min(layers,key=lambda v:abs(v-target));previous=max([v for v in layers if v<z-.001],default=None)
        current=[r for r in roads[name] if abs(r['z']-z)<.001];prev=[r for r in roads[name] if previous is not None and abs(r['z']-previous)<.001]
        if name=='stand':
            # Native drive-side guide at Z=+-13 and flange channel atZ=+-16.5.
            region=[116.8,125,82,128]
        else:
            b=p['bbox_bed_mm'];region=[b['min'][0]-2,b['max'][0]+2,b['min'][1]-2,b['max'][1]+2]
        for rr,color,alpha in [(prev,'#c4cbd0',.7),(current,None,1)]:
            for feature in sorted(set(r['feature'] for r in rr)):
                select=[r for r in rr if r['feature']==feature]
                lines=[[r['p'],r['q']] for r in select]
                axis.add_collection(LineCollection(lines,colors=color or palette.get(feature,'#5f8d60'),linewidths=[r['width']*2 for r in select],alpha=alpha,label=feature if color is None else None))
        axis.set(xlim=region[:2],ylim=region[2:],aspect='equal',title=f'{title}\nZ={z:.2f} mm; prior layer gray',xlabel='Plate X (mm)',ylabel='Plate Y (mm)');axis.grid(alpha=.15)
        chains=collections.defaultdict(list)
        for r in current:
            if r['feature'] in ['Inner wall','Outer wall','Overhang wall']:chains[(r['chain'],r['feature'])].append(r)
        closed=sum(np.linalg.norm(np.array(q[0]['p'])-q[-1]['q'])<.1 for q in chains.values())
        row={'part':name,'requested_layer_z_mm':target,'actual_layer_z_mm':z,'previous_layer_z_mm':previous,'feature_segments':dict(collections.Counter(r['feature'] for r in current)),'closed_wall_chains':int(closed)}
        if name=='stand':
            tr=np.array(p['native_to_bed']);rot=tr[:3,:3];shift=tr[:3,3];hits=0
            for r in current:
                if r['feature'].startswith('Support') or r['feature']=='Brim':continue
                aa=rot.T@(np.array([*r['p'],r['z']])-shift);bb=rot.T@(np.array([*r['q'],r['z']])-shift)
                # Strictly interior1.2mm axial strip inside the actual1.8mm flange channel,
                # at both side arcs (Z+-16.5) at the axle plane.
                for zz in [-16.5,16.5]:
                    q=np.array([41.1,zz]);va=aa[[0,2]];delta=bb[[0,2]]-va;t=np.clip((q-va)@delta/max(delta@delta,1e-20),0,1)
                    hits+=np.linalg.norm(q-va-t*delta)<r['width']/2
            row['deposition_segments_covering_open_channel_probes']=int(hits)
            if hits:raise ValueError('Stand flange channel closed by deposition')
        rows.append(row)
    handles,labels=axes.flat[0].get_legend_handles_labels();fig.suptitle('Current Bambu slice: actual toolpaths, millimetres',fontsize=16)
    fig.savefig(a.output/'critical-layers.png',dpi=150)
    for i in [0,1,3]:
        if rows[i]['closed_wall_chains']==0:raise ValueError('Missing wall loops: '+str(rows[i]))
    r={'gcode_sha256':sha(gcode),'source_sha256':{n:sha(Path(__file__).with_name(n)) for n in ['direct_layers.py','direct_toolpaths.py']},'scope':'Actual sliced layers and finite channel probes. Line display width is illustrative, measurements use logged bead widths. Not printed-surface or strength qualification. Bearing-stop ledges are1.4mm inward projections with no generated support; bridged/overhang roads must be cleaned and physically checked for a full608 seat.','cases':rows,'passed':True}
    (a.output/'critical-layers.json').write_text(json.dumps(r,indent=2)+'\n');print(json.dumps(r,indent=2))

if __name__=='__main__':main()
