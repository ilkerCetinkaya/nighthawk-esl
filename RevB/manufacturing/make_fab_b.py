import csv
import os
import re
import shutil
import subprocess
import sys
import zipfile

import pcbnew

HERE = os.path.dirname(os.path.abspath(__file__))
SRC_DIR = os.path.join(os.path.dirname(HERE), "pcb")
sys.path.insert(0, os.path.join(os.path.dirname(HERE), "schematic"))
import design_b as d

KCLI = "/Applications/KiCad/KiCad.app/Contents/MacOS/kicad-cli"
WORK = os.path.join(HERE, "work")
OUT = os.path.join(HERE, "JLCPCB_REVB_UNROUTED")
NAME = "NIGHTHAWK_REVB"
PCB = os.path.join(WORK, NAME + ".kicad_pcb")
ORIGIN = (100.0, 150.0)

STACKUP = '''		(stackup
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
			(copper_finish "HAL SnPb")
			(dielectric_constraints no)
		)
'''


def run(*args):
    r = subprocess.run([KCLI, *args], capture_output=True, text=True)
    if r.returncode not in (0,):
        print("kicad-cli", args[:3], "rc", r.returncode, r.stderr[-300:])
    return r


def prepare_board():
    os.makedirs(WORK, exist_ok=True)
    for ext in ("kicad_pcb", "kicad_pro", "kicad_dru"):
        shutil.copy(os.path.join(SRC_DIR, f"{NAME}.{ext}"), os.path.join(WORK, f"{NAME}.{ext}"))
    text = open(PCB).read()
    if "(stackup" not in text:
        m = re.search(r"\(setup\n", text)
        text = text[:m.end()] + STACKUP + text[m.end():]
        open(PCB, "w").write(text)
    board = pcbnew.LoadBoard(PCB)
    board.GetDesignSettings().SetAuxOrigin(pcbnew.VECTOR2I(pcbnew.FromMM(ORIGIN[0]), pcbnew.FromMM(ORIGIN[1])))
    pcbnew.SaveBoard(PCB, board)


def gerbers():
    g = os.path.join(OUT, "Gerber")
    dr = os.path.join(OUT, "Drill")
    for p in (g, dr):
        shutil.rmtree(p, ignore_errors=True)
        os.makedirs(p)
    run("pcb", "export", "gerbers", "--layers", "F.Cu,In1.Cu,In2.Cu,B.Cu,F.Paste,B.Paste,F.SilkS,B.SilkS,F.Mask,B.Mask,Edge.Cuts", "--use-drill-file-origin", "--subtract-soldermask", "--check-zones", "-o", g, PCB)
    run("pcb", "export", "drill", "--format", "excellon", "--drill-origin", "plot", "--excellon-units", "mm", "--excellon-zeros-format", "decimal", "--generate-map", "--map-format", "gerberx2", "-o", dr + "/", PCB)
    zpath = os.path.join(OUT, f"{NAME}_JLCPCB_gerbers.zip")
    with zipfile.ZipFile(zpath, "w", zipfile.ZIP_DEFLATED) as z:
        for folder in (g, dr):
            for f in sorted(os.listdir(folder)):
                if f.endswith((".gbrjob", ".rpt")):
                    continue
                z.write(os.path.join(folder, f), f)
    return zpath


def load_rot_db():
    rules = []
    with open(os.path.join(HERE, "jlc_cpl_rotation_db_JLCKicadTools.csv")) as fh:
        rd = csv.reader(fh)
        next(rd)
        for row in rd:
            if not row or not row[0].strip():
                continue
            rules.append((re.compile(row[0]), int(float(row[1])), row[2:] ))
    return rules


def bom_and_cpl():
    rules = load_rot_db()
    by_ref = {p["ref"]: p for p in d.PARTS}
    board = pcbnew.LoadBoard(PCB)
    cpl_rows = []
    placed_refs = set()
    notes = []
    for fp in sorted(board.GetFootprints(), key=lambda f: f.GetReference()):
        ref = fp.GetReference()
        p = by_ref.get(ref)
        if p is None:
            continue
        if p["dnp"]:
            continue
        if not p["lcsc"]:
            continue
        item = fp.GetFPID().GetLibItemName()
        rot = fp.GetOrientationDegrees()
        bottom = fp.GetLayer() != pcbnew.F_Cu
        if bottom:
            rot = (180 - rot) % 360
        corr = None
        for rx, c, _ in rules:
            if rx.match(str(item)):
                corr = c
                break
        rot = (rot + (corr or 0)) % 360
        pos = fp.GetPosition()
        x = pcbnew.ToMM(pos.x) - ORIGIN[0]
        y = ORIGIN[1] - pcbnew.ToMM(pos.y)
        cpl_rows.append([ref, f"{x:.4f}mm", f"{y:.4f}mm", "Bottom" if bottom else "Top", f"{rot:g}"])
        placed_refs.add(ref)
        notes.append((ref, str(item), "Bottom" if bottom else "Top", fp.GetOrientationDegrees(), corr))
    groups = {}
    for ref in sorted(placed_refs, key=lambda r: (re.sub(r"\d", "", r), int(re.sub(r"\D", "", r) or 0))):
        p = by_ref[ref]
        key = (p["value"], p["fp"].split(":")[-1], p["lcsc"])
        groups.setdefault(key, []).append(ref)
    with open(os.path.join(OUT, "BOM_JLCPCB.csv"), "w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["Comment", "Designator", "Footprint", "LCSC Part Number"])
        for (value, fpn, lcsc), refs in groups.items():
            w.writerow([value, ",".join(refs), fpn, lcsc])
    with open(os.path.join(OUT, "CPL_JLCPCB.csv"), "w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["Designator", "Mid X", "Mid Y", "Layer", "Rotation"])
        w.writerows(cpl_rows)
    na = []
    for p in d.PARTS:
        if not p["fp"]:
            continue
        if p["ref"] in placed_refs:
            continue
        reason = "DNP (not populated by design)" if p["dnp"] else ("no LCSC number (not invented)" if not p["lcsc"] else "?")
        na.append([p["ref"], p["value"], p["fp"].split(":")[-1], p["mpn"], p["mfr"], reason])
    with open(os.path.join(OUT, "NOT_ASSEMBLED_BY_JLCPCB.csv"), "w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["Designator", "Value", "Footprint", "MPN", "Manufacturer", "Reason"])
        w.writerows(na)
    with open(os.path.join(OUT, "CPL_rotation_audit.csv"), "w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["Designator", "Footprint", "Layer", "KiCad rotation", "DB correction (None = no rule matched)"])
        w.writerows(notes)
    return len(groups), len(cpl_rows), len(na)


if __name__ == "__main__":
    os.makedirs(OUT, exist_ok=True)
    prepare_board()
    zpath = gerbers()
    print("gerber zip", zpath, os.path.getsize(zpath))
    print("bom lines, cpl rows, not-assembled:", bom_and_cpl())
