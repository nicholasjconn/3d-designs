"""Reuse the native drybox stem, flange, gasket land and locknut."""
import manifold3d as m
import numpy as np
import trimesh

WALL_X = -36.2
MOUNT_AXIS_OFFSET = 3.55
FLANGE_SEAT_X = -24.95
FLANGE_FRONT_X = -22.20
LINER_SEAT_RADIUS = 3.00
BUSHING_STEM_RADIUS = 3.08
BUSHING_STEM_BORE = 4.46
BUSHING_LIP_BORE = 3.98

def mesh(shape):
    points, triangles = shape.tessellate(.018,.135)
    result = trimesh.Trimesh([point.toTuple() for point in points],triangles)
    solid = m.Manifold(m.Mesh(result.vertices.astype(np.float32),result.faces.astype(np.uint32)))
    if not result.is_watertight or solid.status() != m.Error.NoError:
        raise ValueError("Drybox outlet tessellation was not a valid solid")
    return solid

def build(port, box, yz_prism, axis_z, tube_stop):
    import outlet

    cfg = outlet.load_config()
    flange, stem, tube = (cfg[key] for key in ("flange","stem_thread","tube"))
    wall_ring = cfg["wall_ring"]
    thickness = cfg["wall_thickness_mm"]

    mount_z = axis_z-MOUNT_AXIS_OFFSET

    def on_axis(shape, z=mount_z):
        return mesh(shape).rotate([0,90,0]).translate([WALL_X,0,z])

    def around_mount(radius,start,end,end_radius=-1):
        return port(radius,start,end,end_radius).translate([0,0,-MOUNT_AXIS_OFFSET])

    original_body = outlet.make_body(cfg)
    flange_end = WALL_X + flange["z_mm"][1]
    stem_end = WALL_X + stem["z_mm"][0]
    wall_flange = on_axis(original_body.intersect(outlet.cylinder(18,0,flange["z_mm"][1])))
    # An inner lead-in captures the wall ring while the drybox is being assembled.
    retainer = (around_mount(11.41,WALL_X,WALL_X+.14,11.50)
                +around_mount(11.50,WALL_X+.13,WALL_X+.70,11.18)
                -around_mount(10.95,WALL_X-.01,WALL_X+.71))
    wall_flange += retainer
    # Lower the mounting axis relative to the PTFE so the large opening
    # can pass beneath the lid gasket. The PTFE itself stays straight.
    neck = around_mount(15.4,flange_end-.30,-28.15,13.4)
    neck += around_mount(13.4,-28.17,-24.92,12.5)
    neck -= box(-31.45,-18,3.08,-24.86,18,18)
    wall_hole = around_mount(9.61,WALL_X-.12,FLANGE_SEAT_X+.05)
    # The long chamfer on just one corner indexes the off-center PTFE bore.
    shoulder = [(-7.95,2.23),(7.95,2.23),(9.35,.8),(9.35,-14.35),
                (4.9,-19.82),(-7.8,-19.82),(-9.35,-17.5),(-9.35,.8)]
    keyed_head = yz_prism(shoulder,FLANGE_SEAT_X,FLANGE_FRONT_X)
    clearance_outline = [(1.023*y,mount_z+1.023*(z-mount_z)) for y,z in shoulder]
    seat = yz_prism(clearance_outline,FLANGE_SEAT_X,-20.82)
    pilot = around_mount(9.18,WALL_X-.04,FLANGE_SEAT_X+.03)
    pilot += around_mount(9.18,FLANGE_SEAT_X-1.65,FLANGE_SEAT_X-.67,9.45)
    pilot += around_mount(9.45,FLANGE_SEAT_X-.69,FLANGE_SEAT_X+.025)
    threads = on_axis(outlet.external_thread(stem["major_diameter_mm"],stem["pitch_mm"],*stem["z_mm"]))
    tube_guide = port(2.20,stem_end-.12,FLANGE_FRONT_X+.15)
    # The exposed flange seals against the tube. The wider stem bore
    # accommodates inward deflection when pressed into the rigid seat.
    bushing_seat = port(LINER_SEAT_RADIUS,stem_end-.06,stem_end+3.65)
    bushing = port(3.80,stem_end-1.05,stem_end)
    bushing += port(BUSHING_STEM_RADIUS,stem_end-.02,stem_end+3.18)
    bushing += port(BUSHING_STEM_RADIUS,stem_end+3.16,stem_end+3.53,2.85)
    lip, bore = BUSHING_LIP_BORE/2, BUSHING_STEM_BORE/2
    bushing_bore = (port(2.31,stem_end-1.12,stem_end-.69,lip)
                    +port(lip,stem_end-.70,stem_end-.41)
                    +port(lip,stem_end-.42,stem_end-.08,bore)
                    +port(bore,stem_end-.09,stem_end+3.25)
                    +port(bore,stem_end+3.24,stem_end+3.62,2.37))
    inlet = WALL_X+tube["inside_tip_z_mm"]
    liner_clearance = port(tube["od_mm"]/2,inlet,-tube_stop)
    liner = liner_clearance - port(tube["id_mm"]/2,inlet-.05,-tube_stop+.05)
    bulkhead = (threads+pilot+keyed_head)-tube_guide-bushing_seat
    nut = on_axis(outlet.make_nut(cfg))
    panel = box(WALL_X-thickness,-33,mount_z-36,WALL_X,33,mount_z+36)
    panel -= around_mount(cfg["panel_hole_diameter_mm"]/2,WALL_X-thickness-.1,WALL_X+.1)
    seal = on_axis(outlet.elliptical_ring(
        wall_ring["compressed_mean_radius_mm"],wall_ring["compressed_axial_height_mm"],
        wall_ring["compressed_radial_width_mm"],wall_ring["gland_depth_mm"]/2))
    return {
        "mount":wall_flange+neck, "passage":wall_hole+seat, "bulkhead":bulkhead,
        "linerSolid":liner_clearance,"leftTube":liner,"bushing":bushing-bushing_bore,
        "locknut":nut,"panel":panel,"wallSeal":seal,"standardBody":on_axis(original_body),
        "standardFitting":on_axis(outlet.fitting_envelope(cfg)),
        "standardTube":on_axis(outlet.tube(tube["od_mm"]/2,tube["id_mm"]/2,
                                         tube["inside_tip_z_mm"],64)),
        "wallX":WALL_X,"mountZ":mount_z,"linerLength":round(-tube_stop-inlet,3),
    }
