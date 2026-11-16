VOUT = 3.6
ETA = 0.9
L_NOM = 0.47e-6
L_TOL = 0.20
BIAS_DROP = 0.10
ISAT_30 = 6.7
IRMS_40K = 4.9
DCR_MAX = 0.023
ILIM_MIN, ILIM_TYP, ILIM_MAX = 4.0, 5.0, 5.75
THETA = 40.0 / (IRMS_40K ** 2 * DCR_MAX)
L_REC_MIN, L_REC_MAX = 0.37e-6, 0.57e-6
F_BOOST, F_BB = 2.1e6, 1.4e6


def peak(vin, iout, l, f):
    d = (VOUT - vin) / VOUT
    iavg = iout / (ETA * (1 - d))
    ripple = vin * d / (l * f)
    ipk = iavg + ripple / 2
    irms = (iavg ** 2 + ripple ** 2 / 12) ** 0.5
    return d, iavg, ripple, ipk, irms


print(f"inductor: Murata DFE252012F-R47M, 0.47 uH +-20 %, DCR max {DCR_MAX * 1e3:.0f} mohm, Isat(-30 %) {ISAT_30} A, Irms(dT 40 K) {IRMS_40K} A  [DS J(E)TE243A-0017B-01]")
print(f"thermal resistance implied by the rated point: {THETA:.0f} K/W  [CALC]")
print(f"TPS63802 boost peak current limit: min {ILIM_MIN} / typ {ILIM_TYP} / max {ILIM_MAX} A  [DS 8.5]; recommended effective L {L_REC_MIN * 1e6:.2f}-{L_REC_MAX * 1e6:.2f} uH  [DS 8.3]")
print(f"initial inductance window: {L_NOM * (1 - L_TOL) * 1e6:.3f}-{L_NOM * (1 + L_TOL) * 1e6:.3f} uH (inside the recommended window only at the lower edge); with an assumed -{BIAS_DROP * 100:.0f} % bias drop at working current the minimum is {L_NOM * (1 - L_TOL) * (1 - BIAS_DROP) * 1e6:.3f} uH  [A]")
print("TI's own listed inductors (XFL4015-471ME, DFE201612E) are also 0.47 uH +-20 %, so the same window applies to them  [DS table 10-2; tolerance of the TI parts not read]")
print()
print("Vin  Iout  mode        L_eff   D     Iavg   ripple_pp  Ipk(+20% rule)  Irms   P_dcr(85C)  dT_self")
worst = 0
for vin in (2.5, 3.0, 3.3, 3.6, 4.4):
    for iout in (0.8, 1.0, 2.0):
        for lname, l in (("nom", L_NOM), ("min-tol-bias", L_NOM * (1 - L_TOL) * (1 - BIAS_DROP))):
            if vin >= VOUT:
                continue
            f = F_BOOST if vin < 3.0 else F_BB
            d, iavg, rip, ipk, irms = peak(vin, iout, l, f)
            p = irms ** 2 * DCR_MAX * (1 + 0.0039 * 60)
            dt = p * THETA
            worst = max(worst, ipk)
            print(f"{vin:.1f}  {iout:.1f}  {lname:<13}{l * 1e6:.3f}  {d:.3f} {iavg:.2f}  {rip:.2f}      {ipk:.2f} ({ipk * 1.2:.2f})   {irms:.2f}   {p * 1e3:.0f} mW     {dt:.1f} K")
print()
print(f"worst-case steady-state peak current in the table: {worst:.2f} A (x1.2 = {worst * 1.2:.2f} A) against Isat {ISAT_30} A and the converter's maximum boost limit {ILIM_MAX} A  [CALC]")
print(f"the inductor Isat {ISAT_30} A is above the maximum current limit {ILIM_MAX} A, so even a fault that runs the converter into its limit does not drive this inductor into saturation  [DS/CALC]")
print("system load budget used above: ESP32-C3 TX peak about 0.34 A + TRF7970A up to 0.15 A + IR LED average 0.05 A + CC1352R, flash, logic about 0.1 A = about 0.65 A; 0.8 and 1.0 A are budget values, 2.0 A is the converter's rating  [A]")
print("stability: TPS63802 uses internal peak-current-mode compensation; stable inside the datasheet windows L 0.37-0.57 uH and CO,eff >= 7 uF. CO is 2 x 22 uF 10 V X5R 0805 (about 24 uF effective at 3.6 V if 55 % remains [A]); the lower edge of L is the weak point  [DS/A]")
print("not verified: inductance versus DC current curve (Murata SimSurfing), core loss at 1.4-2.1 MHz, measured efficiency and ripple")
