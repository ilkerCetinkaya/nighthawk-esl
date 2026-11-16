# REV B schematic (draft 1): status, ERC and open issues

Date: 2026-11-08. Location: `RevB/schematic/` (KiCad 10.0.6, project `NIGHTHAWK_REVB.kicad_pro`, root `NIGHTHAWK_REVB.kicad_sch`, 7 sheets, PDF `NIGHTHAWK_REVB_schematic.pdf`). Source of truth: `design_b.py` (parts and nets), `symbols_b.py` (custom symbols), `gen_sch_b.py` (writer), `gen_footprints_b.py` (custom footprints), `bom_b.py`, `audit_b.py`. REV A untouched. Not production-ready: no PCB, no routing, no DRC, no measurement.

## 1. What exists
- 241 parts, 174 nets. Sheets: 01 MCU+flash, 02 USB-C/charger/buck-boost/LDOs, 03 CC1352R + IPC + antennas + shield, 04 TRF7970A + matching + coil + shield, 05 IR LED driver and photodiode TIA/comparator, 06 hardware interlock, 07 expanders/UI/debug.
- Custom symbols from datasheet pin tables: CC1352R1F3RGZ (49 pins), TRF7970ARHB (33), TPS63802DLA, Johanson IPC, AND gate, load switch, shield. Custom footprints in `NH_REVB.pretty`: TPS63802 (from TI DLA0010A land pattern), IPC, 868 MHz chip antenna, VSMB10940/VEMD10940F (Vishay pad drawing), and three placeholders (IFA feed, NFC coil feed).

## 2. ERC (kicad-cli, all severities)
0 errors, 1 warning: `lib_symbol_mismatch` for AO3400A (stock library copy differs from the embedded flattened copy; no electrical effect). Footprint-library warnings resolved after `NH_REVB.pretty` was created. Report: `ERC_REPORT.rpt`, `erc_raw.json`.
ERC passing does not prove the design: all connections are global labels, so ERC cannot see a wrong net name. A netlist audit was done by hand for U1 (partly), U3, U4, U7, U8, U9, U10-U14, U17-U20 against datasheet pin tables (`audit_b.py <ref>`); the rest (TCA9555 map, USB-C, passives) was not line-audited.

## 3. Verified against official documents
| Item | Result |
|---|---|
| IPC Johanson 0900PC15A0036001E pin map (datasheet p1) | pins 1 ANT 2.4, 4 ANT sub-GHz, 5 RX_TX, 6 RF_N sub, 7 RF_P sub, 8 RF_N 2.4, 9 RF_P 2.4, 2/3/10 GND; wired to CC1352R pins 1-5 accordingly |
| SWRA629A figure 3 (external bias both bands) | RX_TX net goes to CC1352R pin 5 with **C41 100 pF to GND**; **C51 100 pF is the series DC block on the sub-GHz port**. The 2.4 GHz port already has an internal 12 pF series cap. This corrects my earlier wording ("a DC block on each band") |
| Firmware consequence | CMD_RADIO_SETUP bias mode must be set to external for both bands (not done, no firmware yet) |
| CC1352R pin table (SWRS196I table 7-1) | all 48 pins + EGP in the symbol; unused DIOs marked no-connect (TI preferred practice) |
| 48 MHz crystal | HCI XC32M4-48.000-F08NLDT (LCSC C2925606): 8 pF, 40 ohm; datasheet needs CL 5-9 pF, ESR <= 60 ohm |
| 32.768 kHz crystal | Epson Q13FC13500002 (LCSC C48615): 7 pF, 70 kohm; datasheet needs CL 6-12 pF, ESR <= 100 kohm |
| Shield frame | Wuerth 36103205S land pattern from the KiCad library: pad bbox 21.5 x 21.5 mm, equals the datasheet value I read earlier |
| TPS63802 | pin map and 3.6 V divider (562k/91k) from datasheet table 10-5; 0.47 uH, 10 uF in, 22 uF out |
| BQ24074 | ILIM 3.09k = 1550/0.5 A, ISET 1.78k = 890/0.5 A, ITERM 2.94k, TMR 68k (about 9.1 h), from the datasheet formulas |

