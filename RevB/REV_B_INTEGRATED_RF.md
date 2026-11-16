> UPDATE 2026-11-08: the outline is now 80 x 50 mm (user decision) and the NFC coil window is 28 x 16 mm; antenna keepouts and the cable notch are unchanged. Current drawings are in RevB/integrated/drawings/. Component-level status: REV_B_COMPONENT_GATE.md. PHY verification: CC1352R_PHY_VERIFICATION.md.

# NIGHTHAWK REV B: single-board integrated multi-protocol architecture (pre-routing)

Date: 2026-11-07. Status: architecture and block-level placement only. No schematic, no PCB file, no routing. REV A is unchanged.

`RevB/REV_B_FEASIBILITY.md` (the plug-in module architecture) is superseded by this document. Kept from it:
- the 4-layer JLC04161H-7628 stackup;
- the 50 Ω geometry from the field solver;
- the GD25Q32E storage;
- the power chain;
- the interlock and dead-man design.

Evidence labels:
- **[DS]** manufacturer datasheet or application note read in this session.
- **[FCC]** FCC equipment-authorisation record or test report read in this session.
- **[MFR]** manufacturer web page or spec sheet.
- **[LCSC]** LCSC product page or search page, read 2026-11-07.
- **[CALC]** calculation.
- **[CHK]** the placement rule checker (`RevB/integrated/layout.py`).
- **[A]** assumption.
- **[S]** stated by a third party, not checked.
- **[U]** unknown.
- **[MEAS]** physical measurement. There are none.

---

## 1. Integrated single-board block diagram

Drawing: `RevB/integrated/drawings/block_diagram.svg` (PNG next to it).

**What changed against the previous REV B:**
- The two JST SH 15-pin RF module connectors (J4/J5) and the two edge SMAs are removed.
- All RF transceivers, matching networks, test ports and antennas are on the main PCB.

**Partitioning:**

| Function | Device | Interface to host |
|---|---|---|
| Host, USB, CLI, storage, supervisor | ESP32-C3-WROOM-02-N4 | — |
| 2.4 GHz and sub-GHz RF | TI CC1352R1F3 wireless MCU (RF co-processor with its own firmware) | UART |
| NFC/RFID 13.56 MHz | TI TRF7970A | SPI |
| Pricer infrared | discrete optical front end, timed by CC1352 timers and comparator | via CC1352 |
| Storage | GD25Q32E | SPI |
| Hardware interlock | as before, plus three TPS22918 rails: CC1352, TRF7970A, IR LED | GPIO + TCA9555 |

Every transmit-capable path (CC1352 RF, NFC field, IR LED) is powered only through the interlock-gated rails.

---

## 2. Transceiver IC shortlist (datasheets read; availability read on LCSC 2026-11-07)

| Candidate | Bands / PHY (datasheet) | Fit to verified targets | LCSC | Decision |
|---|---|---|---|---|
| **TI CC1352R1F3RGZR** | 2360–2500 MHz and sub-GHz 287–351 / 359–527 / 861–1054 MHz (and others); BLE 5.2 (1M, 2M, Coded), IEEE 802.15.4, "proprietary FSK-based formats"; BLE 1M sensitivity −97 dBm, saturation > +5 dBm; +5 dBm (2.4 GHz) / +14 dBm (sub-GHz) max; VQFN-48 7 × 7 | covers SoluM (2 MHz plan, BLE-like GFSK), Hanshow (GFSK, 0.5 MHz grid: needs proprietary mode, fine synthesiser assumed [H]), older SoluM ZigBee (802.15.4), and a sub-GHz port if a target appears | C2151581, 1,030 in stock, US$5.61 | **selected** |
| TI CC2652R1F | 2.4 GHz only, same PHY set as above | 2.4 GHz targets only | C779472, 0 in stock | rejected (stock, no sub-GHz) |
| TI CC2500 | 2400–2483.5 MHz, data rate up to 500 kBaud [DS SWRS040C] | cannot do BLE 1 Mbit/s; no 802.15.4 | C57494, 9,351 in stock, US$1.69 | rejected (cannot cover the SoluM PHY) |
| TI CC1101 | 300–348 / 387–464 / 779–928 MHz, up to 600 kbps [DS SWRS061I] | sub-GHz only | C29953, 9,767 in stock, US$1.95 | not needed (CC1352R has a sub-GHz port) |
| **TI TRF7970A** | 13.56 MHz; ISO 14443 A/B, ISO 15693, ISO 18092 (NFCIP-1), FeliCa / NFC-F 212/424 [DS SLOS743M] | NFC on SoluM Newton Pro is "FeliCa, NFC Forum Type 3" [MFR]; Pricer offers NFC [MFR] | C117004, 19,086 in stock, US$2.95 | **selected** |

