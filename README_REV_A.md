# NIGHTHAWK ESL Security Research Tool, REV A

Portable ESL security research instrument: ESP32-C3-WROOM-02, two modular RF expansion slots, passive RF test path, hardware interlock (default RF off).

Status (2026-11-07): schematic and PCB complete; ERC 0 violations; DRC 0 errors and 0 unconnected (3 silkscreen-edge warnings). Nothing has been fabricated, powered or tested. Firmware is not compiled and the desktop app has not been run. No RF range is claimed.

## Layout
- `Hardware/` KiCad project (`NIGHTHAWK.kicad_pro`, root `NIGHTHAWK.kicad_sch`, 11 sheets, `NIGHTHAWK.kicad_pcb`), `build/` generator scripts (design.py is the single source of parts and nets).
- `Manufacturing/` Gerber, Drill, BOM, CPL, Assembly (PDFs, 3D renders), JLCPCB zip.
- `Firmware/` PlatformIO + ESP-IDF project (CLI over USB, interlock monitor, expander, ADC, microSD, device database). Contains no ESL command generation.
- `Software/desktop_app/` PySide6 companion app.
- `Documentation/` PDFs, BOM.xlsx, CPL.csv, Pin_Assignment.xlsx, ISSUES.md, PARTS_VERIFICATION.md, Research/ (TagTinker, protocol matrix, licence audit), Validation/.

## Rebuild
Run with KiCad's Python: `route.py prep`, `route.py jar 25`, `route.py post`, `route.py silk`, `link_sch.py`; then `gen_sch.py` and `export.py`. Freerouting 2.5.0 is taken from `../build/tools` (symlink).

## Intended use
Owned equipment only, conducted or shielded testing, passive measurement. The firmware refuses to start a session when the hardware interlock is open.
