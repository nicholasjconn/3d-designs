# High-flow center cartridge: empty fit-print proposal

> **Superseded 17 November 2026.** The spindle and locking collar replaced this cartridge (see [README](README.md#current-parts-and-sources)). Kept for history; not a current print input.

The center cartridge is a private adaptation of the author's Bambu-spool,
High Flow / Standard Mesh profile. The body, locking ring and refill cap are
prepared for an **empty fit test**, not qualified desiccant storage. Actual molded
spool fit, threads, bearing fits and support removal remain experimental.
The frame, carriers, magnetic disc and retaining clip are not on this plate.
The maximum holder envelope remains 82.2 mm with a 75 × 130 mm base.

## Sources and privacy

Obtain the original Bambu Spool profile from the [reference model](https://makerworld.com/en/models/1193993-high-performance-spool-desiccant-container-holder#profileId-1214551).
The adapter requires archive SHA256
`17824efad742bb14502ec6c657f2af500d2a5dc4d0475cabdd03bf9c760447b9`.
Keep that separately downloaded archive, all combined meshes and all 3MF outputs
private and ignored. The public repository contains original adapter code;
it does not distribute the third-party model or modified copies.

The [published printable Bambu spool](https://wiki.bambulab.com/en/knowledge-sharing/bambu-reusable-spool)
is a surrogate, not exact molded-spool CAD. Its cheek faces intersect the
reference flanges in the restored source pose. Try the actual molded spool
without forcing it; this print does not establish guaranteed compatibility.

## Proposed plate

- H2D, right 0.4 mm nozzle, Bambu PLA Basic, Textured PEI.
- Factory `0.20mm Standard @BBL H2D` baseline.
- Proposed changes requiring approval: enable tree supports and critical regions
  only; four structural walls instead of factory two; interior support blockers.
  Retain the author's 90° infill direction and Standard Mesh modifiers (40%
  triangles, zero walls/top/bottom skins, original local two-wall modifiers).
- Original custom infill-speed and adaptive layer ranges are removed.
- Body open threaded end down, journal up. Ring retains author pose, broad
  flange down. Cap inboard source Z57.8 face down, journal up.
- Supports contact the body exterior flange and cap rim. The two floors and
  journal webs rely on their bridges; support-removal quality is a trial outcome.

The proposed slice estimates **2 h 49 min and 49.28 g**: **41.04 g useful parts**,
**8.21 g support/interface**, no brim or purge tower, no color changes.
Startup positive commands separately total about 0.183 g; actual loading,
firmware purge and calibration consumption are unknown. The slicer time includes
its estimated startup. Studio normalizes filament priming volume from 30 to
45 mm³ on saved-project reimport; part/support estimates stay the same.
Do not claim all-settings equality.

No source commit, release or print-setting approval is established by this
proposal. Commit and release before fabrication, retain exact private inputs
and generated files independently of the working build, and record actual
settings and outcome. No printer is controlled by these preparation scripts.

## Rebuild

Install `requirements-core.txt` in a suitable environment. CAD journals and
mesh adaptation may be run in separate environments with their respective
CadQuery and trimesh/manifold dependencies. All outputs below are private.
Choose new output directories; generators reject an existing output directory.

```sh
python filament-drybox/cad/high_flow_journals.py --output build/core-journals
python filament-drybox/cad/adapt_high_flow_core.py \
  --reference /private/path/to/standard_desiccant_core_62mm-69mm_v1.2.3mf \
  --journals build/core-journals --output build/core-adapted
python filament-drybox/cad/prepare_high_flow_core.py \
  --input build/core-adapted --output build/core-print-proposal \
  --engineering-root /path/to/castle-harker
```

The preparation script resolves factory profiles from the installed Studio
02.09.01.70 and uses the existing Castle Harker factory-profile resolver.
Slicing success alone does not establish support access or mechanical fit.
Review the complete geometry, actual support paths and exact settings before
approving a batch. Slice/reimport and record retained fabrication-file hashes
for each changed candidate. The generated proposal is not an instruction to print.
