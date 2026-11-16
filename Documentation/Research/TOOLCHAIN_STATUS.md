# TOOLCHAIN_STATUS.md (NIGHTHAWK)

Checked: 2026-11-07. Two separate environments were inspected. Do not mix them up.

## Verdict

| Item | Cloud sandbox (Claude Code runs here) | Your MacBook (arm64) |
|---|---|---|
| KiCad | 7.0.11 (apt, installed by me for testing) | 10.0.6 (KiCad.app found, NOT executed) |
| kicad-cli | 7.0.11, works, but no `pcb drc` / `sch erc` | Present (universal binary), NOT run, cannot execute macOS binaries from here |
| pcbnew Python | 7.0.11 on Python 3.12 only | Bundled `pcbnew.py` + `_pcbnew.so` in KiCad's Python 3.9, not imported |
| MCP server | mixelpixx/KiCAD-MCP-Server v2.8.3 (c4761c9) built and registered | Not installed |
| MCP tested | YES (see below) | NO |

The KiCad 10 toolchain on the Mac is unverified. Real design with DRC/ERC should run against KiCad 10, so the Mac install must be tested before PCB work.

## MCP server status

- Registered in Claude Code user config as `kicad` (`claude mcp add --scope user`).
- `claude mcp list`: Connected (real handshake by the CLI).
- Tools appear only in a NEW Claude Code session started after registration.
- Server: `/home/claude/tools/KiCAD-MCP-Server/dist/index.js` (Node 22).
- Python used by server: `/home/claude/tools/kpy312/bin/python` (3.12 venv, system site packages for pcbnew, plus requirements.txt).
- Env: `KICAD_PYTHON`, `PYTHONPATH=/usr/lib/python3/dist-packages`, `KICAD_AUTO_LAUNCH=false`.
- 244 tools exposed. Backend in tests: `swig` (file based, no running KiCad GUI). IPC (live GUI sync) needs KiCad 9+, untested.

## Tests actually run (sandbox, through an MCP client)

| Operation | Result |
|---|---|
| initialize + list_tools | OK, 244 tools |
| create_project | OK, wrote .kicad_pro / .kicad_pcb / .kicad_sch |
| open_project | OK |
| add_board_outline (50x30 mm) | OK, Edge.Cuts geometry present in saved .kicad_pcb |
| save_project | OK |
| add_schematic_component (Device:R) | OK, .kicad_sch grew 215 to 2931 bytes |
| export_gerber | OK, per layer .gbr files written |
| place_component (Resistor_SMD:R_0603_1608Metric) | FAILED: footprint not found, although /usr/share/kicad/footprints exists. Likely library path detection expects KiCad 9/10 layout. Retest on KiCad 10. |
| run_drc | FAILED: server calls `kicad-cli pcb drc`, absent in KiCad 7 |
| run_erc | FAILED: `kicad-cli sch erc` absent in KiCad 7 |

DRC/ERC failures are caused by the old sandbox KiCad 7, not proven server bugs. Footprint failure is unexplained.

## Direct CLI exports (sandbox, KiCad 7)

- PCB to PDF: OK. PCB to STEP: OK. Schematic netlist: failed to load schematic (cause not investigated).
- Not tested: drill, pos, BOM, SVG, 3D render, IPC-2581.

## Alternative MCP evaluated

`kicad-eda-mcp` 0.1.0 (PyPI). Needs `mcp<2` (fails with mcp 2.x: `Server.list_tools` missing). With `mcp 1.30`: starts, 28 router tools, read-only by default (mutations disabled). Not registered.

## Python environment (sandbox)

- System: Python 3.13.18 (default), Python 3.12.3 (needed for pcbnew), Node 22.23.4, uv present.
- `/tmp/venvs/kv` (py3.13): kiutils 1.4.8, kicad-sch-api 0.5.6, kicad-python 0.8.0 (kipy), kicad-eda-mcp 0.1.0, mcp 1.30.
- `kiutils`: wrote and re-read a .kicad_pcb OK. File format version it writes is 20211014 (KiCad 6 era), not KiCad 10. Do not use it for final files.
- `kicad-sch-api`: could not add `Device:R` standalone, needs KiCad symbol libraries on disk.
- Python 3.13 cannot import the apt `pcbnew`. Use the 3.12 venv.

## Export capabilities

- Confirmed: Gerber (via MCP), PDF, STEP (CLI).
- Available per tool list, unverified: drill, position, BOM, netlist, SVG, DXF, DRC/ERC reports, JLCPCB-oriented tools.

## Missing / blockers

1. KiCad 10 is not runnable from Claude Code. Sandbox is Linux; your Mac is reached only through a file/shell bridge that cannot execute macOS binaries.
2. No connected project folder yet. Add a folder in the Claude desktop app for the NIGHTHAWK project.
3. MCP server not installed on the Mac. Needs `git`, Node 18+, and a Python able to import KiCad's `pcbnew`.
4. Sandbox DRC/ERC unavailable (KiCad 7). Pick one: (a) run Claude Code on the Mac, or (b) install KiCad 9/10 in the sandbox (apt has only 7; would need PPA/Flatpak/AppImage, unverified).
5. Footprint lookup failure above.
6. KiCad 10 compatibility of the server is claimed in its README (Windows config references KiCad 10), not verified by me.

## Mac setup (unverified, from the server README)

```
git clone https://github.com/mixelpixx/KiCAD-MCP-Server.git ~/KiCAD-MCP-Server
cd ~/KiCAD-MCP-Server && npm ci && npm run build
python3 -m venv ~/kicad-mcp-venv && ~/kicad-mcp-venv/bin/pip install -r requirements.txt
claude mcp add --scope user kicad \
  -e KICAD_PYTHON=/Applications/KiCad/KiCad.app/Contents/Frameworks/Python.framework/Versions/Current/bin/python3 \
  -e PYTHONPATH=/Applications/KiCad/KiCad.app/Contents/Frameworks/Python.framework/Versions/3.9/lib/python3.9/site-packages \
  -- node ~/KiCAD-MCP-Server/dist/index.js
```

KiCad's bundled Python needs the pip dependencies installed into it, or into a path added to PYTHONPATH. Check the repo's `setup-macos.sh` first.

## Gate

PCB design NOT started. Start only after steps 1 to 4 pass on KiCad 10 with a DRC and ERC round trip.
