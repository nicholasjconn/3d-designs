import * as T from 'three';
import {OrbitControls} from './vendor/OrbitControls.js';

const host = document.querySelector('#view');
const r = await fetch('geometry.json?v=drive-x-7', {cache: 'no-store'});
if (!r.ok) throw Error('geometry.json HTTP ' + r.status);
const data = await r.json();
const renderer = new T.WebGLRenderer({antialias: true});
renderer.setPixelRatio(Math.min(devicePixelRatio, 2));
renderer.localClippingEnabled = true;
document.querySelector('#loading').remove();
host.appendChild(renderer.domElement);
const labelLayer = document.createElement('div');
labelLayer.className = 'labels';
host.appendChild(labelLayer);

const scene = new T.Scene();
scene.background = new T.Color('#eef1f4');
scene.add(new T.HemisphereLight(0xffffff, 0x849080, 2.5));
const light = new T.DirectionalLight(0xffffff, 3);
light.position.set(100, 200, 180);
scene.add(light);
const camera = new T.PerspectiveCamera(35, 1, .1, 3000), orbit = new OrbitControls(camera, renderer.domElement);
orbit.enableDamping = true;
const group = new T.Group();
scene.add(group);
const objects = {}, cut = new T.Plane(new T.Vector3(0, 0, -1), 0);
const colors = {
  'fixed-stand': '#8b9298', 'left-carrier': '#d9dde1', 'right-carrier': '#d9dde1',
  spindle: '#2f8f6b', collar: '#8fbf5a', 'section-spindle': '#2f8f6b', 'section-collar': '#8fbf5a',
  'section-lock-spindle': '#2f8f6b', 'section-lock-collar': '#8fbf5a', 'section-lock-collar-lifted': '#8fbf5a',
  'drive-rotor': '#407bc5', 'retaining-clip': '#ab52ad', 'left-bearing': '#ed8618', 'right-bearing': '#ed8618'};
// Whole-kit parts from cad/drybox.py (absolute holder coordinates; the outlet is set aside, not placed on the container).
const kitColor = id => id === 'kit-wheel' ? '#2d5f99' : id.endsWith('clip-fixed') ? '#91b9d9' : id.endsWith('clip-gate') ? '#4283bc' :
  id.endsWith('-body') ? '#e0b44c' : id.endsWith('-nut') ? '#b98a2e' : id.endsWith('-cap') ? '#9b6fc7' : id.endsWith('-ring') ? '#2b2b2b' :
  id.endsWith('outer-fitting') ? '#5a5f66' : id.endsWith('-filament') ? '#e0402e' : id.endsWith('-wall') ? '#4089bd' : '#f2f2f2';
const kitClear = id => id.endsWith('-wall') || id.endsWith('continuous-tube');
// Outside drive (cad/wheel.py via cad/drybox.py): fixed X, wheel on the extra 608, retainer ring, axle clip, and every magnet.
const driveColors = {'drive-mount-x': '#9aa1a8', 'drive-wheel': '#2d5f99', 'drive-hub-retainer': '#e0b44c', 'drive-axle-clip': '#ab52ad',
  'drive-608-outer': '#ed8618', 'drive-608-inner': '#c9ced3', 'drive-magnets-wheel': '#2b2f33', 'drive-magnets-disc': '#2b2f33',
  'drive-magnets-x': '#2b2f33', 'drive-magnets-frame': '#2b2f33'};
const driveTurn = new Set(['drive-wheel', 'drive-hub-retainer', 'drive-608-outer', 'drive-magnets-wheel', 'drive-magnets-disc']);
for (const p of data.parts) {
  const g = new T.BufferGeometry();
  g.setAttribute('position', new T.Float32BufferAttribute(p.vertices.flat(), 3));
  g.setIndex(p.triangles.flat());
  g.computeVertexNormals();
  const isSpool = p.id.startsWith('spool-'), kit = p.id.startsWith('kit-'), clear = isSpool || (kit && kitClear(p.id));
  const m = new T.Mesh(g, new T.MeshStandardMaterial({color: isSpool ? '#d4a349' : kit ? kitColor(p.id) : driveColors[p.id] || colors[p.id], roughness: .65, side: T.DoubleSide,
    transparent: clear, opacity: isSpool ? .22 : clear ? .35 : 1, depthWrite: !clear}));
  group.add(m);
  objects[p.id] = m;
}

