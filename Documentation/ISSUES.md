# NIGHTHAWK engineering issue tracker

Updated: 2026-11-07. Status: OPEN / BLOCKED / DONE. "Blocked" names what is needed.

## Toolchain (DONE, verified on this Mac)
- DONE: KiCad 10.0.6, `kicad-cli` 10.0.6, `pcbnew` imports in KiCad's Python, `kicad-cli pcb drc` and `sch erc` both exist. Verified by running them 2026-11-07. This clears the gate in `TOOLCHAIN_STATUS.md` for the CLI/Python path (the MCP server was not installed on the Mac; native CLI + Python automation is used instead).
- DONE: Reusable pipeline exists in `../build/` (Freerouting 2.5.0 + JRE in `../build/tools/`) from the GNSS board. Its scripts are 2-layer and GNSS-specific; they need adaptation for a 4-layer board.

## Open issues

| ID | Pri | Status | Issue | Needs |
|---|---|---|---|---|
| N-001 | P0 | DONE | ESP32-C3-WROOM-02-N4 chosen, C2934560, datasheet v1.7 pinout read. See PARTS_VERIFICATION.md | – |
| N-015 | P0 | OPEN | Only 15 usable GPIOs (3 strapping, 2 USB); brief needs more. Plan GPIO expander / bus sharing | Design |
| N-002 | P0 | OPEN | Every other part needs an LCSC number verified from a live LCSC page. **No LCSC number may be written from memory.** Existing GNSS-board numbers in `docs/notlar.md` are re-usable only after re-checking stock | Web access |
| N-003 | P0 | BLOCKED | Pick JLCPCB 4-layer stackup (real dielectric thicknesses, Er) before 50 Ω width calculation. Currently unknown | JLCPCB stackup page (JLC04161H-7628 or other) |
| N-004 | P0 | OPEN | Decide RF expansion connector (keyed, 2 identical ports) and fix pin table. Draft requirement: 3V3, GND, SPI(4), IRQ, 2-4 GPIO, I2C, UART, RST, filtered supply, module-ID. Spec first, part later | Design decision, below |
| N-005 | P0 | OPEN | Hardware interlock logic: default RF-disabled; trips on power-up, MCU reset, firmware hang (watchdog/heartbeat), interlock loop open, enclosure-open, hardware fault. Hardware-only gating of module supply/enable (must not depend on firmware) | Design |
| N-006 | P1 | OPEN | Define what "RF TEST" SMA path is: receive-only/measurement port with DC block + attenuator pad footprints. A generating transmitter is NOT on the board (brief). External lab equipment is controlled via documented interfaces | Design |
| N-007 | P1 | OPEN | "TagTurk" has no documentation read yet. Not covered by earlier research | Research |
| N-008 | P1 | OPEN | Frequencies/modulation for SoluM, Hanshow, Pricer, TagTurk: unknown. Only desk facts exist (see `Research/ESL_PROTOCOL_RESEARCH_MATRIX.md`): Pricer IR 940 nm / 1.25 MHz carrier [stated by Furrtek]; Hanshow 2.4 GHz [stated, unchecked]. Nothing may be declared as verified | Measurements, official docs |
| N-009 | P1 | OPEN | Pricer is IR on the studied family. A 2.4 GHz RF module does not address it. IR daughterboard (see Research/NIGHTHAWK_ARCHITECTURE_UPDATE.md §5) is not in the new brief's connector list; decide whether one RF expansion port can host IR | İlker decision |
| N-010 | P1 | OPEN | Brief says "dark PCB substrate". Mask colour (black/matte black) cost and JLC availability to check; black mask reduces visual inspection and silk contrast | JLC check |
| N-011 | P1 | OPEN | ESP32-C3 USB pins GPIO18/19 and strapping pins (GPIO2/8/9) constrain microSD + two SPI ports + UARTs + ADC. Pin budget must be solved on the verified pinout | N-001 |
| N-012 | P2 | OPEN | Reuse licensing: see `Research/REUSE_AND_LICENSE_AUDIT.md`. Firmware/CLI must not generate third-party ESL commands (brief) | Policy |
| N-013 | P2 | OPEN | Range claim 10-20 m is a target only; link budget needs the real frequency, sensitivity and antenna. No claim until measured | Measurements |
| N-014 | P2 | OPEN | The folder-wide search for "NIGHTHAWK" never finished; the original architecture was not found on disk. This brief is now the source of truth | – |

## Scope honesty

The brief asks for ~20 deliverable groups. Done so far: research docs and toolchain gate. **Not done:** schematic, PCB, routing, BOM/CPL, Gerbers, firmware, desktop app, validation reports. None of these exist yet and none are claimed.

## Status update 2026-11-07 (end of REV A design pass)
DONE: N-001, N-003 (stackup read from JLCPCB), N-004/N-005/N-006 (implemented as connector, AND-gate interlock, passive RF path), N-015 (SD CS moved to native IO5, VMON dropped, expander for module lines). Schematic (11 sheets), PCB (routed), exports, checks, firmware foundation and desktop app written.
OPEN: N-007 TagTurk research, N-008 frequencies (measure), N-009 IR for Pricer (not covered by this board), N-010 black mask check, N-013 range (measure), JLC rotation check, impedance confirmation, firmware compile, app run, datasheet pins for USBLC6/TLV75533/DM3AT, stock re-check.