**One IC is not assumed to do everything.** The CC1352R covers 2.4 GHz and sub-GHz RF only. NFC needs the TRF7970A. Pricer's infrared link needs an optical front end.

Frequency compatibility is not protocol compatibility. Protocol support depends on the CC1352 firmware and is [U] until captures exist (section 3).

---

## 3. Protocol / frequency compatibility matrix (verified items only)

| Family | Verified band | Modulation / PHY (public) | Known constraints | Required transceiver capability | Antenna | Protocol documentation |
|---|---|---|---|---|---|---|
| **SoluM Newton S-Label** (EL029H3WRT, FCC 2AFWN-EL029H3WRT) | 2402–2480 MHz [FCC] | GFSK; 40 channels at 2 MHz spacing; 6 dB bandwidth 0.708 MHz, 99 % bandwidth 1.05 MHz; 3.59 dBm; metal antenna 0.36 dBi [FCC test report] | the channel plan and bandwidth are consistent with a BLE 1 Mbit/s PHY [H]. SoluM sheets describe "BLE physical layer and SOLUM proprietary protocol" [S, from search summary, sheet not read in full] | 2.4 GHz GFSK ~1 Mbit/s, 2 MHz channel steps, flexible sync word / packet format | 2.4 GHz | proprietary; not publicly documented [U] |
| **SoluM Newton Pro** | 2.4 GHz [MFR spec sheet 28.11.2024] | NFC: FeliCa, NFC Forum Type 3 [MFR] | — | TRF7970A NFC-F 212/424 | NFC coil | NFC Type 3 is a public standard; the ESL application layer is [U] |
| **SoluM S-Label (older)** | 2.4 GHz, "ZigBee" [S, FCC listing summary] | IEEE 802.15.4 assumed [H] | — | 802.15.4 O-QPSK 250 kbps | 2.4 GHz | standard PHY/MAC; application layer [U] |
| **Hanshow Nebular Plus-266F** (FCC 2BPF3-NP1-266F) | 2402–2480 MHz [FCC grant] | GFSK; 157 channels at 0.5 MHz spacing; 20 dB bandwidth 0.558–0.591 MHz; PCB antenna −0.70 dBi; "SRD 2.4G" [FCC test report, DEKRA 25A0445R] | the 0.5 MHz grid needs a synthesiser with < 0.5 MHz resolution. Bandwidth suggests a data rate below 1 Mbit/s [H] | 2.4 GHz GFSK, programmable rate and deviation, 0.5 MHz channel grid | 2.4 GHz | proprietary [U] |
| **Pricer** (SmartTAG family) | near-infrared optical [MFR]; 940 nm, 1.25 MHz carrier, PP4/PP16 [S Furrtek; code in PrecIR/TagTinker] | pulse-position modulation [S] | "rapid flashes" from ceiling transmitters [MFR]; uplink carrier 1.245 MHz [S] | 940 nm emitter with ≥ 1.25 MHz modulation; photodiode receiver with bandwidth > 1.25 MHz | optical window | partially reverse-engineered publicly (Furrtek, PrecIR); not official |
| **Pricer NFC** | 13.56 MHz [MFR: "cloud active NFC"] | [U] which NFC type | for interaction, not the label update path [MFR] | TRF7970A | NFC coil | [U] |
| **Sub-GHz ESL** | none of SoluM / Hanshow / Pricer verified on sub-GHz. Furrtek lists DisplayData at 920 MHz [S], not a target here | — | — | CC1352R sub-GHz port (present) | chip antenna (DNP) | — |

**Optical parts [DS]:**
- VSMB10940: λp 940 nm, tr 15 ns, ±75°.
- VEMD10940F: λp 920 nm, 0.23 mm², C_D 4 pF at 0 V, tr 100 ns (RL 1 kΩ).
- Both are fast enough for a 1.25 MHz carrier [CALC: 100 ns rise ≈ 3.5 MHz bandwidth].

