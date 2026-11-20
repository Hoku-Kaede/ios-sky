#!/usr/bin/env python3
"""Print all properties of DTB nodes whose path matches a substring."""
import sys
from pathlib import Path

from dtb_dump import parse, fmt

path = Path(sys.argv[1])
needle = sys.argv[2].lower()
nodes, ver, total = parse(path)
for n in nodes:
    if needle in n["path"].lower():
        print(f"[{n['path']}]")
        for k, v in n["props"].items():
            print(f"  {k} = {fmt(v)}")
