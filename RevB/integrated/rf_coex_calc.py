import math
C = 299792458.0
F = 2.44e9
LAM = C / F * 1e3
D = 58.8
fspl = 20 * math.log10(4 * math.pi * D / LAM)
print(f"wavelength at 2.44 GHz {LAM:.1f} mm; distance {D} mm = {D / LAM:.2f} wavelengths (near field, Friis is only an ESTIMATE)")
print(f"free-space path loss for isotropic antennas at {D} mm: {fspl:.1f} dB. This is a calculated estimate, NOT measured antenna isolation.")
print()
print("worst-case 2.4 GHz power when the ESP32 transmits. The ESP32 conducted TX is 20.5 dBm (802.11b) [DS ESP32-C3-WROOM-02 table 7-2]")
print("CC1352R absolute maximum 2.4 GHz RF input +5 dBm [DS SWRS196I 8.1]. Protection margins are computed on the NO-LOSS basis: P_in = P_TX + S21,")
print("because the IPC insertion loss (1.3 dB typ, 1.6 dB max [DS Johanson]) has no guaranteed minimum and S21 is an antenna-port to antenna-port figure.")
print("   S21 dB | P_in no-loss (protection basis) | margin to +5 dBm | with 1.3 dB typ IPC loss (reference only)")
for s21 in (-10.0, -15.6, -20.0, -25.0, -30.0):
    p = 20.5 + s21
    print(f"   {s21:6.1f} | {p:+6.1f} dBm | {5.0 - p:+6.1f} dB | {p - 1.3:+6.1f} dBm")
print("The previous gate report listed the with-loss column (+9.2, +3.6, -10.8 dBm); the earlier R2 report listed the no-loss values for -15.6 and -30 (+4.9, -9.5). Both were correct for their basis, the basis was not stated; the 1.3 dB is the IPC typical insertion loss.")
print()
print("reverse direction: CC1352R TX +5 dBm (2.4 GHz PA) into the ESP32 receiver, sensitivity -98 dBm (11b 1 Mbps) [DS]")
for s21 in (-10.0, -15.6, -20.0, -30.0):
    p = 5.0 + s21
    print(f"   S21 {s21:6.1f} dB: {p:6.1f} dBm at the ESP32 antenna port (no-loss basis), {p + 98:5.1f} dB above sensitivity")
print()
print("isolation required for simultaneous same-band operation if the victim receiver tolerates an interferer of X dBm (X is an ASSUMPTION, no blocking figure was read):")
for x in (-30, -40, -50):
    print(f"   X {x} dBm: ESP32 -> CC1352R needs {20.5 - x:.0f} dB, CC1352R -> ESP32 needs {5.0 - x:.0f} dB")
print("achievable on one 80 x 50 mm board between two small PCB antennas is of the order of 15-30 dB [A, no source]; therefore time slotting is mandatory")
