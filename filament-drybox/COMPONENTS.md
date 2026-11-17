# Prototype components

Purchased and container items for one drybox. The printed parts, their sources
and latest print states are in [`cad/drybox.json`](cad/drybox.json) and the
[README](README.md#current-parts-and-sources). This is not a released assembly
specification.

| Component | Quantity | Current selection / interface |
| --- | ---: | --- |
| Gasketed food-storage container | 1 | Actual usable interior, taper and wall thickness must be measured. The CAD study uses synthetic dimensions. |
| 608ZZ bearing | 2 | YAMASO or equivalent, 8 mm bore × 22 mm OD × 7 mm width. Printed bearing fits remain unqualified. |
| Axially magnetized neodymium disc | 6 | 15 × 3 mm, three in the disc and three in the outside wheel at 30 mm radius (`stand.json` `magnets`); [selected example](https://www.amazon.com/dp/B0FNX636SK). Actual coupling and adhesive retention need testing. |
| Pass-through push-fit fitting | 1 | [HANGLIFE pack sold as PC4-M10](https://www.amazon.com/dp/B0DQ7W6CGR), for 4 mm OD tube. Its packaging drawing specifies a PT 1/8 thread, 7 mm long, 18 mm overall; "M10" is not used as a thread specification. The outlet's printed socket is R 1/8-compatible (`outlet.json` `purchased_interfaces`). Verify the received thread and full tube passage at the first fit. |
| PTFE printer lead | As routed | 4 mm OD × 2.5 mm ID; [selected example](https://www.amazon.com/dp/B0F5HG7659). One continuous removable lead; the final length depends on the printer route. |
| NBR O-ring | 2 | 18 mm ID × 2 mm cross-section: one wall seal and one cap seal. Kit hardness/tolerances and printed sealing remain unqualified. |
| Humidity monitor | 1 | [TempPro / ThermoPro TP49](https://www.amazon.com/dp/B07WCR5Y4B), initially a trial candidate. A displayed minimum of 10% RH does not establish accuracy below that limit. |
| Refillable desiccant | As tested | Orange indicating silica gel; [selected example](https://www.amazon.com/dp/B01I5Y2DG6). Installed mass and bead-retention openings are unfinished. |
| Desiccant baskets | Not designed | Bottom-side baskets are still to be designed; the holder carries no desiccant. |

The magnets sit behind closed printed skins. Their rear faces are glued into
open pockets; no magnet-cover screws are part of the current concept.

The stand references the drive wall through the surrounding stationary lip; redundant rounded noses and their support wings are removed. There are
no opposite-wall spring arms. Any local contact pad or container-specific
spacer would be a later tested change.

## Qualification still required

- Actual container fit, floor corners, taper, lid access and wall gaps.
- Bearing seating, retention and removal; spindle/collar clamp, thread and lock.
- Wall-stop/frame deformation, full and nearly empty spool stability, and stand
  position with the outside wheel removed for printing and during reattachment.
- Useful magnetic rewind torque, wall friction/wear and adhesive retention.
- Actual fitting thread, bidirectional tube retention and loading ergonomics.
- Functional all-plastic clip geometry, grip and cycling with the supported
  filament types.
- Capped leakage and RH retention; the connected printing path is not claimed
  hermetic.
