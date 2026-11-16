# REV B RF design gate report (R2 baseline, not frozen)

Date: 2026-11-08. The R2 placement is accepted as the preliminary mechanical/layout baseline. **RF performance is not frozen, nothing is measured, no RF routing, no Gerbers, not production-ready.** Labels: [DS] document read, [CALC] calculation, [A] assumption, [U] unknown, [MEAS] needs measurement. Scripts: `integrated/rf_coex_calc.py`, `rf_feed_geometry.py`, `nfc_coil_design.py`, `nfc_retune.py`; PCB checks: `pcb/verify_r2.py`, `integrated/keepout_verification.txt`, `final_placement_checks.txt`.
User direction recorded: working prototype first, production optimisation later; the three RF functions (2.4 GHz SoluM/Hanshow research, 868 MHz, 13.56 MHz NFC/FeliCa) and the Pricer IR link are validated separately; matching networks stay tunable and **no RF test point is removed**.

## 0. Schematic corrections made at this gate (documented engineering corrections)
1. **U.FL taps moved.** My earlier VNA procedure for the IFA was wrong: the 2.4 GHz U.FL was tied to the IPC port, so the antenna could not be measured from it. Now J3 (via R27, DNP) taps `ANT24_FEED` and J4 (via R30, DNP) taps `ANTSUB_FEED`. Conducted CC1352R test: fit R26 (IPC to feed), remove R28/L3 (antenna side). Antenna test: remove R26, fit R28 (or L3). Sub-GHz: conducted test fit R29, remove R31/L4; antenna test remove C35 (or R29) and fit R31/L4. NFC: J8 on `NFC_ANT`, remove R39 for coil tests (unchanged).
2. **Coexistence handshake wired:** `ESP_RF_QUIET` (TCA9555 U22 P02, output) to CC1352R DIO_7 (pin 12); `CC_RF_BUSY` (CC1352R DIO_6, pin 11) to U22 P03 (input); R64 10 kohm pull-down on `ESP_RF_QUIET` (fail-safe, see 1.3). ERC: 0 errors, 1 library warning; everything else in the netlist unchanged.
3. J4 U.FL moved from 1.3 mm to 7.8 mm from the 868 MHz zone (placement only).

