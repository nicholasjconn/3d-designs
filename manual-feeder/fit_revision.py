"""Locate the lid outside its seal and constrain the existing 608 insert."""
import numpy as np


def refine_fit(tray, lid, shapes, loft, track, yz_prism, box, cylinder, seam):
    def mirrored(part):
        return part + part.rotate([0, 0, 180])

    pin_xy = np.array([19.4, 21.35])
    slot_axis = pin_xy / np.linalg.norm(pin_xy)

    def position(part):
        return part.translate([*pin_xy, 0])

    # One round seat locates X/Y. The opposite seat is long only in the
    # direction between the pins so it can tolerate differences in shrinkage.
    stand = (
        cylinder(2.55,-2.75,-2.60).translate([pin_xy[0],16.85,0]) +
        position(cylinder(3.42,seam-.15,seam))
    ).hull()
    gland_keepout = loft([(2.55,*track(2.35)),(seam+.1,*track(2.35))])
    pin = position(cylinder(1.68,seam-.43,6.58)+cylinder(1.68,6.56,7.56,1.14))
    tray += mirrored((stand - gland_keepout) + pin)

    pocket_shell = cylinder(3.50,seam,8.46) + cylinder(3.50,8.44,10.18,1.80)
    bore = cylinder(1.86,seam-.15,7.81)
    bore += cylinder(2.20,seam-.14,5.18,1.86)
    bore += cylinder(1.86,7.78,9.59,.10)
    travel = [*(.36*slot_axis),0]
    slot = (bore.translate(travel)+bore.translate([-v for v in travel])).hull()
    lid += position(pocket_shell-bore)
    lid += position(pocket_shell-slot).rotate([0,0,180])

    # Tighten the guides around the two diagonal tongues on the current
    # insert. The cheeks leave an unobstructed channel for each snap finger.
    cheek_profile = [(11.9,-17.0),(14.71,-17.0),(14.71,2.92),
                     (7.55,2.92),(7.34,2.52),(7.34,-12.8)]
    cheeks = (yz_prism(cheek_profile,9.86,10.43)+
              yz_prism(cheek_profile,14.77,15.32))
    upper_lead = box(10.21,7.15,1.91,10.42,14.85,3.28)
    upper_lead += box(14.78,7.15,1.91,14.99,14.85,3.28)
    cheeks -= upper_lead
    shoulders = box(9.91,10.87,-13.30,11.08,14.67,1.85)
    shoulders += box(14.12,10.87,-13.30,15.52,14.67,1.85)
    tray += mirrored(cheeks+shoulders)

    # Register only the bottom of each rectangular foot, below the
    # wider curved cheeks of the 608 mount.
    foot_pocket = loft([(-30.57,9.48,2.96,.16),(-29.98,9.48,2.96,.16),
                        (-29.28,10.46,3.96,.47)]).translate([0,5.65,0])
    foot = box(-6.02,2.78,-32.45,6.02,8.55,-29.38)-foot_pocket
    tray += foot + foot.mirror([0,1,0])

    root = [(9.98+.9*np.cos(a),-20.6+.9*np.sin(a)) for a in np.linspace(-np.pi/2,0,10)]
    back = [(13.31-.9*np.cos(a),-20.6+.9*np.sin(a)) for a in np.linspace(0,-np.pi/2,10)]
    nose_z = -7.63
    blade = yz_prism(root+[(10.88,-8.76),(10.10,nose_z),(10.93,-6.24),
                          (10.95,-5.42),(12.06,-5.42)]+back+
                     [(13.45,-21.68),(9.98,-21.68)],11.25,13.95)
    return tray, lid, mirrored(blade)


