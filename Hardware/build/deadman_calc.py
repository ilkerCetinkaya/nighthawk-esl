import itertools
PRESET=(170.0,200.0,230.0)
def eq1(c_nf):
    return 77.4*c_nf+55.0
def cap_case(c_nom_nf,tol):
    lo=eq1(c_nom_nf*(1-tol))*0.905
    typ=eq1(c_nom_nf)
    hi=eq1(c_nom_nf*(1+tol))*1.095
    return lo,typ,hi
TOGGLE=50.0
rows=[("preset CWD=10k to VDD, SET1=1 (datasheet min/typ/max)",PRESET)]
for c,tol in [(1.0,0.05),(2.2,0.05),(3.3,0.05),(4.7,0.05),(10.0,0.05)]:
    rows.append((f"CCWD {c} nF C0G +/-{int(tol*100)} % (Eq.1 +/-9.5 %, ideal capacitor)",cap_case(c,tol)))
print("TPS3431 watchdog timeout candidates (ms)")
for name,(lo,typ,hi) in rows:
    print(f"{name}: min {lo:.1f} typ {typ:.1f} max {hi:.1f} | margin vs 50 ms toggle (min/50) {lo/TOGGLE:.1f}x | worst exposure after supervisor stall <= {hi:.0f} ms")
