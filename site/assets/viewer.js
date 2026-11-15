import * as THREE from 'three';
import {OrbitControls} from 'three/addons/controls/OrbitControls.js';
import {GLTFLoader} from 'three/addons/loaders/GLTFLoader.js';
import {RoomEnvironment} from 'three/addons/environments/RoomEnvironment.js';
import {toCreasedNormals} from 'three/addons/utils/BufferGeometryUtils.js';

const BUILD = 'v1';
const $ = id => document.getElementById(id);
const el = $('viewer'), Q = new URLSearchParams(location.search);
const scene = new THREE.Scene();
const cam = new THREE.PerspectiveCamera(28, el.clientWidth / el.clientHeight, 5, 8000);
const r = new THREE.WebGLRenderer({antialias: true, alpha: true, preserveDrawingBuffer: true});
r.setPixelRatio(Math.min(devicePixelRatio, 2)); r.setSize(el.clientWidth, el.clientHeight);
r.shadowMap.enabled = true; r.shadowMap.type = THREE.PCFSoftShadowMap;
r.toneMapping = THREE.ACESFilmicToneMapping; r.toneMappingExposure = 1.05; r.outputColorSpace = THREE.SRGBColorSpace;
el.prepend(r.domElement);
const pm = new THREE.PMREMGenerator(r); scene.environment = pm.fromScene(new RoomEnvironment(), 0.04).texture; scene.environmentIntensity = 0.6;
const ctl = new OrbitControls(cam, r.domElement); ctl.enableDamping = true; ctl.minDistance = 150; ctl.maxDistance = 2600;

// robot frame: x forward, y left, z up (mm)  ->  three: (x, z, -y)
const TGT = new THREE.Vector3(-10, 110, 0);
const VIEWS = {front: [860, 170, 0], '34': [600, 360, -600], side: [0, 170, -880], back: [-880, 190, 0], top: [1, 950, 0], under: [300, -620, -300]};
function setView(n) {
  const v = VIEWS[n] || VIEWS['34']; cam.position.set(...v); ctl.target.copy(TGT); ctl.update();
  document.querySelectorAll('[data-view]').forEach(b => b.classList.toggle('on', b.dataset.view === n));
  floor.visible = n !== 'under';
}

scene.add(new THREE.HemisphereLight(0xfff6ea, 0x9a8f80, 0.9));
const key = new THREE.DirectionalLight(0xffffff, 2.1); key.position.set(420, 820, -460); key.castShadow = true;
key.shadow.mapSize.set(2048, 2048); Object.assign(key.shadow.camera, {left: -360, right: 360, top: 360, bottom: -360, near: 100, far: 2400});
key.shadow.bias = -0.0004; key.shadow.normalBias = 1.0; scene.add(key);
const rim = new THREE.DirectionalLight(0xffe0bf, 1.1); rim.position.set(-600, 380, 300); scene.add(rim);
const floor = new THREE.Mesh(new THREE.CircleGeometry(1400, 96), new THREE.ShadowMaterial({opacity: 0.16}));
floor.rotation.x = -Math.PI / 2; floor.receiveShadow = true; scene.add(floor);
const root = new THREE.Group(); root.rotation.x = -Math.PI / 2; scene.add(root);

const GROUPS = {
  shell: {name: 'Shell', color: '#e7d6b8'}, mechanism: {name: 'Periscope & treats', color: '#f2a65a'},
  drivetrain: {name: 'Drivetrain', color: '#8e959f'}, power: {name: 'Power', color: '#2f62a8'},
  electronics: {name: 'Electronics', color: '#2f8f4e'}, sensors: {name: 'Sensors', color: '#7a2fa0'},
  expression: {name: 'Eye, light, sound', color: '#ff8a3d'}, dock: {name: 'Charging dock', color: '#6b6258'}
};
const SHELL = ['chassis', 'top_shell', 'head_rear', 'head_front', 'cup_lid', 'light_band'];
const items = {}, links = {}, labels = [];
const shellMats = [];
let RI, xray = Q.get('xray') === '1', showLabels = Q.get('labels') !== '0', explodeT = +(Q.get('explode') || 0), demo = false, sel = null;
let lift = Q.has('pose') ? +Q.get('pose') : 80;
const visible = Object.fromEntries(Object.keys(GROUPS).map(g => [g, true]));
(Q.get('hide') || '').split(',').filter(Boolean).forEach(g => visible[g] = false);

