"""Stationary screw cap with closed end and static18x2 O-ring shoulder."""
import math
from direct_interfaces import cyl,tooth,thread_profiles,one

def build(c):
    p=c['port'];a,b=p['cap_x'];_,female,bore=thread_profiles(p['thread_profile'])
    s=cyl(14,a,b).cut(cyl(bore,a-.1,a+4))
    s=s.cut(tooth(c,female,a-.1,a+3.8,a))
    for i in range(12):
        s=s.fuse(cyl(.65,a+1.2,a+4.9).translate((0,13.8*math.cos(i*math.tau/12),13.8*math.sin(i*math.tau/12))))
    return one(s,'sealing cap')
