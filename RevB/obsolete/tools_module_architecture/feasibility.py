import random, math, json, sys, itertools

BW, BH = 80.0, 40.0
NOTCH = (0.0, 7.0, 6.0, 40.0)
ANT = (0.0, 22.0, 6.0, 40.0)
GAP = 0.5
ANT_CLEAR = 15.0

def rect(x, y, w, h):
    return (x, y, x + w, y + h)

def overlap(a, b, m=0.0):
    return not (a[2] + m <= b[0] or b[2] + m <= a[0] or a[3] + m <= b[1] or b[3] + m <= a[1])

def dist(a, b):
    dx = max(a[0] - b[2], b[0] - a[2], 0.0)
    dy = max(a[1] - b[3], b[1] - a[3], 0.0)
    return math.hypot(dx, dy)

BLOCKS = {
    "ESP32": dict(w=14, h=18, sides="T", fixed=(6, 22)),
    "USB": dict(w=7.3, h=9.4, sides="T", fixed=(72.7, 0), both=True),
    "USB_ESD": dict(w=7, h=6, sides="T", near="USB", maxd=6),
    "BATT": dict(w=50.5, h=20.5, sides="B"),
    "COIL": dict(w=28, h=12, sides="T", rot=True),
    "NFC_IC": dict(w=14, h=10, sides="T", near="COIL", maxd=6),
    "CHG": dict(w=8.5, h=7.5, sides="TB", rot=True),
    "REG": dict(w=12, h=12, sides="TB"),
    "DIG1": dict(w=22, h=14, sides="TB", rot=True),
    "DIG2": dict(w=22, h=14, sides="TB", rot=True),
    "SD": dict(w=15.7, h=17.7, sides="T", rot=True, edge=True),
    "STOR": dict(w=12, h=10, sides="TB", rot=True),
    "JST_M1": dict(w=18.8, h=6.6, sides="T", rot=True, edge=True),
    "JST_M2": dict(w=18.8, h=6.6, sides="T", rot=True, edge=True),
    "SMA_IN": dict(w=8, h=12.1, sides="T", edge=True, both=True),
    "SMA_TEST": dict(w=8, h=12.1, sides="T", edge=True, both=True),
    "BATT_CONN": dict(w=5.8, h=6.6, sides="B", near="BATT", maxd=3),
    "UI": dict(w=20, h=8, sides="TB"),
}

RELAX = set(sys.argv[1:])
import os
for _d in filter(None, os.environ.get("DROP", "").split(",")):
    BLOCKS.pop(_d, None)
_coil = os.environ.get("COIL")
if _coil:
    _w, _h = map(float, _coil.split("x"))
    BLOCKS["COIL"].update(w=_w, h=_h)

def board_ok(r):
    if r[0] < -1e-6 or r[1] < -1e-6 or r[2] > BW + 1e-6 or r[3] > BH + 1e-6:
        return False
    if overlap(r, NOTCH):
        return False
    return True

def violations(sol, detail=False):
    v = []
    rects = {}
    for k, s in sol.items():
        rects[k] = rect(s["x"], s["y"], s["w"], s["h"])
    for k, r in rects.items():
        if not board_ok(r):
            v.append(f"{k}: outside board/notch")
    for (a, b) in itertools.combinations(rects, 2):
        same = sol[a]["side"] == sol[b]["side"] or BLOCKS[a].get("both") or BLOCKS[b].get("both")
        if same and overlap(rects[a], rects[b], GAP):
            v.append(f"{a}/{b}: overlap")
    esp = rects["ESP32"]
    for k, r in rects.items():
        if k != "ESP32" and sol[k]["side"] == "B" and overlap(r, esp, 0.0):
            v.append(f"{k}: bottom-side part under ESP32 module")
    for k in [k for k in ("SD", "JST_M1", "JST_M2") if k in rects]:
        r = rects[k]
        if min(r[0], r[1], BW - r[2], BH - r[3]) > 1.5:
            v.append(f"{k}: not flush with a board edge (cable/card access)")

    for k in ("BATT",):
        if "ant15" not in RELAX and dist(rects[k], ANT) < ANT_CLEAR:
            v.append(f"BATT within {ANT_CLEAR} mm of antenna ({dist(rects[k], ANT):.1f})")
    coil = rects["COIL"]
    for k, r in rects.items():
        if k in ("COIL", "NFC_IC", "ESP32"):
            continue
        if "coilvoid" not in RELAX and overlap(coil, r, 0.5):
            if sol[k]["side"] == "T" or k == "BATT" or True:
                v.append(f"{k} overlaps NFC coil window (no copper allowed under coil; top: no parts)")
    if "coilant" not in RELAX and dist(coil, ANT) < ANT_CLEAR:
        v.append(f"NFC coil within {ANT_CLEAR} mm of antenna ({dist(coil, ANT):.1f})")
    for k in ("BATT",):
        if "coilbatt" not in RELAX and dist(rects[k], coil) < 3.0:
            v.append(f"BATT within 3 mm of coil ({dist(rects[k], coil):.1f})")
    for k in [k for k in ("JST_M1", "JST_M2", "SMA_IN", "SMA_TEST", "SD", "USB") if k in rects]:
        if "coilmetal" not in RELAX and dist(rects[k], coil) < 5.0:
            v.append(f"{k} within 5 mm of coil ({dist(rects[k], coil):.1f})")
    reg = rects["REG"]
    if "pwrnoise" not in RELAX:
        if dist(reg, coil) < 10.0:
            v.append(f"REG (switching) within 10 mm of coil ({dist(reg, coil):.1f})")
        if dist(reg, ANT) < 25.0:
            v.append(f"REG within 25 mm of antenna ({dist(reg, ANT):.1f})")
        for rf in ("SMA_IN", "SMA_TEST"):
            if dist(reg, rects[rf]) < 6.0:
                v.append(f"REG within 6 mm of RF port {rf}")
        for rf in [k for k in ("JST_M1", "JST_M2") if k in rects]:
            if dist(reg, rects[rf]) < 3.0 and sol["REG"]["side"] == sol[rf]["side"]:
                v.append(f"REG within 3 mm of module interface {rf}")
        if dist(reg, rects["NFC_IC"]) < 10.0:
            v.append("REG within 10 mm of NFC_IC")
    if "STOR" in rects:
        if dist(rects["STOR"], rects["REG"]) < 6.0:
            v.append("STOR within 6 mm of switching regulator")
        if sol["STOR"]["side"] == "B" and overlap(rects["STOR"], rects["BATT"], 0.5):
            v.append("STOR under the battery")
    if "pwrbatt" not in RELAX and overlap(rects["CHG"], rects["BATT"], 2.0):
        v.append("CHG (linear charger heat) over/near the battery footprint")
    if dist(rects["CHG"], rects["USB"]) > 12:
        v.append("CHG farther than 12 mm from USB")
    if dist(rects["REG"], rects["CHG"]) > 30:
        v.append("REG farther than 30 mm from CHG")
    for rf in ("SMA_IN", "SMA_TEST"):
        if "rfsep" not in RELAX and dist(rects[rf], rects["USB"]) < 6.0:
            v.append(f"RF port {rf} within 6 mm of USB connector ({dist(rects[rf], rects['USB']):.1f})")
        if "rfsep" not in RELAX and dist(rects[rf], ANT) < 30.0:
            v.append(f"RF port {rf} within 30 mm of 2.4 GHz antenna ({dist(rects[rf], ANT):.1f})")
    for rf in [k for k in ("JST_M1", "JST_M2", "SD") if k in rects]:
        if "rfsep" not in RELAX and dist(rects[rf], ANT) < 15.0:
            v.append(f"{rf} within 15 mm of 2.4 GHz antenna ({dist(rects[rf], ANT):.1f})")
    for k in ("SMA_IN", "SMA_TEST"):
        r = rects[k]
        on_edge = abs(r[1]) < 1e-6 or abs(r[3] - BH) < 1e-6 or abs(r[2] - BW) < 1e-6 or abs(r[0]) < 1e-6
        if not on_edge:
            v.append(f"{k}: not on a board edge")
    for k, b in BLOCKS.items():
        if "near" in b:
            if dist(rects[k], rects[b["near"]]) > b["maxd"]:
                v.append(f"{k} not within {b['maxd']} mm of {b['near']}")
    return v

