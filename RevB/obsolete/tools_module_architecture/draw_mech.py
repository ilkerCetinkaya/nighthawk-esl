def stackup(path):
    layers = [
        ("Solder mask (top)", 0.010, "#2e7d32", "assumed ~10-20 um"),
        ("L1 Cu 1 oz 0.035 mm: components, RF (50 ohm CPWG/microstrip), critical signals, GND pour", 0.035, "#c77c02", "JLC04161H-7628"),
        ("Prepreg 7628, 0.2104 mm, er 4.4", 0.2104, "#d9c58a", "JLC04161H-7628"),
        ("L2 Cu 0.5 oz 0.0152 mm: continuous GND (only cut: NFC coil window)", 0.0152, "#c77c02", "JLC04161H-7628"),
        ("Core FR-4, 1.065 mm, er 4.6", 1.065, "#e8dcb0", "JLC04161H-7628"),
        ("L3 Cu 0.5 oz 0.0152 mm: power (VSYS, 3V6, 3V3, 3V3_RF) + secondary signals, GND fill elsewhere", 0.0152, "#c77c02", "JLC04161H-7628"),
        ("Prepreg 7628, 0.2104 mm, er 4.4", 0.2104, "#d9c58a", "JLC04161H-7628"),
        ("L4 Cu 1 oz 0.035 mm: digital/aux signals, bottom parts, GND fill", 0.035, "#c77c02", "JLC04161H-7628"),
        ("Solder mask (bottom)", 0.010, "#2e7d32", "assumed"),
    ]
    S = 260
    W = 1100
    y = 60
    out = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="620" viewBox="0 0 {W} 620" font-family="Helvetica,Arial,sans-serif">', '<rect width="1100" height="620" fill="#fff"/>',
           '<text x="20" y="30" font-size="18" font-weight="bold">REV B four-layer stackup (JLCPCB JLC04161H-7628, 1.6 mm) - thickness to scale x260 for dielectrics, copper exaggerated</text>']
    for name, t, c, src in layers:
        h = max(10, t * S) if "Cu" in name or "mask" in name else t * S
        out.append(f'<rect x="20" y="{y:.1f}" width="380" height="{h:.1f}" fill="{c}" stroke="#333" stroke-width="0.5"/>')
        out.append(f'<text x="415" y="{y + h/2 + 4:.1f}" font-size="12">{name}  [{src}]</text>')
        y += h + 2
    notes = ["50 ohm on L1 referenced to L2 (h = 0.2104 mm): 2D FD quasi-static solve -> microstrip w = 0.36 mm: 50.3 ohm (no mask), 49.3 ohm (20 um mask);",
             "CPWG w = 0.30 mm, gap 0.15 mm: 49.3 ohm. Hammerstad closed form gives 53.6 ohm for w = 0.36 (no thickness correction). Solver check: 123.1 vs 126.6 ohm reference (-2.8 %).",
             "Final widths must be confirmed with JLCPCB's impedance calculator / controlled-impedance order; dielectric constants are the stackup file values, not measured.",
             "USB D+/D-: 90 ohm differential on L1 over L2 (Espressif guideline), geometry to be solved at layout stage; ESP32-C3 USB is full speed (12 Mbit/s)."]
    for i, n in enumerate(notes):
        out.append(f'<text x="20" y="{y + 30 + i*20}" font-size="12">{n}</text>')
    out.append("</svg>")
    open(path, "w").write("\n".join(out))

