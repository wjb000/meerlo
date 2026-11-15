#!/usr/bin/env python3
"""Build everything from cad/meerlo.py + cad/elec.py:
  cad/step/<part>.step       molded parts (also the 3D-print prototype geometry)
  cad/stl/<part>.stl         ASCII STL (decimated to <= 6k facets for git; slice from STEP for full fidelity)
  cad/reports/*.json         interference check, mass + centre of mass
  site/assets/meerlo.gltf + robot_info.json  viewer model (embedded buffer, link hierarchy, labels)
Run: python cad/export.py   (cadquery 2.x, trimesh, manifold3d)"""
import os, sys, json, math, time
import numpy as np, trimesh, cadquery as cq
import manifold3d as mf
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
import meerlo, elec
from textmesh import write_ascii_stl, glb_to_embedded_gltf

DENS = {'ABS': 1.05e-3, 'Clear': 1.2e-3, 'PC': 1.2e-3, 'PP': 0.91e-3, 'POM': 1.41e-3, 'TPU': 1.2e-3}
ELEC_MASS = {'liftmotor': 3.0, 'servo': 9.0, 'battery': 46.0, 'pcb': 12.0, 'esp32': 3.0, 'lcd': 8.0, 'speaker': 3.0, 'caster': 9.0,
             'camera': 2.0, 'tof': 0.5, 'pinion': 0.5}
GROUP = {'chassis': 'shell', 'top_shell': 'shell', 'light_band': 'shell', 'cup_lid': 'shell', 'head_rear': 'shell', 'head_front': 'shell',
         'mast': 'mechanism', 'rotor': 'mechanism', 'treat_cup': 'mechanism', 'pinion': 'mechanism', 'servo': 'mechanism', 'liftmotor': 'mechanism',
         'wheel': 'drivetrain', 'tire': 'drivetrain', 'motor': 'drivetrain', 'caster': 'drivetrain', 'axle': 'drivetrain',
         'battery': 'power', 'bclip': 'power', 'pad': 'power',
         'pcb': 'electronics', 'esp32': 'electronics', 'ic': 'electronics', 'fpc': 'electronics',
         'tof': 'sensors', 'cliff': 'sensors', 'irrx': 'sensors', 'camera': 'sensors', 'mic': 'sensors', 'irled': 'sensors',
         'lcd': 'expression', 'speaker': 'expression', 'led': 'expression', 'dock': 'dock', 'beacon': 'dock'}
EXPLODE = {'top_shell': (0, 0, 70), 'light_band': (0, 0, 34), 'cup_lid': (0, 0, 125), 'treat_cup': (0, 0, 105), 'rotor': (0, 0, 80),
           'mast': (0, 0, 60), 'head_rear': (-30, 0, 85), 'head_front': (35, 0, 85), 'lcd': (55, 0, 85), 'camera': (55, 0, 80), 'irled': (55, 0, 80),
           'mic': (-30, 0, 95), 'fpc': (0, 0, 60), 'motor': (0, 1, 0), 'axle': (0, 1, 0),
           'pcb': (0, 0, 40), 'esp32': (-12, 0, 40), 'ic': (-12, 0, 40),
           'servo': (0, 0, 22), 'battery': (-30, 0, -4), 'bclip': (-30, 0, -4), 'caster': (0, 0, -30), 'cliff': (0, 0, -18), 'tof': (30, 0, 0),
           'irrx': (-30, 0, 0), 'pad': (-30, 0, 0), 'speaker': (-40, 0, 70), 'led': (0, 0, 34), 'liftmotor': (0, 30, 20), 'pinion': (0, 30, 20),
           'dock': (-70, 0, 0), 'beacon': (-70, 0, 0)}
