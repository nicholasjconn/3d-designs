# SUPERSEDED 17 Nov 2026: high-flow center cartridge, replaced by the spindle and locking collar
# (spindle.py / stand.json). Kept for history; not a current print input. See ../README.md.
"""Recess the reference cartridge around unchanged 608-bearing carriers."""
from pathlib import Path
import argparse,hashlib,shutil
import zipfile,xml.etree.ElementTree as E,json
import numpy as np,trimesh
parser=argparse.ArgumentParser(description=__doc__)
parser.add_argument('--reference',type=Path,required=True)
parser.add_argument('--journals',type=Path,required=True)
parser.add_argument('--output',type=Path,required=True)
args=parser.parse_args()
expected='17824efad742bb14502ec6c657f2af500d2a5dc4d0475cabdd03bf9c760447b9'
if hashlib.sha256(args.reference.read_bytes()).hexdigest()!=expected:
 raise ValueError('Reference differs from reviewed Bambu Standard Mesh archive')
P=args.output.resolve();P.mkdir(parents=True,exist_ok=False)
for name in ['body-journal','cap-journal','body-wall','body-floor','cap-wall','cap-floor']:
 shutil.copy2(args.journals/(name+'.stl'),P/(name+'.stl'))
N={'m':'http://schemas.microsoft.com/3dmanufacturing/core/2015/02'}
NS=N['m'];PROD='{http://schemas.microsoft.com/3dmanufacturing/production/2015/06}'
E.register_namespace('',NS);E.register_namespace('p',PROD[1:-1])
z=zipfile.ZipFile(args.reference);root=E.fromstring(z.read('3D/3dmodel.model'));conf=E.fromstring(z.read('Metadata/model_settings.config'));resources=root.find('m:resources',N);objects={o.attrib['id']:o for o in resources.findall('m:object',N)};builds={o.attrib['objectid']:o for o in root.findall('m:build/m:item',N)};replacements={};display=[];notes={}

def part(c):
 path=c.attrib[PROD+'path'].lstrip('/');doc=E.fromstring(replacements.get(path,z.read(path)));o=next(o for o in doc.findall('m:resources/m:object',N)if o.attrib['id']==c.attrib['objectid']);m=o.find('m:mesh',N);v=np.array([[float(v.attrib[k])for k in 'xyz']for v in m.findall('m:vertices/m:vertex',N)]);f=np.array([[int(f.attrib[k])for k in ['v1','v2','v3']]for f in m.findall('m:triangles/m:triangle',N)]);t=np.array(list(map(float,c.attrib['transform'].split()))).reshape(4,3)
 return path,doc,o,trimesh.Trimesh(v@t[:3]+t[3],f,process=False)

def replace(c,path,doc,o,m):
 if not m.is_watertight:raise ValueError('Nonwatertight '+path)
 o.remove(o.find('m:mesh',N));el=E.SubElement(o,'{'+NS+'}mesh');vs=E.SubElement(el,'{'+NS+'}vertices');fs=E.SubElement(el,'{'+NS+'}triangles')
 for v in m.vertices:E.SubElement(vs,'{'+NS+'}vertex',{k:format(float(a),'.9g')for k,a in zip('xyz',v)})
 for f in m.faces:E.SubElement(fs,'{'+NS+'}triangle',{k:str(a)for k,a in zip(['v1','v2','v3'],f)})
 c.set('transform','1 0 0 0 1 0 0 0 1 0 0 0');replacements[path]=E.tostring(doc,encoding='utf-8',xml_declaration=True)

def cy(r,za,zb):
 m=trimesh.creation.cylinder(radius=r,height=zb-za,sections=256);m.apply_translation([0,0,(za+zb)/2]);return m

def load(name,horizontal=False):
 m=trimesh.load_mesh(P/(name+'.stl'))
 if horizontal:
  v=m.vertices.copy();m.vertices=np.column_stack((v[:,2],v[:,1]-104,34-v[:,0]))
 return m

