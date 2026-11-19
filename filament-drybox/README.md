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
| One-piece axle | `cad/direct_spindle.py`, helpers in `spindle.py` | Print matching recessed drive journal/key |
| Locking collar | `cad/spindle.py` | Deeper lock geometry; version of existing print uncertain |
| Inside wall nut | `cad/inside_nut.py` | Print compact flanged version |
| Removable crank | `cad/direct_crank.py` | Print matching longer shaft and deep socket |
| Wall fitting | `cad/wall_fitting.py` | Same shape; included on full nine-part plate |
| Sealing cap | `cad/sealing_cap.py` | Same shape; included on full nine-part plate |
| Filament outlet body, locknut, storage cap | `cad/outlet.py`, `outlet.json` | Reported working; reuse |
| Filament clip | `cad/clip.py`, `clip.json` | Revised flat-jaw fit prototype |
| Desiccant box and refill cap | `cad/desiccant_box.py`, `cad/desiccant_cap.py` | Fit-test one pair |
| Refill funnel | `cad/desiccant_funnel.py` | Optional, print one for both boxes |

Two purchased608 bearings (8 ×22 ×7 mm), one22 ×2 mm wall O-ring and one18 ×2 mm
cap O-ring remain required. No magnetic drive parts or shaft retaining clips
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
before the nut and3.8 mm nominal engagement in the removable crank (at least3.4 mm at the modeled axial-play limits). The running crank shaft isØ8.8 through theØ10.4 fitting bore, giving0.8 mm nominal radial clearance; a short neck transition reaches0.7 mm at the most outward modeled float. The socket ends1 mm past the nominal axle tip. The overall crank length and stationary cap are unchanged.

The wall is assumed2 mm, not measured. The printed custom matching thread is
Ø18 major,2 mm pitch, with3 mm overlap (1.5 turns) at that wall thickness.
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

The vented box is 80.4 mm wide and has a recessed threaded cap between the
keys. Grip the sides to lift and remove it. Stand it on the flat outer face,
undo the cap and pour through the 14.3 mm opening. The optional funnel locates
in that opening. The CAD fill estimate is about 51 mL per box. The two docks
take identical boxes rotated 180° about the vertical axis. Start by printing
one box, one cap and one funnel. The box prints on its normal floor, the cap
with its spokes down, and the funnel with its wide mouth down.

Export these three parts separately from the stand and spindle:

```sh
python filament-drybox/cad/desiccant.py --output build/filament-drybox/desiccant
```

See [the desiccant fit-print settings](PRINTING.md#desiccant-fit-print).

## Build and check

Use a Python environment with the repository requirements (CadQuery, NumPy,
manifold3d). From the repository root:

```sh
python filament-drybox/cad/drybox.py --output build/filament-drybox/direct-drive-current
python filament-drybox/cad/direct_mechanics.py --output build/filament-drybox/direct-drive-current/mechanical-screen.json
```

The first command rebuilds every current part from authored geometry, validates
single solids and checks rotation, float, lift-out, crank extraction, thread
run-in and positive stops. It writes source/output identities and assumptions.
There are no prior STEP or agent-workspace prerequisites. Add `--with-outlet`
or `--with-clip` to include the outlet or clip.

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
