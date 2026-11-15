"""Bought components, modelled from datasheet dimensions and placed in assembly position.
Each entry: key, name, spec (shown in the viewer), link, colour, mesh (cq.Workplane), kind."""
import math
import cadquery as cq
from meerlo import box, cyl, PINION_Z, WHEEL_X, MAST_X, MAST_W, MAST_D, HEAD_CX, HEAD_D, EYE_Z, CAM_Z, HEAD_Z0, HEAD_H, WHEEL_R, ROTOR, CUP, DOCK_X, SPLIT_LO, SPLIT_HI, OUTER

PCB_X = -12.0


def n20(x, y, z, axis_sign=1, encoder=True, vertical=False):
    """N20 gearmotor: 12x10 gearbox (9 mm), 10x12 can (15 mm), optional 4 mm magnetic encoder, 3 mm D-shaft (10 mm)."""
    gb = box(0, 9, -6, 6, -5, 5)
    can = cq.Workplane('YZ').ellipse(6, 5).extrude(15).translate((9, 0, 0)).intersect(box(9, 24, -6, 6, -5, 5))
    shaft = cyl(1.5, 10, (0, 0, 0), (-1, 0, 0))
    parts = {'gearbox': gb, 'can': can, 'shaft': shaft}
    if encoder:
        parts['encoder'] = box(24, 28, -6.5, 6.5, -6.5, 6.5)
    return parts


def place(wp, rot=None, t=(0, 0, 0)):
    if rot:
        for ax, deg in rot:
            wp = wp.rotate((0, 0, 0), ax, deg)
    return wp.translate(t)


