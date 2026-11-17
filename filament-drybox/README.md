# Filament drybox

Original parametric CadQuery source for the filament drybox. Everything current
is built and checked by one entry point, `cad/drybox.py`; it does not slice,
print or approve fabrication.

## Current parts and sources

Each part has one canonical source in `cad/`. The latest print state of every
part, and the purchased items, are listed in `cad/drybox.json` and shown in the
preview's *Current parts* table.

| System | Printed parts | Source |
|---|---|---|
| Holder | gray frame (with four anchor branches), two keyed carriers, spindle, locking collar, blue magnetic disc, disc retaining clip | `stand.py`, `spindle.py`, `stand.json` |
| Outside drive | fixed X with integral axle, handwheel, 608 retainer ring, axle clip | `wheel.py`, `wheel.json`, `stand.json` `mount` |
| Outlet | bulkhead body, inside locknut, storage cap | `outlet.py`, `outlet.json` |
| Filament clip | fixed jaw with hinge, moving jaw with latch | `clip.py`, `clip.json` |

Shared interface values have one owner, and the other parts read them:

- The magnet size, pattern and cups belong to `stand.json` `magnets`. `wheel.py` reads them, so the disc and the wheel always match.
- The outside mount belongs to `stand.json` `mount`: anchor centres and glue pockets, the frame branches, the X, the extra 608's retention faces, clearances and the axle clip. `stand.py` builds the frame branches from it and `wheel.py` the outside parts, so the anchor pairs always line up.
- The locked axial endpoints and base are in `drybox.json` `axial_limits_mm`; `drybox.py` measures them from the exported solids and fails if they differ.
- The filament clip's height and filament size are checked against `outlet.json` `tail`.
- The 608 bearings, disc key and clip groove are all in `stand.json`.

Purchased:

- three 608ZZ bearings (two in the holder, one in the outside drive);
- fourteen Ø15 × 3 mm magnets (three in the disc, three in the wheel, four in the X, four glued into the gray frame);
- one push-fit fitting (PT 1/8 thread per its packaging drawing, sold as HANGLIFE PC4-M10);
- two 18 × 2 mm NBR O-rings;
- one continuous 4 × 2.5 mm PTFE lead.

Not designed yet:

- bottom-side desiccant baskets;
- any container measurement (wall thickness, interior, outlet location).

## Build and check

Use Python 3.11 or newer (CadQuery 2.8.0 requires it) with `requirements.txt`,
and Node for the preview runtime. From the repository root:

```sh
python -m pip install -r requirements.txt
python filament-drybox/cad/drybox.py --output build/filament-drybox/current \
  [--spool /private/path/to/bambu-spool] [--reference-build build/holder-native-spindle-r5-20261117]
(cd filament-drybox/preview && npm ci)
python filament-drybox/preview/holder_geometry.py --native build/filament-drybox/current/holder \
  --system build/filament-drybox/current [--spool /private/path/to/bambu-spool] \
  [--print-prep build/<spindle_print.py output>] --output build/filament-drybox/holder
```

`drybox.py` runs each part's producer into its own subdirectory (`holder/`,
`wheel/`, `outlet/`, `clip/`). It reuses a producer's output when its sources are
unchanged since the last run into the same directory. It then checks the
connections between systems:

- a purchased magnet fits every disc and wheel pocket;
- the drive-magnet face gap through 1, 2 and 4 mm walls;
- each of the four anchor pairs: a magnet fits the frame pocket and the X pocket, coaxial, faces separated only by the wall;
- the outside drive's own checks (`wheel/checks.json`): the wheel clears the fixed X, clip and inner ring by at least 1 mm every 5° of a full turn; retaining faces touch only their own 608 ring and keep clear of the shield zone; every axial direction is positively blocked; and the 608, wheel and clip assembly path is clear;
- the outside drive stays outside the wall;
- the locked endpoints, measured from the exported solids: holder X −37.5…44.7, spindle −36.2…43.2, full assembly −37.5…67.15 at a nominal 2 mm wall, and the frame's floor footprint 75 × 130 mm;
- the PTFE lead passes the outlet body, fitting and nut;
- the closed clip fits inside the storage cap;
- optionally, the unchanged carriers and both 608 envelopes match a reference build exactly. The frame, spindle, collar, disc and clip are excluded because they changed; a missing reference part fails the run.

