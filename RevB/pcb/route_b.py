import math
import os
import subprocess
import sys

import pcbnew
from pcbnew import ToMM

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import make_board_b as m

PCB = m.PCB
WORK = os.path.join(HERE, "work_route")
TOOLS = "/Users/ilkercetinkaya/Desktop/PCB_design_claude/GPace copy/build/tools"
JAVA = os.path.join(TOOLS, "jre25", "jdk-25.0.4.1+1-jre", "Contents", "Home", "bin", "java")
JAR = os.path.join(TOOLS, "freerouting-2.5.0.jar")
DSN = os.path.join(WORK, "NH_REVB.dsn")
SES = os.path.join(WORK, "NH_REVB.ses")
mm = pcbnew.FromMM
ORG = m.ORIGIN

NO_VIA = [
    (0.0, m.NOTCH[1] - 0.6, 6.6, 50.0),
    (m.CABLE_KO[0] - 0.6, 0.0, m.CABLE_KO[2] + 0.6, m.CABLE_KO[3] + 0.6),
    (m.IFA_BOX[0] - 0.4, m.IFA_BOX[1] - 0.4, m.IFA_BOX[2], m.IFA_BOX[3]),
    (m.ANT868_ZONE[0] - 0.4, m.ANT868_ZONE[1], m.ANT868_ZONE[2], m.ANT868_ZONE[3] + 0.4),
    (m.COIL[0] - 0.9, m.COIL[1] - 0.9, m.COIL[2] + 0.9, m.COIL[3] + 0.9),
]


def world(x, y):
    return x - ORG[0], m.BH - (y - ORG[1])


def P(x, y):
    return pcbnew.VECTOR2I(mm(ORG[0] + x), mm(ORG[1] + m.BH - y))


def seg_dist(px, py, ax, ay, bx, by):
    dx, dy = bx - ax, by - ay
    L = dx * dx + dy * dy
    t = 0.0 if L == 0 else max(0.0, min(1.0, ((px - ax) * dx + (py - ay) * dy) / L))
    return math.hypot(px - (ax + t * dx), py - (ay + t * dy))


def add_via(board, net, x, y, dia=0.6, drill=0.3):
    v = pcbnew.PCB_VIA(board)
    v.SetPosition(P(x, y))
    v.SetViaType(pcbnew.VIATYPE_THROUGH)
    v.SetWidth(mm(dia))
    v.SetDrill(mm(drill))
    v.SetNetCode(net)
    board.Add(v)


def add_stub(board, net, a, b, layer, width=0.25):
    t = pcbnew.PCB_TRACK(board)
    t.SetStart(P(*a))
    t.SetEnd(P(*b))
    t.SetWidth(mm(width))
    t.SetLayer(layer)
    t.SetNetCode(net)
    board.Add(t)