let eyeCtx, eyeTex;
function drawEye(open = 1, look = 0) {
  const g = eyeCtx; g.fillStyle = '#07090c'; g.fillRect(0, 0, 256, 256);
  g.save(); g.beginPath(); g.ellipse(128, 128, 104, 104 * Math.max(open, 0.06), 0, 0, Math.PI * 2); g.clip();
  const cx = 128 + look * 26;
  const grd = g.createRadialGradient(cx, 132, 8, cx, 132, 86); grd.addColorStop(0, '#fff3cf'); grd.addColorStop(0.3, '#ffc061'); grd.addColorStop(0.78, '#f07a2c'); grd.addColorStop(1, 'rgba(240,110,40,0)');
  g.fillStyle = grd; g.beginPath(); g.arc(cx, 132, 84, 0, Math.PI * 2); g.fill();
  g.fillStyle = '#07090c'; g.beginPath(); g.arc(cx, 136, 30, 0, Math.PI * 2); g.fill();
  g.fillStyle = 'rgba(255,255,255,.92)'; g.beginPath(); g.ellipse(cx - 24, 104, 13, 10, -0.5, 0, Math.PI * 2); g.fill();
  g.fillStyle = 'rgba(255,255,255,.5)'; g.beginPath(); g.arc(cx + 22, 160, 5, 0, Math.PI * 2); g.fill();
  g.restore(); if (eyeTex) eyeTex.needsUpdate = true;
}
function eyeTexture() {
  const c = document.createElement('canvas'); c.width = c.height = 256; eyeCtx = c.getContext('2d'); drawEye();
  eyeTex = new THREE.CanvasTexture(c); eyeTex.colorSpace = THREE.SRGBColorSpace; return eyeTex;
}

function makeMat(key, it) {
  const k = key.split(':')[1];
  const c = new THREE.Color(it.color);
  if (key.startsWith('part:')) {
    let m;
    if (k === 'light_band') m = new THREE.MeshPhysicalMaterial({color: 0xfff1dc, emissive: 0xffa24a, emissiveIntensity: 0.6, roughness: 0.35, transparent: true, opacity: 0.93});
    else if (k === 'cup_lid') m = new THREE.MeshPhysicalMaterial({color: c, roughness: 0.15, clearcoat: 1, transparent: true, opacity: 0.82});
    else if (k === 'head_front') m = new THREE.MeshPhysicalMaterial({color: c, roughness: 0.18, clearcoat: 1, clearcoatRoughness: 0.08});
    else if (k.startsWith('tire')) m = new THREE.MeshStandardMaterial({color: c, roughness: 0.9});
    else if (k === 'top_shell' || k === 'head_rear') m = new THREE.MeshPhysicalMaterial({color: c, roughness: 0.38, clearcoat: 0.5, clearcoatRoughness: 0.3});
    else if (k === 'chassis') m = new THREE.MeshPhysicalMaterial({color: c, roughness: 0.55, clearcoat: 0.15});
    else m = new THREE.MeshStandardMaterial({color: c, roughness: 0.5});
    if (SHELL.includes(k)) { m.userData.op = m.opacity; shellMats.push(m); }
    return m;
  }
  if (k.startsWith('led')) return new THREE.MeshStandardMaterial({color: 0xffc27a, emissive: 0xff9a3d, emissiveIntensity: 1.4});
  if (k.startsWith('pad') || k.startsWith('dock_spring') || k.startsWith('bclip')) return new THREE.MeshStandardMaterial({color: c, metalness: 0.9, roughness: 0.3});
  if (k.includes('motor') || k === 'caster' || k === 'esp32') return new THREE.MeshStandardMaterial({color: c, metalness: 0.7, roughness: 0.35});
  return new THREE.MeshStandardMaterial({color: c, roughness: 0.5, metalness: 0.05});
}

