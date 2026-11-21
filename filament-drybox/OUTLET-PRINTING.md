# Filament outlet fit prototype

Prepare one set before making four copies. The complete assembly has four
printed parts: bulkhead body, inside locknut, storage cap and filament
barrel stop. It uses one HANGLIFE fitting, a 22 mm ID × 2 mm wall O-ring,
an 18 mm ID × 2 mm cap O-ring,
and one continuous 4 mm OD × 2.5 mm ID PTFE lead. All printed parts use the
owner-selected Bambu PLA Basic. The owner reports that the first outlet set
was started and its clip has failed to stay closed; see the print record below.

## Interfaces and assembly

The fitting's exact product packaging specifies PT 1/8, 7 mm of thread and
18 mm overall length. These are listed dimensions, not received-part measurements.
The intended printed socket matches the R 1/8 tapered thread geometry and lets
the fitting shoulder seat on the outlet face. It is a prototype retention
interface, not a qualified pipe-thread gauge or a sealing taper. Stop tightening
at the shoulder; forcing the metal fitting farther can damage the PLA neck.

The inside nut compresses the wall O-ring beneath the outside flange. The cap
seals on the second O-ring in the smooth neck above its retention thread.
The cap encloses the fitting, barrel stop and bent filament tip. The modeled
bend leaves 2.1 mm below the cap crown. Try the actual parts
before drilling or installing an outlet in a container.

For printing filament, remove the cap and barrel stop as described below.
Prethread the detached PTFE lead,
then slide it along the filament into the purchased fitting and through the
outlet. The nominal insertion mark is 54 mm from the lead's inlet end; verify
that the tube projects inside the box. Press the release collar to remove the
whole lead for storage. Leave enough bare filament to thread the stop and bend
the tip, then fit the cap. The connected printing path is not claimed hermetic.

## Outlet for a 3/4-inch hole

Both fittings use a 3/4″ (19.05 mm) container hole. The outlet's 18.40 mm
mounting thread leaves 0.65 mm of nominal diametral clearance. The new
locknut matches its 1.5 mm pitch and the stem keeps its 12 mm length.
The larger 34 mm flange has the same radial wall-gland dimensions as the
crank fitting. The wall ring now grips a Ø22.4 mm shoulder in a 1.50 mm deep,
2.80 mm wide groove. Use a 22 × 2 mm wall O-ring and the existing 18 × 2 mm
ring under the storage cap. Reuse the storage cap and quick-release tube fitting.

Print one body neck-down and one nut flat. The checked process uses Bambu
PLA Basic, H2D right Standard-flow 0.4 mm, Textured PEI and 0.20 mm Standard
with critical-only Tree Slim. The slice predates the face-groove revision.
Its estimate is 34 min 26 s, 8.29 g in the
parts and 1.68 g of support on the body. Support reaches the cap-ring groove.
The wall-ring groove and tube guide have no generated support paths. Clean
the cap groove, then check the printed stem in a 3/4″ test hole and thread
the matching nut by hand before installing.

Keep the body neck-down with Tree Slim. A same-body orientation comparison
with critical-only Tree Slim put support near the cap-side thread and ring
groove in the neck-down slice. Stem-down moved interface paths to the
mounting stem and wall-face groove and still put interface paths near the
cap-side ring groove. Inspect support removal on the actual part. If cleanup
continues to damage the cap thread, test a local painted support blocker on
its flanks while retaining support under the adjoining shoulder.

## Barrel stop fit print

The first 1.90 mm bore printed too tight to thread the filament (source
`387fd88`). The owner chose a 2.025 mm bore, halfway between the
two-dot and three-dot samples. The first print at that size failed as spaghetti.
The retry keeps the 2.025 mm bore and widens the wings to 16 × 9.5 mm. The
measured CAD bed contact increases from 67 to 145 mm². It prints without dots.

| Dots on the wings | Nominal bore |
| --- | ---: |
| 1 | 1.95 mm |
| 2 | 2.00 mm |
| 3 | 2.05 mm |
| 4 | 2.10 mm |

