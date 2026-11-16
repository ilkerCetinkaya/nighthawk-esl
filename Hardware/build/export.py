import csv
import json
import os
import re
import subprocess
import sys
import zipfile
from collections import OrderedDict

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import design

HW = os.path.dirname(HERE)
ROOT = os.path.dirname(HW)
CLI = "/Applications/KiCad/KiCad.app/Contents/MacOS/kicad-cli"
PCB = os.path.join(HW, "NIGHTHAWK.kicad_pcb")
SCH = os.path.join(HW, "NIGHTHAWK.kicad_sch")
MFG = os.path.join(ROOT, "Manufacturing")
DOC = os.path.join(ROOT, "Documentation")
VAL = os.path.join(DOC, "Validation")

SEEN = "2026-11-07"
STOCK = {
    "C2934560": (13503, 3.3224, "1+", "A"), "C404027": (93165, 0.1227, "5+", "A"), "C7519": (27270, 0.1639, "5+", "A"),
    "C165948": (308460, 0.1736, "5+", "A"), "C465732": (27264, 0.7076, "1+", "A"), "C7666": (94010, 0.0488, "10+", "A"),
    "C108079": (1165800, 0.0121, "50+", "A"), "C19702": (1675120, 0.0205, "20+", "A"), "C15849": (1524300, 0.011, "50+", "A"),
    "C14858": (865500, 0.0083, "50+", "A"), "C21189": (10241400, 0.0022, "100+", "A"), "C21190": (2313200, 0.0017, "100+", "A"),
    "C25804": (3592800, 0.0024, "100+", "A"), "C23162": (3969400, 0.0028, "100+", "A"), "C23186": (15176600, 0.0016, "100+", "A"),
    "C19330": (420500, 0.0122, "50+", "A"), "C17313": (112260, 0.0859, "10+", "A"), "C221895": (17945, 0.3685, "5+", "A"),
    "C160414": (11569, 0.8045, "1+", "A"), "C114218": (707, 1.4038, "1+", "A"), "C5199907": (204, 5.454, "1+", "A"),
    "C7719": (55321, 0.4609, "1+", "B"), "C131941": (70550, 0.3454, "5+", "B"), "C2286": (4174300, 0.0036, "100+", "B"),
    "C51933293": (1973000, 0.0019, "100+", "B"), "C51933297": (736100, 0.0021, "100000+", "B"), "C2691448": (871880, 0.0132, "20000+", "B"),
}
ALT = {"C2934560": "C2926676 (ESP32-C3-WROOM-02U-N4, external antenna)", "C7719": "C20032 TPS3828-33DBVR (agent-reported, not checked)"}


