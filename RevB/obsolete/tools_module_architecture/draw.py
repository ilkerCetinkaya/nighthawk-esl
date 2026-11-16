import json, sys, math
import os
os.environ.setdefault("DROP", "SD")
from feasibility import BW, BH, NOTCH, ANT, BLOCKS, violations, dist, rect

S = 10.0
M = 60

CONTENT = {
    "ESP32": "ESP32-C3-WROOM-02-N4 body 14x18 on board; antenna strip 6x18 over the notch",
    "USB": "USB-C TYPE-C-31-M-12, opening on right edge",
    "USB_ESD": "TPD2E2U06 ESD, 2x5.1k CC, PTC, 10uF",
    "BATT": "PowerXtra PX502050 / PX402050 envelope 50.5 x 20.5 (bottom)",
    "COIL": "NFC coil window 24x12: no copper on L2-L4, no parts either side",
    "NFC_IC": "TRF7970A QFN-32 5x5, 27.12 MHz xtal, matching, EMC filter",
    "CHG": "BQ24074 linear charger + ILIM/ISET/TS parts (heat source, kept off the cell)",
    "REG": "TPS63802 buck-boost + 0.47 uH (DFE201612E class), 2x TLV755P LDO, under removable can",
    "DIG1": "TCA9555 x2, TPS22918 x2 load switches, pull-ups, decoupling",
    "DIG2": "TPS3823, TPS3431, SN74LVC1G74, SN74LVC1G08 x6, TPS22918 x2",
    "SD": "microSD DM3AT-SF-PEJM5 (card slot at edge)",
    "JST_M1": "RF module 1 connector JST SH 15-pin",
    "JST_M2": "RF module 2 connector JST SH 15-pin",
    "SMA_IN": "SMA RF IN (edge, both sides)",
    "SMA_TEST": "SMA RF TEST (edge, both sides)",
    "BATT_CONN": "battery connector (type unverified)",
    "UI": "buttons, LEDs, interlock + debug connectors",
    "STOR": "GD25Q32ESIGR 32 Mbit SPI NOR flash, SOP-8 208 mil, decoupling, CS#/WP#/HOLD# pull-ups",
}
COLORS = {"ESP32": "#4c78a8", "USB": "#9d755d", "USB_ESD": "#bab0ac", "BATT": "#e45756", "COIL": "#f2cf5b", "NFC_IC": "#eeca3b",
          "CHG": "#f58518", "REG": "#d62728", "DIG1": "#72b7b2", "DIG2": "#72b7b2", "SD": "#b279a2", "JST_M1": "#54a24b", "JST_M2": "#54a24b",
          "SMA_IN": "#2f7d32", "SMA_TEST": "#2f7d32", "BATT_CONN": "#e45756", "UI": "#9d9da1", "STOR": "#8c6bb1"}

def X(x):
    return M + x * S
def Y(y):
    return M + (BH - y) * S

def board_path():
    pts = [(0, 0), (BW, 0), (BW, BH), (NOTCH[2], BH), (NOTCH[2], NOTCH[1]), (0, NOTCH[1])]
    return "M " + " L ".join(f"{X(a):.1f} {Y(b):.1f}" for a, b in pts) + " Z"

def svg_head(title, h_extra=0):
    W = int(2 * M + BW * S)
    H = int(2 * M + BH * S + h_extra)
    return [f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" font-family="Helvetica,Arial,sans-serif">',
            f'<rect width="{W}" height="{H}" fill="#ffffff"/>',
            f'<text x="{M}" y="24" font-size="17" font-weight="bold">{title}</text>']

def dims(out):
    out.append(f'<line x1="{X(0)}" y1="{Y(0)+30}" x2="{X(BW)}" y2="{Y(0)+30}" stroke="#333"/>')
    out.append(f'<text x="{X(BW/2)}" y="{Y(0)+46}" font-size="13" text-anchor="middle">80.0 mm</text>')
    out.append(f'<line x1="{X(BW)+30}" y1="{Y(0)}" x2="{X(BW)+30}" y2="{Y(BH)}" stroke="#333"/>')
    out.append(f'<text x="{X(BW)+36}" y="{Y(BH/2)}" font-size="13" transform="rotate(90 {X(BW)+36} {Y(BH/2)})" text-anchor="middle">40.0 mm</text>')
    out.append(f'<text x="{X(3)}" y="{Y(NOTCH[1])+16}" font-size="10" text-anchor="middle">notch 6 x 33</text>')

def block(out, k, s, dashed=False, label=True, alpha=0.55):
    x0, y0, x1, y1 = rect(s["x"], s["y"], s["w"], s["h"])
    dash = ' stroke-dasharray="6 4"' if dashed else ""
    out.append(f'<rect x="{X(x0):.1f}" y="{Y(y1):.1f}" width="{(x1-x0)*S:.1f}" height="{(y1-y0)*S:.1f}" fill="{COLORS[k]}" fill-opacity="{alpha}" stroke="#222" stroke-width="1.2"{dash}/>')
    if label:
        fs = 12 if min(x1 - x0, y1 - y0) > 7 else 9
        out.append(f'<text x="{X((x0+x1)/2):.1f}" y="{Y((y0+y1)/2)+4:.1f}" font-size="{fs}" text-anchor="middle" font-weight="bold">{k}</text>')
        out.append(f'<text x="{X((x0+x1)/2):.1f}" y="{Y((y0+y1)/2)+17:.1f}" font-size="9" text-anchor="middle">{x0:.1f},{y0:.1f} {s["w"]:.1f}x{s["h"]:.1f}</text>')

