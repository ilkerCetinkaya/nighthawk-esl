import os

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "NH_REVB.pretty")


def pad(num, x, y, w, h, shape="rect"):
    return (f'\t(pad "{num}" smd {shape}\n\t\t(at {x:.3f} {y:.3f})\n\t\t(size {w:.3f} {h:.3f})\n'
            f'\t\t(layers "F.Cu" "F.Mask" "F.Paste")\n\t)')


def rect(layer, x0, y0, x1, y1, width=0.12):
    return (f'\t(fp_rect\n\t\t(start {x0:.3f} {y0:.3f})\n\t\t(end {x1:.3f} {y1:.3f})\n\t\t(stroke\n\t\t\t(width {width})\n\t\t\t(type solid)\n\t\t)\n'
            f'\t\t(fill no)\n\t\t(layer "{layer}")\n\t)')


def write(name, descr, body, ref_y, net_tie=None):
    text = (f'(footprint "{name}"\n\t(version 20260206)\n\t(generator "nighthawk_revb")\n\t(layer "F.Cu")\n\t(descr "{descr}")\n'
            f'\t(property "Reference" "REF**"\n\t\t(at 0 {ref_y:.2f} 0)\n\t\t(layer "F.SilkS")\n\t\t(effects\n\t\t\t(font\n\t\t\t\t(size 1 1)\n\t\t\t\t(thickness 0.15)\n\t\t\t)\n\t\t)\n\t)\n'
            f'\t(property "Value" "{name}"\n\t\t(at 0 {-ref_y:.2f} 0)\n\t\t(layer "F.Fab")\n\t\t(effects\n\t\t\t(font\n\t\t\t\t(size 1 1)\n\t\t\t\t(thickness 0.15)\n\t\t\t)\n\t\t)\n\t)\n'
            f'\t(attr smd)\n' + (f'\t(net_tie_pad_groups "{net_tie}")\n' if net_tie else '') + "\n".join(body) + "\n)\n")
    with open(os.path.join(OUT, f"{name}.kicad_mod"), "w") as handle:
        handle.write(text)


tps = []
for i in range(5):
    y = -1.0 + 0.5 * i
    tps.append(pad(str(i + 1), -0.9, y, 0.6, 0.25))
    tps.append(pad(str(10 - i), 0.75, y, 0.9, 0.25))
tps = [p for p in tps if '(at 0.750 0.000)' not in p]
tps.append(pad("8", 0.55, 0.0, 1.3, 0.25))
tps.append(rect("F.Fab", -1.0, -1.5, 1.0, 1.5))
tps.append(rect("F.CrtYd", -1.5, -1.7, 1.5, 1.7, 0.05))
write("TPS63802DLA_VSON-10_3x2mm", "TI DLA0010A VSON-HR 2x3 mm, land pattern from SLVSEU9D example board layout (pin 8 GND pad 1.3x0.25 mm). Pins 1-5 left, 6-10 right.", tps, -2.2)

ipc = []
for num, x, y in (("6", -0.78, -0.75), ("7", -0.78, -0.25), ("8", -0.78, 0.25), ("9", -0.78, 0.75), ("4", 0.79, -0.75), ("3", 0.79, -0.25), ("2", 0.79, 0.25), ("1", 0.79, 0.75)):
    ipc.append(pad(num, x, y, 0.86, 0.34))
ipc.append(pad("5", 0.0, -1.07, 0.43, 0.66))
ipc.append(pad("10", 0.0, 1.18, 0.43, 0.91))
ipc.append(rect("F.Fab", -0.625, -1.0, 0.625, 1.0))
ipc.append(rect("F.CrtYd", -1.35, -1.75, 1.35, 1.75, 0.05))
write("Johanson_0900PC15A0036_2.0x1.25mm", "Johanson 0900PC15A0036 IPC: land pattern measured from the manufacturer pad/soldermask figure (datasheet v1.1 page 2, scale from the 1.27 mm dimension and the 2.0 x 1.25 mm body); body drawn long axis vertical; left column pins 6-9, right column pins 4-1 (top to bottom), pin 5 top end, pin 10 bottom end (ground). Pad 0.86 x 0.34 at 0.5 mm pitch, ends 0.43 x 0.66 / 0.43 x 0.91. Measured from an image, +-0.03 mm; no dimensioned drawing was published.", ipc, -2.0)

ant = [pad("1", 3.5, 0.0, 1.0, 1.8), pad("2", -3.5, 0.0, 1.0, 1.8), rect("F.Fab", -3.5, -1.0, 3.5, 1.0), rect("F.CrtYd", -4.2, -1.2, 4.2, 1.2, 0.05)]
write("Johanson_0868AT43A0020", "Johanson 0868AT43A0020 868 MHz chip antenna 7x2 mm (datasheet v1.8, mounting figure). Pad 1 feed on the right. Meander copper and ground keepout belong to the board layout.", ant, -2.0)

