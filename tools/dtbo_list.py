#!/usr/bin/env python3
"""List Android DTBO entries and report each overlay's root compatible/model."""
import struct
import sys
from pathlib import Path

from dtb_dump import parse, fmt

MAGIC = 0xD7B7AB1E


class Blob:
    def __init__(self, data):
        self.data = data

    def read_bytes(self):
        return self.data


def main():
    for arg in sys.argv[1:]:
        b = Path(arg).read_bytes()
        magic, total, hsize, esize, count, dt_off = struct.unpack_from(">6I", b, 0)
        if magic != MAGIC:
            print(f"{arg}: not DTBO (magic={magic:#x})")
            continue
        print(f"\n===== {Path(arg).name}: count={count} size={total:#x} file={len(b):#x} =====")
        for i in range(count):
            ent = dt_off + i * esize
            size, off = struct.unpack_from(">II", b, ent)
            ident = list(struct.unpack_from(">6I", b, ent + 8))
            blob = b[off:off + size]
            if blob[:4] != b"\xd0\x0d\xfe\xed":
                print(f"{i:02d}: bad dtb at {off:#x}: {blob[:8].hex()}")
                continue
            nodes, _, _ = parse(Blob(blob))
            root = nodes[0]["props"] if nodes else {}
            compat = fmt(root.get("compatible", b""))
            model = fmt(root.get("model", b""))
            print(f"{i:02d}: size={size:#x} off={off:#x} id={[hex(x) for x in ident]} compat={compat} model={model}")


if __name__ == "__main__":
    main()
