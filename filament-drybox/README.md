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
| Holder | gray frame, two keyed carriers, spindle, locking collar, blue magnetic disc, disc retaining clip | `stand.py`, `spindle.py`, `stand.json` |
| Outside handwheel | wheel | `wheel.py`, `wheel.json` |
| Outlet | bulkhead body, inside locknut, storage cap | `outlet.py`, `outlet.json` |
| Filament clip | fixed jaw with hinge, moving jaw with latch | `clip.py`, `clip.json` |

Shared interface values have one owner, and the other parts read them:

- The magnet size, pattern and cups belong to `stand.json` `magnets`. `wheel.py` reads them, so the disc and the wheel always match.
- The filament clip's height and filament size are checked against `outlet.json` `tail`.
- The 608 bearings, disc key and clip groove are all in `stand.json`.

Purchased:

- two 608ZZ bearings;
- six Ø15 × 3 mm magnets;
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
  [--spool /private/path/to/bambu-spool] [--reference-build build/<holder build a print was sliced from>]
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
- the magnet face gap through 1, 2 and 4 mm walls;
- the wheel stays clear of the holder;
- the PTFE lead passes the outlet body, fitting and nut;
- the closed clip fits inside the storage cap;
- optionally, the holder parts match a reference build exactly.

It writes `system-checks.json`, `system-display.json` and `manifest.json` (source
and output SHA-256, producer reuse, environment, inventory). The holder's own
checks are in `holder/stand-build.json`.

`holder_geometry.py` copies the pinned Three.js 0.169.0 runtime from
`preview/node_modules` into the generated page. With `--spool` the output contains
Bambu's printable spool meshes and stays private.

## Holder

`cad/stand.py` / `cad/stand.json` are the canonical holder source: one spoked gray frame, two removable keyed bearing carriers, a printed spindle and threaded collar (`cad/spindle.py`), the keyed blue magnetic disc and the printed retaining clip, plus two purchased 608 bearings. The earlier high-flow cartridge prototype ([CORE-PRINTING.md](CORE-PRINTING.md)) is superseded for this holder, as is the former green axle/core.

| Dimension | Endpoints along the axle (X) | mm | inches |
|---|---|---:|---:|
| W1: minimum inside wall span | Leftmost frame face −37.5 to drive-wall contact face +44.7 | 82.2 | 3.236 |
| B1: base edge to edge | Base −37.5 to +37.5 | 75 | 2.953 |
| Base front to back | Z−65 to +65 | 130 | 5.118 |

Frame: two A-frames on the 75 × 130 mm base, an open U-rim guard around the disc on the drive side with two upper spokes, R6 junction rounds, a central brace and three 45° rim undersides. Frame height is 128 mm and the axle is at 104 mm. The base keeps two smooth Ø8 × 18 mm blind pilot holes for future printed expansion screws.

Carriers: each frame plate has a 24.4 mm keyed vertical slot down to a flat floor 13.2 mm below the axle; its thinned edges run in the carrier's axial grooves. Each carrier holds one 608 in a C-seat (21.6 mm mouth, 0.2 mm jaw movement per side). Carriers, bearings, spindle, collar, spool, disc and clip lift out together; nothing stationary enters the spool bore. Carriers seat by gravity only.

Spindle and collar (r5; first-fit print sent 17 November 2026): the spindle is one part with both 608 journals, a Ø10 shaft, a threaded boss at the refill end (a 45° ramp joins its inboard face to the shaft, so the spindle prints refill end up without support there) and three 6 × 6 mm arms and struts carrying a fixed 3.5 mm-long 45° cone ring at the drive end; the struts share the ring's inner radius. The collar screws onto the boss and carries the matching arms and cone ring. The thread is custom (Ø18 major, 3 mm pitch, right-hand), fitting only this collar, not a standard M18 nut. A positive lock holds the collar in both turning directions, so the spool may feed and rewind either way: twelve slots through the spindle's thread crests (root intact), and a key on a 1 mm compliant arm in the collar wall that rests in one slot. The arm's pocket runs out through the collar's inboard end and the closed guide-hole roof sits 0.75 mm above the key, so neither prints as a roof just above the arm or key. Lifting the key 1.15 mm frees the collar: push the paddle toward the arm's root (about 1 mm, roughly 4 N in a beam estimate); the curved arm swings the key outward. Arm-root strain is then about 1.1% at a sharp corner (estimate, untested). Lock positions are every 30° (0.25 mm of travel). Key play in its slot and guide hole lets the collar turn about ±4° (about ±0.034 mm of axial back-off) before it stops; it cannot keep unscrewing. To clamp, turn the collar with the key lifted only until both cones just seat on the spool, then let go and keep turning forward until the key drops into the next slot; never tighten firmly first and never back off to the previous slot. That forward index can add up to one lock step (0.25 mm), roughly 23–40 N of clamp depending on the assumed modulus and beam model; the actual value needs a physical trial. The cones seat in the spool bore's end chamfers, centering and clamping the hub; that is the only spool contact, and the clamp force closes through spindle, thread and collar, not the 608s. The collar seats when 2 × Δ(bore radius + chamfer) − Δ(hub width), relative to the printable reference, lies within its −0.25/+6 mm travel; at the reference bore that is hub widths of 61.4–67.65 mm (reference 67.4 mm, design envelope 67 mm). The rotating unit floats ±0.5 mm axially (thrust-sleeve gap 0.2, 608 seat 0.1, carrier tongue 0.2); cones keep ≥0.5 mm to the frame plates at any float, 0.25 mm with the collar at its outboard limit, and the reference spool's hub faces keep 0.3 mm. A beam-theory screen with assumed values (not a qualification) gives ≤0.23 MPa per newton of clamp force in the ring, struts and arms; at an assumed 10 MPa sustained stress that ring/strut/arm-only screen is about 43 N. It is not an assembly limit: the lock key's crest bearing (roughly 0.3–0.45 MPa per newton, worse if the key is partly raised under load) would govern at a lower force. No clamp-force or torque capacity is qualified; tighten by hand only. Hold the spool near the collar end when turning the collar so the torque bypasses the spool's two-half twist-lock. Spool change: lift the whole unit out, pull the left carrier off, slide the left 608 off its journal (Ø7.9 printed slip fit, needs a physical trial; the right journal keeps nominal Ø8 with the disc key and clip groove), keep the key lifted with the paddle and unscrew the collar about 3.8 turns from nominal and slide the spool off toward the refill side; reverse to refit. CAD solid volume is 19.3 cm³ (r5 native build: spindle 13.1, collar 6.2), against 36.4 cm³ for the three adapted cartridge parts; the r5 tree-slim slice estimates 14.5 g useful, 3.8 g support and 18.4 g Studio total ([PRINTING](PRINTING.md)).

