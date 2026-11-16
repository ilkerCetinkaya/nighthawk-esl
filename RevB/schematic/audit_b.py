import collections
import sys
import xml.etree.ElementTree as ET

root = ET.parse("nets.xml").getroot()
comp = {c.get("ref"): c for c in root.find("components")}
nets = {}
pinnet = collections.defaultdict(dict)
for n in root.find("nets"):
    name = n.get("name")
    nodes = [(x.get("ref"), x.get("pin"), x.get("pinfunction") or "", x.get("pintype") or "") for x in n.findall("node")]
    nets[name] = nodes
    for ref, pin, fn, ty in nodes:
        pinnet[ref][pin] = (name, fn, ty)

def val(ref):
    v = comp[ref].find("value")
    return v.text if v is not None else ""

if len(sys.argv) > 1:
    for ref in sys.argv[1:]:
        print("==", ref, val(ref))
        for pin, (name, fn, ty) in sorted(pinnet[ref].items(), key=lambda kv: (len(kv[0]), kv[0])):
            others = [f"{r}.{p}" for r, p, _, _ in nets[name] if (r, p) != (ref, pin)][:6]
            print(f"  {pin:>3} {fn:<16}{ty:<14}-> {name:<18} {others}")
    sys.exit()

singles = [(n, v) for n, v in nets.items() if len(v) < 2]
print("nets:", len(nets), "components:", len(comp))
print("single-pin nets:", [(n, v[0][0] + "." + v[0][1]) for n, v in singles])
unnet = [(r, p) for r, c in comp.items() for p in []]
