# Current direct-drive fit print

The current plate is built from `cad/drybox.py` and `direct_drive.json`.
Magnetic-drive plates and earlier axle/stand projects are superseded.
This is a physical fit-test candidate, not strength or sealing qualification.
No printer job is sent by the build or preparation commands.

## Matching parts on one plate

| Part | Bed orientation | Useful-part estimate |
| --- | --- | ---: |
| Stand | Base down, native+Y becomes print+Z |37.42 g |
| Axle | Drive end down, thread-boss ramp upward |10.66 g |
| Locking collar | Outboard stop-ring face down |7.53 g |
| Drive-side carrier | Flat rear locator face down |2.18 g |
| Left carrier | Flat rear locator face down |1.69 g |
| Inside nut | Wide flange down, thread vertical |2.29 g |
| Crank | Grip end down, socket upward |2.94 g |
| Wall fitting | Outside thread down; wall O-ring groove upward |3.97 g |
| Sealing cap | Closed end down; threaded opening upward |2.39 g |

The left carrier and collar match their earlier widened/deeper-lock candidates;
they are included because the versions of the existing physical prints are
uncertain. Omit them only after matching the actual prints to this geometry.
The fitting and sealing cap keep their earlier direct-drive geometry and are
included on this complete nine-part plate. The working filament outlet parts are unchanged;
filament clip work remains deferred. Retain two608 bearings and the22 ×2/18 ×2 mm
static O-rings. Neither a magnetic wheel nor a rotor/retaining clip is needed.

## Configuration and overhead

Baseline: Bambu Studio02.09.01.70, H2D right0.4 mm nozzle, Bambu PLA Basic,
factory0.20 mm Standard, Textured PEI. The established single-PLA support
configuration is retained: support enabled, critical regions only, tree slim.
No interface-material changes, purge tower, custom walls/infill, speed,
temperature or calibration overrides are added. Actual plate and filament
assignment must match before sending; preserve Auto calibration choices.

The saved candidate estimates **3 h9 min38 s** and **77.860 g**:

- Useful parts: **71.071 g**.
- Support body: **4.795 g**; support transition: **0.948 g**;
  support interface: **0.948 g** (same PLA). Total supports **6.691 g**.
- Brim: **0.068 g**; about0.03 g difference remains between reconstructed
  deposition and the slicer's rounded reporting.
- No material changes or purge tower. Logged startup positive extrusion is
  approximately **0.183 g**, separate from deposited-part accounting.
  Firmware loading/purge/calibration consumption and additional heating/setup
  overhead are not fully quantified. The slice estimate is not guaranteed
  wall-clock time.

All nine meshes are single watertight consistently wound components, with
no degenerate triangles or slicer repairs/warnings. The editable project is
actually sliced and reimported; resolved settings match across imports.
Raw G-code bytes differ through ordering, so byte identity is not claimed.
Critical bead checks include the retaining lip, guide, channel-floor top skin,
carrier rim and nut flange. The crank's working socket is clear of intrusive
support-road envelopes. The fitting bore and cap cavity are also clear of deposited material in their checked working regions. Supports elsewhere still require removal and inspection.
The actual slice generates no supports on the stand, either carrier or nut. Axle, collar, crank and wall fitting retain supports; the cap has none. The carriers'1.4 mm bearing-stop ledges print as short overhang/bridge roads; check their undersides before seating a608.

## Rebuild and inspect

From the personal parts repository root, using a Python environment containing
its dependencies and the engineering checkout's maintained slicing tools:

```sh
python filament-drybox/cad/drybox.py --output build/filament-drybox/direct-drive-current
python filament-drybox/cad/direct_mechanics.py --output build/filament-drybox/direct-drive-current/mechanical-screen.json
python filament-drybox/cad/direct_prepare.py --native-input build/filament-drybox/direct-drive-current --engineering-root /path/to/castle-harker --output build/filament-drybox/direct-drive-print
python filament-drybox/cad/direct_toolpaths.py --output build/filament-drybox/direct-drive-print --engineering-root /path/to/castle-harker
python filament-drybox/cad/direct_layers.py --print-input build/filament-drybox/direct-drive-print --engineering-root /path/to/castle-harker --output build/filament-drybox/direct-drive-print/layers
python filament-drybox/preview/direct_geometry.py --native-input build/filament-drybox/direct-drive-current --print-input build/filament-drybox/direct-drive-print --output build/filament-drybox/direct-drive-preview
```

