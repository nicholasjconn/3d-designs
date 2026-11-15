# Filament drybox

Original parametric CadQuery source for the current filament-drybox project. The stand is prepared for its first fit prototype in Bambu PLA Basic. See [print preparation](PRINTING.md) for the proposed factory-preset setup, support change, files and estimate. No print has been sent; strength and physical fit remain unqualified.

## Stand

`cad/stand.py` provides `build(config)` and a small export CLI. `cad/stand.json` is the canonical configuration, in millimetres: 98 × 110 × 8 open base, two continuous A-frames, open bearing cradles at axis height 104 and integral drive-side wall stops. Geometry is unchanged from the reviewed one-solid concept.

With Python and the repository-root `requirements.txt` CadQuery dependency available:

```sh
python filament-drybox/cad/stand.py
```

The default output is repository-local `build/filament-drybox/`, independent of the current working directory. It writes a native STEP, display mesh and geometry receipt. `--config` and `--output` accept explicit paths. Display triangulation uses absolute OCCT deflection; it is not a fabrication mesh or maximum-error guarantee. The generator imports no other repository.

Previous native checks established nominal one-solid connectivity, spool/rotor clearance and upward bearing service in synthetic cases. Portability regeneration checks identity against those results; it does not repeat or extend physical qualification. Actual container fit/taper, bearing support/capture, loads, stiffness, tipping, manufacturing allowances and wall contact remain unqualified. Printed-body connectivity is not strength evidence.

## Other parts: concept sources only

`cad/wheel.py` / `wheel.json` preserve the current original Ø120 handwheel with three Ø15 × 3 magnet pockets at radius 30. `build()` returns its single native solid. Adhesive retention, manufacturing tolerances and performance remain unqualified; it is not the current print-preparation target.

`cad/outlet.py` / `outlet.json` preserve the one-fitting continuous-lead concept. `build(config)` reconstructs the body, nut, short cap and reference assembly components without archived binary caches. Purchased fitting interfaces remain unfinished smooth pilots; the purchased fitting is a dimensional envelope, not manufacturer CAD. No outlet fabrication STL is supplied.

The clamp is only an illustrative preview: its hinge, latch, grip and native one-body geometry are not qualified here. The rotating desiccant core is also a visual concept without a native generator. These previews must not be presented as printable CAD. Only the stand is entering print preparation; no other part is approved for fabrication.


## Preserved concept preview

`preview/` holds authored HTML/JavaScript for the current core and clip concepts and assembly views. It does not yet run independently here: the pinned Three.js dependency, generated mesh payloads and serving integration are intentionally not bundled. See `preview/README.md`. These visuals do not supply missing native CAD or manufacturing qualification.
