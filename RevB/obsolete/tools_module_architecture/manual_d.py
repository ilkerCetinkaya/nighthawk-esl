import json, os
os.environ.setdefault("DROP", "SD")
from feasibility import violations
P = {
 "ESP32": (6, 22, 14, 18, "T"),
 "USB": (72.7, 0, 7.3, 9.4, "T"),
 "USB_ESD": (64.0, 12.6, 7.0, 6.0, "T"),
 "BATT": (29.5, 19.5, 50.5, 20.5, "B"),
 "COIL": (21.0, 1.0, 24.0, 12.0, "T"),
 "NFC_IC": (21.0, 13.5, 15.0, 10.0, "T"),
 "CHG": (71.5, 10.0, 8.5, 7.5, "T"),
 "REG": (58.0, 19.5, 12.0, 12.0, "T"),
 "DIG1": (36.5, 13.5, 21.0, 14.0, "T"),
 "DIG2": (6.0, 0.0, 14.0, 21.5, "B"),
 "JST_M1": (21.0, 33.4, 18.8, 6.6, "T"),
 "JST_M2": (73.4, 19.5, 6.6, 18.8, "T"),
 "SMA_IN": (58.5, 0.0, 8.0, 12.1, "T"),
 "SMA_TEST": (50.0, 0.0, 8.0, 12.1, "T"),
 "BATT_CONN": (22.0, 33.5, 5.8, 6.5, "B"),
 "UI": (40.5, 28.0, 17.0, 12.0, "T"),
 "STOR": (8.0, 0.5, 12.0, 8.0, "T"),
}
sol = {k: dict(x=v[0], y=v[1], w=v[2], h=v[3], side=v[4]) for k, v in P.items()}
v = violations(sol)
print(len(v), "violations")
for m in v: print("  -", m)
json.dump(sol, open("manual_d.json", "w"), indent=1)