// Labelled dimensions (axle coordinates: x along the axle, y = radius) for the spindle/collar view.
const notes = new T.Group(), labels = [];
group.add(notes);
const ink = new T.LineBasicMaterial({color: '#1b2026', depthTest: false});
for (const a of data.annotations || []) {
  const [x0, r0] = a.from, [x1, r1] = a.to, z = .5, pts = [];
  let mid;
  if (a.radial) {
    pts.push([x0, r0], [x1, r1], [x0 - 2, r0], [x0 + 2, r0], [x1 - 2, r1], [x1 + 2, r1]);
    mid = [x0 + 1, (r0 + r1) / 2];
  } else {
    const y = r0 + a.offset;
    pts.push([x0, r0], [x0, y], [x1, r1], [x1, y], [x0, y], [x1, y]);
    mid = [(x0 + x1) / 2, y + (a.offset < 0 ? -1.5 : 1.5)];
  }
  const g = new T.BufferGeometry().setFromPoints(pts.map(([x, y]) => new T.Vector3(x, y, z)));
  const line = new T.LineSegments(g, ink);
  line.renderOrder = 10;
  notes.add(line);
  const el = document.createElement('div');
  el.className = 'label';
  el.textContent = a.label;
  labelLayer.appendChild(el);
  labels.push({el, at: new T.Vector3(mid[0], mid[1], z)});
}

// Labels for the lock slice view (absolute axle coordinates, y about the axis).
const lockNotes = new T.Group(), lockLabels = [];
group.add(lockNotes);
for (const l of data.lock_labels || []) {
  const el = document.createElement('div');
  el.className = 'label';
  el.textContent = l.label;
  labelLayer.appendChild(el);
  lockLabels.push({el, at: new T.Vector3(...l.at)});
}

// Axial section overlay: locked spans, base, drive-magnet gap and retention labels (absolute X, Y on the Z=0 cut plane).
const axialNotes = new T.Group(), axialLabels = [];
group.add(axialNotes);
let driveWall = null;
if (data.axial) {
  const pts = [];
  for (const d of data.axial.dims) {
    const [x0, x1] = d.from, y = d.y;
    pts.push([x0, y], [x1, y], [x0, y - 3], [x0, y + 3], [x1, y - 3], [x1, y + 3]);
    const el = document.createElement('div');
    el.className = 'label dim';
    el.textContent = d.label;
    labelLayer.appendChild(el);
    axialLabels.push({el, at: new T.Vector3((x0 + x1) / 2, y + 1.5, 1)});
  }
  const line = new T.LineSegments(new T.BufferGeometry().setFromPoints(pts.map(([x, y]) => new T.Vector3(x, y, 1))),
    new T.LineBasicMaterial({color: '#1f6f43', depthTest: false}));
  line.renderOrder = 10;
  axialNotes.add(line);
  // Side labels are numbered; narrow screens show only the number, keyed in the caption.
  const sideLabels = data.axial.labels.filter(l => l.to);
  for (const l of data.axial.labels) {
    const el = document.createElement('div');
    el.className = 'label' + (l.warn ? ' warn' : '') + (l.to ? ' side' : '');
    if (l.to) {
      const n = document.createElement('b'), t = document.createElement('span');
      n.textContent = sideLabels.indexOf(l) + 1;
      t.textContent = ' ' + l.label;
      el.append(n, t);
    } else el.textContent = l.label;
    labelLayer.appendChild(el);
    if (l.to) {
      const leader = new T.Line(new T.BufferGeometry().setFromPoints([new T.Vector3(...l.at), new T.Vector3(...l.to)]), new T.LineBasicMaterial({color: '#22282e', depthTest: false}));
      leader.renderOrder = 10;
      axialNotes.add(leader);
    }
    axialLabels.push({el, at: new T.Vector3(...(l.to || l.at))});
  }
  const [wi, wo] = data.axial.wall;
  driveWall = new T.Mesh(new T.BoxGeometry(wo - wi, 220, 240), new T.MeshStandardMaterial({color: '#4089bd', transparent: true, opacity: .15, depthWrite: false, side: T.DoubleSide}));
  driveWall.position.set((wi + wo) / 2, 100, 0);
  group.add(driveWall);
}