def random_sol(rng):
    sol = {}
    for k, b in BLOCKS.items():
        if "fixed" in b:
            sol[k] = dict(x=b["fixed"][0], y=b["fixed"][1], w=b["w"], h=b["h"], side=b["sides"][0])
            continue
        w, h = b["w"], b["h"]
        if b.get("rot") and rng.random() < 0.5:
            w, h = h, w
        side = rng.choice(b["sides"])
        sol[k] = dict(x=round(rng.uniform(0, BW - w) * 2) / 2, y=round(rng.uniform(0, BH - h) * 2) / 2, w=w, h=h, side=side)
        if b.get("edge"):
            e = rng.choice("LRTB")
            if e == "L": sol[k].update(x=0)
            if e == "R": sol[k].update(x=BW - w)
            if e == "B": sol[k].update(y=0)
            if e == "T": sol[k].update(y=BH - h)
    return sol

def mutate(sol, rng):
    s = {k: dict(v) for k, v in sol.items()}
    k = rng.choice([k for k in s if "fixed" not in BLOCKS[k]])
    b = BLOCKS[k]
    r = rng.random()
    if r < 0.15 and b.get("rot"):
        s[k]["w"], s[k]["h"] = s[k]["h"], s[k]["w"]
    if r > 0.85 and len(b["sides"]) > 1:
        s[k]["side"] = rng.choice(b["sides"])
    step = rng.choice([0.5, 1, 2, 5, 10])
    s[k]["x"] = min(max(0, s[k]["x"] + rng.choice([-1, 0, 1]) * step), BW - s[k]["w"])
    s[k]["y"] = min(max(0, s[k]["y"] + rng.choice([-1, 0, 1]) * step), BH - s[k]["h"])
    if b.get("edge"):
        e = rng.choice("LRTB")
        if e == "L": s[k]["x"] = 0
        if e == "R": s[k]["x"] = BW - s[k]["w"]
        if e == "B": s[k]["y"] = 0
        if e == "T": s[k]["y"] = BH - s[k]["h"]
    return s

def search(seed, iters=60000):
    rng = random.Random(seed)
    best = random_sol(rng)
    bv = len(violations(best))
    cur, cv = best, bv
    T = 2.0
    for i in range(iters):
        cand = mutate(cur, rng)
        c = len(violations(cand))
        if c <= cv or rng.random() < math.exp((cv - c) / T):
            cur, cv = cand, c
            if c < bv:
                best, bv = cand, c
                if bv == 0:
                    break
        T = max(0.05, T * 0.9999)
    return best, bv

if __name__ == "__main__":
    results = []
    for seed in range(int(__import__("os").environ.get("SEEDS","12"))):
        sol, nv = search(seed)
        results.append((nv, seed, sol))
        if nv == 0:
            break
    results.sort(key=lambda t: t[0])
    nv, seed, sol = results[0]
    print("relaxed:", sorted(RELAX) or "none", "| best violations:", nv, "seed", seed)
    for m in violations(sol):
        print("  -", m)
    tag = os.environ.get("TAG") or ('_'.join(sorted(RELAX)) or 'strict')
    json.dump(sol, open(f"best_{tag}.json", "w"), indent=1)
