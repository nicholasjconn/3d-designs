# Drybox-mounted manual feeder

This enclosure mounts the removable 608-version Lao Teng feeder at the
drybox's ¾-inch outlet. The keyed inlet bulkhead replaces the spool-side
push-fit and keeps the short PTFE liner aligned with the feeder. A shortened
printer-side outlet screws into the tray and takes the standard push-fit and
cylindrical storage cap. Two captive cams compress a reusable TPU lid gasket.

## Generate and print

Use Python 3.12 with `requirements-core.txt` installed. From the repository root:

```sh
.venv/bin/python manual-feeder/enclosure.py
```

The generator writes the meshes and interference checks to
`build/manual-feeder/`. It reuses the thread and seal geometry from
`filament-drybox/cad/outlet.py`.

- **PLA** · Tray with captive cams, lid, keyed bulkhead and short outlet.
  Import the tray's indexed `drybox-feeder-tray.3mf` as geometry. Keep the tray
  base down, the lid rim down, the bulkhead stem up and the short outlet's cap
  neck down, as exported. The existing drybox wall locknut and storage cap fit
  this revision. Their sources are in `filament-drybox/cad/outlet.py`.
- **TPU** · Perimeter gasket and inlet liner bushing. The lid gasket's nominal
  bead protrusion is 0.50 mm above the 1.36 mm recess.
- **On hand** · Two 22 × 2 mm face O-rings, one 18 × 2 mm storage-cap O-ring,
  one HANGLIFE PC4-M10 pass-through fitting with PT 1/8 thread and 4 mm OD PTFE.
  Reuse the working feeder center and its hardware.

The PLA prototype used an H2D with a 0.4 mm nozzle, 0.20 mm layers and slim
tree supports enabled. The horizontal outlet socket bridged without support
inside the thread. Check the socket and the cam gaps in the slice preview.
After cooling, remove loose support and check that both cams turn.

## Assemble

1. Drop the keyed bulkhead into the tray in the orientation set by its
   clipped corner. Slide the stem through the tray wall and mount the tray
   to the drybox with a 22 × 2 mm O-ring and the matching locknut.
2. Seat the push-fit in the short outlet, fit the other 22 × 2 mm O-ring behind
   the outlet flange and screw it into the tray by hand until the flange seats.
3. Snap the feeder into the tray with both PTFE runs out of the way. From
   inside the drybox insert the TPU bushing and the short inlet liner
   (about 44 mm of 4 mm OD × 2.5 mm ID PTFE). Pass the printer lead through
   the push-fit. Check that both square-cut tubes reach the feeder's original
   stops and that the wheel feeds freely.
4. Lay the TPU gasket flat in its groove. Set the lid down with both cams
   parked outward, then turn both cams closed.
5. For storage, release the printer lead and park about 20 mm of bare
   filament at the fitting. Seat the 18 × 2 mm ring in the smooth groove above
   the cap thread and screw the original cylinder onto the outlet. Check the
   assembled drybox for leakage before relying on the seal.

## References

This repository contains the original enclosure CAD. Obtain the separately
licensed feeder body through [Boss_Design’s MakerWorld listing](https://makerworld.com/en/models/3295848-lao-teng-manual-feeder-ultimate-upgrade-smooth-jam).
The creator’s model uses the MakerWorld Standard Digital File License.

The latch mechanism references [Southco’s quarter-turn compression latch](https://southco.com/en_gb_int/latches/compression-latches/emvise-actionemreg-latchesp/e9-quarter-turn-compression-latches)
and [Xem Studio’s captive print-in-place axle](https://www.xemstudio.com/objects/print-in-place-captive-wheel-axle/).