const walls = new T.Group();
scene.add(walls);
const dim = data.dimensions_mm;
if (!dim) throw Error('geometry.json lacks dimensions_mm');
if (typeof data.axis_y !== 'number') throw Error('geometry.json lacks axis_y');
const inch = n => (n / 25.4).toFixed(3) + ' in', mm = n => +n.toFixed(1);
document.querySelector('#m-span').textContent = mm(dim.wall_span) + ' mm';
document.querySelector('#m-span-in').textContent = inch(dim.wall_span) + ' · from X' + mm(dim.left_wall_x) + ' to X' + mm(dim.right_wall_x);
document.querySelector('#m-base').textContent = mm(dim.base_width) + ' × ' + mm(dim.base_depth) + ' mm';
document.querySelector('#m-base-in').textContent = (dim.base_width / 25.4).toFixed(3) + ' × ' + inch(dim.base_depth);
document.querySelector('#m-height').textContent = mm(dim.frame_height) + ' mm';
document.querySelector('#m-height-in').textContent = inch(dim.frame_height) + ' · upper anchor branches; container fit unmeasured';
const full = data.system && data.system.checks.axial_limits_mm.full_nominal_wall.measured;
document.querySelector('#m-full').textContent = full ? +(full[1] - full[0]).toFixed(2) + ' mm' : '—';
document.querySelector('#m-full-in').textContent = full ? `X${full[0]} to X${full[1]} (knob tip), locked` : '';
for (const x of [dim.left_wall_x, dim.right_wall_x]) {
  const w = new T.Mesh(new T.PlaneGeometry(140, 160), new T.MeshBasicMaterial({color: '#4089bd', transparent: true, opacity: .1, depthWrite: false, side: T.DoubleSide}));
  w.rotation.y = Math.PI / 2;
  w.position.set(x, 80, 0);
  walls.add(w);
}
walls.visible = false;

// Print plate: oriented fabrication meshes on the bed (Studio Z up -> view Y up) and actual sliced support roads.
const printGroup = new T.Group(), pr = data.print;
printGroup.rotation.x = -Math.PI / 2;
printGroup.visible = false;
scene.add(printGroup);
let supportLines = null;
if (!pr) document.querySelector('#print').hidden = true;
if (pr) {
  const bed = new T.Mesh(new T.PlaneGeometry(350, 320), new T.MeshBasicMaterial({color: '#cfd5da', side: T.DoubleSide}));
  bed.position.set(175, 160, -0.05);
  printGroup.add(bed);
  for (const m of pr.meshes) {
    const g = new T.BufferGeometry();
    g.setAttribute('position', new T.Float32BufferAttribute(m.vertices.flat(), 3));
    g.setIndex(m.triangles.flat());
    g.computeVertexNormals();
    printGroup.add(new T.Mesh(g, new T.MeshStandardMaterial({color: colors[m.id], roughness: .65, side: T.DoubleSide})));
  }
  const pos = [], col = [], base = new T.Color('#e39b2d'), face = new T.Color('#c23b22');
  for (const [x1, y1, z1, x2, y2, z2, role] of pr.support_roads) {
    pos.push(x1, y1, z1, x2, y2, z2);
    const c = role ? face : base;
    col.push(c.r, c.g, c.b, c.r, c.g, c.b);
  }
  const g = new T.BufferGeometry();
  g.setAttribute('position', new T.Float32BufferAttribute(pos, 3));
  g.setAttribute('color', new T.Float32BufferAttribute(col, 3));
  supportLines = new T.LineSegments(g, new T.LineBasicMaterial({vertexColors: true}));
  printGroup.add(supportLines);
  const L = pr.material_ledger.materials[0].commanded_mass_kg_by_category, g1 = v => (1000 * (v || 0)).toFixed(2) + ' g';
  const minutes = Math.round(pr.estimate_seconds / 60);
  document.querySelector('#print-info').innerHTML = `<table><tbody>
<tr><td>Prepared replacement plate: Studio estimate (not sent)</td><td>${Math.floor(minutes / 60)} h ${minutes % 60} min; ${pr.slicer_total_g.toFixed(2)} g reported by Studio</td></tr>
<tr><td>Useful parts</td><td>${Object.entries(pr.useful_part_g).map(([name,g]) => name + ' ' + g.toFixed(2) + ' g').join('; ')}</td></tr>
<tr><td>Support (body / transition / interface)</td><td>${g1(L.support_body)} / ${g1(L.support_transition)} / ${g1(L.support_interface)}</td></tr>
<tr><td>Material changes / purge tower</td><td>None in this single-material proposal; firmware loading and calibration overhead remain unmeasured</td></tr>\n<tr><td>Brim / skirt</td><td>${g1(L.brim_or_skirt)}</td></tr>
<tr><td>Identified start-up G-code extrusion</td><td>${g1(L.startup_custom_positive)}, separate from the Studio total; firmware filament loading, purge and calibration are not identified in the G-code and are unknown</td></tr>
<tr><td>Settings</td><td>${pr.settings.layer_height} mm layers; ${pr.settings.wall_loops} walls; ${pr.settings.sparse_infill_density} infill; tree slim supports, critical regions only; one PLA material</td></tr>
<tr><td>Support roads shown</td><td>${pr.support_roads.length.toLocaleString()} of ${pr.support_roads_total.toLocaleString()} actual roads (orange support, red contact interface)</td></tr>
<tr><td>Downloads (prepared replacement)</td><td>${[pr.downloads.project && `<a href="${pr.downloads.project}">editable project 3MF</a>`, pr.downloads.sliced && `<a href="${pr.downloads.sliced}">sliced 3MF</a>`].filter(Boolean).join(' · ')}${(pr.withheld || []).map(w => '<br>' + w).join('')}</td></tr></tbody></table>`;
}

