# Concept preview source reference

This directory preserves the original authored HTML/JavaScript for the current rotating desiccant core, spool/stand context, one-fitting outlet and all-plastic clip. It is **not yet a self-contained working preview** in this repository. No fake core/clip CAD generator is implied by preserving the display code.

- `simple-axle/`: whole drybox, continuous-lead printer context and native stand/wheel viewers. The core, spool and some purchased-part shapes are illustrative geometry.
- `outlet-tail/`: assembled/exploded/section outlet and open/closed clip. Hinge motion and nominal jaw contact do not establish a printable one-body hinge, grip or force.

## Missing runtime dependencies

The source expects `vendor/three.module.js` and `vendor/OrbitControls.js`, with import-map name `three`. The inspected source vendor reports `REVISION = '169'`: pin **Three.js 0.169.0** when supplying these dependencies. Third-party library files are not copied here, installed or fetched; their own license remains applicable. No CDN dependency has been added.

It also expects generated native mesh payloads at `simple-axle/stand-geometry.json`, `simple-axle/wheel-geometry.json` and `outlet-tail/native-geometry.json`. These are not copied as authored source. The portable CAD modules are the geometry source for those parts; the display payload exporter/serving integration remains to be connected. Existing relative links to shopping/sizing pages and image files refer to the original review context and are not supplied here.

Serve through HTTP only after those dependencies are provided. The earlier working preview remains a temporary review service; this source preservation is not a claim that the new repository already serves it. Actual container fit, physical retention, sealing, strength and manufacturing remain unqualified. No purchase intake, account data, private agent report or third-party model geometry is included.
