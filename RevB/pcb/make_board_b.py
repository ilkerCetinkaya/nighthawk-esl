import json
import math
import os
import sys
import xml.etree.ElementTree as ET

import pcbnew
from pcbnew import VECTOR2I, FromMM, ToMM

HERE = os.path.dirname(os.path.abspath(__file__))
SCH = os.path.join(os.path.dirname(HERE), "schematic")
sys.path.insert(0, SCH)
import design_b as d

SUPPORT = "/Applications/KiCad/KiCad.app/Contents/SharedSupport"
PCB = os.path.join(HERE, "NIGHTHAWK_REVB.kicad_pcb")
ORIGIN = (100.0, 100.0)
BW, BH = 80.0, 50.0
NOTCH = (0.0, 15.0, 6.0, 50.0)
CABLE_NOTCH = (36.7, 0.0, 43.3, 4.2)
CABLE_KO = (36.0, 0.0, 44.0, 4.5)
COIL = (30.1, 33.0, 48.1, 49.0)
IFA_BOX = (64.8, 44.3, 80.0, 50.0)
ANT868_ZONE = (70.0, 0.0, 80.0, 11.0)
ANT868_KO_A = (71.3, 0.0, 80.0, 11.0)
ANT868_KO_B = (70.0, 3.0, 71.3, 11.0)
SH1_C = (68.85, 26.0)
CAN_INNER = 9.3
SKIP_TP_FP = "TestPoint:TestPoint_Pad_D1.0mm"
ORIGIN_PLACED = {"J1": (58.0, 0.0, 0), "U1": (13.15, 39.6, 90), "ANT1": (67.85, 44.55, 0), "ANT3": (30.225, 48.875, 0)}
ORIGIN_RECT = {"J1": (53.3, -0.9, 62.7, 7.9), "U1": (0.0, 29.9, 20.3, 49.3), "ANT1": IFA_BOX, "ANT3": (28.2, 33.0, 48.1, 49.0)}

PLACE_GAP = float(os.environ.get('PLACE_GAP', '0.6'))

RF_RESERVED = [
    (69.9, 22.9, 74.8, 26.7),
    (77.7, 22.9, 78.4, 33.0),
    (74.8, 32.0, 78.4, 35.5),
    (74.8, 35.0, 75.5, 38.4),
    (62.5, 37.6, 75.5, 38.4),
    (70.5, 38.0, 71.5, 43.5),
    (62.5, 38.0, 63.3, 43.5),
    (63.6, 38.0, 64.3, 40.6),
    (64.6, 43.0, 72.3, 44.4),
    (76.9, 17.5, 77.9, 25.0),
    (74.8, 13.0, 77.9, 18.8),
    (74.8, 13.1, 75.5, 16.5),
    (68.8, 13.1, 75.5, 13.9),
    (68.8, 10.0, 70.0, 13.9),
    (67.7, 1.2, 69.9, 10.9),
    (58.5, 7.6, 68.3, 8.2),
    (58.5, 7.6, 59.2, 10.9),
]
RF_RESERVED_B_ONLY = [
    (57.8, 15.0, 59.6, 37.0),
    (77.8, 15.0, 79.9, 37.0),
    (57.8, 15.0, 79.9, 16.6),
    (57.8, 35.4, 79.9, 37.0),
]
RF_RESERVED_BOTH = [
    (76.8, 21.6, 77.6, 25.1),
    (74.20, 23.16, 75.80, 24.76),
    (73.80, 21.55, 75.40, 23.15),
    (69.15, 41.17, 70.75, 42.77),
    (69.15, 38.23, 70.75, 39.83),
    (72.10, 40.06, 73.70, 41.66),
    (64.20, 41.60, 65.80, 43.20),
    (75.44, 26.60, 77.04, 28.20),
    (76.40, 23.90, 78.00, 25.50),
    (76.40, 21.20, 78.00, 22.80),
    (66.60, 8.20, 68.20, 9.80),
    (66.60, 2.80, 68.20, 4.40),
    (63.2, 24.2, 68.8, 29.8),
]

