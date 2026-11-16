import json
import math
import os
import subprocess
import sys

import pcbnew
from pcbnew import ToMM

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import design
import make_board as mb

HW = os.path.dirname(HERE)
PCB = mb.PCB
PRO = os.path.join(HW, "NIGHTHAWK.kicad_pro")
WORK = os.path.join(HERE, "work")
DSN = os.path.join(WORK, "NIGHTHAWK.dsn")
SES = os.path.join(WORK, "NIGHTHAWK.ses")
JAVA = os.path.join(HERE, "tools", "jre25", "jdk-25.0.4.1+1-jre", "Contents", "Home", "bin", "java")
JAR = os.path.join(HERE, "tools", "freerouting-2.5.0.jar")
POWER_NETS = ["3V3", "3V3_RF", "3V3_A", "VBUS", "VBUS_F", "RF1_VCC", "RF2_VCC", "RF1_VCC_F", "RF2_VCC_F"]
os.makedirs(WORK, exist_ok=True)


def write_project():
    base = {"bus_width": 12, "clearance": 0.15, "diff_pair_gap": 0.25, "diff_pair_via_gap": 0.25, "diff_pair_width": 0.2,
            "line_style": 0, "microvia_diameter": 0.3, "microvia_drill": 0.1, "pcb_color": "rgba(0, 0, 0, 0.000)",
            "priority": 2147483647, "schematic_color": "rgba(0, 0, 0, 0.000)", "track_width": 0.2, "via_diameter": 0.6,
            "via_drill": 0.3, "wire_width": 6}
    classes = [dict(base, name="Default"),
               dict(base, name="POWER", clearance=0.2, track_width=0.4, priority=1),
               dict(base, name="RF", clearance=0.2, track_width=design.RF_WIDTH, priority=0)]
    patterns = [{"netclass": "POWER", "pattern": n} for n in POWER_NETS] + [{"netclass": "RF", "pattern": n} for n in mb.RF_NETS]
    pro = {
        "meta": {"filename": "NIGHTHAWK.kicad_pro", "version": 3},
        "net_settings": {"classes": classes, "meta": {"version": 4}, "net_colors": None, "netclass_assignments": None, "netclass_patterns": patterns},
        "board": {"design_settings": {"rules": {
            "min_clearance": 0.127, "min_track_width": 0.1, "min_via_diameter": 0.5, "min_through_hole_diameter": 0.2,
            "min_copper_edge_clearance": 0.3, "min_hole_clearance": 0.2, "min_hole_to_hole": 0.25,
            "min_text_height": 0.5, "min_text_thickness": 0.05, "min_silk_clearance": 0.0}}},
        "sheets": [],
        "text_variables": {},
    }
    with open(PRO, "w") as handle:
        json.dump(pro, handle, indent=2)


def pad_world(board, ref, number):
    fp = board.FindFootprintByReference(ref)
    out = []
    for pad in fp.Pads():
        if pad.GetNumber() == number:
            out.append(mb.from_pt(pad.GetPosition()))
    return out[0]


def ref_of(net, kind, index=0):
    found = []
    for p in design.PARTS:
        if net in p["nets"].values() and p["ref"].startswith(kind):
            found.append(p)
    return found


def manhattan(board, net_name, a, b, width=design.RF_WIDTH, layer=pcbnew.F_Cu, horizontal_first=True):
    net = board.FindNet(net_name)
    if abs(a[0] - b[0]) < 1e-3 or abs(a[1] - b[1]) < 1e-3:
        pts = [a, b]
    else:
        mid = (b[0], a[1]) if horizontal_first else (a[0], b[1])
        pts = [a, mid, b]
    for p, q in zip(pts, pts[1:]):
        t = pcbnew.PCB_TRACK(board)
        t.SetStart(mb.pt(*p))
        t.SetEnd(mb.pt(*q))
        t.SetWidth(mb.mm(width))
        t.SetLayer(layer)
        board.Add(t)
        t.SetNetCode(net.GetNetCode())


def find_pad_for(board, net_name, ref_prefix, side):
    refs = [p for p in design.PARTS if p["ref"].startswith(ref_prefix) and net_name in p["nets"].values()]
    return refs


