"""Build the one-piece drybox filament stop in its upright print orientation."""

import argparse
import json
from pathlib import Path

import cadquery as cq

import outlet

DEFAULT_CONFIG = Path(__file__).with_suffix('.json')
DEFAULT_OUTPUT = Path(__file__).resolve().parents[2] / 'build/filament-drybox/clip'


def load_config(path=DEFAULT_CONFIG):
    return json.loads(Path(path).read_text())


def build(c, outlet_config=None):
    """Return the stop at Z0 with the wings down and a vertical through-bore."""
    ports = outlet.load_config() if outlet_config is None else outlet_config
    seat = ports['tail']['reference_release_z_mm']
    top = seat + c['barrel_length_mm']
    barrel_radius = c['barrel_diameter_mm'] / 2
    bore_radius = c['bore_diameter_mm'] / 2
    bore = outlet.cylinder(bore_radius, seat - 1, top + 1)
    wings = cq.Workplane('XY', origin=(0, 0, seat)).rect(
        c['wing_span_mm'], c['wing_depth_mm']
    ).extrude(c['wing_height_mm']).edges('|Z').fillet(c['wing_corner_radius_mm']).val()
    barrel = outlet.cylinder(barrel_radius, seat, top)
    part = outlet.fuse([barrel, wings]).cut(bore).clean()

    for height, radius in [(seat, c['entry_radius_mm']), (top, c['exit_radius_mm'])]:
        edges = [edge for edge in part.Edges()
                 if edge.geomType() == 'CIRCLE' and abs(edge.radius() - bore_radius) < 1e-6
                 and abs(edge.Center().z - height) < 1e-6]
        if len(edges) != 1:
            raise ValueError(f'Expected one bore edge at Z{height}, found {len(edges)}')
        part = part.fillet(radius, edges)

    clear_space = outlet.cylinder(
        ports['cap']['bore_diameter_mm'] / 2, seat, ports['cap']['blind_z_mm']
    )
    if abs(part.Volume() - part.intersect(clear_space).Volume()) > 1e-5:
        raise ValueError('The filament stop extends beyond the cap cavity')
    return outlet.require_one(part, 'filament stop').translate((0, 0, -seat))


def export(c, output):
    output = Path(output)
    output.mkdir(parents=True, exist_ok=True)
    ports = outlet.load_config()
    part = build(c, ports)
    cq.exporters.export(part, str(output / 'barrel-stop.step'))
    report = {
        'volume_mm3': part.Volume(),
        'print_bounds_mm': outlet.bounds(part),
        'bore_diameter_mm': c['bore_diameter_mm'],
        'room_above_installed_barrel_mm': (
            ports['cap']['blind_z_mm'] - ports['tail']['reference_release_z_mm']
            - c['barrel_length_mm']
        ),
        'status': 'Geometry checked. Printed bore fit and bent-tip retention require a physical test.',
    }
    (output / 'checks.json').write_text(json.dumps(report, indent=2) + '\n')
    return report


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--config', type=Path, default=DEFAULT_CONFIG)
    parser.add_argument('--output', type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()
    print(json.dumps(export(load_config(args.config), args.output), indent=2))
