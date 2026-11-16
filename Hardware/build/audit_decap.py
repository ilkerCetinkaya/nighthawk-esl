import pcbnew,math
b=pcbnew.LoadBoard("../NIGHTHAWK.kicad_pcb")
caps=[f for f in b.GetFootprints() if f.GetReference().startswith("C")]
def pos(p):
    q=p.GetPosition();return (pcbnew.ToMM(q.x),pcbnew.ToMM(q.y))
chk=[("U1","1"),("U2","24"),("U7","5"),("U8","5"),("U9","5"),("U10","5"),("U11","5"),("U12","5"),("U3","1"),("U4","1"),("U5","1"),("U6","1"),("J7","4")]
for ref,pad in chk:
    fp=b.FindFootprintByReference(ref); p=[x for x in fp.Pads() if x.GetNumber()==pad][0]
    net=p.GetNetname(); pp=pos(p)
    best=None
    for c in caps:
        for cp in c.Pads():
            if cp.GetNetname()==net:
                d=math.dist(pp,pos(cp))
                if best is None or d<best[0]: best=(d,c.GetReference(),c.GetValue())
    print(f"{ref} pad{pad} {net}: nearest cap {best[1]} {best[2]} at {best[0]:.1f} mm")
