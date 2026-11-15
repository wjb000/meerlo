# Meerlo: the pet that pet-sits

**Live 3D viewer:** https://wjb000.github.io/meerlo/ (every component, layer toggles, labels, X-ray, exploded view, standard views, click any part for details, and a periscope lift slider).

Meerlo is a small autonomous home robot, about 17 x 15 cm and 19 cm tall, that does two things:

1. **It's a pet.** It has one big expressive eye, ears that hear its name, a glowing belly band and a meerkat "stand up" when something interesting happens.
2. **It does a job people already pay for: pet-and-home sitting.** It patrols on a schedule, checks on the dog or cat in whatever room they're in, tosses them treats, hears barking, glass breaking or the smoke alarm, and sends you short clips. Then it docks and charges itself.

Target retail is **$149**. The volume BOM is about **$44** landed at 10k units/yr; the prototype BOM is about **$184** in hobby parts. See [BOM.md](BOM.md).

## What's new about it
- **Periscope head.** One N20 motor and a molded rack lift the head 80 mm, so the camera rides at 16 cm while roaming and 21 cm in "sentinel" mode, looking over cushions, toys and pet beds. When fully lowered, the molded brow covers the lens, which gives a physical privacy shutter at zero part cost.
- **Treat toss on wheels.** A lift-out, dishwasher-safe 180 ml cup feeds a two-pocket rotor. Each servo half-turn drops exactly one treat down a chute and out of the chin.
- **No lidar, no Linux.** One ESP32-S3 module handles the motors, a time-of-flight ranger, cliff sensors, the IMU, wheel encoders, IR dock homing, the camera stream and small on-device detectors (pet, person, sound events). The phone app and an optional cloud plan handle clip history and smarter search.

## Repo layout
| Path | What |
|---|---|
| `cad/meerlo.py` | Parametric CadQuery model of all 12 molded parts (assembly position) |
| `cad/elec.py` | Bought components modelled from datasheet dimensions and placed inside |
| `cad/export.py` | Builds STEP, ASCII STL, interference + mass reports and the viewer glTF |
| `cad/bom.py` | Single source for both BOMs; writes `BOM.md` and `site/assets/bom.json` |
| `cad/step/`, `cad/stl/` | Per-part STEP (molding / CNC / printing) and ASCII STL |
| `cad/reports/` | `interference.json` (0 static clashes, 0 clashes over the mast's full travel) and `mass_properties.json` |
| `docs/PRODUCTION.md` | DFM notes, tooling plan, assembly steps, test plan, prototype print guide |
| `site/` | GitHub Pages viewer (three.js), deployed by `.github/workflows/pages.yml` |

## Build the CAD
```bash
pip install cadquery trimesh manifold3d fast-simplification
python cad/export.py      # ~30 s: STEP, STL, reports, site/assets/meerlo.gltf
python cad/bom.py         # BOM.md + site/assets/bom.json
cd site && python -m http.server   # open http://localhost:8000
```

## Key numbers (from the CAD)
| | |
|---|---|
| Size | 173 x 145 mm, 192 mm tall asleep, 272 mm in sentinel |
| Mass | ~507 g estimated (shell volumes x resin density + datasheet masses) |
| Parts | 12 molded parts from 11 tools; 4 actuators (2 drive motors, lift motor, treat servo); 1 main PCB |
| Wheels | 68 mm with TPU tyres, climbs ~12 mm thresholds and rug edges |
| Battery | one 18650, ~10.8 Wh |
| Stability | centre of mass 5.6 mm ahead of the axle (8-11 % on the front caster) plus a molded rear anti-tip skid |

## Status: honest gaps
This is a design model for review. **Nothing has been built, printed or tested yet.** Bought parts are dimensionally modelled from datasheets, not vendor STEP files. The main PCB, firmware, app and the volume-price estimates (marked "est" in BOM.md) still need to be done or quoted.
