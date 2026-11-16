import math
ESL = {"0402 part+pads (low)": 0.3e-9, "0402 part+pads (typical)": 0.4e-9, "0402 part+pads (high)": 0.6e-9}
caps = [("C34/C35/C59 100 pF (IPC C41/C51, NFC C21)", 100e-12, [868e6, 2.44e9, 13.56e6]), ("C57 220 pF NFC", 220e-12, [13.56e6]), ("C63 330 pF NFC tank", 330e-12, [13.56e6]),
        ("C55/C58 680 pF NFC", 680e-12, [13.56e6]), ("C53/C54 1.2 nF NFC", 1.2e-9, [13.56e6]), ("C51/C52 1.5 nF NFC series", 1.5e-9, [13.56e6]),
        ("C69 1.5 pF TIA", 1.5e-12, [10.6e6]), ("C37 3.9 pF 868 MHz match", 3.9e-12, [868e6]), ("C38 0.3 pF 868 MHz match", 0.3e-12, [868e6])]
print("SRF = 1/(2 pi sqrt(L C)) with assumed ESL; effective C = C/(1-(f/SRF)^2); |X| at f  [CALC, ESL is an assumption, Murata/Samsung data not read]")
for name, c, fs in caps:
    print(name)
    for k, l in ESL.items():
        srf = 1 / (2 * math.pi * math.sqrt(l * c))
        row = []
        for f in fs:
            r = f / srf
            ceff = c / (1 - r * r) if r < 0.99 else float("inf")
            x = 2 * math.pi * f * l - 1 / (2 * math.pi * f * c)
            row.append(f"{f / 1e6:.0f} MHz: f/SRF {r:.2f}, Ceff {ceff * 1e12:.1f} pF, X {x:+.2f} ohm")
        print(f"   ESL {l * 1e9:.1f} nH ({k}): SRF {srf / 1e6:.0f} MHz | " + " | ".join(row))
