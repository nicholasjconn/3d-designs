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


def build(c, outlet_config=None, *, wing_marks=0):
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
    part = part.translate((0, 0, -seat))
    if wing_marks:
        # Blind marks identify the fit samples while leaving their seating faces flat.
        mark_centers = [(4.9, -1.05), (4.9, 1.05), (-4.9, -1.05), (-4.9, 1.05)]
        mark_top = c['wing_height_mm']
        cutters = [
            outlet.cylinder(.66, mark_top - .6, mark_top + .1).translate((x, y, 0))
            for x, y in mark_centers[:wing_marks]
        ]
        part = outlet.cut(part, cutters)
    return outlet.require_one(part, 'filament stop')


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


def export_bore_trials(c, output):
    """Export four samples with distinct dot counts on their wings."""
    output = Path(output)
    output.mkdir(parents=True, exist_ok=True)
    ports = outlet.load_config()
    trials = []
    for marks, diameter in enumerate((1.95, 2.00, 2.05, 2.10), start=1):
        part = build(dict(c, bore_diameter_mm=diameter), ports, wing_marks=marks)
        filename = f'barrel-{marks}-dot.step'
        cq.exporters.export(part, str(output / filename))
        trials.append({'dots': marks, 'bore_diameter_mm': diameter, 'step': filename})
    (output / 'trials.json').write_text(json.dumps(trials, indent=2) + '\n')
    return trials


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--config', type=Path, default=DEFAULT_CONFIG)
    parser.add_argument('--output', type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument('--bore-fit-trials', action='store_true')
    args = parser.parse_args()
    generator = export_bore_trials if args.bore_fit_trials else export
    print(json.dumps(generator(load_config(args.config), args.output), indent=2))
