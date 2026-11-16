> SUPERSEDED for the RF architecture by REV_B_INTEGRATED_RF.md (2026-11-07): plug-in RF modules (J4/J5) and edge SMAs are removed. Stackup, impedance, storage, power and interlock content below still applies.

# NIGHTHAWK REV B — 80 × 40 mm placement and RF feasibility study

Status: block-level placement feasibility only. No schematic, no PCB file, no routing. REV A is unchanged.

Evidence labels used throughout:
- **[DS]** a manufacturer document read in this session.
- **[WEB]** a manufacturer web page read in this session.
- **[CALC]** a hand or script calculation (scripts in `RevB/tools/`).
- **[SIM]** a numerical model run here: the 2D field solver and the placement checker.
- **[A]** an assumption.
- **[U]** unverified.
- **[MEAS]** physical measurement. There are none.

## 0. Verdict

- **80 × 40 mm is feasible at block level** without touching the antenna keepout, L2 ground continuity or RF separation. The placement satisfies every encoded rule (section 1.2): 0 violations [SIM].
- **Storage (user decisions, 2026-11-07):** the microSD socket is removed (it had no legal position: an exhaustive 0.5 mm grid search over both sides and both rotations found none). It is replaced by a soldered SPI NOR flash costing at most US$1, with lower capacity accepted (section 1.4).
- **Other limits:** several items are at their limit rather than comfortably inside it (section 9).
- **Pending validation:** the cell dimensions are inferred, not taken from a datasheet. The 15 mm housing clearance has consequences for the enclosure that must be resolved before this can be called a "clean working board".

## 1. Dimensioned placement proposal (origin = bottom-left corner, x → 80, y → 40, mm)

### 1.1 Blocks (`RevB/tools/manual_d.json`)

| Block | Side | x range | y range | Content |
|---|---|---|---|---|
| ESP32 | Top | 6.0–20.0 | 22.0–40.0 | ESP32-C3-WROOM-02-N4 body; antenna strip 18 × 6 hangs over the notch (x 0–6) |
| Notch | — | 0–6 | 7–40 | board removed under and beside the antenna (keepout) |
| USB | Top, both sides (THT shell) | 72.7–80 | 0–9.4 | USB-C, opening on the right edge (diagonal to the ESP32) |
| USB_ESD | Top | 64.0–71.0 | 12.6–18.6 | TPD2E2U06, CC resistors, PTC, VBUS caps |
| CHG | Top | 71.5–80 | 10.0–17.5 | BQ24074 linear charger (heat source; ≥ 2 mm outside the cell footprint) |
| REG | Top | 58.0–70.0 | 19.5–31.5 | TPS63802 buck-boost + 0.47 µH, 2 × TLV755P; removable can |
| COIL | Top (window on all layers) | 21.0–45.0 | 1.0–13.0 | NFC coil 24 × 12; L2–L4 copper void, no parts on either side |
| NFC_IC | Top | 21.0–36.0 | 13.5–23.5 | TRF7970A, 27.12 MHz crystal, matching network, EMC filter |
| DIG1 | Top | 36.5–57.5 | 13.5–27.5 | TCA9555 × 2, TPS22918 × 2, pull-ups/downs |
| DIG2 | Bottom | 6.0–20.0 | 0–21.5 | TPS3823, TPS3431, SN74LVC1G74, SN74LVC1G08 × 6 |
| UI | Top | 40.5–57.5 | 28.0–40.0 | 2 buttons, 4 LEDs, interlock connector (JST SH 4) |
| STOR | Top | 8.0–20.0 | 0.5–8.5 | SPI NOR flash GD25Q32ESIGR (SOP-8 208 mil) + 100 nF, 1 µF, CS#/WP#/HOLD# pull-ups, SCLK series R; 13.5 mm from the module, 13.6 mm from the antenna |
| JST_M1 | Top | 21.0–39.8 | 33.4–40.0 | RF module 1 interface, JST SH 15, top edge |
| JST_M2 | Top | 73.4–80 | 19.5–38.3 | RF module 2 interface, JST SH 15, right edge |
| SMA_TEST | Top, both sides (edge) | 50.0–58.0 | 0–12.1 | edge SMA, bottom edge |
| SMA_IN | Top, both sides (edge) | 58.5–66.5 | 0–12.1 | edge SMA, bottom edge |
| BATT | Bottom | 29.5–80 | 19.5–40.0 | cell envelope 50.5 × 20.5 (max, [A]) |
| BATT_CONN | Bottom | 22.0–27.8 | 33.5–40.0 | battery connector at the cell's lead end (type [U]) |

