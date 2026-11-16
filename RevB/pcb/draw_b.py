import json, math, os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import make_board_b as m
info = json.load(open(os.path.join(HERE, "placement_b.json")))
S, M = 12.0, 40
BW, BH = m.BW, m.BH
X = lambda x: M + x * S
Y = lambda y: M + (BH - y) * S
COL = {"FLASH_F": "#8c6bb1", "DIG_B": "#72b7b2", "IR_F": "#e377c2", "NFC_F": "#eeca3b", "NFC_TANK": "#eeca3b", "IR_LED": "#e377c2", "ANT24_PI": "#1f77b4", "ANT868_PI": "#9467bd", "RF_CAN": "#17becf", "PWR_F": "#f58518", "REG_B": "#d62728", "UI_F": "#aaaaaa"}
def svg(side, zones):
    W = H = int(2 * M + BW * S)
    o = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" font-family="Helvetica,Arial,sans-serif"><rect width="{W}" height="{H}" fill="#fff"/>']
    title = {"F": "TOP (F) side", "B": "BOTTOM (B) side"}[side] if not zones else "RF zoning, keepouts, shield cans, antennas (all layers)"
    o.append(f'<text x="{M}" y="24" font-size="16" font-weight="bold">NIGHTHAWK REV B preliminary placement, 80 x 50 mm: {title}</text>')
    pts = [(0, 0), (m.CABLE_NOTCH[0], 0), (m.CABLE_NOTCH[0], 3), (m.CABLE_NOTCH[2], 3), (m.CABLE_NOTCH[2], 0), (BW, 0), (BW, BH), (m.NOTCH[2], BH), (m.NOTCH[2], 15.5), (0, 15.5)]
    o.append('<polygon points="%s" fill="#f4f4f0" stroke="#000" stroke-width="2"/>' % " ".join(f"{X(a):.1f},{Y(b):.1f}" for a, b in pts))
    def rc(r, fill, op, stroke="#222", dash="", sw=1.0):
        d = f' stroke-dasharray="{dash}"' if dash else ""
        o.append(f'<rect x="{X(r[0]):.1f}" y="{Y(r[3]):.1f}" width="{(r[2]-r[0])*S:.1f}" height="{(r[3]-r[1])*S:.1f}" fill="{fill}" fill-opacity="{op}" stroke="{stroke}" stroke-width="{sw}"{d}/>')
    def tx(x, y, t, fs=9, anchor="middle", fill="#000"):
        o.append(f'<text x="{X(x):.1f}" y="{Y(y):.1f}" font-size="{fs}" text-anchor="{anchor}" fill="{fill}">{t}</text>')
    if zones:
        rc((0, 15.5, 6.0, 50), "#d62728", 0.12, "#d62728", "6 4"); tx(3, 33, "ESP32 antenna", 8); tx(3, 30, "cut-out (air)", 8)
        rc((-0.0, 0.0, 0.0, 0.0), "none", 0)
        rc((6.0, 15.5, 21.0, 30.0), "none", 0, "#d62728", "2 3")
        tx(13.5, 14.5, "Espressif: 15 mm clear below the module side", 7)
        rc(m.IFA_BOX, "#1f77b4", 0.25, "#1f77b4", "6 4", 1.5); tx(72.4, 47.0, "2.4 GHz IFA (TI AN043) 15.2 x 5.7, no copper on any layer", 7)
        rc(m.ANT868_ZONE, "#9467bd", 0.25, "#9467bd", "6 4", 1.5); tx(75, 8.0, "868 MHz Johanson corner zone", 7); tx(75, 7.0, "10 x 11, no metal, all layers", 7)
        c = m.COIL; rc(c, "#f2cf5b", 0.35, "#a08000", "", 1.5); tx((c[0]+c[2])/2, 41, "NFC coil 18 x 16, 6 turns (1.43 uH calc.)", 9)
        rc((c[0]-10, c[1]-10, c[2]+10, c[3]+10), "none", 0, "#a08000", "5 4"); tx((c[0]+c[2])/2, 30.0, "TI SLOA241C: 10 mm from metal", 7)
        rc(m.CABLE_KO, "#7f7f7f", 0.3, "#555", "4 3"); tx(40, 5.8, "cable keepout", 7)
        cx, cy = m.SH1_C
        rc((cx - 10.75, cy - 10.75, cx + 10.75, cy + 10.75), "#17becf", 0.18, "#000", "", 1.5); rc((cx - 9.75, cy - 9.75, cx + 9.75, cy + 9.75), "none", 0, "#000", "3 2")
        tx(cx, cy + 12.0, "RF shield 21.5 x 21.5 (CC1352R + IPC)", 8)
        rc((0.4, 29.9, 20.3, 49.3), "#4c78a8", 0.2); tx(11, 40, "ESP32-C3-WROOM-02", 10)
        rc(info["J1"]["rect"], "#9d755d", 0.3); tx(58, 4, "USB-C", 9)
        rc(info["J2"]["rect"], "#7f7f7f", 0.3); tx(40, 9, "battery", 9)
        for r in ("J3", "J4"):
            rc(info[r]["rect"], "#2ca02c", 0.4)
        tx(68, 36.3, "U.FL 2.4", 7); tx(66.5, 9.2, "U.FL sub", 7)
        rc(info["ANT2"]["rect"], "#9467bd", 0.5); rc((31.0, 14.0, 46.5, 31.0), "#eeca3b", 0.15, "#a08000", "3 3"); tx(38.7, 12.8, "TRF7970A (no shield)", 7)
        rc((21.5, 31.0, 28.0, 48.5), "#eeca3b", 0.15, "#a08000", "3 3"); tx(24.7, 49.0, "coil tank", 7)
    else:
        for ref, v in info.items():
            sides = ("F", "B") if ref in ("J1", "J6", "J7") else (v["side"],)
            if side not in sides and ref not in ("SH1", "SH2"):
                continue
            r = v["rect"]
            if ref in ("SH1", "SH2"):
                continue
            col = COL.get(v.get("region", ""), "#4c78a8")
            rc(r, col, 0.55, "#222", "", 0.5)
            if ref[0] in "UJYQDFS" or ref.startswith("ANT"):
                tx((r[0] + r[2]) / 2, (r[1] + r[3]) / 2 - 0.3, ref, 8)
        if side == "F":
            for cx, cy in (m.SH1_C,):
                rc((cx - 10.75, cy - 10.75, cx + 10.75, cy + 10.75), "none", 0, "#000", "", 1.5)
            c = m.COIL; rc((c[0], c[1], c[2], c[3]), "#f2cf5b", 0.3, "#a08000", "", 1.2); tx((c[0]+c[2])/2, 41, "NFC coil window", 9)
    o.append("</svg>")
    return "\n".join(o)
os.makedirs(os.path.join(HERE, "drawings"), exist_ok=True)
for name, side, z in (("blocks_top", "F", False), ("blocks_bottom", "B", False), ("rf_zones_keepouts", "F", True)):
    open(os.path.join(HERE, "drawings", name + ".svg"), "w").write(svg(side, z))