TXT = {
    'chassis': ('Chassis tub', 'One molded tub: floor, motor saddles, battery cradle, mast guide tower, servo ribs, treat chute, anti-tip skid, sensor windows.'),
    'light_band': ('Light band', 'Frosted clear-PC ring on the split line. Glows with the LED ring: mood, status, night-light.'),
    'top_shell': ('Top shell', 'Upper body with the head nest, the privacy brow, the treat-cup pocket and the speaker grille all molded in.'),
    'treat_cup': ('Treat cup', 'Lift-out, dishwasher-safe PP cup, ~180 ml (~120 small kibble treats). Funnel floor feeds the rotor.'),
    'cup_lid': ('Cup lid', 'Smoke-tint lid that is the top of the body when closed. Snap fit, finger tab underneath.'),
    'rotor': ('Treat rotor', 'Two-pocket acetal rotor: each half-turn of the servo drops one treat down the chute and out of the chin.'),
    'mast': ('Periscope mast', 'Hollow POM mast with the rack molded in. Lifts the head 85 mm: asleep, roam, or meerkat "sentinel" stance.'),
    'head_rear': ('Head shell', 'Rounded head with two little ears (mic ports) and the mast socket.'),
    'head_front': ('Face plate', 'Gloss espresso face: eye window with bezel and the camera "nose".'),
    'wheel': ('Wheel hub', '68 mm wheel, paw-print hubcap; 2-shot molded with its TPU tyre (one part). Climbs rug edges and 12 mm thresholds.'),
    'tire': ('Tyre (TPU overmold)', 'Soft 85A TPU tread with sipes: quiet on hard floors, grips on rugs.'),
    'dock': ('Dock', 'Weighted charging dock: spring contacts, IR beacon, USB-C in. Meerlo backs onto it by itself.'),
}
LBL = {'chassis': (60, -50, 22), 'light_band': (40, 50, 47), 'top_shell': (-60, -40, 90), 'treat_cup': (23, 0, 80), 'cup_lid': (23, 10, 110),
       'rotor': (20, 8, 58), 'mast': (-30, 0, 100), 'head_rear': (-35, 25, 150), 'head_front': (-5, -20, 160), 'wheel_l': (-16, 72, 50), 'tire_r': (-16, -72, 8),
       'dock': (-198, -50, 50)}


def d(*p):
    q = os.path.join(ROOT, *p); os.makedirs(q, exist_ok=True); return q


def tess(shape, tol=0.15):
    v, f = shape.tessellate(tol, 0.2)
    m = trimesh.Trimesh(np.array([[p.x, p.y, p.z] for p in v]), np.array(f), process=True)
    m.merge_vertices(); trimesh.repair.fix_normals(m)
    return m


def wp_mesh(wp, tol=0.15):
    vs = [v for v in wp.vals() if isinstance(v, cq.Shape)]
    return trimesh.util.concatenate([tess(s, tol) for s in vs])


def to_mf(m):
    return mf.Manifold(mf.Mesh(vert_properties=np.asarray(m.vertices, np.float32), tri_verts=np.asarray(m.faces, np.uint32)))


def inter_vol(a, b):
    try:
        return (to_mf(a) ^ to_mf(b)).volume()
    except Exception:
        return float('nan')


def stem(k):
    k = k.split(':')[-1]
    for g in (k, k.split('_')[0], ''.join(c for c in k.split('_')[0] if not c.isdigit())):
        if g in GROUP:
            return g
    return k