Use a new print-output directory per preparation; earlier fabrication inputs
are retained. The preview requires the existing Three.js dependency in
`filament-drybox/preview/node_modules/three` and shows the exact fabrication
meshes with sampled real support roads. The editable project is
`direct-drive-fit/direct-drive-fit.3mf`, with the sliced project and G-code
under its `out/` directory. File hashes and source digests bind the candidate.
No scratch source or copied native intermediate is required.

Claude Opus High independently approved the corrected candidate for a gentle
first fit print on18 November2026, with no remaining mechanical/print blockers.
The increased crank running clearance resolved its original rubbing objection.
That review covered the geometry and seven-part plate; the unchanged fitting
and cap were subsequently added, freshly sliced and checked with all nine parts.
Container fit, bearing-ledge cleanup, spool fit and sealing remain physical
checks. The final source and fabrication inputs are hash-bound in the retained
handoff manifest; no print has been sent by the preparation tools. This
personal repository uses normal Git commits, not Castle Harker's release-tag
sequence. Retain the exact print files and record the source commit before
fabrication.

The revised crank has aØ8.8 running shaft (0.8 mm radial gap in theØ10.4 bore) and a shorter blind socket, preserving3.8 mm nominal keyed overlap and the overall length. The increased running gap prevents likely rubbing from printed/drilled alignment error. It affects the opening while cranking; the stationary cap still closes the opening when the crank is removed. No rotary seal is added.

## Current selected print: eight parts, stand deferred

On 18 November 2026 the owner removed the stand from the plate, pending
additional base features. All eight other parts retain their matching geometry
and print orientations. The nine-part single-PLA plate above remains the
reproducible baseline, not the settings of this owner-edited job.

The saved owner-edited project uses H2D right 0.4 mm, Textured PEI, Bambu PLA
Basic for all useful parts and Bambu Support For PLA/PETG for interfaces only.
The 0.20 mm layers, two walls and 15% grid infill are unchanged. Tree supports
use the default style, with critical-regions-only disabled and independent
support layer height disabled. Interface pattern is rectilinear interlaced,
spacing 0 mm and top Z gap 0 mm; bottom Z gap remains 0.2 mm. The owner chose
these settings; they do not replace the single-PLA build defaults.

The actual saved slice estimates **3 h 26 min 53 s, 66.70 g**:

- Useful parts: **33.647 g**; no support material is deposited in useful parts.
- Supports: **13.611 g**, including body 8.906 g, transition 2.415 g and
  interface 2.290 g.
- Prime tower: **5.466 g**; brim: **0.074 g**.
- The remaining approximately **13.902 g** of the slicer's reported total is
  outside reconstructed deposited roads; it must not be described as useful
  plastic. Startup positive extrusion is approximately 0.183 g separately;
  firmware purge/calibration consumption is not fully reconstructed.

Both used filaments are assigned to the right nozzle. Studio warns this
allocation adds approximately 13 g and 24 nozzle purges relative to its
suggested grouping. Separate-nozzle grouping is a lower-overhead alternative;
no grouping, filament assignment or send settings were changed during review.
The support-interface settings were accepted for the first physical fit test;
they do not qualify sealing, printed strength or long-term operation. The
owner controls sending the job; a saved or reviewed plate is not a print record.

## First physical fit test

Remove supports and brim. Inspect journals, bearing pockets, threads and the
collar paddle before assembly. Test matching threads by fingers; do not force
or wrench-tighten the nut. Tighten the fitting and nut with open hand access, then
lower the stand over the upward-open nut flange channel. Seat the empty bearing/axle unit, check upward
lift-out with the crank removed, and check crank insertion/extraction. Then
load the spool, verify clearance at both sides and turn it both ways.

The carrier and stationary nut faces have zero nominal gap; printed face
cleanup may be required. The actual spool bore/recess, wall thickness, hole
position and usable container cavity are not fully measured. Check these
physically before drilling. Check lip/flange flex, collar retention and seals;
stop if a thread binds, a flange whitens or a bearing does not slide correctly.
Nominal collision checks and a local load screen do not qualify printed
strength, creep, airtightness or long-term operation.