## 1. 2.4 GHz coexistence
### 1.1 The 15.6 dB figure
15.6 dB is the **calculated free-space path loss for isotropic antennas at 58.8 mm** (20 log(4 pi d / lambda), lambda 122.9 mm, d = 0.48 lambda). At 0.48 lambda the antennas are in the near field and Friis does not strictly apply; it is an estimate, **not a measured antenna isolation**. Real coupling is unknown [U]; I use scenarios from -10 to -30 dB (the 15-30 dB range is my assumption, no source).
### 1.2 Worst-case CC1352R input power (reconciled, `rf_coex_calc_output.txt`)
ESP32 TX 20.5 dBm (802.11b, conducted at the module antenna port [DS]); CC1352R absolute maximum 2.4 GHz RF input **+5 dBm** [DS]. **Reconciliation of the 1.3 dB:** the user's arithmetic (20.5 + S21) is correct. The first gate table subtracted the IPC typical insertion loss (1.3 dB) before the CC1352R pins and did not say so, while the R2 report listed the no-loss values for two of the points (+4.9, -9.5 dBm). The protection margin must not rely on a loss that has no guaranteed minimum (the IPC gives 1.3 dB typ, 1.6 dB max, no minimum) and S21 is an antenna-port figure, so **all protection margins now use the no-loss basis P_in = 20.5 dBm + S21**:
| S21 antenna to antenna | P_in (no-loss, protection basis) | margin to +5 dBm | for reference, with 1.3 dB IPC loss |
|---|---|---|---|
| -10 dB | **+10.5 dBm** | **-5.5 dB (exceeds)** | +9.2 dBm |
| -15.6 dB (free-space estimate) | +4.9 dBm | +0.1 dB | +3.6 dBm |
| -20 dB | +0.5 dBm | +4.5 dB | -0.8 dBm |
| -30 dB | -9.5 dBm | +14.5 dB | -10.8 dBm |
Consequence: at the free-space estimate there is effectively **no margin**; the unknown real S21 decides. **Mandatory protective step for the first two-radio test:** measure S21 with the ESP32 at reduced TX power (esp_wifi_set_max_tx_power, 10 dBm or lower) and a 10 dB or larger attenuator in the J3 path, and only raise the power after the measured S21 shows a margin of at least 6 dB below +5 dBm at the full 20.5 dBm. Reverse direction (no-loss basis): CC1352R +5 dBm gives -5 to -25 dBm at the ESP32 antenna port, 73-93 dB above its -98 dBm sensitivity.
### 1.3 Mandatory firmware time slotting
- Any CC1352R RF activity (2.4 GHz or sub-GHz, TX or RX, including RX scanning) counts as BUSY until sub-GHz/2.4 GHz concurrency is measured; any ESP32 Wi-Fi or BLE activity counts as ESP active.
- Signals: `CC_RF_BUSY` (CC1352R output, read by the ESP32 through the TCA9555 input) and `ESP_RF_QUIET` (written by the ESP32 through the TCA9555, read by the CC1352R GPIO). Default at power-up: `ESP_RF_QUIET` low through R64 (the TCA9555 powers up as inputs with pull-ups, so without R64 the CC1352R would read "quiet" while the ESP32 radio may be on); `CC_RF_BUSY` is high-impedance while the CC1352R is held in reset by the interlock, which reads as BUSY at the TCA pull-up: both defaults are fail-safe.
- Rules: (1) the ESP32 stops Wi-Fi and BLE (esp_wifi_stop, BLE controller off, modem off) and then sets QUIET = 1; (2) the CC1352R may enable any radio only after reading QUIET = 1 for at least 2 ms, then sets BUSY = 1 before enabling the radio; (3) the CC1352R turns the radio off, waits 2 ms, clears BUSY; (4) the ESP32 may start Wi-Fi/BLE only after BUSY = 0 for at least 2 ms; (5) minimum slot 10 ms, guard 2 ms (I2C TCA access about 1 ms at 400 kHz [A]); (6) if BUSY = 1 and the ESP32 radio is on (or QUIET = 1 is withdrawn while BUSY = 1) the CC1352R aborts its radio and the ESP32 kills its radio and logs a coexistence fault; (7) the hardware interlock (CC_RESET gated by INTERLOCK_OK) stays the independent kill for the CC1352R.
- The ESP32-C3's own external-coexistence pins were not investigated [U]; the scheme works without them.
### 1.4 Is extra isolation or switching required?
For time-multiplexed operation **no RF switch or extra isolation is required**. For simultaneous same-band operation a victim receiver tolerating -30/-40/-50 dBm would need 50/60/70 dB (ESP32 to CC1352R) and 35/45/55 dB (CC1352R to ESP32); passive isolation on this board is of the order of 15-30 dB [A]. A switch cannot isolate two receivers sharing a board; the levers are separation (58.8 mm already the maximum), antenna orientation, and the shield. Simultaneous ESP32 2.4 GHz with CC1352R **sub-GHz** is plausible by frequency separation but is untested; the IPC rejection at 2.44 GHz on the sub-GHz path is not listed [U].

## 2. 868 MHz antenna against the Johanson reference
Reference [DS 0868AT43A0020 v1.8 p. 2-3]: corner placements on a 26 x 42 mm ground with a 10 x 11 mm (or 11 x 10 mm) zone, complete GND and layer clearance, free of metal below and above; 50 ohm feed; pi slots; also a 40 x 20 mm board with a 9.5 mm ground-free end. The manufacturer's layout/CAD file was not obtained [U].
| Item | Reference | R2 layout | Status |
|---|---|---|---|
| zone size | 10 x 11 (or 11 x 10) mm | 10 x 11 mm, x 70-80, y 0-11 | matches |
| position | board corner | bottom-right corner | matches |
| all-layer clearance | no GND or metal on any layer in the zone | rule area on F, L2, L3, B; verification below: 0 foreign pads/tracks/fill | matches (only pour present so far is L2) |
| orientation | antenna along the board edge, feed line from the side | along the bottom edge, feed from the left (vertical mirror of the figure) | equivalent by symmetry [A] |
| surrounding ground | 26 x 42 mm ground | full 80 x 50 board ground | not the same; effect [U] |
| 50 ohm feed | required | 0.359 mm over L2 (section 5) | planned |
| pi network | slots required | C37 / L4 / C38 (+ R29/R31) DNP | present |
| nearby metal | none shown | RF shield frame 4.2 mm, USB-C shell 6.6 mm, U.FL J4 7.8 mm (was 1.3 mm) | **outside anything tested; unquantified** |
- Investigated: the 4.2 mm RF shield (21.5 mm frame, lid height 3.0-3.2 mm [U]): the cover is a metal plate about 4 mm from the zone; a 16.1 mm frame (Wuerth 36103166S, 17.3 mm land) would add about 2.2 mm but its footprint is unverified; moving the can further up conflicts with the IFA U.FL area and the coil clearance. USB-C shell 6.6 mm: moving it left collides with the IR receiver at the bottom edge. **I do not claim compliance or performance**: only S11 (and later efficiency) measurements decide. Option A (current): measure. Option B: if S11 is bad, swap the 21.5 mm can for the 16.1 mm one or remove the cover during the 868 MHz test (cover-off S11 shows the can effect). VNA matching network preserved (C37, L4, C38, R29, R31, R30, J4).