**Footprint sizes.** Courtyard sizes come from the KiCad 10 libraries: SMA 14.72 × 8.00 (12.1 mm inside the edge), JST SH 15 18.80 × 6.56, USB-C 10.64 × 9.42, microSD 15.70 × 17.70, TSSOP-24 7.70 × 8.30, QFN-32 6.26 × 6.26, QFN-16 4.26 × 4.26, SOT-23-5 4.10 × 3.40, 0402 1.82 × 0.92, 0603 2.96 × 1.46. Package bodies for parts not in the library come from their datasheets [DS].

### 1.2 Rules encoded in the checker (`RevB/tools/feasibility.py`; result 0 violations)

1. Inside 80 × 40 minus the notch; 0.5 mm between blocks on the same side. SMAs and the USB shell occupy both sides.
2. Nothing on the bottom under the ESP32 module.
3. Battery ≥ 15 mm from the antenna strip [WEB, Espressif].
4. NFC coil window: no block within 0.5 mm on either side.
   - Battery ≥ 3 mm from the coil; connectors ≥ 5 mm from the coil [A].
   - Coil ≥ 15 mm from the antenna [A, same spirit as the Espressif 15 mm].
5. Switching regulator spacing [A]:
   - ≥ 10 mm from the coil;
   - ≥ 25 mm from the antenna;
   - ≥ 6 mm from the RF ports;
   - ≥ 3 mm from the module connectors on the same side;
   - ≥ 10 mm from the NFC IC.
6. Linear charger not within 2 mm of the cell footprint (thermal) and ≤ 12 mm from USB.
7. RF ports: ≥ 30 mm from the antenna, ≥ 6 mm from USB, on a board edge.
8. Module connectors and microSD ≥ 15 mm from the antenna and flush with an edge.
9. Battery connector ≤ 3 mm from the cell.

The numeric spacings marked [A] are engineering judgement, not datasheet requirements. Changing them changes the result.

### 1.3 Density inside blocks [CALC] (`density_output.txt`)

| Block | Area mm² | Sum of courtyards mm² | Fill |
|---|---|---|---|
| USB_ESD | 42 | 23 | 54 % |
| CHG | 64 | 39 | 62 % |
| REG | 144 | 75 | 52 % |
| NFC_IC | 150 | 107 | 72 % |
| DIG1 | 294 | 179 | 61 % |
| DIG2 | 301 | 159 | 53 % |
| STOR | 96 | 64 | 67 % |
| UI | 204 | 117 | 58 % |

72 % in the NFC block is dense for a matching network; it is the tightest area.

### 1.4 Embedded storage (replaces the microSD socket; cost limit US$1)

**Choice: GigaDevice GD25Q32ESIGR**, 32 Mbit (4 MB) SPI NOR flash [DS: GD25Q32E datasheet Rev 1.1, 2020-04-15, LCSC copy].

| Item | Value | Source |
|---|---|---|
| Package | SOP-8 208 mil, body 5.23 × 5.28 mm, 7.90 mm over leads; KiCad SOIC-8_5.3x5.3mm_P1.27mm courtyard 9.3 × 5.8 mm | [DS], KiCad library |
| Pinout | 1 CS#, 2 SO (IO1), 3 WP# (IO2), 4 VSS, 5 SI (IO0), 6 SCLK, 7 HOLD# (IO3), 8 VCC | [DS Table 1] |
| Supply | 2.7–3.6 V; program/erase current 15 typ / 25 mA max (−40 to 85 °C table) | [DS] |
| Erase / endurance | sector 4 kB: 45 ms typ, 300 ms max; 100,000 cycles min | [DS] |
| Note | CS# must be driven high and never float after power-on → 10 kΩ pull-up | [DS] |
| LCSC | C2832998, stock 25,756, US$0.8433 (1 pc), 0.7262 (10+), 0.4093 (500+), read 2026-11-07 | LCSC search result page |

**Firmware impact (REV B):**
- The SD-card path (`sdspi`) is replaced.
- Checked in the local ESP-IDF v5.4 source:
  - `spi_bus_add_flash_device()` attaches a flash to an already initialised SPI bus, so the bus stays shared with the module connectors;
  - `esp_partition_register_external()` exposes it as a partition;
  - `CONFIG_SPI_FLASH_SUPPORT_GD_CHIP` exists.
