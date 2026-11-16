from layout import B, KEEPOUTS, ANT_NOTCH, CABLE_NOTCH, NOTCH_R, BW, BH, check, metrics, R, dist, ESP_ANT

S, M = 10.0, 60
COL = {"ESP32": "#4c78a8", "USB": "#9d755d", "USB_ESD": "#bab0ac", "CHG": "#f58518", "REG": "#d62728", "STOR": "#8c6bb1",
       "IR": "#e377c2", "BATT_CONN": "#7f7f7f", "NFC_IC": "#eeca3b", "COIL": "#f2cf5b", "RF_SOC": "#17becf", "UFL24": "#2ca02c",
       "UFLSUB": "#2ca02c", "ANT24": "#1f77b4", "SUBANT": "#9467bd", "UI_T": "#c7c7c7", "DIG1": "#72b7b2", "DIG2": "#72b7b2", "UI_B": "#c7c7c7"}
X = lambda x: M + x * S
Y = lambda y: M + (BH - y) * S

def outline():
    r = NOTCH_R
    x0, y0, x1, y1 = CABLE_NOTCH
    p = [f"M {X(0)} {Y(0)}", f"L {X(x0 - r)} {Y(0)}", f"A {r*S} {r*S} 0 0 0 {X(x0)} {Y(r)}", f"L {X(x0)} {Y(y1 - r)}",
         f"A {r*S} {r*S} 0 0 1 {X(x0 + r)} {Y(y1)}", f"L {X(x1 - r)} {Y(y1)}", f"A {r*S} {r*S} 0 0 1 {X(x1)} {Y(y1 - r)}",
         f"L {X(x1)} {Y(r)}", f"A {r*S} {r*S} 0 0 0 {X(x1 + r)} {Y(0)}", f"L {X(BW)} {Y(0)}", f"L {X(BW)} {Y(BH)}",
         f"L {X(ANT_NOTCH[2])} {Y(BH)}", f"L {X(ANT_NOTCH[2])} {Y(ANT_NOTCH[1])}", f"L {X(0)} {Y(ANT_NOTCH[1])}", "Z"]
    return " ".join(p)

def head(title, extra=0, w=None):
    W = w or int(2 * M + BW * S)
    H = int(2 * M + BH * S + extra)
    return [f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" font-family="Helvetica,Arial,sans-serif">',
            f'<rect width="{W}" height="{H}" fill="#fff"/>', f'<text x="{M}" y="26" font-size="17" font-weight="bold">{title}</text>']

def rect(o, r, fill, op=0.5, dash="", sw=1.2, stroke="#222"):
    d = f' stroke-dasharray="{dash}"' if dash else ""
    o.append(f'<rect x="{X(r[0]):.1f}" y="{Y(r[3]):.1f}" width="{(r[2]-r[0])*S:.1f}" height="{(r[3]-r[1])*S:.1f}" fill="{fill}" fill-opacity="{op}" stroke="{stroke}" stroke-width="{sw}"{d}/>')

def label(o, r, t, fs=11, sub=None):
    cx, cy = (r[0] + r[2]) / 2, (r[1] + r[3]) / 2
    o.append(f'<text x="{X(cx):.1f}" y="{Y(cy)+4:.1f}" font-size="{fs}" text-anchor="middle" font-weight="bold">{t}</text>')
    if sub:
        o.append(f'<text x="{X(cx):.1f}" y="{Y(cy)+16:.1f}" font-size="8.5" text-anchor="middle">{sub}</text>')

def board(o):
    o.append(f'<path d="{outline()}" fill="#e8f0e3" stroke="#1b5e20" stroke-width="2"/>')
    o.append(f'<line x1="{X(0)}" y1="{Y(0)+32}" x2="{X(BW)}" y2="{Y(0)+32}" stroke="#333"/><text x="{X(40)}" y="{Y(0)+48}" font-size="13" text-anchor="middle">80.0 mm</text>')
    o.append(f'<line x1="{X(BW)+32}" y1="{Y(0)}" x2="{X(BW)+32}" y2="{Y(BH)}" stroke="#333"/><text x="{X(BW)+46}" y="{Y(25)}" font-size="13" transform="rotate(90 {X(BW)+46} {Y(25)})" text-anchor="middle">50.0 mm</text>')

def keepouts(o):
    rect(o, ESP_ANT, "#4c78a8", 0.25, "", 1.5, "#4c78a8")
    o.append(f'<text x="{X(3)}" y="{Y(31)}" font-size="9" text-anchor="middle" transform="rotate(-90 {X(3)} {Y(31)})">ESP32 antenna (overhang)</text>')
    for k, r in KEEPOUTS.items():
        if k == "ESP_CLEAR":
            continue
        rect(o, r, "#ffffff", 0.0, "5 3", 1.5, "#d62728")

