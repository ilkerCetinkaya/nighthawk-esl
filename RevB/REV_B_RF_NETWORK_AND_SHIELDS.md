# REV B: replacement CC1352R RF network and shield frame/cover parts

Date: 2026-11-08. Replaces the Murata LFB182G45BG5D920 (LCSC C90492) proposal, which the user did not approve (reported out of stock at LCSC, EOL notice at Mouser). Note for the record: on 2026-11-07 I read LCSC stock 1,205 and on 2026-11-08 Murata's product page showed "In Production". The user's decision stands and the part is not used.

Labels: [DS] datasheet, [CALC] arithmetic, [INF] inferred, [U] unverified, [MEAS] measured (none exists).

## 1. CC1352R RF network

### 1.1 What TI's own documents prescribe
- TI's official CC1352R designs (CC1352REM-XD7793-XD24, LAUNCHXL-CC1352R1) could not be downloaded: the design-file archive sits behind a myTI login, which I do not use. The values of the discrete network are therefore **not** copied from them.
- SWRA629A (TI application note on integrated passive components, IPC) lists the integrated balun/filter parts TI qualified for CC1352R/P: **Johanson 0900PC15A0036** and **Murata LFB21868MDZ5E757** [DS].
- SWRA640H: stay close to the reference design; a custom balun needs EM simulation and retuning [DS]. That is why a discrete network built from guessed values is rejected.

### 1.2 Selected solution
| Item | Part | Status |
|---|---|---|
| Dual-band balun/filter (IPC) | **Johanson 0900PC15A0036001E** (TI-listed IPC for CC1352R/P) | selected |
| DC-block capacitors C41, C51 | 100 pF, 0402 C0G/NP0, one per band, per SWRA629A circuit | selected, values from the application-note circuit [DS]; verify at schematic |
| Bias | external bias on both bands for this IPC (SWRA629A) | firmware/hardware rule: set `biasMode` external in CMD_RADIO_SETUP |
| Second source | Murata LFB21868MDZ5E757 | different bias (external sub-GHz, internal 2.4 GHz); needs a different radio-setup configuration, so it is a re-spin, not a drop-in |

Replaces a 23-component discrete front end with the IPC plus two capacitors and the bias network.

### 1.3 Availability and cost evidence
- DigiKey: Active, 25,968 in stock, about CHF 0.73 each (read 2026-11-08).
- LCSC / JLCPCB: **0 in stock** (C17328223, C3305216). Not usable for JLC economic assembly today.
- Risk: the part is not stocked at JLCPCB. Options: (a) wait for LCSC restock, (b) ask JLCPCB about consigned/global-sourcing parts [U, acceptance unconfirmed], (c) hand-place the IPC from DigiKey stock. Decision needed from the user (section 4).
- Lifecycle: Active at DigiKey; no EOL notice seen. Datasheet: Johanson 0900PC15A0036 (saved as jti0900.pdf in the research folder).

### 1.4 Open points
- The exact pin-to-pin mapping to CC1352R RF_P/RF_N (2.4 GHz) and sub-GHz pins and the bias network values must be taken from the Johanson datasheet and SWRA629A page 5 when the schematic is drawn; I did not transcribe them here from memory.
- Sub-GHz output: still no verified sub-GHz target; chip antenna stays DNP, U.FL kept as a conducted test port.
- The IPC land pattern and keepout need the 4-layer stackup check (JLC04161H-7628) at layout.

## 2. Shield frame and cover parts

| Use | Frame | Cover | Footprint (land pattern) | Heights | Source / status |
|---|---|---|---|---|---|
| RF SoC (20 × 20) | Würth **36103205S** (approved) | Würth **36003200S** | 21.5 × 21.5 mm [DS] | assembled about 3.2 mm [INF]; DigiKey lists 3.0 mm; **discrepancy, confirm before enclosure/height budget** | frame/cover pair read from Würth datasheets via pdf.js; assembled height is the open item |
| smaller sections | Laird **BMI-S-201-F** (approved) | Laird **BMI-S-201-C** | see 2.1 | frame 2.54 ±0.10; cover 2.00; assembled **2.67** mm [DS] | datasheet BMI-S-201-SALES parsed 2026-11-08 |
| alternate (not selected) | Würth 36103166S | Würth 36003160S | 17.3 × 17.3 mm; frame height 3.6 mm | | for reference |
| alternate (not selected) | Würth 3610213126S | Würth 3600213120S | inner 13.26 mm | | for reference |

Prices of covers and LCSC availability of these shield parts were not verified [U].

### 2.1 Laird BMI-S-201 details [DS, BMI-S-201-SALES drawing]
- Outline 13.66 ±0.10 × 12.70 ±0.10 mm; fence thickness 0.20 mm cold-rolled steel, cover 0.13 mm, tin plated.
- Packaging: fence on 330 mm reel, 24 mm tape, 20 mm pitch, 1000 pcs; cover bulk pack. Frame and cover are sold separately.
- Fence height 2.54 ±0.10; cover height 2.00; assembled height 2.67.
- Footprint (pad drawing): corner L-pads and edge bars; dimension callouts 3.13, 3.80, 2.20, 2.65, 3.80, 2.20, 1.00 mm. The pad drawing is a diagram; the land-pattern coordinates need to be redrawn at the 2.00 scale when the KiCad footprint is made, and the drawing checked against the 13.66 × 12.70 mm outline [U until footprint is drawn].
- Via fence: not given on the datasheet. Rule used: pitch of 1–2 mm around the can, to be checked in layout [A].

## 3. Consequences for the placement
- The RF SoC zone in `integrated/layout.py` is 17.5 × 12 mm; a 20 × 20 can needs a 21.5 × 21.5 land pattern. The RF zone must be redrawn before the schematic/board starts.
- The NFC section also needs a decision: a 20 × 20 can is large; BMI-S-201 (13.66 × 12.70) is smaller than the NFC IC block (13 × 16.5 mm), so the NFC IC needs a larger can or a layout change.
- The buck-boost can (if used) fits the BMI-S-201 size.

## 4. AO3400A verification summary (IR LED driver)
- The CC1352R pad delivers about 8 mA [DS]. The gate charge then takes about 310 ns of a 400 ns half-period at 1.25 MHz [CALC], so a direct drive is too slow.
- Recommendation: a gate buffer (the spare SN74LVC1G08 gate, about ±24 mA) with a series gate resistor.
- MOSFET self-heating about 1 K at the pulsed LED current [CALC]. LED pulsed current limits: VSMB10940 IFM 130 mA, PV 104 mW, RthJA 450 K/W [DS].
- Not measured.

## 5. Decisions needed from the user
1. IPC procurement route for Johanson 0900PC15A0036001E (wait for LCSC stock, consigned part, or hand placement).
2. Approval to enlarge the RF and NFC shield zones (20 × 20 can for the RF SoC; larger can for the NFC IC).
3. Approval to start the KiCad schematic (not started).