// Checks table, straight from the build results.
const k = data.checks, rows = [];
const row = (a, b) => rows.push(`<tr><td>${a}</td><td>${b}</td></tr>`);
const g = k.rotating_min_gap_mm;
row(`Spindle and collar turning past the frame and carriers (every 10° over 0–110°, one period of the three-fold bodies; axial float ±${k.axial_float_mm.total} mm).`, `≥ ${Math.min(...Object.values(g)).toFixed(2)} mm gap; collar at its outboard limit including thread flank play ${Object.values(k.thread.cases)[0].frame_gap_after_float_and_flank_mm} mm`);
row('Whole collar through a full turn at maximum outboard travel, float and thread flank play', `${k.collar_full_turn_outboard_mm.carrier_gap_mm} mm to left carrier; ${k.collar_full_turn_outboard_mm.frame_gap_mm} mm to frame`);
row('Collar on the thread across its travel (moves along the helix)', `0 mm³ overlap at ${Object.keys(k.thread.cases).join(', ')} mm; ${k.thread.cases['+0.00'].spindle_gap_mm.toFixed(2)} mm flank gap`);
row('Same collar shifted half a pitch without turning (check is discriminating)', `${k.thread.half_pitch_unrotated_overlap_mm3} mm³ overlap`);
const L = k.lock;
row(`Collar lock: key in a slot at every lock position (every ${L.index_deg}°, ${L.index_travel_mm} mm of travel)`, `0 mm³ overlap; turning 5° either way collides (${Math.min(...Object.values(L.stop_overlap_mm3).map(v => v.mm3)).toFixed(2)} mm³ or more, on at least ${Math.min(...Object.values(L.stop_overlap_mm3).map(v => v.crest_bands))} crest bands, at 0 and ${k.collar_travel_mm.inboard} mm travel)`);
row(`Key lifted ${L.lift_required_mm.toFixed(2)} mm (rigid radial illustration; the real arm tilts the key, about 0.04 mm guide-hole margin estimated)`, `Collar turns freely: 0 mm³ overlap between lock positions`);
row('Spindle + collar CAD solid volume', `${mm(k.volume_mm3.spindle / 1000)} + ${mm(k.volume_mm3.collar / 1000)} cm³`);
const f = k.spool_fit;
if (f) {
  row('Spool envelope seated: measured overall width and hub width; radial profile assumed', `flat stop faces; ${f.seated.frame_gap_mm} mm to frame (${f.seated.frame_gap_after_axial_float_mm} mm at full float)`);
  row('Spool slides on from the refill end; collar runs in', f.failures.length ? f.failures.join('; ') : 'Clear at sampled steps');
  row('Hub face widths covered by collar travel', `${f.clamp_range.clamped_hub_width_mm.join('–')} mm (measured ${f.clamp_range.measured_hub_face_width_mm} mm)`);
} else row('Spool fit', 'Not run for this preview');
if(k.drive_key) row('Square drive and retaining clip', `${k.drive_key.engagement_mm} mm radial engagement; ${k.drive_key.free_turn_deg}° free turn; ${k.drive_key.clip_snap_each_jaw_mm} mm snap per jaw`);
if(k.spool_relief) row('Local flange clearance relief', `${k.spool_relief.working_inner_faces_mm} mm working inner span; ${k.spool_relief.plate_thickness_mm.join(' → ')} mm local plate thickness`);
document.querySelector('#checks').innerHTML = rows.join('');
const sys = data.system;
if (sys) {
  const esc = t => String(t).replace(/[&<>]/g, c => ({'&': '&amp;', '<': '&lt;', '>': '&gt;'}[c]));
  document.querySelector('#inventory').innerHTML = '<tr><th>Part</th><th>Source (cad/)</th><th>Latest state</th><th>Build output</th></tr>' +
    sys.inventory.parts.map(p => `<tr><td>${esc(p.name)}</td><td><code>${esc(p.source)}</code></td><td>${esc(p.state)}</td><td><code>${esc(p.output)}</code> · ${p.output_sha256.slice(0, 12)}</td></tr>`).join('') +
    sys.inventory.purchased.map(p => `<tr><td>${esc(p.name)} × ${p.quantity}</td><td><code>${esc(p.interface)}</code></td><td>Purchased</td><td>—</td></tr>`).join('');
  const c = sys.checks, mc = c.magnet_coupling, sr = [];
  const add = (a, b) => sr.push(`<tr><td>${a}</td><td>${b}</td></tr>`);
  add('Ø15 × 3 magnet in every disc and wheel pocket (shared stand.json magnet spec)', mc.pockets.every(p => p.disc_overlap_mm3 === 0 && p.wheel_overlap_mm3 === 0) ? 'Fits: 0 mm³ overlap in all pockets' : 'FAILS');
  add('Drive-magnet face to face, disc to wheel, through the drive wall (wall unmeasured; coupling torque not evaluated)', Object.entries(mc.magnet_face_to_face_gap_mm).map(([w, g]) => `${g} mm at ${w}`).join(', ') + ` (was ${mc.baseline_gap_mm_at_nominal_wall} mm at 2 mm before the X)`);
  const ap = c.anchor_pairs, od = c.outside_drive, al = c.axial_limits_mm;
  add('Anchor pairs: a magnet in each frame glue pocket and each X pocket, coaxial, faces separated only by the wall', ap.pairs.every(q => q.frame_pocket_overlap_mm3 === 0 && q.x_pocket_overlap_mm3 === 0 && q.axis_offset_mm <= 1e-3) ? `All 4 fit and line up (axis offset ≤ ${Math.max(...ap.pairs.map(q => q.axis_offset_mm))} mm); face gap ${ap.pairs.map(q => q.face_gap_mm).join(', ')} mm` : 'FAILS');
  add('Locked endpoints along the axle and base (exact to 0.001 mm)', Object.entries(al).map(([k, v]) => `${k.replace('_nominal_wall', ' (2 mm wall)')} ${v.measured.join('…')}`).join('; '));
  add('Wheel turning past the fixed X, axle clip and 608 inner ring (every 5°, full turn)', `≥ ${Math.min(...Object.values(od.running_min_gap_mm)).toFixed(2)} mm; wheel to X ${od.running_min_gap_mm['wheel / mount-x']} mm`);
  add('608 retention: lip and retainer bear on the outer ring only; shoulder and clip on the inner ring only', `Shield zone kept ≥ ${Math.min(...Object.values(od.race_contacts).map(r => r['608 shield zone'].gap_mm)).toFixed(2)} mm; every direction blocked (outer ring float ${od.axial_float_mm['outer ring in the wheel']} mm, inner ring ${od.axial_float_mm['inner ring on the journal']} mm)`);
  add('Assembly path: 608 into the hub, wheel onto the axle, clip in through the lip notch', Object.entries(od.assembly_path_max_overlap_mm3).filter(([k]) => !k.includes('blocked')).every(([, v]) => v === 0) ? 'Clear at every step (clip snap 0.1 mm per jaw; retainer ring squeezed ' + od.retainer_install.radial_squeeze_mm + ' mm, about ' + od.retainer_install.bending_strain_pct + '% strain, estimate)' : 'FAILS');
  add('Outside drive to holder (stays outside the wall)', `${c.outside_drive_to_holder_gap_mm} mm minimum`);
  add('Outlet, printing: PTFE lead clear of body, fitting and nut', Object.entries(c.outlet_printing).filter(([k]) => k.startsWith('continuous-tube')).map(([k, v]) => `${k.split(' / ')[1]} ${v.gap_mm} mm`).join(', '));
  add('Outlet, storage: closed clip inside the cap', Object.entries(c.outlet_storage).filter(([k]) => k.endsWith('/ cap')).map(([k, v]) => `${k.split(' ')[1]} ${v.gap_mm} mm`).join(', ') + ' clearance');
  if (c.reference_build) add(`Printed or sent holder parts unchanged against ${c.reference_build.directory}: ${Object.keys(c.reference_build.symmetric_difference_mm3).join(', ')}. The gray frame is not compared because it changed.`, Object.values(c.reference_build.symmetric_difference_mm3).every(v => v === 0) ? 'Identical (0 mm³ difference, each listed part)' : JSON.stringify(c.reference_build.symmetric_difference_mm3));
  document.querySelector('#system-checks').innerHTML = sr.join('');
  document.querySelector('#build-id').textContent = `Built from commit ${sys.git_head.slice(0, 7)}${sys.working_tree_changes ? ' plus uncommitted working-tree changes' : ''}.`;
} else document.querySelector('#kit').hidden = true;

