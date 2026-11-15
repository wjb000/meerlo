"""Meerlo - parametric CadQuery model of the molded parts.
Frame: x forward, y left, z up, millimetres, origin on the floor under the wheel axle.
Every molded part is a function returning a cq.Workplane in ASSEMBLY position (mast parts at the fully-down 'sleep' pose).
Wall 2.2 mm nominal (ABS/PC), 1 deg+ draft implied by the lofted shells, split lines where the tools open."""
import math
import cadquery as cq

T = 2.2                       # nominal wall
SPLIT_LO, SPLIT_HI = 44.0, 50.0  # light band between the chassis tub and the top shell
WHEEL_R, WHEEL_W, WHEEL_Y, WHEEL_X = 34.0, 16.0, 64.0, -18.0
MAST_X, MAST_W, MAST_D = -30.0, 20.0, 16.0   # mast section: W along y, D along x
MAST_Z0, MAST_LEN, MAST_STROKE = 9.0, 104.0, 80.0
PINION_Z = 97.0
HEAD_Z0 = MAST_Z0 + MAST_LEN   # head bottom in sleep pose (112)
HEAD_D, HEAD_W, HEAD_H, HEAD_CX, HEAD_R = 44.0, 64.0, 70.0, -27.0, 12.0
EYE_Z = HEAD_Z0 + 41.0         # eye centre (sleep pose)
CAM_Z = HEAD_Z0 + 18.0         # camera 'nose' below the eye: hidden behind the brow when asleep
CUP = dict(x0=4.0, x1=42.0, w=46.0, z0=52.0)
ROTOR = dict(x=22.0, z=54.0, r=16.0, h=6.0)
BROW_TOP = 137.0

# body sections: (z, length, width, corner radius, x offset)
OUTER = [(6, 118, 78, 34, 2), (16, 156, 100, 46, 1), (40, 172, 108, 50, 0), (70, 168, 106, 50, -2),
         (95, 146, 96, 44, -6), (110, 104, 74, 34, -10), (116, 60, 48, 22, -12)]


def rr_wire(L, W, r, z, dx=0.0):
    w = cq.Workplane('XY').workplane(offset=z).center(dx, 0).rect(L, W).val()
    f = cq.Face.makeFromWires(w)
    return f.fillet2D(min(r, min(L, W) / 2 - 0.01), f.Vertices()).outerWire()


def loft(secs):
    return cq.Workplane('XY').add(cq.Solid.makeLoft([rr_wire(L, W, r, z, dx) for z, L, W, r, dx in secs], False))


def body_outer():
    return loft(OUTER)


def body_inner(t=T):
    s = []
    for i, (z, L, W, r, dx) in enumerate(OUTER):
        zz = z + t if i == 0 else (z - t if i == len(OUTER) - 1 else z)
        s.append((zz, L - 2 * t, W - 2 * t, r - t, dx))
    return loft(s)


def box(x0, x1, y0, y1, z0, z1):
    return cq.Workplane('XY').box(x1 - x0, y1 - y0, z1 - z0).translate(((x0 + x1) / 2, (y0 + y1) / 2, (z0 + z1) / 2))


def cyl(r, h, p, d=(0, 0, 1)):
    return cq.Workplane('XY').add(cq.Solid.makeCylinder(r, h, cq.Vector(*p), cq.Vector(*d)))


def hollow():
    return body_outer().cut(body_inner())


def nest_cut():   # pocket in the top shell the head sinks into
    return box(MAST_X - 25, MAST_X + 26, -34, 34, 107, 160).edges('|Z').fillet(10)


def mast_hole(m=2.0):
    return box(MAST_X - MAST_D / 2 - m, MAST_X + MAST_D / 2 + m, -MAST_W / 2 - m, MAST_W / 2 + m, -5, 200)