def legend(o, items, y0):
    for i, (c, t) in enumerate(items):
        o.append(f'<rect x="{M}" y="{y0+i*17}" width="13" height="11" fill="{c}" fill-opacity="0.6" stroke="#222"/><text x="{M+19}" y="{y0+i*17+10}" font-size="11.5">{t}</text>')

def plan(side, title, path):
    keys = [k for k in B if side in B[k][4]]
    o = head(title, 17 * (len(keys) + 3) + 30)
    board(o)
    keepouts(o)
    if side == "B":
        for k in ("ESP32", "RF_SOC", "COIL"):
            rect(o, R(k), "#ffffff", 0.0, "3 3", 1.0, "#555")
            label(o, R(k), {"ESP32": "no parts", "RF_SOC": "GND only (under RF)", "COIL": "coil window: clear"}[k], 9)
    for k in keys:
        rect(o, R(k), COL[k], 0.55)
        r = R(k)
        label(o, r, k, 11 if min(r[2]-r[0], r[3]-r[1]) > 6 else 7.5, f"{r[0]:.1f},{r[1]:.1f} {r[2]-r[0]:.1f}x{r[3]-r[1]:.1f}" if min(r[2]-r[0], r[3]-r[1]) > 6 else None)
    y0 = int(2 * M + BH * S) + 24
    legend(o, [(COL[k], f"{k}: {B[k][5]}") for k in keys] + [("#ffffff", "red dashed: antenna keepout (no copper on any layer, no parts) / cable notch keepout 1 mm")], y0)
    o.append("</svg>")
    open(path, "w").write("\n".join(o))

def zones(path):
    o = head("REV B RF zones, shield cans, antenna keepouts (top view)", 200)
    board(o)
    keepouts(o)
    Z = [("Z1 ESP32 2.4 GHz (module); no extra can", "ESP32", "#4c78a8", 1.0),
         ("Z2 CC1352R RF section: removable can 18.5 x 13 mm, via fence; antennas outside the can", "RF_SOC", "#17becf", 0.5),
         ("Z3 NFC TRF7970A: removable can over IC + matching only; coil outside", "NFC_IC", "#eeca3b", 0.5),
         ("Z4 buck-boost (bottom): removable can", "REG", "#d62728", 0.5),
         ("Z5 IR optical front end: TIA guard ring, no can over optics", "IR", "#e377c2", 0.5)]
    for name, k, c, m in Z:
        r = R(k)
        rect(o, (r[0]-m, r[1]-m, r[2]+m, r[3]+m), c, 0.15, "", 2.5, c)
    for k in ("RF_SOC", "NFC_IC", "REG"):
        r = R(k)
        rect(o, (r[0]+0.3, r[1]+0.3, r[2]-0.3, r[3]-0.3), "#ffffff", 0.0, "2 2", 2.0, "#000")
    for k in ("ANT24", "SUBANT", "COIL"):
        rect(o, R(k), COL[k], 0.6)
        label(o, R(k), k, 9)
    for k in ("UFL24", "UFLSUB"):
        rect(o, R(k), COL[k], 0.7)
    yy = int(2 * M + BH * S) + 24
    legend(o, [(z[2], z[0]) for z in Z] + [(COL["ANT24"], "ANT24: 2.4 GHz IFA (TI AN043), keepout 16.2 x 6.7 mm all layers"),
                                       (COL["SUBANT"], "SUBANT: 868 MHz chip antenna (DNP), clearance 11 x 13 mm all layers"),
                                       ("#ffffff", "black dotted: shield-can frame outline")], yy)
    o.append("</svg>")
    open(path, "w").write("\n".join(o))