def rf_routes(board):
    c_dc = next(p["ref"] for p in design.PARTS if p["value"] == "100p")
    rs = next(p["ref"] for p in design.PARTS if p["nets"] == {"1": "RF_A", "2": "RF_B"} and not p["dnp"])
    rt = next(p["ref"] for p in design.PARTS if p["nets"] == {"1": "RF_B", "2": "RF_TEST"})
    manhattan(board, "RF_IN", pad_world(board, "J2", "1"), pad_world(board, c_dc, "1"))
    manhattan(board, "RF_A", pad_world(board, c_dc, "2"), pad_world(board, rs, "1"))
    manhattan(board, "RF_B", pad_world(board, rs, "2"), pad_world(board, rt, "1"), horizontal_first=True)
    manhattan(board, "RF_TEST", pad_world(board, rt, "2"), pad_world(board, "J3", "1"), horizontal_first=False)


def add_via(board, net_name, x, y, dia=0.6, drill=0.3):
    net = board.FindNet(net_name)
    v = pcbnew.PCB_VIA(board)
    v.SetPosition(mb.pt(x, y))
    v.SetViaType(pcbnew.VIATYPE_THROUGH)
    v.SetWidth(mb.mm(dia))
    v.SetDrill(mb.mm(drill))
    board.Add(v)
    v.SetNetCode(net.GetNetCode())


def add_stub(board, net_name, a, b, width=0.2):
    net = board.FindNet(net_name)
    t = pcbnew.PCB_TRACK(board)
    t.SetStart(mb.pt(*a))
    t.SetEnd(mb.pt(*b))
    t.SetWidth(mb.mm(width))
    t.SetLayer(pcbnew.F_Cu)
    board.Add(t)
    t.SetNetCode(net.GetNetCode())


def ground_vias(board):
    gnd = board.FindNet("GND").GetNetCode()
    pads = []
    for fp in board.GetFootprints():
        for pad in fp.Pads():
            b = pad.GetBoundingBox()
            pads.append((pad.GetNetCode(), ToMM(b.GetLeft()), ToMM(b.GetTop()), ToMM(b.GetRight()), ToMM(b.GetBottom())))
    placed = []
    count = 0
    for fp in board.GetFootprints():
        ref = fp.GetReference()
        if ref.startswith(("H", "J1", "J2", "J3", "J7")):
            continue
        c = fp.GetPosition()
        cx, cy = ToMM(c.x), ToMM(c.y)
        for pad in fp.Pads():
            if pad.GetNetCode() != gnd or not pad.IsOnLayer(pcbnew.F_Cu) or pad.GetAttribute() != pcbnew.PAD_ATTRIB_SMD:
                continue
            size = max(ToMM(pad.GetSize().x), ToMM(pad.GetSize().y))
            if ref == "U1" and size > 2.0:
                continue
            px, py = ToMM(pad.GetPosition().x), ToMM(pad.GetPosition().y)
            dx, dy = px - cx, py - cy
            n = math.hypot(dx, dy) or 1.0
            ux, uy = dx / n, dy / n
            options = [(ux, uy), (-uy, ux), (uy, -ux), (0, 1), (0, -1), (1, 0), (-1, 0)]
            done = False
            for ox, oy in options:
                for dist in (0.85, 1.2, 1.6):
                    vx, vy = px + ox * dist, py + oy * dist
                    samples = [(px + (vx - px) * k / 6.0, py + (vy - py) * k / 6.0) for k in range(1, 7)]
                    ok = all(code == gnd or not any(l - 0.45 <= sx <= r + 0.45 and t - 0.45 <= sy <= bt + 0.45 for sx, sy in samples) for code, l, t, r, bt in pads)
                    ok = ok and all(math.hypot(vx - qx, vy - qy) > 0.9 for qx, qy in placed)
                    ox_b, oy_b = mb.ORIGIN
                    wx, wy = vx - ox_b, design.BOARD_H - (vy - oy_b)
                    ok = ok and 1.0 < wx < design.BOARD_W - 1.0 and 1.0 < wy < design.BOARD_H - 1.0
                    if ok:
                        a = (px - ox_b, design.BOARD_H - (py - oy_b))
                        add_stub(board, "GND", a, (wx, wy))
                        add_via(board, "GND", wx, wy, 0.5, 0.3)
                        placed.append((vx, vy))
                        count += 1
                        done = True
                        break
                if done:
                    break
    return count


def lock_tracks(board):
    for t in board.GetTracks():
        t.SetLocked(True)


def strip_blocks(text, keys):
    out = []
    i = 0
    n = len(text)
    while i < n:
        if any(text.startswith(k, i) for k in keys):
            depth = 0
            while i < n:
                if text[i] == "(":
                    depth += 1
                elif text[i] == ")":
                    depth -= 1
                    if depth == 0:
                        i += 1
                        break
                i += 1
            continue
        out.append(text[i])
        i += 1
    return "".join(out)