It writes `system-checks.json`, `system-display.json` and `manifest.json` (source
and output SHA-256, producer reuse, environment, inventory). The holder's own
checks are in `holder/stand-build.json`.

`holder_geometry.py` copies the pinned Three.js 0.169.0 runtime from
`preview/node_modules` into the generated page. The preview shows the same spool envelope used in the fit check: A and D measured, radial dimensions assumed. The supplied reference mesh is used separately by the spool-fit check.

## Holder

`cad/stand.py` / `cad/stand.json` are the canonical holder source: one spoked gray frame, two removable keyed bearing carriers, a printed spindle and threaded collar (`cad/spindle.py`), the keyed blue magnetic disc and the printed retaining clip, plus two purchased 608 bearings. The earlier high-flow cartridge prototype ([CORE-PRINTING.md](CORE-PRINTING.md)) is superseded for this holder, as is the former green axle/core.

| Dimension | Endpoints along the axle (X) | mm | inches |
|---|---|---:|---:|
| W1: minimum inside wall span | Leftmost frame face −37.5 to drive-wall contact face +44.7 | 82.2 | 3.236 |
| B1: base edge to edge | Base −37.5 to +37.5 | 75 | 2.953 |
| Base front to back | Z−65 to +65 | 130 | 5.118 |

Frame: two A-frames on the 75 × 130 mm base, an open U-rim guard around the disc on the drive side with two upper spokes, R6 junction rounds, a central brace and three 45° rim undersides. The axle is at 104 mm. Four integral anchor branches (17 November 2026) run from the guard to glue pockets at R77.5 on the diagonals, faces on the wall-contact plane; they take the frame height from 128 to 168.8 mm. The base keeps two smooth Ø8 × 18 mm blind pilot holes for future printed expansion screws.

Carriers: each frame plate has a 24.4 mm keyed vertical slot down to a flat floor 13.2 mm below the axle; its thinned edges run in the carrier's axial grooves. Each carrier holds one 608 in a C-seat (21.6 mm mouth, 0.2 mm jaw movement per side). Carriers, bearings, spindle, collar, spool, disc and clip lift out together; nothing stationary enters the spool bore. Carriers seat by gravity only.

