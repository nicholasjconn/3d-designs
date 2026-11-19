"""Original drybox clip: captured pin hinge, rigid upper jaw and compliant click latch.

Independently authored CadQuery geometry. No downloaded mesh is loaded or
transformed. This is a fit prototype; physical grip and hinge function are
unqualified. All dimensions are millimetres. See OUTLET-PRINTING.md.
"""
from pathlib import Path
import argparse
import json
import math
import cadquery as cq
from cad_helpers import absolute_tessellation
DEFAULT_CONFIG = Path(__file__).with_suffix('.json')
DEFAULT_OUTPUT = Path(__file__).resolve().parents[2]/'build/filament-drybox/clip'

def load_config(path=DEFAULT_CONFIG):
    c=json.loads(Path(path).read_text())
    outlet=json.loads(Path(__file__).with_name('outlet.json').read_text())
    for actual,expected,label in [
        (c['axial_height_mm'],outlet['tail']['clip_height_mm'],'clip height'),
        (c['filament_diameter_mm'],outlet['tail']['filament_diameter_mm'],'filament diameter')]:
        if abs(actual-expected)>1e-9:
            raise ValueError(f"Clip/outlet {label} mismatch: {actual} vs {expected}")
    return c

def build(c):
    H=c['axial_height_mm'];PX=c['hinge_x_mm'];PIN=c['pin_radius_mm']
    BORE=PIN+c['pin_radial_clearance_mm'];RING=c['fixed_knuckle_radius_mm'];HUB=c['moving_knuckle_radius_mm']
    knuckle=c['end_knuckle_height_mm'];axial_gap=c['axial_hinge_clearance_mm']
    def prism(points,z=0,h=None,r=0):
        h=H if h is None else h
        s=cq.Workplane('XY').polyline(points).close().extrude(h).val()
        if r:s=cq.Workplane(obj=s).edges('|Z').fillet(r).val()
        return s.translate((0,0,z))
    def rect(x0,x1,y0,y1,z=0,h=None,r=0):return prism([(x0,y0),(x1,y0),(x1,y1),(x0,y1)],z,h,r)
    def cyl(x,y,r,z0=0,z1=None):
        z1=H if z1 is None else z1
        return cq.Solid.makeCylinder(r,z1-z0,cq.Vector(x,y,z0))
    def fuse(*ss):
        s=ss[0]
        for q in ss[1:]:s=s.fuse(q)
        return s.clean()
    def ring(z0,z1):return cyl(PX,0,RING,z0,z1).cut(cyl(PX,0,BORE,z0-.1,z1+.1)).clean()
    def sector(ri,ro,a0,a1,z,h):
        a0,a1=map(math.radians,[a0,a1]);mid=(a0+a1)/2
        pt=lambda r,a:(PX+r*math.cos(a),r*math.sin(a))
        w=cq.Workplane('XY').moveTo(*pt(ro,a0)).threePointArc(pt(ro,mid),pt(ro,a1)).lineTo(*pt(ri,a1)).threePointArc(pt(ri,mid),pt(ri,a0)).close()
        return w.extrude(h).val().translate((0,0,z))
    # Broad lower jaw, two end knuckles and a lower spine are a single solid.
    body=fuse(rect(-4.65,4.65,-4.2,-.1,r=.45),rect(-7.3,-3.8,-3.0,-2.05,r=.3),ring(0,knuckle),ring(H-knuckle,H),sector(HUB+.25,RING,180,360,knuckle,H-2*knuckle))
    body=body.cut(cyl(0,0,c["seat_radius_mm"],-.1,H+.1)).clean()
    body=body.cut(rect(3.82,7,-4.5,-2.55,h=H)).clean()
    # Catch has a flat retaining underside. The jaw faces set the closing stop.
    catch=prism([(3.9,-.6),(4.55,-.6),(5.35,-1.85),(5.35,-2.55),(3.9,-2.55)],r=.06)
    body = fuse(body, catch)
    # One smooth upper frame joins the rigid jaw to the outside latch root.
    frame=prism([(-4.65,.15),(-4.65,2.0),(-3.8,3.6),(.3,6.9),(1.8,7.1),(1.8,5.75),(.2,4.85),(-2.8,2.8),(-3.7,1.8),(-3.7,.15)],r=.2)

    # A single flat face closes against the fixed jaw. Only the rounded
    # filament groove interrupts the grip surface.
    jaw = rect(*c["moving_jaw_x_mm"], -.10, 1.8, r=.12)
    jaw = jaw.cut(cyl(0, c["unloaded_grip_gap_mm"] - 2 * c["seat_radius_mm"],
                      c["seat_radius_mm"], -.1, H+.1)).clean()
    # Brace the gripping bar to the rigid diagonal frame, with clearance
    # between this web and the separate free span of the curved latch.
    web = prism([(-4.25,1.30),(3.23,1.30),(3.23,4.10),(2.12,5.32),
                 (0.55,5.41),(-3.72,2.53)],r=.16)
    # Middle knuckle stem; full-height frame remains outside the fixed end rings.
    stem=rect(PX,-4.4,.1,1.15,z=knuckle+axial_gap,h=H-2*(knuckle+axial_gap),r=.15)
    hub=cyl(PX,0,HUB,knuckle+axial_gap,H-knuckle-axial_gap);pin=cyl(PX,0,PIN)
    # A curved latch spring gains length within the cap envelope. Its positive
    # hook has 0.10 mm nominal clearance against the catch at the empty stop.
    # The full-height latch shares the first-layer plane with the gate.
    def latch_arc():
        cx,cy=.8,.1;ro=c["latch_outer_radius_mm"];ri=ro-c["latch_thickness_mm"];rt=math.sqrt(.5)
        return cq.Workplane('XY').moveTo(cx+ro,cy).threePointArc((cx+ro*rt,cy+ro*rt),(cx,cy+ro)).lineTo(cx,cy+ri).threePointArc((cx+ri*rt,cy+ri*rt),(cx+ri,cy)).close().extrude(H).val()
    arm=fuse(latch_arc(),rect(.8+c["latch_outer_radius_mm"]-c["latch_thickness_mm"],.8+c["latch_outer_radius_mm"],-3.45,.3,r=.1))
    # A blunt lip has full 1 mm backing beneath its retaining flat. The 0.7 mm
    # nose and R0.15 corners replace the fragile pointed triangular underside.
    hook=prism([(3.98,-2.65),(8.25,-2.65),(8.6,-2.95),(8.6,-3.4),(8.25,-3.65),(3.98,-3.65)],r=.15)

    rigid = fuse(frame,jaw,web,stem,hub,pin)
    gate = fuse(rigid,arm,hook)
    # Datum is the straight nominal filament, seated against the rigid cradle.
    dy=c['seat_radius_mm']-c['filament_diameter_mm']/2
    return {'fixed':body.translate((0,dy,0)), 'gate':gate.translate((0,dy,0))}

