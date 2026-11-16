import cmath
import math

MU0 = 4e-7 * math.pi
F0 = 13.56e6
W0 = 2 * math.pi * F0
RHO = 1.72e-8
T_CU = 35e-6


def l_rect(n, w, h, a):
    d = math.hypot(h, w)
    s = -2 * (w + h) + 2 * d - h * math.log((h + d) / w) - w * math.log((w + d) / h) + h * math.log(2 * h / a) + w * math.log(2 * w / a)
    return n * n * MU0 / math.pi * s


def spiral(outer_w, outer_h, n, a, gap):
    pitch = a + gap
    turns = []
    length = 0.0
    for i in range(n):
        w = outer_w - a - 2 * i * pitch
        h = outer_h - a - 2 * i * pitch
        if w <= 0 or h <= 0:
            return None
        turns.append((w, h))
        length += 2 * (w + h)
    return turns, length


def coil(outer_w, outer_h, n, a, gap, layers=1):
    sp = spiral(outer_w * 1e-3, outer_h * 1e-3, n, a * 1e-3, gap * 1e-3)
    if not sp:
        return None
    turns, length = sp
    wavg = sum(t[0] for t in turns) / n
    havg = sum(t[1] for t in turns) / n
    ltot = l_rect(n * layers, wavg, havg, a * 1e-3)
    skin = math.sqrt(RHO / (math.pi * F0 * MU0))
    rac_factor = max(1.0, T_CU / (2 * skin) if skin < T_CU else 1.0)
    rdc = RHO * length * layers / (a * 1e-3 * T_CU)
    r13 = rdc * 1.3
    return dict(n=n, layers=layers, L=ltot, length=length * layers, rdc=rdc, r=r13, q=W0 * ltot / r13, wavg=wavg, havg=havg, inner_w=turns[-1][0] * 1e3, inner_h=turns[-1][1] * 1e3)


def match(L, rs, q_target, rp=None):
    xl = W0 * L
    if rp is None:
        rp = xl * q_target
    c_res = 1 / (W0 * W0 * L)

    def zp(cp):
        return 1 / (1 / complex(rs, xl) + 1j * W0 * cp + 1 / rp)

    lo, hi = 0.0, c_res
    if zp(hi).real < 50:
        return rp, float("nan"), float("nan"), zp(hi)
    for _ in range(80):
        mid = (lo + hi) / 2
        if zp(mid).real < 50:
            lo = mid
        else:
            hi = mid
    cp = (lo + hi) / 2
    z = zp(cp)
    cs = 1 / (W0 * z.imag) if z.imag > 0 else float("nan")
    return rp, cp, cs, z


def s11_bw(L, rs, rp, cp, cs, rl_db=-10.0):
    pts = []
    for k in range(-400, 401):
        f = F0 * (1 + k / 400 * 0.3)
        w = 2 * math.pi * f
        yp = 1 / complex(rs, w * L) + 1j * w * cp + 1 / rp
        z = 1 / yp + 1 / (1j * w * cs)
        g = abs((z - 50) / (z + 50))
        pts.append((f, 20 * math.log10(g + 1e-12)))
    below = [f for f, g in pts if g < rl_db]
    return (max(below) - min(below)) if below else 0.0


if __name__ == "__main__":
    print("validation against TI SLOA241C example: L 1.35 uH, R 0.754 ohm, X 115 ohm; TI final Cp 47 pF, Rp 700 ohm, Cs 68 pF (simulated start Cp 43, Rp 800, Cs 63)")
    L = 115 / W0
    for rp in (700.0, 800.0):
        rp_, cp, cs, zp = match(L, 0.754, None, rp)
        print(f"  solver Rp {rp:.0f}: Cp {cp * 1e12:.1f} pF, Cs {cs * 1e12:.1f} pF (L from X=115: {L * 1e6:.2f} uH)")
    print()
    print("coil candidates: outer w x h mm, turns, trace/gap mm, layers -> L (SLOA241C eq. 2), series R (DC x1.3), unloaded Q")
    for (w, h) in ((28, 16), (18, 16), (20, 16), (22, 16)):
        for a, gap in ((0.2, 0.1), (0.25, 0.1), (0.3, 0.15)):
            for layers in (1, 2):
                for n in range(2, 9):
                    c = coil(w, h, n, a, gap, layers)
                    if c and 1.0e-6 <= c["L"] <= 1.6e-6:
                        print(f"  {w}x{h} a{a} g{gap} N{n} x{layers}L: L {c['L'] * 1e6:.2f} uH, R {c['r']:.2f} ohm, Q0 {c['q']:.0f}, inner {c['inner_w']:.1f}x{c['inner_h']:.1f} mm")
    print()
    for name, (w, h, n, a, gap, layers) in {"A 18x16, 6 turns, 0.25/0.10 mm, F.Cu only (selected)": (18, 16, 6, 0.25, 0.1, 1), "B 18x16, 3+3 turns F+B, 0.25/0.10": (18, 16, 3, 0.25, 0.1, 2), "C 20x16, 6 turns, 0.3/0.15": (20, 16, 6, 0.3, 0.15, 1), "old 28x16 3 turns (previous estimate)": (28, 16, 3, 0.25, 0.1, 1)}.items():
        c = coil(w, h, n, a, gap, layers)
        print(name, f"L {c['L'] * 1e6:.2f} uH R {c['r']:.2f} Q0 {c['q']:.0f}")
        for q in (7, 9):
            rp, cp, cs, zp = match(c["L"], c["r"], q)
            bw = s11_bw(c["L"], c["r"], rp, cp, cs)
            print(f"   target Q {q}: Rp {rp:.0f} ohm, Cp {cp * 1e12:.1f} pF, Cs {cs * 1e12:.1f} pF, -10 dB RL bandwidth {bw / 1e6:.2f} MHz")