To reproduce the comparison, run
`python filament-drybox/cad/clip.py --bore-fit-trials --output build/filament-drybox/bore-trials`
from the repository root. The four marked STEP files print
upright with the wings on the bed. The checked plate uses Bambu PLA Basic,
H2D right Standard-flow 0.4 mm, Textured PEI and 0.20 mm Standard with
critical-only Tree Slim. The slice generates no support, brim or tower.
The estimate is 16 min 10 s and 2.27 g of useful PLA.

Try the same strand in each bore and choose the smallest that threads through
the full length by hand without forcing. The 16 mm barrel sits on the
push-to-release collar. Bend the exposed tip
sideways just beyond the rounded exit. Verify the bend holds under a pull and
the cap screws on without touching the tip. To reload, pull out a little slack,
hold the straight strand, snip below the bend and slide the stop off before
threading the PTFE lead.

## Superseded flat-jaw clip fit print

The owner reported a large gap and weak grip with the 19 November flat-jaw
clip. Its source is retained at `68cfb8a`.

Print one clip and reuse the outlet body, locknut and cap. In the new design,
the 6 mm-deep jaws close against each other on flat faces. The rounded grooves
form a 1.43 mm nominal opening at the empty stop. A solid web braces the moving
jaw to its frame, and the curved spring's hook reaches 0.22 mm farther under
the catch. On 1.75 mm filament the jaws open about 2.5 degrees and the spring
flexes to engage the catch. The outlet still locates the clip at Z38.5.

Use the two solids together from `clip-open.step`, with both at their native
Z0 and the gate 65 degrees open. The checked plate uses Bambu PLA Basic,
H2D right 0.4 mm, factory 0.20 mm Standard and Textured PEI. Tree Slim support
is enabled for critical regions only and produces no supports on this clip.
The offline estimate is 8 min 48 s total, with approximately 0.63 g of PLA
in the clip. No brim or tower was generated.

After cooling, free the hinge by hand. Check that the latch catches on 1.75 mm
filament, the filament stays put when pulled, the latch releases by hand, and
the loaded clip clears the cap. This test also checks for filament damage.
Grip force and the effects of cycling and sustained load remain unverified.

## Superseded rigid-jaw clip design — 15 November 2026

