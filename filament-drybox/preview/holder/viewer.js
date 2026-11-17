import * as T from 'three';
import {OrbitControls} from './vendor/OrbitControls.js';

const host = document.querySelector('#view');
const r = await fetch('geometry.json', {cache: 'no-store'});
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
for (const p of data.parts) {
  const g = new T.BufferGeometry();
  g.setAttribute('position', new T.Float32BufferAttribute(p.vertices.flat(), 3));
  g.setIndex(p.triangles.flat());
  g.computeVertexNormals();
  const isSpool = p.id.startsWith('spool-'), kit = p.id.startsWith('kit-'), clear = isSpool || (kit && kitClear(p.id));
  const m = new T.Mesh(g, new T.MeshStandardMaterial({color: isSpool ? '#d4a349' : kit ? kitColor(p.id) : colors[p.id], roughness: .65, side: T.DoubleSide,
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
document.querySelector('#m-height-in').textContent = inch(dim.frame_height);
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
<tr><td>Prepared single-material comparison: Studio estimate (not the sent job)</td><td>${Math.floor(minutes / 60)} h ${minutes % 60} min; ${pr.slicer_total_g.toFixed(2)} g reported by Studio</td></tr>
<tr><td>Useful parts</td><td>spindle ${pr.useful_part_g.spindle.toFixed(2)} g, collar ${pr.useful_part_g.collar.toFixed(2)} g</td></tr>
<tr><td>Support (body / transition / interface)</td><td>${g1(L.support_body)} / ${g1(L.support_transition)} / ${g1(L.support_interface)}</td></tr>
<tr><td>Brim / skirt</td><td>${g1(L.brim_or_skirt)}</td></tr>
<tr><td>Identified start-up G-code extrusion</td><td>${g1(L.startup_custom_positive)}, separate from the Studio total; firmware filament loading, purge and calibration are not identified in the G-code and are unknown</td></tr>
<tr><td>Settings</td><td>${Object.entries(pr.settings).map(([k, v]) => k + ' = ' + v).join(', ')}</td></tr>
<tr><td>Support roads shown</td><td>${pr.support_roads.length.toLocaleString()} of ${pr.support_roads_total.toLocaleString()} actual roads (orange support, red contact interface)</td></tr>
<tr><td>Downloads (prepared comparison)</td><td>${[pr.downloads.project && `<a href="${pr.downloads.project}">editable project 3MF</a>`, pr.downloads.sliced && `<a href="${pr.downloads.sliced}">sliced 3MF</a>`].filter(Boolean).join(' · ')}${(pr.withheld || []).map(w => '<br>' + w).join('')}</td></tr></tbody></table>`;
}

// Checks table, straight from the build results.
const k = data.checks, rows = [];
const row = (a, b) => rows.push(`<tr><td>${a}</td><td>${b}</td></tr>`);
const g = k.rotating_min_gap_mm;
row(`Spindle and collar turning past the frame and carriers (every 10° over 0–110°, one period of the three-fold bodies; axial float ±${k.axial_float_mm.total} mm). The single lock paddle is checked analytically for the full turn: ≥1.25 mm axially from the left carrier at every angle`, `≥ ${Math.min(...Object.values(g)).toFixed(2)} mm gap; collar cone at its outboard limit ${Object.values(k.thread.cases)[0].frame_gap_after_float_mm} mm`);
row('Collar on the thread across its travel (moves along the helix)', `0 mm³ overlap at ${Object.keys(k.thread.cases).join(', ')} mm; ${k.thread.cases['+0.00'].spindle_gap_mm.toFixed(2)} mm flank gap`);
row('Same collar shifted half a pitch without turning (check is discriminating)', `${k.thread.half_pitch_unrotated_overlap_mm3} mm³ overlap`);
const L = k.lock;
row(`Collar lock: key in a slot at every lock position (every ${L.index_deg}°, ${L.index_travel_mm} mm of travel)`, `0 mm³ overlap; turning 5° either way collides (${Math.min(...Object.values(L.stop_overlap_mm3).map(v => v.mm3)).toFixed(2)} mm³ or more, on at least ${Math.min(...Object.values(L.stop_overlap_mm3).map(v => v.crest_bands))} crest bands, at 0 and ${k.collar_travel_mm.inboard} mm travel)`);
row(`Key lifted ${L.lift_required_mm.toFixed(2)} mm (rigid radial illustration; the real arm tilts the key, about 0.04 mm guide-hole margin estimated)`, `Collar turns freely: 0 mm³ overlap between lock positions`);
row('Spindle + collar CAD solid volume', `${mm(k.volume_mm3.spindle / 1000)} + ${mm(k.volume_mm3.collar / 1000)} cm³`);
const f = k.spool_fit;
if (f) {
  row('Bambu printable spool seated', `contact only in the chamfer bands (X ${f.seated.spindle.overlap_extent.x.join('…')}, R ${f.seated.spindle.overlap_extent.r.join('…')}); ${f.seated.frame_gap_mm} mm to frame (${f.seated.frame_gap_after_axial_float_mm} mm at full float)`);
  row('Spool slides on from the refill end; collar runs in', f.failures.length ? f.failures.join('; ') : 'Clear at every step');
  row('Spool hub widths the collar can clamp at the reference bore', `${f.clamp_range.hub_width_mm_at_reference_bore.join('–')} mm (reference ${f.clamp_range.reference_hub_width_mm} mm); joint condition with bore size`);
} else row('Spool fit', 'Not run for this preview');
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
  add('Disc magnet face to wheel magnet face, through the drive wall (wall unmeasured)', Object.entries(mc.magnet_face_to_face_gap_mm).map(([w, g]) => `${g} mm at ${w}`).join(', '));
  add('Outlet, printing: PTFE lead clear of body, fitting and nut', Object.entries(c.outlet_printing).filter(([k]) => k.startsWith('continuous-tube')).map(([k, v]) => `${k.split(' / ')[1]} ${v.gap_mm} mm`).join(', '));
  add('Outlet, storage: closed clip inside the cap', Object.entries(c.outlet_storage).filter(([k]) => k.endsWith('/ cap')).map(([k, v]) => `${k.split(' ')[1]} ${v.gap_mm} mm`).join(', ') + ' clearance');
  if (c.reference_build) add(`Holder parts identical to the build the running spindle/collar print was sliced from (${c.reference_build.directory})`, Object.values(c.reference_build.symmetric_difference_mm3).every(v => v === 0) ? 'Identical (0 mm³ difference, every part)' : JSON.stringify(c.reference_build.symmetric_difference_mm3));
  document.querySelector('#system-checks').innerHTML = sr.join('');
  document.querySelector('#build-id').textContent = `Built from commit ${sys.git_head.slice(0, 7)}${sys.working_tree_changes ? ' plus uncommitted working-tree changes' : ''}.`;
} else document.querySelector('#kit').hidden = true;

const state = {mode: 'assembly', cut: false, spool: false, lifted: false, supports: true, height: 0, angle: 0};
const rotators = new Set(['spindle', 'collar', 'section-spindle', 'section-collar', 'drive-rotor', 'retaining-clip', 'spool-narrow', 'spool-wide']);
const separated = {'left-carrier': -150, 'left-bearing': -115, collar: -75, 'right-bearing': 55, 'right-carrier': 85, 'drive-rotor': 120, 'retaining-clip': 150};
const change = {'left-carrier': -70, 'left-bearing': -70, collar: -45, 'spool-narrow': -110, 'spool-wide': -110};
const centerParts = ['section-spindle', 'section-collar'];

function fit(direction) {
  group.updateMatrixWorld(true);
  const box = new T.Box3();
  const target = state.mode === 'print' ? printGroup : group;
  target.updateMatrixWorld(true);
  target.traverseVisible(o => { if (o.geometry && (state.mode === 'print' || state.mode !== 'lock' || o === objects['section-lock-collar'] || o === objects['section-lock-collar-lifted'])) { o.geometry.computeBoundingBox(); box.union(o.geometry.boundingBox.clone().applyMatrix4(o.matrixWorld)); } });
  const center = box.getCenter(new T.Vector3()), d = (direction || new T.Vector3(.6, .45, 1.3)).clone().normalize();
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
  assembly: 'Gray frame, two light-grey carriers in keyed seats, and the green spindle with its light-green collar. The spool hub is clamped between the spindle\'s fixed cone (drive side) and the collar\'s cone (refill side).',
  lift: 'Spindle, collar, spool, blue disc, purple clip, both bearings and both carriers lift out together. The frame keeps only the empty keyed seats.',
  parts: 'Printed: gray frame, two carriers, green spindle, light-green collar, blue magnetic disc, purple clip. Purchased: two orange 608 bearings.',
  carriers: 'Each carrier slides down a 24.4 mm slot in the frame plate to a flat floor. Grooves on the carrier ride on thinned frame edges to stop movement along the axle. Carriers are held down by gravity only.',
  center: 'CAD half-section (cut on the axle plane) of the spindle and collar. The collar screws onto the spindle; its cone and the spindle\'s cone seat in the spool bore\'s end chamfers. Clamp force stays inside spindle, collar and spool.',
  lock: 'Slice through the collar lock, viewed from the refill side. The key rests in one of the slots cut through the spindle thread crests, so the collar cannot turn either way. Press “Lift key” to see it raised clear of the crests.',
  lifted: 'Key lifted clear of the thread crests, so the collar can be turned. Push the paddle toward the arm root to lift it; this view shows a rigid radial lift for illustration, while the real arm also tilts the key. Let go and keep turning forward until the key drops into the next slot.',
  change: 'Spool change, after lifting the whole unit out: pull off the left carrier, slide the left 608 off its slip-fit journal, hold the spool near the collar end and unscrew the collar (about 3.8 turns), then slide the spool off toward the refill side. Reverse to refit.'};
captions.kit = 'Every current part. The outside handwheel sits coaxial with the blue disc across a nominal 2 mm drive wall (container unmeasured). In front, set aside because its place on the container is not defined: the outlet in its printing configuration (left: PTFE lead through the body and purchased fitting) and its storage configuration (right: cap on, filament tail held by the two-body clip inside the cap). Translucent plates are 50 mm wall patches.';
captions.print = 'Print plate as sliced: spindle standing on its drive journal end, collar on its outboard cone face, with the actual support roads of the prepared single-material comparison. The sent job used separate support material; see the print section below.';
const modes = ['assembly', 'kit', 'lift', 'parts', 'carriers', 'center', 'lock', 'change', 'print'];

const view = () => state.mode === 'center' ? new T.Vector3(0, 0, 1) : state.mode === 'lock' ? new T.Vector3(-1, 0, 0) : undefined;

function update(reframe = true) {
  for (const [n, o] of Object.entries(objects)) {
    const spool = n.startsWith('spool-'), section = n.startsWith('section-'), kit = n.startsWith('kit-');
    o.visible = spool ? state.spool && !['parts', 'carriers'].includes(state.mode) : !section && !kit;
    o.position.set(0, n === 'fixed-stand' || kit ? 0 : data.axis_y + state.height, 0);
    if (kit) { o.visible = state.mode === 'kit'; o.rotation.x = 0; }
    o.rotation.x = rotators.has(n) ? state.angle : 0;
    if (state.mode === 'parts') { o.visible = n !== 'fixed-stand' && !spool && !section && !kit; o.position.x = separated[n] || 0; }
    if (state.mode === 'carriers') o.visible = ['fixed-stand', 'left-carrier', 'right-carrier', 'left-bearing', 'right-bearing'].includes(n);
    if (state.mode === 'center') { o.visible = centerParts.includes(n) || (spool && state.spool); o.rotation.x = 0; }
    if (state.mode === 'lock') { o.visible = n === 'section-lock-spindle' || n === (state.lifted ? 'section-lock-collar-lifted' : 'section-lock-collar'); o.rotation.x = 0; }
    if (state.mode === 'change') { if (n === 'fixed-stand') o.visible = false; o.position.x = change[n] || 0; }
    o.traverse(m => { if (m.material) m.material.clippingPlanes = state.cut && state.mode !== 'center' ? [cut] : (spool && state.mode === 'center' ? [cut] : []); });
  }
  group.visible = state.mode !== 'print';
  printGroup.visible = state.mode === 'print';
  if (state.mode === 'print') walls.visible = false;
  if (supportLines) supportLines.visible = state.supports;
  document.querySelector('#supports').hidden = state.mode !== 'print';
  document.querySelector('#supports').setAttribute('aria-pressed', state.supports);
  notes.visible = state.mode === 'center';
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
  const shown = notes.visible ? labels : lockNotes.visible ? lockLabels : [];
  if (shown.length) {
    group.updateMatrixWorld(true);
    const frame = notes.visible ? notes : lockNotes;
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
