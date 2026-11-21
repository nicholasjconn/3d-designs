# Filament drybox

Current design: a bearing-supported spool spindle with a removable through-wall
crank and a stationary sealing cap. The magnetic drive was superseded after
reported rubbing and weak coupling. The canonical current source is
`cad/drybox.py`, with shared datums in `cad/direct_drive.json` and the part
inventory in `cad/drybox.json`. Generated files belong in ignored `build/`.

## Current parts

| Part | Geometry source | Current action |
| --- | --- | --- |
| Stand with nut channel | `cad/direct_stand.py` | Frozen base attachment for two removable desiccant boxes; stand-only fit print prepared |
| Left and right608 carriers | `cad/bearing_carrier.py` | Right revised; left unchanged from widened sliding version |
| One-piece axle | `cad/direct_spindle.py`, helpers in `spindle.py` | Print the next axle in PETG |
| Locking collar | `cad/spindle.py` | Print the matching collar in PETG |
| Inside wall nut | `cad/inside_nut.py` | Print compact flanged version |
| Removable crank | `cad/direct_crank.py` | One matching crank can serve multiple dryboxes |
| Wall fitting | `cad/wall_fitting.py` | Two fixed grip tabs for holding the fitting while turning the cap; fit-test pending |
| Sealing cap | `cad/sealing_cap.py` | Six rounded grip spokes on the crank storage cap; same thread and seal seat |
| Filament outlet body and locknut | `cad/outlet.py`, `outlet.json` | Matched pair for the same 3/4″ wall hole as the crank |
| Filament outlet storage cap | `cad/outlet.py`, `outlet.json` | Reuse |
| Filament barrel stop | `cad/clip.py`, `clip.json` | Wider print and seating foot with the selected 2.025 mm bore |
| Desiccant box and refill cap | `cad/desiccant_box.py`, `cad/desiccant_cap.py` | Flat refill wall and flush coin-slot cap. Fit-test one pair. |
| Screw-in refill funnel | `cad/desiccant_funnel.py` | Shared by both boxes. The longer threaded stem fits the flush port in CAD. |

Use two 608 bearings (8 × 22 × 7 mm), two 22 × 2 mm wall O-rings, one 20 × 2 mm
crank cap O-ring and one 18 × 2 mm outlet cap O-ring. Ring sizes are inside diameter × cross-section.
No magnetic drive parts or shaft retaining clips
are used by the current direct-drive assembly.

## Dimensions and physical limits

Axes: X along the axle, Y upward, Z transverse; axle at Y104 mm. Uprights are
74.8 mm apart. The measured67.8 mm spool flange span has3.5 mm centered clearance
per side, or3 mm after the conservative modeled±0.5 mm axial float. The hub
face width is measured59.6 mm. BoreØ55, recessØ80 and outsideØ200 remain reference
assumptions, not measurements of the owner's spool.

The marked outside-left-stand to inside-container-wall span is84.6 mm; stand
alone84.4 mm. The inside nut is4.2 mm axially, its solid flange1.6 mm; the gray
outboard retaining plate is2.2 mm thick and overlaps the flange2.4 mm radially.
The drive-side bearing sits at X28.3–35.3 mm and its carrier back at X40.2 mm.
The carrier and nut meet at that stationary plane with zero nominal gap;
printed faces may need cleanup. The drive key ends at X39.2 mm, giving1 mm
before the nut and3.8 mm nominal engagement in the removable crank (at least3.4 mm at the modeled axial-play limits). The running crank shaft isØ8.8 through theØ10.4 fitting bore, giving0.8 mm nominal radial clearance; a short neck transition reaches0.7 mm at the most outward modeled float. The socket ends1 mm past the nominal axle tip. The stationary cap has six grip spokes on a Ø44 mm envelope and keeps its original thread and seal seat.

The wall is assumed2 mm, not measured. The printed custom matching thread is
Ø18 major,2 mm pitch, with3 mm overlap (1.5 turns) at that wall thickness.
Both fittings use 3/4″ (19.05 mm) holes. Each wall face groove has a Ø22.4 mm
inner shoulder, Ø28 mm outer edge, 1.5 mm depth and 2.8 mm radial width.
The crank cap face groove uses the same depth and width on a Ø20.4 mm shoulder
with a Ø26 mm outer edge. The 20 × 2 mm ring clears the Ø18 mm thread on the way in.
The wall fitting has two rounded 12 mm wide tabs across a 65 mm tip span.
Each extends 10.5 mm beyond the sweep of the cap spokes. Hold the fitting at
the tabs while turning the cap so the inside nut stays clamped. Both threads
remain right-handed. Verify finger access and continued wall clamp on the actual tub.
Finger-snug assembly only; no tightening-torque or printed-strength rating is
established. Hole alignment, actual wall/spool fit, support removal, collar lock,
loaded rotation, wear, creep and sealing remain physical checks.

