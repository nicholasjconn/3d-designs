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

The final offline slice has zero warnings and zero mesh repairs. Actual paths retain
one connected clip footprint in all 20 layers. The 0.8 mm leaf, jaws and latch
remain present; the jaw and latch gaps stay open. This checks deposition, not
hinge strength, grip or fatigue.

| Material / time | Estimate |
|---|---:|
| Useful body | 6.268 g |
| Useful nut | 1.570 g |
| Useful cap | 12.833 g |
| Useful clip | 0.185 g |
| Useful parts total | 20.856 g |
| Removable supports and support interface | 1.660 g |
| Brim and tower | 0 g |
| Slicer-minus-deposition residual | 0.030 g |
| Slicer total | 22.547 g |
| Estimated total time | 1 h 2 m 16 s |

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

The internal guide now meets the fitting socket through a 45° funnel, rather
than an abrupt ledge. It joins the Ø4.4 mm tube guide to the Ø10.2 mm tip relief
over 2.9 mm, leaving 19.2 mm of straight guide and the full 7 mm fitting thread.
The continuous PTFE tube passes through this funnel; filament remains inside
PTFE. The exterior and both seal glands are unchanged.

Actual support paths in the final four-part slice contain no support bead
inside the socket or tube passage. Exterior supports remain necessary for the
M26 shoulder and flange; only `enable_support` differs from factory Standard.
The other three parts receive no generated support. Supports also reach the
external radial O-ring groove: remove them and inspect its smooth surfaces and
the retention threads before fitting the ring. The upward wall-face gland has
no support roads. Cleanup, surface quality and sealing still need physical checks.

The replacement editable project is `outlet-funnel.3mf`. It has been opened in
native Bambu Studio with all four parts visible; the estimates above come from
the checked offline slice. No print has been sent.
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