- A wear-levelled FAT or LittleFS then sits on that partition.
- Nothing has been compiled or run for this yet.
- An external flash on SPI2 is not expected to stall the CPU cache the way internal-flash writes do. That is relevant to the dead-man timer jitter, and is unverified.

**Wiring:** CS# on GPIO5 (REV A `SD_CS`). WP# and HOLD# pulled high (single-bit SPI). SPI_SCK/MOSI/MISO shared. `SD_CD` is dropped and TCA9555 P13 becomes free.

**Trade-offs:**
- 4 MB instead of a card: about 70,000 CSV lines of 60 bytes [CALC];
- not removable; logs leave the device over USB.

**Alternatives checked on 2026-11-07:**

| Part | LCSC | Stock | Price (1 pc) | Notes |
|---|---|---|---|---|
| CS Semiconductor CSNP1GCR01-BOW SD NAND | C2691593 | 3349 | US$7.88 | over the US$1 limit; datasheet read |
| Winbond W25Q64JVSSIQ | C179171 | 3 | US$1.94 | over the limit |
| GD25Q32ESIG | C2685733 | — | US$1.13 | same die, over the limit at 1 pc |
| XTX XT25F32B | — | — | — | "not available / not recommended for new designs" |
| The ESP32-C3-WROOM-02-N4's own 4 MB flash | — | — | US$0 | rejected as the primary store: internal-flash erases disable the cache and can stall the supervisor (the 170 ms dead-man margin) |

## 2. Top and bottom placement drawings

- `RevB/drawings/placement_top.svg`
- `RevB/drawings/placement_bottom.svg`

PNG copies sit next to them. The drawings show placement blocks with their coordinates, not individual footprints.

## 3. Four-layer stackup

Drawing: `RevB/drawings/stackup.svg`.

JLCPCB JLC04161H-7628, 1.6 mm [stackup values as used in REV A]:
- L1 1 oz
- prepreg 7628, 0.2104 mm, εr 4.4
- L2 0.5 oz
- core 1.065 mm, εr 4.6
- L3 0.5 oz
- prepreg 0.2104 mm
- L4 1 oz

Layer roles:
- **L1:** components, RF, critical signals, GND pour.
- **L2:** continuous GND. The only cut is the NFC coil window, which no RF or high-speed trace crosses.
- **L3:** power planes and secondary signals, GND fill elsewhere. Espressif recommends GND under RF and the crystal on this layer too [WEB].
- **L4:** digital/auxiliary signals, bottom parts, GND fill.

RF trace impedance, 2D finite-difference quasi-static solve [SIM] (`zsolve.py`, `validation_air.txt`):

| Geometry on L1 over L2 | Z0 |
|---|---|
| Microstrip 0.36 mm, no mask | 50.3 Ω (grid 0.005 mm; 49.9 Ω at 0.01 mm) |
| Microstrip 0.36 mm, 20 µm mask (εr 3.8 [A]) | 49.3 Ω |
| CPWG 0.30 mm, gap 0.15 mm | 49.3 Ω |

- **Solver check:** an air microstrip with w/h = 1 gives 123.1 Ω against the 126.6 Ω closed-form value for zero thickness, i.e. −2.8 %. Part of that is the finite strip thickness.
- **Closed form vs solver:** Hammerstad without a thickness term gives 53.6 Ω for 0.36 mm.
- **Before ordering:** confirm with JLCPCB's controlled-impedance calculator.
- **USB:** ESP32-C3 USB is full speed. Espressif asks for 90 Ω ±10 % differential and a continuous reference [WEB]. Geometry to be solved at layout time.

## 4. RF zoning and shield cans

Drawing: `RevB/drawings/rf_zoning_shields.svg`.

| Zone | Content | Can | Why |
|---|---|---|---|
| Z1 | ESP32 module, 2.4 GHz | none | never cover the antenna strip; nothing in the clearance |
| Z2 | NFC IC + matching | optional, over TRF7970A only, never over the coil | fit only if measured coupling requires it |
| Z3a | Linear charger | none | heat, no switching |
| Z3b | TPS63802 + inductor | yes, removable frame + lid | 1.4–2.1 MHz switching with harmonics sweeping the NFC band (section 7) |
| Z4/Z5 | Module interfaces | no can (cable exits) | filtering on the supply and data lines at the connector instead |
| Z6 | SMA-to-SMA test path | no can | CPWG with a via fence |