# ------------------------------------------------------------------ chassis (lower tub)
def chassis():
    s = hollow().intersect(box(-200, 200, -200, 200, -5, SPLIT_LO))
    inner = body_inner()
    feats = []
    for sg in (1, -1):   # motor saddles
        feats.append(box(WHEEL_X - 8, WHEEL_X + 8, min(sg * 17, sg * 47), max(sg * 17, sg * 47), 8, 27.5))
    feats.append(box(MAST_X - 13, MAST_X + 13, -11, 11, 8, 44))                      # mast guide tower
    for xx in (-73, -51):                                                             # battery cradle ribs
        feats.append(box(xx - 1.5, xx + 1.5, -34, 34, 8, 20))
    feats.append(cyl(10, 2, (50, 0, 6.5)))                                               # caster boss
    feats.append(box(ROTOR['x'] - 6, ROTOR['x'] + 6, -21, -18.5, 8, 39.5)); feats.append(box(ROTOR['x'] - 6, ROTOR['x'] + 6, 7, 9.5, 8, 39.5))  # servo flange ribs
    feats.append(cq.Workplane('XY').sphere(8).translate((-55, 0, 12)).intersect(box(-70, -40, -10, 10, 0, 12)))  # rear anti-tip skid
    # treat chute: sloped tube from cup outlet (x~36, z~50) to the chin (x~86, z~16)
    ch_o = cq.Workplane('YZ').rect(30, 22).extrude(64).translate((0, 0, 0))
    ch_o = ch_o.rotate((0, 0, 0), (0, 1, 0), 33).translate((32, 0, 48)).intersect(box(28.6, 200, -40, 40, 0, 51.5))
    feats.append(ch_o)
    for f in feats:
        s = s.union(f.intersect(inner) if f is not ch_o else f.intersect(body_outer()))
    # cuts
    ch_i = cq.Workplane('YZ').rect(25, 17).extrude(80).rotate((0, 0, 0), (0, 1, 0), 33).translate((26, 0, 52))
    s = s.cut(ch_i.intersect(box(30, 200, -40, 40, 10, 51)))
    s = s.cut(box(MAST_X - 9.5, MAST_X + 9.5, -11.5, 12.6, 8.4, 60))                   # guide bore (mast 16x20 + 1.5 clearance)
    for sg in (1, -1):
        s = s.cut(cyl(6.1, 6, (WHEEL_X, sg * 41, WHEEL_R), (0, sg, 0)))                # motor gearbox nose bore
        s = s.cut(cyl(2.4, 30, (WHEEL_X, sg * 60, WHEEL_R), (0, -sg, 0)))              # shaft bore
    s = s.cut(cyl(9.6, 70, (-62, 35, 18.5), (0, -1, 0)))                              # battery
    s = s.cut(box(83, 92, -5, 5, 34, 40))                                             # ToF window
    for (x, y) in ((40, 26), (40, -26), (-44, 22)):                                    # cliff sensor windows
        s = s.cut(box(x - 4, x + 4, y - 3, y + 3, 0, 9))
    s = s.cut(cyl(8.8, 12, (50, 0, 0)))                                               # caster opening
    s = s.cut(box(-95, -79.6, -15, 15, 17, 26).union(box(-95, -82.5, -3.5, 3.5, 31, 37)))     # dock pads + IR window
    return s


def light_band():
    return hollow().intersect(box(-200, 200, -200, 200, SPLIT_LO, SPLIT_HI))


def top_shell():
    s = hollow().intersect(box(-200, 200, -200, 200, SPLIT_HI, 200))
    n = nest_cut()
    tray = box(MAST_X - 27.2, MAST_X + 28.2, -36.2, 36.2, 104.8, 130).edges('|Z').fillet(12).cut(nest_cut()).intersect(body_outer())
    s = s.cut(n).union(tray)
    # brow: raised visor in front of the nest = physical privacy shutter for the camera
    # collar ('cowl') round the nest: high at the front = the brow that hides the camera when asleep
    collar = box(MAST_X - 29.5, MAST_X + 34, -39, 39, 100, BROW_TOP + 4).edges('|Z').fillet(22).cut(nest_cut())
    slope = math.degrees(math.atan2(BROW_TOP - 116.0, 60.0))
    cutter = box(-300, 300, -100, 100, 0, 200).rotate((0, 0, 0), (0, 1, 0), -slope).translate((MAST_X + 30, 0, BROW_TOP))
    collar = collar.cut(cutter)
    try:
        collar = collar.faces('>Z').edges().fillet(2.5)
    except Exception:
        pass
    s = s.union(collar.intersect(box(-200, 200, -200, 200, 104, 200)))
    s = s.cut(mast_hole())
    # treat-cup pocket
    s = s.cut(lid_prism(0.6))
    pocket = box(CUP['x0'] - 2.2, CUP['x1'] + 2.2, -CUP['w'] / 2 - 2.2, CUP['w'] / 2 + 2.2, 60, 125).edges('|Z').fillet(10).cut(
        box(CUP['x0'] - 0.4, CUP['x1'] + 0.4, -CUP['w'] / 2 - 0.4, CUP['w'] / 2 + 0.4, 50, 200).edges('|Z').fillet(8)).intersect(body_inner(0.1))
    s = s.union(pocket)
    for i in range(5):                                                                # speaker grille, rear
        s = s.cut(box(-90, -70, -14 + i * 7 - 1.2, -14 + i * 7 + 1.2, 62, 76))
    return s


