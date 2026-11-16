import math, importlib.util, io, contextlib

print("=== CC1352R proprietary PHY ranges (TRM SWCU185G, Eq. 15 and Table 25-175/25-183) ===")
fclk = 48e6
def fbaud(R, p):
    return R * fclk / (p * 2**21)
print(f"symbol rate: fbaud = R * 48 MHz / (p * 2^21); R is 21 bits (1..{2**21-1}), p 4..255")
for R, p in ((2**21-1, 4), (350000, 4), (170000, 4), (100000, 8), (1, 255)):
    print(f"  R={R:>8} p={p:>3}: {fbaud(R,p)/1e3:10.3f} kBaud")
print("  (the formula range is wider than the characterised range; datasheet characterises specific rates only)")
print("deviation: 11-bit field (0..2047) x step {15.625, 62.5, 250, 1000} Hz")
for step in (15.625, 62.5, 250, 1000):
    print(f"  step {step:>7} Hz: max {2047*step/1e3:8.1f} kHz, resolution {step} Hz")
print("frequency: CMD_FS integer MHz + fractFreq/65536 MHz -> programming step", round(1e6/65536, 3), "Hz")
print("channel spacing 500 kHz = 32768 fractFreq counts: exactly representable")
for k in (0, 1, 2, 78, 156):
    f = 2402 + 0.5 * k
    ip = int(f); fr = round((f - ip) * 65536)
    print(f"  Hanshow-style grid ch{k:>3}: {f:7.1f} MHz -> frequency={ip}, fractFreq={fr}")

print("\nRX bandwidth settings available at 2432 MHz (TRM Table 25-183, enhanced mode), selected rows:")
rows = {84: 153.1, 85: 174.2, 86: 219.6, 87: 263.9, 88: 306.1, 89: 348.3, 90: 439.1, 91: 527.8, 92: 612.2, 93: 696.7, 94: 878.2, 95: 1055.6, 96: 1224.4, 97: 1393.3, 98: 1756.4, 99: 2111.1}
for s, bw in rows.items():
    print(f"  setting {s}: {bw} kHz")
print("  Hanshow 20 dB bandwidth 558-591 kHz [FCC test report]; SoluM 6 dB 708 kHz, 99% 1.05-1.06 MHz [FCC test report]")

print("\n=== IR LED driver (VSMB10940, AO3400A) ===")
vcc = 3.3; vf = 1.5; vds = 0.05
for R in (12, 13, 15, 18, 22):
    i = (vcc - vf - vds) / R
    p_led_pulse = i * vf
    print(f"  R={R:>2} ohm: I_pk = {i*1e3:6.1f} mA, LED pulse power {p_led_pulse*1e3:6.1f} mW, resistor pulse power {i*i*R*1e3:6.1f} mW")
R = 15
ipk = (vcc - 1.55 - vds) / R
print(f"chosen R={R} ohm: I_pk (VF 1.55 V) = {ipk*1e3:.0f} mA  (datasheet: IFM 130 mA at tp/T 0.5, tp 100 us; IFSM 500 mA at tp 100 us)")
carrier = 1.25e6
tp = 0.5 / carrier
print(f"carrier 1.25 MHz square: pulse width {tp*1e9:.0f} ns, period {1e9/carrier:.0f} ns")
for burst, period in ((40e-6, 61e-6), (40e-6, 150e-6), (40e-6, 284e-6)):
    duty = 0.5 * burst / period
    iavg = ipk * duty
    pav = iavg * 1.5
    print(f"  burst {burst*1e6:.0f} us every {period*1e6:.0f} us -> duty {duty*100:.1f} %, I_avg {iavg*1e3:5.1f} mA, P_avg {pav*1e3:5.1f} mW, dTj {pav*450:4.1f} K (RthJA 450 K/W), PV limit 104 mW")