**Shielding estimate** [CALC]: rule-of-thumb aperture SE = 20 log(λ/2L) − 10 log(N). This is not a simulation.

| Frequency | Single 2 mm slot | 10 × 3 mm openings |
|---|---|---|
| 2.44 GHz | 30 dB | 16 dB |
| 868 MHz | 39 dB | 25 dB |
| 434 MHz | 45 dB | 31 dB |

A can only helps if its lid contacts are dense. Can part numbers are not selected [U].

## 5. Antenna keepout

Drawing: `RevB/drawings/antenna_keepout.svg`. Source [WEB]: Espressif ESP Hardware Design Guidelines, ESP32-C3, "Keepout Zone for ESP32-C3 Module's Antenna". The figure was read directly.

- **Clearance area:** antenna strip 6 mm deep; clearance area at least 15 mm to the left, to the right and outward of the antenna.
- **Overhang preferred:** place the antenna outside the base board with the feed point near the edge. Otherwise cut the board away on both sides of and below the antenna.
- **Ground near the antenna:** sufficient ground copper and dense ground vias near the antenna.
- **Housing:** at least 15 mm clearance in all directions inside the housing (recommended).
- **How applied here:** the 18 × 6 mm strip overhangs the board (notch x 0–6, y 7–40). The ESP32 sits in the top-left corner with the antenna toward the left edge. The datasheet land pattern labels the "Antenna Area" with the 6 mm depth [DS v1.7 Fig. 11-1, text-extracted].
- **Battery and coil:** the cell is 23.5 mm from the strip and the coil 15.0 mm.

## 6. Battery mechanical envelope

Drawing: `RevB/drawings/battery_envelope.svg`.

**PX402050 / PX502050: no datasheet was found [U].** Sizes are inferred from the PowerXtra pattern T-W-L, which matches two published sheets:
- PX505060 = 5.0 × 50 × 60 mm (±0.5 mm on L and W);
- PX502030: width max 20.5 mm, thickness max 5.02 mm.

Inferred envelopes: PX502050 ≈ 5.0 × 20 × 50 mm, PX402050 ≈ 4.0 × 20 × 50 mm, planned as 50.5 × 20.5 (max). Capacity is not known.

- **Placement:** bottom side, x 29.5–80, y 19.5–40.
- **Height:** 0.3 mm foam + cell + 0.5 mm swelling allowance [A] → 6.0 mm below the PCB (PX502050). Total about 10.9 mm with the 3.3 mm top parts; about 9.9 mm with PX402050.
- **Leads and connector:** leads go to a connector at the cell's left end (x 22–27.8). Connector type and lead length depend on the delivered cell [U].
- **Protection module:** a PCM may add length [U]. The cell's maximum envelope is flush with the right and top board edges, so any length beyond 50.5 mm breaks this placement.
- **Retention:** foam tape plus a housing rib; nothing clamps over the cell; a 1 mm keep-free border.

## 7. Power integrity and EMC risk analysis

**Rails.** USB 5 V → PTC → ESD → BQ24074 IN. BQ24074 OUT (4.4 V with USB, VBAT without [DS SLUS810N]) → TPS63802 at 3.6 V [A]. From there:
- TLV755P 3.3 V digital (ESP32, logic);
- TLV755P 3.3 V RF → TPS22918 → module rails.

The LDO headroom is 0.3 V; TLV755P dropout at the real load must be checked [U].