led = [pad("2", 0.0, -1.75, 1.5, 1.5), pad("1", 0.0, 1.75, 1.5, 1.5), pad("3", -0.65, 0.0, 0.9, 0.9), rect("F.Fab", -1.0, -1.5, 1.0, 1.5), rect("F.CrtYd", -1.2, -2.7, 1.2, 2.7, 0.05)]
for n, d in (("VSMB10940_SideView_3x2", "Vishay VSMB10940 IR emitter, recommended solder pad footprint (datasheet 84170 rev 1.1). Pad 2 anode (top), pad 1 cathode, pad 3 reinforcing pin (non-electrode)."),
             ("VEMD10940F_SideView_3x2", "Vishay VEMD10940F photodiode, same footprint as VSMB10940 (datasheet 84171). Pad 1 K and pad 2 A follow the same terminal order as the emitter: polarity to be confirmed on the part marking.")):
    write(n, d, led, -3.2)

write("IFA_2G4_STACKUP_TBD", "PLACEHOLDER for the 2.4 GHz inverted-F antenna feed point only. Geometry (radiator, short stub, ground keepout) is NOT designed yet; it must be derived and validated for the JLC04161H-7628 stackup.", [pad("1", 0.0, 0.0, 0.5, 0.5), rect("F.CrtYd", -0.6, -0.6, 0.6, 0.6, 0.05)], -1.2)
write("NFC_COIL_28x16", "PLACEHOLDER for the 13.56 MHz coil feed pads only. The 28x16 mm 3-turn coil traces are not drawn yet (layout phase). Pad 1 coil start, pad 2 coil end (ground).", [pad("1", -1.0, 0.0, 1.0, 1.0), pad("2", 1.0, 0.0, 1.0, 1.0), rect("F.CrtYd", -1.6, -0.8, 1.6, 0.8, 0.05)], -1.6)
print(sorted(os.listdir(OUT)))


def fp_poly_rect(x0, y0, x1, y1, layer="F.Cu"):
    return (f'\t(fp_poly\n\t\t(pts\n\t\t\t(xy {x0:.3f} {y0:.3f})\n\t\t\t(xy {x1:.3f} {y0:.3f})\n\t\t\t(xy {x1:.3f} {y1:.3f})\n\t\t\t(xy {x0:.3f} {y1:.3f})\n\t\t)\n'
            f'\t\t(stroke\n\t\t\t(width 0)\n\t\t\t(type solid)\n\t\t)\n\t\t(fill yes)\n\t\t(layer "{layer}")\n\t)')


def fp_line(x0, y0, x1, y1, w, layer):
    return (f'\t(fp_line\n\t\t(start {x0:.3f} {y0:.3f})\n\t\t(end {x1:.3f} {y1:.3f})\n\t\t(stroke\n\t\t\t(width {w})\n\t\t\t(type solid)\n\t\t)\n\t\t(layer "{layer}")\n\t)')


def pth(num, x, y, size, drill):
    return (f'\t(pad "{num}" thru_hole circle\n\t\t(at {x:.3f} {y:.3f})\n\t\t(size {size} {size})\n\t\t(drill {drill})\n\t\t(layers "*.Cu" "*.Mask")\n\t)')


FX, FY = 3.05, 0.25
rects = [(0.5, 4.9, 5.5, 5.4), (0.5, 0.0, 1.4, 4.9), (2.8, 0.0, 3.3, 4.9), (5.0, 2.26, 5.5, 4.9), (5.0, 2.26, 8.0, 2.76), (7.5, 2.26, 8.0, 5.4),
         (7.5, 4.9, 10.2, 5.4), (9.7, 2.26, 10.2, 4.9), (9.7, 2.26, 12.7, 2.76), (12.2, 2.26, 12.7, 5.4), (12.2, 4.9, 14.9, 5.4), (14.4, 0.96, 14.9, 4.9)]
body = [fp_poly_rect(x0 - FX, -(y1 - FY), x1 - FX, -(y0 - FY)) for x0, y0, x1, y1 in rects]
body.append(pad("1", 0.0, 0.0, 0.5, 0.5))
body.append(pth("2", 0.95 - FX, -(0.35 - FY), 0.6, 0.3))
body.append(rect("Dwgs.User", 0.0 - FX, -(5.7 - FY), 15.2 - FX, FY, 0.1))
body.append(rect("F.CrtYd", 0.0 - FX - 0.2, -(5.7 - FY) - 0.2, 15.2 - FX + 0.2, FY + 0.2, 0.05))
write("IFA_AN043_15.2x5.7", "TI AN043 (SWRA117D) figure 3 / table 1: 15.2 x 5.7 mm inverted-F antenna. Dimensions L1 3.94 L2 2.70 L3 5.00 L4 2.64 L5 2.00 L6 4.90 W1 0.90 W2 0.50 D1 0.50 D2 0.30 D3 0.30 D4 0.50 D5 1.40 D6 1.70 mm, reconstructed from the figure (sums check to 15.2 and 5.7). Origin = feed pad 1 centre. Pad 2 = short-stub via to ground. Layer-2 ground edge must end 0.5 mm above the box bottom; no copper elsewhere on any layer inside the box. Reference PCB thickness unknown.", body, -3.5, net_tie="1, 2")