def difference(a,*b):return trimesh.boolean.difference([a,*b],engine='manifold')
def union(*ms):return trimesh.boolean.union(ms,engine='manifold')

for oid,name,off,mid in [('4','body',32.5,'3'),('15','locking-ring',61.5,None),('19','refill-cap',64,'18')]:
 cs=objects[oid].findall('m:components/m:component',N);c=next(c for c in cs if c.attrib['objectid']in ['1','13','17']);path,doc,o,original=part(c);original.apply_translation([0,0,off]);guards=[]
 if name!='locking-ring':
  prefix='body'if name=='body'else'cap';journal=load(prefix+'-journal',True);wall=load(prefix+'-wall');floor=load(prefix+'-floor');cut=cy(15.2,-20,7)if name=='body'else cy(15.2,61,90)
  cut_original=difference(original,cut);reinforcement=union(journal,wall)
  result=union(cut_original,reinforcement,floor)
  attachment=trimesh.boolean.intersection([reinforcement,cut_original],engine='manifold')
  print(name,'original-to-added overlap',attachment.volume,'watertight',result.is_watertight,flush=True)
  local=result.copy();local.apply_translation([0,0,-off]);replace(c,path,doc,o,local)
  meshc=next(c for c in cs if c.attrib['objectid']==mid);mp,md,mo,mesh=part(meshc);mesh.apply_translation([0,0,off]);mesh=difference(mesh,cut,reinforcement)
  # Apply Standard Mesh only to NEW floor volume; preserve reference walls.
  newmesh=difference(floor,original,reinforcement)
  mesh=union(mesh,newmesh);local=mesh.copy();local.apply_translation([0,0,-off]);replace(meshc,mp,md,mo,local);guards=[mesh]
  notes[name]={'attachment_overlap_mm3':float(attachment.volume),'removed_original_mm3':float(original.volume-cut_original.volume),'adapted_volume_mm3':float(result.volume),'original_volume_mm3':float(original.volume),'pocket_radius_mm':15.2,'pocket_end_source_z_mm':7 if name=='body' else 61}
  # End-only edits: actual reference remains identical between Z10.2..58.
 else:result=original
 result.export(P/(name+'-adapted.stl'));np.savez_compressed(P/(name+'-adapted.npz'),vertices=result.vertices,faces=result.faces)
 t=np.array(list(map(float,builds[oid].attrib['transform'].split()))).reshape(4,3);notes.setdefault(name,{}).update({'object_id':oid,'source_offset_z':off,'original_build_transform':t.tolist(),'bounds':result.bounds.tolist(),'watertight':bool(result.is_watertight)})
for o in list(resources):
 if o.tag.endswith('object')and o.attrib['id']not in ['4','15','19']:resources.remove(o)
build=root.find('m:build',N)
for o in list(build):
 if o.attrib['objectid']not in ['4','15','19']:build.remove(o)
for o in list(conf):
 if o.tag=='object'and o.attrib['id']not in ['4','15','19']:conf.remove(o)
 if o.tag=='plate'and o!=conf.findall('plate')[0]:conf.remove(o)
 if o.tag=='assemble':conf.remove(o)
for oid,extension in [('4',9.2),('19',2.2)]:
 t=builds[oid].attrib['transform'].split();t[-1]=str(float(t[-1])+extension);builds[oid].set('transform',' '.join(t))
replacements['3D/3dmodel.model']=E.tostring(root,encoding='utf-8',xml_declaration=True);replacements['Metadata/model_settings.config']=E.tostring(conf,encoding='utf-8',xml_declaration=True)
with zipfile.ZipFile(P/'high-flow-standard-recessed-concept.3mf','w',zipfile.ZIP_DEFLATED)as out:
 for name in z.namelist():
  if name.endswith('.gcode')or name.startswith('Metadata/plate_')or name.startswith('Metadata/top_')or name.startswith('Metadata/pick_'):continue
  out.writestr(name,replacements.get(name,z.read(name)))
(P/'adaptation.json').write_text(json.dumps(notes,indent=2));print('private recessed concept saved',flush=True)
