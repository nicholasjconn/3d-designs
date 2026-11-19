"""Compact inside nut with solid flange captured by the stand channel."""
from direct_interfaces import cyl,tooth,thread_profiles,one

def build(c):
    p=c['port'];a,b=p['nut_x'];_,female,bore=thread_profiles(p['thread_profile'])
    s=cyl(p['nut_body_radius'],a,b).cut(cyl(bore,a-.1,b+.1))
    s=s.cut(tooth(c,female,a-.1,b+.1,p['thread_phase_x']))
    flange=cyl(p['flange_radius'],a,a+p['flange_thickness']).cut(cyl(14,a-.1,a+p['flange_thickness']+.1))
    return one(s.fuse(flange),'inside nut')