const state = {mode: 'assembly', cut: false, spool: false, lifted: false, supports: true, height: 0, angle: 0};
const driveSeparated = {'drive-mount-x': 170, 'drive-magnets-x': 170, 'drive-608-inner': 205, 'drive-608-outer': 205, 'drive-hub-retainer': 190,
  'drive-wheel': 240, 'drive-magnets-wheel': 240, 'drive-axle-clip': 275};
const rotators = new Set(['spindle', 'collar', 'section-spindle', 'section-collar', 'drive-rotor', 'retaining-clip', 'spool-envelope']);
const separated = {'left-carrier': -150, 'left-bearing': -115, collar: -75, 'right-bearing': 55, 'right-carrier': 85, 'drive-rotor': 120, 'retaining-clip': 150};
const change = {'left-carrier': -70, 'left-bearing': -70, collar: -45, 'spool-envelope': -110};
const centerParts = ['section-spindle', 'section-collar'];

function fit(direction) {
  group.updateMatrixWorld(true);
  const box = new T.Box3();
  const target = state.mode === 'print' ? printGroup : group;
  target.updateMatrixWorld(true);
  // The drive-wall slab is a view-only reference: it never sets the camera extents.
  target.traverseVisible(o => { if (state.mode === 'center' && o === objects['spool-envelope']) return; if (o.geometry && o !== driveWall && (state.mode === 'print' || state.mode !== 'lock' || o === objects['section-lock-collar'] || o === objects['section-lock-collar-lifted'])) { o.geometry.computeBoundingBox(); box.union(o.geometry.boundingBox.clone().applyMatrix4(o.matrixWorld)); } });
  // The axial section's side labels sit right of the knob tip: keep room for them.
  if (state.mode === 'axial' && data.axial) box.expandByPoint(new T.Vector3(data.axial.labels.find(l => l.to).to[0] + 70, data.axis_y, 0));
  const center = box.getCenter(new T.Vector3()), d = (direction || new T.Vector3(1, .3, .8)).clone().normalize();
  const right = new T.Vector3(0, 1, 0).cross(d).normalize(), up = d.clone().cross(right).normalize();
  const tan = Math.tan(T.MathUtils.degToRad(camera.fov / 2)) * .86;
  let distance = 0;
  for (const x of [box.min.x, box.max.x]) for (const y of [box.min.y, box.max.y]) for (const z of [box.min.z, box.max.z]) {
    const v = new T.Vector3(x, y, z).sub(center);
    distance = Math.max(distance, v.dot(d) + Math.abs(v.dot(up)) / tan, v.dot(d) + Math.abs(v.dot(right)) / (tan * camera.aspect));
  }
  orbit.target.copy(center);
  camera.position.copy(center).add(d.multiplyScalar(distance));
  orbit.update();
}

