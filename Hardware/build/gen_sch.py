import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import design
from sch_helpers import Q, dump, esc, flatten, lib_symbols, parse, pins_of, uid

HW = os.path.dirname(HERE)
PROJECT = "NIGHTHAWK"
ROOT_UUID = uid("nighthawk_root")
SHEET_UUID = {name: uid("sheet", name) for name in design.SHEETS}
POWER_FLAG_NETS = ["GND", "VBUS", "VBUS_F", "3V3_A", "RF1_VCC_F", "RF2_VCC_F"]

CUSTOM = {
    "AND2": ("NH_LOCAL", "SN74LVC1G08", "U", "Package_TO_SOT_SMD:SOT-23-5",
             [("1", "A", "input", "L"), ("2", "B", "input", "L"), ("4", "Y", "output", "R"), ("3", "GND", "power_in", "B"), ("5", "VCC", "power_in", "T")]),
    "TPS22918": ("NH_LOCAL", "TPS22918", "U", "Package_TO_SOT_SMD:SOT-23-6",
                 [("1", "VIN", "power_in", "L"), ("3", "ON", "input", "L"), ("2", "GND", "power_in", "B"), ("4", "CT", "passive", "R"),
                  ("5", "QOD", "passive", "R"), ("6", "VOUT", "power_out", "R")]),
}

LIB_MAP = {
    "J1": ("Connector", "USB_C_Receptacle_USB2.0_16P"),
    "U1": ("RF_Module", "ESP32-C3-WROOM-02"),
    "U2": ("Interface_Expansion", "TCA9555PWR"),
    "U3": ("Regulator_Linear", "TLV75533PDBV"),
    "U4": ("Regulator_Linear", "TLV75533PDBV"),
    "U7": ("Power_Supervisor", "TPS3823-xxDBV"),
    "D1": ("Power_Protection", "USBLC6-2SC6"),
    "F1": ("Device", "Polyfuse"),
    "J2": ("Connector", "Conn_Coaxial"),
    "J3": ("Connector", "Conn_Coaxial"),
    "J4": ("Connector_Generic", "Conn_01x15"),
    "J5": ("Connector_Generic", "Conn_01x15"),
    "J6": ("Connector_Generic", "Conn_01x04"),
    "J7": ("Connector", "Micro_SD_Card_Det_Hirose_DM3AT"),
    "J8": ("Connector_Generic", "Conn_01x04"),
    "J9": ("Connector_Generic", "Conn_01x04"),
    "SW1": ("Switch", "SW_Push"),
    "SW2": ("Switch", "SW_Push"),
}


def custom_symbol(key):
    lib, name, refp, fpid, pins = CUSTOM[key]
    left = [p for p in pins if p[3] == "L"]
    right = [p for p in pins if p[3] == "R"]
    top = [p for p in pins if p[3] == "T"]
    bottom = [p for p in pins if p[3] == "B"]
    h = max(len(left), len(right), 2) * 2.54 + 2.54
    w = 12.7
    lines = [f'(symbol "{lib}:{name}" (pin_names (offset 1.016)) (exclude_from_sim no) (in_bom yes) (on_board yes)',
             f'(property "Reference" "{refp}" (at 0 {h / 2 + 2.54:.2f} 0) (effects (font (size 1.27 1.27))))',
             f'(property "Value" "{name}" (at 0 {-h / 2 - 2.54:.2f} 0) (effects (font (size 1.27 1.27))))',
             f'(property "Footprint" "{fpid}" (at 0 0 0) (effects (font (size 1.27 1.27)) (hide yes)))',
             '(property "Datasheet" "" (at 0 0 0) (effects (font (size 1.27 1.27)) (hide yes)))',
             f'(symbol "{name}_1_1"',
             f'(rectangle (start {-w / 2:.2f} {h / 2:.2f}) (end {w / 2:.2f} {-h / 2:.2f}) (stroke (width 0.254) (type default)) (fill (type background)))']

    def pin(typ, x, y, ang, num, pname):
        lines.append(f'(pin {typ} line (at {x:.2f} {y:.2f} {ang}) (length 5.08) (name "{pname}" (effects (font (size 1.27 1.27)))) (number "{num}" (effects (font (size 1.27 1.27)))))')

    for i, (num, pname, typ, _) in enumerate(left):
        pin(typ, -w / 2 - 5.08, h / 2 - 2.54 - i * 2.54, 0, num, pname)
    for i, (num, pname, typ, _) in enumerate(right):
        pin(typ, w / 2 + 5.08, h / 2 - 2.54 - i * 2.54, 180, num, pname)
    for i, (num, pname, typ, _) in enumerate(top):
        pin(typ, 0, h / 2 + 5.08, 270, num, pname)
    for i, (num, pname, typ, _) in enumerate(bottom):
        pin(typ, 0, -h / 2 - 5.08, 90, num, pname)
    lines.append(")")
    lines.append(")")
    return parse("\n".join(lines))


