import collections
import csv
import design_b as d
import passive_data as pd

DIGIKEY_MPN = {"0900PC15A0036001E", "36103205S", "36003200S", "TLV3501AIDBVR"}
ALT_DIGIKEY = {"C37": "Johanson 500R07S3R9BV4T", "C38": "Johanson 500R07S0R3BV4T", "L4": "Johanson L-07C18NJV6T"}


def pkg(fp):
    n = fp.split(":")[-1]
    for k in ("0402", "0603", "0805", "1008", "1206"):
        if f"_{k}" in n:
            return k
    return n


def ladder_of(code):
    return pd.DATA[code][4] if code in pd.DATA else pd.OTHER[code][1]


def price(code, qty):
    ladder = ladder_of(code)
    best = ladder[0][1]
    for q, p in ladder:
        if qty >= q:
            best = p
    return best


def source(p):
    if p["mpn"] in DIGIKEY_MPN or p["ref"] in ("U12",):
        return "DigiKey/Farnell"
    if p["lcsc"]:
        return "LCSC/JLCPCB"
    return "OPEN"


groups = collections.OrderedDict()
for p in d.PARTS:
    key = (p["value"], p["fp"], p["mpn"], p["lcsc"], p["dnp"], p["ref"][0] if p["ref"][0] not in "RCL" else "", p["desc"] if p["ref"][0] not in "RCLT" else "")
    groups.setdefault(key, []).append(p)

with open("BOM_REVB_schematic.csv", "w", newline="") as h:
    w = csv.writer(h)
    w.writerow(["Refs", "Qty", "Qty_populated", "Value", "Package", "Footprint", "Manufacturer", "MPN", "LCSC", "LCSC_stock", "JLC_class", "Datasheet", "DNP", "Source", "Unit_USD_qty5boards", "Cost_USD_per_board", "Cost_USD_5_boards", "Cost_USD_50_boards", "Cost_USD_500_boards", "RF_critical", "Description"])
    for key, ps in groups.items():
        p = ps[0]
        pop = 0 if p["dnp"] else len(ps)
        code = p["lcsc"]
        has = code in pd.DATA or code in pd.OTHER
        stock = (pd.DATA[code][2] if code in pd.DATA else pd.OTHER[code][0]) if has else ""
        cls = (("Basic" if pd.DATA[code][3] else "Extended") if code in pd.DATA else {"B": "Basic", "E": "Extended", "E?": "Extended (assumed, not checked)"}[pd.OTHER[code][2]]) if has else ""
        ds = pd.DATA[code][5] if code in pd.DATA else p["ds"]
        up = price(code, pop * 5) if has and pop else ""
        row_cost = [round(price(code, pop * n) * pop, 4) if has and pop else "" for n in (1, 5, 50, 500)]
        c5 = round(price(code, pop * 5) * pop * 5, 3) if has and pop else ""
        c50 = round(price(code, pop * 50) * pop * 50, 2) if has and pop else ""
        c500 = round(price(code, pop * 500) * pop * 500, 2) if has and pop else ""
        rf = "; ".join(sorted({pd.RF_CRITICAL[x["ref"]] for x in ps if x["ref"] in pd.RF_CRITICAL}))
        w.writerow([",".join(x["ref"] for x in ps), len(ps), pop, p["value"], pkg(p["fp"]), p["fp"], p["mfr"], p["mpn"], code, stock, cls, ds, "DNP" if p["dnp"] else "", source(p), up, row_cost[0], c5, c50, c500, "YES" if rf else "", p["desc"] + ((" | RF note: " + rf) if rf else "")])

sel = [p for p in d.PARTS if p["ref"] in d.GENERIC_REFS]
print("lines:", len(groups), "parts:", len(d.PARTS))
with open("RF_CRITICAL_PASSIVES.csv", "w", newline="") as h:
    w = csv.writer(h)
    w.writerow(["Ref", "Value", "Package", "MPN", "LCSC", "Dielectric_or_type", "Role", "DNP", "Alternative_if_needed"])
    for p in d.PARTS:
        if p["ref"] in pd.RF_CRITICAL:
            w.writerow([p["ref"], p["value"], pkg(p["fp"]), p["mpn"], p["lcsc"], "inductor" if p["ref"][0] == "L" else ("resistor" if p["ref"][0] == "R" else "C0G"), pd.RF_CRITICAL[p["ref"]], "DNP" if p["dnp"] else "", ALT_DIGIKEY.get(p["ref"], "")])
