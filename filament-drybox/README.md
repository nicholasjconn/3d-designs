# Filament drybox

Original parametric CadQuery source for the current filament-drybox project. The owner reports the first stand fit prototype is printed and complete. See [print preparation](PRINTING.md) for its prepared Bambu PLA Basic factory-preset setup, files, estimate and print record. Strength, physical fit and surface quality remain unreported.

## Stand

`cad/stand.py` provides `build(config)` and a small export CLI. `cad/stand.json` is the canonical configuration, in millimetres: 98 × 110 × 8 open base, two continuous A-frames, open bearing cradles at axis height 104 and integral drive-side wall stops. Geometry is unchanged from the reviewed one-solid concept.

With Python and the repository-root `requirements.txt` CadQuery dependency available:

```sh
python filament-drybox/cad/stand.py
```

The default output is repository-local `build/filament-drybox/`, independent of the current working directory. It writes a native STEP, display mesh and geometry receipt. `--config` and `--output` accept explicit paths. Display triangulation uses absolute OCCT deflection; it is not a fabrication mesh or maximum-error guarantee. The generator imports no other repository.

Previous native checks established nominal one-solid connectivity, spool/rotor clearance and upward bearing service in synthetic cases. Portability regeneration checks identity against those results; it does not repeat or extend physical qualification. Actual container fit/taper, bearing support/capture, loads, stiffness, tipping, manufacturing allowances and wall contact remain unqualified. Printed-body connectivity is not strength evidence.

## Outlet prototype preparation

See [outlet print preparation](OUTLET-PRINTING.md) for the body, nut, cap and
filament clip. `cad/outlet.py` / `outlet.json` own the bulkhead and cap assembly;
the purchased fitting is a dimensional envelope, not manufacturer CAD. Its exact
packaging specifies PT 1/8, 7 mm of thread and 18 mm overall length. The printed
fitting socket follows the nominal shoulder-seated tapered interface. Its native
solid and fabrication mesh pass the geometric checks; printed engagement still
requires the first fit trial.

`cad/clip.py` / `clip.json` provide an original one-piece hinged clip with smooth
sandwich jaws, side loading and a releasable latch. The **open** pose is the
fabrication input; the closed pose is an assembly reference. The current native
and factory-slice checks support a first PLA fit/function trial, not qualified
grip, fatigue, sustained retention or use across all filament materials.

## Remaining concepts

`cad/wheel.py` / `wheel.json` preserve the original Ø120 handwheel with three
Ø15 × 3 magnet pockets at radius 30. `build()` returns its single native solid.
Adhesive retention, manufacturing tolerances and performance remain unqualified;
it is not the current print-preparation target.

The rotating desiccant core is still a visual concept without a native generator.
The older clamp preview predates the printable prototype and is not its geometry
source. These concept visuals must not be presented as printable CAD.


## Preserved concept preview

`preview/` holds authored HTML/JavaScript for the current core and clip concepts and assembly views. It does not yet run independently here: the pinned Three.js dependency, generated mesh payloads and serving integration are intentionally not bundled. See `preview/README.md`. These visuals do not supply missing native CAD or manufacturing qualification.
