import json
import math
import subprocess
import sys

import pcbnew

SUBSET = ["FLASH_WP", "FLASH_CS", "FLASH_HOLD", "BB_EN", "BB_FB", "BB_MODE", "ARM_WDG", "LOOPS_OK", "RESET_BTN", "BQ_ISET", "BQ_ILIM", "BQ_ITERM", "BQ_TMR", "BQ_TS", "CC1", "CC2"]
KCLI = "/Applications/KiCad/KiCad.app/Contents/MacOS/kicad-cli"


def drc(path):
    subprocess.run([KCLI, "pcb", "drc", "--format", "json", "--severity-all", "-o", "/tmp/_m.json", path], capture_output=True)
    d = json.load(open("/tmp/_m.json"))
    c = {}
    for v in d["violations"]:
        c[v["type"]] = c.get(v["type"], 0) + 1
    return c, len(d["unconnected_items"])


def stats(path):
    b = pcbnew.LoadBoard(path)
    length = 0.0
    vias = 0
    per = {}
    for t in b.GetTracks():
        n = t.GetNetname()
        if t.GetClass() == "PCB_VIA":
            if n in SUBSET:
                vias += 1
        elif n in SUBSET:
            length += pcbnew.ToMM(t.GetLength())
            per[n] = per.get(n, 0) + 1
    return round(length, 1), vias, len(per)


if __name__ == "__main__":
    base_c, base_u = drc(sys.argv[1])
    for p in sys.argv[2:]:
        c, u = drc(p)
        delta = {k: c.get(k, 0) - base_c.get(k, 0) for k in set(c) | set(base_c) if c.get(k, 0) != base_c.get(k, 0) and not k.startswith("silk")}
        print(p.split("/")[-1], "unconnected", u, "(baseline", base_u, ") length_mm/vias/nets_with_tracks", stats(p), "DRC delta vs baseline", delta)
