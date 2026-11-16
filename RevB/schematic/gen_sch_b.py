import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import design_b as design
import symbols_b
from sch_helpers import Q, dump, esc, flatten, lib_symbols, parse, uid

PROJECT = "NIGHTHAWK_REVB"
ROOT_UUID = uid("nhb_root")
SHEET_UUID = {name: uid("nhb_sheet", name) for name in design.SHEETS}
DATE = "2026-11-08"


def pin_table(node):
    pins = []

    def walk(n):
        if isinstance(n, list):
            if n and n[0] == "pin" and any(isinstance(c, list) and c and c[0] == "number" for c in n):
                at = next(c for c in n if isinstance(c, list) and c[0] == "at")
                number = str(next(c for c in n if isinstance(c, list) and c[0] == "number")[1])
                name = str(next(c for c in n if isinstance(c, list) and c[0] == "name")[1])
                pins.append({"num": number, "name": name, "type": str(n[1]), "x": float(at[1]), "y": float(at[2]), "ang": float(at[3])})
            for c in n:
                walk(c)

    walk(node)
    return pins


def lib_node(sym):
    lib, name = sym
    if lib == "NH_LOCAL":
        return symbols_b.custom_symbol(name)
    node = flatten(lib, name)
    return node


_pt = {}


def pins_for(sym):
    if sym not in _pt:
        node = lib_node(sym)
        _pt[sym] = pin_table(node)
    return _pt[sym]


def resolve(parts):
    problems = []
    for p in parts:
        pins = pins_for(p["sym"])
        numbers = {x["num"] for x in pins}
        names = {x["name"] for x in pins}
        for key in p["nets"]:
            if key not in numbers and key not in names:
                problems.append(f"{p['ref']}: net key {key} matches no pin of {p['sym']}")
    return problems


def net_for(p, pin):
    nets = p["nets"]
    if pin["num"] in nets:
        return nets[pin["num"]]
    byname = [x for x in pins_for(p["sym"]) if x["name"] == pin["name"]]
    if pin["name"] in nets and len(byname) == 1:
        return nets[pin["name"]]
    return None


def label_text(net, X, Y, lab, key):
    just = "right" if lab == 180 else ("left" if lab == 0 else "left bottom")
    return (f'(global_label "{net}" (shape bidirectional) (at {X:.2f} {Y:.2f} {int(lab)}) (effects (font (size 1.27 1.27)) (justify {just})) '
            f'(uuid "{uid(*key)}") (property "Intersheetrefs" "${{INTERSHEET_REFS}}" (at {X:.2f} {Y:.2f} 0) (effects (font (size 1.27 1.27)) (hide yes))))')


def compute_flag_nets():
    drivers, powered = set(), set()
    for p in design.PARTS:
        for pin in pins_for(p["sym"]):
            net = net_for(p, pin)
            if not net:
                continue
            if pin["type"] == "power_out":
                drivers.add(net)
            if pin["type"] == "power_in":
                powered.add(net)
    return sorted(powered - drivers)