Remove the crank before lifting the axle, spool, bearings and carriers as a
unit. Carriers intentionally slide upward without snaps. The fixed stand and
wall nut remain in place. First tighten the wall fitting and inside nut with open hand access, then lower the stand over the nut flange. The channel is open upward. For spool replacement, remove the left carrier and
608, lift the collar paddle and unscrew the collar. Do not pry on the nut flange.

## Desiccant attachment

The stand has two through-open T-key sockets at each end of its base.
Future box closures stay on the boxes and must preserve this frozen attachment.
Each box lifts 2.9 mm, then pulls outward; it does not require spool removal.
The matching key dimensions and 0.35 mm socket allowance are authored in
`cad/direct_stand.py`. Socket fit and actual container service room still need
physical checks.

The vented box is 80.4 mm wide. Its coin-slot cap sits flush between the
mounting keys and threads into a 6.47 mm end wall. The chamber face is flat all
the way to the bore, with about 58.6 mL of CAD fill volume below the opening.
The new box takes the matching coin-slot cap. The two docks take identical
boxes rotated 180° about the vertical axis.

Grip the sides to lift and remove the box, then stand it on the broad flat
outer face with the port facing up. Use a U.S. quarter to start turning the cap.
The shared 56 mm screw-in funnel retains its 6.55 mm stem and 2.4 mm thread
pitch. Cap engagement, emptying and funnel fit still need a physical check.

Export the box, cap and funnel separately from the stand and spindle:

```sh
python filament-drybox/cad/desiccant.py --output build/filament-drybox/desiccant
```

See [the desiccant refill print guidance](PRINTING.md#desiccant-refill-parts).

## Physical fit checks

- Check both 608 bearings on the PETG journals, the collar lock in both directions,
  and free rotation with a loaded spool. Verify the loaded assembly at the intended
  drying temperature before relying on it for hot drying.
- Check the crank wall fitting, inside nut and both O-ring seats after removing
  support. Hold the tabs when turning the cap and check that the wall clamp stays
  tight. Check the outlet and the clearance under its storage cap.
- Check that each coin-slot cap seats flush and opens with a quarter, the funnel
  seats and holds, and a small bead charge pours out cleanly.
- The TP49 did not fit with the spool installed. The container sits lid-down.
  Check any future sensor mount for loaded-spool clearance, visibility and vent access.

## Build and check

Use a Python environment with the repository requirements (CadQuery, NumPy,
manifold3d). From the repository root:

```sh
python filament-drybox/cad/drybox.py --output build/filament-drybox/direct-drive-current
python filament-drybox/cad/direct_mechanics.py --output build/filament-drybox/direct-drive-current/mechanical-screen.json
```

The first command rebuilds the direct-drive assembly from authored geometry, validates
single solids and checks rotation, float, lift-out, crank extraction, thread
run-in and positive stops. It writes source/output identities and assumptions.
There are no prior STEP or agent-workspace prerequisites. Add `--with-outlet`
or `--with-clip` to include the outlet or barrel stop.

The local lip/flange cantilever calculation is a limited hand-load sensitivity
screen. It is not FE, a material allowable or physical strength qualification;
previous frame simulations do not apply to this changed stand.

See [print preparation](PRINTING.md) for the matching plate, configuration,
material accounting, review and first physical checks. `preview/direct_geometry.py`
builds the current assembled, separated, actual-section and individual print
views from the exact native and fabrication inputs.

## Superseded sources

`stand.py`, `stand.json`, `wheel.py`, `wheel.json`, the old holder/printing
previews and `spindle_print.py` recipes belong to the earlier magnetic designs.
They are not current geometry or print entry points. Some unchanged generic
mesh/slicing helpers in `stand_print.py`, `stand_prepare.py` and
`spindle_print.py` are reused by `direct_prepare.py`; their earlier part recipes
are not used. Earlier center-desiccant and magnetic-drive variants are not
current fabrication inputs. See [OUTLET-PRINTING.md](OUTLET-PRINTING.md)
for the outlet and the current clip fit print.
