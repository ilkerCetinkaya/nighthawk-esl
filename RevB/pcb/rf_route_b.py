import os, sys, pcbnew
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import make_board_b as m

mm = pcbnew.FromMM
PCB = m.PCB
ORG = m.ORIGIN


def P(x, y):
    return pcbnew.VECTOR2I(mm(ORG[0] + x), mm(ORG[1] + m.BH - y))


class Router:
    def __init__(self, board):
        self.b = board
        self.n = 0

    def net(self, name):
        n = self.b.FindNet(name)
        assert n is not None, name
        return n

    def track(self, net, pts, w, layer=pcbnew.F_Cu, lock=True):
        for a, c in zip(pts, pts[1:]):
            if a == c:
                continue
            t = pcbnew.PCB_TRACK(self.b)
            t.SetStart(P(*a))
            t.SetEnd(P(*c))
            t.SetWidth(mm(w))
            t.SetLayer(layer)
            t.SetNet(self.net(net))
            t.SetLocked(lock)
            self.b.Add(t)
            self.n += 1

    def via(self, net, x, y, dia=0.6, drill=0.3, lock=True):
        v = pcbnew.PCB_VIA(self.b)
        v.SetPosition(P(x, y))
        v.SetViaType(pcbnew.VIATYPE_THROUGH)
        v.SetWidth(mm(dia))
        v.SetDrill(mm(drill))
        v.SetNet(self.net(net))
        v.SetLocked(lock)
        self.b.Add(v)
        self.n += 1


def route_24(r):
    W50 = 0.36
    for (u7y, u8y, net) in ((24.25, 23.25, "RF24_P"), (24.75, 23.75, "RF24_N"), (25.25, 24.25, "RFSUB_P"), (25.75, 24.75, "RFSUB_N")):
        r.track(net, [(69.44, u7y), (70.0, u7y), (71.0, u8y), (72.72, u8y)], 0.2)
    r.track("RX_TX", [(69.44, 26.25), (73.5, 26.25), (73.5, 25.2)], 0.3)
    r.track("RX_TX", [(73.5, 26.25), (75.28, 26.25)], 0.3)
    r.track("ANT24_IPC", [(74.29, 23.25), (75.51, 23.25)], 0.25)
    r.track("ANTSUB_IPC", [(74.29, 24.78), (75.53, 24.78)], 0.25)
    r.track("GND", [(74.29, 23.96), (75.0, 23.96)], 0.3)
    r.via("GND", 75.0, 23.96, 0.45, 0.2)
    r.track("GND", [(73.5, 22.5), (74.6, 22.35)], 0.3)
    r.via("GND", 74.6, 22.35, 0.45, 0.2)
    r.track("ANT24_FEED", [(76.53, 23.22), (78.0, 23.22), (78.0, 32.1), (75.1, 35.0), (75.1, 38.0), (62.9, 38.0), (62.9, 43.36), (63.99, 43.36)], W50)
    r.track("ANT24_FEED", [(70.97, 38.0), (70.97, 43.36)], W50)
    r.track("ANT24_FEED", [(63.97, 38.0), (63.97, 40.61)], W50)
    r.track("ANT24_A", [(64.96, 43.36), (67.85, 43.36), (67.85, 44.3)], W50)
    r.track("ANT24_A", [(67.85, 44.08), (71.99, 44.08), (71.99, 43.36)], 0.3)
    r.track("UFL24_C", [(64.99, 40.61), (66.85, 40.5)], W50)
    r.track("GND", [(69.48, 41.97), (69.95, 41.97)], 0.4)
    r.via("GND", 69.95, 41.97)
    r.track("GND", [(69.48, 39.03), (69.95, 39.03)], 0.4)
    r.via("GND", 69.95, 39.03)
    r.track("GND", [(71.93, 40.86), (72.9, 40.86)], 0.4)
    r.via("GND", 72.9, 40.86)
    r.track("GND", [(65.9, 42.4), (65.0, 42.4)], 0.4)
    r.via("GND", 65.0, 42.4)
    r.track("GND", [(76.24, 26.45), (76.24, 27.4)], 0.4)
    r.via("GND", 76.24, 27.4)


def route_868(r):
    W = 0.36
    r.track("ANTSUB_DC", [(76.49, 24.7), (77.2, 24.7)], W)
    r.via("ANTSUB_DC", 77.2, 24.7)
    r.track("ANTSUB_DC", [(77.2, 24.7), (77.2, 22.0)], W, layer=pcbnew.B_Cu)
    r.via("ANTSUB_DC", 77.2, 22.0)
    r.track("ANTSUB_DC", [(77.2, 22.0), (77.2, 18.4), (75.1, 16.3), (75.1, 13.5), (69.2, 13.5), (69.2, 11.31)], W)
    r.track("ANTSUB_FEED", [(69.2, 10.29), (69.2, 6.49)], W)
    r.track("ANTSUB_FEED", [(69.2, 6.5), (68.0, 6.51)], 0.3)
    r.track("ANTSUB_A", [(69.2, 5.51), (69.2, 1.9), (71.1, 1.9)], W)
    r.track("ANTSUB_A", [(68.0, 5.49), (69.2, 5.51)], 0.3)
    r.track("UFLSUB_C", [(68.21, 7.9), (58.85, 7.9), (58.85, 11.3)], W)
    r.track("GND", [(68.24, 9.0), (67.4, 9.0)], 0.4)
    r.via("GND", 67.4, 9.0)
    r.track("GND", [(68.24, 3.6), (67.4, 3.6)], 0.4)
    r.via("GND", 67.4, 3.6)


def main():
    board = pcbnew.LoadBoard(PCB)
    r = Router(board)
    route_24(r)
    route_868(r)
    filler = pcbnew.ZONE_FILLER(board)
    filler.Fill(board.Zones())
    pcbnew.SaveBoard(PCB, board)
    print("items", r.n)


if __name__ == "__main__":
    main()
