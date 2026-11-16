import re
import uuid

SUPPORT = "/Applications/KiCad/KiCad.app/Contents/SharedSupport"


class Q(str):
    pass


TOKEN = re.compile(r'\(|\)|"(?:\\.|[^"\\])*"|[^\s()"]+')


def parse(text):
    stack = [[]]
    for tok in TOKEN.findall(text):
        if tok == "(":
            stack.append([])
        elif tok == ")":
            node = stack.pop()
            stack[-1].append(node)
        elif tok.startswith('"'):
            stack[-1].append(Q(tok[1:-1]))
        else:
            stack[-1].append(tok)
    return stack[0][0]


def esc(s):
    return str(s).replace("\\", "\\\\").replace('"', '\\"')


def dump(node, indent=0):
    pad = "\t" * indent
    if not isinstance(node, list):
        return f'"{esc(node)}"' if isinstance(node, Q) else str(node)
    if all(not isinstance(c, list) for c in node):
        return pad + "(" + " ".join(dump(c) for c in node) + ")"
    head = []
    rest = []
    for c in node:
        if isinstance(c, list):
            rest.append(c)
        elif not rest:
            head.append(c)
        else:
            rest.append(c)
    out = pad + "(" + " ".join(dump(c) for c in head)
    for c in rest:
        if isinstance(c, list):
            out += "\n" + dump(c, indent + 1)
        else:
            out += " " + dump(c)
    out += "\n" + pad + ")"
    return out


_lib_cache = {}


def lib_symbols(lib):
    if lib not in _lib_cache:
        with open(f"{SUPPORT}/symbols/{lib}.kicad_sym") as handle:
            tree = parse(handle.read())
        _lib_cache[lib] = {c[1]: c for c in tree if isinstance(c, list) and c and c[0] == "symbol"}
    return _lib_cache[lib]


def flatten(lib, name):
    node = lib_symbols(lib)[name]
    parent = next((c for c in node if isinstance(c, list) and c and c[0] == "extends"), None)
    if not parent:
        return ["symbol", Q(f"{lib}:{name}")] + [c for c in node[2:]]
    base = flatten(lib, str(parent[1]))
    props = {c[1]: c for c in node if isinstance(c, list) and c and c[0] == "property"}
    merged = [base[0], base[1]]
    for c in base[2:]:
        if isinstance(c, list) and c and c[0] == "property" and c[1] in props:
            merged.append(props[c[1]])
        elif isinstance(c, list) and c and c[0] == "symbol":
            sub = list(c)
            sub[1] = Q(str(c[1]).replace(str(parent[1]), name, 1))
            merged.append(sub)
        else:
            merged.append(c)
    return ["symbol", Q(f"{lib}:{name}")] + merged[2:]




def pins_of(lib, name):
    node = lib_symbols(lib)[name]
    parent = next((c for c in node if isinstance(c, list) and c and c[0] == "extends"), None)
    if parent:
        node = lib_symbols(lib)[str(parent[1])]
    pins = []

    def walk(n):
        if isinstance(n, list):
            if n and n[0] == "pin" and any(isinstance(c, list) and c and c[0] == "number" for c in n):
                at = next(c for c in n if isinstance(c, list) and c[0] == "at")
                number = next(c for c in n if isinstance(c, list) and c[0] == "number")[1]
                pins.append((str(number), float(at[1]), float(at[2]), float(at[3])))
            for c in n:
                walk(c)

    walk(node)
    return pins




def uid(*parts):
    return str(uuid.uuid5(uuid.NAMESPACE_DNS, ":".join(str(p) for p in parts)))
