"""Coaxial fitting socket and storage-cap threads in the feeder tray."""
import manifold3d as m
import numpy as np

from drybox_mount import mesh
from geometry import TUBE_Z, port, yz_prism

CAP_FACE = 30.30
FITTING_SEAT = CAP_FACE + 2.35
COLLET = FITTING_SEAT + 11
CAP_PITCH = 1.5
CAP_MAJOR = 20.0
CAP_BORE = 21.5
SOCKET_RADIUS = 7.01
CAP_GLAND_INNER_LIP = .29
CAP_GLAND_OUTER_LIP = .65
CAP_GLAND_OUTER_RELIEF = .16


def on_axis(part, face):
    return mesh(part).rotate([0,90,0]).translate([face,0,TUBE_Z])


def face_gland(spec):
    """Rounded entry and retaining throat over a full-depth face gland."""
    ri, ro = spec["gland_inner_radius_mm"],spec["gland_outer_radius_mm"]
    depth, corner = spec["gland_depth_mm"],spec["root_corner_radius_mm"]
    # Limit the overhang on the crown-down print so the cap lip grows
    # gradually toward the throat as the groove walls print.
    inner_lip, outer_lip = ri+CAP_GLAND_INNER_LIP, ro-CAP_GLAND_OUTER_LIP
    ro += CAP_GLAND_OUTER_RELIEF
    outline = [(inner_lip-.13,-.05),(outer_lip+.11,-.05),
               (outer_lip+.11,0),(outer_lip+.034,.05),(outer_lip,.12),
               (outer_lip,.29),(ro,depth-.32)]
    outline += [(ro-corner+corner*np.cos(a),depth-corner+corner*np.sin(a))
                for a in np.linspace(0,np.pi/2,12)]
    outline += [(ri+corner-corner*np.cos(a),depth-corner+corner*np.sin(a))
                for a in np.linspace(np.pi/2,0,12)]
    outline += [(ri,.83),(inner_lip,.29),(inner_lip,.12),
                (inner_lip-.037,.05),(inner_lip-.13,0)]
    return (m.Manifold.revolve(m.CrossSection([outline],m.FillRule.EvenOdd),128)
            .rotate([0,90,0]).translate([CAP_FACE,0,TUBE_Z]))


def build(outlet, cfg, floor, tube_stop):
    """Cut both socket threads from a single, supported boss."""
    thread_start = cfg["stem_thread"]["z_mm"][0]
    female = outlet.internal_cutter(
        CAP_MAJOR,CAP_PITCH,-5.8,.08,cfg["female_radial_allowance_mm"],thread_start,
        cfg["female_flank_axial_allowance_mm"])
    boss = (port(9.8,20.82,23.0,13.2)+port(13.2,22.98,27.0,16.0)
            +port(16.,26.99,CAP_FACE)+port(SOCKET_RADIUS,CAP_FACE-.1,FITTING_SEAT))
    boss += yz_prism([(-4.5,floor),(4.5,floor),(6.15,floor+3.8),
                      (-6.15,floor+3.8)],21.6,CAP_FACE)
    # The cap threads around the integral push-fit socket.
    coarse_cut = (on_axis(female,CAP_FACE)+port(9.89,CAP_FACE-.52,CAP_FACE+.12,10.32)
                  -port(SOCKET_RADIUS,CAP_FACE-6.2,FITTING_SEAT+.1))
    purchase = cfg["purchased_interfaces"]
    tap_origin = FITTING_SEAT-purchase["shoulder_stop_z_mm"]
    socket_cut = on_axis(outlet.purchased_socket_tool(cfg),tap_origin)
    socket_cut += (port(2.23,tube_stop-.1,FITTING_SEAT-13.40)
                   +port(2.23,FITTING_SEAT-13.41,FITTING_SEAT-7.93,5.10)
                   +port(5.10,FITTING_SEAT-7.94,FITTING_SEAT-6.98))
    fitting = on_axis(outlet.fitting_envelope(cfg),tap_origin)

    # The face ring closes the exposed end during storage.
    ring = cfg["wall_ring"]
    land = (port(ring["gland_outer_radius_mm"]+CAP_GLAND_OUTER_RELIEF,CAP_FACE-.025,CAP_FACE-.005)
            -port(ring["gland_inner_radius_mm"],CAP_FACE-.03,CAP_FACE))
    seal = on_axis(outlet.elliptical_ring(
        ring["compressed_mean_radius_mm"],ring["compressed_axial_height_mm"],
        ring["compressed_radial_width_mm"],ring["gland_depth_mm"]/2),CAP_FACE)
    bolt = outlet.external_thread(CAP_MAJOR,CAP_PITCH,*cfg["stem_thread"]["z_mm"])
    bolt = bolt.intersect(outlet.cylinder(CAP_MAJOR/2+.2,-5.15,.001))
    blind = COLLET+cfg["tail"]["exposed_tail_mm"]+3
    crown = blind+2.1
    cap = (on_axis(bolt,CAP_FACE)+port(8.8,CAP_FACE-.065,CAP_FACE+.06)
           +port(15.4,CAP_FACE,crown-1.65)+port(15.4,crown-1.66,crown,13.7))
    keepout = (port(7.36,CAP_FACE-5.2,CAP_FACE+1.59)
               +port(7.36,CAP_FACE+1.58,CAP_FACE+5.19,CAP_BORE/2)
               +port(CAP_BORE/2,CAP_FACE+5.18,blind))
    gland = face_gland(ring)
    gland_volume = (cap ^ gland).volume()
    cap -= keepout+gland
    return boss, coarse_cut+socket_cut, cap, fitting, land, seal, blind, gland_volume