def fit_audit(before, after, frame, box, seam):
    """Measure centered travel and straight-pull interference in both CAD revisions."""
    def overlap(a,b):
        return abs((a ^ b).volume())

    def limit(moving, fixed, pose, upper):
        if overlap(pose(moving,upper),fixed) < .003:
            return f">={upper:g}"
        lo,hi=0.,upper
        for _ in range(12):
            mid=(lo+hi)/2
            if overlap(pose(moving,mid),fixed) < .003:
                lo=mid
            else:
                hi=mid
        return round(lo,3)

    out = {}
    for name,(tray,lid,fingers,closed) in (("before",before),("after",after)):
        # Remove far-away thread triangles before measuring the near-rim fit.
        rim = tray ^ box(-42,-40,seam-.02,42,40,13)
        active_lid = lid ^ box(-40,-36,seam-.03,40,36,13)
        travel = {}
        for state, fixed, lift in (
            ("unlatched",rim,.54),
            # The extra 0.1 mm at the cam is working compliance, letting
            # the probe measure sideways capture independently of squeeze.
            ("latched",rim+closed.translate([0,0,.10]),0.),
        ):
            travel[state] = [
                round(sum(lim),3) if all(isinstance(v,(int,float)) for v in lim) else lim
                for axis in (0,1)
                for lim in [[limit(active_lid,fixed,
                    lambda part,t: part.translate([sign*t if axis==0 else 0,
                                                   sign*t if axis==1 else 0,lift]),5.)
                    for sign in (-1,1)]]
            ]
        guides = tray ^ box(-22.5,-15.5,-32.22,22.5,15.5,4.50)
        body = frame ^ box(-22,-14,-31,22,14,16)
        moves = {}
        for axis, label in ((2,"yaw"),(0,"roll"),(1,"pitch")):
            moves[label] = [
                limit(body,guides,lambda part,t: part.rotate([sign*t if j==axis else 0
                      for j in range(3)]),5.)
                for sign in (-1,1)
            ]
        snap = [(round(float(z),3),overlap(body.translate([0,0,z]),fingers))
                for z in np.linspace(0,5,51)]
        interference = body ^ guides
        out[name] = {
            "lid_total_sideways_travel_xy_mm":travel,
            "insert_total_sideways_travel_xy_mm":[round(sum(limit(
                body,guides,lambda part,t: part.translate(
                    [sign*t if axis==0 else 0,sign*t if axis==1 else 0,0]),2.)
                for sign in (-1,1)),3) for axis in (0,1)],
            "centered_insert_rotation_by_direction_deg":moves,
            "first_rigid_detent_contact_on_lift_mm":next(
                (z for z,hit in snap if hit>.005),None),
            "straight_lift_snap_peak_rigid_intersection_mm3":round(max(hit for z,hit in snap),4),
            "nominal_insert_fixed_collision_mm3":round(abs(interference.volume()),5),
            "seated_interference_bounds":[[round(v,3) for v in part.bounding_box()]
                for part in interference.decompose() if abs(part.volume())>.005],
            "nominal_insert_finger_collision_mm3":round(overlap(body,fingers),5),
        }
        # A rotated pull is more revealing than a perfectly straight one.
        # Probe near each seated yaw stop before lifting the frame.
        rotated_pulls = []
        for sign,stop in zip((-1,1),moves["yaw"]):
            if not isinstance(stop,(int,float)):
                continue
            angle=.95*sign*stop
            rotated=body.rotate([0,0,angle])
            poses=[rotated.translate([0,0,z]) for z in np.linspace(0,4,33)]
            rotated_pulls.append({
                "yaw_deg":round(angle,3),
                "rigid_guide_peak_mm3":round(max(overlap(p,guides) for p in poses),5),
                "detent_peak_mm3":round(max(overlap(p,fingers) for p in poses),5),
            })
        out[name]["near_yaw_stop_pull"] = rotated_pulls
        if name=="after":
            result = out[name]
            result["fixed_guide_lift_collision_mm3"] = round(max(overlap(body.translate([0,0,z]),guides)
                for z in np.linspace(0,35,141)),5)
            travel_max = .9
            nose = -7.63
            def flex(shift):
                def deflect(p):
                    x,y,z=p
                    ratio=max(0.,min(1.,(z+21.50)/(nose+21.50)))
                    return x,y+np.sign(y)*shift*.5*ratio*ratio*(3-ratio),z
                return fingers.warp(deflect)
            result["finger_wall_collision_at_0_9_mm3"] = round(overlap(
                flex(travel_max)^box(-20.,-18.,-19.9,20.,18.,4.),guides),5)
            result["peak_required_snap_flex_mm"] = 0.
            result["seated_snap_preload_displacement_mm"] = 0.
            for z, hit in snap:
                if hit<=.005:
                    continue
                moving = body.translate([0,0,z])
                if overlap(flex(travel_max),moving)>.005:
                    raise ValueError("The detent cannot clear the insert within its allowed travel")
                low,high=0.,travel_max
                for _ in range(10):
                    mid=(low+high)/2
                    if overlap(flex(mid),moving)>.005:
                        low=mid
                    else:
                        high=mid
                result["peak_required_snap_flex_mm"] = max(result["peak_required_snap_flex_mm"],round(high,3))
                if z == 0:
                    result["seated_snap_preload_displacement_mm"] = round(high,3)
    return out
