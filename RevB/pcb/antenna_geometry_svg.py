import math, os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
S = 40.0
M = 40
def box(o, x0, y0, x1, y1, fill, ox, oy, stroke="#7a4a00", sw=0.6, op=0.9):
    o.append(f'<rect x="{ox + x0 * S:.1f}" y="{oy + (-y1) * S:.1f}" width="{(x1 - x0) * S:.1f}" height="{(y1 - y0) * S:.1f}" fill="{fill}" fill-opacity="{op}" stroke="{stroke}" stroke-width="{sw}"/>')
def text(o, x, y, t, fs=10, anchor="start"):
    o.append(f'<text x="{x:.1f}" y="{y:.1f}" font-size="{fs}" text-anchor="{anchor}" font-family="Helvetica,Arial,sans-serif">{t}</text>')
W = H = 1200
o = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}"><rect width="{W}" height="{H}" fill="#fff"/>']
text(o, M, 28, "NIGHTHAWK REV B antenna geometry (documented dimensions; NOT validated)", 16)
ox, oy = M, 300
text(o, ox, 60, "1) TI AN043 IFA, 15.2 x 5.7 mm (SWRA117D fig. 3, table 1; reconstructed from the figure)", 12)
rects = [(0.5, 4.9, 5.5, 5.4), (0.5, 0.0, 1.4, 4.9), (2.8, 0.0, 3.3, 4.9), (5.0, 2.26, 5.5, 4.9), (5.0, 2.26, 8.0, 2.76), (7.5, 2.26, 8.0, 5.4), (7.5, 4.9, 10.2, 5.4), (9.7, 2.26, 10.2, 4.9), (9.7, 2.26, 12.7, 2.76), (12.2, 2.26, 12.7, 5.4), (12.2, 4.9, 14.9, 5.4), (14.4, 0.96, 14.9, 4.9)]
box(o, 0, 0, 15.2, 5.7, "none", ox, oy - 0.0 * S, "#888", 0.8, 0)
box(o, 0, -3.0, 15.2, 0.5, "#b0b0b0", ox, oy, "#555", 0.5, 0.5)
for r in rects:
    box(o, *r, "#d98c1f", ox, oy)
text(o, ox + 6 * S, oy + 3.4 * S, "Layer-2 ground ends 0.5 mm above the stub feet (D4)", 9)
text(o, ox + 0.2 * S, oy + 0.8 * S, "ground via (short stub)", 9)
text(o, ox + 2.6 * S, oy + 0.9 * S, "feed", 9)
text(o, ox, oy - 0.5 * S + 18, "L1 3.94  L2 2.70  L3 5.00  L4 2.64  L5 2.00  L6 4.90  W1 0.90  W2 0.50  D1 0.50  D2 0.30  D3 0.30  D4 0.50  D5 1.40  D6 1.70 (mm)", 10)
text(o, ox, oy + 5.0 * S, "Reference PCB thickness not published in the note (readme in the TI design, not obtained). Ours: 1.59 mm JLC04161H-7628, antenna region copper-free on every layer.", 10)
# 868 antenna
ox2, oy2 = M, 700
text(o, ox2, 520, "2) Johanson 0868AT43A0020 (datasheet v1.8, page 3 figure): chip 8.0 x 1.8 incl. 1.0 mm pads; meander 7.1 x 5.1, trace 0.5, legs 3.0 and 5.1", 12)
box(o, 0, 0, 1.0, 1.8, "#d98c1f", ox2, oy2 - 0 * S); 
def b2(x0, y0, x1, y1, fill="#d98c1f"):
    o.append(f'<rect x="{ox2 + x0 * S:.1f}" y="{oy2 + y0 * S:.1f}" width="{(x1 - x0) * S:.1f}" height="{(y1 - y0) * S:.1f}" fill="{fill}" stroke="#7a4a00" stroke-width="0.6"/>')
o.pop()
b2(0, 0, 1.0, 1.8); b2(7.0, 0, 8.0, 1.8); b2(1.0, 0.2, 7.0, 1.6, "#cccccc")
b2(7.5, 1.8, 8.0, 5.1); b2(0.9, 4.6, 8.0, 5.1); b2(0.9, 2.1, 1.4, 5.1); b2(1.4, 2.1, 6.5, 2.6)
text(o, ox2, oy2 + 6.0 * S, "Corner placement only: 10 x 11 mm (or 11 x 10 mm) zone with complete ground AND layer clearance free of metal above and below (yellow area in the datasheet); 50 ohm feed line; pi slots required.", 10)
text(o, ox2, oy2 + 6.45 * S, "Meander shape drawn from the datasheet figure; the manufacturer's layout file was not obtained [U].", 10)
# NFC coil
ox3, oy3 = 650, 120
text(o, ox3, 80, "3) NFC coil: 18 x 16 mm, 6 turns, 0.25 / 0.10 mm (calc. 1.43 uH, SLOA241C eq. 2)", 12)
A, P, N = 0.25, 0.35, 6
CW, CH = 18.0 - A, 16.0 - A
pts = [(0.0, 0.0)]
for i in range(N):
    xl, xr, yt, yb = i * P, CW - i * P, i * P, CH - i * P
    pts += [(xr, yt), (xr, yb), (xl, yb)]
    if i < N - 1:
        pts.append((xl, (i + 1) * P))
pl = " ".join(f"{ox3 + 20 + x * 22:.1f},{oy3 + 20 + y * 22:.1f}" for x, y in pts)
o.append(f'<polyline points="{pl}" fill="none" stroke="#d98c1f" stroke-width="{A * 22:.1f}"/>')
ex, ey = pts[-1]
o.append(f'<line x1="{ox3 + 20 + ex * 22:.1f}" y1="{oy3 + 20 + ey * 22:.1f}" x2="{ox3 + 20 - 1.4 * 22:.1f}" y2="{oy3 + 20 + ey * 22:.1f}" stroke="#4c78a8" stroke-width="{A * 22:.1f}" stroke-dasharray="6 3"/>')
text(o, ox3, oy3 + 420, "F.Cu spiral (orange); B.Cu underpass from the inner end to the outer return via (blue dashed).", 10)
text(o, ox3, oy3 + 436, "Pad 1 (outer start) = NFC_COIL_A, pad 2 = GND. No copper on L2, L3 or elsewhere on B.Cu under the window.", 10)
text(o, ox3, oy3 + 452, "TI: 10 mm from metal and from ground planes is recommended; achieved: ESP32 module about 10 mm,", 10)
text(o, ox3, oy3 + 468, "RF shield about 10 mm, ground plane only vertically removed (L2-L4), lateral ground pours not 10 mm [U].", 10)
# ESP keepout
text(o, ox3, 640, "4) ESP32-C3-WROOM-02: base board cut away over module width + 15 mm each side (Espressif figure); antenna 18 x 6 mm;", 12)
text(o, ox3, 658, "our cut-out: x 0-6.0 mm, y 15.5-50 mm; module tip at the board edge, antenna base line at x = 6.0 mm;", 10)
text(o, ox3, 674, "15 mm clear outward and above/below inside the housing is an enclosure requirement (not verifiable here).", 10)
o.append("</svg>")
open(os.path.join(HERE, "drawings", "antenna_geometry.svg"), "w").write("\n".join(o))