Promise.all([
  fetch('assets/robot_info.json?v=' + BUILD).then(x => x.json()),
  fetch('assets/bom.json?v=' + BUILD).then(x => x.json()).catch(() => null),
  new Promise((ok, bad) => new GLTFLoader().load('assets/meerlo.gltf?v=' + BUILD, ok, undefined, bad))
]).then(([ri, bom, gltf]) => {
  RI = ri; const g = gltf.scene; root.add(g);
  const fix = s => s.replace(/^(link|part|elec)(?!:)/, '$1:');
  const meshes = [];
  g.traverse(o => { const n = fix(o.name); if (n.startsWith('link:') && !o.isMesh) links[n.slice(5)] = o; if (o.isMesh) meshes.push(o); });
  for (const o of meshes) {
    let n = fix(o.name); if (!ri.items[n]) n = fix(o.parent.name);
    const it = ri.items[n]; if (!it) continue;
    o.geometry = toCreasedNormals(o.geometry.index ? o.geometry.toNonIndexed() : o.geometry, THREE.MathUtils.degToRad(35));
    o.material = makeMat(n, it); o.castShadow = true; o.receiveShadow = true;
    const node = ri.items[fix(o.name)] ? o : o.parent;
    if (!items[n]) items[n] = Object.assign({key: n, nodes: [], p0: []}, it);
    if (!items[n].nodes.includes(node)) { items[n].nodes.push(node); items[n].p0.push(node.position.clone()); }
    o.userData.key = n;
  }
  for (const l of Object.values(links)) { l.userData.q0 = l.quaternion.clone(); l.userData.p0 = l.position.clone(); }
  if (links.mast) {   // the eye graphic on the round LCD (mast frame: origin at x=-30)
    const eye = new THREE.Mesh(new THREE.CircleGeometry(16.2, 64), new THREE.MeshBasicMaterial({map: eyeTexture(), toneMapped: false}));
    eye.rotation.y = Math.PI / 2; eye.rotation.z = Math.PI / 2; eye.position.set(22.95, 0, 154);
    eye.userData.key = 'elec:lcd'; links.mast.add(eye);
    const lcd = items['elec:lcd']; if (lcd) { lcd.nodes.push(eye); lcd.p0.push(eye.position.clone()); }
  }
  if (bom) { $('pb').textContent = '$' + Math.round(bom.prototype_total); $('vb').textContent = '$' + bom.volume_total.toFixed(0); $('vb2').textContent = '$' + bom.volume_total.toFixed(0); }
  buildUI(); applyAll(); setView(Q.get('view') || '34');
  document.body.classList.add('loaded');
}).catch(e => { $('loading').textContent = 'Could not load the model: ' + e; console.error(e); });

function buildUI() {
  const counts = {};
  for (const it of Object.values(items)) counts[it.group] = (counts[it.group] || 0) + 1;
  $('layers').innerHTML = Object.entries(GROUPS).map(([g, G]) =>
    `<label class="layer"><input type="checkbox" data-g="${g}" ${visible[g] ? 'checked' : ''}><span class="sw" style="background:${G.color}"></span>${G.name}<span class="n">${counts[g] || 0}</span></label>`).join('');
  $('layers').querySelectorAll('input').forEach(i => i.onchange = () => { visible[i.dataset.g] = i.checked; applyAll(); });
  const rows = {};
  for (const it of Object.values(items)) { const k = it.group + '|' + it.title; (rows[k] = rows[k] || {it, keys: [], n: 0}).keys.push(it.key); rows[k].n++; }
  let html = '', ncomp = 0;
  for (const g of Object.keys(GROUPS)) {
    const rs = Object.values(rows).filter(r => r.it.group === g); if (!rs.length) continue;
    html += `<div class="grp"><span class="sw" style="background:${GROUPS[g].color}"></span>${GROUPS[g].name}</div>`;
    for (const rw of rs) {
      ncomp++;
      const short = (rw.it.desc || '').split(/(?<=\.)\s/)[0];
      const multi = rw.n > 1 && !/\(x\d+\)/.test(rw.it.title) && !rw.it.title.includes('N20') ? ` &times;${rw.n}` : '';
      html += `<div class="c" data-keys="${rw.keys.join(',')}" data-g="${g}"><b>${rw.it.title}${multi}</b><span>${short}</span></div>`;
    }
  }
  $('clist').innerHTML = html; $('ncomp').textContent = '(' + ncomp + ')';
  $('clist').querySelectorAll('.c').forEach(d => {
    d.onclick = () => select(d.dataset.keys.split(','));
    d.onmouseenter = () => highlight(d.dataset.keys.split(','), true); d.onmouseleave = () => { if (!sel || sel.join() !== d.dataset.keys) highlight(d.dataset.keys.split(','), false); };
  });
  const L = $('labels');
  for (const lb of RI.labels) {
    const it = items[lb.key]; if (!it) continue;
    const a = new THREE.Object3D(); a.position.fromArray(lb.local);
    const itn = it.nodes[0]; (itn && itn.parent ? itn : (links[lb.node.slice(5)] || root)).add(a);
    if (itn) a.position.sub(itn.position).add(new THREE.Vector3()); // anchor rides with the part (explode)
    const d = document.createElement('div'); d.className = 'lbl'; d.innerHTML = `<i></i><span>${it.title.replace(/ \(x\d+\)$/, '')}</span>`;
    d.onclick = () => select(groupKeys(lb.key)); L.appendChild(d);
    const ext = it.group === 'shell' || ['part:dock', 'part:wheel_l', 'part:tire_r', 'elec:lcd', 'elec:camera', 'elec:tof', 'elec:mic_l'].includes(lb.key);
    labels.push({a, d, it, ext, key: lb.key});
  }
  const s = RI.summary;
  $('stats').innerHTML = `<div><b>${s.length_mm} mm</b>long</div><div><b>${s.width_mm} mm</b>wide</div><div><b>${s.height_sleep_mm}&ndash;${s.height_sentinel_mm}</b>mm tall</div>` +
    `<div><b>${s.total_mass_g} g</b>est. mass</div><div><b>${s.molded_parts}</b>molded parts</div><div><b>${s.static_clashes}</b>CAD clashes</div>`;
}
function groupKeys(k) { const it = items[k]; return Object.values(items).filter(x => x.title === it.title && x.group === it.group).map(x => x.key); }

