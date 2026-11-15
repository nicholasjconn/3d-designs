# Filament outlet fit prototype

Prepare one set before making four copies. The complete assembly has four
printed parts: bulkhead body, inside locknut, storage cap and side-loading
filament clip. It uses one HANGLIFE fitting, two 18 mm ID × 2 mm NBR O-rings,
and one continuous 4 mm OD × 2.5 mm ID PTFE lead. All printed parts use the
owner-selected Bambu PLA Basic. No outlet print has been sent by this task.

## Interfaces and assembly

The fitting's exact product packaging specifies PT 1/8, 7 mm of thread and
18 mm overall length. These are listed dimensions, not received-part measurements.
The intended printed socket matches the R 1/8 tapered thread geometry and lets
the fitting shoulder seat on the outlet face. It is a prototype retention
interface, not a qualified pipe-thread gauge or a sealing taper. Stop tightening
at the shoulder; forcing the metal fitting farther can damage the PLA neck.

The inside nut compresses the wall O-ring beneath the outside flange. The cap
seals on the second O-ring in the smooth neck above its retention thread.
The cap encloses the fitting, clip and a nominal 20 mm parked filament tail.
Listed fitting dimensions give 3 mm of crown clearance. Try the actual parts
before drilling or installing an outlet in a container.

For printing filament, remove the cap and clip. Prethread the detached PTFE lead,
then slide it along the filament into the purchased fitting and through the
outlet. The nominal insertion mark is 54 mm from the lead's inlet end; verify
that the tube projects inside the box. Press the release collar to remove the
whole lead for storage, hold the filament, rewind to a 20 mm tail, attach the
clip, then fit the cap. The connected printing path is not claimed hermetic.

## Prepared outlet candidate

The body prints neck face down and mounting stem up. The nut prints flat;
the cap prints closed crown down and mouth up; the clip prints flat in its
open pose. Use `clip-open.stl` for the clip; its closed model is an assembly
reference, not a print input.

| Selection | Candidate |
|---|---|
| Bambu Studio | 02.09.01.70 |
| Printer / nozzle | H2D, right hardened-steel 0.4 mm Standard flow |
| Material | Bambu PLA Basic @BBL H2D |
| Process | Factory 0.20mm Standard @BBL H2D |
| Plate | Textured PEI; confirm physical plate before sending |
| Process overrides | `enable_support = 1`; all other process and filament settings factory defaults |
| Count | One body, one nut, one cap and one open clip |

The offline slice has zero warnings and zero mesh repairs. Actual paths retain
one connected clip footprint in all 20 layers. The 0.8 mm leaf, jaws and latch
remain present; the jaw and latch gaps stay open. This checks deposition, not
hinge strength, grip or fatigue.

| Material / time | Estimate |
|---|---:|
| Useful body | 6.272 g |
| Useful nut | 1.570 g |
| Useful cap | 12.833 g |
| Useful clip | 0.185 g |
| Useful parts total | 20.860 g |
| Removable supports and support interface | 1.729 g |
| Brim and tower | 0 g |
| Slicer-minus-deposition residual | 0.030 g |
| Slicer total | 22.620 g |
| Estimated total time | 1 h 2 m 39 s |

Positive startup extrusion commands separately represent approximately 0.183 g.
Conditional startup, loading and calibration consumption depend on printer state
and are not fully quantified. Stationary positive E includes unretraction and
must not be added as consumed waste. These are estimates, not weighed material.

The body passes the one-solid and watertight fabrication-mesh checks without
repairs. Its external geometry, including both seal glands and the two printed
retention threads, is unchanged from the earlier nominal assembly checks.
The added purchased-fitting socket is a complete rounded tapered helix with
provisional print allowance and a small root clearance. This is not an ISO
thread-gauge qualification.

A support-free body slice starts the M26 shoulder and outer flange walls without
previous-layer support. The proposed body therefore uses factory supports,
with only `enable_support` changed from the Standard preset. The other three
parts need no generated supports. Body-only comparison: support off is 6.302 g
and 23 m 25 s; support on is 8.031 g and 33 m 52 s. The lower-overhead slice is
not the proposed first print because of those unsupported starts.

Supports reach about 7.8 mm into the fitting socket. Break them apart and remove
them through its wide, bed-facing mouth, rather than trying to push a rigid plug
through the narrow PTFE passage. The external radial O-ring groove also needs
support cleanup. Inspect the thread and smooth groove carefully before trying
the metal fitting or ring. The upward wall-face O-ring gland has no support
roads. Accessibility is a geometric check; successful cleanup and sealing are
physical checks.

The editable four-part project and upright STLs are offline candidates. They
have not been verified in the native Studio window or sent to a printer.
Current generated files live under the ignored
`build/filament-drybox/outlet-print/` directory. The exact prepared project
retains its support-selection metadata; importing meshes into a fresh factory
process instead requires explicitly enabling supports before slicing.

## Clip first test

The clip uses a curved leaf, smooth opposing jaws and a releasable latch. Its
nominal 1.60 mm gap interferes by 0.15 mm with 1.75 mm filament; the jaws flex to
accommodate it. Elementary strain screens do not establish printed PLA strength
or contact pressure. Assumed jaw stiffness gives a wide force sensitivity;
filament marking, especially with TPU, must be tested.

Inspect the continuous thin features, side-load a straight piece of PLA filament,
close once gently, test a light pull, then release by pulling the outside latch
tongue away from the filament. Inspect for whitening, cracks and filament marks.
Do not leave the prototype as the only safeguard against losing a filament end
until its grip has been tested. TPU, PETG, abrasive filament, sustained retention
and repeated cycling remain physical checks.

## Rebuild and qualification

From the repository root, with the CadQuery dependency installed:

```sh
python filament-drybox/cad/outlet.py
python filament-drybox/cad/clip.py
```

The outlet generator writes native STEP references and upright fabrication STLs
to `build/filament-drybox/outlet/`; the clip generator writes to
`build/filament-drybox/clip/`. Both accept `--config` and `--output`. The outlet
also accepts `--parts body nut cap` or a subset. Regenerated slices need their
own review.

`cad/clip.py` exports the native open and closed references and the open STL.
Its loader checks the shared bore, filament diameter and axial height against
canonical `cad/outlet.json` so a changed outlet cannot silently retain stale clip
clearance assumptions.

The nominal native assembly fits and screw motions are geometric checks.
Printed thread fit, received fitting passage and retention, O-ring fit, layer
texture, leakage and humidity retention require the prototype. An intact print
or a compressed O-ring alone does not establish airtight storage.
