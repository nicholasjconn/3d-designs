# First stand fit prototype

One complete stand is prepared upright, base down, in Bambu PLA Basic.
The wall-contact noses have small sloped undersides so this revision can be
printed with the factory support setting left off. The rounded contact areas,
base, bearing seats and main frames are retained. This is a fit prototype;
the rest of the drybox is still in development. No print has been sent.

## Prepared files

Generated files are retained locally under
`build/filament-drybox/print-review/` and excluded from Git:

- `stand-upright.stl`: the upright fabrication mesh, in millimetres.
- `stand.step`: the same upright native part, for CAD inspection.
- `stand-no-support.3mf`: the native saved, editable Bambu Studio project.
- `stand-no-support.gcode.3mf`: the native exported sliced plate.
- `index.html`: rotatable before/after stand and actual nose deposition paths.

Use the reviewed sliced plate for the prototype. Its native export opens
straight into Preview without reslicing. The editable project was separately
reopened in Studio and retained support off. A command-line reimport alone
does not establish native GUI behavior. Earlier supported projects and slices
are superseded and retained only as local evidence.

## Prepared setup

| Selection | Value |
|---|---|
| Bambu Studio | 02.09.01.70 |
| Printer preset | Bambu Lab H2D 0.4 nozzle |
| Material | Bambu PLA Basic @BBL H2D, selected by the owner |
| Process | Factory 0.20mm Standard @BBL H2D |
| Nozzle | Right, hardened steel 0.4 mm Standard flow; device configuration confirmed |
| Plate | Textured PEI; physical plate must be confirmed before sending |
| Process-preset changes | None; support remains off |
| Orientation and count | One stand upright, base flat on the bed |
| Part envelope | 102 × 110 × 114.724 mm |

The installed process retains its factory 2 walls and 15% grid infill. No custom
wall, infill, speed or support parameters were introduced. Physical plate,
feed assignment and send-time calibration choices remain to be checked before
fabrication.

## Material and time estimate

The native exported plate reports **60.29 g and 1 h 53 m 45 s**, approximately
1 h 54 m. The independent command-line slice of the same mesh reports 60.289 g
and 1 h 53 m 48 s. Both have zero generated supports. The native deposition ledger assigns 60.259 g to the stand and a 0.031 g
residual against its rounded total. Startup positive extrusion is separately
estimated at 0.183 g; printer loading and calibration consumption remain unknown.

These are profile-density and toolpath estimates, not weighed material or
measured elapsed time. No brim or prime/wipe tower is generated. Actual startup,
loading, purging and calibration consumption depends on printer state and is
not fully quantified by the slice; the slicer total is not exact total spool
consumption. The superseded supported geometry used approximately 67.83 g and
2 h 19 m 32 s.

## What was checked

The native part is one valid solid. Its 3,944-triangle fabrication STL is one
watertight, consistently wound component with zero repairs. STEP roundtrip,
mesh dimensions and nominal rotating-part clearances were checked: 1.5 mm to
the spool and 0.5 mm to the magnetic rotor. Affected native horizontal sections
show no new disconnected starts. The support-off slice has no warnings.

The window crowns retain short bridges, approximately 8.12 mm. The new nose
undersides still contain overhangs; support-free does not guarantee their
surface finish. Bearing fit/capture, container contact, stiffness and tipping
require the physical prototype. Native connectivity and nominal clearance do
not establish strength or stability.

## Rebuilding geometry

Run `python filament-drybox/cad/stand.py` with the repository dependencies to
generate the native stand STEP. Its design axes are X along the axle and Y up.
For the reviewed upright pose, rotate +90° about X, then translate the minimum
XYZ corner to the origin. Import into Bambu Studio with the selections above.
Display meshes are for preview; use the native STEP or the prepared fabrication
STL for print preparation. A regenerated slice needs its own review.
