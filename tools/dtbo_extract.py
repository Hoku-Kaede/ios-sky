#!/usr/bin/env python3
"""Extract individual DTB overlays from an Android DTBO image."""
import struct
import sys
from pathlib import Path

src, outdir = sys.argv[1], sys.argv[2]
b = Path(src).read_bytes()
magic, total, hsize, esize, count, dt_off = struct.unpack_from(">6I", b, 0)
assert magic == 0xD7B7AB1E, hex(magic)
out = Path(outdir)
out.mkdir(parents=True, exist_ok=True)
for i in range(count):
    size, off = struct.unpack_from(">II", b, dt_off + i * esize)
    (out / f"{i:02d}.dtbo").write_bytes(b[off:off + size])
print(f"wrote {count} overlays")
