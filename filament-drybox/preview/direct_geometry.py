#!/usr/bin/env python3
"""Build the current native assembly and real print/support review page."""
from pathlib import Path
import argparse,json,shutil,sys,struct
import numpy as np
import cadquery as cq
CAD=Path(__file__).resolve().parents[1]/'cad';sys.path.insert(0,str(CAD))
from drybox import mesh,sha
from direct_interfaces import config
COLORS={'stand':'#929ca2','axle':'#328761','collar':'#8ab94d','inside-nut':'#df9141','fitting':'#c99838','cap':'#8c68b2','crank':'#3778bd','right-carrier':'#7e8c94','left-carrier':'#7e8c94','spool':'#ded2b5','wall':'#94bed0','left-bearing':'#b8bec6','right-bearing':'#b8bec6'}
NAMES={'stand':'Stand','axle':'Axle','collar':'Locking collar','inside-nut':'Inside nut','fitting':'Wall fitting','cap':'Storage cap','crank':'Removable crank','right-carrier':'Drive-side bearing carrier','left-carrier':'Left bearing carrier','spool':'Spool reference','wall':'Wall reference','left-bearing':'Left608','right-bearing':'Drive608'}
EXPLODE={'left-carrier':[-15,15,0],'left-bearing':[-8,10,0],'right-carrier':[5,25,0],'right-bearing':[8,10,0],'spool':[0,18,0],'collar':[-20,0,0],'axle':[0,18,0],'inside-nut':[5,25,0],'fitting':[18,0,0],'cap':[30,0,0],'crank':[45,0,0]}

def payload(q):
    t=q.to_mesh();return {'v':t.vert_properties[:,:3].tolist(),'f':t.tri_verts.tolist()}

def main():
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--native-input',type=Path,required=True);ap.add_argument('--print-input',type=Path,required=True);ap.add_argument('--output',type=Path,required=True);a=ap.parse_args();out=a.output.resolve();out.mkdir(parents=True,exist_ok=True)
    src=Path(__file__).with_name('direct-drive')
    for n in ['index.html','viewer.js']:shutil.copy2(src/n,out/n)
    vendor=Path(__file__).parent/'node_modules/three';(out/'vendor').mkdir(exist_ok=True)
    for x,y in [('build/three.module.js','three.module.js'),('examples/jsm/controls/OrbitControls.js','OrbitControls.js'),('examples/jsm/utils/BufferGeometryUtils.js','BufferGeometryUtils.js'),('LICENSE','THREE-LICENSE')]:
        if not (vendor/x).is_file():raise ValueError('Missing installed Three.js input: '+str(vendor/x))
        shutil.copy2(vendor/x,out/'vendor'/y)
    manifest=json.loads((a.native_input/'manifest.json').read_text());parts=[]
    for n,r in manifest['outputs'].items():
        path=a.native_input/r['file']
        if sha(path)!=r['sha256']:raise ValueError('Changed native part '+n)
        q=mesh(cq.importers.importStep(str(path)).val());cut=q.trim_by_plane([0,0,-1],0)
        parts.append({'id':n,'name':NAMES[n],'color':COLORS[n],'explode':EXPLODE.get(n,[0,0,0]),'whole':payload(q),'section':payload(cut)})
    (out/'geometry.json').write_text(json.dumps({'parts':parts,'checks':json.loads((a.native_input/'checks.json').read_text()),'source':manifest,'manifest_sha256':sha(a.native_input/'manifest.json')},separators=(',',':')))
    printparts=json.loads((a.print_input/'plate-parts.json').read_text());report=json.loads((a.print_input/'final-print-analysis.json').read_text());rows=[]
    for p in printparts:
        data=Path(p['stl']).read_bytes();count=struct.unpack_from('<I',data,80)[0];pts=np.array([struct.unpack_from('<12fH',data,84+i*50)[3:12] for i in range(count)]).reshape(-1,3);v,ix=np.unique(pts,axis=0,return_inverse=True);v[:,:2]+=p['placement_xy_mm']
        roads=json.loads((a.print_input/(p['id']+'-supports.json')).read_text())['segments'];stride=max(1,len(roads)//18000);lines=[];x,y=p['placement_xy_mm']
        for r in roads[::stride]:lines.extend([[r[0]+x,r[1]+y,r[2]],[r[3]+x,r[4]+y,r[5]]])
        rows.append({'id':p['id'],'name':NAMES[p['id']],'color':COLORS[p['id']],'orientation':p['orientation'],'useful_g':report['useful_part_g'][p['id']],'v':v.tolist(),'f':ix.reshape(-1,3).tolist(),'supports':lines})
    (out/'plate.json').write_text(json.dumps({'parts':rows,'report':{k:report[k] for k in ['estimate_seconds','slicer_total_g','useful_part_g','removed_g']}},separators=(',',':')))
    layers=a.print_input/'layers/critical-layers.png'
    if not layers.is_file():raise ValueError('Missing actual critical layer evidence: '+str(layers))
    shutil.copy2(layers,out/'critical-layers.png')
    for folder,name in [('', 'direct-drive-fit.3mf'),('out','direct-drive-fit-sliced.3mf')]:shutil.copy2(a.print_input/'direct-drive-fit'/folder/name,out/name)
    print('Private preview generated from canonical sources and exact fabrication inputs:',out)

if __name__=='__main__':main()