def antenna(out, keepout=True):
    out.append(f'<rect x="{X(ANT[0])}" y="{Y(ANT[3])}" width="{(ANT[2]-ANT[0])*S}" height="{(ANT[3]-ANT[1])*S}" fill="#4c78a8" fill-opacity="0.25" stroke="#4c78a8" stroke-width="1.5"/>')
    out.append(f'<text x="{X(3)}" y="{Y(31)}" font-size="10" text-anchor="middle" transform="rotate(-90 {X(3)} {Y(31)})">ESP32 antenna 6x18 (overhang)</text>')
    if keepout:
        out.append(f'<rect x="{X(-15)}" y="{Y(55)}" width="{21*S}" height="{48*S}" fill="none" stroke="#d62728" stroke-width="1.5" stroke-dasharray="7 4"/>')

def legend(out, items, y0):
    for i, (c, t) in enumerate(items):
        out.append(f'<rect x="{M}" y="{y0 + i*18}" width="14" height="12" fill="{c}" fill-opacity="0.6" stroke="#222"/>')
        out.append(f'<text x="{M+20}" y="{y0 + i*18 + 11}" font-size="12">{t}</text>')

def plan(sol, side, title, path):
    keys = [k for k in sol if sol[k]["side"] == side or BLOCKS[k].get("both")]
    out = svg_head(title, h_extra=18 * (len(keys) + 2) + 40)
    out.append(f'<path d="{board_path()}" fill="#e8f0e3" stroke="#1b5e20" stroke-width="2"/>')
    antenna(out, keepout=False)
    if side == "B":
        e = sol["ESP32"]
        block(out, "ESP32", e, dashed=True, label=False, alpha=0.08)
        out.append(f'<text x="{X(13)}" y="{Y(31)}" font-size="10" text-anchor="middle">no parts under module</text>')
        c = sol["COIL"]
        block(out, "COIL", c, dashed=True, label=False, alpha=0.15)
        out.append(f'<text x="{X(c["x"]+c["w"]/2)}" y="{Y(c["y"]+c["h"]/2)}" font-size="10" text-anchor="middle">coil window: keep clear</text>')
    for k in keys:
        if side == "B" and k in ("ESP32", "COIL"):
            continue
        block(out, k, sol[k])
    dims(out)
    y0 = int(2 * M + BH * S) + 20
    legend(out, [(COLORS[k], f"{k}: {CONTENT[k]}") for k in keys], y0)
    out.append("</svg>")
    open(path, "w").write("\n".join(out))

def zoning(sol, path):
    out = svg_head("REV B RF zoning, shield cans, ground voids (top view)", h_extra=170)
    out.append(f'<path d="{board_path()}" fill="#e8f0e3" stroke="#1b5e20" stroke-width="2"/>')
    antenna(out, keepout=True)
    zones = [
        ("Z1 2.4 GHz ESP32 module (no extra can; never cover the antenna strip)", sol["ESP32"], "#4c78a8", 2.0),
        ("Z2 13.56 MHz NFC (no can over coil; optional can over TRF7970A only)", sol["NFC_IC"], "#eeca3b", 1.0),
        ("Z3a linear charger (thermal zone, no can)", sol["CHG"], "#f58518", 1.0),
        ("Z3b switching regulator (removable can over buck-boost + inductor)", sol["REG"], "#d62728", 1.0),
        ("Z4 RF module 1 interface + load switch + filter", sol["JST_M1"], "#54a24b", 1.5),
        ("Z5 RF module 2 interface + load switch + filter", sol["JST_M2"], "#54a24b", 1.5),
        ("Z6 RF test path (SMA to SMA, CPWG, via fence)", sol["SMA_IN"], "#2f7d32", 1.5),
        ("Z6 RF test path", sol["SMA_TEST"], "#2f7d32", 1.5),
    ]
    for name, s, c, m in zones:
        x0, y0, x1, y1 = s["x"] - m, s["y"] - m, s["x"] + s["w"] + m, s["y"] + s["h"] + m
        out.append(f'<rect x="{X(x0):.1f}" y="{Y(y1):.1f}" width="{(x1-x0)*S:.1f}" height="{(y1-y0)*S:.1f}" fill="{c}" fill-opacity="0.18" stroke="{c}" stroke-width="2.5"/>')
    c = sol["COIL"]
    out.append(f'<rect x="{X(c["x"]):.1f}" y="{Y(c["y"]+c["h"]):.1f}" width="{c["w"]*S:.1f}" height="{c["h"]*S:.1f}" fill="#ffffff" stroke="#b8860b" stroke-width="2" stroke-dasharray="4 3"/>')
    out.append(f'<text x="{X(c["x"]+c["w"]/2)}" y="{Y(c["y"]+c["h"]/2)+4}" font-size="11" text-anchor="middle">L2-L4 copper void (coil window)</text>')
    for k in ("REG",):
        s = sol[k]
        out.append(f'<rect x="{X(s["x"]+1):.1f}" y="{Y(s["y"]+s["h"]-1):.1f}" width="{(s["w"]-2)*S:.1f}" height="{(s["h"]-2)*S:.1f}" fill="none" stroke="#000" stroke-width="2" stroke-dasharray="2 2"/>')
    nfc = sol["NFC_IC"]
    out.append(f'<rect x="{X(nfc["x"]+0.5):.1f}" y="{Y(nfc["y"]+nfc["h"]-0.5):.1f}" width="{(nfc["w"]-1)*S:.1f}" height="{(nfc["h"]-1)*S:.1f}" fill="none" stroke="#000" stroke-width="2" stroke-dasharray="2 2"/>')
    dims(out)
    y0 = int(2 * M + BH * S) + 20
    legend(out, [(z[2], z[0]) for z in zones[:7]] + [("#ffffff", "dashed black: removable shield can (frame + lid); red dashed: ESP32 antenna clearance (Espressif, min 15 mm)")], y0)
    out.append("</svg>")
    open(path, "w").write("\n".join(out))

