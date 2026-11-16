import json
import math
import os
import sys

import pcbnew
from pcbnew import VECTOR2I, FromMM, ToMM

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import design

SUPPORT = "/Applications/KiCad/KiCad.app/Contents/SharedSupport"
HW = os.path.dirname(HERE)
PCB = os.path.join(HW, "NIGHTHAWK.kicad_pcb")
ORIGIN = (100.0, 100.0)
H = design.BOARD_H
RF_NETS = ("RF_IN", "RF_A", "RF_B", "RF_TEST")


def mm(v):
    return FromMM(v)


def pt(x, y):
    return VECTOR2I(mm(ORIGIN[0] + x), mm(ORIGIN[1] + H - y))


def from_pt(p):
    return (ToMM(p.x) - ORIGIN[0], H - (ToMM(p.y) - ORIGIN[1]))


def load_footprint(fp_id):
    lib, name = fp_id.split(":")
    fp = pcbnew.FootprintLoad(f"{SUPPORT}/footprints/{lib}.pretty", name)
    if fp is None:
        raise RuntimeError(f"footprint not found: {fp_id}")
    return fp


def get_net(board, name):
    net = board.FindNet(name)
    if net is None:
        net = pcbnew.NETINFO_ITEM(board, name)
        board.Add(net)
    return net


def world_rect(fp):
    bb = fp.GetBoundingBox(False)
    x0, y0 = ToMM(bb.GetLeft()) - ORIGIN[0], H - (ToMM(bb.GetBottom()) - ORIGIN[1])
    x1, y1 = ToMM(bb.GetRight()) - ORIGIN[0], H - (ToMM(bb.GetTop()) - ORIGIN[1])
    return (x0, y0, x1, y1)


def overlap(a, b, m=0.45):
    return not (a[2] + m <= b[0] or b[2] + m <= a[0] or a[3] + m <= b[1] or b[3] + m <= a[1])


def add_outline(board):
    w, h, r = design.BOARD_W, design.BOARD_H, design.BOARD_CORNER

    def seg(a, b):
        s = pcbnew.PCB_SHAPE(board)
        s.SetShape(pcbnew.SHAPE_T_SEGMENT)
        s.SetLayer(pcbnew.Edge_Cuts)
        s.SetStart(pt(*a))
        s.SetEnd(pt(*b))
        s.SetWidth(mm(0.1))
        board.Add(s)

    def arc(center, start, end):
        s = pcbnew.PCB_SHAPE(board)
        s.SetShape(pcbnew.SHAPE_T_ARC)
        a0 = math.atan2(start[1] - center[1], start[0] - center[0])
        a1 = math.atan2(end[1] - center[1], end[0] - center[0])
        d = a1 - a0
        while d > math.pi:
            d -= 2 * math.pi
        while d < -math.pi:
            d += 2 * math.pi
        am = a0 + d / 2
        mid = (center[0] + r * math.cos(am), center[1] + r * math.sin(am))
        s.SetArcGeometry(pt(*start), pt(*mid), pt(*end))
        s.SetLayer(pcbnew.Edge_Cuts)
        s.SetWidth(mm(0.1))
        board.Add(s)

    seg((r, 0), (w - r, 0))
    seg((w, r), (w, h - r))
    seg((w - r, h), (r, h))
    seg((0, h - r), (0, r))
    arc((r, r), (0, r), (r, 0))
    arc((w - r, r), (w - r, 0), (w, r))
    arc((w - r, h - r), (w, h - r), (w - r, h))
    arc((r, h - r), (r, h), (0, h - r))


def add_zone(board, layer, net, priority=0, clearance=0.2, name=""):
    z = pcbnew.ZONE(board)
    z.SetLayer(layer)
    z.SetNet(net)
    z.SetMinThickness(mm(0.2))
    z.SetLocalClearance(mm(clearance))
    z.SetPadConnection(pcbnew.ZONE_CONNECTION_THERMAL)
    z.SetThermalReliefGap(mm(0.25))
    z.SetThermalReliefSpokeWidth(mm(0.3))
    z.SetIslandRemovalMode(pcbnew.ISLAND_REMOVAL_MODE_ALWAYS)
    z.SetAssignedPriority(priority)
    if name:
        z.SetZoneName(name)
    outline = z.Outline()
    outline.NewOutline()
    for x, y in ((0.0, 0.0), (design.BOARD_W, 0.0), (design.BOARD_W, H), (0.0, H)):
        outline.Append(pt(x, y).x, pt(x, y).y)
    board.Add(z)
    return z


def add_text(board, text, x, y, size=1.0, layer=pcbnew.F_SilkS, rot=0, bold=False):
    t = pcbnew.PCB_TEXT(board)
    t.SetText(text)
    t.SetLayer(layer)
    t.SetPosition(pt(x, y))
    t.SetTextSize(VECTOR2I(mm(size), mm(size)))
    t.SetTextThickness(mm(max(0.12, size * 0.14)))
    t.SetBold(bold)
    t.SetTextAngleDegrees(rot)
    board.Add(t)