def main():
    t0 = time.time()
    J = meerlo.JOINTS
    origin = {'base': np.zeros(3), 'dock': np.zeros(3)}
    for jn, (p, c, o, a, lim) in J.items():
        origin[c] = np.array(o, float)
    parts = []
    for P in meerlo.PARTS:
        s = P['fn'](); P = dict(P); P['solid'] = s; P['mesh'] = wp_mesh(s); parts.append(P)
        print('part', P['name'], len(P['mesh'].faces), P['mesh'].is_watertight, round(time.time() - t0, 1), flush=True)
    E = elec.components()
    for e in E:
        e['mesh'] = wp_mesh(e['wp'], 0.2)

    stepd, stld = d('cad', 'step'), d('cad', 'stl')
    for P in parts:
        cq.exporters.export(P['solid'], os.path.join(stepd, P['name'] + '.step'))
        m = P['mesh']
        if len(m.faces) > 6000:
            m = m.simplify_quadric_decimation(face_count=6000)
        write_ascii_stl(m, os.path.join(stld, P['name'] + '.stl'), P['name'])

    allm = [('part:' + P['name'], P['mesh']) for P in parts if P['name'] != 'dock'] + [('elec:' + e['key'], e['mesh']) for e in E if e['link'] != 'dock']
    clashes = []
    ALLOWED = {('part:wheel_l', 'part:tire_l'), ('part:wheel_r', 'part:tire_r')}
    for i in range(len(allm)):
        for j in range(i + 1, len(allm)):
            a, b = allm[i], allm[j]
            if (a[0], b[0]) in ALLOWED:
                continue
            ba, bb = a[1].bounds, b[1].bounds
            if np.any(ba[1] < bb[0]) or np.any(bb[1] < ba[0]):
                continue
            v = inter_vol(a[1], b[1])
            if v > 1.0:
                clashes.append(dict(a=a[0], b=b[0], mm3=round(v, 1)))
    mast_up = [(P['name'], P['mesh']) for P in parts if P['link'] == 'mast'] + [(e['key'], e['mesh']) for e in E if e['link'] == 'mast']
    fixed = [(P['name'], P['mesh']) for P in parts if P['link'] == 'base'] + [(e['key'], e['mesh']) for e in E if e['link'] == 'base']
    up_clash = []
    for st in (25, 55, meerlo.MAST_STROKE):
        for n1, m in mast_up:
            mm = m.copy(); mm.apply_translation((0, 0, st))
            for n2, f in fixed:
                ba, bb = mm.bounds, f.bounds
                if np.any(ba[1] < bb[0]) or np.any(bb[1] < ba[0]):
                    continue
                v = inter_vol(mm, f)
                if v > 1.0:
                    up_clash.append(dict(stroke=st, a=n1, b=n2, mm3=round(v, 1)))
    tot, mom = 0.0, np.zeros(3)
    massrows = []
    for P in parts:
        if P['name'] == 'dock':
            continue
        mat = P['material'].split()[0].split('/')[0].split(',')[0]
        dens = DENS.get(mat, 1.05e-3)
        vol = sum(v.Volume() for v in P['solid'].vals() if isinstance(v, cq.Shape))
        g = vol * dens
        c = P['mesh'].center_mass if P['mesh'].is_watertight else P['mesh'].bounds.mean(0)
        tot += g; mom += g * c; massrows.append(dict(part=P['name'], grams=round(g, 1), material=P['material']))
    for e in E:
        if e['link'] == 'dock':
            continue
        st = stem(e['key'])
        g = 2.5 if st == 'motor' else ELEC_MASS.get(st, 0.4)
        tot += g; mom += g * e['mesh'].bounds.mean(0)
    com = mom / tot
    treats = 25.0
    com_t = (mom + treats * np.array([23, 0, 70])) / (tot + treats)
    caster_x, axle_x = 50.0, meerlo.WHEEL_X
    allb = np.vstack([m.bounds for _, m in allm])
    summary = dict(total_mass_g=round(tot), com_mm=[round(x, 1) for x in com], com_with_treats_mm=[round(x, 1) for x in com_t],
                   front_caster_load_pct=round(100 * (com[0] - axle_x) / (caster_x - axle_x), 1),
                   front_caster_load_pct_with_treats=round(100 * (com_t[0] - axle_x) / (caster_x - axle_x), 1),
                   molded_parts=12, unique_tools=11, length_mm=round(allb[:, 0].max() - allb[:, 0].min()), width_mm=round(allb[:, 1].max() - allb[:, 1].min()),
                   height_sleep_mm=round(allb[:, 2].max()), height_sentinel_mm=round(allb[:, 2].max() + meerlo.MAST_STROKE),
                   static_clashes=len(clashes), mast_travel_clashes=len(up_clash), components=len(E))
    rd = d('cad', 'reports')
    json.dump(dict(static=clashes, mast_travel=up_clash), open(os.path.join(rd, 'interference.json'), 'w'), indent=1)
    json.dump(dict(summary=summary, parts=massrows), open(os.path.join(rd, 'mass_properties.json'), 'w'), indent=1)
    print(json.dumps(summary, indent=1)); print('clashes', clashes[:40]); print('up', up_clash[:20])

    out = d('site', 'assets')
    sc = trimesh.Scene()
    for l in ['base', 'dock', 'wheel_l', 'wheel_r', 'mast', 'rotor']:
        T = np.eye(4); T[:3, 3] = origin[l]
        sc.graph.update(frame_from=sc.graph.base_frame, frame_to='link:' + l, matrix=T)

    def put(name, mesh, link, faces):
        m = mesh.copy(); m.apply_translation(-origin[link])
        if len(m.faces) > faces:
            m = m.simplify_quadric_decimation(face_count=faces)
        m.vertices = np.round(m.vertices, 2)
        sc.add_geometry(m, node_name=name, geom_name=name, parent_node_name='link:' + link)

    items, labels = {}, []
    BUDGET = {'chassis': 9000, 'top_shell': 9000, 'dock': 2500, 'tire_l': 2400, 'tire_r': 2400, 'head_rear': 3500, 'head_front': 2500, 'mast': 1600}
    for P in parts:
        key = 'part:' + P['name']
        put(key, P['mesh'], P['link'], BUDGET.get(P['name'], 1800))
        st = stem(P['name'])
        t, s = TXT[st]
        ex = list(EXPLODE.get(st, (0, 0, 0)))
        if st in ('wheel', 'tire'):
            ex = [0, 45 * (1 if P['name'].endswith('_l') else -1), 0]
        items[key] = dict(title=t, desc=s, group=GROUP[st], color=P['color'], material=P['material'], process=P['process'], kind='molded', explode=ex)
        if P['name'] in LBL:
            labels.append(dict(key=key, node='link:' + P['link'], local=(np.array(LBL[P['name']], float) - origin[P['link']]).tolist()))
    seen = set()
    for e in E:
        key = 'elec:' + e['key']
        put(key, e['mesh'], e['link'], 900)
        st = stem(e['key'])
        ex = np.array(EXPLODE.get(st, (0, 0, 0)), float)
        if st in ('motor', 'axle'):
            sg = 1 if '_l' in e['key'] else -1
            ex = np.array([0, (22 if st == 'motor' else 52) * sg, 0])
        if e['key'].startswith('dock_'):
            ex = np.array(EXPLODE['dock'], float)
        items[key] = dict(title=e['name'], desc=e['spec'], group=('dock' if e['link'] == 'dock' else GROUP.get(st, 'electronics')), color=e['color'],
                          kind='bought', explode=ex.tolist(), emissive=st in ('led', 'beacon'))
        if e.get('label') and e['name'] not in seen:
            seen.add(e['name'])
            labels.append(dict(key=key, node='link:' + e['link'], local=(e['mesh'].bounds.mean(0) - origin[e['link']]).tolist()))
    glb = os.path.join(out, 'meerlo.glb'); sc.export(glb)
    glb_to_embedded_gltf(glb, os.path.join(out, 'meerlo.gltf')); os.remove(glb)
    info = dict(summary=summary, joints={jn: dict(node='link:' + c, axis=list(a), limits=list(lim) if lim else None, type='prismatic' if jn == 'mast_lift' else 'revolute')
                                         for jn, (p, c, o, a, lim) in J.items()}, items=items, labels=labels)
    json.dump(info, open(os.path.join(out, 'robot_info.json'), 'w'), indent=1)
    print('gltf kB', os.path.getsize(os.path.join(out, 'meerlo.gltf')) // 1024, 'time', round(time.time() - t0))


if __name__ == '__main__':
    main()