FIXED = {
    "TP10": (70.8, 13.4, 0, "B"),
    "TP11": (73.0, 13.4, 0, "B"),
    "TP12": (75.2, 13.4, 0, "B"),
    "TP13": (77.4, 13.4, 0, "B"),
    "R29": (69.2, 10.8, 270, "F"),
    "C37": (68.72, 9.0, 180, "F"),
    "R30": (68.72, 7.9, 180, "F"),
    "L4": (69.2, 6.0, 270, "F"),
    "R31": (68.0, 6.0, 270, "F"),
    "C38": (68.72, 3.6, 180, "F"),
    "C34": (75.75, 26.45, 0, "F"),
    "C35": (76.0, 24.7, 0, "F"),
    "R26": (76.02, 23.22, 0, "F"),
    "C36": (71.45, 40.86, 0, "F"),
    "R28": (71.47, 43.36, 0, "F"),
    "R27": (64.47, 40.61, 0, "F"),
    "L3": (64.47, 43.36, 0, "F"),
    "U1": (13.15, 39.6, 90, "F"),
    "J1": (58.0, 0.0, 0, "F"),
    "J2": (40.0, 9.8, 0, "F"),
    "C84": (65.9, 42.88, 270, "F"),
    "Y2": (72.59, 28.4, 0, "F"),
    "J3": (68.0, 40.5, 0, "F"),
    "J4": (60.0, 11.3, 0, "F"),
    "ANT1": (67.85, 44.55, 0, "F"),
    "ANT2": (75.0, 1.9, 180, "F"),
    "ANT3": (30.225, 48.875, 0, "F"),
    "SH1": (SH1_C[0], SH1_C[1], 0, "F"),
    "J5": (52.0, 21.5, 0, "F"),
    "J6": (2.6, 8.0, 0, "F"),
    "J7": (6.4, 8.0, 0, "F"),
    "D2": (32.0, 2.6, 270, "F"),
    "D3": (48.75, 2.6, 270, "F"),
    "U7": (66.0, 27.0, 180, "F"),
    "U8": (73.5, 24.0, 0, "F"),
    "U9": (38.5, 23.0, 0, "F"),
}


def _both(r):
    return [("F", r), ("B", r)]


REGIONS = {
    "FLASH_F": _both((9.0, 21.5, 29.0, 29.4)) + _both((47.0, 26.5, 57.0, 32.4)),
    "DIG_B": [("B", (9.0, 11.0, 29.0, 21.0)), ("F", (9.0, 11.0, 29.0, 21.0)), ("B", (22.0, 0.5, 34.5, 10.0)), ("B", (47.0, 26.5, 57.0, 32.4)), ("F", (47.0, 26.5, 57.0, 32.4))],
    "IR_F": _both((44.9, 0.5, 52.2, 14.2)) + _both((44.9, 14.4, 51.8, 17.6)) + _both((36.0, 14.5, 44.8, 17.6)),
    "NFC_F": _both((31.0, 14.0, 46.5, 31.0)),
    "NFC_TANK": _both((21.5, 31.0, 28.0, 48.5)),
    "IR_LED": _both((28.5, 4.4, 35.0, 10.5)),
    "RF_CAN": [("F", (SH1_C[0] - CAN_INNER, SH1_C[1] - CAN_INNER, SH1_C[0] + CAN_INNER, SH1_C[1] + CAN_INNER))],
    "ANT24_PI": [("F", (60.5, 37.6, 80.0, 43.9))],
    "ANT868_PI": [("F", (64.0, 0.5, 69.8, 9.6))],
    "TP_B2": [("B", (69.8, 11.6, 79.8, 15.0)), ("B", (66.0, 13.6, 69.8, 15.2)), ("B", (79.8, 11.6, 79.9, 15.0))],
    "PWR_F": [("F", (52.5, 10.5, 69.5, 15.0)), ("B", (52.5, 10.5, 69.5, 15.0)), ("B", (64.0, 0.5, 69.8, 9.6))],
    "REG_B": [("B", (9.0, 0.5, 21.0, 10.5)), ("F", (9.0, 0.5, 21.0, 10.5))],
    "UI_F": _both((22.0, 11.0, 30.0, 21.0)) + _both((22.0, 0.5, 34.5, 10.0)),
}
TIGHT_REGIONS = ("RF_CAN", "ANT24_PI", "ANT868_PI", "IR_LED", "TP_B2", "NFC_TANK")
OVERFLOW = [("B", (50.5, 17.0, 76.0, 42.5)), ("F", (49.5, 32.0, 59.5, 42.5)), ("B", (50.0, 43.0, 62.0, 49.0)), ("B", (24.0, 24.0, 33.5, 31.5)), ("B", (35.5, 27.0, 47.0, 31.5))]
if os.environ.get("USE_OVERFLOW", "1") == "1":
    for _k in ("FLASH_F", "DIG_B", "IR_F", "NFC_F", "PWR_F", "REG_B", "UI_F"):
        REGIONS[_k] = REGIONS[_k] + OVERFLOW
