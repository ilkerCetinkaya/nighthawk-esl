# REV B preliminary PCB placement (not frozen, not routed)

Date: 2026-11-08. File: `pcb/NIGHTHAWK_REVB.kicad_pcb` (KiCad 10.0.6). Generator: `pcb/make_board_b.py` (reads `schematic/design_b.py` and `schematic/nets.xml`), drawings by `pcb/draw_b.py`. REV A untouched. **No Gerbers produced; nothing is production-ready; RF layout is not frozen; no copper routed.**

## 1. Board
80 x 50 mm, 4 copper layers (stackup JLC04161H-7628 is not yet written into the PCB file: set it in KiCad Board Setup before routing), black solder mask and HASL with lead are fabrication choices recorded here only. Outline: ESP32 antenna notch x 0-6.2 mm, y 17-50 mm; battery cable notch 4 x 3 mm at x 44.5-48.5 (bottom edge, moved from x 38-42 to sit by the battery connector). Square corners for now (no radius yet). Min through drill set to 0.2 mm.
All 239 footprints with a footprint are placed (172 top, 67 bottom). Net assignment to pads came from the KiCad netlist; every pad number matched (no missing pad nets reported).

## 2. Placement
| Block | Position (x, y mm, y up from the USB edge) | Notes |
|---|---|---|
| ESP32-C3-WROOM-02 | module x 0.4-20.3, y 30-49, antenna toward the notch (left), rotated 90 | module's own antenna keepout covers the notch (air) |
| USB-C TYPE-C-31-M-12 | bottom-right corner, x 69-80, y -0.9-8.6 | opposite end from the ESP32 (53 mm apart); shell front sticks out 0.85 mm past the edge as in REV A [U: check the datasheet drawing] |
| NFC coil window | x 21.7-49.7, y 33-49 | **no components, no copper on L2, L3, B** (rule areas on In1, In2, B.Cu, footprints disallowed); coil traces on F.Cu are layout work still to do; coil feed pads placeholder at its lower edge |
| NFC shield (Wuerth 36103205S + 36003200S) | centre (32.0, 21.0), land pattern 21.5 x 21.5 | inside: TRF7970A, 27.12 MHz crystal, matching network, test points; the coil is outside, 1.2 mm from the can |
| RF shield (same parts) | centre (63.8, 32.2) | inside: CC1352R, IPC, both crystals, RF passives, test points |
| 2.4 GHz IFA zone | x 65-80, y 44.3-50 | rule area on all four layers (tracks, vias, fills); feed placeholder pad only: **the IFA geometry is not designed** |
| 868 MHz chip antenna (DNP) | right edge, x 74.5-80, y 19.5-31.5 keepout | chip antenna footprint from the Johanson datasheet; the meander and ground clearance are layout work |
| U.FL 2.4 / sub-GHz | x 75-80 beside the RF can | conducted test ports |
| Battery connector JST S2B-PH-SM4-TB | x 44.2-53.4, y 4.1-14.3, 0.1 mm from the cable keepout | notch keepout rule area on all layers |
| Buck-boost, LDOs (bottom side) | x 53.5-69, y 0.5-11.3 | **10.2 mm from the RF can, 10.8 mm from the NFC can, 10.4 mm from the IR parts, 19.8 mm from the coil** |
| Charger, USB ESD, PTC | bottom edge, x 53.5-69 (top side) | near USB |
| IR emitter / receiver (side-view), TIA | bottom edge x 21-43 | emitter and photodiode rotated to look out of the bottom edge |
| TCA9555 x2, interlock gates, supervisor | mostly bottom side, left column and bottom centre | none under the RF can or the ESP32 module |
| SPI flash, ESP32 passives | left, under the module | |
| Reset/boot/user buttons, LEDs | near the left/centre | |
| Debug headers J6/J7 | bottom-left | 2.54 mm through-hole, both sides blocked |
| JTAG 2 x 5 1.27 mm | between the cans, x 43-52, y 15-23 | |
Drawings: `pcb/drawings/blocks_top.png`, `blocks_bottom.png`, `rf_zones_keepouts.png` (zoning, keepouts, cans, antennas) plus `.svg`.

## 3. Rule check on the placement
| Rule | Result |
|---|---|
| ESP32 and USB at opposite ends | 53 mm apart: pass |
| ESP32 antenna to NFC coil (>= 15 mm) | 15.5 mm: pass |
| ESP32 antenna to 2.4 GHz IFA | 58.8 mm |
| Switching regulator to RF can / NFC can / IR (>= 10 mm) | 10.2 / 10.8 / 10.4 mm: pass |
| Coil to RF can | 3.3 mm (RF can left edge to coil edge) [A: no minimum rule defined] |
| Parts inside antenna / coil / cable keepouts | KiCad DRC: none |
| Courtyard overlaps | none |
| Board-edge copper clearance | none (the ESP32 was moved 0.4 mm after a first DRC run flagged pad 1) |
KiCad DRC (`pcb/DRC_REPORT_placement.rpt`): 4 errors, all the same item: IPC pad spacing 0.17 mm against the default 0.2 mm clearance (the IPC land pattern is my assumption from terminal dimensions, JLCPCB's minimum spacing is smaller; replace with Johanson CAD). 499 unconnected items (nothing routed). Silk warnings ignored. Netlist unchanged by this stage.

## 4. Unresolved risks
1. **RF layout not frozen**: IFA and 868 MHz antenna geometry not designed or verified against the stackup; sub-GHz chip antenna positioned for the keepout only.
2. RF/NFC passive network still unresolved: NFC L1 loss (see `REV_B_RF_PASSIVE_VERIFICATION.md`), SRF/ESR of the 100 pF IPC capacitors, TI reference design not obtained.
3. **IPC harmonic isolation**: TI says the IPC alone is not enough for ETSI at 2604 MHz and recommends an SPDT switch; none in the design.
4. Both cans are 21.5 mm; frame pad ring leaves 2.4-4.9 mm gaps per side for signal exits; RF and signal exit routes (RF traces under the frame gaps) not planned. Cover compatibility with the frame: pair names from Wuerth datasheets, assembled height 3.0-3.2 mm unresolved.
5. The NFC coil is 1.2 mm from the NFC can and 3.3 mm from the RF can; the ESP32 shield can is 1.6 mm from the coil edge: coupling and detuning of the coil are unknown until simulated/measured.
6. USB-C shell overhang past the edge; battery cable notch width/depth versus a real cable and enclosure unverified.
7. 239 parts on 80 x 50 mm with test points on both sides: some bottom-side clusters are dense; there is no routing estimate yet.
8. Stackup not stored in the PCB file; HASL-lead and black mask are not representable here.
9. The placer put some spill parts (test points, two flash pull-ups) far from their ICs (top middle, beside the coil): these are placeholders for later hand placement.
10. Footprints: the VEMD10940F/VSMB10940 pad mapping, IPC land pattern, TPS63802 footprint (from TI's DLA0010A example) and the shield frame come from datasheets/KiCad libraries and are not cross-checked on the manufactured part.
