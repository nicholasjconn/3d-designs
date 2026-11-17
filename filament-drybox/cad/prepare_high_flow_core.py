# SUPERSEDED 17 Nov 2026: high-flow center cartridge, replaced by the spindle and locking collar
# (spindle.py / stand.json). Kept for history; not a current print input. See ../README.md.
from pathlib import Path
import sys,json,zipfile,xml.etree.ElementTree as E,subprocess
import argparse
parser=argparse.ArgumentParser(description='Prepare unreleased H2D empty-fit core project; never sends a print')
parser.add_argument('--input',type=Path,required=True,help='Output directory from adapt_high_flow_core.py')
parser.add_argument('--output',type=Path,required=True)
parser.add_argument('--engineering-root',type=Path,required=True)
args=parser.parse_args()
P=args.output.resolve();P.mkdir(parents=True,exist_ok=False)
ENGINE=args.engineering_root.resolve();sys.path.insert(0,str(ENGINE))
from systems.test_fixture.manufacturing.factory import load_factory
BIN=Path('/Applications/BambuStudio.app/Contents/MacOS/BambuStudio')
recipe={'studio_version':'02.09.01.70','presets':{'machine':'Bambu Lab H2D 0.4 nozzle','process':'0.20mm Standard @BBL H2D','filament':'Bambu PLA Basic @BBL H2D'},'plate':'Textured PEI Plate','filament_map':'2'}
if not (P/'factory').exists(): profiles,record=load_factory(BIN,recipe,P/'factory')
else: profiles={k:json.loads((P/'factory/resolved'/f'{k}.json').read_text())for k in ['machine','process','filament']}
NS='http://schemas.microsoft.com/3dmanufacturing/core/2015/02';N={'m':NS};E.register_namespace('',NS);E.register_namespace('p','http://schemas.microsoft.com/3dmanufacturing/production/2015/06')
source=args.input.resolve()/'high-flow-standard-recessed-concept.3mf'
for kind in ['core-fit-proposal']:
 d=P/kind;d.mkdir(exist_ok=True)
 proc=dict(profiles['process'])
 proc['enable_support']='1'
 proc['support_critical_regions_only']='1'
 (d/'process.json').write_text(json.dumps(proc,indent=2))
 with zipfile.ZipFile(source)as z:
  model=E.fromstring(z.read('3D/3dmodel.model'));settings=E.fromstring(z.read('Metadata/model_settings.config'))
  for it in model.findall('m:build/m:item',N):
   oid=it.attrib['objectid'];x={'4':85,'15':165,'19':240}[oid]
   if oid=='4':tr=[1,0,0,0,-1,0,0,0,-1,x,110,32.5]
   elif oid=='15':tr=[1,0,0,0,-1,0,0,0,-1,x,110,6.5]
   else:tr=[1,0,0,0,1,0,0,0,1,x,110,6.2]
   it.set('transform',' '.join(map(str,tr)))
  for ob in settings.findall('object'):
   for meta in list(ob.findall('metadata')):
    # Retain author 4-wall structural shell and90deg mesh direction;
    # remove decorative surface/sequence overrides.
    if 'key'in meta.attrib and meta.attrib['key']not in ['name','extruder','wall_loops','infill_direction']:ob.remove(meta)
   for part in ob.findall('part'):
    for m in list(part.findall('metadata')):
     if m.attrib.get('key')=='sparse_infill_speed':part.remove(m)
  for plate in settings.findall('plate'):
   for me in plate.findall('metadata'):
    if me.attrib.get('key')=='plater_name':me.set('value','EMPTY core fit prototype — proposal')
  # Explicit support blockers in original local object coordinates.
  resources=model.find('m:resources',N)
  for oid,blockid,rad,lo,hi,off in [('4','301',24,-12,70,32.5),('19','302',16.6,55,75,64)]:
   count=128
   import math
   verts=[]
   for zz in [lo-off,hi-off]:
    verts.extend([(rad*math.cos(2*math.pi*i/count),rad*math.sin(2*math.pi*i/count),zz)for i in range(count)])
   verts.extend([(0,0,lo-off),(0,0,hi-off)])
   faces=[]
   for i in range(count):
    j=(i+1)%count
    faces.extend([(i,j,count+j),(i,count+j,count+i),(2*count,j,i),(2*count+1,count+i,count+j)])
   ob=E.SubElement(resources,'{'+NS+'}object',{'id':blockid,'type':'model'})
   mesh=E.SubElement(ob,'{'+NS+'}mesh');vs=E.SubElement(mesh,'{'+NS+'}vertices');fs=E.SubElement(mesh,'{'+NS+'}triangles')
   for v in verts:E.SubElement(vs,'{'+NS+'}vertex',{k:str(t)for k,t in zip('xyz',v)})
   for f in faces:E.SubElement(fs,'{'+NS+'}triangle',{k:str(t)for k,t in zip(['v1','v2','v3'],f)})
   owner=next(o for o in resources.findall('m:object',N)if o.attrib['id']==oid)
   E.SubElement(owner.find('m:components',N),'{'+NS+'}component',{'objectid':blockid,'transform':'1 0 0 0 1 0 0 0 1 0 0 0'})
   owner=next(o for o in settings.findall('object')if o.attrib['id']==oid)
   part=E.SubElement(owner,'part',{'id':blockid,'subtype':'support_blocker'})
   E.SubElement(part,'metadata',{'key':'name','value':'Keep interior clear — support blocker'})
  patch={'3D/3dmodel.model' :E.tostring(model,encoding='utf-8',xml_declaration=True),'Metadata/model_settings.config':E.tostring(settings,encoding='utf-8',xml_declaration=True)}
  dest=d/'candidate.3mf'
  with zipfile.ZipFile(dest,'w',zipfile.ZIP_DEFLATED)as out:
   for name in z.namelist():
    if name in ['Metadata/layer_config_ranges.xml','Metadata/cut_information.xml','Metadata/slice_info.config','Metadata/filament_sequence.json']:continue
    out.writestr(name,patch.get(name,z.read(name)))
 out=d/'slice';out.mkdir(exist_ok=True)
 args=[str(BIN),'--datadir',str(d/'data'),'--debug','2','--load-settings',str(P/'factory/resolved/machine.json')+';'+str(d/'process.json'),'--load-filaments',str(P/'factory/resolved/filament.json'),'--filament-map','2','--filament-map-mode','Manual','--filament-colour','#328665','--arrange','0','--orient','0','--slice','1','--export-settings',str(out/'settings.json'),'--export-3mf','core-fit-sliced.3mf','--outputdir',str(out),str(dest)]
 (d/'invocation.json').write_text(json.dumps(args,indent=2))
 with(d/'slice.log').open('w')as f:r=subprocess.run(args,stdout=f,stderr=subprocess.STDOUT)
 print(kind,'exit',r.returncode,flush=True)
 print((d/'slice.log').read_text()[-4500:],flush=True)
 if r.returncode:raise SystemExit(r.returncode)
