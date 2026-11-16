import collections
import design_b as d
import passive_data as pd

FEE = 3.07
REVERSE = {"C1525": ("C108079", "100n"), "C23630": ("C100082", "2.2u"), "C59461": ("C29277", "22u")}
HAND = {"LED set (D4-D7, 3 unique Extended)": ["C51933293", "C51933297", "C2286"], "Debug/interlock headers J6,J7 (THT)": ["C2691448"],
        "PTC F1 + ferrite beads FB1-FB2": ["C17313", "C19330"], "Reset/boot/user buttons SW1-SW4": ["C221895"]}
NOT_LCSC = {"U8 Johanson IPC 0900PC15A0036001E": "DigiKey ~CHF 0.73", "SH1/SH2 Wuerth 36103205S frames": "DigiKey/Farnell, price not read", "SH1C/SH2C Wuerth 36003200S covers": "DigiKey/Farnell, price not read", "U12 TLV3501AIDBVR": "DigiKey, price not read"}


def info(code):
    if code in pd.DATA:
        dd = pd.DATA[code]
        return dd[4], ("B" if dd[3] else "E")
    o = pd.OTHER[code]
    return o[1], o[2]


def price(lad, q):
    best = lad[0][1]
    for t, p in lad:
        if q >= t:
            best = p
    return best


def lines(baseline):
    c = collections.Counter()
    for p in d.PARTS:
        if p["dnp"] or not p["lcsc"] or p["lcsc"] == "":
            continue
        code = p["lcsc"]
        if baseline and code in REVERSE:
            code = REVERSE[code][0]
        c[code] += 1
    return c


def scenario(c, n, hand=()):
    handcodes = {x for h in hand for x in HAND[h]}
    total, ext = 0.0, set()
    for code, q in c.items():
        if code in handcodes:
            continue
        lad, cls = info(code)
        total += price(lad, q * n) * q * n
        if cls != "B":
            ext.add(code)
    return total, len(ext), total + FEE * len(ext)


if __name__ == "__main__":
    base, cur = lines(True), lines(False)
    print("populated LCSC lines baseline:", len(base), "current:", len(cur))
    hand_all = list(HAND)
    rows = []
    for n in (1, 5, 50, 100):
        b = scenario(base, n)
        c = scenario(cur, n)
        h = scenario(cur, n, hand_all)
        rows.append((n, b, c, h))
        print(f"N={n:3d} | baseline parts ${b[0]:.2f} + {b[1]} ext x $3.07 = ${b[2]:.2f} (${b[2] / n:.2f}/board) | swaps parts ${c[0]:.2f} + {c[1]} ext = ${c[2]:.2f} (${c[2] / n:.2f}/board) | swaps + hand-fit {len(hand_all)} groups: parts ${h[0]:.2f} + {h[1]} ext = ${h[2]:.2f} (${h[2] / n:.2f}/board)")
    print("extended codes (current):", sorted(code for code in cur if info(code)[1] != "B"))
