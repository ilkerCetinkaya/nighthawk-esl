# REV B: resolution of the four open RF/power passive items

Date: 2026-11-08. Labels: [DS] datasheet read, [CALC] calculation (scripts in `integrated/`), [A] assumption, [U] unknown/not verified, [MEAS] measurement (none exists). Nothing here is measured. The NFC coil network and the CC1352R RF network are **not frozen**.

## 1. NFC L1 (150 nH, TX path)
Operating point [CALC/A]: TRF7970A TX_OUT is a 0..VDD_RF square wave with 4 ohm source impedance (TRF7970A datasheet 7.3). With VDD_RF about 3.4 V (VIN 3.6 V) the fundamental is about 2.16 V peak, so the matched current is about 0.27 A peak = **0.19 A RMS** and about 146 mW into the 4 ohm node. L1 sits in this path.

| Candidate | L / tol | Q (spec point) | SRF | DCR | Irms | Stock | P at 0.19 A (DCR only) |
|---|---|---|---|---|---|---|---|
| APV AHW1608C-R15GTF (0603, previous choice) | 150 nH +-2 % | 28 @150 MHz | 990 MHz | 0.92 ohm | 280 mA | 3,980 | 33 mW (23 %) |
| **TDK MLF2012DR15JT000** (0805, now provisional) | 150 nH +-5 % | min 20 / typ 30 @25 MHz | min 320 / typ 410 MHz | max 0.20 / typ 0.13 ohm | 300 mA | 9,540 | 4.7-7.2 mW (3-5 %) |
| Coilank HWF1608KR15DS (0603) | +-10 % | min 12 @7.9 MHz | 950 MHz | 0.15 ohm | 1,000 mA | **0** | 5.4 mW |
| Coilank HWC2520JR15D (1008 wirewound) | +-5 % | not read | not read | 0.70 ohm | 580 mA | 3,750 | 25 mW |
| Murata LQW18ANR15J00D (0603) | +-5 % | not read | not read | 1.5 ohm | 160 mA | 3,480 | 54 mW, current rating too low |
| Taiyo HK1608R15J-T (0603 multilayer) | +-5 % | not read | not read | 0.73 ohm | 300 mA | not checked | 26 mW |
Operating frequency 13.56 MHz is far below every SRF (>= 23x) [DS]. **Caveat:** none of the datasheets gives Q or series resistance at 13.56 MHz; Q is specified at 7.9-150 MHz. For the TDK part the Q minimum at 25 MHz (20) implies up to 1.18 ohm series resistance at 25 MHz, which would be 42 mW at 0.19 A, so the DCR-based advantage is **not guaranteed**; at 13.56 MHz the real series resistance is expected to be between DCR (0.13 ohm) and that bound [A]. The ranking by DCR is only an estimate.
**Decision (provisional):** TDK MLF2012DR15JT000 replaces the APV part (lower DCR, higher current margin, tolerance +-5 %, in stock, 0.85 mm height); Coilank HWF1608KR15DS stays the preferred part when it is back in stock (the placement footprint is an 0805 land that also takes the 0603 body). L1 loss and tuning must be measured on the first prototype (series resistance of L1 with an impedance analyzer or VNA, then output power into 50 ohm). L6 (330 nH, 50 ohm side, about 60 mA RMS) was changed to TDK MLF2012DR33JT000 (+-5 %, SRF min 200 MHz, DCR max 0.40 ohm, 250 mA; 2,160 in stock) for the same family and tighter tolerance.
**Status: NFC network unresolved until [MEAS].**

## 2. TPS63802 inductor: Murata DFE252012F-R47M (`integrated/tps63802_inductor_calc.py`)
Datasheet values [DS, Murata J(E)TE243A-0017B-01]: 0.47 uH +-20 % (1 MHz), DCR max 23 mohm, rated current **6.7 A at -30 % inductance, 4.9 A at 40 K temperature rise**, operating -40..+125 C including self-heating, inductance temperature coefficient <= 1000 ppm/C, 2.5 x 2.0 x 1.2 mm. (My previous text called 4.9 A the saturation current: that was wrong, 4.9 A is the thermal rating.)
TPS63802 [DS SLVSEU9D]: boost peak current limit 4 / 5 / 5.75 A (min/typ/max), recommended effective L 0.37-0.57 uH, CO,eff >= 7 uF, f 2.1 MHz boost, 1.4 MHz buck-boost.
Worst-case results [CALC]:
- Peak inductor current by the datasheet equation, Vin 2.5 V, Vout 3.6 V: 0.8 A load: 1.67-1.82 A; 1.0 A: 1.99-2.14 A; 2.0 A: 3.59-3.74 A. Datasheet rule (+20 %) gives at most 4.48 A, below 6.7 A. L at the low end (0.376 uH tolerance, assumed -10 % bias drop = 0.338 uH).
- The inductor 6.7 A rating is above the converter's maximum current limit 5.75 A, so even a hard current-limit fault cannot saturate it.
- RMS current 1.3-1.6 A at 0.8-1.0 A load (Vin 2.5 V); 3.2 A at 2 A: below 4.9 A. Conduction loss at 85 C (copper +23 %): 48-75 mW at 0.8-1.0 A, 292 mW at 2 A. Self-heating with the 72 K/W implied by the rated point: 3.5-5.5 K (0.8-1.0 A), 21 K (2 A).
- Stability: the converter is internally compensated; stable inside the datasheet windows. **Marginal point:** the initial tolerance window 0.376-0.564 uH sits at the lower edge of 0.37-0.57 uH, and a bias drop would push it below. TI's own listed inductors (XFL4015-471ME, DFE201612E) are also 0.47 uH +-20 %, so TI accepts the same window [DS table 10-2, tolerance of the TI parts not read].
- Not verified: inductance versus DC current curve (Murata SimSurfing), core loss at 1.4-2.1 MHz, measured ripple and efficiency, the real system peak load (0.65 A budget is my estimate).
**Verdict:** electrically adequate on paper; part is not on TI's list [U].

