import math


def K(k):
    a, b = 1.0, math.sqrt(1 - k * k)
    for _ in range(40):
        a, b = (a + b) / 2, math.sqrt(a * b)
    return math.pi / (2 * a)


def kp(k):
    return math.sqrt(1 - k * k)


def microstrip(w, h, er, t=0.0):
    u = w / h
    a = 1 + math.log((u ** 4 + (u / 52) ** 2) / (u ** 4 + 0.432)) / 49 + math.log(1 + (u / 18.1) ** 3) / 18.7
    b = 0.564 * ((er - 0.9) / (er + 3)) ** 0.053
    ee = (er + 1) / 2 + (er - 1) / 2 * (1 + 10 / u) ** (-a * b)
    f = 6 + (2 * math.pi - 6) * math.exp(-(30.666 / u) ** 0.7528)
    z = 60 / math.sqrt(ee) * math.log(f / u + math.sqrt(1 + (2 / u) ** 2))
    return z, ee


def cpwg(w, g, h, er):
    k = w / (w + 2 * g)
    k1 = math.tanh(math.pi * w / (4 * h)) / math.tanh(math.pi * (w + 2 * g) / (4 * h))
    r = K(kp(k)) / K(k)
    r1 = K(k1) / K(kp(k1))
    ee = (1 + er * (K(kp(k)) * K(k1)) / (K(k) * K(kp(k1)))) / (1 + (K(kp(k)) * K(k1)) / (K(k) * K(kp(k1))))
    z = 60 * math.pi / math.sqrt(ee) / (K(k) / K(kp(k)) + K(k1) / K(kp(k1)))
    return z, ee


def solve(fn, target=50.0, lo=0.05, hi=1.5):
    for _ in range(60):
        mid = (lo + hi) / 2
        if fn(mid) > target:
            lo = mid
        else:
            hi = mid
    return (lo + hi) / 2


H, ER = 0.2104, 4.4
print("JLCPCB JLC04161H-7628 (jlcpcb.com/impedance): top Cu 0.035 mm, 7628 prepreg 0.2104 mm (eps_r 4.4), L2 Cu 0.0152, core 1.065 (4.6), L3 Cu 0.0152, prepreg 0.2104, bottom Cu 0.035; mask 1.2 mil on substrate, 0.6 mil on trace, 1.2 mil between traces, eps_r 3.8")
print("JLCPCB calculator, microstrip L1 over L2, 50 ohm: 14.12 mil = 0.3586 mm")
z, ee = microstrip(0.3586, H, ER)
print(f"closed-form check (Hammerstad-Jensen, zero thickness, no mask): 0.3586 mm -> {z:.1f} ohm, eps_eff {ee:.2f}; width for 50 ohm = {solve(lambda w: microstrip(w, H, ER)[0]):.3f} mm")
print("conformal-mapping CPWG with ground on L2, zero conductor thickness, no mask [CALC, not JLCPCB data]: width for 50 ohm")
for g in (0.15, 0.20, 0.25, 0.30, 0.40, 0.60):
    w = solve(lambda x: cpwg(x, g, H, ER)[0], lo=0.05, hi=1.2)
    z, ee = cpwg(w, g, H, ER)
    print(f"   gap {g:.2f} mm: width {w:.3f} mm ({w / 0.0254:.1f} mil), Z {z:.1f} ohm, eps_eff {ee:.2f}")
print("The JLCPCB coplanar calculator result was NOT obtained (the web form returned no width in the automated run); order controlled impedance with the JLCPCB-calculated width.")