ANCHOR_REGION = {
    "U2": "FLASH_F", "D1": "PWR_F", "F1": "PWR_F", "U3": "PWR_F", "U4": "REG_B", "U5": "REG_B", "U6": "REG_B",
    "Y1": "RF_CAN", "Y2": "RF_CAN", "Y3": "NFC_F", "Q1": "IR_F", "U10": "IR_F", "U11": "IR_F", "U12": "IR_F",
    "SW1": "UI_F", "SW2": "UI_F", "SW3": "UI_F", "SW4": "UI_F", "U21": "DIG_B", "U22": "DIG_B",
}
for n in range(13, 21):
    ANCHOR_REGION[f"U{n}"] = "DIG_B"
OVERRIDE = {"Q1": "IR_LED", "R43": "IR_LED", "R44": "IR_LED", "R45": "IR_LED", "TP14": "FLASH_F", "TP29": "FLASH_F", "TP30": "FLASH_F", "TP31": "FLASH_F", "TP32": "FLASH_F", "TP33": "FLASH_F", "TP10": "TP_B2", "TP11": "TP_B2", "TP12": "TP_B2", "TP13": "TP_B2", "FB1": "IR_F", "FB2": "NFC_F", "FB3": "NFC_F",
            "C36": "ANT24_PI", "L3": "ANT24_PI", "R28": "ANT24_PI", "C84": "ANT24_PI", "R27": "ANT24_PI",
            "R29": "ANT868_PI", "R30": "ANT868_PI", "C37": "ANT868_PI", "L4": "ANT868_PI", "C38": "ANT868_PI", "R31": "ANT868_PI",
            "C61": "NFC_TANK", "C62": "NFC_TANK", "R42": "NFC_TANK", "C63": "NFC_TANK", "C64": "NFC_TANK"}
ANCHORS = {"U", "J", "Y", "Q", "D", "F", "SW", "ANT", "SH"}


def mm(v):
    return FromMM(v)


def pt(x, y):
    return VECTOR2I(mm(ORIGIN[0] + x), mm(ORIGIN[1] + BH - y))


def load_footprint(fp_id):
    lib, name = fp_id.split(":")
    path = os.path.join(SCH, "NH_REVB.pretty") if lib == "NH_REVB" else f"{SUPPORT}/footprints/{lib}.pretty"
    fp = pcbnew.FootprintLoad(path, name)
    if fp is None:
        raise RuntimeError(f"footprint not found: {fp_id}")
    return fp


def get_net(board, name):
    net = board.FindNet(name)
    if net is None:
        net = pcbnew.NETINFO_ITEM(board, name)
        board.Add(net)
    return net