const captions = {
  assembly: 'Gray frame (now with four anchor branches), two light-grey carriers in keyed seats, and the green spindle with its light-green collar clamping the recessed spool hub between their flat stop faces. Outside the translucent 2 mm wall (nominal), the fixed gray X holds the blue handwheel on an extra 608; one magnet per X arm pairs with a magnet glued into each frame branch.',
  lift: 'Spindle, collar, spool, blue disc, purple clip, both bearings and both carriers lift out together. The frame keeps only the empty keyed seats; its anchor branches stay outside the disc\'s lift path. The outside drive stays on the wall.',
  parts: 'Printed: two carriers, green spindle, light-green collar, blue magnetic disc, purple clip (frame hidden); outside: gray X, yellow retainer ring, extra 608, blue wheel, purple axle clip. Purchased: three 608s and the magnets.',
  carriers: 'Each carrier slides down a 24.4 mm slot in the frame plate to a flat floor. Grooves on the carrier ride on thinned frame edges to stop movement along the axle. Carriers are held down by gravity only.',
  center: 'Native CAD half-section through the spindle and threaded collar. Their hub-face stops clamp the spool; the short pilots enter its bore. Clamp force stays inside spindle, collar and spool.',
  lock: 'Slice through the collar lock, viewed from the refill side. The key rests in one of the slots cut through the spindle thread crests, so the collar cannot turn either way. Press “Lift key” to see it raised clear of the crests.',
  lifted: 'Key lifted clear of the thread crests, so the collar can be turned. Push the paddle toward the arm root to lift it; this view shows a rigid radial lift for illustration, while the real arm also tilts the key. Let go and keep turning forward until the key drops into the next slot.',
  change: 'Spool change, after lifting the whole unit out: pull off the left carrier, slide the left 608 off its slip-fit journal, hold the spool near the collar end and unscrew the collar, then slide the spool off toward the refill side. Reverse to refit.'};
