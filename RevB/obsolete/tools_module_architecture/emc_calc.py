import math

C = 299792458.0
MU0 = 4e-7 * math.pi

def fspl_db(d_m, f_hz):
    return 20 * math.log10(4 * math.pi * d_m * f_hz / C)

print("1. Free-space path loss between isotropic antennas (Friis); valid only beyond the reactive near field")
for f in (433.92e6, 868e6, 2.44e9):
    lam = C / f
    print(f"  f = {f/1e6:.2f} MHz: lambda = {lam*1000:.0f} mm, reactive near-field boundary lambda/2pi = {lam/(2*math.pi)*1000:.0f} mm")
    print("   ", ", ".join(f"{d} mm: {fspl_db(d/1000, f):.1f} dB" for d in (20, 30, 40, 60, 80)))
ptx = 20.0
print(f"  ESP32-C3 max TX power {ptx} dBm (datasheet 'RF transmit power range -24.0 ~ 20.0 dBm'). Received power at an isotropic 2.44 GHz port 60 mm away, 0 dBi both ends: {ptx - fspl_db(0.060, 2.44e9):.1f} dBm (illustrative; near-field, antenna patterns and board currents not modelled)")

print("\n2. Harmonic coincidences")
def hits(fsw_list, lo, hi, label):
    for fsw in fsw_list:
        ns = [n for n in range(1, 400) if lo <= n * fsw <= hi]
        print(f"  {label}: fsw {fsw/1e6:.2f} MHz -> harmonics in {lo/1e6:.2f}-{hi/1e6:.2f} MHz: " + (", ".join(f"n={n} ({n*fsw/1e6:.2f} MHz)" for n in ns) or "none"))
nfc_lo, nfc_hi = 13.56e6 - 0.848e6, 13.56e6 + 0.848e6
hits([1.4e6, 1.6e6, 2.1e6], nfc_lo, nfc_hi, "TPS63802 typ. fsw (datasheet, no load, forced PWM)")
f_any = [n for n in range(5, 12)]
print("  any fsw between 1.4 and 2.1 MHz has a harmonic n in 7..9 that can fall on 13.56 MHz; e.g. 13.56/7 = 1.937 MHz, 13.56/8 = 1.695 MHz, 13.56/9 = 1.507 MHz")
for n, band in ((32, "433.92 MHz ISM"), (64, "868 MHz SRD"), (177, "2.4 GHz ISM")):
    print(f"  13.56 MHz NFC carrier x {n} = {13.56e6*n/1e6:.2f} MHz ({band})")
for n in (60, 61, 62):
    print(f"  ESP32-C3 40 MHz crystal x {n} = {40*n} MHz (inside 2.400-2.4835 GHz)")
print("  USB full-speed 12 Mbit/s: data spectrum has energy at and below 12 MHz and harmonics of 6 MHz; 12 MHz is 0.7 MHz below the lower NFC subcarrier (12.71 MHz)")

print("\n3. Shield can aperture leakage estimate SE ~ 20 log10(lambda / (2 L)) - 10 log10(N) (single-slot rule of thumb, not a simulation)")
for f in (433.92e6, 868e6, 2.44e9, 5.8e9):
    lam = C / f * 1000
    row = []
    for L, N in ((2, 1), (3, 10), (5, 1), (10, 1)):
        se = 20 * math.log10(lam / (2 * L)) - 10 * math.log10(N)
        row.append(f"L={L} mm x{N}: {se:.0f} dB")
    print(f"  {f/1e6:.0f} MHz: " + "; ".join(row))

print("\n4. NFC PCB coil inductance, Greenhouse segment summation (rectangular spiral, trace w=0.5 mm, t=0.035 mm, spacing 0.5 mm)")
def self_l(l, w, t):
    return 2e-7 * l * (math.log(2 * l / (w + t)) + 0.50049 + (w + t) / (3 * l))
def mutual(l, d):
    q = math.log(l / d + math.sqrt(1 + (l / d) ** 2)) - math.sqrt(1 + (d / l) ** 2) + d / l
    return 2e-7 * l * q
def mutual_offset(l1, l2, p, q_off, d):
    def F(x):
        return x * math.log(x / d + math.sqrt(1 + (x / d) ** 2)) - math.sqrt(x * x + d * d) if x > 0 else -d
    return 1e-7 * (F(l1 + q_off + p) - F(q_off + p) - F(l1 + q_off) + F(q_off)) if False else None
def coil_L(W, H, n, w=0.5e-3, s=0.5e-3, t=35e-6):
    segs = []
    x0, y0, x1, y1 = 0.0, 0.0, W, H
    for k in range(n):
        o = k * (w + s)
        a, b, c2, d2 = x0 + o, y0 + o, x1 - o, y1 - o
        segs += [("h", a, c2, b, +1), ("v", c2, b, d2, +1), ("h", a, c2, d2, -1), ("v", a, b, d2, -1)]
    L = 0.0
    for sg in segs:
        length = abs(sg[2] - sg[1]) if sg[0] == "h" else abs(sg[3] - sg[2])
        L += self_l(length, w, t)
    for i in range(len(segs)):
        for j in range(i + 1, len(segs)):
            A, B = segs[i], segs[j]
            if A[0] != B[0]:
                continue
            if A[0] == "h":
                a0, a1, ya, sa = A[1], A[2], A[3], A[4]
                b0, b1, yb, sb = B[1], B[2], B[3], B[4]
            else:
                ya, a0, a1, sa = A[1], A[2], A[3], A[4]
                yb, b0, b1, sb = B[1], B[2], B[3], B[4]
            d = abs(ya - yb)
            if d < 1e-9:
                continue
            lo, hi = max(a0, b0), min(a1, b1)
            if hi <= lo:
                continue
            m = mutual(hi - lo, d)
            L += 2 * m * (1 if sa == sb else -1)
    return L
for (W, H) in ((28e-3, 12e-3), (24e-3, 14e-3), (20e-3, 20e-3), (40e-3, 20e-3)):
    for n in (2, 3, 4):
        print(f"  {W*1000:.0f} x {H*1000:.0f} mm, {n} turns: L ~ {coil_L(W, H, n)*1e6:.2f} uH (overlap-length approximation of mutuals; +/-15 % expected)")

print("\n5. Thermal (datasheet thermal resistances, JEDEC boards; real board differs)")
for vbat in (3.0, 3.7, 4.1):
    i = 0.5
    p = (5.0 - vbat) * i
    print(f"  BQ24074 linear charge 0.5 A at VBAT {vbat} V from 5.0 V: P = {p:.2f} W -> dT = {p*44.5:.0f} C (RthetaJA 44.5 C/W); IC reduces charge current in thermal regulation")
p = 0.3 * 0.3
print(f"  TLV755P 3.6 V -> 3.3 V at 300 mA: P = {p:.2f} W -> dT = {p*100.8:.0f} C (RthetaJA 100.8 C/W EVM)")
