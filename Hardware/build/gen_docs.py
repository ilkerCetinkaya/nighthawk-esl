import csv
import json
import os
import re
import shutil
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import design

ROOT = os.path.dirname(os.path.dirname(HERE))
DOC = os.path.join(ROOT, "Documentation")
VAL = os.path.join(DOC, "Validation")
CHROME = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"


def pin_assignment():
    import openpyxl
    from openpyxl.styles import Font
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "ESP32-C3 module"
    ws.append(["Module pad", "Module pin name", "Net", "Notes"])
    names = {"1": "3V3", "2": "EN", "3": "IO4", "4": "IO5", "5": "IO6", "6": "IO7", "7": "IO8", "8": "IO9", "9": "GND", "10": "IO10", "11": "IO20/RXD", "12": "IO21/TXD",
             "13": "IO18", "14": "IO19", "15": "IO3", "16": "IO2", "17": "IO1", "18": "IO0", "19": "GND"}
    notes = {"2": "10k pull-up, 1u; driven by TPS3823 RESET", "3": "ADC1_CH4", "4": "SD chip select", "7": "strapping pin, I2C pull-up 4.7k", "8": "strapping pin, 10k pull-up, BOOT button",
             "10": "10k pull-down, default low", "13": "USB D-", "14": "USB D+", "16": "strapping pin, I2C pull-up 4.7k"}
    u1 = next(p for p in design.PARTS if p["ref"] == "U1")
    for pad in sorted(names, key=int):
        ws.append([pad, names[pad], u1["nets"][pad], notes.get(pad, "")])
    ws2 = wb.create_sheet("TCA9555 expander")
    ws2.append(["Pin", "Net"])
    u2 = next(p for p in design.PARTS if p["ref"] == "U2")
    for pin in sorted(u2["nets"], key=int):
        ws2.append([pin, u2["nets"][pin]])
    for ref in ("J4", "J5", "J6", "J8", "J9", "J7", "J2", "J3"):
        part = next(p for p in design.PARTS if p["ref"] == ref)
        sheet = wb.create_sheet(f"{ref} {part['value']}"[:31])
        sheet.append(["Pin", "Net"])
        for pin in sorted(part["nets"], key=lambda k: (not k.isdigit(), int(k) if k.isdigit() else 0, k)):
            sheet.append([pin, part["nets"][pin]])
    for s in wb.worksheets:
        for c in s[1]:
            c.font = Font(bold=True)
    wb.save(os.path.join(DOC, "Pin_Assignment.xlsx"))


def validation_files():
    drc = json.load(open(os.path.join(HERE, "work", "drc.json")))
    import collections
    counts = collections.Counter((v["severity"], v["type"]) for v in drc["violations"])
    unconnected = len(drc.get("unconnected_items", []))
    text = f"Connectivity check (KiCad DRC engine, kicad-cli 10.0.6)\nunconnected items: {unconnected}\nshorting items: {sum(n for (s, t), n in counts.items() if t == 'shorting_items')}\nRESULT: {'PASS' if unconnected == 0 else 'FAIL'}\n"
    open(os.path.join(VAL, "Connectivity_Check.txt"), "w").write(text)
    checklist = """NIGHTHAWK REV A manufacturing checklist (status as of 2026-11-07)
[x] 4-layer stackup JLC04161H-7628 recorded in board file
[x] DRC: 0 errors, 0 unconnected (3 silk-edge warnings from the USB-C footprint)
[x] ERC: 0 violations
[x] Gerber, drill, BOM, CPL exported from final PCB; BOM and CPL references match
[x] Every BOM line has an LCSC number read on an LCSC page (grade A) or reported by a sub-agent (grade B, see Engineering_BOM.xlsx)
[ ] JLCPCB assembly viewer rotation check (NOT DONE)
[ ] JLCPCB impedance calculator confirmation of 0.36 mm 50 ohm trace (NOT DONE)
[ ] Black solder mask availability and price (NOT CHECKED)
[ ] Stock re-check before ordering (J7 707 pcs, J2/J3 204 pcs at check time)
[ ] Datasheet pin check for USBLC6-2SC6, TLV75533, DM3AT detect pins (NOT DONE)
[ ] Firmware compile (NOT DONE), desktop app run (NOT DONE)
[ ] First-article tests: power rails, interlock truth table, USB enumeration, SD, RF path continuity (NOT DONE)
"""
    open(os.path.join(VAL, "Manufacturing_Checklist.txt"), "w").write(checklist)
    shutil.copy(os.path.join(ROOT, "Manufacturing", "CPL", "JLCPCB_CPL.csv"), os.path.join(DOC, "CPL.csv"))


CSS = "body{font-family:Helvetica,Arial,sans-serif;max-width:820px;margin:30px auto;font-size:13px;line-height:1.45}table{border-collapse:collapse;width:100%}td,th{border:1px solid #999;padding:4px 6px;text-align:left;vertical-align:top}th{background:#eee}h1{font-size:22px}h2{font-size:17px}code{background:#f2f2f2}"


def pdfs():
    import markdown
    src = os.path.join(DOC, "src")
    for name in ("Architecture", "RF_Research", "Manufacturing_Notes", "Design_Review"):
        html = markdown.markdown(open(os.path.join(src, f"{name}.md")).read(), extensions=["tables"])
        path = os.path.join(src, f"{name}.html")
        open(path, "w").write(f"<html><head><meta charset='utf-8'><style>{CSS}</style></head><body>{html}</body></html>")
        subprocess.run([CHROME, "--headless=new", "--disable-gpu", "--no-pdf-header-footer", f"--print-to-pdf={os.path.join(DOC, name + '.pdf')}", f"file://{path}"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=120)
        os.remove(path)


if __name__ == "__main__":
    pin_assignment()
    validation_files()
    pdfs()
    print(sorted(os.listdir(DOC)))
