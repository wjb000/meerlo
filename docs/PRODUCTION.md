# Meerlo production notes

## Part list (molded)
| # | Part | Material | Tool notes |
|---|---|---|---|
| 1 | Chassis tub | ABS/PC, warm taupe | 2-plate, 2 lifters (axle bores, ToF + dock windows). Motor saddles, battery cradle, mast tower, servo ribs, chute and skid are molded in. |
| 2 | Light band | Clear PC, frosted (VDI 27) | Simple ring; also the split-line seal |
| 3 | Top shell | ABS/PC, sand | 1 slider (rear grille). Head nest, collar/brow and cup pocket are molded in. |
| 4 | Treat cup | PP, food-contact | Straight-pull, dishwasher safe |
| 5 | Cup lid | PC, smoke tint | Family tool with #4 |
| 6 | Treat rotor | POM | Family tool with #7 |
| 7 | Periscope mast | POM (or PA12-GF) | Rack molded in; hollow cable channel; core pull |
| 8 | Head shell | ABS/PC, sand | Ears/mic ports, mast socket |
| 9 | Face plate | ABS/PC, espresso high gloss | Eye window, bezel, camera aperture |
| 10/11 | Wheel L/R | ABS hub + TPU 85A tyre | 2-shot, mirrored cavities in one tool |
| 12 | Dock | ABS + stamped steel weight plate | Open-bottom shell |

Rules used in the CAD: 2.2 mm nominal wall, a single horizontal split line hidden by the light band, no undercuts on the shells except the listed lifters/slider, snap fits instead of screws wherever the part isn't load-bearing, and 8 screws total.

Tooling estimate: P20 steel family tools about $55k-75k; aluminum bridge tooling for the first ~5k units about $20k-28k.

## Electronics (one PCB)
ESP32-S3-WROOM-1 (pre-certified radio), 2x DRV8833, a 6-axis IMU, a Li-ion linear charger with DW01 protection and an NTC, a MAX98357A amp, a WS2812 driver line, an I2S mic header, FPC connectors for the camera and eye, and JST-SH connectors for the sensors. It's 4 layers, 70 x 40 mm, with SMT on one side. The camera FPC and eye cable run down the hollow mast with a 90 mm rolling service loop, which should be life-tested to 50k lift cycles.

## Assembly (8 steps, 8 screws, target about 11 minutes)
1. Drive motors into the saddles; wheels onto the D-shafts with M2.5 screws (2).
2. Press in the caster, battery contacts and charging pads; snap in the 18650.
3. Servo on its ribs (2 screws); lift motor and pinion (2 screws).
4. Slide the mast into the tower; plug the head flex cables into the board.
5. Snap the main board into its slot; plug in the ToF, cliff sensors, IR receiver, speaker and LED ring.
6. Lay the light band on the tub, lower the top shell over the mast, and fit 2 screws (under the cup).
7. Snap the face plate and head shell onto the mast socket.
8. Fit the rotor, cup and lid. End-of-line test: drive, lift homing, one treat drop, camera frame, mic level, LEDs, dock charge current.

## Firmware plan (not written yet)
- Real-time loop on core 0: wheel PID from the encoders, cliff and bump stop, IMU tilt and pick-up detection, lift homing by stall current.
- Core 1: camera to the Wi-Fi stream, ESP-DL person and pet detector at low fps, audio event classifier (bark, glass, smoke alarm), and the behaviour tree (patrol, approach pet, treat, play-flee, follow, dock).
- Navigation without lidar: ToF wall-following plus odometry, with room "waypoints" taught from the app by driving once. Dock homing uses the 38 kHz beacon.

## Prototype print guide
- PETG for the shells, cup, mast and rotor (rack at 0.12 mm layers); TPU 95A for the tyres. Everything fits a 250 mm bed.
- The top shell prints upside down (collar on the bed) with tree supports in the cup pocket; the chassis prints upright.
- Add 0.3-0.6 mm clearance on the snap fits and the mast-to-tower fit for FDM.
- The prototype uses a XIAO ESP32-S3 Sense (camera and mic on board) in the head plus breakout boards. See BOM.md.
