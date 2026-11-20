#!/usr/bin/env python3
"""Minimal flat device-tree dump tool for Qualcomm stock DTBs."""
import struct
import sys
from pathlib import Path

MAGIC = 0xD00DFEED
BEGIN, END, PROP, NOP, ENDALL = 1, 2, 3, 4, 9


def u32(buf, off):
    return struct.unpack_from(">I", buf, off)[0]


def u64(buf, off):
    return struct.unpack_from(">Q", buf, off)[0]


def text(raw):
    if not raw:
        return ""
    s = raw.split(b"\0", 1)[0]
    try:
        v = s.decode("ascii")
    except UnicodeDecodeError:
        return ""
    return v if all(32 <= ord(c) < 127 or c == "\n" for c in v) else ""


def fmt(raw):
    t = text(raw)
    if t:
        return repr(t)
    if len(raw) <= 64:
        return raw.hex()
    return raw[:64].hex() + f"... ({len(raw)} bytes)"


def parse(path):
    b = path.read_bytes()
    if u32(b, 0) != MAGIC:
        raise ValueError(f"{path}: not a DTB")
    tot, struct_off, strings_off, rsvmap_off = struct.unpack_from(">IIII", b, 4)
    version = u32(b, 16)
    strings = b[strings_off:tot]
    off = struct_off
    stack = []
    nodes = []
    cur = None
    while off < tot:
        tag = u32(b, off)
        off += 4
        if tag == BEGIN:
            name = b[off:].split(b"\0", 1)[0].decode("ascii", "replace")
            off += (len(name.encode()) + 4) & ~3
            cur = {"path": "/" + "/".join(stack + [name]), "props": {}}
            nodes.append(cur)
            stack.append(name)
        elif tag == END:
            if stack:
                stack.pop()
        elif tag == PROP:
            length, nameoff = struct.unpack_from(">II", b, off)
            off += 8
            name = text(strings[nameoff:]) or f"?{nameoff}"
            raw = b[off:off + length]
            off += (length + 3) & ~3
            if cur is not None:
                cur["props"][name] = raw
        elif tag == NOP:
            pass
        elif tag == ENDALL:
            break
        else:
            raise ValueError(f"{path}: bad tag {tag} at {off - 4}")
    return nodes, version, tot


def interesting(nodes):
    keys = (
        "compatible", "model", "device_type", "reg", "ranges", "dma-ranges",
        "#address-cells", "#size-cells", "status", "clock-frequency",
        "interrupt-parent", "interrupts", "interrupt-names", "phandle",
        "stdout-path", "bootargs", "serial-number", "linux,usable-memory",
        "linux,crashkernel-base", "android,soc-id", "qcom,msm-id",
        "qcom,board-id", "qcom,pmic-id", "qcom,dtb-info",
    )
    out = []
    for n in nodes:
        p = n["path"]
        if p.count("/") > 5:
            continue
        hit = {k: fmt(v) for k, v in n["props"].items() if k in keys}
        if hit:
            out.append((p, hit))
    return out


def main():
    if len(sys.argv) < 2:
        print("usage: dtb_dump.py FILE.dtb [...]")
        return
    for arg in sys.argv[1:]:
        path = Path(arg)
        print(f"\n===== {path.name} =====")
        nodes, version, tot = parse(path)
        print(f"version={version} total={tot} nodes={len(nodes)}")
        root = nodes[0]["props"] if nodes else {}
        print("root compatible:", fmt(root.get("compatible", b"")))
        print("root model:", fmt(root.get("model", b"")))
        for p, props in interesting(nodes):
            print(f"\n[{p}]")
            for k, v in props.items():
                print(f"  {k} = {v}")


if __name__ == "__main__":
    main()