def lid_prism(m=0.0):
    return box(CUP['x0'] - m, CUP['x1'] + m, -CUP['w'] / 2 - m, CUP['w'] / 2 + m, 60, 200).edges('|Z').fillet(8 + m)


def cup_lid():
    return hollow().intersect(lid_prism()).intersect(box(-200, 200, -200, 200, 96, 200)).union(
        box(CUP['x0'] + 2.6, CUP['x1'] - 2.6, -CUP['w'] / 2 + 2.6, CUP['w'] / 2 - 2.6, 96, 100).edges('|Z').fillet(6).intersect(body_inner()).cut(
            box(CUP['x0'] + 4.4, CUP['x1'] - 4.4, -CUP['w'] / 2 + 4.4, CUP['w'] / 2 - 4.4, 95, 99).edges('|Z').fillet(4)))


def treat_cup():
    o = box(CUP['x0'], CUP['x1'], -CUP['w'] / 2, CUP['w'] / 2, CUP['z0'], 100).edges('|Z').fillet(8)
    i = box(CUP['x0'] + 1.8, CUP['x1'] - 1.8, -CUP['w'] / 2 + 1.8, CUP['w'] / 2 - 1.8, CUP['z0'] + 1.8, 120).edges('|Z').fillet(6.5)
    c = o.cut(i)
    c = c.cut(cyl(5.2, 5, (ROTOR['x'] + 11, 0, CUP['z0'] - 1)))                         # drop hole to the chute
    c = c.cut(cyl(2.6, 5, (ROTOR['x'], 0, CUP['z0'] - 1)))                              # rotor spline
    # funnel ramps toward the rotor
    ramp = box(CUP['x0'] + 1.8, CUP['x1'] - 1.8, -CUP['w'] / 2 + 1.8, CUP['w'] / 2 - 1.8, CUP['z0'] + 1.8, CUP['z0'] + 16).cut(
        cq.Workplane('XY').add(cq.Solid.makeCone(ROTOR['r'] + 1, ROTOR['r'] + 16, 14.2, cq.Vector(ROTOR['x'], 0, CUP['z0'] + 1.8))))
    c = c.union(ramp.cut(cyl(ROTOR['r'] + 1.0, 30, (ROTOR['x'], 0, CUP['z0']))))
    c = c.union(box(CUP['x0'] + 6, CUP['x0'] + 9, -2, 2, CUP['z0'] + 16, 97))                    # finger rib/handle
    return c


def rotor():
    r = cyl(ROTOR['r'], ROTOR['h'], (ROTOR['x'], 0, ROTOR['z']))
    r = r.cut(cyl(2.5, 4, (ROTOR['x'], 0, ROTOR['z'] - 0.1)))   # servo spline socket
    for a in (0, 180):
        import math
        x = ROTOR['x'] + 11 * math.cos(math.radians(a)); y = 11 * math.sin(math.radians(a))
        r = r.cut(cyl(4.8, 20, (x, y, ROTOR['z'] - 1)))
    r = r.union(cyl(4, 9, (ROTOR['x'], 0, ROTOR['z'] + ROTOR['h'])).edges('>Z').fillet(1.5))   # agitator nub
    return r


def mast():
    m = box(MAST_X - MAST_D / 2, MAST_X + MAST_D / 2, -MAST_W / 2, MAST_W / 2, MAST_Z0, MAST_Z0 + MAST_LEN + 6).edges('|Z').fillet(3)
    m = m.cut(box(MAST_X - MAST_D / 2 + 2, MAST_X + MAST_D / 2 - 2, -MAST_W / 2 + 2, MAST_W / 2 - 2, MAST_Z0 - 1, 300))  # cable channel
    # rack teeth (module 1) on the +y face
    for i in range(int(MAST_LEN / 3.14) - 2):
        z = MAST_Z0 + 4 + i * 3.1416
        m = m.union(box(MAST_X - 4, MAST_X + 4, MAST_W / 2 - 0.2, MAST_W / 2 + 1.6, z, z + 1.5))
    return m


def head_solid(o=0.0):
    return cq.Workplane('XY').box(HEAD_D - 2 * o, HEAD_W - 2 * o, HEAD_H - 2 * o).edges().fillet(HEAD_R - o).translate(
        (HEAD_CX, 0, HEAD_Z0 + HEAD_H / 2))