The owner asked for a purpose-built clip after reviewing the trimmed
[Mc2.project3D reference](https://makerworld.com/en/models/797139-clip-filament-click-print-in-place#profileId-736443).
The clip source at `7f54693` defined independently authored native CAD,
using a captured pin hinge and a positive click latch. No third-party mesh is
loaded or trimmed by this generator. The downloaded reference and personal-use
trim remain local only; they are superseded as the current design.

Two printed bodies form the clip. The fixed jaw has a 2 mm open cradle and
already spans the outlet. Following the owner's snapping and stability concerns,
the moving jaw is now solid all the way to the hinge frame. The former short
0.7 mm gripping spring and its clearance slot are removed. The broad jaw is
1.55 mm thick in its plain section, with a minimum 1.3 mm ligament above the
filament groove, through the full 5 mm axial depth. The long outside latch is
the only part intended to flex. Its blunt hook and lip provide retention and
release. The former pointed
triangle is replaced by a 0.7 mm flat nose with R0.15 corners and full 1 mm
backing beneath the retaining flat. The empty-closed retaining overlap is
0.94 mm nominal, or 0.69 mm after a 0.25 mm outward pin shift.
The filament position is unchanged because a separate flexible pad is no longer
needed. The spool channel, tall flange, branding and extra stop tab are absent.

At nominal native Z36–41, the empty closed CAD fits within the 21.5 mm cap bore
with 0.95 mm radial margin and 11 mm below the blind end. Outlet tail metadata
records this 5 mm clip and its center at Z38.5; body, cap and seal geometry are
unchanged. These are nominal dimensions, not printed or loaded elastic fit.

The unloaded jaw gap is 1.5 mm. Nominal 1.75 mm filament holds the rigid jaw
about 1.97° open; the outside latch must bend to engage. The viewer explicitly
shows the empty closed geometry, without filament intersecting the rigid jaw.
Open and separated views explain loading and the two printed bodies. It does
not simulate the loaded latch deformation.

A simplified planar beam model predicts about 0.33 mm downward latch-tip travel
at nominal filament fit, with about 1% peak bending strain. Nine sampled radial
hinge-play positions reach about 2% strain; the modeled hook overlap remains at
least 0.70 mm after the hook revision. These are comparison estimates with a
fixed root and uniform
section, excluding local concentrations, nonlinear contact, print errors, creep
and fatigue. They do not establish holding force or PLA reliability. The prior
short-neck design and a folded gripping-leaf candidate are superseded; a folded
leaf still allowed the broad pad to rotate.

The fixed jaw is exactly unchanged. Empty closure has no part intersection,
and the opening check finds only the intended hook/catch snap contact near
closure. Native STEP and display meshes are in
`build/filament-drybox/clip-own/`. No replacement fabrication mesh or slice is
prepared. Hinge freeing, actual latch engagement, grip, release, loaded cap fit,
printed dimensions, creep, fatigue, TPU and filled filament need physical tests.
The source allows an initial Bambu PLA Basic prototype; it does not qualify PLA
life. Grok independently agreed the blunt-hook revision is ready for design
review with the existing strain and grip limits; this is not fabrication
approval. The old four-part sliced plate below contains the failed clip and
must not be reused.

## Previous outlet candidate with the failed clip

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
the checked offline slice with critical-regions-only off. The owner's print
uses critical-regions-only on, as recorded below.
Current generated files live under the ignored
`build/filament-drybox/outlet-print/` directory. The exact prepared project
retains its support-selection metadata; importing meshes into a fresh factory
process instead requires explicitly enabling supports before slicing.

## Failed original clip first test

The owner reports that the hook never caught and the clip did not come close to
staying closed. Its 0.8 mm leaf and nominal 1.60 mm jaw gap had passed geometric
and deposition checks. Those checks did not establish that the latch would
engage or retain filament. The original mechanism and the trimmed third-party
reference are superseded by the current design above. The exact failed source
is retained at the print-record commit.

## Rebuild and qualification

From the repository root, with the CadQuery dependency installed:

```sh
python filament-drybox/cad/outlet.py
python filament-drybox/cad/clip.py --output build/filament-drybox/barrel-stop
```

The outlet generator writes native STEP references and upright fabrication STLs
to `build/filament-drybox/outlet/`. The stop generator writes
`barrel-stop.step` in upright print orientation and checks the cap envelope.
Both accept `--config` and `--output`; the outlet also accepts `--parts body nut
cap` or a subset.

The nominal native assembly fits and screw motions are geometric checks.
Printed thread fit, received fitting passage and retention, O-ring fit, layer
texture, leakage and humidity retention require the prototype. An intact print
or a compressed O-ring alone does not establish airtight storage.

## Print record

15 November 2026, reported at approximately 14:50 EST — Owner reports the first outlet prototype set printing; prepared for Bambu PLA Basic, factory 0.20 mm Standard on H2D right 0.4 mm, supports enabled with **Support critical regions only** enabled by the owner (final feed mapping and calibration selections not reported); source `cad/outlet.py` / `cad/outlet.json` and `cad/clip.py` / `cad/clip.json`, commit `edf2a7d637a1d674d95a74f1eb75242fa4517ef5`; outcome: the owner reports the printed clip did not come close to staying closed, and clarified that the hook never caught. Completion and fit of the remaining outlet parts have not been reported. The closure mechanism is being reconsidered; the cause of failure has not been established. The affected comparison passed with exterior supports retained and no internal supports; estimate 61 min 6 s, 22.266 g total (20.856 g useful parts, 1.379 g supports, 0.030 g residual), with startup consumption separate. The owner's exact sent project has not been captured; no release tag is recorded for this print.