def crt_rect(fp):
    bb = fp.GetCourtyard(pcbnew.F_CrtYd if not fp.IsFlipped() else pcbnew.B_CrtYd).BBox()
    if bb.GetWidth() == 0:
        bb = fp.GetBoundingBox(False)
    return (ToMM(bb.GetLeft()) - ORIGIN[0], BH - (ToMM(bb.GetBottom()) - ORIGIN[1]), ToMM(bb.GetRight()) - ORIGIN[0], BH - (ToMM(bb.GetTop()) - ORIGIN[1]))


def overlap(a, b, m=0.15):
    return not (a[2] + m <= b[0] or b[2] + m <= a[0] or a[3] + m <= b[1] or b[3] + m <= a[1])


def has_tht(fp):
    return any(p.GetAttribute() in (pcbnew.PAD_ATTRIB_PTH, pcbnew.PAD_ATTRIB_NPTH) for p in fp.Pads())


def load_nets():
    root = ET.parse(os.path.join(SCH, "nets.xml")).getroot()
    pinnet = {}
    for n in root.find("nets"):
        for x in n.findall("node"):
            pinnet.setdefault(x.get("ref"), {})[x.get("pin")] = n.get("name")
    return pinnet


def parents():
    out, cur = {}, {}
    for p in d.PARTS:
        pre = "".join(c for c in p["ref"] if c.isalpha())
        if pre in ANCHORS:
            cur[p["sheet"]] = p["ref"]
            out[p["ref"]] = p["ref"]
        else:
            out[p["ref"]] = cur.get(p["sheet"])
    return out


def region_for(p, par):
    ref = p["ref"]
    if ref in OVERRIDE:
        return OVERRIDE[ref]
    anchor = par[ref]
    if anchor in ANCHOR_REGION:
        return ANCHOR_REGION[anchor]
    if anchor in FIXED:
        return {"U1": "FLASH_F", "J1": "PWR_F", "J2": "PWR_F", "U7": "RF_CAN", "U8": "RF_CAN", "U9": "NFC_F", "D2": "IR_F", "D3": "IR_F",
                "ANT1": "RF_CAN", "ANT2": "RF_CAN", "J3": "RF_CAN", "J4": "RF_CAN", "J5": "RF_CAN", "ANT3": "NFC_F", "SH1": "RF_CAN",
                "J6": "DIG_B", "J7": "DIG_B", "J8": "NFC_F"}[anchor]
    return "DIG_B"


def outline(board):
    pts = [(7.0, 17.0), (0.0 + 7.0, 17.0)]
    poly = [(7.0, 17.0), (7.0, 0.0), (CABLE_NOTCH[0], 0.0), (CABLE_NOTCH[0], CABLE_NOTCH[3]), (CABLE_NOTCH[2], CABLE_NOTCH[3]), (CABLE_NOTCH[2], 0.0), (BW, 0.0), (BW, BH), (7.0, BH)]
    poly = [(0.0, 0.0)] + poly[1:] if False else poly
    full = [(0.0, 0.0), (CABLE_NOTCH[0], 0.0), (CABLE_NOTCH[0], CABLE_NOTCH[3]), (CABLE_NOTCH[2], CABLE_NOTCH[3]), (CABLE_NOTCH[2], 0.0), (BW, 0.0), (BW, BH), (NOTCH[2], BH), (NOTCH[2], NOTCH[1]), (0.0, NOTCH[1])]
    for a, b in zip(full, full[1:] + full[:1]):
        s = pcbnew.PCB_SHAPE(board)
        s.SetShape(pcbnew.SHAPE_T_SEGMENT)
        s.SetLayer(pcbnew.Edge_Cuts)
        s.SetStart(pt(*a))
        s.SetEnd(pt(*b))
        s.SetWidth(mm(0.1))
        board.Add(s)
    return full