Not claimed: any packet format, sync word, data rate, addressing or encryption for any family. Those are [U] until captured with the conducted test ports.

---

## 4. Antenna architecture and placement

Drawing: `RevB/integrated/drawings/rf_zones_shields_antennas.svg`.

| Antenna | Type and source | Location | Keepout | Matching / tuning | Test access |
|---|---|---|---|---|---|
| ESP32 | module PCB antenna | top-left corner; strip 18 × 6 overhangs a 6 × 33 mm notch | Espressif: ≥ 15 mm clear left, right and outward; ≥ 15 mm in all directions inside the housing (recommended) [MFR] | module internal | — |
| 2.4 GHz (CC1352) | PCB inverted-F, exact copy of TI AN043, 15.2 × 5.7 mm [DS SWRA117D: L1 3.94, L2 2.70, L3 5.00, L4 2.64, L5 2.00, L6 4.90, W1 0.90, W2 0.50, D1 0.50, D2 0.30, D3 0.30, D4 0.50, D5 1.40, D6 1.70 mm] | top-right corner, along the top edge (x 64.8–80, y 34.3–40) | 16.2 × 6.7 mm, no copper on any layer except the antenna, no parts | 3 × 0402 π footprint at the feed | U.FL (C598199) with 0R select |
| Sub-GHz (CC1352) | Johanson 0868AT43A0020 chip, 7 × 2 mm, −1.0 dBi peak / −4.0 dBi average [DS v1.8]. A PCB IFA per TI DN023 needs 43 × 20 mm [DS SWRA228C], half the board: rejected | right edge, mid (x 77.5–79.5, y 16–23) | 11 × 13 mm, no copper on any layer | π network footprint (Johanson recommends one) | U.FL with 0R select. **DNP by default**: no sub-GHz target verified |
| NFC | PCB spiral 24 × 12 mm (~0.27 µH at 3 turns, [CALC] ±15 %) | top, x 21–45, y 27–39 | window: no copper L2–L4, nothing on either side | series/parallel C0G matching to TRF7970A; tuning trimmer footprint [A] | test pads for a VNA loop |
| IR (Pricer) | 940 nm LED + photodiode, top-facing | x 22–34, y 0.5–8.5 | enclosure needs an IR-transparent window above [A] | LED current resistor; TIA gain/feedback footprints | test points at the TIA output and the LED gate |

Distances [CHK]:
- ESP32 antenna ↔ 2.4 GHz IFA: 58.8 mm.
- ESP32 antenna ↔ sub-GHz antenna: 71.5 mm.
- 2.4 GHz IFA ↔ sub-GHz antenna: 11.3 mm.
- NFC coil ↔ ESP32 antenna: 15.0 mm.
- NFC coil ↔ 2.4 GHz IFA: 19.8 mm.

**Not finalised (as required):**
- The IFA geometry is the AN043 copy. AN043 asks for the same PCB thickness and material as its reference, which is [U] for this stackup. Final dimensions wait for measurement on the real ground plane and enclosure.
- Johanson notes that matching values on a customer board differ from its evaluation board.
- The Johanson datasheet recommends corner placements. The corners are taken by the ESP32 antenna, USB-C, the 2.4 GHz IFA and the cable/storage edge, so the mid-edge position is a deviation [DS] that must be measured.

**Measurement strategy (all [MEAS] still to do):**
1. **VNA, conducted:** S11 of each antenna through the U.FL with the 0R moved, after de-embedding the pigtail. Tune the π networks.
2. **Conducted RF:** CC1352 output and receive sensitivity at the U.FL ports. Spectrum analyser for harmonics: 2.4 GHz × 2/× 3, sub-GHz × 3, NFC × 32/× 64.
3. **Radiated:** relative OTA comparison against a reference 2.4 GHz dongle in a fixed geometry, with the enclosure on and off.
4. **NFC:** resonance and Q with a VNA loop; read range with reference tags.
5. **IR:** photodiode response to a known 1.25 MHz source with an oscilloscope; LED drive waveform.

---

## 5. RF shield compartments

Drawing: `RevB/integrated/drawings/rf_zones_shields_antennas.svg`.

