# NIGHTHAWK parts verification (LCSC)

Checked 2026-11-07 (prices and stock change daily; re-check before ordering).
Evidence grades: **A** = read by me in the LCSC page in the built-in browser; **B** = reported by a sub-agent from LCSC pages (category summaries or product pages), not re-read by me; **C** = not verified. Datasheet facts for the ESP32 module were read by me from the official Espressif PDF (v1.7).

## 1. MCU module: ESP32-C3-WROOM-02

Datasheet v1.7 (documentation.espressif.com/esp32-c3-wroom-02_datasheet_en.pdf):

| Item | Value |
|---|---|
| Variants (ANT) | -N4 (4 MB quad flash, -40..85 °C), -H4 (4 MB, -40..105 °C), -N8 (8 MB, -40..85 °C); chip rev v0.4 |
| Variants (connector) | 02U-N4 / -H4 / -N8, 18.0 × 14.3 × 3.2 mm, external antenna via connector |
| Size (ANT) | 18.0 × 20.0 × 3.2 mm |
| Supply | 3.0 to 3.6 V |
| Pads | 19 (3V3 1, EN 2, IO4 3, IO5 4, IO6 5, IO7 6, IO8 7, IO9 8, GND 9/19, IO10 10, RXD(GPIO20) 11, TXD(GPIO21) 12, IO18/USB_D- 13, IO19/USB_D+ 14, IO3 15, IO2 16, IO1 17, IO0 18) |
| Usable GPIOs | **15**: GPIO0-10, 18, 19, 20, 21. Flash pins are not exposed |
| Strapping | GPIO2 (floating default), GPIO8 (floating), GPIO9 (weak pull-up). Download boot = GPIO9 low with GPIO2 and GPIO8 high. EN must not float |
| ADC | ADC1: GPIO0-4; ADC2: GPIO5 |
| Antenna keepout | Defined in the datasheet figure and the ESP32-C3 Hardware Design Guidelines; exact dimensions **not yet extracted**. The -02U has no keepout |

LCSC (grade A):

| MPN | LCSC | Stock | Price (1+) | Class |
|---|---|---|---|---|
| ESP32-C3-WROOM-02-N4 | **C2934560** | 13,503 | $3.3224 | Extended |
| ESP32-C3-WROOM-02-H4 | C2944070 | **0** | $3.4206 | Extended |
| ESP32-C3-WROOM-02U-N4 | C2926676 | 2,780 | $3.2658 | Extended |
| 02D-N4 / 02UD-N4 | C2980301 / C2980302 | 0, "Pre/New" | $14.76 | not a datasheet variant I read; ignore |

**Decision:** use ESP32-C3-WROOM-02-N4 (C2934560). The 02U-N4 (C2926676) is an in-stock alternative if an external antenna is wanted. Note the module's PCB antenna conflicts with the brief's goal of keeping the 2.4 GHz radio quiet; the brief only requires that the radio can be disabled in firmware.

**Design consequence (new issue N-015):** only 15 GPIOs, 3 strapping, 2 on USB. The brief needs microSD (4-6), two RF ports (shared SPI 3 + 2 CS + 2 IRQ + resets), UART, I²C, interlock, LEDs, ADC. This will not fit directly: an I²C GPIO expander or shared buses with careful strapping use will be required.

## 2. Other parts

| Function | MPN | LCSC | Stock / price | Grade | Notes |
|---|---|---|---|---|---|
| 3.3 V LDO (digital) | TLV75533PDBVR (TI, SOT-23-5) | C404027 | 93,165; $0.1227 (5+) | A | Enable, soft-start, output discharge; Extended |
| USB ESD | USBLC6-2SC6 (ST, SOT-23-6L) | C7519 | 27,270; $0.1639 (5+) | A | 17 V clamp, 5 A Ipp, -40..125 °C; Extended |
| USB-C receptacle 16-pin | TYPE-C-31-M-12 (Korean Hroparts) | C165948 | 308,460; $0.1736 (5+) | A | SMT, Extended |
| Low-noise LDO candidate | TPS7A2033DQNR (TI, X2SON-4 1×1) | C46459900 | 4,274; $0.3301 (1+) | A (listing only; noise specs not read from the datasheet) | 1×1 mm X2SON is hard to hand-solder; JLC assembly feasibility unverified |
| Low-noise LDO alternative | TPS7A2033YCKR (DSBGA-4) | C42038768 | 245; $0.3476 (5+) | A | BGA, impractical |
| 100 nF 0603 X7R 16 V | CC0603KRX7R7BB104 (Yageo) | C108079 | 1,165,800; $0.0121 (50+) | A | LCSC tags it **Extended** |
| Supervisor/watchdog | TPS3823-33DBVR (TI, SOT-23-5) | C7719 | 55,321; $0.4609 (1+) | B (product page) | Page lists conflicting reset timeouts (1.6 s vs 200 ms): read datasheet |
| Load switch | TPS22918DBVR (TI, SOT-23-6) | C131941 | 70,550; $0.3454 (5+) | B | 1 to 5.5 V, 2 A, -40..105 °C |
| microSD socket | TF-CARD H1.8 (Shou Han) | C7529389 | 66,490; $0.0613 (10+) | B | push-push, card-detect yes, 1.8 mm high |
| Tactile switch | YZA-072-5.0 etc. (YIZHI) | C49108658 | 2,950; $0.0132 (50+) | B | 4-pin, 6×6×5 mm |
| LED red/green | KT-0603R / GL0603UG01 | C2286 / C51933293 | millions | B | white 0603: C51933297 (GL0603UW01), 736,100 |
| 4-pin header | PZ254V-11-04P (XFCN) | C2691448 | 871,880 | B | through-hole 2.54 mm |
| SMA edge-launch | – | **not found** | – | C | search "SMA edge launch" returned only antennas |
| 5.1 k 0603, 10 µF, 1 µF 0603 | – | **not verified** | – | C | the 5.1k search was cut off by a page navigation |
| 2×5 1.27 mm header | – | **not found** in the category page 1 | – | C | |
| AND gate (interlock) | SN74LVC1G08 | **not found** | – | C | |

## 3. Cost note
Parts verified so far are not enough for a BOM total; do not quote one yet.

## 4. Still to verify
SMA edge-launch connector and its datasheet footprint; basic 0603 passives; 10 µF/1 µF; debug and RF expansion connectors (keyed); 2.4-GHz-radio-independent clock/LDO choices; whether JLCPCB offers black mask and the 4-layer stackup (N-003).