def place_all(board):
    placed = {}
    rects = []
    gnd = get_net(board, "GND")

    def instantiate(p):
        fp = load_footprint(p["fp"])
        fp.SetReference(p["ref"])
        fp.SetValue(p["value"])
        for pad in fp.Pads():
            name = p["nets"].get(pad.GetNumber())
            if name:
                pad.SetNet(get_net(board, name))
        if p["dnp"]:
            fp.SetDNP(True)
        fp.SetOrientationDegrees(p["rot"])
        board.Add(fp)
        return fp

    fixed = [p for p in design.PARTS if p["pos"]]
    for p in fixed:
        fp = instantiate(p)
        fp.SetPosition(pt(*p["pos"]))
        placed[p["ref"]] = fp
        r = world_rect(fp)
        if p["ref"] == "U1":
            r = (p["pos"][0] - 10.0, p["pos"][1] - 11.5, p["pos"][0] + 10.0, p["pos"][1] + 10.5)
        rects.append((p["ref"], r))
    for i, (x, y) in enumerate(design.HOLES, start=1):
        fp = load_footprint("MountingHole:MountingHole_2.7mm_M2.5_Pad_TopBottom")
        fp.SetReference(f"H{i}")
        fp.SetValue("M2.5")
        fp.SetPosition(pt(x, y))
        for pad in fp.Pads():
            pad.SetNet(gnd)
        board.Add(fp)
        placed[f"H{i}"] = fp
        rects.append((f"H{i}", (x - 3.2, y - 3.2, x + 3.2, y + 3.2)))

    order = sorted([p for p in design.PARTS if not p["pos"]], key=lambda p: (p["region"] or "", -ord(p["ref"][0])))
    failures = []
    for p in order:
        fp = instantiate(p)
        fp.SetPosition(pt(0, 0))
        w = world_rect(fp)
        fw, fh = w[2] - w[0], w[3] - w[1]
        cx_off, cy_off = -(w[0] + w[2]) / 2, -(w[1] + w[3]) / 2
        x0, y0, x1, y1 = design.REGIONS[p["region"]]
        spot = None
        y = y1 - fh / 2
        while y >= y0 + fh / 2 - 1e-9 and spot is None:
            x = x0 + fw / 2
            while x <= x1 - fw / 2 + 1e-9:
                cand = (x - fw / 2, y - fh / 2, x + fw / 2, y + fh / 2)
                if not any(overlap(cand, r) for _, r in rects):
                    spot = (x, y, cand)
                    break
                x += 0.25
            y -= 0.25
        if spot is None:
            failures.append((p["ref"], p["region"]))
            board.Remove(fp)
            continue
        fp.SetPosition(pt(spot[0] + cx_off + 0.0, spot[1] + cy_off + 0.0))
        rects.append((p["ref"], spot[2]))
        placed[p["ref"]] = fp
    if failures:
        raise RuntimeError(f"could not place: {failures}")
    return placed


def tune_text(placed):
    for ref, fp in placed.items():
        fp.Reference().SetTextSize(VECTOR2I(mm(0.8), mm(0.8)))
        fp.Reference().SetTextThickness(mm(0.12))
        fp.Value().SetVisible(False)
        if ref.startswith(("R", "C", "TP", "FB", "H", "D1", "SW")) and not ref.startswith(("RF",)):
            fp.Reference().SetVisible(False)


def silk(board):
    add_text(board, "NIGHTHAWK", 40.0, 40.0, 2.4, rot=0, bold=True)
    add_text(board, "ESL SECURITY RESEARCH", 40.0, 37.0, 1.1)
    add_text(board, "REV A", 40.0, 34.8, 1.0)
    labels = [
        ("USB", 24.0, 12.5), ("RF IN", 8.0, 72.0), ("RF TEST", 8.0, 56.0), ("EXT MODULE 1", 71.0, 76.5),
        ("EXT MODULE 2", 71.0, 28.0), ("UART", 33.0, 10.5), ("DEBUG", 45.0, 10.5), ("RESET", 58.0, 69.5),
        ("BOOT", 66.0, 69.5), ("POWER", 40.0, 29.0), ("INTERLOCK", 9.0, 46.0),
    ]
    for text, x, y in labels:
        add_text(board, text, x, y, 0.8)


def stackup(board):
    try:
        bds = board.GetDesignSettings()
        stack = bds.GetStackupDescriptor()
        stack.BuildDefaultStackupList(bds, 4)
        return True
    except Exception as exc:
        print("stackup not set:", exc)
        return False


def build():
    board = pcbnew.CreateEmptyBoard()
    board.SetCopperLayerCount(4)
    bds = board.GetDesignSettings()
    bds.SetBoardThickness(mm(1.6))
    bds.m_TrackMinWidth = mm(0.1)
    bds.m_MinClearance = mm(0.15)
    bds.m_ViasMinSize = mm(0.5)
    bds.m_MinThroughDrill = mm(0.2)
    bds.m_CopperEdgeClearance = mm(0.3)
    stackup(board)
    board.SetLayerType(pcbnew.In1_Cu, pcbnew.LT_POWER)
    board.GetDesignSettings().SetAuxOrigin(pt(0, 0))
    placed = place_all(board)
    tune_text(placed)
    add_outline(board)
    silk(board)
    gnd = get_net(board, "GND")
    v33 = get_net(board, "3V3")
    add_zone(board, pcbnew.In1_Cu, gnd, 0, 0.2, "GND_PLANE")
    add_zone(board, pcbnew.F_Cu, gnd, 0, 0.2, "GND_TOP")
    add_zone(board, pcbnew.B_Cu, gnd, 0, 0.2, "GND_BOTTOM")
    return board, placed


def add_in2_pour(board):
    add_zone(board, pcbnew.In2_Cu, get_net(board, "3V3"), 0, 0.2, "3V3_POUR")


def save(board, path=PCB):
    pcbnew.SaveBoard(path, board)


if __name__ == "__main__":
    board, placed = build()
    pcbnew.ZONE_FILLER(board).Fill(board.Zones())
    save(board)
    print("saved", PCB, "footprints", len(placed))