| Zone | Can | Justification | Antenna inside? |
|---|---|---|---|
| Z1 ESP32 | none added | module | no |
| Z2 CC1352R + crystals + matching | removable frame + lid, about 18.5 × 13 mm [A] | sensitive receiver (−97 dBm BLE); keeps REG and digital noise out | no (IFA and chip antenna outside, keepouts excluded) |
| Z3 TRF7970A + matching | removable frame + lid, about 13.5 × 16 mm [A] | 13.56 MHz harmonics into sub-GHz/433 bands (section 9) | no (coil outside) |
| Z4 TPS63802 + inductor (bottom) | removable frame + lid | switching harmonics hit the NFC band and sit near the IR carrier (section 9) | no |
| Z5 IR front end | no can over the optics; TIA guard ring and GND pour | high-impedance photodiode node | — |

All cans sit on a GND via fence. Can part numbers are not selected [U].

---

## 6. Updated 80 × 40 mm top-side placement

Drawing: `RevB/integrated/drawings/placement_top.svg`. Coordinates in mm, origin bottom-left.

**Top blocks:** ESP32, USB, USB_ESD, CHG, STOR, IR, BATT_CONN, NFC_IC, COIL, RF_SOC, UFL24, UFLSUB, ANT24, SUBANT, UI_T. Exact rectangles are in `placement.json`.

**Rule check [CHK]: 0 violations.** The rules are:
1. Outline and both notches respected.
2. 0.5 mm spacing between blocks.
3. Antenna keepouts (all layers) and the coil window free.
4. Nothing on the bottom under the ESP32 or under the RF section.
5. Metal ≥ 15 mm from the ESP32 antenna.
6. Switching regulator ≥ 10 mm from the RF SoC, NFC IC, coil, IR and both antenna keepouts.
7. RF SoC ≤ 6 mm from both antenna feeds.
8. NFC IC ≤ 6 mm from the coil.
9. ESD ≤ 3 mm from USB.
10. Battery connector ≤ 3 mm from the cable notch.

**Fill** (sum of courtyards / block area, `density.txt`) [CALC]:

| Block | Fill |
|---|---|
| RF_SOC | 72 % |
| DIG1 | 67 % |
| STOR | 67 % |
| IR | 67 % |
| UI_B | 69 % |
| REG | 63 % |
| CHG | 62 % |
| DIG2 | 57 % |
| USB_ESD | 52 % |
| NFC_IC | 51 % |
| UI_T | 50 % |

72 % in the RF block is dense for a CC1352 layout. It is the tightest area.

## 7. Updated bottom-side placement

Drawing: `RevB/integrated/drawings/placement_bottom.svg`.

| Bottom block | Content |
|---|---|
| REG | buck-boost under a can |
| DIG1 | expanders and load switches |
| DIG2 | interlock logic |
| UI_B | interlock connector and CC1352 cJTAG pads |

Kept clear on the bottom: under the ESP32, under the RF section (GND only), the coil window and both antenna keepouts.

## 8. Battery cable notch

Drawing: `RevB/integrated/drawings/cable_notch.svg`.

- **Shape:** Edge.Cuts notch on the bottom edge at x 38–42 mm, 4.0 mm wide × 3.0 mm deep, internal corner radii R1.0.
- **Assumption [A]:** two AWG26 UL1007 wires, OD 1.3 mm each (pair 2.6 × 1.3 mm), plus 0.7 mm clearance per side. AWG24 would need about 4.5 mm.
- **Keepout:** 1.0 mm copper/via/part keepout around the notch.
- **Connector:** JST PH 2-pin SMD (S2B-PH-SM4-TB, C295747, 5,925 in stock; KiCad courtyard 9.2 × 10.2 mm) directly above.
- **Cable protection:** heat-shrink over the pair at the edge; the housing needs a matching passage.
- **Clearance:** the notch is ≥ 20 mm from every antenna keepout.

---

## 9. Power and RF coexistence analysis

