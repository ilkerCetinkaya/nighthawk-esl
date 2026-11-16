# REV B antenna engineering, revision R2 (placement not frozen, nothing validated)

Date: 2026-11-08. Supersedes `REV_B_ANTENNA_DESIGN_INTERIM.md`. No RF traces routed, no Gerbers, **not production-ready, no antenna validated**. Labels: [DS] document read, [CALC] calculation (scripts in `integrated/`), [A] assumption, [U] unknown, [MEAS] needs measurement (none done). PCB: `pcb/NIGHTHAWK_REVB.kicad_pcb`; drawings `pcb/drawings/` (`rf_zones_keepouts.png`, `antenna_geometry.png`, `blocks_top.png`, `blocks_bottom.png`); metrics `integrated/placement_r2_metrics.txt`.

## 0. Summary of the R2 arrangement (all fit in 80 x 50 mm; one item conflicts, see 3 and 4)
ESP32 top-left with the antenna over the cut-out; TI AN043 IFA in the top-right corner; Johanson 868 MHz antenna in the **bottom-right corner** (documented corner layout) with the RF shield above it; USB-C at the bottom edge (x 52.7-63.4), battery connector and cable notch bottom centre; NFC coil 18 x 16 mm in the top centre; **NFC shield removed**; one RF shield (21.5 mm) kept for CC1352R + IPC. 240 footprints placed, KiCad DRC: no courtyard, keepout or edge errors; only the IPC pad spacing (0.17 mm, assumed land pattern) and false positives from the antenna footprints' own unnetted copper artwork (IFA polygons, coil lines).
**Conflict reported, not violated:** TI's 10 mm coil-to-metal and coil-to-ground-plane guidance cannot be fully met on this board (ground plane lateral spacing, J5 header 7.8 mm, ESP32 module 9.8 mm); the documented Johanson corner zone is met, but nearby metal (RF shield 4.2 mm, USB shell 6.6 mm, U.FL 1.3 mm) is outside anything the manufacturer tested.

## 1. ESP32-C3-WROOM-02 (Espressif datasheet v1.7 fig. 11-1; Hardware Design Guidelines, PCB layout)
- Antenna area 18 x 6 mm at the module end; first pad row 7.1 mm from the tip [DS]. Base board cut away at the antenna base line on both sides of the antenna, 15 mm minimum clear to the left, right and outward; module on the board edge with the feed point near the edge; dense ground vias next to the antenna; 15 mm clear in all directions inside the housing; validate by test [DS].
- **Corrected geometry:** tip at x = 0, antenna base line at x = 6.0, cut-out x 0-6.0, y 15.5-50 (the module side is at y 30.1, so 14.6-15 mm below it; the previous 17 mm gave 13 mm). Module origin (13.15, 39.6), rotated 90 degrees. No copper on any layer inside the cut-out (it is air); the footprint's own keepout is retained.
- Not verifiable here: the 15 mm of free space beyond the board's top edge and in front of the tip is an enclosure requirement.
- Measured/DRC: pad 1 copper is 0.4 mm from the cut-out edge (limit 0.3).