worst = ipk * 0.5 * 1.5
print(f"  worst case continuous 1.25 MHz carrier: P = {worst*1e3:.0f} mW vs PV 104 mW, dTj = {worst*450:.0f} K -> Tj = {25+worst*450:.0f} C vs 100 C limit at 25 C ambient: needs a firmware limit on burst length and duty")
print("MOSFET AO3400A [DS]: Vgs(th) 0.65-1.45 V, Qg 6-7 nC (Vgs 4.5 V), Ciss 630 pF")
Qg = 7e-9
print(f"  gate drive charge current at 1.25 MHz: {Qg*carrier*1e3:.1f} mA average; with 100 ohm gate resistor tau = {100*630e-12*1e9:.0f} ns (vs 400 ns pulse)")
print(f"  gate drive from a CC1352 DIO at 3.3 V: Vgs = 3.3 V is above Vth max 1.45 V; RDS(on) at 2.5-4.5 V is in the datasheet curves (numbers not extracted) -> assumed <= 0.1 ohm, drop {ipk*0.1*1e3:.0f} mV")

print("\n=== IR photodiode TIA (VEMD10940F, OPA356) ===")
GBW = 200e6
for Rf in (4.7e3, 10e3, 22e3, 47e3):
    for Cin in (8e-12,):
        cf_min = math.sqrt(Cin / (2 * math.pi * Rf * GBW))
        for Cf in (1.0e-12, 1.5e-12, 2.2e-12):
            bw = 1 / (2 * math.pi * Rf * Cf)
            ok = Cf >= cf_min
            inoise = math.sqrt(4 * 1.380649e-23 * 300 / Rf) * math.sqrt(bw)
            print(f"  Rf={Rf/1e3:5.1f}k Cin={Cin*1e12:.0f}pF Cf={Cf*1e12:.1f}pF: -3dB {bw/1e6:6.2f} MHz, Cf_min(stability est.) {cf_min*1e12:.2f} pF, ok={ok}, Rf noise {inoise*1e9:5.2f} nA rms, 1 uA -> {1e-6*Rf*1e3:.0f} mV")
print("  VEMD10940F [DS]: CD 1.3 pF at 5 V (0 V value garbled in extraction), tr 100 ns (RL 1 kohm), Ira 234 uA at 1 mW/cm2 / 950 nm / 5 V")
print("  required signal bandwidth >= 1.25 MHz carrier +/- 10 kHz passband (Furrtek [S]); a 100 ns rise time corresponds to about 3.5 MHz [CALC]")
print("  irradiance of a real Pricer transmitter at 1-3 m is unknown [U]: sensitivity and range cannot be computed")

print("\n=== NFC coil tank (24 x 12 mm was assumed; this layout reserves 28 x 16 mm) ===")
spec = importlib.util.spec_from_file_location("e", "../obsolete/tools_module_architecture/emc_calc.py"); m = importlib.util.module_from_spec(spec)
with contextlib.redirect_stdout(io.StringIO()): spec.loader.exec_module(m)
f0 = 13.56e6
for (W, H) in ((28e-3, 16e-3), (24e-3, 12e-3)):
    for n in (2, 3, 4):
        L = m.coil_L(W, H, n)
        C = 1 / ((2 * math.pi * f0) ** 2 * L)
        length = n * 2 * (W + H)
        rdc = 1.68e-8 * length / (0.5e-3 * 35e-6)
        Q = 2 * math.pi * f0 * L / rdc
        print(f"  {W*1e3:.0f}x{H*1e3:.0f} mm, {n} turns: L ~ {L*1e6:.3f} uH, resonating C = {C*1e12:6.0f} pF, trace {length*1e3:.0f} mm, R_dc ~ {rdc:.2f} ohm, unloaded Q ~ {Q:.0f}")
print("  ISO 14443 needs a loaded Q low enough for ~ MHz-wide sidebands (loaded Q about 10-30 [A]); a damping resistor in the tank is required (TI reference uses 680 ohm, Fig. 7-1)")
print("  TI reference tank values (Fig. 7-1, for a 0.95 uH antenna): C23 68 pF series, C24 82 pF shunt, R6 680 ohm, optional C27 1 pF / C28 2 pF: NOT directly reusable for 0.3 uH")