HEAD_SPLIT = HEAD_CX + 8.0


def _head_shell():
    h = head_solid().cut(head_solid(2.0))
    h = h.cut(cyl(17.2, 20, (HEAD_CX + 10, 0, EYE_Z), (1, 0, 0)))          # eye window
    h = h.cut(cyl(3.6, 20, (HEAD_CX + 10, 0, CAM_Z), (1, 0, 0)))           # camera aperture
    return h


def head_front():
    h = _head_shell().intersect(box(HEAD_SPLIT, 100, -100, 100, 0, 400))
    bezel = cyl(20.5, 2.4, (HEAD_CX + HEAD_D / 2 - 1.4, 0, EYE_Z), (1, 0, 0)).cut(cyl(17.2, 40, (HEAD_CX, 0, EYE_Z), (1, 0, 0)))
    return h.union(bezel.edges().fillet(0.9))


def head_rear():
    h = _head_shell().intersect(box(-200, HEAD_SPLIT, -100, 100, 0, 400))
    for sg in (1, -1):    # ears (mic ports)
        e = cq.Workplane('XY').sphere(10.5).translate((HEAD_CX - 6, sg * 21, HEAD_Z0 + HEAD_H - 1)).intersect(
            box(-200, 200, -200, 200, HEAD_Z0 + HEAD_H - 6, 400))
        e = e.cut(cyl(0.6, 30, (HEAD_CX - 6, sg * 19, HEAD_Z0 + HEAD_H - 8)))
        h = h.union(e)
    h = h.cut(box(MAST_X - MAST_D / 2 - 0.2, MAST_X + MAST_D / 2 + 0.2, -MAST_W / 2 - 0.2, MAST_W / 2 + 0.2, HEAD_Z0 - 2, HEAD_Z0 + 2.5))
    sock = box(MAST_X - MAST_D / 2 - 2, MAST_X + MAST_D / 2 + 2, -MAST_W / 2 - 2, MAST_W / 2 + 2, HEAD_Z0 + 1, HEAD_Z0 + 14).cut(
        box(MAST_X - MAST_D / 2 - 0.1, MAST_X + MAST_D / 2 + 0.1, -MAST_W / 2 - 0.1, MAST_W / 2 + 0.1, HEAD_Z0, HEAD_Z0 + 12))
    return h.union(sock)


def wheel_hub(sg):
    y0 = sg * WHEEL_Y
    w = cyl(WHEEL_R - 4.5, WHEEL_W - 2, (WHEEL_X, y0 - sg * (WHEEL_W / 2 - 1), WHEEL_R), (0, sg, 0))
    w = w.cut(cyl(WHEEL_R - 8, 4, (WHEEL_X, y0 + sg * (WHEEL_W / 2 - 3.5), WHEEL_R), (0, sg, 0)))          # dished face
    import math
    w = w.union(cyl(5.5, 3, (WHEEL_X, y0 + sg * (WHEEL_W / 2 - 5), WHEEL_R), (0, sg, 0)))
    w = w.cut(cyl(WHEEL_R - 7.5, WHEEL_W - 6, (WHEEL_X, y0 - sg * (WHEEL_W / 2 + 1), WHEEL_R), (0, sg, 0)))   # coring from the inside
    w = w.union(cyl(6, WHEEL_W - 6, (WHEEL_X, y0 - sg * (WHEEL_W / 2 - 1), WHEEL_R), (0, sg, 0)))
    w = w.cut(cyl(1.6, 9, (WHEEL_X, y0 - sg * (WHEEL_W / 2 + 1), WHEEL_R), (0, sg, 0)))                       # D-shaft bore
    for k in range(4):   # paw-print pads on the hub face
        a = math.radians(-60 + k * 40)
        p = (WHEEL_X + 10.5 * math.sin(a), y0 + sg * (WHEEL_W / 2 - 5), WHEEL_R + 10.5 * math.cos(a))
        w = w.union(cyl(3.0, 2.4, p, (0, sg, 0)))
    w = w.union(cyl(7.5, 2.4, (WHEEL_X, y0 + sg * (WHEEL_W / 2 - 5), WHEEL_R - 3), (0, sg, 0)))
    return w


