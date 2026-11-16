# Design review (REV A)

## Results of automated checks
| Check | Result |
|---|---|
| ERC (kicad-cli 10.0.6, all severities) | 0 violations |
| DRC (kicad-cli, all severities, zones refilled) | 0 errors, 0 unconnected, 3 warnings (USB-C footprint silkscreen crosses board edge) |
| Schematic vs PCB references | 102 = 102 |
| BOM vs CPL | 87 = 87, PASS |
| CPL coordinates vs re-read PCB | 0 mismatches |
| Datasheet pin checks done | ESP32-C3-WROOM-02 (pinout), TPS22918, TPS3823, SN74LVC1G08, TCA9555 (pin tables read in datasheets) |
| Pin checks not done | USBLC6-2SC6, TLV75533, HRO USB-C, Hirose DM3AT detect pins (taken from KiCad libraries, reused from the earlier GNSS board where applicable) |

## Not validated
Nothing has been fabricated, powered, programmed or measured. Firmware was not compiled (ESP-IDF not installed here). The desktop app was syntax-checked only (PySide6 not installed here). ERC returning zero issues was not cross-checked with a deliberately injected fault.

## Findings and risks
1. Autorouted board: USB D+/D- are not length-matched or impedance-controlled (full-speed USB tolerates this, not verified).
2. RF trace is a short manual route but has no ground-via fence beyond the 5 mm stitching grid.
3. All GPIOs are used (15 of 15). Boot strapping: IO8 and IO2 have 4.7k pull-ups (I2C), IO9 10k pull-up.
4. SPI lines connect to module connectors whose modules are unpowered when the interlock is open; leakage through module input protection diodes is possible.
5. TPS3823 reset delay text conflicts between sources (200 ms vs 1.6 s); read the datasheet before firmware tuning.
6. TCA9555 inputs power up as inputs with weak pull-ups; RFx_EN pins have 10k pull-downs on the board, and the AND with ARM keeps the supply off regardless.
7. J7 microSD detect switch polarity (DET_A/DET_B) is from the KiCad symbol; verify against the Hirose datasheet.
8. BOM total is indicative: prices are at different quantity tiers as shown by LCSC on 2026-11-07.

## Recommendations for REV B
Add RF ESD and ground fence once the frequency is known; add Schottky or ideal-diode reverse protection with a stocked part; add dedicated UART pins to the module connector via a larger connector; add a native RF detector once the frequency range is known; consider an SD slot on its own SPI bus.
