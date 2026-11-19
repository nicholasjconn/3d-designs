# 3D designs

Original parametric designs, printable models and practical build notes.

Each project has its own folder, CAD source and parameters. Generated models,
sliced projects and local print evidence live in ignored `build/` directories.
Use a committed source revision and retain the exact project sent to the printer
when making a physical prototype.

## Projects

- [Filament drybox](filament-drybox/README.md): a passive spool holder with a
  bearing-supported spindle and removable through-wall crank. Matching compact
  stand, carriers, spindle, collar, nut and crank are prepared for a physical fit test.

## Tools

CAD uses Python 3.12 and CadQuery 2.8.0. Install project dependencies in a local
virtual environment:

```sh
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
```

Bambu Studio is used for print preparation. A slicer project records the actual
printer, nozzle, filament, orientation, process and support selections. A CAD
clearance check does not establish printed fit or mechanical performance.

## Licensing

Copyright © 2026 nicholasjconn. Unless a file states otherwise, original designs,
CAD source, previews and documentation are licensed under
[Creative Commons Attribution-NonCommercial 4.0 International](LICENSE)
(`CC-BY-NC-4.0`).

You may use, share and modify this material for noncommercial purposes with
attribution and an indication of changes, subject to the license terms.
Commercial use requires separate permission; contact
[nicholasjconn on GitHub](https://github.com/nicholasjconn) to discuss it.
The public license does not include a commercial license or a revenue-sharing
agreement.

Third-party material retains its own license and attribution. This license
grants only the rights the author holds; it does not grant patent or trademark
rights. See the [full license](LICENSE) for the governing terms.