def wheel_tire(sg):
    y0 = sg * WHEEL_Y
    t = cyl(WHEEL_R, WHEEL_W, (WHEEL_X, y0 - sg * WHEEL_W / 2, WHEEL_R), (0, sg, 0)).edges().fillet(4.5)
    t = t.cut(cyl(WHEEL_R - 4.6, 40, (WHEEL_X, y0 - sg * 20, WHEEL_R), (0, sg, 0)))
    for k in range(24):  # tread sipes
        t = t.cut(box(WHEEL_X - 0.8, WHEEL_X + 0.8, y0 - 5, y0 + 5, WHEEL_R * 2 - 1.4, WHEEL_R * 2 + 2).rotate((WHEEL_X, 0, WHEEL_R), (WHEEL_X, 1, WHEEL_R), k * 15))
    return t


DOCK_X = -178.0


def dock():
    base = box(DOCK_X - 30, DOCK_X + 52, -62, 62, 0, 6).edges('|Z').fillet(20).edges('>Z').fillet(2.5)
    wall = cq.Workplane('XY').add(cq.Solid.makeLoft([rr_wire(30, 124, 14, 0, DOCK_X - 18), rr_wire(26, 116, 12, 40, DOCK_X - 20),
                                                     rr_wire(16, 90, 7, 62, DOCK_X - 22)], False))
    d = base.union(wall)
    d = d.cut(box(DOCK_X + 2, DOCK_X + 60, -40, 40, 3.5, 20))                         # wheel lane
    d = d.union(box(DOCK_X - 6, DOCK_X + 6, -18, 18, 3.5, 28).edges('|X').fillet(3))  # contact tower
    d = d.cut(box(DOCK_X - 12, DOCK_X - 2, -6, 6, 30, 42))                             # beacon window
    try:
        d = d.faces('<Z').shell(-2.4)                                                  # open-bottom molded shell + weight plate
    except Exception:
        pass
    return d


PARTS = [
    dict(name='chassis', fn=chassis, link='base', color='#5c4b3f', material='ABS/PC, warm taupe', process='Injection molded (2-plate tool, 2 lifters)'),
    dict(name='light_band', fn=light_band, link='base', color='#ffd59a', material='Clear PC, frosted', process='Injection molded'),
    dict(name='top_shell', fn=top_shell, link='base', color='#ecdcc0', material='ABS/PC, sand', process='Injection molded (1 slider for the grille)'),
    dict(name='treat_cup', fn=treat_cup, link='base', color='#d9c6a6', material='PP, food-contact grade', process='Injection molded, dishwasher safe'),
    dict(name='cup_lid', fn=cup_lid, link='base', color='#5a4636', material='PC tinted smoke', process='Injection molded'),
    dict(name='rotor', fn=rotor, link='rotor', color='#f2a65a', material='POM (acetal)', process='Injection molded'),
    dict(name='mast', fn=mast, link='mast', color='#3d332c', material='POM or PA12-GF, rack molded in', process='Injection molded'),
    dict(name='head_rear', fn=head_rear, link='mast', color='#ecdcc0', material='ABS/PC, sand', process='Injection molded'),
    dict(name='head_front', fn=head_front, link='mast', color='#2b2420', material='ABS/PC, espresso gloss', process='Injection molded'),
    dict(name='wheel_l', fn=lambda: wheel_hub(1), link='wheel_l', color='#ecdcc0', material='ABS hub', process='2-shot molded with TPU tyre'),
    dict(name='tire_l', fn=lambda: wheel_tire(1), link='wheel_l', color='#2e2a27', material='TPU 85A tyre', process='overmold (same part as hub)'),
    dict(name='wheel_r', fn=lambda: wheel_hub(-1), link='wheel_r', color='#ecdcc0', material='ABS hub', process='2-shot molded with TPU tyre'),
    dict(name='tire_r', fn=lambda: wheel_tire(-1), link='wheel_r', color='#2e2a27', material='TPU 85A tyre', process='overmold (same part as hub)'),
    dict(name='dock', fn=dock, link='dock', color='#ecdcc0', material='ABS, sand, weighted base', process='Injection molded'),
]

JOINTS = {   # name: (parent, child, origin, axis, limits)
    'wheel_l': ('base', 'wheel_l', (WHEEL_X, WHEEL_Y, WHEEL_R), (0, 1, 0), None),
    'wheel_r': ('base', 'wheel_r', (WHEEL_X, -WHEEL_Y, WHEEL_R), (0, 1, 0), None),
    'mast_lift': ('base', 'mast', (MAST_X, 0, 0), (0, 0, 1), (0, MAST_STROKE)),
    'treat_rotor': ('base', 'rotor', (ROTOR['x'], 0, ROTOR['z']), (0, 0, 1), (0, 180)),
}
