# Print-in-place manual feeder enclosure

The tray fits the 608 idler version of the Lao Teng manual feeder. Two cams
print captive on the tray and turn by hand to compress the lid gasket. The
lid lifts off with both PTFE tubes connected. Tapered braces support the cam
mounts and the underside of each tube socket.

## Generate the enclosure

Install the Python 3.12 dependencies from `requirements-core.txt` in the
repository's virtual environment. Run the generator from the repository root.

```sh
.venv/bin/python manual-feeder/enclosure.py
```

The generator uses the repository's drybox outlet geometry for the HANGLIFE
PT 1/8 push-fits. It writes `tray-with-captive-cams.stl`, `lid.stl`, and
`checks.json` to `build/manual-feeder/`.

## Print and assemble

The first prototype uses PLA Basic on the Bambu Lab H2D with a 0.4 mm nozzle,
0.20 mm Standard layers, and Textured PEI. Print the tray with its groove up
and the lid with its rim down. The tested slim-tree slice placed supports
around the lid roof and rim. The tray uses the small breakaway ribs built
into the model to start each cam.

After the parts cool, free the cams from the ribs and check they turn by
hand. Install the AS568-132 O-ring (44.12 mm ID × 2.62 mm cross-section) in
the 3.90 × 2.05 mm groove. Seat the lid and turn both cams to their stops.
Verify that the lid seats evenly at the tube ends and check for leakage.

## References

This repository contains the original enclosure CAD. Obtain the separately
licensed feeder body through [Boss_Design’s MakerWorld listing](https://makerworld.com/en/models/3295848-lao-teng-manual-feeder-ultimate-upgrade-smooth-jam).
The creator’s model uses the MakerWorld Standard Digital File License.

The latch mechanism references [Southco’s quarter-turn compression latch](https://southco.com/en_gb_int/latches/compression-latches/emvise-actionemreg-latchesp/e9-quarter-turn-compression-latches)
and [Xem Studio’s captive print-in-place axle](https://www.xemstudio.com/objects/print-in-place-captive-wheel-axle/).