## 3. CC1352R 10 uH inductor
- cjiang FTC201212S100MBCA: the LCSC datasheet link returns a 0-page PDF; no usable manufacturer documentation was obtained. **Rejected.**
- Replacement with documentation in hand: **Murata DFE252012F-100M=P2** (LCSC C703141, 6,515 in stock, US$0.165): 10 uH +-20 %, DCR max 480 mohm, rated 1.4 A (-30 % L) / 0.95 A (dT 40 K), operating -40..+125 C incl. self-heating, <= 1000 ppm/C [DS, same spec document as L1]. Q and SRF are not given in that document [U].
- Need: TI's DC/DC inductor requirement (value, tolerance, DCR, Isat) is only in the device reference design (SWRA640 says values are in the device-specific reference design; the design files need a myTI login, not used). DCOUPL 1 uF is confirmed by SWRA640 (section 11) [DS]. 10 uH and 22 uF (CC1352R datasheet note) remain assumptions for the inductor value [U].
- CC1352R current is a few tens of mA [A], far below 0.95 A.

## 4. RF capacitors, and comparison with TI and Johanson
What the documents give [DS]: Murata GRM1555C1H101JA01 (and the GRM1555C1H... family): C0G, 0 +-30 ppm/C, +-5 %, 50 V, Q >= 1000 at the test point, insulation resistance > 10 GOhm. Samsung CL05C series: same C0G figures. **SRF and ESR are not in these datasheets [U]**; they require Murata SimSurfing / Samsung EPS data, which I did not obtain.
Estimate [CALC, assumed ESL 0.3-0.6 nH for part + pads] in `integrated/rf_cap_srf_estimate_output.txt`:
- 100 pF (IPC C41/C51): SRF about 650-920 MHz. At 868 MHz the capacitor is at or just above series resonance, so as a series DC block (C51) it is a low impedance (about -0.2 to +1.4 ohm), and as an RX_TX decoupler (C41) it is a small reactance; at 2.44 GHz it is inductive (about +4 to +9 ohm to ground). This is the same 100 pF value TI and Johanson specify, so the behaviour matches the reference, but **the exact part TI used is unknown** [U].
- NFC capacitors (220 pF-1.5 nF): SRF 170-620 MHz, 12-45x above 13.56 MHz, effective C within 0.1-0.7 % of nominal: OK. Series 1.5 nF carries 0.19 A RMS and C63 (330 pF) about 0.2-0.3 A circulating [CALC/A]; ESR heating not checked [U].
- 0.3-3.9 pF 868 MHz matching parts (Murata GJM, +-0.1 pF): SRF > 5 GHz, OK; Johanson's own 500R07 parts remain the specified alternates.
- TIA Cf 1.5 pF: tolerance +-0.1 pF (6.7 %) shifts the 10.6 MHz bandwidth by about +-4 % [CALC].
DC-bias: C0G parts have none. X5R/X7R decoupling parts are covered in `REV_B_PASSIVE_SELECTION.md`; the replacement parts are CL10A225KO8NNNC (2.2 uF, X5R, 16 V, now Basic) and CL10A226MQ8NRNC (22 uF X5R 6.3 V 0603, matching TI's TPS63802 recommended class [DS table 10-3]); bias derating is typical-value only [A].
**Comparison with TI/Johanson:**
- Topology matches SWRA629A figure 3 and Johanson page 3: IPC pins 1/4/5/6-9 wired as in the Johanson reference schematic; external bias for both bands; sub-GHz series DC block and RX_TX shunt. Naming differs between the documents (TI: C41 on RX_TX, C51 on the sub-GHz port; Johanson: C41 series on the sub-GHz port, C51 shunt on RX_TX); the function is the same, and the schematic follows TI's names.
- Johanson also lists GND vias close to pads 2, 3 and 10 and a 1.27 mm via spacing as "crucial for filter harmonic attenuation" [DS]: layout requirement, not yet implemented.
- **Isolation risk (SWRA629A):** with the IPC the third harmonic of 868 MHz measured on the 2.4 GHz port is -33 dBm (discrete design -45 dBm); a 2.4 GHz antenna connected directly to the IPC port fails ETSI limits at 2604 MHz, so TI recommends an SPDT switch with the IPC. The REV B design has no switch. For a research instrument used for owned devices this is a compliance and EMC risk: do not transmit sub-GHz at full power with the 2.4 GHz antenna fitted until measured.
- The TI official reference design files were **not obtained** (login required), so the comparison is against SWRA629A and Johanson only.
**Status: RF network not frozen; SRF/ESR and the isolation issue open.**

## 5. Changes made to the BOM/netlist as a result
L5 -> TDK MLF2012DR15JT000 (C76739), L6 -> TDK MLF2012DR33JT000 (C87521), L2 -> Murata DFE252012F-100M=P2 (C703141). Netlist unchanged (175 nets identical). Footprints: L2 1008, L5/L6 0805.
