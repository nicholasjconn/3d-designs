# Holder print preparation

## Current: spindle and collar first-fit print (r5)

A **gentle, manual first fit** of the two printed center parts only. The
founder sent the job on 17 November 2026 with separate support material:
2 h 15 min 59 s and 38.55 g in its saved slice (14.54 g useful parts, 9.58 g
supports and interface, 6.32 g prime tower, 8.09 g nominal flush, 14 right-nozzle
AMS changes). Completion and fit are not reported; see the
[print record](https://macbook.terrier-shade.ts.net/castle-harker/notebook/pages/2026-11-17/manufacturing.html). The single-material numbers below are the
prepared comparison, not the sent job. It qualifies no clamp force, torque or load: do not test index
preload or loaded rewind on these prints. Geometry and rationale are in
[README](README.md#holder); the producer command (`cad/spindle_print.py`) is
listed there. The [private live preview](https://macbook.terrier-shade.ts.net/3d-designs/filament-drybox/holder/)
shows the oriented parts and support paths; it is built by
`preview/holder_geometry.py --print-prep`.

| Part | Bed orientation | Useful-part estimate |
| --- | --- | ---: |
| Spindle | Axle vertical, drive journal end on the bed (cone ring starts 9.7 mm up) | 8.79 g |
| Collar | Axle vertical, outboard cone face on the bed (hub starts 8 mm up) | 5.75 g |

Prepared single-material comparison: Bambu Lab H2D right 0.4 mm nozzle, Bambu PLA Basic,
Textured PEI, factory **0.20mm Standard**. Changes from factory: supports
enabled, critical regions only, and support style **tree_slim** (resolved by
Studio as `tree(auto)` + `tree_slim`). Nothing else is customised: one
filament, factory walls and infill, no purge tower; the auto brim is
negligible (0.008 g).

Estimate from the saved r5 slice (`build/spindle-print-r5-20261117`,
`critical-tree-slim`): **1 h 11 m 26 s**, **18.42 g** Studio total (r4:
1 h 15 m 16 s, 19.71 g). The r5 spindle's 45° ramp under the thread boss
removed the tall support tree to the boss face; all spindle support now ends
below 14.2 mm.

The founder sent a different configuration on 17 November: Support For PLA/PETG
interface material on the same right nozzle as the PLA, default tree style,
critical-regions-only off, independent support layers off, and dense zero-gap
interfaces. Its saved sent file estimates **2 h 15 m 59 s and 38.55 g**, still
printing each part once. Reconstructed useful-part material is unchanged at
14.54 g; support grows to 9.58 g, a prime tower adds 6.32 g, and fourteen AMS
material changes command about 8.09 g of filament flushing. The two files have
the same 5 min 18 s startup allowance. This is a comparison of two configurations,
not measured elapsed time or weighed waste. See the
[recorded comparison](https://macbook.terrier-shade.ts.net/castle-harker/notebook/pages/2026-11-17/manufacturing.html#drybox-print-estimate-comparison-2026-11-17).
Future estimates must use the final interface material, support settings and
nozzle assignment. No settings on the running print were changed during the investigation.

- Useful parts: **14.54 g** (spindle 8.79, collar 5.75).
- Support: **3.84 g** (body 2.79, transition 0.53, interface 0.53); r4 5.17 g.
- Startup G-code positive extrusion: about **0.183 g**, separate. Firmware
  loading, purge and calibration consumption is unknown. Stationary positive
  extrusion in the G-code may include unretraction and is not a measure of purge waste.

Support removal at the first fit: pick the tree support out of the spindle's
2.2 mm clip groove and check that the clip seats; pull the support interface
under the collar's spring arm off axially (do not lever the arm radially);
remove nubs from the thrust-sleeve face. No support enters the thread, lock
slots, female thread, spring pocket or key hole. These are estimates, not
weighed spool consumption, and no fabrication is approved by this preparation.

## Superseded: four-part holder fit-print proposal

> **17 November 2026:** the frame and green core on this four-part plate are superseded by the spoked frame, removable carriers, spindle and collar in [README](README.md#holder). The blue disc and retaining clip are unchanged. The spindle and collar are now sliced (see the current proposal above); the current frame and carriers have not been sliced.

The current holder is prepared as **one empty fit-prototype plate**, not a released
or physically qualified drybox. The redundant rounded wall noses and their
support wings are removed. The surrounding lip retains the 1.5 mm nominal wall
gap. Assembly wall span is 82.2 mm (3.236″); base width is 75 mm (2.953″), with
130 mm (5.118″) front-to-back depth. Both purchased 608 bearings remain required.

### Parts and orientations

| Part | Bed orientation | Nominal print envelope, mm | Useful-part estimate |
| --- | --- | --- | ---: |
| Grey frame | Base down; native +Y becomes print +Z (Rx90°) | 82.2 × 130 × 133.321 | 54.412 g |
| Green axle/core | Axle horizontal; Rx90° | 79.4 × 54.854 × 54.854 | 24.403 g |
| Blue drive disc | Closed magnet-cover face down, pockets up; Ry90° | 80 × 80 × 7 | 14.194 g |
| Purple retaining clip | Broad face down; Ry90° | 18 × 18 × 2 | 0.417 g |

Colors identify parts; the proposed plate uses one PLA filament. Frame, core and
disc need supports; the clip has none. The HTML review presents each part
individually, on its bed with sampled actual support roads. All four parts fit
together on one H2D plate. The oriented fabrication meshes are exported with
0.05 mm absolute linear and 0.15 rad angular meshing settings, not the looser
assembly-display triangulation.

The mesh audit caught a zero-thickness tangent connection between the core's
upper air tube and a longitudinal rib, even though native-solid validity and
slicer repair checks passed. Reducing the rib inner radius from 21 to 20.8 mm
creates positive overlap without changing the Ø6 bore or outside envelope.
All four final fabrication meshes are single, watertight, consistently wound
components with no degenerate triangles or nonmanifold edges. The producer
rejects bad meshes before writing a plate recipe; it does not repair them.

### Proposed settings and overhead

| Selection | Proposal |
| --- | --- |
| Bambu Studio | 02.09.01.70 |
| Printer / nozzle | Bambu Lab H2D, right 0.4 mm |
| Material | Bambu PLA Basic @BBL H2D |
| Process baseline | Factory 0.20mm Standard @BBL H2D |
| Plate | Textured PEI; actual plate must be confirmed |
| Process changes requiring approval before fabrication | `enable_support: 0 → 1`; `support_critical_regions_only: 0 → 1` |
| Other process, filament and machine fields | Factory baseline |

Normal automatic support trapped material inside the core's air bores. A
build-plate-only comparison did not solve it. Critical-regions-only support in
the horizontal pose leaves all three bores clear: even the conservative support
road-width envelopes do not intrude, with at least 0.517 mm nominal clearance.
The frame pilot bores and narrow thrust reliefs also contain no support roads.
The selected slice supports the grey bearing-holder undersides and blue counterbore roof; the angled guard underside needs no generated supports.
Core cage supports remain accessible through the open rib windows, and disc
supports through the open Ø24 counterbore and radial channel. Physical support
removal and supported journal surface quality remain first-print checks.

The final slice estimates **3 h 53 m 5 s** and **100.476 g**:

- Useful parts: **93.426 g**.
- Support bodies and interfaces: **7.011 g**.
- Brim: **0.008 g**; approximately **0.030 g** remains between reconstructed
  deposition and slicer reporting.
- No purge tower or color changes. About **0.183 g** of startup positive
  extrusion commands is separate; loading, purging and calibration consumption
  remain unknown. These are estimates, not weighed spool consumption.

The saved editable project was sliced and reimported with identical resolved
settings, zero warnings and zero mesh repairs. Direct 3MF vertex transforms
agree with the declared oriented STL placements within 0.000004 mm. Raw G-code
bytes may differ after reimport through travel ordering; byte identity is not
claimed. Actual feed assignment and send-time calibration require confirmation.
No manufacturing configuration or fabrication is approved by this preparation.

### Gray frame by itself

The current frame uses a narrow attached roof beneath the guard, with short
35° side struts landing on the existing legs. Its axial underside rises 1:1.
The roof stops 0.2 mm inside the drive-wall plane, preserving the original
wall-contact face. The two free diaphragm tips end at the highest existing
guard contact, reducing frame height from 151.634 to 133.321 mm. Native checks
retain the full bearing seats/jaws, base and original wall-contact surface.
The annulus reserved toward each bearing (|X|27–34.3, radius14.8–27.5 mm) stays
clear; this reserves space without defining the longer green cartridge.

The separate base-down gray-only plate estimates **2 h 3 m 58 s** and
**57.090 g**: **54.412 g useful frame**, **2.648 g support/interface**, no brim
or purge tower. Startup positive extrusion is separately about **0.183 g**;
firmware loading/purge/calibration consumption remains unknown. Compared with
the preceding 2 h 13 m 24 s /58.455 g plate, this saves about **9 min 26 s**
and **36.7% of support material**. The guard needs no generated supports;
carrier undersides still do. Saved project reimport has no warnings or repairs,
all resolved settings match, and blind pilots stay clear. The process retains
the same two proposed support changes; no speeds, walls or infill were changed.

A quadratic-tetrahedron comparison at E1,000 MPa used 40 N axial and 15 N
radial per seat, with an optimistic fixed floor and axial wall restraint.
Fine-mesh mean axial movement changes from 0.5742 to 0.5795 mm (0.92%), while
mesh refinement changes either result about1.4%; combined force-work differs
0.61%. This does not resolve a meaningful stiffness loss, and does not establish
printed strength. Both versions show substantial left-seat lateral flexibility
in this uncoupled frame-only model; bearing/shaft contact, physical loaded fit,
print anisotropy, retention and creep remain unqualified. The prior steel
holder's strength screen does not qualify this frame. No fabrication approval
is established by this preparation.

### Rebuilding

Use Python with the repository's CadQuery dependency. The offline slicing stage
also uses the Castle Harker engineering checkout's maintained factory-profile,
manufacturing and G-code analysis tools. Its location is an explicit argument;
no agent scratch files are prerequisites.

```sh
python filament-drybox/cad/stand.py --output build/holder-native
python filament-drybox/cad/stand_prepare.py \
  --engineering-root /path/to/castle-harker \
  --native-input build/holder-native --output build/holder-print \
  --bambu /Applications/BambuStudio.app/Contents/MacOS/BambuStudio
python filament-drybox/cad/stand_sections.py \
  --build build/holder-native --output build/holder-native/stand-sections.json
python filament-drybox/preview/prepare_print_view.py \
  --print-input build/holder-print --native-input build/holder-native \
  --house-renderer /path/to/castle-harker/shared/render \
  --output build/holder-print-view
```

`stand_print.py` can separately export and audit the four oriented meshes and
plate-placement inputs using `--native-input` and `--output`. `stand_prepare.py`
produces the proposed editable/sliced project, exact input identities, mesh
checks, placement proof, material ledger, support paths and bore-clearance
checks. The house renderer requires Blender and the Castle Harker house look.
Use a new output directory for each new preparation. Generated outputs are
local artifacts, not released inputs; the source must be approved, committed and tagged before authorized fabrication,
and the exact fabrication files retained and bound to that release.

### First physical checks

Print empty. Remove support, inspect the Ø8 journals, bearing seats and thrust
faces, then test snap insertion/release, full clip seating and retention, spool
hub grip, rotation at both axial slack limits, guard clearance and container
stability. The nominal Ø55 hub remains unmeasured. Creep, cyclic retention,
service strength, magnet retention and actual container fit are unqualified.
Desiccant bead containment and refill closure remain unfinished; these files do
not yet define a working refillable desiccant cartridge.

### Earlier printed prototype

The owner reported an earlier fixed stand printed on 15 November 2026 in PLA
Basic with factory 0.20 mm Standard on the H2D right 0.4 mm, support off (actual
send settings not reported). Its source commit was
`463119cc972861f764fc8ddcdc39d433d4c2cbd7`; outcome: completed, fit/surface quality
not reported. Its 60.29 g / 1 h 53 m 45 s plate, and the later fifteen-part
steel-fastener plate, are superseded and do not qualify this four-part holder.
