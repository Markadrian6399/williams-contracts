#!/usr/bin/env python3
"""Generate (or --check) the README "Contract Functions" table from the
public entry points declared in contracts/will/src/lib.rs (issue #235)."""
import re, sys

LIB = "contracts/will/src/lib.rs"
README = "README.md"
BEGIN, END = "<!-- api-table:begin -->", "<!-- api-table:end -->"


def signatures(src):
    for m in re.finditer(r"\n    pub fn (\w+)\(", src):
        i, depth = m.end(), 1
        while depth:
            depth += {"(": 1, ")": -1}.get(src[i], 0)
            i += 1
        args = src[m.end():i - 1]
        ret = re.match(r"\s*(?:->\s*([^{]+?))?\s*\{", src[i:]).group(1)
        parts, depth, cur = [], 0, ""
        for ch in args:
            depth += {"<": 1, "(": 1, ">": -1, ")": -1}.get(ch, 0)
            if ch == "," and depth == 0:
                parts.append(cur); cur = ""
            else:
                cur += ch
        parts.append(cur)
        params = [p.split(":")[0].strip() for p in parts if ":" in p]
        yield m.group(1), [p for p in params if p != "env"], ret


def table():
    rows = ["| Function | Parameters | Returns |", "|---|---|---|"]
    for name, params, ret in signatures(open(LIB).read()):
        p = ", ".join(f"`{x}`" for x in params) or "—"
        r = f"`{' '.join(ret.split())}`" if ret else "—"
        rows.append(f"| `{name}` | {p} | {r} |")
    return "\n".join(rows)


readme = open(README).read()
head, rest = readme.split(BEGIN, 1)
_, tail = rest.split(END, 1)
new = f"{head}{BEGIN}\n{table()}\n{END}{tail}"
if "--check" in sys.argv:
    if new != readme:
        sys.exit("README function table is stale; run scripts/gen-api-table.py")
else:
    open(README, "w").write(new)
