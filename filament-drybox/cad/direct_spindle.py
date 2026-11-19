"""Approved asymmetric journals and unchanged spool clamping faces, one printed axle."""
import copy,math
import spindle as sp
from direct_interfaces import one

def build(c):
    left=copy.deepcopy(c);right=copy.deepcopy(c)
    right['axle']['shoulder_end_x']-=3.4
    right['axle']['thrust_face_x']-=3.4
    a=right['axle'];s=c['spindle'];t=s['thread'];y=c['bearings']['axis_y']
    male,_,_=sp.thread_profiles(t)
    shaft=sp._cyl(s['shaft_radius'],t['boss_x'][1]-.5,s['drive_arm_x'][0]+.5,y)
    boss=sp._cyl(t['root_radius'],-left['axle']['shoulder_end_x'],t['boss_x'][1],y)
    tooth=sp._helical(male,t['pitch'],*t['thread_x'],t['phase_x'],y,t['hand']=='left')
    hub=sp._cyl(a['shoulder_radius'],s['drive_arm_x'][0],a['shoulder_end_x']-a['shoulder_length']+.1,y)
    xb=t['boss_x'][1];run=(t['root_radius']-s['shaft_radius'])/math.tan(math.radians(s['boss_ramp_angle_deg']));ri=s['shaft_radius']-.5
    ramp=sp._revolve([(xb-.1,ri),(xb-.1,t['root_radius']-.1),(xb,t['root_radius']),(xb+run,s['shaft_radius']),(xb+run+.1,ri)],y)
    body=sp._join([sp._journal(right,1),sp._journal(left,-1),shaft,boss,tooth,hub,ramp,sp._cone_ring(s,y,1),*sp._spider(s,y,1,s['drive_arm_x'],a['shoulder_radius'])],'direct spindle')
    k=s['lock'];step=360/k['slot_count'];phase=k['key_angle_deg']%step
    for i in range(k['slot_count']):
        body=body.cut(sp._radial_box(t['thread_x'][0]-.2,t['thread_x'][1]+.2,k['slot_floor_radius']+.01,t['major_radius']+.5,k['slot_width'],phase+i*step,y))
    return one(body,'direct spindle')