| # | Aggressor → victim | Analysis | Basis | Mitigation |
|---|---|---|---|---|
| 1 | ESP32 2.4 GHz TX → CC1352 2.4 GHz RX | 58.8 mm separation → free-space loss 15.6 dB at 2.44 GHz. ESP32 +20 dBm → about +4.4 dBm at the CC1352 port (0 dBi both ends): at the CC1352 saturation limit (> +5 dBm) and 101 dB above its BLE sensitivity (−97 dBm) | [CALC] + [DS] | **No simultaneous operation.** The ESP32 radio stays uninitialised (REV A firmware never starts Wi-Fi/BLE). If ever enabled, strict time division with CC1352 receive. Orthogonal antenna orientation helps but is not quantified |
| 2 | CC1352 2.4 GHz TX (+5 dBm max) → ESP32 | about −10.6 dBm at the ESP32 antenna | [CALC] | same time division |
| 3 | CC1352 2.4 GHz ↔ sub-GHz antenna (11.3 mm) | different bands. A 2.4 GHz signal at the 868 port is attenuated by the sub-GHz LPF/matching [A]. Sub-GHz 868 × 3 = 2604 MHz is outside the 2.4 GHz band | [CALC] | LPF on the sub-GHz port; only one CC1352 band active at a time (single radio core [H]) |
| 4 | NFC 13.56 MHz harmonics → sub-GHz RX | 13.56 × 32 = 433.92 MHz; × 64 = 867.84 MHz | [CALC] | no NFC field during sub-GHz receive; EMC filter at the TRF output; can over Z3 |
| 5 | IR LED 1.25 MHz drive → NFC RX | harmonics 10 / 11 = 12.5 / 13.75 MHz, near and inside the NFC sub-carrier band (12.71–14.41 MHz) | [CALC] | no IR transmit during NFC receive; LED loop small; gate resistor slows edges |
| 6 | TPS63802 switching → NFC, IR RX, CC1352 | fsw 1.4 / 1.6 / 2.1 MHz typical [DS]; harmonics 8–10 sweep the NFC band. The IR carrier (1.25 MHz) is 0.15–0.85 MHz from fsw; PFM varies the frequency further | [DS] + [CALC] | REG ≥ 10 mm from those blocks [CHK], under a can; force PWM mode (MODE pin [DS]) during IR receive; LC filter on 3V3_RF [A] |
| 7 | Digital (SPI, USB, I2C) → RF | no digital under the RF section on the bottom [CHK]. SPI runs to TRF7970A and the flash, not under the CC1352 | layout rule | route on L4/L3 away from Z2, GND fence |
| 8 | ESP32 40 MHz crystal harmonics | 40 × 60 / 61 / 62 = 2400 / 2440 / 2480 MHz | [CALC] | module internal; keep its traces short |
| 9 | Power | CC1352 RX 6.9 mA / TX 0 dBm 7.1 mA at 2.4 GHz, TX +14 dBm 24.9 mA at 868 MHz [DS]; TRF7970A and the IR LED (up to 65 mA DC, 130 mA peak [DS]) on separate gated rails. The 3V3_RF LDO (TLV755P, 500 mA) has margin [DS] | [DS] | IR LED rail sized for pulses; bulk capacitor near the LED [A] |
| 10 | Shields vs antennas | no can covers an antenna or its keepout [CHK] | layout | — |

---

## 10. Updated BOM (new or changed lines; availability read on LCSC 2026-11-07)