A, GAP, N = 0.25, 0.10, 6
P = A + GAP
CW, CH = 18.0 - A, 16.0 - A
pts = [(0.0, 0.0)]
for i in range(N):
    xl, xr, yt, yb = i * P, CW - i * P, i * P, CH - i * P
    if i > 0:
        pts.append((xl - P, yt))
    pts += [(xr, yt), (xr, yb), (xl, yb)]
    if i < N - 1:
        pts.append((xl, yt + P))
lines = []
cur = (0.0, 0.0)
path = [(0.0, 0.0)]
for i in range(N):
    xl, xr, yt, yb = i * P, CW - i * P, i * P, CH - i * P
    path += [(xr, yt), (xr, yb), (xl, yb)]
    if i < N - 1:
        path += [(xl, (i + 1) * P)]
body = []
for (x0, y0), (x1, y1) in zip(path, path[1:]):
    body.append(fp_line(x0, y0, x1, y1, A, "F.Cu"))
ex, ey = path[-1]
body.append(pad("1", 0.0, 0.0, 0.6, 0.6))
body.append(pth("2", ex, ey, 0.6, 0.3))
body.append(pth("2", -1.4, ey, 0.6, 0.3))
body.append(fp_line(ex, ey, -1.4, ey, A, "B.Cu"))
body.append(rect("F.CrtYd", -1.9, -0.5, CW + 0.5, CH + 0.5, 0.05))
body.append(rect("Dwgs.User", -A / 2, -A / 2, CW + A / 2, CH + A / 2, 0.1))
write("NFC_COIL_18x16_6T", f"13.56 MHz coil, outer 18 x 16 mm, {N} turns, trace {A} mm, gap {GAP} mm (SLOA241C: gap 0.1 mm or less), F.Cu spiral with a B.Cu underpass from the inner end to an outer via (pad 2). Origin = outer start (pad 1). Calculated 1.43 uH (SLOA241C eq. 2), NOT measured. No copper on L2, L3 or the rest of B.Cu inside the window.", body, -1.5, net_tie="1, 2")
print("coil inner end", ex, ey)


def oval_pth(num, x, y, w, h, dw, dh):
    return (f'\t(pad "{num}" thru_hole oval\n\t\t(at {x:.3f} {y:.3f})\n\t\t(size {w} {h})\n\t\t(drill oval {dw} {dh})\n\t\t(layers "*.Cu" "*.Mask")\n\t)')


def npth(x, y, d):
    return (f'\t(pad "" np_thru_hole circle\n\t\t(at {x:.3f} {y:.3f})\n\t\t(size {d} {d})\n\t\t(drill {d})\n\t\t(layers "*.Cu" "*.Mask")\n\t)')


usb = []
PY = -6.86
layout = [(-3.2, ("A1", "B12"), 0.6), (-2.4, ("A4", "B9"), 0.6), (-1.75, ("B8",), 0.3), (-1.25, ("A5",), 0.3), (-0.75, ("B7",), 0.3), (-0.25, ("A6",), 0.3),
          (0.25, ("A7",), 0.3), (0.75, ("B6",), 0.3), (1.25, ("A8",), 0.3), (1.75, ("B5",), 0.3), (2.4, ("B4", "A9"), 0.6), (3.2, ("B1", "A12"), 0.6)]
for x, names, w in layout:
    for n in names:
        usb.append(pad(n, x, PY, w, 1.14))
for sx in (-1, 1):
    usb.append(oval_pth("SH", sx * 4.325, -6.35, 0.9, 2.0, 0.6, 1.7))
    usb.append(oval_pth("SH", sx * 4.325, -2.09, 0.9, 1.7, 0.6, 1.4))
    usb.append(npth(sx * 2.89, -5.79, 0.6))
usb.append(rect("F.Fab", -4.47, -6.52, 4.47, 0.83))
usb.append(rect("F.CrtYd", -4.7, -7.8, 4.7, 1.05, 0.05))
usb.append(fp_line(-4.8, 0.0, 4.8, 0.0, 0.1, "Dwgs.User"))
write("HRO_TYPE-C-31-M-12_DS", "HRO TYPE-C-31-M-12 (LCSC C165948) built from the manufacturer's recommended PCB layout (drawing 2020.12.08): pad row centre 6.86 mm from the PCB edge, pads 1.14 long, 4 x 0.60 and 8 x 0.30 wide, positioning holes 0.6 at +-2.89 / 5.79 from the edge, shell slots at +-4.325 (upper 0.9x2.0 pad, 0.6x1.7 hole, 6.35 from the edge; lower 0.9x1.7 pad, 0.6x1.4 hole, 2.09 from the edge). Origin = connector centre on the PCB edge line (Dwgs.User). Shell front outline (0.83 mm beyond the edge) is NOT from the drawing: 7.35 mm depth from the drawing, back edge position assumed.", usb, -8.5)