| # | Risk | Analysis | Basis | Mitigation in this proposal | Open |
|---|---|---|---|---|---|
| 1 | ESP32 2.4 GHz TX into other receivers | ESP32 TX up to +20 dBm [DS]. Free-space loss at 2.44 GHz is only 12.2 dB at 40 mm and 15.8 dB at 60 mm [CALC]; the reactive near field extends to ~20 mm. Distance alone cannot protect a 2.4 GHz ESL receiver on a module (Hanshow/SoluM ESLs are commonly 2.4 GHz [U for each target]) | [DS]+[CALC] | firmware keeps Wi-Fi/BLE uninitialised (REV A firmware); RF ports ≥ 30 mm from the antenna; modules on cables | measured isolation; time-division if the ESP32 radio is ever enabled |
| 2 | ESP32 40 MHz crystal harmonics | 40 × 60/61/62 = 2400/2440/2480 MHz, in band | [CALC] | the crystal is inside the module; keep module-side traces short; no long lines near the module | measure with a 2.4 GHz module receiving |
| 3 | Buck-boost harmonics in the NFC band | TPS63802 switches at 2.1 MHz (boost), 1.4 MHz (buck-boost), 1.6 MHz (buck), typical, no load [DS]. Harmonics 8–10 hit 12.7–14.4 MHz; PFM varies the frequency | [DS]+[CALC] | REG ≥ 10 mm from the coil, under a can; forced-PWM mode available [DS] | measure the NFC noise floor with REG on |
| 4 | NFC carrier harmonics | 13.56 MHz × 32 = 433.92 MHz (433 ISM centre), × 64 = 867.84 MHz, × 177 = 2400.12 MHz | [CALC] | do not run NFC while a module receives at 433/868 MHz; filter at the TRF output (EMC filter in NFC_IC) | measure harmonic levels |
| 5 | USB SI/ESD | Full speed 12 Mbit/s; TPD2E2U06 1.5 pF typ [DS SLLSEG9C] next to the connector. The mandated diagonal places the pair ~60 mm across the board | [DS]+[WEB] | L1 over L2, GND guard, no vias if possible; ESD before any branch | reserve a routing corridor (not in the block checker) |
| 6 | Ground return | L2 continuous except the coil window. No signal may cross the window; the module and SMA paths run over solid L2 | design rule | coil window placed where only its own feed enters | verify at layout |
| 7 | RF trace impedance | 50 Ω geometry from the field solver (section 3) | [SIM] | CPWG + via fence for SMA_IN → SMA_TEST | JLCPCB impedance confirmation; TDR [MEAS] |
| 8 | Antenna efficiency | Espressif keepout respected; no simulation of the PCB antenna on this board | [WEB] | notch, corner placement, GND vias | OTA / range test; housing effect (section 9, item 8) |
| 9 | NFC coil | 24 × 12 mm, inductance [CALC] 0.16 / 0.27 / 0.37 / 0.45 µH for 2–5 turns (Greenhouse-type sum, ±15 %). TI defers antenna design to an app note not read here | [CALC]+[DS] | coil away from the cell (≥ 3 mm), REG (≥ 10 mm) and the antenna (15 mm) | read range and Q unknown [U] |
| 10 | Shielding | estimates in section 4 | [CALC] | can only over REG | near-field scan |
| 11 | Battery / power noise | the cell sits under REG/DIG1/UI/JST_M2. Linear charger (no switching noise) is off the cell. Charger at 0.5 A from 5 V: P = 1.00 / 0.65 / 0.45 W at VBAT 3.0 / 3.7 / 4.1 V; with RθJA 44.5 °C/W [DS] → +44 / +29 / +20 °C | [CALC] | limit ISET to ~0.3 A unless thermal tests allow more; NTC / TS input to be decided with the cell | thermal measurement |
| 12 | Back-powering of modules | carried over from REV A (FAILURE_MODE_MATRIX row 15) | review | series resistors / buffer at the module connectors (REV B recommendation) | — |

## 8. Preliminary BOM (datasheet references read in this session)