function highlight(keys, on) {
  for (const k of keys) { const it = items[k]; if (!it) continue;
    for (const n of it.nodes) n.traverse(o => { if (o.isMesh && o.material.emissive && !k.startsWith('elec:led') && k !== 'part:light_band') { o.material.emissive.set(on ? 0xff6a1a : 0x000000); o.material.emissiveIntensity = on ? 0.45 : 1; } }); }
}
function select(keys) {
  if (sel) highlight(sel, false);
  sel = keys; highlight(keys, true);
  const it = items[keys[0]];
  $('info').classList.remove('hidden'); $('info-t').textContent = it.title;
  $('info-k').textContent = (GROUPS[it.group] || {}).name + (it.kind === 'molded' ? ' · molded part' : ' · bought part');
  $('info-d').textContent = it.desc + (it.material ? ' Material: ' + it.material + '.' : '') + (it.process ? ' ' + it.process + '.' : '');
  document.querySelectorAll('#clist .c').forEach(c => c.classList.toggle('sel', c.dataset.keys.split(',').includes(keys[0])));
  labels.forEach(l => l.d.classList.toggle('sel', keys.includes(l.key)));
}

function applyLift() {
  if (links.mast) links.mast.position.copy(links.mast.userData.p0).add(new THREE.Vector3(0, 0, lift));
  $('lift').value = lift; $('liftv').textContent = Math.round(lift) + ' mm';
  document.querySelectorAll('[data-pose]').forEach(b => b.classList.toggle('on', Math.abs(+b.dataset.pose - lift) < 1));
}
function applyAll() {
  for (const it of Object.values(items)) {
    const vis = visible[it.group];
    it.nodes.forEach((n, i) => { n.visible = vis; n.position.copy(it.p0[i]).add(new THREE.Vector3(...it.explode).multiplyScalar(explodeT)); });
  }
  for (const m of shellMats) { m.transparent = xray || m.userData.op < 1; m.opacity = xray ? 0.12 : m.userData.op; m.depthWrite = !xray; m.needsUpdate = true; }
  $('xray').classList.toggle('on', xray); $('lbls').classList.toggle('on', showLabels); $('demo').classList.toggle('on', demo);
  $('explode').value = explodeT;
  document.querySelectorAll('#clist .c').forEach(c => c.classList.toggle('off', !visible[c.dataset.g]));
  applyLift();
}