## 3. NFC coil (prototype candidate)
Geometry kept: outer 18 x 16 mm, 6 turns, trace 0.25 mm, gap 0.10 mm, F.Cu spiral plus B.Cu underpass.
| Parameter | Value | Status |
|---|---|---|
| inductance | **1.43 uH** | **calculated**, SLOA241C equation 2 for the average-turn rectangle (average width/height of the six turns), mu_r = 1, "a" = trace width 0.25 mm, N = 6, no layer-to-layer or ground-plane coupling, no shield or enclosure effect; TI's online calculator not run [U] |
| series resistance | 0.92 ohm | **calculated**: 35 um copper, rho 1.72e-8, DC resistance x 1.3 for skin/proximity [A] |
| unloaded Q | 133 | **calculated** (omega L / R) |
| loaded Q target | 7 (7-10 for ISO 14443A/B and FeliCa [DS]) | chosen |
| Rp, Cp, Cs | 845 ohm, 39 (+2.2) pF, 47 + 12 pF | **calculated starting values** for 1.43 uH |
| measured L, R, Q | - | **not measured** (no PCB) |
Retuning after fabrication: measure L and R at 13.56 MHz with the VNA at J8 (R39 removed), then `python3 integrated/nfc_retune.py <L_uH> <R_ohm or -Q> [target_Q]` prints Rp, Cp, Cs (E96/E24 nearest) and the expected -10 dB bandwidth; example: 1.43 uH, 0.92 ohm, Q 7 gives 853 ohm, 39.8 pF, 60.2 pF; a measured 1.20 uH with Q 110 and target Q 8 gives 818 ohm, 56.7 pF, 62.2 pF. Tune with the RF cover and the enclosure fitted. Clearances to metal and the shield evidence are in `REV_B_ANTENNA_ENGINEERING_R2.md` section 4 (ESP32 9.8 mm, RF shield 10.0 mm, J5 7.8 mm; lateral ground not 10 mm).