Disc and clip: unchanged. The disc slides onto the spindle drive journal's six flats (0.15 mm nominal clearance); the U clip enters through the disc's side channel into the journal groove. Three Ø15 × 3 mm magnets sit in 3.9 mm pockets behind 1.3 mm covers.

Native checks (`stand.py`) cover single-solid validity, zero nominal overlap between all parts, a collision-free 0.2–120 mm lift, spindle and collar running clearance to the frame and carriers across the ±0.5 mm axial float, sampled every 10° over 0–110° (one period of the three-fold spindle and collar bodies; the single lock paddle breaks that symmetry, and its full-turn clearance is analytical: at R ≤ 14.5 and X ≥ −25.75 at worst travel and float it stays ≥1.25 mm axially from the left carrier's inner face at X −27.5, R ≤ 14, at every angle), the collar thread clear of the spindle across its travel while following the helix, and the collar lock (key clear in its slot at lock positions, colliding when turned 5° either way, clear of the crests when lifted; the lifted key is a rigid radial illustration, while the real curved arm tilts the key, which stays within its guide-hole clearance by about 0.04 mm in a beam estimate). `spool_fit.py` checks the seated spool against Bambu's published printable spool model (contact only in the chamfer bands), sliding the spool on, running the collar in and lifting the spool out. They do not cover molded-spool dimensions, thread fit, clamp torque, strength, carrier retention or printability.

Unresolved: gravity-only carrier retention and guide strength; molded-spool seat (the cones are sized to the printable model's chamfers); printed thread, left-journal slip fit and collar lock (arm spring, strain, wear); the spindle/collar first fit (sent 17 November 2026, see [PRINTING](PRINTING.md); pick support out of the spindle's clip groove at fit); frame and carrier print preparation; bottom-side desiccant baskets remain to be designed.

Run on their own, `stand.py --output DIR` builds and checks the holder, and
`spool_fit.py --native DIR --spool SPOOL --output FILE` checks the spool against it.
`spindle_print.py --native-input DIR --engineering-root CASTLE --bambu STUDIO --output OUT`
prepares the spindle/collar plate.

`stand.py` writes each part's STEP, `stand.step`, `stand-build.json` and `stand-display.json` (schema `drybox-holder-native-v2`). `spindle_print.py` orients the spindle drive end down and the collar cone face down on one H2D plate and slices it offline with the factory 0.20 mm Standard, PLA Basic and Textured PEI presets plus critical-region support, default and tree-slim styles; it never sends a print, and its settings are not approved for fabrication. `--print-prep` adds that plate, its support roads and 3MF downloads to the preview.

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

## Outside handwheel

`cad/wheel.py` / `wheel.json` define the reinforced Ø120 handwheel: three 20 mm wide spokes, 7 mm structural depth and a common wall-facing front plane. Maximum overall depth remains 20.45 mm. Its three magnet pockets (Ø15 × 3 magnets at radius 30 behind 1.3 mm covers) come from `stand.json` `magnets`, the same values as the disc; the cutters pass through the thicker spokes so magnets can still be inserted. `build()` returns one native solid. The existing external central pad and actual wall compliance remain separate; adhesive retention and physical performance require testing.

## Superseded material (not current print inputs)

Kept for history only. Do not print any of these as current parts.

- **Original fixed stand and green rotating desiccant core:** replaced by the holder above. `preview/simple-axle/`, `cad/stand_sections.py` and `preview/prepare_print_view.py` belong to the superseded four-part plate in [PRINTING](PRINTING.md#superseded-four-part-holder-fit-print-proposal). `cad/stand_print.py` and `cad/stand_prepare.py` also prepared that plate; `spindle_print.py` still reuses their helpers.
- **High-flow center cartridge:** replaced by the spindle and collar. This covers [CORE-PRINTING.md](CORE-PRINTING.md), `cad/high_flow_journals.py`, `cad/adapt_high_flow_core.py`, `cad/prepare_high_flow_core.py` and `requirements-core.txt`.
- **First (C-leaf) filament clip:** printed 15 Nov 2026; its hook never caught, and it is replaced by the two-body clip. `preview/outlet-tail/` shows the earlier outlet and clip; its payload producer is not maintained here.