def ground_vias(board):
    gnd = board.FindNet("GND").GetNetCode()
    pads = []
    for fp in board.GetFootprints():
        for pad in fp.Pads():
            b = pad.GetBoundingBox()
            wl, wt = world(ToMM(b.GetLeft()), ToMM(b.GetBottom()))
            wr, wb = world(ToMM(b.GetRight()), ToMM(b.GetTop()))
            pads.append((pad.GetNetCode(), wl, wt, wr, wb))
    segs = []
    vias = []
    for t in board.GetTracks():
        if t.GetClass() == "PCB_VIA":
            vx, vy = world(ToMM(t.GetPosition().x), ToMM(t.GetPosition().y))
            vias.append((vx, vy, t.GetNetCode()))
        else:
            ax, ay = world(ToMM(t.GetStart().x), ToMM(t.GetStart().y))
            bx, by = world(ToMM(t.GetEnd().x), ToMM(t.GetEnd().y))
            segs.append((ax, ay, bx, by, ToMM(t.GetWidth()) / 2.0, t.GetNetCode()))
    new = []

    def free(vx, vy, px, py):
        if any(r[0] <= vx <= r[2] and r[1] <= vy <= r[3] for r in NO_VIA):
            return False
        if not (1.0 < vx < m.BW - 1.0 and 1.0 < vy < m.BH - 1.0):
            return False
        for k in range(0, 7):
            sx, sy = px + (vx - px) * k / 6.0, py + (vy - py) * k / 6.0
            for code, l, t, r, b in pads:
                if code != gnd and l - 0.43 <= sx <= r + 0.43 and t - 0.43 <= sy <= b + 0.43:
                    return False
        for ax, ay, bx, by, hw, code in segs:
            if code != gnd and seg_dist(vx, vy, ax, ay, bx, by) < hw + 0.225 + 0.2:
                return False
        for qx, qy, code in vias + new:
            if math.hypot(vx - qx, vy - qy) < 0.8:
                return False
        return True

    count = 0
    skipped = []
    for fp in board.GetFootprints():
        ref = fp.GetReference()
        if ref.startswith("H") or fp.GetLayer() not in (pcbnew.F_Cu, pcbnew.B_Cu):
            pass
        c = fp.GetPosition()
        cx, cy = world(ToMM(c.x), ToMM(c.y))
        for pad in fp.Pads():
            if pad.GetNetCode() != gnd:
                continue
            if pad.GetAttribute() != pcbnew.PAD_ATTRIB_SMD:
                continue
            layer = pcbnew.F_Cu if pad.IsOnLayer(pcbnew.F_Cu) else pcbnew.B_Cu
            px, py = world(ToMM(pad.GetPosition().x), ToMM(pad.GetPosition().y))
            sx, sy = ToMM(pad.GetSize().x), ToMM(pad.GetSize().y)
            if ref == "U7" and max(sx, sy) > 4.0:
                for gx in (-1.6, 0.0, 1.6):
                    for gy in (-1.6, 0.0, 1.6):
                        add_via(board, gnd, px + gx, py + gy, 0.5, 0.3)
                        new.append((px + gx, py + gy, gnd))
                        count += 1
                continue
            if ref == "SH1":
                n = max(1, int(max(sx, sy) // 2.4))
                for i in range(n):
                    off = (i - (n - 1) / 2.0) * 2.0
                    vx, vy = (px + off, py) if sx > sy else (px, py + off)
                    if not any(math.hypot(vx - qx, vy - qy) < 0.95 for qx, qy, _ in vias + new):
                        add_via(board, gnd, vx, vy, 0.5, 0.3)
                        new.append((vx, vy, gnd))
                        count += 1
                continue
            if max(sx, sy) > 2.0:
                continue
            if any(math.hypot(px - qx, py - qy) < 1.3 for qx, qy, code in vias if code == gnd):
                continue
            dx, dy = px - cx, py - cy
            n = math.hypot(dx, dy) or 1.0
            ux, uy = dx / n, dy / n
            options = [(ux, uy), (-uy, ux), (uy, -ux), (0, 1), (0, -1), (1, 0), (-1, 0), (-ux, -uy)]
            done = False
            for ox, oy in options:
                for dist in (0.75, 0.95, 1.2, 1.5, 1.9, 2.4):
                    vx, vy = px + ox * dist, py + oy * dist
                    if free(vx, vy, px, py):
                        add_stub(board, gnd, (px, py), (vx, vy), layer, 0.2)
                        add_via(board, gnd, vx, vy, 0.45, 0.2)
                        new.append((vx, vy, gnd))
                        count += 1
                        done = True
                        break
                if done:
                    break
            if not done:
                skipped.append((ref, pad.GetNumber()))
    return count, skipped


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


def prep():
    board = pcbnew.LoadBoard(PCB)
    n, skipped = ground_vias(board)
    print("ground vias", n, "skipped", skipped)
    pcbnew.ZONE_FILLER(board).Fill(board.Zones())
    pcbnew.SaveBoard(PCB, board)


def jar(passes):
    board = pcbnew.LoadBoard(PCB)
    pcbnew.ExportSpecctraDSN(board, DSN)
    text = open(DSN).read()
    text = strip_blocks(text, ("(place_keepout",))
    text = text.replace('(layer In1.Cu\n      (type signal)', '(layer In1.Cu\n      (type power)')
    assert '(type power)' in text
    open(DSN, "w").write(text)
    if os.path.exists(SES):
        os.remove(SES)
    cmd = [JAVA, "-jar", JAR, "-de", "NH_REVB.dsn", "-do", "NH_REVB.ses", "-mp", str(passes), "--router.optimizer.enabled=false", "-l", "en"]
    with open(os.path.join(WORK, "fr_jar.log"), "w") as log:
        subprocess.run(cmd, cwd=WORK, stdin=subprocess.DEVNULL, stdout=log, stderr=subprocess.STDOUT, timeout=3000)
    print("ses exists", os.path.exists(SES), flush=True)


def finish():
    board = pcbnew.LoadBoard(PCB)
    pcbnew.ImportSpecctraSES(board, SES)
    z = pcbnew.ZONE(board)
    z.SetLayer(pcbnew.In2_Cu)
    z.SetNet(board.FindNet("3V3"))
    z.SetMinThickness(mm(0.2))
    z.SetLocalClearance(mm(0.2))
    z.SetPadConnection(pcbnew.ZONE_CONNECTION_THERMAL)
    z.SetIslandRemovalMode(pcbnew.ISLAND_REMOVAL_MODE_ALWAYS)
    z.SetZoneName("3V3_POUR_L3")
    o = z.Outline()
    o.NewOutline()
    for x, y in ((0.0, 0.0), (m.BW, 0.0), (m.BW, m.BH), (6.0, m.BH), (6.0, m.NOTCH[1]), (0.0, m.NOTCH[1])):
        p = P(x, y)
        o.Append(p.x, p.y)
    board.Add(z)
    pcbnew.ZONE_FILLER(board).Fill(board.Zones())
    pcbnew.SaveBoard(PCB, board)
    print("finished")


if __name__ == "__main__":
    stage = sys.argv[1]
    if stage == "prep":
        prep()
    elif stage == "jar":
        jar(int(sys.argv[2]) if len(sys.argv) > 2 else 20)
    elif stage == "finish":
        finish()
