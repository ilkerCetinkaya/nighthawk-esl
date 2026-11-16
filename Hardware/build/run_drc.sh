#!/bin/zsh
cd "$(dirname "$0")"
CLI=/Applications/KiCad/KiCad.app/Contents/MacOS/kicad-cli
$CLI pcb drc --format json --severity-all --units mm --refill-zones -o work/drc.json ../NIGHTHAWK.kicad_pcb >/dev/null 2>&1
python3 - <<'PY'
import json,collections
d=json.load(open("work/drc.json"))
print(dict(collections.Counter(v["type"] for v in d["violations"])), "unconnected", len(d.get("unconnected_items",[])))
seen=set()
for v in d["violations"]:
    if v["type"] in ("silk_overlap","text_height","silk_over_copper","silk_edge_clearance","starved_thermal"): continue
    k=(v["type"],v["items"][0]["description"][:28])
    if k in seen: continue
    seen.add(k); print(" ",v["type"],v["description"][:90],"|",[i["description"][:48] for i in v["items"]][:2])
PY
