VCC = 3.3
VF_65 = 1.35
VF_500 = 1.8
R_LED = 20.0
RDS_MAX_2V5 = 48e-3
RDS_MAX_4V5 = 32e-3
CISS, CRSS, QG, RG_INT = 630e-12, 50e-12, 7e-9, 3.0
R_GATE = 22.0
R_DRV = 33.0
F = 1.25e6
DUTY = 0.5
RTHJA_FET = 125.0
RTHJA_LED = 450.0
PV_MAX = 0.104
IF_AVG_MAX = 0.065
IFM_MAX = 0.130
TJ_MAX_LED = 100.0
TJ_MAX_FET = 150.0
RSW_ON_TPS22918 = 0.06

vf_est = VF_65 + (VF_500 - VF_65) * (0.095 - 0.065) / (0.5 - 0.065) * 0.5
i_pk = (VCC - vf_est - 0.095 * RDS_MAX_4V5 - 0.095 * RSW_ON_TPS22918) / R_LED
vf_pk = vf_est
i_avg = i_pk * DUTY
p_led_avg = vf_pk * i_avg
p_res = i_pk ** 2 * R_LED * DUTY
p_cond = i_pk ** 2 * RDS_MAX_4V5 * DUTY
tau_gate = (R_DRV + R_GATE + RG_INT) * (CISS + CRSS * 4)
t_rise_gate = 2.2 * tau_gate
vgs_final = VCC
p_gate_cv = (CISS + CRSS) * vgs_final ** 2 * F
p_gate_q = QG * (vgs_final / 4.5) * vgs_final * F
t_sw = t_rise_gate * 0.35
p_sw = 2 * 0.5 * VCC * i_pk * t_sw * F
p_fet = p_cond + p_sw
dt_fet = p_fet * RTHJA_FET
dt_led = p_led_avg * RTHJA_LED
tamb_max_led = TJ_MAX_LED - dt_led
tj_fet_85 = 85 + dt_fet

print("IR LED pulse current and thermal (VSMB10940, AO3400A, 3.3 V, Rled 20 ohm, 1.25 MHz carrier, 50 % duty)")
print(f"  Vf at pulse peak (interpolated between datasheet points 1.35 V @65 mA and 1.8 V @500 mA): {vf_pk:.2f} V  [CALC]")
print(f"  peak current IF_pk = {i_pk * 1e3:.0f} mA (limit IFM 130 mA at tp/T 0.5: margin {IFM_MAX / i_pk:.2f}x)  [CALC]")
print(f"  carrier-averaged LED current = {i_avg * 1e3:.0f} mA (limit continuous IF 65 mA: margin {IF_AVG_MAX / i_avg:.2f}x)  [CALC]")
print(f"  LED average power = {p_led_avg * 1e3:.0f} mW (PV max 104 mW: margin {PV_MAX / p_led_avg:.2f}x)  [CALC]")
print(f"  LED self-heating at 100 % burst duty = {dt_led:.0f} K (RthJA 450 K/W) -> maximum ambient for Tj 100 C = {tamb_max_led:.0f} C  [CALC]")
print(f"  current-limit resistor dissipation = {p_res * 1e3:.0f} mW average (0805 needs a 0.25 W part; 0.125 W part would be at {p_res / 0.125 * 100:.0f} % load)  [CALC]")
print("AO3400A gate drive and losses")
print(f"  gate time constant (driver {R_DRV:.0f} ohm + Rg {R_GATE:.0f} + internal {RG_INT:.1f}) x (Ciss + 4 Crss) = {tau_gate * 1e9:.0f} ns; 10-90 % gate rise about {t_rise_gate * 1e9:.0f} ns vs half period 400 ns  [CALC, driver 33 ohm assumed from VOH 2.2 V at 24 mA]")
print(f"  direct drive from a CC1352R pin (about 8 mA): gate charging time = Qg*Vgs-based {QG * 0.73 / 8e-3 * 1e9:.0f} ns for the charge alone, not acceptable  [CALC]")
print(f"  gate charge power = {p_gate_q * 1e3:.1f} mW (Qg scaled to 3.3 V) / CV^2f = {p_gate_cv * 1e3:.1f} mW, dissipated in the driver and Rg  [CALC]")
print(f"  conduction loss = {p_cond * 1e6:.0f} uW, switching loss (linear crossing, {t_sw * 1e9:.0f} ns) = {p_sw * 1e3:.1f} mW  [CALC]")
print(f"  MOSFET self-heating = {dt_fet:.2f} K at RthJA 125 K/W; Tj at 85 C ambient = {tj_fet_85:.1f} C (limit 150 C)  [CALC]")
print("  Vgs 3.3 V is above the 2.5 V RDS(on) test point (max 48 mOhm) and 2.3x the Vgs(th) max 1.45 V  [DS]")
print("Not verified: Vf spread with temperature, real driver output impedance, layout parasitics, ringing. All [A] until measured.")
