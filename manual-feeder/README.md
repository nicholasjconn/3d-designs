# Compact 693 manual feeder

This revision keeps the original filament guides and both PTFE stops. The lower
roller is a bare 693 bearing. The existing upper 608 bearing, TPU thumbwheel,
and axle hardware transfer to the new center. Four ramped feet locate the
center. Pads under the lid keep the center seated when the lid is latched.

The keyed drybox inlet and locknut transfer from the printed assembly. The
storage cap threads directly into the tray around the integral socket for the
HANGLIFE PC4-M10. The fitting seals against the 4 mm PTFE printer lead.
Use PTFE pipe-thread tape on the tapered fitting-to-tray threads for the
cap-off seal test. The cap and drybox wall each use an existing 22 × 2 mm
face O-ring.

## Generate the model

Use Python 3.12 with `requirements-core.txt` installed. Download the original
[pneumatic latch profile 3740072](https://makerworld.com/en/models/3295848-lao-teng-manual-feeder-ultimate-upgrade-smooth-jam#profileId-3740072).
Pass the original 3MF to the generator.

```sh
.venv/bin/python manual-feeder/enclosure.py --source /path/to/pneumatic-latch.3mf
```

The generated parts and fit checks are in `build/manual-feeder/`. Keep the
MakerWorld model and its derived meshes private under the MakerWorld Standard
Digital File License.

## Parts for the prototype

| Part | Material | Details |
| --- | --- | --- |
| Tray and two captive cams | PLA Basic | Import the indexed `tray-with-cam.3mf`. The flange and tray base share the bed plane. |
| Lid | PLA Basic | Print rim down. The pockets fit over the four tapered guide posts molded into the tray. |
| Compact center | PLA Basic | The exported orientation keeps the guide along the build axis. |
| Perimeter gasket | TPU 95A | Print flat and seat it in the tray groove. |
| Inlet liner bushing | TPU 95A | Print flange down. The 4.46 mm stem bore allows for compression in the existing inlet. |
| Direct-to-tray storage cap | PLA Basic | Print closed end down. The rounded lip retains the 22 × 2 mm O-ring. |

Reuse the keyed inlet, wall nut, push-fit, PTFE, upper
drive, and two 22 × 2 mm O-rings. The bare 693 takes an M3 × 16 countersunk
screw (BelMetric SF3X16SS) and an M3 DIN 934 hex nut (BelMetric NR3SS-A4-50),
both listed in the Harker orders. Two captive cams draw the cover down
from opposite sides.

## Assembly

1. Lower the 693 into the center before transferring the upper drive. Insert
   the M3 screw from the countersunk side and snug the nut. The bearing should
   spin freely, with both shoulders clear of its outer race.
2. Seat the keyed inlet from above and slide it outward through the tray wall.
   Fit the wall O-ring over the raised inner rim and fasten the tray to the
   drybox with the existing nut. Seat the TPU liner bushing fully before
   feeding the 4 mm PTFE through it from inside the drybox.
3. Seat the center with both PTFE runs retracted. Wrap the tapered thread
   with PTFE pipe-thread tape and screw the PC4-M10 into the socket from outside
   the tray. Push both square-cut tubes
   through to their original stops. Check the feed with the lid off.
4. Lay the TPU gasket flat. Park both cams and lower the lid straight down.
   The four tapered posts guide it into position while it rests on the
   uncompressed gasket. Turn both cams closed to compress the gasket. Park
   both cams again and lift the lid straight up to remove it.
5. For storage, release the printer lead and leave about 20 mm of bare filament
   beyond the collet, including the portion through the optional barrel stop.
   The cap allows 23 mm from the collet to its blind end. Seat a 22 × 2 mm
   O-ring past the rounded lip in the cap groove and screw the cap into the
   tray by hand. For a dry leak test with the cap off, insert the printer
   lead and temporarily plug its far end. The tube bore is open during feeding.

Before preparing a full print, inspect support in Bambu Preview around the
captured cams and the horizontal socket. Leave support enabled at plate level.
Individual cam and socket fit prints can verify both features before a full
tray print.

For the outlet fit test, print `fit-test-receiver.stl` in its exported
orientation. It isolates the two horizontal threads at the same orientation
as the tray. Confirm the fitting starts cleanly, seats fully, and holds when
pulling gently on the installed tube. Use `storage-cap.stl` to check the
cap threads and parked tail clearance. Check the cap-off seal on the full
assembly with the far end of the printer lead temporarily plugged.
Check the new inlet bushing seated in the keyed inlet with a square-cut tube.
Check that the cap O-ring stays seated with the cap held groove-down.