## 2. CC1352R 2.4 GHz IFA (TI AN043 / SWRA117D, https://www.ti.com/lit/an/swra117d/swra117d.pdf)
- Geometry: 15.2 x 5.7 mm; L1 3.94, L2 2.70, L3 5.00, L4 2.64, L5 2.00, L6 4.90, W1 0.90, W2 0.50, D1 0.50, D2 0.30, D3 0.30, D4 0.50, D5 1.40, D6 1.70 mm. Reconstruction (figure 3 + table 1) checked by sums: 0.9+1.4+0.5+1.7+0.5 = 5.0 (L3), 0.5+14.4+0.3 = 15.2, 0.3+0.5+4.9 = 5.7. Footprint `IFA_AN043_15.2x5.7` (radiator as copper polygons, pad 1 feed, pad 2 ground via). TI: "make an exact copy; compensate PCB thickness by antenna length"; the TI Gerber/DXF (IFA_USB) was not obtained [U].
- Placement: box x 64.8-80, y 44.3-50 (top-right corner), feed pad at (67.85, 44.55). Rule areas: all of L2, L3, B.Cu copper-free from y = 44.8 (layer-2 ground edge 0.5 mm above the stub feet as in AN043 fig. 3), F.Cu tracks/vias/pours disallowed in the whole box.
- **Stackup differences [DS/U]:** AN043: antenna on L1 with a single "Ground Layer 2"; PCB material and thickness are in a readme that was not obtained [U]. TI's other IFA note (SWRU120D, +3.3 dBi, 25.7 x 7.5 mm) used 1 mm FR-4 and recommends a pi network. Ours: JLC04161H-7628, finished 1.59 mm, 7628 prepreg eps_r 4.4, core 4.6, 1.2 mil solder mask eps_r 3.8 over the antenna copper (black mask, HASL with lead on the radiator) [DS jlcpcb.com/impedance]. Expect: resonance shifted (mask loading lowers it, thicker board shifts it; TI says plastic encapsulation lowers the resonance and thicker PCBs need a shorter antenna), bandwidth changed; none quantified [U]. The antenna copper is HASL (rough, tin-lead) rather than the reference's finish [U].
- Matching: pi network footprints at the feed (all 0402): C36 1 pF shunt (DNP), series L3 1 nH (DNP) / R28 0 ohm (fitted), C84 1 pF shunt at the antenna side (DNP, added this stage); plus R26 0 ohm (IPC to feed, fitted) and R27 0 ohm (IPC to U.FL J3, DNP). U.FL J3 at (68, 40.5), 1.2 mm below the IFA box: it is a conducted access, outside the radiator.
- Isolation from other items [CALC from placement]: IFA box to ESP32 antenna 58.8 mm; to NFC coil 16.7 mm; to RF shield 7.5 mm; to the 868 MHz zone 33.3 mm.

### VNA tuning procedure (IFA), [MEAS] required
1. Remove R26, fit R27 (0 ohm) so the U.FL J3 connects to the IFA feed through the pi pads; fit a 0 ohm series (R28) and leave the shunts open. Calibrate (SOL) at the U.FL end with the cable fitted (TI: coax placement shifts resonance by 5-10 MHz and return loss by 3-4 dB).
2. Measure S11 from 2.3 to 2.6 GHz on the bare board, then again with the battery, enclosure and shield cover fitted (TI: plastic shifts resonance down).
3. Target return loss <= -10 dB over 2400-2483.5 MHz (VSWR < 2, the AN043 criterion).
4. If the resonance is low/high or the centre impedance is off, read the Smith chart and add shunt C (C36/C84) or series L (L3) in 0.1-0.5 pF / 0.5 nH steps. If the resonance cannot be recovered with the pi network, lengthen/shorten the final antenna leg on a spare board and repeat (the amount is not given by TI [U]).
5. Then measure efficiency and pattern in a chamber (not possible in-house).

