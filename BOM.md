# Meerlo bill of materials

Prices checked 2026-11-14. Prototype = one robot built from hobby parts with printed shells. Volume = landed cost per robot at 10k units/year, molded parts and one custom PCB. Lines marked **est** are engineering estimates that need an RFQ; **quote** lines are distributor price breaks read that day.

## Prototype BOM: **$184.23** per robot

| Part | Qty | Unit | Line | Source | Note |
|---|---:|---:|---:|---|---|
| Seeed XIAO ESP32-S3 Sense (ESP32-S3 + camera + mic) | 1 | $19.99 | $19.99 | [link](https://www.seeedstudio.com/XIAO-ESP32S3-Sense-p-5639.html) | brain, camera and mic in one; sits in the head for the prototype |
| Waveshare 1.28" round LCD, GC9A01, 240x240 | 1 | $14.59 | $14.59 | [link](https://www.waveshare.com/1.28inch-lcd-module.htm) | price shown for 10+, single price similar |
| N20 gearmotor 6 V 1:50 with magnetic encoder (drive) | 2 | $12.50 | $25.00 | [link](https://www.adafruit.com/product/4638) |  |
| N20 gearmotor 6 V with encoder (mast lift, encoder unused) | 1 | $12.50 | $12.50 | [link](https://www.adafruit.com/product/4638) | same SKU keeps the proto simple |
| Micro servo TowerPro SG92R (treat rotor) | 1 | $5.95 | $5.95 | [link](https://www.adafruit.com/product/169) | out of stock at Adafruit today; any SG90 works |
| DRV8833 dual motor driver breakout | 2 | $5.95 | $11.90 | [link](https://www.adafruit.com/product/3297) |  |
| VL53L1X time-of-flight sensor breakout | 1 | $14.95 | $14.95 | [link](https://www.adafruit.com/product/3967) |  |
| Pololu QTR-1A reflectance sensor 2-pack (cliff, 3 used) | 2 | $5.65 | $11.30 | [link](https://www.pololu.com/product/2458) |  |
| LSM6DS3TR-C 6-DoF IMU breakout | 1 | $9.95 | $9.95 | [link](https://www.adafruit.com/product/4503) |  |
| Li-ion 18650 cell 2200 mAh, protected | 1 | $9.95 | $9.95 | [link](https://www.adafruit.com/product/1781) | out of stock at Adafruit today |
| Micro-Lipo charger, USB-C | 1 | $5.95 | $5.95 | [link](https://www.adafruit.com/product/4410) |  |
| MAX98357A I2S 3 W amplifier | 1 | $5.95 | $5.95 | [link](https://www.adafruit.com/product/3006) | out of stock at Adafruit today |
| Mini oval speaker 8 ohm 1 W | 1 | $1.95 | $1.95 | [link](https://www.adafruit.com/product/3923) |  |
| NeoPixel Stick, 8 RGB LEDs | 1 | $5.95 | $5.95 | [link](https://www.adafruit.com/product/1426) | proto uses 8 LEDs, production 12 |
| Pololu ball caster, 1/2" metal ball | 1 | $2.95 | $2.95 | [link](https://www.pololu.com/product/953) |  |
| Magnetic pogo connector, 3 contacts (dock) | 1 | $5.95 | $5.95 | [link](https://www.adafruit.com/product/5358) | stands in for leaf-spring contacts |
| IR receiver TSOP38238 (dock homing) | 1 | $1.95 | $1.95 | [link](https://www.adafruit.com/product/157) |  |
| PETG filament ~380 g + TPU ~40 g (all printed parts) | 1 | $9.50 | $9.50 | [link](https://www.prusa3d.com/category/filament/) | at ~$20-25/kg |
| Screws, wire, perfboard, IR LEDs, contacts (allowance) | 1 | $8.00 | $8.00 | - | estimate |

## Volume BOM (10k units/yr, landed in US): **$44.38** per robot

| Part | Unit | Basis | Source |
|---|---:|---|---|
| ESP32-S3-WROOM-1-N8R8 module (FCC/CE pre-certified) | $3.48 | quote | [LCSC](https://www.lcsc.com/product-image/C2913201.html) |
| OV3660 3 MP 120 deg camera, long 24-pin FPC | $3.20 | est | - |
| 1.28" GC9A01 round IPS panel (bare, FPC) | $2.10 | est | - |
| VL53L1CX ToF sensor (bare) | $3.20 | quote | [LCSC](https://www.lcsc.com/product-image/C190004.html) |
| N20 gearmotor + hall encoder x2 (drive) | $3.40 | est | - |
| N20 gearmotor 1:150 (mast lift) | $0.95 | est | - |
| 9 g micro servo (treat rotor) | $0.95 | est | - |
| DRV8833 x2 motor drivers | $0.70 | est | - |
| 6-axis IMU (QMI8658-class) | $0.55 | est | - |
| I2S MEMS microphones x2 | $0.70 | est | - |
| MAX98357A amp + 2030 speaker | $0.90 | est | - |
| WS2812B-2020 x12 on flex ring | $0.55 | est | - |
| Cliff ITR8307 x3, IR LEDs x2, IR receiver | $0.45 | est | - |
| 18650 3000 mAh protected cell (UL 2054 / UN38.3) | $2.20 | est | - |
| Charger + protector + NTC | $0.25 | est | - |
| Main PCB 4-layer 70x40 + SMT + passives + connectors | $4.20 | est | - |
| Molded parts: 11 tools, ~215 g resin, 2-shot TPU tyres | $4.60 | est | - |
| Caster ball, pinion, springs, 8 screws, contacts | $1.10 | est | - |
| Dock: shell + steel weight, PCB, USB-C, springs, IR LEDs | $2.40 | est | - |
| USB-C 5 V/2 A adapter + cable | $1.70 | est | - |
| Packaging + quick-start card | $1.40 | est | - |
| Final assembly + test (~11 min) + 3% yield loss | $1.80 | est | - |
| Compliance amortisation (FCC SDoC, UL/IEC 62368, battery) | $0.50 | est | - |
| Freight + duty to a US warehouse | $3.10 | est | - |

## One-off costs (not in the per-robot figure)

- Injection-mold tooling, 11 tools (P20 steel, family tools where possible): about $55k-75k; aluminum bridge tools for the first ~5k units: about $20k-28k (estimate).
- Certification: FCC part 15B SDoC (radio is the pre-certified ESP32-S3 module), IEC 62368-1 + UL 2054 battery, UN38.3 shipping: about $15k-25k (estimate).
- Test fixtures (bed-of-nails for the main PCB + end-of-line robot test jig): about $6k (estimate).