def keepout(board, name, rect, layers, tracks=True, vias=True, pour=True, fps=False):
    z = pcbnew.ZONE(board)
    z.SetIsRuleArea(True)
    z.SetZoneName(name)
    ls = pcbnew.LSET()
    for l in layers:
        ls.AddLayer(l)
    z.SetLayerSet(ls)
    z.SetDoNotAllowTracks(tracks)
    z.SetDoNotAllowVias(vias)
    z.SetDoNotAllowZoneFills(pour)
    z.SetDoNotAllowPads(False)
    z.SetDoNotAllowFootprints(fps)
    o = z.Outline()
    o.NewOutline()
    x0, y0, x1, y1 = rect
    for x, y in ((x0, y0), (x1, y0), (x1, y1), (x0, y1)):
        p = pt(x, y)
        o.Append(p.x, p.y)
    board.Add(z)


def add_text(board, text, x, y, size=1.0, layer=pcbnew.F_SilkS):
    t = pcbnew.PCB_TEXT(board)
    t.SetText(text)
    t.SetLayer(layer)
    t.SetPosition(pt(x, y))
    t.SetTextSize(VECTOR2I(mm(size), mm(size)))
    t.SetTextThickness(mm(max(0.12, size * 0.14)))
    board.Add(t)


def build():
    pinnet = load_nets()
    par = parents()
    board = pcbnew.CreateEmptyBoard()
    board.SetCopperLayerCount(4)
    bds = board.GetDesignSettings()
    bds.SetBoardThickness(mm(1.6))
    bds.m_TrackMinWidth = mm(0.1)
    bds.m_MinClearance = mm(0.15)
    bds.m_HoleClearance = mm(0.2)
    bds.m_ViasMinSize = mm(0.45)
    bds.m_MinThroughDrill = mm(0.2)
    bds.m_CopperEdgeClearance = mm(0.3)
    bds.m_MinThroughDrill = mm(0.2)
    try:
        st = bds.GetStackupDescriptor()
        st.BuildDefaultStackupList(bds, 4)
    except Exception as exc:
        print("stackup:", exc)
    rects = {"F": [], "B": []}
    for i, rr in enumerate(RF_RESERVED):
        rects["F"].append(("RFRES%d" % i, rr))
    for i, rr in enumerate(RF_RESERVED_B_ONLY):
        rects["B"].append(("RFRESRING%d" % i, rr))
    for i, rr in enumerate(RF_RESERVED_BOTH):
        rects["F"].append(("RFRESB%d" % i, rr))
        rects["B"].append(("RFRESB%d" % i, rr))
    placed = {}
    info = {}

    def instantiate(p, rot, side):
        fp_id = p["fp"]
        if p["ref"].startswith("TP"):
            fp_id = SKIP_TP_FP
        fp = load_footprint(fp_id)
        fp.SetReference(p["ref"])
        fp.SetValue(p["value"])
        for pad in fp.Pads():
            net = pinnet.get(p["ref"], {}).get(pad.GetNumber())
            if net and not net.startswith("unconnected"):
                pad.SetNet(get_net(board, net))
        if p["dnp"]:
            fp.SetDNP(True)
        board.Add(fp)
        fp.SetOrientationDegrees(rot)
        if side == "B":
            fp.Flip(fp.GetPosition(), pcbnew.FLIP_DIRECTION_LEFT_RIGHT)
        return fp

    def put(fp, cx, cy):
        fp.SetPosition(pt(0, 0))
        r = crt_rect(fp)
        ox, oy = -(r[0] + r[2]) / 2, -(r[1] + r[3]) / 2
        fp.SetPosition(pt(cx + ox, cy + oy))
        return crt_rect(fp)

    def register(ref, fp, rect, side):
        if ref == "SH1":
            cx, cy = SH1_C
            e = 10.75
            i = 9.75
            for bar in ((cx - e, cy - e, cx + e, cy - i), (cx - e, cy + i, cx + e, cy + e), (cx - e, cy - e, cx - i, cy + e), (cx + i, cy - e, cx + e, cy + e)):
                rects["F"].append((ref, bar))
            return
        sides = ("F", "B") if has_tht(fp) else (side,)
        for s in sides:
            rects[s].append((ref, rect))

    by_ref = {p["ref"]: p for p in d.PARTS}
    for ref, (x, y, rot, side) in FIXED.items():
        p = by_ref[ref]
        fp = instantiate(p, rot, side)
        if ref in ORIGIN_PLACED:
            ox, oy, orot = ORIGIN_PLACED[ref]
            fp.SetPosition(pt(ox, oy))
            r = ORIGIN_RECT[ref]
            both_layers = ref == "ANT3"
        else:
            r = put(fp, x, y)
            both_layers = False
        if both_layers:
            rects["F"].append((ref, r))
            rects["B"].append((ref, r))
        else:
            register(ref, fp, r, side)
        placed[ref] = fp
        info[ref] = dict(x=x, y=y, rot=rot, side=side, rect=[round(v, 2) for v in r])
    failures = []
    order = [p for p in d.PARTS if p["ref"] not in FIXED and p["fp"]]
    prio = {"U": 0, "Y": 0, "Q": 0, "D": 1, "F": 1, "SW": 1}
    order.sort(key=lambda p: (prio.get("".join(c for c in p["ref"] if c.isalpha()), 3), 0))
    def pin_target(p, region_rects):
        refs = set()
        for net in pinnet.get(p["ref"], {}).values():
            if net in ("GND",):
                continue
            refs.add(net)
        best = None
        for q in placed.values():
            if q.GetReference() == p["ref"] or q.GetReference().startswith(("TP", "R", "C", "L", "FB")):
                continue
            for pad in q.Pads():
                if pad.GetNet() and pad.GetNetname() in refs and pad.GetNetname() not in ("3V3", "3V6", "3V3_RF", "3V3_A", "SYS"):
                    pos = pad.GetPosition()
                    cand = (ToMM(pos.x) - ORIGIN[0], BH - (ToMM(pos.y) - ORIGIN[1]))
                    if any(r[0] <= cand[0] <= r[2] + 3 and r[1] - 3 <= cand[1] <= r[3] + 3 for r in region_rects):
                        best = cand
                        break
            if best:
                break
        if not best:
            r = region_rects[0]
            best = ((r[0] + r[2]) / 2, (r[1] + r[3]) / 2)
        return best

    for p in order:
        rname = region_for(p, par)
        rlist = REGIONS[rname]
        primary = rlist[0][0]
        if p["ref"] in ("U1",):
            continue
        fp = instantiate(p, 0, "F")
        done = False
        tgt = pin_target(p, [r for _, r in rlist])
        for rot in (0, 90):
            fp.SetOrientationDegrees(rot)
            fp.SetPosition(pt(0, 0))
            r0 = crt_rect(fp)
            w, h = r0[2] - r0[0], r0[3] - r0[1]
            cands = []
            for side, (x0, y0, x1, y1) in rlist:
                x = x0 + w / 2
                while x <= x1 - w / 2 + 1e-9:
                    y = y0 + h / 2
                    while y <= y1 - h / 2 + 1e-9:
                        cands.append((math.hypot(x - tgt[0], y - tgt[1]) + (0.0 if side == primary else 1.5), side, x, y))
                        y += 0.25
                    x += 0.25
                    pass
            cands.sort()
            for _, side, x, y in cands:
                gap_ = 0.0 if rname in TIGHT_REGIONS else (0.2 if p["ref"] in ("U21", "U22") else PLACE_GAP)
                rect = (x - w / 2 - gap_, y - h / 2 - gap_, x + w / 2 + gap_, y + h / 2 + gap_)
                sides = ("F", "B") if has_tht(fp) else (side,)
                if not any(overlap(rect, r) for s_ in sides for _, r in rects[s_]):
                    done = (x, y, rect, rot, side)
                    break
            if done:
                break
        if not done:
            print('DBG fail', p['ref'], rname, 'w,h', round(w,2), round(h,2), 'cands', len(cands), 'regions', [(sd, tuple(round(v,1) for v in rr)) for sd, rr in rlist])
            failures.append((p["ref"], rname, p["fp"].split(":")[-1]))
            board.Remove(fp)
            continue
        x, y, rect, rot, side = done
        fp.SetOrientationDegrees(rot)
        if side == "B":
            fp.Flip(fp.GetPosition(), pcbnew.FLIP_DIRECTION_LEFT_RIGHT)
        r = put(fp, x, y)
        register(p["ref"], fp, r, side)
        placed[p["ref"]] = fp
        info[p["ref"]] = dict(x=round(x, 2), y=round(y, 2), rot=rot, side=side, region=rname, rect=[round(v, 2) for v in r])
    return board, placed, info, failures