def build_sheet(sheet, parts):
    items, labels, ncs, used = [], [], [], {}
    x, y, row_h = 25.0, 45.0, 0.0
    max_x = 800.0
    for p in parts:
        sym = p["sym"]
        used[sym] = True
        pins = pins_for(sym)
        xs = [q["x"] for q in pins] or [0]
        ys = [q["y"] for q in pins] or [0]
        x0, x1, y0, y1 = min(xs), max(xs), min(ys), max(ys)
        w = (x1 - x0) + 36.0
        h = (y1 - y0) + 24.0
        if x + w > max_x:
            x = 25.0
            y += row_h
            row_h = 0.0
        cx = round((x - x0 + 18.0) / 1.27) * 1.27
        cy = round((y - y0 + 14.0) / 1.27) * 1.27
        x += w
        row_h = max(row_h, h)
        ds = p["ds"] or (f"https://www.lcsc.com/product-detail/{p['lcsc']}.html" if p["lcsc"] else "")
        props = [("Reference", p["ref"]), ("Value", p["value"]), ("Footprint", p["fp"]), ("Datasheet", ds),
                 ("LCSC", p["lcsc"]), ("MPN", p["mpn"]), ("Manufacturer", p["mfr"]), ("Description", p["desc"])]
        sym_lines = ["(symbol", f'\t(lib_id "{sym[0]}:{sym[1]}")', f"\t(at {cx:.2f} {cy:.2f} 0)", "\t(unit 1)", "\t(exclude_from_sim no)", "\t(in_bom yes)", "\t(on_board yes)",
                     f"\t(dnp {'yes' if p['dnp'] else 'no'})", f'\t(uuid "{uid("sym", p["ref"])}")']
        for i, (k, v) in enumerate(props):
            hide = " (hide yes)" if k not in ("Reference", "Value") else ""
            sym_lines.append(f'\t(property "{k}" "{esc(v)}" (at {cx:.2f} {cy - y1 - 4.0 - i * 1.6:.2f} 0) (effects (font (size 1.27 1.27)){hide}))')
        for q in pins:
            sym_lines.append(f'\t(pin "{q["num"]}" (uuid "{uid("pin", p["ref"], q["num"])}"))')
        sym_lines.append(f'\t(instances (project "{PROJECT}" (path "/{ROOT_UUID}/{SHEET_UUID[sheet]}" (reference "{p["ref"]}") (unit 1))))')
        sym_lines.append(")")
        items.append("\n".join(sym_lines))
        for q in pins:
            net = net_for(p, q)
            X, Y = cx + q["x"], cy - q["y"]
            if net:
                labels.append(label_text(net, X, Y, (q["ang"] + 180) % 360, (p["ref"], q["num"], net)))
            else:
                ncs.append(f'(no_connect (at {X:.2f} {Y:.2f}) (uuid "{uid("nc", p["ref"], q["num"])}"))')
    return items, labels, ncs, used


def flag_block(sheet, nets, base_y):
    out = []
    for i, net in enumerate(nets):
        fx, fy = 25.4 + i * 30.48, base_y
        out.append("(symbol\n\t(lib_id \"power:PWR_FLAG\")\n\t(at %.2f %.2f 0)\n\t(unit 1)\n\t(exclude_from_sim no)\n\t(in_bom no)\n\t(on_board no)\n\t(dnp no)\n\t(uuid \"%s\")\n"
                   "\t(property \"Reference\" \"#FLG_%s_%s\" (at %.2f %.2f 0) (effects (font (size 1.27 1.27)) (hide yes)))\n"
                   "\t(property \"Value\" \"PWR_FLAG\" (at %.2f %.2f 0) (effects (font (size 1.27 1.27)) (hide yes)))\n"
                   "\t(pin \"1\" (uuid \"%s\"))\n\t(instances (project \"%s\" (path \"/%s/%s\" (reference \"#FLG_%s_%s\") (unit 1))))\n)" % (
                       fx, fy, uid("flag", sheet, net), sheet[:2], net, fx, fy + 2, fx, fy - 2, uid("flagpin", sheet, net), PROJECT, ROOT_UUID, SHEET_UUID[sheet], sheet[:2], net))
        out.append(label_text(net, fx, fy, 0, ("flaglabel", sheet, net)))
    return out


def write_sheet(sheet, flag_nets, first_sheet):
    parts = [p for p in design.PARTS if p["sheet"] == sheet]
    items, labels, ncs, used = build_sheet(sheet, parts)
    nets_here = [n for n in flag_nets if first_sheet.get(n) == sheet]
    flags = flag_block(sheet, nets_here, 12.7) if nets_here else []
    libs = [dump(lib_node(key), 2) for key in used]
    if flags:
        libs.append(dump(flatten("power", "PWR_FLAG"), 2))
    header = f'''(kicad_sch
	(version 20260206)
	(generator "eeschema")
	(generator_version "10.0")
	(uuid "{uid('nhb_sheetfile', sheet)}")
	(paper "A1")
	(title_block
		(title "NIGHTHAWK REV B {sheet}")
		(date "{DATE}")
		(rev "B-draft")
		(comment 1 "Integrated single-board security research instrument")
		(comment 2 "Generated by RevB/schematic/gen_sch_b.py; not production-ready")
	)
	(lib_symbols
{chr(10).join(libs)}
	)
'''
    with open(os.path.join(HERE, f"{sheet}.kicad_sch"), "w") as handle:
        handle.write(header + "\n".join(items + labels + ncs + flags) + "\n\t(embedded_fonts no)\n)\n")
    return len(items), len(labels), len(ncs), len(flags) // 2