| Function | Part | Package | Datasheet | LCSC / stock / price (1 pc unless stated) |
|---|---|---|---|---|
| RF SoC | TI CC1352R1F3RGZR | VQFN-48 7 × 7 | SWRS196I [DS] | C2151581 / 1,030 / US$5.61 |
| NFC | TI TRF7970ARHBR | VQFN-32 5 × 5 | SLOS743M [DS] | C117004 / 19,086 / US$2.95 |
| Sub-GHz antenna (DNP) | Johanson 0868AT43A0020E | 7 × 2 mm | Johanson v1.8 [DS] | C3284550 / 203 / US$1.33 |
| 2.4 GHz antenna | PCB IFA, TI AN043 | copper | SWRA117D [DS] | — |
| RF test ports × 2 | Hirose U.FL-R-SMT-1(01) | SMD | (not read) | C598199 / 6,866 / US$1.26 |
| IR emitter | Vishay VSMB10940 | SMD 3 × 2 | Vishay [DS] | C4749241 / 1,775 / US$0.57 |
| IR photodiode | Vishay VEMD10940F | SMD | Vishay [DS] | C3211032 / 1,013 / US$0.41 |
| IR TIA | TI OPA356AIDBVR, 200 MHz GBW, 2.5–5.5 V | SOT-23-5 | SBOS212A [DS] | C183100 / 3,002 / US$1.39 |
| Battery connector | JST S2B-PH-SM4-TB(LF)(SN) | SMD right-angle | (not read) | C295747 / 5,925 / US$0.23 (5+) |
| Storage | GigaDevice GD25Q32ESIGR | SOP-8 208 mil | GD25Q32E Rev 1.1 [DS] | C2832998 / 25,756 / US$0.84 |
| Load switch × 3 | TPS22918DBVR | SOT-23-6 | SLVSD76C [DS] | C131941 (REV A, stock not re-read) |
| GPIO expander × 2 | TCA9555PWR | TSSOP-24 | SCPS200E [DS] | C465732 (REV A, stock not re-read) |
| CC1352 crystals | 48 MHz and 32.768 kHz | 2520 / 3215 | requirement from CC1352 [DS]; parts not chosen | — |
| IR LED switch | N-MOSFET (e.g. AO3400) | SOT-23 | not chosen | — |
| Shield cans × 3 | frame + lid | — | not selected [U] | — |

Unchanged lines (ESP32, USB-C, ESD, charger, buck-boost, LDOs, supervisor, dead-man, gates) are as in `REV_B_FEASIBILITY.md` section 8.

**Removed against the previous REV B:** JST SM15B ×2, SMA ×2, microSD.

---

## 11. Pin allocation and bus conflict analysis

**ESP32-C3 (15 usable GPIOs, all allocated):**

| GPIO | Function | Note |
|---|---|---|
| 0 | SPI_SCK | |
| 1 | SPI_MOSI | |
| 3 | SPI_MISO | |
| 4 | TRF_CS | was RSSI ADC in REV A (removed) |
| 5 | FLASH_CS | 10 k pull-up |
| 2 | I2C_SCL | strapping pin, 4.7 k pull-up |
| 8 | I2C_SDA | strapping pin, 4.7 k pull-up |
| 6 | EXP_INT | shared INT of both TCA9555 |
| 7 | WDI | supervisor pulse |
| 9 | BOOT button | strapping |
| 10 | ARM | interlock |
| 18 / 19 | USB D− / D+ | console over USB-Serial-JTAG |
| 20 / 21 | UART RX / TX to CC1352 | UART0 pins |

**TCA9555 #1 (0x20):** CC1352_RESET_N, CC1352_BOOT, TRF_EN, TRF_IRQ (in), RF_PWR_EN_CC1352, RF_PWR_EN_TRF, IR_PWR_EN, INTERLOCK_OK (in), 2 LEDs, spares.

**TCA9555 #2 (0x21, A0 high):** PERMIT (in), WDO (in), ENOUT (in), 3 rail-sense inputs, LOOP_OK and ENCL_OK read-back (in), FLASH_WP#/HOLD#, 2 LEDs, spares.

**CC1352R (28 DIOs, any peripheral on any GPIO [DS]):** UART to ESP32, IR LED PWM (timer), IR RX into a comparator/timer capture, cJTAG (TMS/TCK), ROM-bootloader backdoor pin [U: pin set in CCFG], 2 spare test points. RF ports have fixed pins [DS].

| Bus | Conflict | Severity | Mitigation |
|---|---|---|---|
| SPI (flash + TRF7970A) | The ESP-IDF external-flash driver serialises with the SPI bus lock. A sector erase is 45 ms typical / 300 ms max [DS]. If the driver holds the bus while polling, TRF7970A access is blocked that long [U, behaviour to verify]. NFC transactions have tight timing | medium | dedicated storage task; erase only when NFC is idle (application-level arbiter); pre-erase during idle; program in 256 B pages (shorter); GD25Q32E program/erase suspend (75H/7AH) exists [DS] |
| SPI modes | TRF7970A SPI timing/mode requirements differ from the flash [U, check datasheet section] | low | per-device SPI configuration in IDF |
| I2C | two TCA9555, no other devices | low | 400 kHz; INT shared on GPIO6 |
| UART0 | UART0 also prints ESP32 ROM boot messages at reset (GPIO8 / eFuse control [DS]), which the CC1352 will receive | low | framed host protocol with CRC; CC1352 ignores pre-sync bytes; or burn the ROM-print eFuse |
| Interrupt latency | TRF_IRQ and CC1352 events go through the TCA9555 INT plus I2C (~0.1–0.3 ms [A]) | medium for NFC | TRF FIFO buffering; if insufficient, move TRF_IRQ to GPIO9 after boot (not recommended: strapping pin) or re-assign TRF_CS to the expander |
| Safety supervisor | flash work in its own task; the supervisor never touches SPI | — | as in WATCHDOG_TASK_HEALTH_MATRIX.md |