def symbol_for(part):
    ref, value = part["ref"], part["value"]
    if ref in LIB_MAP:
        return LIB_MAP[ref]
    if part["fp"].startswith("Package_TO_SOT_SMD:SOT-23-5") and value.startswith("SN74"):
        return ("NH_LOCAL", "SN74LVC1G08")
    if value.startswith("TPS22918"):
        return ("NH_LOCAL", "TPS22918")
    if ref.startswith("TP"):
        return ("Connector", "TestPoint")
    if ref.startswith("R"):
        return ("Device", "R")
    if ref.startswith("C"):
        return ("Device", "C")
    if ref.startswith("FB"):
        return ("Device", "FerriteBead")
    if ref.startswith("D"):
        return ("Device", "LED")
    raise KeyError(ref)


def symbol_pins(lib, name):
    if lib == "NH_LOCAL":
        key = "AND2" if name == "SN74LVC1G08" else "TPS22918"
        node = custom_symbol(key)
        result = []

        def walk(n):
            if isinstance(n, list):
                if n and n[0] == "pin" and any(isinstance(c, list) and c and c[0] == "number" for c in n):
                    at = next(c for c in n if isinstance(c, list) and c[0] == "at")
                    number = next(c for c in n if isinstance(c, list) and c[0] == "number")[1]
                    result.append((str(number), float(at[1]), float(at[2]), float(at[3])))
                for c in n:
                    walk(c)

        walk(node)
        return result
    return pins_of(lib, name)


def lib_node(lib, name):
    if lib == "NH_LOCAL":
        return custom_symbol("AND2" if name == "SN74LVC1G08" else "TPS22918")
    return flatten(lib, name)


def symbol_extent(pins):
    xs = [p[1] for p in pins]
    ys = [p[2] for p in pins]
    return min(xs), max(xs), min(ys), max(ys)


def label_text(net, X, Y, lab, uuid_key):
    just = "right" if lab == 180 else ("left" if lab == 0 else "left bottom")
    return (f'(global_label "{net}" (shape bidirectional) (at {X:.2f} {Y:.2f} {int(lab)}) (effects (font (size 1.27 1.27)) (justify {just})) '
            f'(uuid "{uid(*uuid_key)}") (property "Intersheetrefs" "${{INTERSHEET_REFS}}" (at {X:.2f} {Y:.2f} 0) (effects (font (size 1.27 1.27)) (hide yes))))')


def build_sheet(sheet, parts):
    items, labels, ncs, used = [], [], [], {}
    x, y, row_h = 25.0, 40.0, 0.0
    max_x = 400.0
    seen_flag = set()
    for p in parts:
        lib, name = symbol_for(p)
        used[(lib, name)] = True
        pins = symbol_pins(lib, name)
        x0, x1, y0, y1 = symbol_extent(pins)
        w = (x1 - x0) + 40.0
        h = (y1 - y0) + 22.0
        if x + w > max_x:
            x = 25.0
            y += row_h
            row_h = 0.0
        cx = round((x - x0 + 20.0) / 1.27) * 1.27
        cy = round((y - y0 + 14.0) / 1.27) * 1.27
        x += w
        row_h = max(row_h, h)
        props = [("Reference", p["ref"]), ("Value", p["value"]), ("Footprint", p["fp"]), ("Datasheet", f"https://www.lcsc.com/product-detail/{p['lcsc']}.html" if p["lcsc"] else ""),
                 ("LCSC", p["lcsc"]), ("MPN", p["mpn"]), ("Manufacturer", p["mfr"])]
        sym = ["(symbol", f'\t(lib_id "{lib}:{name}")', f"\t(at {cx:.2f} {cy:.2f} 0)", "\t(unit 1)", "\t(exclude_from_sim no)", "\t(in_bom yes)", "\t(on_board yes)",
               f"\t(dnp {'yes' if p['dnp'] else 'no'})", f'\t(uuid "{uid("sym", p["ref"])}")']
        for i, (k, v) in enumerate(props):
            hide = " (hide yes)" if k not in ("Reference", "Value") else ""
            sym.append(f'\t(property "{k}" "{esc(v)}" (at {cx:.2f} {cy + y1 + 3.0 + i * 1.6:.2f} 0) (effects (font (size 1.27 1.27)){hide}))')
        for number, *_ in pins:
            sym.append(f'\t(pin "{number}" (uuid "{uid("pin", p["ref"], number)}"))')
        sym.append(f'\t(instances (project "{PROJECT}" (path "/{ROOT_UUID}/{SHEET_UUID[sheet]}" (reference "{p["ref"]}") (unit 1))))')
        sym.append(")")
        items.append("\n".join(sym))
        pad_nets = p["nets"]
        pin_numbers = {pn for pn, *_ in pins}
        for number, px, py, angle in pins:
            net = pad_nets.get(number)
            X, Y = cx + px, cy - py
            if net:
                labels.append(label_text(net, X, Y, (angle + 180) % 360, (p["ref"], number, net)))
            else:
                ncs.append(f'(no_connect (at {X:.2f} {Y:.2f}) (uuid "{uid("nc", p["ref"], number)}"))')
        for net in set(pad_nets.values()):
            if net in POWER_FLAG_NETS and net not in seen_flag and (sheet, net) not in FLAG_DONE:
                FLAG_DONE.add((sheet, net))
                seen_flag.add(net)
    return items, labels, ncs, used