def notch(path):
    s = 40
    o = [f'<svg xmlns="http://www.w3.org/2000/svg" width="1100" height="760" viewBox="0 0 1100 760" font-family="Helvetica,Arial,sans-serif">', '<rect width="1100" height="760" fill="#fff"/>',
         '<text x="30" y="30" font-size="17" font-weight="bold">Battery cable notch (Edge.Cuts) - detail, scale 40 px/mm</text>']
    ox, oy = 120, 470
    x = lambda v: ox + (v - 34) * s
    y = lambda v: oy - v * s
    r = NOTCH_R
    x0, y0, x1, y1 = CABLE_NOTCH
    path_d = (f"M {x(34)} {y(0)} L {x(x0-r)} {y(0)} A {r*s} {r*s} 0 0 0 {x(x0)} {y(r)} L {x(x0)} {y(y1-r)} A {r*s} {r*s} 0 0 1 {x(x0+r)} {y(y1)} "
              f"L {x(x1-r)} {y(y1)} A {r*s} {r*s} 0 0 1 {x(x1)} {y(y1-r)} L {x(x1)} {y(r)} A {r*s} {r*s} 0 0 0 {x(x1+r)} {y(0)} L {x(47)} {y(0)} L {x(47)} {y(9)} L {x(34)} {y(9)} Z")
    o.append(f'<path d="{path_d}" fill="#e8f0e3" stroke="#1b5e20" stroke-width="3"/>')
    o.append(f'<rect x="{x(37)}" y="{y(4)}" width="{6*s}" height="{4*s}" fill="none" stroke="#d62728" stroke-dasharray="6 4" stroke-width="2"/>')
    o.append(f'<text x="{x(40)}" y="{y(4)-8}" font-size="13" fill="#d62728" text-anchor="middle">copper / via / part keepout 1.0 mm around the notch</text>')
    for cx in (39.35, 40.65):
        o.append(f'<circle cx="{x(cx)}" cy="{y(1.2)}" r="{0.65*s}" fill="#444" stroke="#000"/>')
    o.append(f'<text x="{x(40)}" y="{y(-1.0)}" font-size="13" text-anchor="middle">2 x AWG26 UL1007 assumed, OD 1.3 mm each (pair 2.6 x 1.3 mm)</text>')
    def dim(xa, ya, xb, yb, t, off=(0, -8)):
        o.append(f'<line x1="{xa}" y1="{ya}" x2="{xb}" y2="{yb}" stroke="#1f77b4" stroke-width="1.5"/>')
        o.append(f'<text x="{(xa+xb)/2+off[0]}" y="{(ya+yb)/2+off[1]}" font-size="13" fill="#1f77b4" text-anchor="middle">{t}</text>')
    dim(x(x0), y(y1) - 60, x(x1), y(y1) - 60, "4.0 mm (2.6 cable + 2 x 0.7 clearance)")
    dim(x(x1) + 40, y(0), x(x1) + 40, y(y1), "3.0 mm", (40, 0))
    o.append(f'<text x="{x(x1)+60}" y="{y(y1)+30}" font-size="13">internal corner radius R1.0 (4x)</text>')
    o.append(f'<text x="{x(34.2)}" y="{y(8.4)}" font-size="13">PCB (bottom edge, x 38-42 mm)</text>')
    o.append(f'<rect x="{x(34.5)}" y="{y(9)}" width="{9.2*s}" height="{0.0}" fill="none"/>')
    notes = ["Cable route: battery (enclosure, below the PCB) -> through the notch -> JST PH 2-pin SMD connector (top side, 1 mm above the keepout).",
             "Edge finish: routed edge; ask the fab for edge deburring; add a heat-shrink sleeve over the pair where it passes the notch.",
             "Enclosure: the housing needs a matching 4 x 3 mm (or larger) passage at the same position; no sharp metal near the cable.",
             "Assumption to confirm with the actual battery: two AWG26 UL1007 wires (OD 1.3 mm). Thicker leads (e.g. AWG24, OD ~1.5 mm) need a 4.5 mm notch.",
             "The notch takes 12 mm2 of the outline and sits >= 20 mm from every antenna keepout."]
    for i, n in enumerate(notes):
        o.append(f'<text x="30" y="{560 + i*24}" font-size="13">{n}</text>')
    o.append("</svg>")
    open(path, "w").write("\n".join(o))

