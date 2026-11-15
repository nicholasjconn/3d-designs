# First stand fit prototype

One complete stand is prepared upright, base down, in Bambu PLA Basic.
This is a fit prototype; the rest of the drybox is still in development.
No fabrication has been approved or sent.

## Prepared files

Generated files are retained locally under
`build/filament-drybox/print-review/` and excluded from Git:

- `stand-upright.stl`: the upright fabrication mesh, in millimetres.
- `stand.step`: the same upright native part, for CAD inspection.
- `stand-setup.3mf`: the editable, unsliced Bambu Studio project.
- `stand-sliced.3mf`: the fixed offline sliced candidate used for review.
- `index.html`: rotatable stand and actual support paths, with material accounting.

Keep the exact reviewed project when making a physical prototype; a later slice
can change toolpath ordering and estimates. The prepared files are not releases.

## Proposed setup

| Selection | Value |
|---|---|
| Bambu Studio used for the offline slice | 02.09.01.70 |
| Printer preset | Bambu Lab H2D 0.4 nozzle |
| Material | Bambu PLA Basic @BBL H2D, selected by the owner |
| Process | 0.20mm Standard @BBL H2D |
| Nozzle | Right, stock Standard 0.4 mm hotend; physical configuration assumed |
| Plate | Textured PEI; physical plate assumed |
| Only process-preset change | Enable support; retain factory tree (auto) settings |
| Orientation and count | One stand upright, base flat on the bed |
| Part envelope | 102 × 110 × 114.724 mm |

The installed process retains its factory 2 walls and 15% grid infill. No custom
wall, infill, speed or support parameters were introduced. Actual plate/hotend,
feed assignment and send-time calibration choices must be checked before
fabrication. Support use is a disclosed proposed change, awaiting approval.

## Material and time estimate

| Quantity | Estimate |
|---|---:|
| Useful stand deposition | 60.379 g |
| Removable tree supports and interfaces | 7.422 g |
| Unassigned difference from the slicer total | 0.030 g |
| Slicer-reported total | 67.831 g |
| Slicer-reported total time | 2 h 19 m 31 s |

These are profile-density and toolpath estimates, not weighed material or
measured elapsed time. No brim or prime/wipe tower is generated. Actual startup,
loading, purging and calibration consumption depends on printer state and is
not fully quantified by this offline slice; do not treat the slicer total as
exact total spool consumption.

The unsupported comparison used 60.409 g and 1 h 53 m 48 s, but left floating
nose starts and is unsuitable. Supports add about 7.42 g and 25 m 43 s.
Reducing that overhead by changing the nose shape would require a design
revision and renewed preparation; no such revision is included here.

## What was checked

The exported STL reloads as one watertight, consistently wound component, with
4,026 triangles and no repair. Native STEP roundtrip and mesh dimensions were
checked. Both the editable project and the fixed sliced archive were imported
and resliced offline: resolved settings and material totals match, with zero
mesh repairs and no warnings. Toolpath ordering and time differ slightly on
reslicing, so byte identity is not claimed.

The first nose layer has factory support interfaces below it. Supports also
reach the window crowns; the bearing seats have no support roads. The external
noses and open windows provide removal access. Support removal, surface marks,
bearing fit/capture, actual container fit, stiffness and tipping require the
physical prototype. Native connectivity and nominal clearance do not establish
strength or stability.

## Rebuilding geometry

Run `python filament-drybox/cad/stand.py` with the repository dependencies to
generate the native stand STEP. Its design axes are X along the axle and Y up.
For the reviewed upright pose, rotate +90° about X, then translate the minimum
XYZ corner to the origin. Import into Bambu Studio with the selections above.
Display meshes are for preview; use the native STEP or the prepared fabrication
STL for print preparation. A regenerated slice needs its own review.