---

## 12. Risk register

| ID | Risk | Likelihood | Impact | Evidence level | Mitigation / next step |
|---|---|---|---|---|---|
| R1 | Hanshow 0.5 MHz grid / proprietary PHY not reproducible on the CC1352 proprietary mode | medium | high | [H] | conducted capture with a known tag; check synthesiser resolution and data-rate limits in the TI technical reference manual (not read) |
| R2 | SoluM protocol on a BLE PHY but non-standard framing | medium | medium | [H] | capture at the U.FL; compare with the BLE 1M PHY |
| R3 | ESP32 ↔ CC1352 2.4 GHz coupling (15.6 dB free-space) | high if both radios run | high | [CALC] | time division; ESP32 radio off by default |
| R4 | AN043 IFA detuned by stackup, ground size, enclosure | high | medium | [DS] note | π network, VNA tuning, iterate |
| R5 | Sub-GHz chip antenna at mid-edge, 3.6 mm from USB-C, against Johanson's corner recommendation | medium | low (DNP) | [DS] + [CHK] | only populate if a sub-GHz target is verified; then measure |
| R6 | RF block 72 % filled | medium | medium | [CALC] | component-level placement next; 0201 passives in matching if needed |
| R7 | NFC coil 24 × 12 mm small, near the ESP32 antenna (15 mm) | medium | medium | [CALC] | read-range measurement; FPC coil option |
| R8 | Pricer IR physical layer details disputed between sources (PP4 timing) | medium | medium | [S] | scope capture of a real transmitter/tag |
| R9 | SPI bus held during flash erase blocks NFC | medium | medium | [U] | storage arbiter; measure |
| R10 | Buck-boost PFM noise near the IR carrier | medium | medium | [DS] + [CALC] | forced PWM during IR receive; can |
| R11 | Shield cans not selected; fit and height unknown | medium | low | [U] | choose from the fab's library; reserve frame footprints |
| R12 | Battery cable size assumed | medium | low | [A] | confirm with the user's battery |
| R13 | Housing ≥ 15 mm around the ESP32 antenna (Espressif recommendation) | high | medium | [MFR] | enclosure decision |
| R14 | Regulatory: transmit-capable radios (+5 / +14 dBm) | — | — | [DS] | transmit only with interlock armed and only for authorised testing of owned devices; no ESL command generation in firmware (existing policy) |
| R15 | CC1352 needs its own firmware (TI SDK) and an update path (ROM bootloader over UART) | certain | medium | [DS] | plan firmware; keep cJTAG pads |

---

## 13. Does it fit 80 × 40 mm?

At block level, yes: 0 rule violations [CHK], with no change to the ESP32 keepout, the L2 plane (only the coil window is void), RF separation or switching-regulator spacing.

**Two physical limits to state plainly:**
1. **A sub-GHz PCB antenna does not fit.** The TI DN023 868/915 MHz IFA needs 43 × 20 mm plus ≥ 5 mm clearance [DS], i.e. more than half the board. Correction: a chip antenna (7 × 2 mm, −4 dBi average [DS]) in an 11 × 13 mm keepout, not populated until a sub-GHz target is verified. If a sub-GHz target appears and the chip antenna proves inadequate, the justified fix is a larger board (the IFA plus its 5 mm clearance adds roughly 25 mm in one direction, about 80 × 65 mm [CALC, rough]), not squeezing it in.
2. **Two 2.4 GHz radios on one 80 mm board cannot be isolated by distance** (15.6 dB [CALC]). Correction: time division, enforced in firmware. Hardware cannot provide 100 dB isolation at this size.

**Not production-ready.** Everything above is datasheet review, calculation and a geometric rule check. Nothing is simulated electromagnetically, routed or measured.