| Function | Part | Package | Datasheet | LCSC |
|---|---|---|---|---|
| MCU + radio | ESP32-C3-WROOM-02-N4 | module 18 × 20 × 3.2 | Espressif datasheet v1.7 [DS] | C2934560 (verified in REV A) |
| Charger + power path | BQ24074 | VQFN-16 3 × 3 | TI SLUS810N [DS] | not checked |
| Buck-boost 3.6 V | TPS63802 | DLA DFN (body per datasheet table 3.0 × 2.0) | TI SLVSEU9D [DS] | not checked |
| Inductor | 0.47 µH, DFE201612E (Toko) or XFL4015-471ME (Coilcraft), as listed by TI | 2.0 × 1.6 / 4 × 4 | TI SLVSEU9D Table 10-2 [DS] | not checked |
| LDO 3.3 V × 2 | TLV75533PDBVR | SOT-23-5 | TI TLV755P [DS] | C404027 (REV A) |
| Load switch × 2 | TPS22918DBVR | SOT-23-6 | TI SLVSD76C [DS] | C131941 (REV A) |
| Supervisor | TPS3823-33DBVR | SOT-23-5 | TI SLVS165O [DS] | C7719 (REV A, grade B) |
| Dead-man timer | TPS3431 | VSON-8 3 × 3 | TI SNVSB66A [DS] | not checked |
| Latch | SN74LVC1G74 | US8 / SM8 | TI SCES794G [DS] | not checked |
| AND gates × 6 | SN74LVC1G08DBVR | SOT-23-5 | TI SCES217AA [DS] | C7666 (REV A) |
| GPIO expander × 2 | TCA9555PWR | TSSOP-24 | TI SCPS200E [DS] | C465732 (REV A) |
| NFC reader | TRF7970A | VQFN-32 5 × 5 | TI SLOS743M [DS] | not checked |
| NFC crystal | 27.12 MHz (or 13.56 MHz) | 3225 | requirement from SLOS743M [DS]; part not chosen | — |
| USB ESD | TPD2E2U06 | SOT-5 DRL 1.6 × 1.2 | TI SLLSEG9C [DS] | not checked |
| USB-C | TYPE-C-31-M-12 | SMT + THT shell | not read (REV A note) | C165948 (REV A) |
| Module connectors × 2 | JST SM15B-SRSS-TB | SMD | KiCad footprint only | C160414 (REV A) |
| RF ports × 2 | Samtec SMA-J-P-H-ST-EM1 | edge mount | not read | C5199907 (REV A) |
| Battery | PowerXtra PX402050 or PX502050, 1S Li-Po | ~4.0/5.0 × 20 × 50 | not found [U] | — |
| Shield can over REG | frame + lid ~14 × 14 × 2.5 mm [A] | — | not selected | — |
| Embedded storage | GigaDevice GD25Q32ESIGR, 32 Mbit SPI NOR | SOP-8 208 mil | GD25Q32E Rev 1.1 [DS] | C2832998 (stock 25,756, US$0.84 / 1 pc, read 2026-11-07) |

## 9. Compromises and items that prevent or threaten 80 × 40 mm

1. **microSD socket: RESOLVED by removal (user decision).** The socket had no legal position. It is replaced by a US$0.84 SPI NOR flash (section 1.4). Consequences:
   - no removable card;
   - logs leave the device only over USB;
   - 4 MB capacity;
   - the storage firmware must be rewritten for SPI NOR.
2. **NFC coil limited to 24 × 12 mm** (about 0.27 µH at 3 turns [CALC]). Smaller than typical reader antennas; read range unknown. Alternative: an external coil on an FPC behind the housing face, with a connector in place of the window.
3. **RF IN is 6.2 mm from the USB-C body**, exactly at the rule limit. Alternative: U.FL connectors with bulkhead pigtails (frees about 2 × 90 mm² and moves the RF ports anywhere).
4. **Battery data is unverified**, and the envelope is flush with two board edges. Any length beyond 50.5 mm (PCM, tabs) breaks the placement. A drawing of the real cell is required. PX402050 saves 1 mm of height for the same footprint.
5. **Charger heat:** 2 mm from the cell, up to 1 W at 0.5 A. Lower the charge current or measure.
6. **2.54 mm headers removed:** interlock and debug through JST SH 4 / pads (a convenience compromise).
7. **USB routing corridor:** about 60 mm diagonal, not reserved by the block checker. Must be shown at layout.
8. **Housing clearance:** Espressif recommends ≥ 15 mm free space around the antenna in all directions inside the housing. That implies an enclosure ≥ 15 mm beyond the left edge and, read literally, also above and below the antenna region. Not resolvable on the PCB; it is an enclosure decision [U].
9. **Spacing rules:** the numeric rules marked [A] in section 1.2 are judgement. Changing them can change feasibility.

Not compromised:
- the Espressif antenna clearance area;
- the L2 ground plane (the only void is the coil window, crossed by nothing else);
- separation of the RF ports from the 2.4 GHz antenna and from the switching regulator;
- nothing under the module.

## 10. What was not done

- No antenna or 3D EM simulation, no SPICE/PI simulation, no thermal simulation.
- No component-level placement, no routing, no schematic.
- No LCSC check for the new parts.
- No physical measurement of anything.

Next steps:
1. Settle the NFC coil approach (item 9.2). The storage question is settled: GD25Q32E SPI NOR.
2. Obtain the cell drawing.
3. Component-level placement with routing corridors, re-running the checker.
4. Only then routing.
