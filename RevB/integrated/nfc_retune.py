import math
import sys

from nfc_coil_design import W0, match, s11_bw

E24 = [1.0, 1.1, 1.2, 1.3, 1.5, 1.6, 1.8, 2.0, 2.2, 2.4, 2.7, 3.0, 3.3, 3.6, 3.9, 4.3, 4.7, 5.1, 5.6, 6.2, 6.8, 7.5, 8.2, 9.1]
E96 = [1.00, 1.02, 1.05, 1.07, 1.10, 1.13, 1.15, 1.18, 1.21, 1.24, 1.27, 1.30, 1.33, 1.37, 1.40, 1.43, 1.47, 1.50, 1.54, 1.58, 1.62, 1.65, 1.69, 1.74, 1.78, 1.82, 1.87, 1.91,
       1.96, 2.00, 2.05, 2.10, 2.15, 2.21, 2.26, 2.32, 2.37, 2.43, 2.49, 2.55, 2.61, 2.67, 2.74, 2.80, 2.87, 2.94, 3.01, 3.09, 3.16, 3.24, 3.32, 3.40, 3.48, 3.57, 3.65, 3.74, 3.83, 3.92,
       4.02, 4.12, 4.22, 4.32, 4.42, 4.53, 4.64, 4.75, 4.87, 4.99, 5.11, 5.23, 5.36, 5.49, 5.62, 5.76, 5.90, 6.04, 6.19, 6.34, 6.49, 6.65, 6.81, 6.98, 7.15, 7.32, 7.50, 7.68, 7.87, 8.06,
       8.25, 8.45, 8.66, 8.87, 9.09, 9.31, 9.53, 9.76]


def nearest(v, series):
    best = None
    dec = 10 ** math.floor(math.log10(v))
    for d in (dec / 10, dec, dec * 10):
        for e in series:
            c = e * d
            if best is None or abs(c - v) < abs(best - v):
                best = c
    return best


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("usage: nfc_retune.py L_uH (measured at 13.56 MHz) Rs_ohm_or_-Q (series resistance, or negative number = measured Q) [target_Q=7]")
        sys.exit(0)
    L = float(sys.argv[1]) * 1e-6
    x = float(sys.argv[2])
    rs = (W0 * L / -x) if x < 0 else x
    q = float(sys.argv[3]) if len(sys.argv) > 3 else 7.0
    rp, cp, cs, z = match(L, rs, q)
    print(f"INPUT (measured): L = {L * 1e6:.3f} uH, Rs = {rs:.3f} ohm (Q0 = {W0 * L / rs:.0f}); target loaded Q = {q}")
    print(f"CALCULATED: Rp = {rp:.0f} ohm (E96 {nearest(rp, E96):.0f}), Cp = {cp * 1e12:.1f} pF (E24 {nearest(cp * 1e12, E24):.1f}), Cs = {cs * 1e12:.1f} pF (E24 {nearest(cs * 1e12, E24):.1f})")
    print(f"-10 dB return-loss bandwidth with the exact values: {s11_bw(L, rs, rp, cp, cs) / 1e6:.2f} MHz")
    print("Cs is made of C61 + C62 in parallel, Cp of C63 + C64; Rp is R42; then tune on the VNA at J8 with R39 removed.")