## 4. Harmonics and spurious emissions
- **TI's SPDT recommendation** (SWRA629A): measured third harmonic of the 868 MHz TX on the 2.4 GHz port: discrete reference -45 dBm, IPC -33 dBm; an efficient 2.4 GHz antenna connected directly to the IPC (or through a diplexer) fails the ETSI limit at 2604 MHz, so TI recommends an SPDT with the IPC. CC1352R conducted spec: sub-GHz 2nd/3rd/4th harmonic < -30 dBm (+14 dBm, 868 MHz) [DS]. Required ETSI limit value: not read [U].
- **Switch in the schematic?** Decision: **not for prototype 1.** Reasons: it matters only when transmitting at 868 MHz with the IFA fitted and when regulatory limits apply; I did not research or select a part (no part number invented), insertion loss would reduce the +5 dBm 2.4 GHz power, and it would remove the direct path that the U.FL/VNA procedure needs. Instead: the 2.4 GHz path is already segmented by R26/R28 (0402 pads) so a switch or filter can be inserted later; the routing proposal (section 7) reserves a 3 x 3 mm area inside the shield next to R26. Trigger to add it: the spectrum measurement 4.3 shows the 2604 MHz level above the limit that applies to the intended use, or the product must be certified.
- **868 MHz third harmonic, 2604 MHz:** -33 dBm at the 2.4 GHz port with the IPC [DS]; the sub-GHz antenna and the IFA both exist; coupling between them over 33.3 mm is unknown [U]. Conducted level is the starting point; radiated level needs the antennas.
- **Crystal-related spurs [CALC]:** 48 MHz x 50/51/52 = 2400/2448/2496 MHz; ESP32 40 MHz x 60/61/62 = 2400/2440/2480 MHz; TRF7970A 27.12 MHz x 90 = 2440.8 MHz and x 32 = 867.84 MHz; 13.56 MHz x 64 = 867.84 MHz; 32.768 kHz irrelevant; buck-boost 1.4-2.1 MHz switching harmonics reach 868 MHz only as weak spurs [A]. Mitigation in layout: crystals inside the RF shield (CC1352R) or close to their IC with ground guard, no RF traces near them.
### 4.3 Spectrum analyzer test plan (mandatory prototype measurements, conducted at the U.FL unless noted)
1. Setup: analyzer 9 kHz-6 GHz minimum, 50 ohm, attenuator 20 dB, calibrated cable; board on battery or a clean USB supply; interlock armed; R26 fitted, R28 removed (2.4 GHz) / R29 fitted, R31 removed (868 MHz); J3/J4 R27/R30 fitted.
2. 868 MHz TX +14 dBm (highest power): measure fundamental, 2nd/3rd/4th harmonic at 1736, 2604, 3472 MHz at the **2.4 GHz port (J3)** and at the sub-GHz port (J4); RBW 100 kHz; record dBm; pass criterion: below the limit chosen for the intended use (open [U]); with the IFA connected instead (R28 fitted, R27 removed) compare.
3. 2.4 GHz TX +5 dBm: fundamental, harmonics 4.8/7.2 GHz, channel spacing mask for the SoluM/Hanshow GFSK settings.
4. Crystal spurs: CC1352R idle and in RX, ESP32 transmitting, TRF7970A transmitting: scan 2.3-2.6 GHz and 860-876 MHz at the three U.FL ports with a near-field probe for the sources; log any line at 2400/2440/2448/2480/2496/2604/867.84 MHz.
5. Coexistence: ESP32 transmitting at full power while the analyzer measures the level at the CC1352R U.FL (J3) with the antennas connected (S21 estimate), and the reverse with the CC1352R transmitting while measuring at the ESP32 antenna via a probe.
6. NFC: 13.56 MHz harmonics up to 1 GHz at J8 with the coil disconnected (matched dummy load) and with the coil.
7. Repeat steps 2 and 4 with the RF shield cover fitted and removed.