def block_diagram(path):
    o = ['<svg xmlns="http://www.w3.org/2000/svg" width="1200" height="760" viewBox="0 0 1200 760" font-family="Helvetica,Arial,sans-serif">', '<rect width="1200" height="760" fill="#fff"/>',
         '<defs><marker id="a" markerWidth="8" markerHeight="8" refX="7" refY="4" orient="auto"><path d="M0,0 L8,4 L0,8 z" fill="#333"/></marker></defs>',
         '<text x="30" y="34" font-size="19" font-weight="bold">NIGHTHAWK REV B - single-board integrated block diagram</text>']
    def box(x, y, w, h, t, sub, c):
        o.append(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="6" fill="{c}" fill-opacity="0.25" stroke="{c}" stroke-width="2"/>')
        o.append(f'<text x="{x+w/2}" y="{y+22}" font-size="14" font-weight="bold" text-anchor="middle">{t}</text>')
        for i, s in enumerate(sub):
            o.append(f'<text x="{x+w/2}" y="{y+40+i*15}" font-size="11" text-anchor="middle">{s}</text>')
    def arrow(x1, y1, x2, y2, t="", both=False):
        mk = ' marker-end="url(#a)"' + (' marker-start="url(#a)"' if both else "")
        o.append(f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="#333" stroke-width="1.6"{mk}/>')
        if t:
            o.append(f'<text x="{(x1+x2)/2+4}" y="{(y1+y2)/2-5}" font-size="11">{t}</text>')
    box(30, 70, 200, 110, "USB-C", ["TPD2E2U06 ESD", "PTC, CC 5.1k"], "#9d755d")
    box(30, 230, 200, 120, "Power", ["BQ24074 charger (linear)", "TPS63802 buck-boost 3.6 V", "TLV755P 3V3 / 3V3_RF"], "#f58518")
    box(30, 400, 200, 90, "Battery (user)", ["1S Li-Po via cable notch", "JST PH 2-pin"], "#7f7f7f")
    box(330, 230, 230, 150, "ESP32-C3-WROOM-02", ["host, USB-CDC CLI, storage task", "supervisor (WDI, ARM)", "own 2.4 GHz antenna (radio off", "by default)"], "#4c78a8")
    box(330, 70, 230, 110, "Hardware interlock", ["TPS3823 + TPS3431 dead-man", "SN74LVC1G74 latch, LVC1G08 x7", "TPS22918 x3 rail switches"], "#72b7b2")
    box(330, 440, 230, 90, "GD25Q32E 4 MB", ["SPI NOR (log storage)"], "#8c6bb1")
    box(330, 580, 230, 90, "TCA9555 x2 (0x20/0x21)", ["CS/RESET/IRQ/rail-sense/permit", "readback"], "#72b7b2")
    box(680, 70, 250, 170, "CC1352R1F3 RF SoC", ["2360-2500 MHz: BLE 1M/2M, 802.15.4,", "proprietary 2-GFSK", "sub-GHz port (359-527 / 861-1054 MHz)", "IR timing (timers, comparator)", "under shield can"], "#17becf")
    box(990, 50, 180, 80, "2.4 GHz PCB IFA", ["TI AN043, 15.2 x 5.7 mm", "+ U.FL test port"], "#1f77b4")
    box(990, 150, 180, 80, "868 MHz chip ant.", ["0868AT43A0020 (DNP)", "+ U.FL test port"], "#9467bd")
    box(680, 300, 250, 120, "TRF7970A NFC/RFID", ["ISO 14443 A/B, 15693, FeliCa", "(NFC-F 212/424)", "under shield can"], "#eeca3b")
    box(990, 320, 180, 80, "NFC PCB coil", ["28 x 16 mm window"], "#f2cf5b")
    box(680, 480, 250, 120, "IR optical front end", ["VSMB10940 940 nm LED + MOSFET", "VEMD10940F + OPA356 TIA", "(Pricer IR, 1.25 MHz carrier [S])"], "#e377c2")
    arrow(230, 125, 330, 290, "VBUS / D+ D-")
    arrow(130, 180, 130, 230, "5 V")
    arrow(130, 400, 130, 350, "VBAT")
    arrow(230, 290, 330, 300, "3V3")
    arrow(445, 230, 445, 180, "WDI, ARM, EN", True)
    arrow(560, 110, 680, 110, "")
    o.append('<text x="565" y="100" font-size="11">3V3_RF (gated)</text>')
    arrow(560, 300, 680, 215, "", True)
    o.append('<text x="585" y="275" font-size="11">UART [A]</text>')
    arrow(560, 350, 680, 350, "SPI (shared)", True)
    arrow(445, 380, 445, 440, "SPI (shared)", True)
    o.append('<polyline points="330,625 305,625 305,340 322,340" fill="none" stroke="#333" stroke-width="1.6" marker-end="url(#a)"/>')
    o.append('<text x="240" y="560" font-size="11">I2C + INT</text>')
    arrow(930, 110, 990, 90, "", True)
    arrow(930, 180, 990, 190, "", True)
    arrow(930, 360, 990, 360, "", True)
    o.append('<polyline points="930,225 955,225 955,540 938,540" fill="none" stroke="#333" stroke-width="1.6" marker-end="url(#a)"/>')
    o.append('<text x="960" y="470" font-size="11">IR TX/RX timing</text>')
    o.append('<text x="30" y="730" font-size="12">No plug-in RF modules or RF expansion connectors. All RF transceivers, matching, test ports and antennas are on the single 80 x 50 mm 4-layer PCB. Transmit paths are powered only through the hardware interlock.</text>')
    o.append("</svg>")
    open(path, "w").write("\n".join(o))

if __name__ == "__main__":
    print(check())
    plan("T", "REV B integrated placement - TOP (80 x 50 mm, 4-layer)", "drawings/placement_top.svg")
    plan("B", "REV B integrated placement - BOTTOM (x-ray from top)", "drawings/placement_bottom.svg")
    zones("drawings/rf_zones_shields_antennas.svg")
    notch("drawings/cable_notch.svg")
    block_diagram("drawings/block_diagram.svg")