## 4. IR driver check (AO3400A), `integrated/ir_driver_calcs.py`
Peak LED current 96 mA (limit 130 mA), carrier-averaged 48 mA (limit 65 mA), LED power 66 mW (limit 104 mW). At 100 % burst duty the LED self-heats 30 K, so Tj 100 C is reached at 70 C ambient (continuous transmission is limited above that). Gate: driver 33 ohm + Rg 22 ohm gives a gate rise of about 106 ns versus a 400 ns half period; direct drive from a 8 mA CC1352R pin would need about 640 ns, so the gate buffer is kept. MOSFET loss about 15 mW, self-heating 1.9 K. The 20 ohm resistor dissipates 93 mW average, so it needs a 0.25 W 0805. All [CALC]/[A]; driver impedance, Vf spread and ringing are not measured.

## 5. Unresolved issues (honest list)
1. **Passives without LCSC numbers:** 67 parts on 38 BOM lines are generic values (0402 RF caps/inductors, 100k, 20R, 22u, etc.) with no chosen MPN (`BOM_REVB_schematic.csv`, source = OPEN). I did not guess numbers.
2. **TRF7970A matching values** are transcribed from TI figure 7-1 by reading the image; the RX_IN1/RX_IN2 capacitive dividers (1.2n/1.2n and 220p/680p) are my reading of the drawing. Verify against the TRF7970A EVM schematic. Coil tank (C23 68 pF, R6 680 ohm, C24 330 pF) is a starting point for an assumed 0.38 uH coil; needs VNA tuning. TRF7970A VIN is 3.6 V here (TI example uses 5 V), so TX power will be lower.
3. **IPC land pattern** is assumed from terminal dimensions; replace with Johanson reference CAD (GND vias beside the part are mandatory per their datasheet).
4. **CC1352R passives** (10 uH DC/DC inductor, 1 uF DCOUPL, 100 nF decoupling count, 12 pF optional crystal caps) are not from the TI reference design (not obtainable without login). Compare with the CC1352R reference design before layout.
5. **Bootloader/backdoor pin:** DIO_15 assumed for CC_BSL; the CCFG setting is not defined [U].
6. **IR receive path** (OPA356 TIA, AC coupling, TLV3501 comparator, VREF 1.97 V) is my design, not verified by simulation. TLV3501 is not on LCSC (DigiKey). Photodiode polarity (pad mapping) must be confirmed on the part marking [U].
7. **Buck-boost inductor:** footprint is a placeholder 0805; the reference XFL4015-471MEC costs US$4.27 at LCSC. A cheaper 0.47 uH, >= 4 A, 4x4 mm part must be selected and its footprint set.
8. **Battery:** user-supplied pack; no NTC (TS fixed 10k), no protection circuit on board. Pack must have its own protection.
9. **USB-C data lines / ESP32 IO** assignments are mine; strap pins IO2/IO8/IO9 have pull-ups, IO2 is also the watchdog output.
10. **Unused TCA9555 pins** left unconnected: firmware must set them as outputs.
11. **Laird BMI-S-201 stock footprint** (pad bbox 13.5 x 14.5 mm) was not cross-checked with the datasheet drawing; it is not used in this schematic.
12. **Layout consequences:** two 20x20 shield frames (21.5 mm land) mean the block placement in `integrated/layout.py` must be redone before the PCB; the NFC coil must remain outside the can. Antenna/IFA geometry, NFC coil traces, and four-layer keepouts are PCB-phase work, not done.
13. The ERC "global label appears once" check is off by default; single-pin nets were reviewed and are all intended no-connects.

## 6. JLCPCB consigned parts (investigation)
JLCPCB accepts consigned and global-sourcing parts. Key terms from its help pages: only parts with a JLC part number are accepted directly, otherwise engineer review; consigned parts are not tested; the standard separate-component fee is quoted as US$0.142 per piece; overseas consignment adds import VAT and a 2 % handling fee (minimum US$10); an agent fee of US$85 for 1-50 part numbers is quoted on one page and US$45/85 on another, so the current fee must be confirmed with JLCPCB. Sources: https://jlcpcb.com/help/article/consignment-part-terms-conditions , https://jlcpcb.com/help/article/how-to-use-jlcpcb-global-sourcing-parts-service . Plan for prototype 1 (user instruction): IPC, shield frames/covers, TLV3501 from DigiKey/Farnell, soldered by hand or consigned; standard passives from LCSC.