def finish(board, placed):
    for ref, fp in placed.items():
        fp.Reference().SetTextSize(VECTOR2I(mm(0.8), mm(0.8)))
        fp.Reference().SetTextThickness(mm(0.12))
        fp.Value().SetVisible(False)
        if ref[0] in "RCLT" and not ref.startswith(("SW",)):
            fp.Reference().SetVisible(False)
    outline(board)
    gnd = get_net(board, "GND")
    all_cu = [pcbnew.F_Cu, pcbnew.In1_Cu, pcbnew.In2_Cu, pcbnew.B_Cu]
    keepout(board, "KO_ANT24_L2_L4_AN043_GND_EDGE", (IFA_BOX[0], IFA_BOX[1] + 0.5, IFA_BOX[2], IFA_BOX[3]), [pcbnew.In1_Cu, pcbnew.In2_Cu, pcbnew.B_Cu])
    keepout(board, "KO_ANT24_F_CU", (IFA_BOX[0], IFA_BOX[1] + 0.5, IFA_BOX[2], IFA_BOX[3]), [pcbnew.F_Cu], tracks=True, vias=True, pour=True)
    keepout(board, "KO_ANT868_ALL_LAYERS_JOHANSON_CORNER", ANT868_KO_A, all_cu)
    keepout(board, "KO_ANT868_ALL_LAYERS_JOHANSON_CORNER_B", ANT868_KO_B, all_cu)
    keepout(board, "KO_NFC_COIL_L2_B", (COIL[0] - 0.5, COIL[1] - 0.5, COIL[2] + 0.5, COIL[3] + 0.5), [pcbnew.In1_Cu, pcbnew.In2_Cu], fps=True)
    keepout(board, "KO_CABLE_NOTCH", CABLE_KO, all_cu, fps=True)
    z = pcbnew.ZONE(board)
    z.SetLayer(pcbnew.In1_Cu)
    z.SetNet(gnd)
    z.SetMinThickness(mm(0.2))
    z.SetZoneName("GND_L2")
    o = z.Outline()
    o.NewOutline()
    for x, y in ((0.0, 0.0), (BW, 0.0), (BW, BH), (6.0, BH), (6.0, NOTCH[1]), (0.0, NOTCH[1])):
        p = pt(x, y)
        o.Append(p.x, p.y)
    board.Add(z)
    add_text(board, "NIGHTHAWK REV B - PRELIMINARY PLACEMENT", 40.0, 28.0, 1.0)


if __name__ == "__main__":
    board, placed, info, failures = build()
    finish(board, placed)
    pcbnew.SaveBoard(PCB, board)
    json.dump(info, open(os.path.join(HERE, "placement_b.json"), "w"), indent=1)
    print("placed", len(placed), "of", len([p for p in d.PARTS if p["fp"]]))
    print("failures", failures)