## 5. RF feed geometry and reference planes
**Stackup used (JLCPCB, https://jlcpcb.com/impedance, read 2026-11-08): JLC04161H-7628, finished 1.59 mm +-10 %:** top copper 0.035 mm (1 oz, 1.38 mil); prepreg 7628 x1 0.2104 mm (8.28 mil, resin 49 %, eps_r 4.4); L2 copper 0.0152 mm; core 1.065 mm (eps_r 4.6); L3 copper 0.0152 mm; prepreg 7628 x1 0.2104 mm; bottom copper 0.035 mm; solder mask 1.2 mil above substrate, 0.6 mil above trace, 1.2 mil between traces, eps_r 3.8. JLCPCB calculator inputs: rigid, 4 layers, 1.6 mm, outer 1 oz, inner 0.5 oz, mil, 50 ohm, single-ended non-coplanar, signal layer 1, bottom reference layer 2, no top reference: **trace width 14.12 mil = 0.3586 mm**. The calculator's default first stack-up is a different one (JLC04161H-3313A, 13.57 mil); the 7628 tab was selected explicitly. Tolerance +-10 % [DS JLCPCB]; controlled-impedance ordering or acceptance of the nominal width must be chosen on the order.
**Coplanar (guard traces):** the JLCPCB coplanar calculator was driven but returned no width in the automated run, so **no JLCPCB coplanar result exists**. Closed-form conformal-mapping estimate (zero thickness, no mask, eps_r 4.4, h 0.2104 mm; `rf_feed_geometry_output.txt`): 50 ohm width 0.355 / 0.376 / 0.389 / 0.398 mm for gaps 0.15 / 0.20 / 0.25 / 0.30 mm. The same formulas give 0.403 mm for the microstrip where JLCPCB gives 0.359 mm, so applying the ratio 0.89 gives roughly 0.32 / 0.33 / 0.35 / 0.35 mm [CALC, low confidence]. Use JLCPCB's coplanar calculator on the actual order page before routing a guarded line; I recommend plain microstrip with stitched ground vias (no guard trace) for the first prototype.
**Reference plane for every feed:**
| Feed | Layer | Reference | Notes |
|---|---|---|---|
| IPC pin 1 to R26 / pi / IFA feed pad | L1 microstrip 0.359 mm | L2 solid ground, no split under the line | L2 ground ends at y = 44.8 mm at the IFA (AN043 0.5 mm edge); line ends at the feed pad |
| IPC pin 4 to C35 / R29 / pi / 868 MHz antenna | L1 microstrip 0.359 mm | L2 | L2 ground ends at the zone boundary x = 70 mm; the last 1-2 mm to the antenna pad is in the ground-free zone as in the Johanson figure |
| U.FL J3 / J4 taps | L1 stubs as short as possible | L2 | taps off the feed node, DNP when not testing |
| RF pads of the IPC and ground vias | L1 | L2 and via fence | Johanson: GND vias at 1.27 mm spacing around pads 2, 3, 10 are "crucial for filter harmonic attenuation" |
| ESP32 antenna | inside the module | module ground | no external feed |
| NFC 13.56 MHz coil and tank | F.Cu / B.Cu underpass | none (wavelength 22 m) | L2/L3 deliberately empty under the window |
Neither L3 nor B.Cu may serve as an RF reference; no RF line crosses a plane split.

## 6. Final placement integrity (`pcb/verify_r2.py`, `integrated/keepout_verification.txt`)
| Check | Result |
|---|---|
| Keepouts on every copper layer | 19 keepout/layer checks (ESP32 cut-out F/L2/L3/B; IFA box L1; IFA L2-L4 from y 44.8; 868 MHz zone F/L2/L3/B; coil window L2, L3 and B footprints; cable notch F/L2/L3/B): 0 foreign pads, 0 tracks or vias, 0 mm2 of filled zone inside any of them. Only the L2 GND zone is drawn (3,130 mm2 filled); L1/L3/B pours do not exist yet, so for those layers the check is trivially clean until they are drawn |
| KiCad DRC | no courtyard overlap, no keepout violation, no edge-clearance violation; errors left: IPC pad spacing 0.17 mm (assumed land pattern) and antenna-footprint artwork artifacts (unnetted copper of the IFA and coil footprints overlapping their own pads) |
| RF shield courtyard | frame outer 21.5 x 21.5 mm at x 58.10-79.60, y 15.25-36.75, 0.40 mm from the board edge; nearest foreign courtyards: F1 0.3 mm, U3 0.4 mm, R15 0.5 mm (below the can), J3 1.2 mm. The pick-and-place and lid-removal clearance beside the frame is too small there; the routing proposal re-clears 1 mm around the frame |
| Lid / enclosure height | Wuerth frame 36103205S + cover 36003200S assembled height 3.0 mm (DigiKey) to about 3.2 mm (my inference): **unresolved**; the enclosure drawing does not exist; the lid is removed vertically, so only free height above is needed |
| USB-C edge | KiCad footprint (courtyard) overhangs the board edge by 0.85 mm. The HRO drawing (LCSC C165948) shows lower shell legs 5.79 mm from the contact row against 5.09 mm in the KiCad footprint (0.70 mm difference) and does not state the overhang numerically in what I read [U]: the footprint must be re-checked against the drawing before routing |
| Battery connector and cable notch | connector courtyard x 35.4-44.6, y 4.1-14.3; notch x 38-42, y 0-3 (4 x 3 mm); keepout 37-43 x 0-4. JST S2B-PH-SM4-TB side entry: wafer mating face toward the notch side per the JST drawing (signal pads at the back, mating side opposite) [DS, read from the LCSC copy]. The plug housing width (PHR-2) was **not read** [U]: if the plug is wider than 4 mm it cannot seat through the notch, so the notch width must be set from the plug datasheet before freezing; the notch also assumes a loose cable |
| ESP32 antenna clearance | cut-out x 0-6.0, y 15.5-50 (15 mm below the module side: 14.6 mm, 0.4 mm short of the 15 mm figure because the cut-out is bounded by y = 15.5; widening to y = 15.0 is cheap and recommended); module tip at x 0; 15 mm clear above/outward is an enclosure requirement |
Correction to the Espressif number: 30.1 - 15.5 = 14.6 mm; the cut-out bottom should move to y = 15.1 or below.

## 7. Mandatory prototype measurements (before any RF value is fixed)
1. Bare-board S11 of the 2.4 GHz IFA, 2.3-2.6 GHz, at J3 (R26 removed, R28 fitted, R27 fitted): bare, with battery, with enclosure, with the shield cover.
2. S11 of the 868 MHz antenna, 840-900 MHz, at J4: shield cover on/off, USB cable plugged/unplugged, with and without J4 populated.
3. S11 of the ESP32 module antenna in place, and Wi-Fi/BLE range baseline.
4. NFC coil L, R, Q at 13.56 MHz (12-15 MHz sweep) at J8; then tank tuning, bandwidth (2 dB points), read range with cards; with and without RF cover and battery.
5. S21 between the ESP32 antenna and the IFA (and the 868 MHz antenna) with 50 ohm terminations at the other ports.
6. Spectrum plan of section 4.3 (harmonics at 2604 MHz, crystal spurs, coexistence levels).
7. CC1352R 2.4 GHz and sub-GHz TX power and receiver sensitivity at the U.FL; compare with the datasheet figures.
8. Pricer IR optical link (separate): LED current waveform on the shunt resistor, gate waveform, photodiode/TIA output, link range and error rate against a reference transmitter; thermal check of the LED (limit 70 C ambient at 100 % burst duty [CALC]).
9. SoluM/Hanshow protocol capture and decode with a known tag (conducted parameters first), per `CC1352R_PHY_VERIFICATION.md`.
10. Supply and noise: buck-boost ripple on 3V6/3V3_RF/3V3_A and its effect on the TIA and the CC1352R sensitivity; interlock tests.
Each result decides one of: IFA pi values, 868 MHz pi values, NFC Rp/Cp/Cs, shield cover on/off, SPDT decision, notch width.

## 8. Final routing proposal (for approval; nothing routed)
**Layers (JLC04161H-7628):** L1 signals, RF lines, components; L2 solid GND (void only under the coil window, IFA box from y 44.8, 868 MHz zone); L3 power pours/signals (3V6, 3V3, 3V3_RF, 3V3_A), void under the coil window and the antenna zones; L4 signals plus ground fill. Stitching vias around all RF lines and shield frames, 1.27 mm pitch around the IPC ground pads, at most 2 mm elsewhere in RF areas [A].
**Rules (JLCPCB minimums: 3.5 mil trace/space, 0.2 mm via [DS]):** signal 0.15 mm / 0.15 mm; power 0.3-0.5 mm; via 0.3 mm drill / 0.6 mm pad [A]; RF microstrip 0.359 mm on L1 (ref L2); RF lines have no vias, no stubs and no 90 degree bends; the pi networks stay at the feed point with 0402 pads and are routed first.
**Net classes:** RF (RF24_P/N, RFSUB_P/N, ANT24_*, ANTSUB_*, UFL*): 0.359 mm where 50 ohm, short stubs to the balanced pins; RF_BIAS (RX_TX): 0.2 mm; XTAL (X48M_*, X32K_*, NFC_OSC_*): shortest, guarded; NFC_TANK (NFC_ANT, NFC_COIL_A, NFC_TXOUT...): short, away from the digital bus; ANALOG_IR (TIA_*, PD_BIAS, CMP_IN, VREF): short, guarded, away from the buck-boost; POWER (SYS, 3V6, VBAT, VBUS_F): wide; DIGITAL: default.
**Order of work:** (1) re-clear 1 mm around the RF shield frame and widen the ESP32 cut-out to y 15.0; fix the USB-C and battery footprints against their drawings; (2) route the CC1352R RF section: IPC to the pi networks to the antennas (the 2.4 GHz line about 20 mm, the 868 MHz line about 20 mm, both on L1 over L2); (3) crystals and CC1352R decoupling; (4) NFC tank and coil traces (coil on F.Cu with the B.Cu underpass); (5) power (buck-boost loop first, short and compact, kept at least 10 mm from the RF can, the NFC area and the IR receiver as placed); (6) IR TIA path; (7) interlock, digital, USB, SPI/I2C; (8) pours, stitching, DRC, connectivity audit, verification of keepouts on every layer (`verify_r2.py`).
**Things that stay adjustable:** all pi networks and tuning pads, R26/R28/R29/R31/R39 0 ohm links, the U.FL J3/J4/J8 taps, the shield cover, and every test point (none removed). Reserved: 3 x 3 mm inside the RF shield next to R26 for a possible 2.4 GHz switch/filter.
**Open items that block freezing:** USB-C footprint difference, plug width for the battery notch, JLCPCB coplanar result, IPC land pattern from Johanson, Wuerth cover height, all measurements in section 7.