Spindle and collar (changed 17 November 2026 after the r5 first-fit print was sent: square key and flat spool stops; not printed; the generated preview's `grip.html` shows how the two green rings attach, from the same build): the spindle is one part with both 608 journals, a Ø10 shaft, a threaded boss at the refill end (a 45° ramp joins its inboard face to the shaft, so the spindle prints refill end up without support there) and three 6 × 6 mm arms and struts carrying a fixed flat stop ring at the drive end; the struts share the ring's inner radius. The collar screws onto the boss and carries the mirrored arms and stop ring. Each ring has a flat face (Ø54–62, 1.7 mm flange) at |X| 29.8, half the measured hub-face width D 59.6 mm, and a 2 mm Ø54 pilot with a 0.5 mm lead-in that enters the bore loosely (0.5 mm radial to the assumed Ø55 bore); only the hub faces are measured, so the bore, its chamfer and the recess opening are assumptions. The thread is custom (Ø18 major, 3 mm pitch, right-hand), fitting only this collar, not a standard M18 nut. A positive lock holds the collar in both turning directions, so the spool may feed and rewind either way: twelve slots through the spindle's thread crests (root intact), and a key on a 1 mm compliant arm in the collar wall that rests in one slot. The arm's pocket runs out through the collar's inboard end and the closed guide-hole roof sits 0.75 mm above the key, so neither prints as a roof just above the arm or key. Lifting the key 1.15 mm frees the collar: push the paddle toward the arm's root (about 1 mm, roughly 4 N in a beam estimate); the curved arm swings the key outward. Arm-root strain is then about 1.1% at a sharp corner (estimate, untested). Lock positions are every 30° (0.25 mm of travel). Key play in its slot and guide hole lets the collar turn about ±4° (about ±0.034 mm of axial back-off) before it stops; it cannot keep unscrewing. To clamp, turn the collar with the key lifted only until both stop faces just meet the hub faces, then let go and keep turning forward until the key drops into the next slot; never tighten firmly first and never back off to the previous slot. That forward index can add up to one lock step (0.25 mm), roughly 23–40 N of clamp depending on the assumed modulus and beam model; the actual value needs a physical trial. The stop faces clamp the hub faces; the pilots only guide, and the clamp force closes through spindle, thread and collar, not the 608s. The collar travels 2.0 mm outboard and 5.0 mm inboard, clamping hub-face widths 54.6–61.6 mm (measured 59.6 ± 2). The rotating unit floats ±0.5 mm axially (thrust-sleeve gap 0.2, 608 seat 0.1, carrier tongue 0.2); the stop rings keep ≥2.5 mm to the frame plates at any float. At its outboard limit, full float and the 0.25 mm thread flank clearance (the clamp pushes the collar outboard through it), the collar swept through a full turn keeps 0.25 mm to the left carrier and to the frame. Both plates' inner faces are relieved 0.5 mm (3 → 2.5 mm) in the spool flange sweep, R34–R101 about the axle; the carrier heads and slots keep 3 mm. The working faces are 70 mm apart: 1.1 mm per side to the measured 67.8 mm spool width, 0.6 mm at full float. An assumed 1.25 kg spool loads each relieved plate member about 2.4/w MPa in-plane (w = member width, mm). Out-of-plane loads (anchor magnet pull, hand loads) enter at the carrier heads and reach the base through the relieved legs, whose bending strength is ×0.694 and stiffness ×0.579 of the 3 mm section; the spool clamp closes internally through spindle, thread and collar, not through the frame. These are section ratios, not FE or qualification. The earlier beam screen (≤0.23 MPa per newton of clamp force in the ring, struts and arms) was for the cone ring and has not been redone; the flat flange's root adds at most about 0.05 MPa per newton with all load at its outer edge. Neither is an assembly limit: the lock key's crest bearing (roughly 0.3–0.45 MPa per newton, worse if the key is partly raised under load) would govern at a lower force. No clamp-force or torque capacity is qualified; tighten by hand only. Hold the spool near the collar end when turning the collar so the torque bypasses the spool's two-half twist-lock. Spool change: lift the whole unit out, pull the left carrier off, slide the left 608 off its journal (Ø7.9 printed slip fit, needs a physical trial; the right journal keeps nominal Ø8 with the disc key and clip groove), keep the key lifted with the paddle and unscrew the collar about 4.2 turns from nominal and slide the spool off toward the refill side; reverse to refit. CAD solid volume is 22.6 cm³ (spindle 14.7, collar 7.9; r5 was 19.3); the seven-part holder plate is prepared for a gentle first fit ([PRINTING](PRINTING.md)).

Disc and clip (square drive, 17 November 2026, after the first disc slipped on the shaft): the drive journal outboard of the 608 has four flats 6.4 mm across, with Ø8 corners, so the 608 still slides over it and still sits on the round Ø8 journal. The disc's square socket is 6.7 mm across flats, so the corners reach 0.65 mm past the socket flats (the earlier six shallow flats engaged only 0.10 mm). The flats sit at the clip-groove root, so the groove neck stays a full Ø6.4 circle and the U clip snaps the same at any key angle. Its mouth is 6.0 mm, a 0.2 mm snap per jaw (was 0.1). The clip enters through the disc's side channel into the journal groove; four corner lugs outboard of the groove (4.4 mm² under the actual clip) hold the clip and disc against the wheel magnets' pull. The drive tip (X42.7–43.2, printed on the bed) has a 0.5 mm 45° chamfer on its corners and flat edges so bed flare cannot jam the 608 or the socket; the lugs (X41.8–42.7) and the end at X43.2 are unchanged. Three Ø15 × 3 mm magnets sit in 3.9 mm pockets behind 1.3 mm covers.

Native checks (`stand.py`) cover single-solid validity, zero nominal overlap between all parts, a collision-free 0.2–120 mm lift, spindle and collar running clearance to the frame and carriers across the ±0.5 mm axial float, sampled every 10° over 0–110° (one period of the three-fold spindle and collar bodies; the single lock paddle breaks that symmetry, and a computed full-turn sweep of the whole collar at its outboard limit, full float and thread flank clearance keeps ≥0.25 mm to the left carrier within its 19.24 mm radial reach and to the frame), the collar thread clear of the spindle across its travel while following the helix, the anchor branches (≥2.0 mm from the turning disc, nothing in the disc's straight-up lift corridor |Z| < 40.5 above the axle, a magnet fits each pocket), the drive key (the disc stops within 3.75° turned either way, the 608 and disc slide over the key, the groove neck is a full circle, the clip passes the disc channel and must spread over the neck at 0°, 22.5° and 45° key angles, and the clip holds the disc outward within 0.3 mm on 4.36 mm² of lug face, measured with the actual clip and its mouth, and inward against the 608), and the collar lock (key clear in its slot at lock positions, colliding when turned 5° either way, clear of the crests when lifted; the lifted key is a rigid radial illustration, while the real curved arm tilts the key, which stays within its guide-hole clearance by about 0.04 mm in a beam estimate). `stand.py` also checks the stop faces sit at D/2 with collar travel covering D ± 2 mm, and that no frame material remains in the relief. `spool_fit.py` checks a measured-spool envelope (A 67.8 and D 59.6 measured; Ø55 bore, Ø80 recess opening and Ø200 rim assumed from Bambu's published printable model, whose flush 67.4 mm hub is recorded separately and sets no datum): both stop faces bear on the hub faces with zero nominal overlap, the flanges clear the frame through the float, and the spool slides on, the collar runs in and the spool lifts out. They do not cover the real bore, chamfer or recess, thread fit, clamp torque, strength, carrier retention or printability.

Unresolved: gravity-only carrier retention and guide strength; spool seat beyond A and D (bore, chamfer and recess unmeasured; first fit, not qualification); printed thread, left-journal slip fit and collar lock (arm spring, strain, wear); physical support removal and fit of the prepared seven-part holder plate; container fit of the taller frame; bottom-side desiccant baskets remain to be designed.

Run on their own, `stand.py --output DIR` builds and checks the holder, and
`spool_fit.py --native DIR --spool SPOOL --output FILE` checks the spool against it.
`spindle_print.py --native-input DIR --engineering-root CASTLE --bambu STUDIO --output OUT`
prepares the spindle/collar plate; add `--scope holder --variant critical-tree-slim` for all seven holder parts.

`stand.py` writes each part's STEP, `stand.step`, `stand-build.json` and `stand-display.json` (schema `drybox-holder-native-v2`). `spindle_print.py` orients the spindle drive end down and the collar stop face down on one H2D plate and slices it offline with the factory 0.20 mm Standard, PLA Basic and Textured PEI presets plus critical-region support, default and tree-slim styles; it never sends a print, and its settings are not approved for fabrication. `--print-prep` adds that plate, its support roads and 3MF downloads to the preview.

## Outlet and filament clip

See [outlet print preparation](OUTLET-PRINTING.md) for the body, nut, cap and
filament clip. `cad/outlet.py` / `outlet.json` own the bulkhead and cap assembly;
the purchased fitting is a dimensional envelope, not manufacturer CAD. Its exact
packaging specifies PT 1/8, 7 mm of thread and 18 mm overall length. The printed
fitting socket follows the nominal shoulder-seated tapered interface. Its native
solid and fabrication mesh pass the geometric checks; printed engagement still
requires the first fit trial. A 45° internal funnel removes the socket ledge,
so the checked slice needs no internal supports; exterior body supports remain.

`cad/clip.py` / `clip.json` now define an original 5 mm thick clip for the
straight drybox tail. Two captured printed bodies provide a fixed cradle,
broad rigid moving jaw and curved releasable click latch with a blunt, backed
hook. The short gripping spring has been removed; only the outside latch is
intended to flex. No downloaded mesh,
spool mount, extra stop or bought hinge pin is used. The prior C-leaf clip failed
because its hook never caught; the old sliced plate is not a current clip input.
The trimmed third-party reference is also superseded. Current exports are
native design references; printability and physical grip remain unqualified.
See [outlet print preparation](OUTLET-PRINTING.md) for current files and checks.

## Outside drive

Founder-selected 17 November 2026 so the handwheel no longer turns against the container; the previous wheel is in commit 7f54693. `cad/wheel.py` builds four printed parts from `wheel.json` and `stand.json` (`magnets`, `mount`), measured from the wall's outside face:

- **Fixed X:** a hub and four diagonal arms 3 mm thick under the wheel, with four 4 mm cups beyond the wheel's R60 sweep (cup edge R67.5). Each cup has a glue pocket for one Ø15 × 3 magnet, open to the wall. One solid also carries the Ø11 inner-ring shoulder and the Ø7.9 journal with its clip groove.
- **Handwheel:** the earlier spokes, rim and magnet cups, starting 4 mm farther out (3 mm X + 1 mm running gap). The knob is 4 mm shorter, so its tip stays at X67.15 with a 9.45 mm exposed grip (was 13.45). A 608 hub opens toward the wall, with a 1 mm lip of inner diameter 19.6 that bears on the outer ring and carries the magnets' inward pull. A groove behind the 608 holds the retainer ring, and one lip notch lets the axle clip in.
- **Retainer ring:** a printed internal split ring that holds the outer ring when the knob is pulled. It is squeezed 0.7 mm through the bore, closing 4.4 of its 6 mm gap (about 0.6% bending strain, estimate).
- **Axle clip:** a radial U clip like the disc's, with an Ø11 outer edge, so it bears on the inner ring only (0.1 mm jaw snap each side).

Retaining faces stay within SKF's 608-2Z abutment ranges ([SKF 608-2Z data sheet](https://www.tme.com/Document/f588dfef35358a8c89b0e2ea5d52848a/608-2Z.pdf)), clear of the shields: shaft side Ø11 (da 10–12, inner land 12.15), housing side Ø19.6 (outer land 19.2, Da max 20). The purchased bearing's lands are not measured. Each ring floats 0.3 mm axially, so nothing preloads the 608. The drive-magnet face gap is 10.1 mm at a nominal 2 mm wall (6.1 mm before the X); coupling torque is not evaluated.

Assembly:

1. Glue one magnet into each X pocket and each frame pocket, faces flush with the wall face (the 3.1 mm pocket leaves 0.1 mm for glue). Mark matching faces so every frame magnet attracts its X magnet through the wall, and check every pair before the glue sets.
2. Slide the 608 into the wheel's Ø22.4 hub pocket (0.2 mm radial clearance) from the wall side. Fit the retainer ring.
3. Slide the wheel onto the journal. Turn its lip notch to the clip and push the clip into the groove.
4. Set the X on the wall's outside face, lined up with the frame branches.

Because the anchor magnets hold the frame to the wall, remove the X before lifting the whole frame out. The spindle unit still lifts out on its own.

Untested: coupling torque, anchor holding force and X tilt stiffness, glue retention, the printed 608 fits, retainer and clip snap strength, and how the taller frame fits the container. None of these parts is ready to print; see [PRINTING](PRINTING.md).

## Superseded material (not current print inputs)

Kept for history only. Do not print any of these as current parts.

- **Original fixed stand and green rotating desiccant core:** replaced by the holder above. `preview/simple-axle/`, `cad/stand_sections.py` and `preview/prepare_print_view.py` belong to the superseded four-part plate in [PRINTING](PRINTING.md#superseded-four-part-holder-fit-print-proposal). `cad/stand_print.py` and `cad/stand_prepare.py` also prepared that plate; `spindle_print.py` still reuses their helpers.
- **High-flow center cartridge:** replaced by the spindle and collar. This covers [CORE-PRINTING.md](CORE-PRINTING.md), `cad/high_flow_journals.py`, `cad/adapt_high_flow_core.py`, `cad/prepare_high_flow_core.py` and `requirements-core.txt`.
- **First (C-leaf) filament clip:** printed 15 Nov 2026; its hook never caught, and it is replaced by the two-body clip. `preview/outlet-tail/` shows the earlier outlet and clip; its payload producer is not maintained here.