def export_dsn(board, drop=("(place_keepout",)):
    pcbnew.ExportSpecctraDSN(board, DSN)
    with open(DSN) as handle:
        text = handle.read()
    with open(DSN, "w") as handle:
        handle.write(strip_blocks(text, drop))


def run_jar(passes):
    if os.path.exists(SES):
        os.remove(SES)
    cmd = [JAVA, "-jar", JAR, "-de", "NIGHTHAWK.dsn", "-do", "NIGHTHAWK.ses", "-mp", str(passes), "--router.optimizer.enabled=false", "-l", "en"]
    with open(os.path.join(WORK, "fr_jar.log"), "w") as log:
        subprocess.run(cmd, cwd=WORK, stdin=subprocess.DEVNULL, stdout=log, stderr=subprocess.STDOUT, timeout=1500)


def prep():
    write_project()
    board, placed = mb.build()
    rf_routes(board)
    n = ground_vias(board)
    lock_tracks(board)
    pcbnew.ZONE_FILLER(board).Fill(board.Zones())
    pcbnew.SaveBoard(PCB, board)
    print("ground vias", n)


def jar(passes):
    board = pcbnew.LoadBoard(PCB)
    export_dsn(board)
    run_jar(passes)
    print("ses exists", os.path.exists(SES), flush=True)
    if os.path.exists(SES):
        pcbnew.ImportSpecctraSES(board, SES)
        mb.add_in2_pour(board)
        pcbnew.ZONE_FILLER(board).Fill(board.Zones())
        pcbnew.SaveBoard(PCB, board)


if __name__ == "__main__":
    stage = sys.argv[1]
    if stage == "prep":
        prep()
    elif stage == "jar":
        jar(int(sys.argv[2]) if len(sys.argv) > 2 else 20)


def seg_dist(px, py, ax, ay, bx, by):
    dx, dy = bx - ax, by - ay
    L = dx * dx + dy * dy
    t = 0.0 if L == 0 else max(0.0, min(1.0, ((px - ax) * dx + (py - ay) * dy) / L))
    return math.hypot(px - (ax + t * dx), py - (ay + t * dy))


def rect_dist(px, py, l, t, r, b):
    dx = max(l - px, 0, px - r)
    dy = max(t - py, 0, py - b)
    return math.hypot(dx, dy)


def stitch(board, pitch=5.0, radius=0.3):
    gnd = board.FindNet("GND").GetNetCode()
    segs, vias, pads = [], [], []
    for t in board.GetTracks():
        if t.GetNetCode() == gnd:
            continue
        a, b = t.GetStart(), t.GetEnd()
        if isinstance(t, pcbnew.PCB_VIA):
            vias.append((ToMM(a.x), ToMM(a.y), ToMM(t.GetWidth()) / 2))
        else:
            segs.append((ToMM(a.x), ToMM(a.y), ToMM(b.x), ToMM(b.y), ToMM(t.GetWidth()) / 2))
    allvias = [(ToMM(t.GetStart().x), ToMM(t.GetStart().y)) for t in board.GetTracks() if isinstance(t, pcbnew.PCB_VIA)]
    for fp in board.GetFootprints():
        for pad in fp.Pads():
            if pad.GetNetCode() == gnd and pad.GetAttribute() == pcbnew.PAD_ATTRIB_SMD:
                continue
            b = pad.GetBoundingBox()
            pads.append((ToMM(b.GetLeft()), ToMM(b.GetTop()), ToMM(b.GetRight()), ToMM(b.GetBottom())))
    ox, oy = mb.ORIGIN
    added = 0
    y = 4.0
    while y < design.BOARD_H - 3.0:
        x = 4.0
        while x < design.BOARD_W - 3.0:
            wx, wy = ox + x, oy + design.BOARD_H - y
            in_ant = 24.5 < x < 55.5 and y > 66.0
            ok = not in_ant
            if ok:
                ok = all(rect_dist(wx, wy, *r) > radius + 0.25 for r in pads)
            if ok:
                ok = all(seg_dist(wx, wy, *s[:4]) > radius + s[4] + 0.2 for s in segs)
            if ok:
                ok = all(math.hypot(wx - v[0], wy - v[1]) > radius + v[2] + 0.2 for v in vias)
            if ok:
                ok = all(math.hypot(wx - qx, wy - qy) > 0.9 for qx, qy in allvias)
            if ok:
                add_via(board, "GND", x, y, 0.6, 0.3)
                allvias.append((wx, wy))
                added += 1
            x += pitch
        y += pitch
    return added


