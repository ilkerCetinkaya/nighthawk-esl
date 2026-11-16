import os
import sys
import pcbnew
from pcbnew import ToMM, FromMM, VECTOR2I

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import make_board_b as m

board = pcbnew.LoadBoard(os.path.join(HERE, "NIGHTHAWK_REVB.kicad_pcb"))
pcbnew.ZONE_FILLER(board).Fill(board.Zones())
O = m.ORIGIN
BH = m.BH


def kpt(x, y):
    return VECTOR2I(FromMM(O[0] + x), FromMM(O[1] + BH - y))


def rect_poly(r):
    ps = pcbnew.SHAPE_POLY_SET()
    ps.NewOutline()
    for x, y in ((r[0], r[1]), (r[2], r[1]), (r[2], r[3]), (r[0], r[3])):
        p = kpt(x, y)
        ps.Append(p.x, p.y)
    return ps


def layer_name(l):
    return board.GetLayerName(l)


KO = {
    "ESP32 cut-out (air)": ((0.0, m.NOTCH[1], 6.0, 50.0), "all", ()),
    "2.4 GHz IFA L2-L4 (from y 44.8)": ((m.IFA_BOX[0], m.IFA_BOX[1] + 0.5, m.IFA_BOX[2], m.IFA_BOX[3]), "inner_b", ("ANT1",)),
    "2.4 GHz IFA F.Cu box (from y 44.8)": ((m.IFA_BOX[0], m.IFA_BOX[1] + 0.5, m.IFA_BOX[2], m.IFA_BOX[3]), "F", ("ANT1",)),
    "868 MHz corner zone A (all layers)": (m.ANT868_KO_A, "all", ("ANT2",)),
    "868 MHz corner zone B (all layers, feed corridor y<3 open)": (m.ANT868_KO_B, "all", ("ANT2",)),
    "NFC coil window L2, L3": ((m.COIL[0] - 0.5, m.COIL[1] - 0.5, m.COIL[2] + 0.5, m.COIL[3] + 0.5), "inner", ("ANT3",)),
    "NFC coil window B.Cu (footprints)": ((m.COIL[0], m.COIL[1], m.COIL[2], m.COIL[3]), "B", ("ANT3",)),
    "cable notch keepout (all layers)": (m.CABLE_KO, "all", ()),
}
layers = {"F": [pcbnew.F_Cu], "B": [pcbnew.B_Cu], "inner": [pcbnew.In1_Cu, pcbnew.In2_Cu], "inner_b": [pcbnew.In1_Cu, pcbnew.In2_Cu, pcbnew.B_Cu],
          "all": [pcbnew.F_Cu, pcbnew.In1_Cu, pcbnew.In2_Cu, pcbnew.B_Cu]}
out = []
for name, (r, which, allowed) in KO.items():
    for l in layers[which]:
        issues = []
        for fp in board.GetFootprints():
            if fp.GetReference() in allowed:
                continue
            for pad in fp.Pads():
                if not pad.IsOnLayer(l):
                    continue
                bb = pad.GetBoundingBox()
                x0, x1 = ToMM(bb.GetLeft()) - O[0], ToMM(bb.GetRight()) - O[0]
                y0, y1 = BH - (ToMM(bb.GetBottom()) - O[1]), BH - (ToMM(bb.GetTop()) - O[1])
                if not (x1 <= r[0] or r[2] <= x0 or y1 <= r[1] or r[3] <= y0):
                    issues.append(f"{fp.GetReference()} pad {pad.GetNumber()}")
        for t in board.GetTracks():
            if t.IsOnLayer(l):
                bb = t.GetBoundingBox()
                x0, x1 = ToMM(bb.GetLeft()) - O[0], ToMM(bb.GetRight()) - O[0]
                y0, y1 = BH - (ToMM(bb.GetBottom()) - O[1]), BH - (ToMM(bb.GetTop()) - O[1])
                if not (x1 <= r[0] or r[2] <= x0 or y1 <= r[1] or r[3] <= y0):
                    issues.append("track/via")
        area = 0.0
        for z in board.Zones():
            if z.GetIsRuleArea() or not z.IsOnLayer(l):
                continue
            fill = z.GetFilledPolysList(l)
            if fill.OutlineCount() == 0:
                continue
            inter = pcbnew.SHAPE_POLY_SET(fill)
            inter.BooleanIntersection(rect_poly(r))
            area += inter.Area() / 1e12
        out.append((name, layer_name(l), issues, area))
print("Keepout verification (KiCad zone fill, pads, tracks/vias); areas in mm^2 of filled copper inside each keepout")
for name, ln, issues, area in out:
    print(f"  {name:38s} {ln:6s} foreign pads/tracks: {len(issues):2d} {issues[:3]}  zone fill inside: {area:.3f} mm2")