FLAG_DONE = set()


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


def write_sheet(sheet, parts):
    items, labels, ncs, used = build_sheet(sheet, parts)
    first_sheet_of = {}
    for s in design.SHEETS:
        for p in design.PARTS:
            if p["sheet"] == s:
                for net in p["nets"].values():
                    first_sheet_of.setdefault(net, s)
    nets_here = [n for n in POWER_FLAG_NETS if first_sheet_of.get(n) == sheet]
    flags = flag_block(sheet, nets_here, 12.7) if nets_here else []
    libs, seen = [], set()
    for key in list(used):
        node = lib_node(*key)
        libs.append(dump(node, 2))
    if flags:
        libs.append(dump(flatten("power", "PWR_FLAG"), 2))
    header = f'''(kicad_sch
	(version 20260206)
	(generator "eeschema")
	(generator_version "10.0")
	(uuid "{uid('sheetfile', sheet)}")
	(paper "A2")
	(title_block
		(title "NIGHTHAWK {sheet}")
		(date "2026-11-07")
		(rev "A")
		(comment 1 "NIGHTHAWK ESL SECURITY RESEARCH")
		(comment 2 "Generated from Hardware/build/design.py")
	)
	(lib_symbols
{chr(10).join(libs)}
	)
'''
    body = "\n".join(items + labels + ncs + flags) + "\n"
    footer = '\t(embedded_fonts no)\n)\n'
    with open(os.path.join(HW, f"{sheet}.kicad_sch"), "w") as handle:
        handle.write(header + body + footer)
    return len(items), len(labels), len(ncs)


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
		(title "NIGHTHAWK ESL SECURITY RESEARCH")
		(date "2026-11-07")
		(rev "A")
		(comment 1 "Portable multi-protocol ESL security research instrument")
		(comment 2 "ESP32-C3-WROOM-02, modular RF expansion, hardware interlock")
	)
	(lib_symbols)
{chr(10).join(sheets)}
	(sheet_instances
		(path "/" (page "1"))
	)
	(embedded_fonts no)
)
'''
    with open(os.path.join(HW, "NIGHTHAWK.kicad_sch"), "w") as handle:
        handle.write(text)


def write_local_lib():
    body = []
    for key in ("AND2", "TPS22918"):
        text = dump(custom_symbol(key), 1).replace("NH_LOCAL:", "")
        body.append(text)
    with open(os.path.join(HW, "NH_LOCAL.kicad_sym"), "w") as handle:
        handle.write('(kicad_symbol_lib\n\t(version 20251024)\n\t(generator "nighthawk")\n\t(generator_version "1.0")\n' + "\n".join(body) + "\n)\n")
    with open(os.path.join(HW, "sym-lib-table"), "w") as handle:
        handle.write('(sym_lib_table\n\t(version 7)\n\t(lib (name "NH_LOCAL")(type "KiCad")(uri "${KIPRJMOD}/NH_LOCAL.kicad_sym")(options "")(descr "NIGHTHAWK local symbols"))\n)\n')


def main():
    write_local_lib()
    for sheet in design.SHEETS:
        parts = [p for p in design.PARTS if p["sheet"] == sheet]
        print(sheet, write_sheet(sheet, parts))
    write_root()


if __name__ == "__main__":
    main()