def components():
    E = []

    def add(key, name, spec, link, color, wp, kind='bought', label=True):
        E.append(dict(key=key, name=name, spec=spec, link=link, color=color, wp=wp, kind=kind, label=label))

    # --- drivetrain: two N20 encoder gearmotors, axle along y, gearbox outboard (shaft into the wheel hub)
    for sg, nm in ((1, 'l'), (-1, 'r')):
        m = n20(0, 0, 0)
        rot = [((0, 0, 1), -90 * sg)]          # shaft (-x) -> outboard
        for k, w in m.items():
            ww = place(w, rot, (WHEEL_X, sg * 50, WHEEL_R))
            add(f'motor_{nm}_{k}', 'Drive gearmotor N20 + encoder', 'N20 metal gearmotor, 6 V, 1:50, 2-channel magnetic encoder (wheel odometry). '
                '~300 rpm at 3.7 V gives 0.5 m/s top speed on 68 mm wheels; 2 per robot.', 'base',
                {'gearbox': '#b9bec6', 'can': '#c9ced6', 'shaft': '#d9dde3', 'encoder': '#1d5f3a'}[k], ww, label=(k == 'can'))
    # --- mast lift motor (no encoder, homed by stall on the end stops) + module-1 pinion
    m = n20(0, 0, 0, encoder=False)
    for k, w in m.items():
        ww = place(w, [((0, 1, 0), 90)], (MAST_X, 23.6, PINION_Z - 10))   # shaft pointing up (+z)
        add(f'liftmotor_{k}', 'Periscope lift motor N20', 'N20 gearmotor 1:150 (no encoder). Drives a 12-tooth pinion on the mast rack: 80 mm of stroke in ~1.5 s. '
            'Position from motor-current end-stop homing + time.', 'base', {'gearbox': '#b9bec6', 'can': '#c9ced6', 'shaft': '#d9dde3'}[k], ww, label=(k == 'can'))
    pin = cq.Workplane('XY').polygon(12, 14).extrude(6).translate((MAST_X, 18.4, PINION_Z))
    add('pinion', 'Mast pinion (POM, m1 z12)', 'Stock 12-tooth module-1 POM pinion pressed on the lift motor D-shaft.', 'base', '#f2a65a', pin)
    # --- treat servo under the cup (output spline drives the rotor through the cup floor)
    sv = box(-6.1, 6.1, -17, 6, 24, 46.5).union(box(-6.1, 6.1, -21.8, 10.7, 39.5, 42))
    sv = sv.union(cyl(5.9, 4, (0, 0, 46.5))).union(cyl(2.3, 5.6, (0, 0, 50.4)))
    sv = sv.translate((ROTOR['x'], 0, 0))
    add('servo', 'Treat servo (SG90-class)', '9 g micro servo, 180 deg. Swings the two-pocket rotor: each half turn drops exactly one treat into the chute.', 'base', '#3f6fb5', sv)
    # --- battery: one 18650 Li-ion (protected) lying across the rear
    add('battery', '18650 Li-ion cell 3000 mAh', 'One protected 18650 cell (3.6 V, ~10.8 Wh), UL 2054 / UN38.3. ~3 h roaming or 24 h+ on watch, docked.', 'base', '#2f62a8',
        cyl(9.0, 65, (-62, 32.5, 18.5), (0, -1, 0)))
    for sg in (1, -1):
        add(f'bclip_{"l" if sg > 0 else "r"}', 'Battery contacts', 'Nickel-plated spring contacts pressed into the chassis cradle.', 'base', '#cfd3d8',
            box(-70, -54, sg * 33.4 - 0.4, sg * 33.4 + 0.4, 10.5, 26.5), label=False)
    # --- main board, vertical behind the treat cup
    add('pcb', 'Main board (4-layer, 70x40 mm)', 'Single PCB: ESP32-S3 module, 2x DRV8833 motor drivers, 6-axis IMU, Li-ion charger + protection, '
        'I2S amp, LED driver, all connectors. Assembled on the same SMT line as the rest.', 'base', '#1c3b2c', box(PCB_X - 0.8, PCB_X + 0.8, -35, 35, 50, 90))
    add('esp32', 'ESP32-S3-WROOM-1 N8R8', 'Dual-core 240 MHz + vector AI instructions, 8 MB flash, 8 MB PSRAM, Wi-Fi 4 + BLE 5, FCC/CE-certified module. '
        'Runs navigation, on-device pet/person/sound detection and the camera stream.', 'base', '#9aa3ad', box(PCB_X - 4.0, PCB_X - 0.8, -9, 9, 64.5, 90))
    for i, (nm, y, z, w, h, c) in enumerate([('DRV8833 motor driver (x2)', -24, 58, 4, 4, '#222'), ('DRV8833 motor driver (x2)', -16, 58, 4, 4, '#222'),
                                             ('IMU (6-axis)', 18, 70, 3, 3, '#222'), ('Li-ion charger + protector', 24, 58, 4, 4, '#222'),
                                             ('MAX98357A I2S amp', 18, 58, 3, 3, '#222')]):
        add(f'ic{i}', nm, {'DRV8833 motor driver (x2)': 'TI DRV8833, dual H-bridge, 1.5 A/ch: one for the wheels, one for the lift motor + spare.',
                           'IMU (6-axis)': 'QMI8658 / ICM-42670-class accel + gyro: tilt, bump, pick-up and stuck detection.',
                           'Li-ion charger + protector': '1.5 A linear charger + DW01 protector + NTC: charges from the dock pads in ~2.5 h.',
                           'MAX98357A I2S amp': '3 W class-D I2S amplifier for voice, chirps and your recorded "good boy".'}[nm],
            'base', c, box(PCB_X - 1.6, PCB_X - 0.8, y - w / 2, y + w / 2, z - h / 2, z + h / 2), label=(i in (0, 2, 3, 4)))
    # --- sensors
    add('tof', 'Front ToF ranger VL53L1X', 'ST VL53L1X time-of-flight, 4 m, 27 deg FoV, multi-zone ROI scan: obstacle + wall following behind an IR window.', 'base', '#7a2fa0',
        box(79, 80.6, -6, 6, 32, 42).union(box(80.6, 82.4, -2.5, 2.5, 35.8, 38.2)))
    for nm, (x, y) in (('fl', (40, 26)), ('fr', (40, -26)), ('rr', (-44, 22))):
        add(f'cliff_{nm}', 'Cliff sensor ITR8307 (x3)', 'Reflective IR pair looking at the floor: stops before stairs and table edges.', 'base', '#7a2fa0',
            box(x - 5, x + 5, y - 4, y + 4, 9.2, 10.4).union(box(x - 2, x + 2, y - 1.5, y + 1.5, 7.2, 9.2)), label=(nm == 'fl'))
    add('irrx', 'Dock-homing IR receiver', '38 kHz IR receiver at the rear: finds the dock beacon and backs straight onto the charging pads.', 'base', '#7a2fa0',
        box(-82.0, -77.0, -3, 3, 30.5, 37.5))
    add('camera', 'Camera OV3660 (3 MP, 120 deg)', 'Wide-angle 3 MP camera on a 24-pin FPC that runs down the hollow mast. Night mode with the IR-cut-free lens + 2 IR LEDs. '
        'Hidden behind the brow when Meerlo is asleep: a real privacy shutter.', 'mast', '#7a2fa0',
        box(HEAD_CX + 14, HEAD_CX + 17, -5, 5, CAM_Z - 5, CAM_Z + 5).union(cyl(3.4, 4.2, (HEAD_CX + 17, 0, CAM_Z), (1, 0, 0))))
    add('fpc', 'Camera/eye flex cable', '24-pin camera FPC + eye cable, routed down the mast channel with a 90 mm rolling service loop.', 'mast', '#c88a2a',
        box(MAST_X - 0.15, MAST_X + 0.15, -7, 7, 14, HEAD_Z0 + 4), label=False)
    for sg, nm in ((1, 'l'), (-1, 'r')):
        add(f'mic_{nm}', 'MEMS microphones (x2, in the ears)', 'Two I2S MEMS mics: bark/meow/glass-break/smoke-alarm detection, direction of sound, two-way talk.', 'mast', '#7a2fa0',
            box(HEAD_CX - 9, HEAD_CX - 3, sg * 19 - 3, sg * 19 + 3, HEAD_Z0 + HEAD_H - 9, HEAD_Z0 + HEAD_H - 8), label=(nm == 'l'))
    for sg, nm in ((1, 'l'), (-1, 'r')):
        add(f'irled_{nm}', 'Night-vision IR LEDs (x2)', '850 nm IR LEDs either side of the camera for seeing in the dark.', 'mast', '#5a1f70',
            cyl(1.6, 3, (HEAD_CX + 16.5, sg * 9, CAM_Z), (1, 0, 0)), label=False)
    # --- expression
    add('lcd', 'Round eye display 1.28" GC9A01', '240x240 round IPS (32.4 mm active), SPI. One big expressive eye: sleepy, curious, alert, happy.', 'mast', '#101418',
        cyl(18.7, 1.8, (HEAD_CX + 18.0, 0, EYE_Z), (1, 0, 0)).union(box(HEAD_CX + 14.6, HEAD_CX + 18.0, -18, 18, EYE_Z - 18, EYE_Z + 18).edges('|X').fillet(8)))
    add('speaker', 'Speaker 20x30 mm, 1 W', '8 ohm 1 W oval speaker firing through the rear grille.', 'base', '#2a2a2a',
        cq.Workplane('YZ').ellipse(15, 10).extrude(5).translate((-79, 0, 69)).rotate((-79, 0, 69), (0, 1, 0), -20))
    # LED ring under the light band
    import numpy as np
    n = 12
    for i in range(n):
        a = 2 * math.pi * i / n
        x, y = 78 * math.cos(a), 46 * math.sin(a)
        add(f'led{i}', 'RGB LEDs WS2812B-2020 (x12)', '12 addressable RGB LEDs on a flex ring behind the frosted band: mood, status, night-light, "follow me" glow.', 'base',
            '#ffcf8a', box(-2, 2, -2, 2, 46, 48).rotate((0, 0, 0), (0, 0, 1), math.degrees(a)).translate((x, y, 0)), label=(i == 1))
    # caster
    add('caster', 'Ball caster 1/2"', 'Ball caster with a 12.7 mm steel ball. 3-point stance: two wheels + this ball, plus a rear anti-tip skid.', 'base', '#9aa1ab',
        cyl(8.5, 6, (50, 0, 6.6)).union(cq.Workplane('XY').sphere(6.35).translate((50, 0, 6.35))))
    for sg in (1, -1):
        add(f'pad_{"l" if sg > 0 else "r"}', 'Charging pads (robot side)', 'Two gold-plated contact pads at the rear; the dock springs press on them.', 'base', '#d4a64a',
            box(-81.2, -79.8, sg * 8 - 4, sg * 8 + 4, 18.5, 24.5), label=(sg > 0))
    for sg in (1, -1):
        add(f'axle_{"l" if sg > 0 else "r"}', 'Wheel fasteners', 'M2.5 screw + washer holding each wheel on the D-shaft.', 'wheel_' + ('l' if sg > 0 else 'r'), '#9aa1ab',
            cyl(2.5, 2, (WHEEL_X, sg * 70.5, WHEEL_R), (0, sg, 0)), label=False)
    # --- dock electronics
    add('dock_pcb', 'Dock board + USB-C', 'Tiny dock PCB: USB-C 5 V in, reverse/short protection, 38 kHz beacon driver.', 'dock', '#1c3b2c',
        box(DOCK_X - 26, DOCK_X - 24.4, -25, 25, 6, 28))
    for sg in (1, -1):
        add(f'dock_spring_{"l" if sg > 0 else "r"}', 'Dock spring contacts', 'Gold-plated leaf springs with 4 mm of travel: tolerant of a few mm docking error.', 'dock', '#d4a64a',
            box(DOCK_X + 6, DOCK_X + 8.5, sg * 8 - 4, sg * 8 + 4, 18.5, 24.5), label=(sg > 0))
    add('beacon', 'IR beacon LEDs', 'Two 940 nm LEDs behind the window broadcast the dock code the robot homes on.', 'dock', '#5a1f70',
        cyl(2.5, 4, (DOCK_X - 10, 0, 36), (1, 0, 0)))
    return E