captions.kit = 'Every current part. The outside drive (fixed X, extra 608, handwheel) sits coaxial with the blue disc across a nominal 2 mm drive wall (container unmeasured). In front, set aside because its place on the container is not defined: the outlet in its printing configuration (left: PTFE lead through the body and purchased fitting) and its storage configuration (right: cap on, filament tail held by the two-body clip inside the cap). Translucent plates are 50 mm wall patches.';
captions.axial = 'Optional amber spool envelope: measured overall and hub widths, assumed radial profile. Axial section on the axle plane (front half removed). Green: the locked spans along the axle (holder 82.2, spindle 79.4, full assembly 104.65 mm at a nominal 2 mm wall) and the 75 × 130 mm base, all checked against the build. Outside the wall, the fixed gray X carries the extra 608 on its integral axle. The wheel\'s lip and retainer ring hold the outer ring, and the X shoulder and axle clip hold the inner ring. Turn the rotation slider: the wheel, retainer, outer ring and both magnet sets turn with the disc.';
captions.print = 'Current holder plate in its actual fabrication orientations. Orange lines are sampled support roads; red lines are contact interfaces. This replacement plate has not been sent to the printer.';
if (data.axial) captions.axial += ' Labels: ' + data.axial.labels.filter(l => l.to).map((l, i) => `${i + 1} ${l.label}`).join('; ') + '.';
const modes = ['assembly', 'kit', 'axial', 'lift', 'parts', 'carriers', 'center', 'lock', 'change', 'print'];

const view = () => state.mode === 'center' || state.mode === 'axial' ? new T.Vector3(0, 0, 1) : state.mode === 'lock' ? new T.Vector3(-1, 0, 0) : undefined;