def export(c,output):
    output=Path(output);output.mkdir(parents=True,exist_ok=True)
    parts=build(c)
    dy=c['seat_radius_mm']-c['filament_diameter_mm']/2
    pivot=(c['hinge_x_mm'],dy,0)
    poses={
        'closed':parts,
        'open':{'fixed':parts['fixed'], 'gate':parts['gate'].rotate(pivot,(pivot[0],pivot[1],1),c['opening_angle_deg'])},
        'separated':{'fixed':parts['fixed'].translate((11,0,0)), 'gate':parts['gate'].translate((-11,0,0))}
    }
    payload=[]
    for name,part in parts.items():
        if not part.isValid() or len(part.Solids())!=1:
            raise ValueError(f"{name} must be one valid solid")
        cq.exporters.export(part,str(output/(name+'.step')))
        meshes={}
        for pose,pp in poses.items():
            v,f=absolute_tessellation(pp[name],tolerance=.025,angular_tolerance=.15)
            meshes[pose]={'vertices':[[round(x,6) for x in p.toTuple()] for p in v],'triangles':f}
        payload.append({'id':name,'name':{'fixed':'Fixed jaw and captured hinge','gate':'Rigid moving jaw and flexible latch'}[name],
                        'color':{'fixed':'#91b9d9','gate':'#4283bc'}[name],'meshes':meshes})
    (output/'geometry.json').write_text(json.dumps({'parts':payload},separators=(',',':')))
    # The open assembly preserves the two solids at their print-in-place spacing.
    for pose in ['closed','open']:
        cq.exporters.export(cq.Compound.makeCompound(list(poses[pose].values())),str(output/('clip-'+pose+'.step')))
    report={'status':c['status'],'valid_solids':{n:p.isValid() for n,p in parts.items()},
            'part_volumes_mm3':{n:p.Volume() for n,p in parts.items()},
            'closed_part_intersection_mm3':sum(s.Volume() for s in parts['fixed'].intersect(parts['gate']).Solids()),
            'filament_datum_y_translation_mm':dy,'fabrication_approved':False,
            'closed_pose':'Empty closed stop; the rigid jaw opens slightly on filament and the outer latch must elastically deform to engage.'}
    (output/'checks.json').write_text(json.dumps(report,indent=2))
    return report

if __name__=='__main__':
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--config',type=Path,default=DEFAULT_CONFIG)
    ap.add_argument('--output',type=Path,default=DEFAULT_OUTPUT)
    args=ap.parse_args()
    print(json.dumps(export(load_config(args.config),args.output),indent=2))