document.querySelectorAll('[data-view]').forEach(b => b.onclick = () => setView(b.dataset.view));
document.querySelectorAll('[data-pose]').forEach(b => b.onclick = () => { liftTarget = +b.dataset.pose; });
document.querySelectorAll('[data-tab]').forEach(b => b.onclick = () => {
  document.querySelectorAll('[data-tab]').forEach(x => x.classList.toggle('on', x === b));
  document.querySelectorAll('.tab').forEach(t => t.classList.toggle('hidden', t.id !== 'tab-' + b.dataset.tab));
});
$('xray').onclick = () => { xray = !xray; applyAll(); };
$('lbls').onclick = () => { showLabels = !showLabels; applyAll(); };
$('demo').onclick = () => { demo = !demo; if (!demo) { for (const l of Object.values(links)) l.quaternion.copy(l.userData.q0); drawEye(); } applyAll(); };
$('explode').oninput = e => { explodeT = +e.target.value; applyAll(); };
$('lift').oninput = e => { lift = liftTarget = +e.target.value; applyLift(); };
let liftTarget = lift;

const ray = new THREE.Raycaster(), mp = new THREE.Vector2(); let down = null;
r.domElement.addEventListener('pointerdown', e => down = [e.clientX, e.clientY]);
r.domElement.addEventListener('pointerup', e => {
  if (!down || Math.hypot(e.clientX - down[0], e.clientY - down[1]) > 4) return;
  const b = r.domElement.getBoundingClientRect(); mp.set((e.clientX - b.left) / b.width * 2 - 1, -(e.clientY - b.top) / b.height * 2 + 1);
  ray.setFromCamera(mp, cam);
  const hits = ray.intersectObject(root, true).filter(h => h.object.userData.key && isShown(h.object) && !(xray && shellMats.includes(h.object.material)));
  if (hits.length) select(groupKeys(hits[0].object.userData.key)); else { if (sel) highlight(sel, false); sel = null; $('info').classList.add('hidden'); }
});
function isShown(o) { while (o) { if (!o.visible) return false; o = o.parent; } return true; }

const v = new THREE.Vector3(), q = new THREE.Quaternion();
let lastT = 0;
function step(t) {
  const dt = Math.min(0.05, t - lastT); lastT = t;
  if (Math.abs(liftTarget - lift) > 0.2) { lift += Math.sign(liftTarget - lift) * Math.min(Math.abs(liftTarget - lift), dt * 55); applyLift(); }
  if (!demo) return;
  const cyc = t % 10;
  liftTarget = cyc < 3 ? 30 : cyc < 6.5 ? 80 : cyc < 8 ? 30 : 0;
  const spin = cyc < 3 || (cyc > 6.5 && cyc < 8) ? t * 4 : 0;
  for (const [j, ax] of [['wheel_l', [0, 1, 0]], ['wheel_r', [0, 1, 0]]]) { const l = links[j]; if (!l) continue; q.setFromAxisAngle(new THREE.Vector3(...ax), spin); l.quaternion.copy(l.userData.q0).multiply(q); }
  if (links.rotor) { const k = Math.floor(t / 2.5) % 2; q.setFromAxisAngle(new THREE.Vector3(0, 0, 1), k * Math.PI); links.rotor.quaternion.slerp(q, 0.08); }
  const blink = (t % 4) < 0.15 ? 0.1 : 1; drawEye(cyc > 8.5 ? 0.15 : blink, Math.sin(t * 0.9) * 0.6);
}
function placeLabels() {
  const w = el.clientWidth, h = el.clientHeight;
  for (const L of labels) {
    const vis = showLabels && visible[L.it.group] && (L.ext || xray || !visible.shell || explodeT > 0.35);
    if (!vis) { L.d.style.display = 'none'; continue; }
    L.a.getWorldPosition(v); v.project(cam);
    if (v.z > 1 || Math.abs(v.x) > 1.1 || Math.abs(v.y) > 1.1) { L.d.style.display = 'none'; continue; }
    L.d.style.display = ''; L.d.style.transform = `translate(${(v.x * .5 + .5) * w}px,${(-v.y * .5 + .5) * h}px)`;
  }
}
new ResizeObserver(() => { cam.aspect = el.clientWidth / el.clientHeight; cam.updateProjectionMatrix(); r.setSize(el.clientWidth, el.clientHeight); }).observe(el);
(function loop(t) { requestAnimationFrame(loop); step((t || 0) / 1000); ctl.update(); placeLabels(); r.render(scene, cam); })();