function update(reframe = true) {
  for (const [n, o] of Object.entries(objects)) {
    const spool = n.startsWith('spool-'), section = n.startsWith('section-'), kit = n.startsWith('kit-'), drive = n in driveColors;
    o.visible = spool ? state.spool && !['parts', 'carriers'].includes(state.mode) : !section && !kit;
    // Outside-drive parts never lift with the spindle; only the disc's magnets do.
    o.position.set(0, n === 'fixed-stand' || kit ? 0 : drive ? (driveTurn.has(n) ? data.axis_y + (n === 'drive-magnets-disc' ? state.height : 0) : 0) : data.axis_y + state.height, 0);
    if (kit) { o.visible = state.mode === 'kit'; o.rotation.x = 0; }
    o.rotation.x = rotators.has(n) || driveTurn.has(n) ? state.angle : 0;
    if (state.mode === 'parts') { o.visible = n !== 'fixed-stand' && n !== 'drive-magnets-frame' && n !== 'drive-magnets-disc' && !spool && !section && !kit; o.position.x = separated[n] || driveSeparated[n] || 0; }
    if (state.mode === 'carriers') o.visible = ['fixed-stand', 'left-carrier', 'right-carrier', 'left-bearing', 'right-bearing'].includes(n);
    if (state.mode === 'center') { o.visible = centerParts.includes(n) || (spool && state.spool); o.rotation.x = 0; }
    if (state.mode === 'lock') { o.visible = n === 'section-lock-spindle' || n === (state.lifted ? 'section-lock-collar-lifted' : 'section-lock-collar'); o.rotation.x = 0; }
    if (state.mode === 'change') { if (n === 'fixed-stand' || drive) o.visible = false; o.position.x = change[n] || 0; }
    if (state.mode === 'axial' && spool) o.visible = state.spool;
    o.traverse(m => { if (m.material) m.material.clippingPlanes = (state.cut || state.mode === 'axial') && state.mode !== 'center' ? [cut] : (spool && state.mode === 'center' ? [cut] : []); });
  }
  group.visible = state.mode !== 'print';
  printGroup.visible = state.mode === 'print';
  if (state.mode === 'print') walls.visible = false;
  if (supportLines) supportLines.visible = state.supports;
  document.querySelector('#supports').hidden = state.mode !== 'print';
  document.querySelector('#supports').setAttribute('aria-pressed', state.supports);
  notes.visible = state.mode === 'center';
  axialNotes.visible = state.mode === 'axial';
  if (driveWall) { driveWall.visible = ['assembly', 'kit', 'axial', 'lift'].includes(state.mode); driveWall.material.clippingPlanes = state.cut || state.mode === 'axial' ? [cut] : []; }
  for (const l of axialLabels) l.el.style.display = axialNotes.visible ? '' : 'none';
  notes.position.set(0, data.axis_y + state.height, 0);
  lockNotes.visible = state.mode === 'lock';
  lockNotes.position.set(0, data.axis_y + state.height, 0);
  for (const l of labels) l.el.style.display = notes.visible ? '' : 'none';
  for (const l of lockLabels) l.el.style.display = lockNotes.visible ? '' : 'none';
  document.querySelector('#release').hidden = state.mode !== 'lock';
  document.querySelector('#release').setAttribute('aria-pressed', state.lifted);
  for (const id of modes) document.querySelector('#' + id).setAttribute('aria-pressed', state.mode === id);
  document.querySelector('#cut').setAttribute('aria-pressed', state.cut);
  document.querySelector('#spool').setAttribute('aria-pressed', state.spool);
  document.querySelector('#walls').setAttribute('aria-pressed', walls.visible);
  document.querySelector('#height').value = state.height;
  document.querySelector('#height-value').textContent = state.height + ' mm';
  document.querySelector('#caption').textContent = captions[state.mode === 'lock' && state.lifted ? 'lifted' : state.mode];
  if (reframe) fit(view());
}

for (const id of modes) document.querySelector('#' + id).onclick = () => {
  state.mode = id; state.height = id === 'lift' ? 90 : 0; state.angle = 0;
  document.querySelector('#rotation').value = 0; update();
};
document.querySelector('#supports').onclick = () => { state.supports = !state.supports; update(false); };
document.querySelector('#release').onclick = () => { state.lifted = !state.lifted; update(false); };
for (const id of ['cut', 'spool']) document.querySelector('#' + id).onclick = () => { state[id] = !state[id]; update(); };
document.querySelector('#walls').onclick = () => { walls.visible = !walls.visible; update(false); };
document.querySelector('#height').oninput = e => { state.height = +e.target.value; update(false); };
document.querySelector('#rotation').oninput = e => { state.angle = +e.target.value * Math.PI / 180; update(false); };
document.querySelector('#drive').onclick = () => fit(new T.Vector3(1, .08, .08));
document.querySelector('#back').onclick = () => fit(new T.Vector3(-1, .08, .08));
new ResizeObserver(() => {
  renderer.setSize(host.clientWidth, host.clientHeight);
  camera.aspect = host.clientWidth / host.clientHeight;
  camera.updateProjectionMatrix();
  fit(view());
}).observe(host);
update();

const v = new T.Vector3();
function draw() {
  requestAnimationFrame(draw);
  orbit.update();
  renderer.render(scene, camera);
  const shown = notes.visible ? labels : lockNotes.visible ? lockLabels : axialNotes.visible ? axialLabels : [];
  if (shown.length) {
    group.updateMatrixWorld(true);
    const frame = notes.visible ? notes : lockNotes.visible ? lockNotes : axialNotes;
    for (const l of shown) {
      v.copy(l.at).applyMatrix4(frame.matrixWorld).project(camera);
      const half = l.el.offsetWidth / 2;  // keep labels inside the view on narrow screens
      l.el.style.left = Math.min(Math.max((v.x + 1) / 2 * host.clientWidth, half), host.clientWidth - half) + 'px';
      l.el.style.top = ((1 - v.y) / 2 * host.clientHeight) + 'px';
    }
  }
}
draw();
window.holderReview = {objects, state, update, renderer, camera, orbit};