def write_root():
    sheets = []
    for i, name in enumerate(design.SHEETS):
        col, row = i % 4, i // 4
        x, y = 30.0 + col * 95.0, 40.0 + row * 55.0
        sheets.append(f'''	(sheet
		(at {x:.2f} {y:.2f})
		(size 70.0 30.0)
		(exclude_from_sim no)
		(in_bom yes)
		(on_board yes)
		(dnp no)
		(stroke (width 0.1524) (type solid))
		(fill (color 0 0 0 0.0))
		(uuid "{SHEET_UUID[name]}")
		(property "Sheetname" "{name}" (at {x:.2f} {y - 1.0:.2f} 0) (effects (font (size 1.27 1.27)) (justify left bottom)))
		(property "Sheetfile" "{name}.kicad_sch" (at {x:.2f} {y + 31.0:.2f} 0) (effects (font (size 1.27 1.27)) (justify left top)))
		(instances (project "{PROJECT}" (path "/{ROOT_UUID}" (page "{i + 2}"))))
	)''')
    text = f'''(kicad_sch
	(version 20260206)
	(generator "eeschema")
	(generator_version "10.0")
	(uuid "{ROOT_UUID}")
	(paper "A3")
	(title_block
		(title "NIGHTHAWK ESL REV B (integrated)")
		(date "{DATE}")
		(rev "B-draft")
		(comment 1 "80 x 50 mm, 4 layers; component-level schematic draft")
		(comment 2 "ESP32-C3 + CC1352R + TRF7970A + IR link + hardware interlock")
	)
	(lib_symbols)
{chr(10).join(sheets)}
	(sheet_instances
		(path "/" (page "1"))
	)
	(embedded_fonts no)
)
'''
    with open(os.path.join(HERE, f"{PROJECT}.kicad_sch"), "w") as handle:
        handle.write(text)


def write_project_files():
    with open(os.path.join(HERE, f"{PROJECT}.kicad_pro"), "w") as handle:
        json.dump({"meta": {"filename": f"{PROJECT}.kicad_pro", "version": 3}, "schematic": {"drawing": {"default_line_thickness": 6.0}}}, handle, indent=2)
    body = [dump(symbols_b.custom_symbol(k), 1).replace("NH_LOCAL:", "") for k in symbols_b.CUSTOM]
    with open(os.path.join(HERE, "NH_LOCAL.kicad_sym"), "w") as handle:
        handle.write('(kicad_symbol_lib\n\t(version 20251024)\n\t(generator "nighthawk")\n\t(generator_version "1.0")\n' + "\n".join(body) + "\n)\n")
    with open(os.path.join(HERE, "sym-lib-table"), "w") as handle:
        handle.write('(sym_lib_table\n\t(version 7)\n\t(lib (name "NH_LOCAL")(type "KiCad")(uri "${KIPRJMOD}/NH_LOCAL.kicad_sym")(options "")(descr "NIGHTHAWK REV B local symbols"))\n)\n')
    with open(os.path.join(HERE, "fp-lib-table"), "w") as handle:
        handle.write('(fp_lib_table\n\t(version 7)\n\t(lib (name "NH_REVB")(type "KiCad")(uri "${KIPRJMOD}/NH_REVB.pretty")(options "")(descr "NIGHTHAWK REV B local footprints"))\n)\n')


def main():
    problems = resolve(design.PARTS)
    if problems:
        print("\n".join(problems))
        sys.exit(1)
    flag_nets = compute_flag_nets()
    first_sheet = {}
    for s in design.SHEETS:
        for p in design.PARTS:
            if p["sheet"] == s:
                for net in p["nets"].values():
                    first_sheet.setdefault(net, s)
    write_project_files()
    for sheet in design.SHEETS:
        print(sheet, write_sheet(sheet, flag_nets, first_sheet))
    write_root()
    print("flag nets:", flag_nets)


if __name__ == "__main__":
    main()