def battery(path, b=None):
    S = 9
    out = ['<svg xmlns="http://www.w3.org/2000/svg" width="1100" height="760" viewBox="0 0 1100 760" font-family="Helvetica,Arial,sans-serif">', '<rect width="1100" height="760" fill="#fff"/>',
           '<text x="20" y="30" font-size="18" font-weight="bold">Battery mechanical envelope - PowerXtra 1S Li-Po (dimensions INFERRED from part-number pattern, datasheet not found)</text>']
    ox, oy = 60, 90
    out.append(f'<text x="{ox}" y="{oy-12}" font-size="14" font-weight="bold">Side section (x-z), board length 80 mm, scale 9 px/mm</text>')
    z0 = oy + 120
    def r(x, z, w, h, c, label="", dash=False):
        d = ' stroke-dasharray="5 3"' if dash else ""
        out.append(f'<rect x="{ox + x*S:.1f}" y="{z0 - (z+h)*S:.1f}" width="{w*S:.1f}" height="{h*S:.1f}" fill="{c}" fill-opacity="0.6" stroke="#222"{d}/>')
        if label:
            out.append(f'<text x="{ox + (x+w/2)*S:.1f}" y="{z0 - (z+h/2)*S + 4:.1f}" font-size="11" text-anchor="middle">{label}</text>')
    r(6, 0, 74, 1.6, "#1b5e20", "PCB 1.6")
    r(0, 0, 6, 1.6, "#ffffff", "", True)
    r(6, 1.6, 14, 3.2, "#4c78a8", "ESP32 3.2")
    r(0, 1.6, 6, 0.8, "#4c78a8", "")
    r(72.7, 1.6, 7.3, 3.26, "#9d755d", "USB-C 3.26")
    bx = b["x"]
    r(bx, -0.3, 50.5, 0.3, "#999999", "")
    r(bx, -5.5, 50.5, 5.2, "#e45756", "cell 5.0 +0.2 (PX502050) / 4.0 (PX402050)")
    r(bx, -6.0, 50.5, 0.5, "#ffd0d0", "swelling allowance 0.5 (assumed)", True)
    out.append(f'<text x="{ox}" y="{z0 + 90}" font-size="12">Bottom: 0.3 mm adhesive foam + cell 5.2 max + 0.5 mm swelling allowance = 6.0 mm below the PCB; top: 3.3 mm (USB-C 3.26, ESP32 3.2).</text>')
    out.append(f'<text x="{ox}" y="{z0 + 110}" font-size="12">Assembly height ~ 3.3 + 1.6 + 6.0 = 10.9 mm (PX502050) or ~ 9.9 mm (PX402050), before enclosure walls. SMA edge connectors extend ~ +/-3.2 mm about the board plane (to be confirmed).</text>')
    out.append(f'<text x="{ox}" y="{z0 + 130}" font-size="12">Section is a projection on x: the cell (y {b["y"]:.1f}-{b["y"]+b["h"]:.1f}) does not overlap the USB-C legs (y 0-9.4). Cell edge x = {bx:.1f} mm, i.e. {bx-6:.1f} mm from the antenna strip (x 0-6); Espressif: >= 15 mm.</text>')
    px, py = 60, 420
    out.append(f'<text x="{px}" y="{py-12}" font-size="14" font-weight="bold">Plan view of the bottom (x-y), cell, leads, connector and retention</text>')
    def rp(x, y, w, h, c, label="", dash=False):
        d = ' stroke-dasharray="5 3"' if dash else ""
        out.append(f'<rect x="{px + x*S:.1f}" y="{py + (40-(y+h))*S:.1f}" width="{w*S:.1f}" height="{h*S:.1f}" fill="{c}" fill-opacity="0.45" stroke="#222"{d}/>')
        if label:
            out.append(f'<text x="{px + (x+w/2)*S:.1f}" y="{py + (40-(y+h/2))*S + 4:.1f}" font-size="11" text-anchor="middle">{label}</text>')
    pts = [(0, 0), (80, 0), (80, 40), (6, 40), (6, 7), (0, 7)]
    out.append('<path d="M ' + " L ".join(f"{px + a*S:.1f} {py + (40-b)*S:.1f}" for a, b in pts) + ' Z" fill="#e8f0e3" stroke="#1b5e20" stroke-width="2"/>')
    return out, rp, S, px, py

def finish_battery(out, rp, batt, conn, path):
    b = batt
    rp(b["x"], b["y"], b["w"], b["h"], "#e45756", "cell envelope 50.5 x 20.5 (L x W max, assumed)")
    rp(b["x"] - 1.0, b["y"] - 1.0, b["w"] + 2.0, b["h"] + 2.0, "#ffffff", "", True)
    c = conn
    rp(c["x"], c["y"], c["w"], c["h"], "#e45756", "conn")
    out.append('<text x="60" y="830" font-size="12"></text>')
    notes = ["Retention: 0.3 mm double-sided foam on the cell face + housing rib; no clips over the cell; dashed = 1 mm keep-free border for tolerance/swelling.",
             "Leads: 2 wires from the cell's short edge to the board connector (lead length and connector type depend on the delivered cell: NOT verified).",
             "Protection: a PCM is often fitted at the lead end and can add length; the 50.5 mm envelope may not include it - verify on the physical cell.",
             "No bottom-side components inside the cell envelope; L4 under the cell: GND fill, no switching nodes (heat and coupling)."]
    for i, n in enumerate(notes):
        out.append(f'<text x="60" y="{810 + i*20}" font-size="12">{n}</text>')
    out.append("</svg>")
    open(path, "w").write("\n".join(out).replace('height="760" viewBox="0 0 1100 760"', 'height="900" viewBox="0 0 1100 900"').replace('<rect width="1100" height="760"', '<rect width="1100" height="900"'))

if __name__ == "__main__":
    import json, sys
    stackup("../drawings/stackup.svg")
    sol = json.load(open(sys.argv[1]))
    out, rp, S, px, py = battery(None, sol["BATT"])
    finish_battery(out, rp, sol["BATT"], sol["BATT_CONN"], "../drawings/battery_envelope.svg")
    print("ok")