def run(*args):
    subprocess.run([CLI, *args], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


def patch_stackup():
    text = open(PCB).read()
    if "(stackup" in text:
        return "already"
    stack = '''		(stackup
			(layer "F.SilkS" (type "Top Silk Screen") (color "White"))
			(layer "F.Paste" (type "Top Solder Paste"))
			(layer "F.Mask" (type "Top Solder Mask") (color "Black") (thickness 0.01) (material "Solder Mask") (epsilon_r 3.8) (loss_tangent 0))
			(layer "F.Cu" (type "copper") (thickness 0.035))
			(layer "dielectric 1" (type "prepreg") (thickness 0.2104) (material "7628") (epsilon_r 4.4) (loss_tangent 0.02))
			(layer "In1.Cu" (type "copper") (thickness 0.0152))
			(layer "dielectric 2" (type "core") (thickness 1.065) (material "FR4") (epsilon_r 4.6) (loss_tangent 0.02))
			(layer "In2.Cu" (type "copper") (thickness 0.0152))
			(layer "dielectric 3" (type "prepreg") (thickness 0.2104) (material "7628") (epsilon_r 4.4) (loss_tangent 0.02))
			(layer "B.Cu" (type "copper") (thickness 0.035))
			(layer "B.Mask" (type "Bottom Solder Mask") (color "Black") (thickness 0.01) (material "Solder Mask") (epsilon_r 3.8) (loss_tangent 0))
			(layer "B.Paste" (type "Bottom Solder Paste"))
			(layer "B.SilkS" (type "Bottom Silk Screen") (color "White"))
			(copper_finish "ENIG")
			(dielectric_constraints no)
		)
'''
    m = re.search(r"\(setup\n", text)
    if not m:
        return "no setup block"
    text = text[:m.end()] + stack + text[m.end():]
    open(PCB, "w").write(text)
    return "patched"


def pcb_parts():
    import pcbnew
    board = pcbnew.LoadBoard(PCB)
    out = {}
    aux = board.GetDesignSettings().GetAuxOrigin()
    for fp in board.GetFootprints():
        pos = fp.GetPosition()
        out[fp.GetReference()] = {
            "x": pcbnew.ToMM(pos.x - aux.x), "y": -pcbnew.ToMM(pos.y - aux.y), "rot": fp.GetOrientationDegrees(),
            "side": "bottom" if fp.IsFlipped() else "top", "dnp": fp.IsDNP(), "fp": str(fp.GetFPID().GetLibItemName()),
        }
    return out


def groups():
    g = OrderedDict()
    for p in design.PARTS:
        if p["dnp"] or p["ref"].startswith("TP"):
            continue
        key = (p["value"], p["fp"].split(":")[1], p["lcsc"])
        g.setdefault(key, {"refs": [], "p": p})["refs"].append(p["ref"])
    return g


def ref_sort(r):
    m = re.match(r"([A-Za-z]+)(\d+)", r)
    return (m.group(1), int(m.group(2)))


def bom():
    os.makedirs(os.path.join(MFG, "BOM"), exist_ok=True)
    g = groups()
    with open(os.path.join(MFG, "BOM", "JLCPCB_BOM.csv"), "w", newline="") as handle:
        w = csv.writer(handle)
        w.writerow(["Comment", "Designator", "Footprint", "LCSC Part Number"])
        for (value, fp, lcsc), d in g.items():
            w.writerow([value, ",".join(sorted(d["refs"], key=ref_sort)), fp, lcsc])
    import openpyxl
    from openpyxl.styles import Font
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Engineering BOM"
    head = ["Reference", "Quantity", "Value", "Description", "Manufacturer", "Manufacturer Part Number", "LCSC Part Number", "Footprint", "Package",
            "Unit Price (USD)", "Total Price (USD)", "Datasheet URL", "Stock", "Alternative", "Verification Status", "Assembly Status"]
    ws.append(head)
    for c in ws[1]:
        c.font = Font(bold=True)
    total = 0.0
    for (value, fp, lcsc), d in g.items():
        p = d["p"]
        qty = len(d["refs"])
        stock = STOCK.get(lcsc)
        unit = stock[1] if stock else None
        line = unit * qty if unit is not None else None
        if line:
            total += line
        status = {"A": "Verified on LCSC page (read in browser) " + SEEN, "B": "Reported from LCSC page by sub-agent, not re-read"}.get(stock[3], "UNVERIFIED") if stock else "UNVERIFIED"
        tier = f" (price at {stock[2]} qty tier)" if stock else ""
        ws.append([",".join(sorted(d["refs"], key=ref_sort)), qty, value, p["desc"], p["mfr"], p["mpn"], lcsc, p["fp"], fp, unit, line,
                   f"https://www.lcsc.com/product-detail/{lcsc}.html", stock[0] if stock else "", ALT.get(lcsc, ""), status + tier, "JLCPCB SMT" if lcsc not in ("C5199907",) else "JLCPCB SMT, verify edge-mount placement"])
    ws.append([])
    ws.append(["TOTAL (indicative, mixed quantity tiers)", "", "", "", "", "", "", "", "", "", round(total, 2)])
    wb.save(os.path.join(MFG, "BOM", "Engineering_BOM.xlsx"))
    wb.save(os.path.join(DOC, "BOM.xlsx"))
    return round(total, 2)


def cpl():
    os.makedirs(os.path.join(MFG, "CPL"), exist_ok=True)
    raw = os.path.join(MFG, "CPL", "raw_pos.csv")
    run("pcb", "export", "pos", "--format", "csv", "--units", "mm", "--side", "both", "--exclude-dnp", "--use-drill-file-origin", "-o", raw, PCB)
    wanted = {p["ref"] for p in design.PARTS if not p["dnp"] and not p["ref"].startswith("TP")}
    rows = []
    with open(raw) as handle:
        for row in csv.DictReader(handle):
            if row["Ref"] in wanted:
                rows.append(row)
    with open(os.path.join(MFG, "CPL", "JLCPCB_CPL.csv"), "w", newline="") as handle:
        w = csv.writer(handle)
        w.writerow(["Designator", "Mid X", "Mid Y", "Layer", "Rotation"])
        for row in sorted(rows, key=lambda r: ref_sort(r["Ref"])):
            w.writerow([row["Ref"], f'{float(row["PosX"]):.4f}mm', f'{float(row["PosY"]):.4f}mm', "Top" if row["Side"].lower().startswith("top") or row["Side"].lower() == "front" else "Bottom", f'{float(row["Rot"]):.2f}'])
    os.remove(raw)
    return len(rows)


def fabrication():
    gerber = os.path.join(MFG, "Gerber")
    drill = os.path.join(MFG, "Drill")
    for d in (gerber, drill, os.path.join(MFG, "Assembly")):
        os.makedirs(d, exist_ok=True)
    run("pcb", "export", "gerbers", "--layers", "F.Cu,In1.Cu,In2.Cu,B.Cu,F.Paste,B.Paste,F.SilkS,B.SilkS,F.Mask,B.Mask,Edge.Cuts", "--use-drill-file-origin", "--subtract-soldermask", "-o", gerber, PCB)
    run("pcb", "export", "drill", "--format", "excellon", "--drill-origin", "plot", "--excellon-units", "mm", "--generate-map", "--map-format", "gerberx2", "-o", drill + "/", PCB)
    run("pcb", "export", "pdf", "--layers", "F.Cu,F.SilkS,F.Mask,Edge.Cuts,F.Fab", "-o", os.path.join(MFG, "Assembly", "Assembly_Top.pdf"), PCB)
    run("pcb", "export", "pdf", "--layers", "B.Cu,B.SilkS,Edge.Cuts,B.Fab", "-o", os.path.join(MFG, "Assembly", "Assembly_Bottom.pdf"), PCB)
    run("sch", "export", "pdf", "-o", os.path.join(DOC, "Schematic.pdf"), SCH)
    with zipfile.ZipFile(os.path.join(MFG, "NIGHTHAWK_JLCPCB_gerbers.zip"), "w", zipfile.ZIP_DEFLATED) as z:
        for d in (gerber, drill):
            for name in sorted(os.listdir(d)):
                z.write(os.path.join(d, name), name)


def render():
    out = os.path.join(MFG, "Assembly")
    for side, name in (("top", "Render_Top.png"), ("bottom", "Render_Bottom.png")):
        try:
            run("pcb", "render", "--side", side, "--width", "2000", "--height", "2000", "--quality", "basic", "-o", os.path.join(out, name), PCB)
        except subprocess.CalledProcessError as exc:
            print("render failed", side, exc)


def checks():
    os.makedirs(VAL, exist_ok=True)
    parts = pcb_parts()
    sch_refs = set()
    for sheet in design.SHEETS:
        text = open(os.path.join(HW, f"{sheet}.kicad_sch")).read()
        sch_refs |= set(re.findall(r'\(reference "([A-Za-z]+\d+)"\)', text))
    design_refs = {p["ref"] for p in design.PARTS}
    pcb_refs = {r for r in parts if not r.startswith("H")}
    lines = []
    ok = True
    only_sch = sorted(sch_refs - pcb_refs)
    only_pcb = sorted(pcb_refs - sch_refs)
    lines.append(f"schematic references: {len(sch_refs)}  pcb references (excluding mounting holes): {len(pcb_refs)}")
    lines.append(f"in schematic only: {only_sch}")
    lines.append(f"in pcb only: {only_pcb}")
    ok &= not only_sch and not only_pcb
    bom_refs = set()
    with open(os.path.join(MFG, "BOM", "JLCPCB_BOM.csv")) as handle:
        for row in csv.DictReader(handle):
            bom_refs |= set(row["Designator"].split(","))
    cpl_rows = list(csv.DictReader(open(os.path.join(MFG, "CPL", "JLCPCB_CPL.csv"))))
    cpl_refs = {r["Designator"] for r in cpl_rows}
    expected = {p["ref"] for p in design.PARTS if not p["dnp"] and not p["ref"].startswith("TP")}
    lines.append(f"BOM designators: {len(bom_refs)}  CPL designators: {len(cpl_refs)}  expected assembly parts: {len(expected)}")
    lines.append(f"expected but missing in BOM: {sorted(expected - bom_refs)}")
    lines.append(f"expected but missing in CPL: {sorted(expected - cpl_refs)}")
    lines.append(f"in BOM but not CPL: {sorted(bom_refs - cpl_refs)}")
    lines.append(f"in CPL but not BOM: {sorted(cpl_refs - bom_refs)}")
    ok &= expected == bom_refs == cpl_refs
    open(os.path.join(VAL, "BOM_Check.txt"), "w").write("\n".join(lines) + f"\nRESULT: {'PASS' if expected == bom_refs == cpl_refs else 'FAIL'}\n")
    c = []
    mismatches = 0
    for r in cpl_rows:
        p = parts[r["Designator"]]
        x, y = float(r["Mid X"][:-2]), float(r["Mid Y"][:-2])
        if abs(x - p["x"]) > 0.01 or abs(y - p["y"]) > 0.01:
            mismatches += 1
            c.append(f"{r['Designator']}: CPL ({x:.3f},{y:.3f}) vs PCB ({p['x']:.3f},{p['y']:.3f})")
    bottom = [r["Designator"] for r in cpl_rows if r["Layer"] != "Top"]
    c.insert(0, f"CPL rows: {len(cpl_rows)}; coordinate mismatches vs re-read PCB: {mismatches}; bottom-layer parts: {bottom}")
    c.append("Rotations are exported from KiCad as placed. JLCPCB package-specific rotation offsets were NOT applied or checked; verify in the JLCPCB viewer before ordering.")
    c.append("Excluded: DNP parts, test points, mounting holes.")
    open(os.path.join(VAL, "CPL_Check.txt"), "w").write("\n".join(c) + f"\nRESULT: {'PASS (coordinates)' if mismatches == 0 else 'FAIL'}\n")
    return ok


def drc_erc():
    os.makedirs(VAL, exist_ok=True)
    subprocess.run([CLI, "pcb", "drc", "--format", "report", "--severity-all", "--units", "mm", "--refill-zones", "--all-track-errors", "-o", os.path.join(VAL, "DRC.txt"), PCB], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    subprocess.run([CLI, "sch", "erc", "--format", "report", "--severity-all", "-o", os.path.join(VAL, "ERC.txt"), SCH], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


if __name__ == "__main__":
    stage = sys.argv[1] if len(sys.argv) > 1 else "all"
    if stage in ("all", "stackup"):
        print("stackup", patch_stackup())
    if stage in ("all", "fab"):
        fabrication()
        print("fab done")
    if stage in ("all", "bom"):
        print("bom total", bom())
        print("cpl rows", cpl())
    if stage in ("all", "render"):
        render()
    if stage in ("all", "check"):
        print("checks", checks())
    if stage in ("all", "drc"):
        drc_erc()