def keepout(sol, path):
    global M
    M = 210
    out = svg_head("ESP32-C3-WROOM-02 antenna keepout (Espressif HW design guidelines figure, applied)", h_extra=120)
    out.append(f'<rect x="{X(-15)}" y="{Y(55)}" width="{21*S}" height="{48*S}" fill="#d62728" fill-opacity="0.07" stroke="#d62728" stroke-width="1.5" stroke-dasharray="7 4"/>')
    out.append(f'<path d="{board_path()}" fill="#e8f0e3" stroke="#1b5e20" stroke-width="2"/>')
    e = sol["ESP32"]
    block(out, "ESP32", e, label=False)
    antenna(out, keepout=False)
    def dim(x1, y1, x2, y2, t, off=0):
        out.append(f'<line x1="{X(x1)}" y1="{Y(y1)}" x2="{X(x2)}" y2="{Y(y2)}" stroke="#d62728" stroke-width="1.2"/>')
        out.append(f'<text x="{(X(x1)+X(x2))/2+off}" y="{(Y(y1)+Y(y2))/2-4}" font-size="11" fill="#d62728" text-anchor="middle">{t}</text>')
    dim(-15, 41.5, 0, 41.5, "15 (min)")
    dim(-15, 20, 0, 20, "")
    dim(3, 22, 3, 7, "15 min", 22)
    dim(0, 41.5, 6, 41.5, "6")
    b = sol["BATT"]
    out.append(f'<rect x="{X(b["x"])}" y="{Y(b["y"]+b["h"])}" width="{b["w"]*S}" height="{b["h"]*S}" fill="#e45756" fill-opacity="0.15" stroke="#e45756" stroke-dasharray="5 3"/>')
    out.append(f'<text x="{X(b["x"]+b["w"]/2)}" y="{Y(b["y"]+b["h"]/2)}" font-size="11" text-anchor="middle">battery (bottom), {dist(rect(b["x"],b["y"],b["w"],b["h"]), ANT):.1f} mm from antenna</text>')
    out.append(f'<text x="{X(13)}" y="{Y(31)}" font-size="11" text-anchor="middle" fill="#fff">module body</text>')
    y0 = int(2 * M + BH * S) + 20
    for i, t in enumerate([
        "Antenna strip 18 x 6 mm overhangs the board: board cut away under it and 15 mm on both sides along the edge (notch x 0-6, y 7-40).",
        "Red dashed: clearance area per Espressif 'Keepout Zone for ESP32-C3 Module's Antenna' (min 15 mm left/right and outward).",
        "Inside the product housing: >= 15 mm free space around the antenna in all directions (Espressif recommendation) -> enclosure wall >= 15 mm beyond x = 0.",
        "No copper on any layer, no components, no battery, no shield can inside the clearance area. Dense GND vias along the notch edge and module body."]):
        out.append(f'<text x="{M}" y="{y0 + i*20}" font-size="12">{t}</text>')
    out.append("</svg>")
    open(path, "w").write("\n".join(out))
    M = 60

if __name__ == "__main__":
    sol = json.load(open(sys.argv[1]))
    v = violations(sol)
    print("violations:", v)
    plan(sol, "T", "REV B placement proposal - TOP side (80 x 40 mm, 4-layer, 1.6 mm)", "../drawings/placement_top.svg")
    plan(sol, "B", "REV B placement proposal - BOTTOM side (viewed from top, x-ray)", "../drawings/placement_bottom.svg")
    zoning(sol, "../drawings/rf_zoning_shields.svg")
    keepout(sol, "../drawings/antenna_keepout.svg")
