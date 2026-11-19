# Preview source

The current preview is `holder/` (the authored page and viewer) together with
`holder_geometry.py`, which generates its data. It shows:

- the holder assembly, with lift-out, separated, carrier, spindle-and-collar section, collar lock and spool-change views;
- a *Whole kit* view with the outside handwheel and the outlet in its printing and storage configurations;
- the spindle/collar print plate with actual support paths;
- the current part inventory and the connection checks between systems.

Build it as described in the drybox [README](../README.md#build-and-check):

1. Run `cad/drybox.py`.
2. Run `npm ci` here, which installs the Three.js version pinned in `package.json` / `package-lock.json` (0.169.0).
3. Run `holder_geometry.py --native <current>/holder --system <current> --output <site>`.

The generated site directory holds everything it needs: `geometry.json`, the page, and `vendor/` (copied from `node_modules`, with Three's license). Serve it over HTTP. With `--spool` the output contains Bambu's printable spool meshes and stays private.

The generated payloads are derived; the CAD in `cad/` governs the parts.

## Superseded pages (not maintained)

These pages are kept for history and are not current print inputs. Their generated payloads came from producers that are no longer maintained, so they are not reproducible from this checkout.

- `simple-axle/`, with `prepare_print_view.py`: the four-part holder with the green core.
- `outlet-tail/`: the earlier outlet and C-leaf clip page. It expects `native-geometry.json`.
- `clip/`: the earlier two-body clip preview, with matching CAD at `68cfb8a`. The current barrel stop is described in [OUTLET-PRINTING.md](../OUTLET-PRINTING.md#barrel-stop-fit-print).