## 3. 868 MHz chip antenna (Johanson 0868AT43A0020 v1.8, https://www.johansontechnology.com/ ; datasheet pages 2-3)
- Documented layouts: (a) test board 40 x 20 mm with a 9.5 mm full-width no-ground end; (b) corner placement on a 26 x 42 mm ground with a **10 x 11 mm (or 11 x 10 mm) zone, "complete GND and layer clearance free of metal below and above"**; 50 ohm feed; "leave slots for a pi network"; matching values given are valid only for their evaluation board. Chip 7 x 2 x 0.8 mm, copper meander 7.1 x 5.1, trace 0.5, legs 3.0 and 5.1 (drawing in `antenna_geometry.png`, shape taken from the datasheet figure; the manufacturer's CAD file was not obtained [U]). Edge placement is not a documented configuration.
- **Decision:** bottom-right corner, zone x 70-80, y 0-11 (10 x 11), rule area on all four copper layers (tracks, vias, fills); antenna footprint at the bottom edge, feed to the left. The RF shield could stay 21.5 mm because it moved to the right and above the corner (bottom edge y = 15.25, 4.2 mm from the zone). Shield reduction was therefore not needed for the corner; a 16.1 mm frame (Wuerth 36103166S, 17.3 mm land) exists but its footprint was not verified.
- **No alternative chip antenna was researched** (not needed once the Johanson corner zone fits); alternatives remain open.
- Matching footprints (pi): C37 3.9 pF shunt, L4 18 nH series, C38 0.3 pF shunt, R29/R31 0 ohm links, all DNP with the antenna (values are Johanson's board values); C35 100 pF series DC block (IPC, fitted); U.FL J4 via R30.
- Concerns [U]: RF shield 4.2 mm, USB shell 6.6 mm, U.FL J4 1.3 mm from the zone; the manufacturer tested corners of a bare ground board without such metal.
- Distance to the other antennas: IFA 33.3 mm, ESP32 antenna 64.2 mm, NFC coil 31.0 mm.
VNA procedure: same as 2, band 858-878 MHz, target -10 dB (Johanson reference: -14.5 dB at 858/878 MHz, -23 dB at 868 MHz), starting values 18 nH / 3.9 pF / 0.3 pF; Johanson offers a tuning service from the measured S-parameters.

## 4. NFC coil and matching (TI SLOA241C, https://www.ti.com/lit/an/sloa241/sloa241.pdf)
- Evidence [DS]: target coil inductance 1-1.5 uH; Q 7-10 for ISO 14443A/B and FeliCa; coil gap <= 0.1 mm; metal near the coil damps and detunes it; **TI recommends 10 mm** to metal (stacked or side by side) and about 10 mm to the ground plane; a ferrite sheet if metal cannot be avoided; tune in the final enclosure; 1 % parts; two pads for Cs and Cp; U.FL pads between the 50 ohm point and the coil network with a 0 ohm isolation resistor; coil measurement 12-15 MHz on a network analyzer.
- Previous coil (28 x 16 mm, 3 turns) recalculated with SLOA241C eq. 2: 0.54 uH, not the 0.38 uH estimate, and in any case below 1 uH. It is **retired**.
- **New coil:** outer 18 x 16 mm, 6 turns, trace 0.25 mm, gap 0.10 mm (JLCPCB minimum 3.5 mil = 0.089 mm), F.Cu spiral with a B.Cu underpass; **L = 1.43 uH [CALC]**, series R about 0.92 ohm (DC x 1.3), unloaded Q about 133. Alternatives computed: two-layer 3+3 turns 1.56 uH; 20 x 16 mm 0.3/0.15 mm 1.40 uH (`integrated/nfc_coil_design_output.txt`). Footprint `NFC_COIL_18x16_6T`.
- **Verified against the TRF7970A circuit:** the TI Figure 7-1 50 ohm network is unchanged; the tank is calculated with the SLOA241C three-element method (Rp = X x Q): my solver reproduces the TI example (1.35 uH, Cp 47, Rp 700, Cs 68 pF) as Cp 40.5 / Cs 66.5 pF at Rp 700. For 1.43 uH and Q 7: Rp 854 ohm, Cp 39.7 pF, Cs 60.1 pF, -10 dB return-loss bandwidth 1.4 MHz. Fitted: Cs = 47 pF (C61) + 12 pF (C62) = 59 pF; Cp = 39 pF (C63) + 2.2 pF trim (C64, DNP); Rp = 845 ohm (R42, 1206 for up to about 100 mW); R39 0 ohm isolation; U.FL J8 (DNP) at NFC_ANT. The old values (68 pF, 330 pF, 680 ohm) are retired. **L must be measured** (the equation is an estimate) and the values redone. Coil voltage about 12 V peak, current about 0.1 A [CALC].
- **Shield can effect and clearance:** evidence only from TI's generic statement (metal damps and detunes, 10 mm recommended); no number for a 3 mm tall shield can beside a coil was found [U]. Achieved clearances (rectangle edge to edge): ESP32 module 9.8 mm, RF shield 10.0 mm, USB shell 24.8 mm, battery connector 18.7 mm, 2.4 GHz IFA zone 16.7 mm, J5 JTAG header 7.8 mm. Ground plane: L2, L3 removed under the window, but the lateral ground plane/pours come closer than 10 mm; TI's "10 mm to ground plane" is not met [U].
- **Retain vs remove the NFC shield:** the 21.5 mm NFC can would sit about 2.5 mm from any usable coil position and was **removed**. The TRF7970A has no documented need for a shield at 13.56 MHz; its 2nd-order output filter handles harmonics; EMC pre-compliance of the unshielded stage is untested [U]. A small optional footprint around the IC only (outside the 10 mm radius) is not placed.
- Tuning procedure [MEAS]: (1) remove R39, connect the VNA at J8, calibrate; (2) measure the bare coil 12-15 MHz, extract L and R on the Smith chart; (3) recompute Rp = X x Q, Cp, Cs (script `integrated/nfc_coil_design.py`), populate, aim at a centre of 13.56 MHz and SWR bandwidth for Q 7-10 (2 dB points); (4) repeat with the RF shield cover fitted, the battery and the enclosure; (5) read range with real cards.

## 5. Shield cans: what needs shielding
| Circuit | Needs a can? | Decision |
|---|---|---|
| CC1352R + IPC + crystals | not needed for function (TI reference boards are open [A]); helpful against ESP32 near-field and crystal harmonics | keep **one** 21.5 mm can (Wuerth 36103205S frame + 36003200S cover), located 4.2 mm from the 868 MHz zone, 7.5 mm from the IFA box, 10 mm from the coil; test with and without the cover [MEAS] |
| TRF7970A + matching | no documented need; shield conflicts with the 10 mm coil rule | **removed** |
| ESP32 module | own can | none |
| IR TIA / comparator | sensitive, but no documented requirement | no can |
| Switching regulator | not a radio circuit; distance used instead (10 mm rule) | no can; regulator parts 38 mm from the RF can, 16.9 mm from the NFC area, 24.2 mm from the IR parts |
A smaller 16.1 mm can (36103166S, land 17.3 mm) would give 2.2 mm more room around the 868 MHz zone, but its footprint was not verified.

## 6. 50 ohm feed geometry on JLC04161H-7628 (JLCPCB impedance calculator, run 2026-11-08, https://jlcpcb.com/pcb-impedance-calculator)
Inputs: rigid, 4 layers, 1.6 mm class, outer 1 oz, inner 0.5 oz, mil units, 50 ohm single-ended non-coplanar, signal L1, reference L2, stack-up **JLC04161H-7628 (finished 1.59 mm +-10 %)**: **trace width 14.12 mil = 0.359 mm** with 7628 prepreg 0.2104 mm (eps_r 4.4), core 1.065 mm, 1.38 mil outer copper, mask 1.2 mil (eps_r 3.8). This agrees with my 2D solver (0.36 mm, 50.3 ohm). The default first stack-up (JLC04161H-3313A) gives 13.57 mil, which is not our stackup. A coplanar-with-ground variant was not calculated; the 7628 stack-up's tolerance (+-10 % per JLCPCB's guide) should be stated on the order. Both feed lines (IFA, 868 MHz) use 0.359 mm over an unbroken L2 ground; the U.FL footprint pads and the IPC pads need their own width transitions (not routed).

## 7. Coexistence: ESP32-C3 (2.4 GHz) with CC1352R
Data [DS]: ESP32 TX up to 20.5 dBm (802.11b), RX sensitivity -98 dBm (1 Mbps); CC1352R 2.4 GHz TX up to +5 dBm, absolute-maximum 2.4 GHz RF input +5 dBm, sensitivity -97 dBm (BLE), IPC attenuation >= 40 dB at 2604-2784 MHz on the sub-GHz path; CC1352R sub-GHz harmonics: 2nd/3rd/4th <= -30 dBm (868 MHz, +14 dBm), IPC 3rd harmonic -33 dBm measured, at the 2.4 GHz port [SWRA629A].
- **Antenna-to-antenna coupling:** edge separation ESP32 antenna to IFA 58.8 mm. Free-space path loss at 2.44 GHz over 58.8 mm is 15.6 dB [CALC]; real coupling between PCB antennas on one board is typically 15-30 dB [A, no source].
- **Receiver desensitization:** ESP32 TX 20.5 dBm gives +4.9 to -9.5 dBm (S21 -15.6 to -30 dB, no IPC loss; superseded by the reconciled table in `REV_B_RF_DESIGN_GATE.md` 1.2) at the CC1352R antenna (against an absolute maximum of +5 dBm and a -97 dBm sensitivity): the CC1352R receiver is saturated or desensitized by 70-100 dB. CC1352R TX +5 dBm gives -10.6 to -25 dBm at the ESP32, 70-90 dB above its sensitivity. To tolerate a -30 dBm interferer [A] 50 dB (ESP to CC) and 35 dB (CC to ESP) would be needed: not achievable passively on this board.
- **Simultaneous versus time multiplexed:** **simultaneous operation in the same band is not possible; time multiplexing is required** (firmware arbitration with a handshake through spare TCA9555 pins or the UART; the hardware interlock already gates the CC1352R reset, TRF enable and IR). No RF switch fixes it: a switch cannot isolate two receivers that share a board; the only isolation lever is separation (already 58.8 mm) and orientation. Simultaneous ESP32 (2.4 GHz) with CC1352R sub-GHz is plausible by frequency separation but untested: the IPC rejection at 2.44 GHz on the sub-GHz path is not listed [U].
- **Harmonic/spurious paths:** (a) CC1352R 868 MHz 3rd harmonic at 2604 MHz: -33 dBm (IPC) against the -30 dBm limit; TI says a 2.4 GHz antenna connected directly to the IPC fails the ETSI limit at 2604 MHz and recommends an SPDT switch (SWRA629A): **open**; (b) crystal harmonics inside the 2.4 GHz band: 48 MHz x 50-52 = 2400/2448/2496 MHz, ESP32 40 MHz x 60-62 = 2400/2440/2480 MHz, TRF 27.12 MHz x 90 = 2440.8 MHz; (c) 13.56 MHz x 64 = 867.84 MHz and 27.12 MHz x 32 = 867.84 MHz land in the 868 MHz band (the TRF output filter should suppress them) [CALC]; (d) 2.4 GHz second harmonic of the ESP32 4.8-4.97 GHz is outside the CC1352R bands; (e) the 1.4-2.1 MHz buck-boost switching harmonics reach 868 MHz only as very weak spurs [A]. All need spectrum-analyzer measurement.
- **Required isolation/switching:** none beyond time multiplexing for the 2.4 GHz pair; for the 868 MHz path an SPDT/diplexer or further filtering is TI's recommendation for regulatory use and is **not in the design**.

## 8. Matching network BOM (all values start points, DNP where noted)
| Ref | Function | Value / part | LCSC | Status |
|---|---|---|---|---|
| R26 | IPC to IFA feed link | 0 ohm 0402 | C17168 | fitted |
| R27 | IPC to U.FL J3 | 0 ohm 0402 | C17168 | DNP |
| C36, C84 | IFA pi shunts | 1 pF C0G +-0.1 pF (Murata GJM1555C1H1R0BB01D) | C76898 | DNP |
| L3 | IFA series | 1 nH (Murata LQG15HS1N0S02D) | C18222 | DNP |
| R28 | IFA series link | 0 ohm 0402 | C17168 | fitted |
| C35 | 868 MHz DC block (IPC C51) | 100 pF C0G | C77177 | fitted |
| R29, R31 | 868 MHz links | 0 ohm | C17168 | R29 fitted, R31 DNP |
| R30 | to U.FL J4 | 0 ohm | C17168 | DNP |
| C37, L4, C38 | 868 MHz pi (Johanson values) | 3.9 pF, 18 nH, 0.3 pF | C76907, C7519796, C85885 | DNP |
| C61, C62 | NFC Cs | 47 pF + 12 pF C0G | C1567, C1547 | fitted |
| C63, C64 | NFC Cp | 39 pF (+ 2.2 pF trim) C0G | C86288, C1559 | C63 fitted, C64 DNP |
| R42 | NFC Rp | 845 ohm 1 % 1206 | C247179 | fitted |
| R39 | NFC isolation | 0 ohm | C17168 | fitted |
| J3, J4, J8 | U.FL (2.4 GHz, sub-GHz, NFC) | Hirose U.FL-R-SMT-1(01) | C598199 | DNP |
(TI recommends 0603 for NFC prototype tuning; 0402 is used for space [A].)

## 9. RF risk register
| # | Risk | Severity | Mitigation / action |
|---|---|---|---|
| 1 | IFA reference stackup unknown; our 1.59 mm board with HASL and black mask shifts resonance | high | pi network, VNA, spare boards for leg length trial [MEAS] |
| 2 | IFA copper HASL with lead (rough, uneven thickness) and mask over antenna | medium | consider mask opening or ENIG for the antenna later; measure |
| 3 | 868 MHz corner zone has nearby metal (RF shield 4.2 mm, USB 6.6 mm, U.FL 1.3 mm) not covered by Johanson's test | high | measure S11; move J4 and consider a 16.1 mm can [MEAS] |
| 4 | IPC 3rd harmonic at 2604 MHz -33 dBm vs -30 dBm (ETSI), no SPDT switch | high | spectrum-analyzer test; add switch for any regulatory use |
| 5 | ESP32 TX saturates the CC1352R 2.4 GHz receiver in the same band | high | strict time multiplexing in firmware |
| 6 | Crystal harmonics inside 2.4 GHz and 868 MHz bands (48/40/27.12 MHz) | medium | crystals inside/near the can, ground guard, spectrum test |
| 7 | NFC coil L is calculated, not measured; metal within 10 mm only partly avoided (ESP32 9.8 mm, J5 7.8 mm, lateral ground) | high | measure with J8, retune; test with cover |
| 8 | No shield-effect number for the NFC coil | medium | measure with and without the RF cover |
| 9 | ESP32 15 mm housing clearance depends on the enclosure | medium | enclosure design |
| 10 | IPC and shield footprints from datasheet/library; IPC land pattern assumed | medium | Johanson CAD |
| 11 | JLCPCB 50 ohm +-10 %, microstrip width 0.359 mm to be ordered as controlled impedance or accepted as is | medium | choose on the order |
| 12 | Polarity/cleanup of footprints (VEMD10940F), USB shell overhang | low | verify |
| 13 | No RF routing exists; feed-line lengths (IPC to IFA about 20 mm, to the 868 MHz antenna about 20 mm) estimated only | medium | route after review |

## 10. Items requiring physical measurement
VNA (calibrated at the U.FL): IFA S11 bare and in the enclosure; 868 MHz S11; NFC coil L, R, Q and the tank match (12-15 MHz) with and without the RF cover and the battery; ESP32 antenna S11 in the module's final position. Spectrum analyzer: CC1352R sub-GHz harmonics at 2604 MHz with the IFA fitted; crystal harmonics; TRF7970A 13.56 MHz harmonics at 868 MHz; ESP32 -> CC1352R coupling level (conducted measurement at the U.FL with the ESP32 transmitting). Chamber: IFA and 868 MHz efficiency/pattern, ESP32 antenna efficiency with the board cut-out. Bench: NFC read range, IR link, supply noise from the buck-boost on the RF rails.

## 11. Files and changes
Schematic: ANT1 now `Antenna_Chip` (feed + ground stub), second IFA shunt C84, NFC tank values (C61 47p, C62 12p fitted, C63 39p, C64 2.2p DNP, R42 845 ohm 1206), NFC shield SH2/SH2C removed, U.FL J8 added; ERC: 0 errors, 1 library warning. BOM `schematic/BOM_REVB_schematic.csv`, `RF_CRITICAL_PASSIVES.csv`. Placement/PCB scripts `pcb/make_board_b.py`; footprints `schematic/NH_REVB.pretty/IFA_AN043_15.2x5.7`, `NFC_COIL_18x16_6T`.
