"""Stationary threaded wall fitting, unchanged from the prior prototype."""
from direct_interfaces import cyl,tube,tooth,thread_profiles,one

def build(c):
    p=c['port'];a=p['fitting_tip_x'];b,d=p['fitting_flange_x'];e=p['fitting_end_x']
    male,_,_=thread_profiles(p['thread_profile'])
    s=cyl(8.3,a,e).fuse(cyl(16,b,d),tooth(c,male,a,b,a),tooth(c,male,d,e,d))
    s=s.cut(cyl(p['bore_radius'],a-.1,e+.1))
    return one(s.cut(tube(13.3,10.7,*p['wall_groove_x'])).cut(tube(11.3,8.7,*p['cap_groove_x'])),'wall fitting')