def post():
    board = pcbnew.LoadBoard(PCB)
    gnd = board.FindNet("GND")
    for ref, number in (("J4", "3"), ("J5", "3"), ("J7", "6"), ("J1", "A1"), ("J1", "A12"), ("J1", "B1"), ("J1", "B12")):
        fp = board.FindFootprintByReference(ref)
        for pad in fp.Pads():
            if pad.GetNumber() == number:
                pad.SetLocalZoneConnection(pcbnew.ZONE_CONNECTION_FULL)
    sh = [mb.from_pt(p.GetPosition()) for p in board.FindFootprintByReference("J1").Pads() if p.GetNumber() == "SH" and p.GetAttribute() == pcbnew.PAD_ATTRIB_PTH]
    sh.sort()
    a1, a12 = pad_world(board, "J1", "A1"), pad_world(board, "J1", "A12")
    add_stub(board, "GND", a1, min(sh, key=lambda s: math.hypot(s[0] - a1[0], s[1] - a1[1])), 0.2)
    add_stub(board, "GND", a12, min(sh, key=lambda s: math.hypot(s[0] - a12[0], s[1] - a12[1])), 0.2)
    n = stitch(board)
    pcbnew.ZONE_FILLER(board).Fill(board.Zones())
    pcbnew.SaveBoard(PCB, board)
    print("stitch vias", n)


if stage_post := (len(sys.argv) > 1 and sys.argv[1] == "post"):
    post()


def silk_fix():
    board = pcbnew.LoadBoard(PCB)
    rects = []
    for fp in board.GetFootprints():
        bb = fp.GetBoundingBox(False, False)
        rects.append((fp.GetReference(), ToMM(bb.GetLeft()), ToMM(bb.GetTop()), ToMM(bb.GetRight()), ToMM(bb.GetBottom())))
        ref = fp.GetReference()
        if ref.startswith(("U5", "U6", "U7", "U8", "U9", "U10", "U11", "U12", "D2", "D3", "D4", "D5")) and ref not in ("U1", "U2", "U3", "U4"):
            fp.Reference().SetVisible(False)
    ox, oy = mb.ORIGIN
    texts = [d for d in board.GetDrawings() if isinstance(d, pcbnew.PCB_TEXT) and d.GetLayer() == pcbnew.F_SilkS]
    brand = {"NIGHTHAWK", "ESL SECURITY RESEARCH", "REV A"}
    placed = []
    for t in texts:
        if t.GetText() in brand:
            bb = t.GetBoundingBox()
            placed.append((ToMM(bb.GetLeft()), ToMM(bb.GetTop()), ToMM(bb.GetRight()), ToMM(bb.GetBottom())))
    for t in texts:
        if t.GetText() in brand:
            continue
        bb = t.GetBoundingBox()
        w, h = ToMM(bb.GetWidth()), ToMM(bb.GetHeight())
        cx, cy = ToMM(t.GetPosition().x), ToMM(t.GetPosition().y)
        best = None
        for radius in [i * 0.5 for i in range(0, 60)]:
            for k in range(0, 360, 20):
                px, py = cx + radius * math.cos(math.radians(k)), cy + radius * math.sin(math.radians(k))
                r = (px - w / 2 - 0.3, py - h / 2 - 0.3, px + w / 2 + 0.3, py + h / 2 + 0.3)
                bx, by = px - ox, design.BOARD_H - (py - oy)
                if not (2.0 < bx - w / 2 and bx + w / 2 < design.BOARD_W - 2.0 and 1.5 < by - h / 2 and by + h / 2 < design.BOARD_H - 1.5):
                    continue
                if 24.0 < bx < 56.0 and by > 66.0:
                    continue
                if any(not (r[2] < f[1] or f[3] < r[0] or r[3] < f[2] or f[4] < r[1]) for f in rects if not f[0].startswith("H") or True):
                    continue
                if any(not (r[2] < q[0] or q[2] < r[0] or r[3] < q[1] or q[3] < r[1]) for q in placed):
                    continue
                best = (px, py)
                break
            if best:
                break
        if best:
            t.SetPosition(pcbnew.VECTOR2I(mb.mm(best[0]), mb.mm(best[1])))
            placed.append((best[0] - w / 2, best[1] - h / 2, best[0] + w / 2, best[1] + h / 2))
        else:
            print("no spot for", t.GetText())
    pcbnew.SaveBoard(PCB, board)


if len(sys.argv) > 1 and sys.argv[1] == "silk":
    silk_fix()
