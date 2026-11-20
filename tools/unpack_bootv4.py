#!/usr/bin/env python3
"""Unpack Android boot image v4 and vendor_boot v4 (sky / Xiaomi HyperOS).

The upstream tools/unpack_bootv2.py only handles header versions 0-3. Sky's
boot.img is v4 (kernel + generic ramdisk) and its board DTB lives only in
vendor_boot.img. This tool writes raw segments to an output directory and
prints the parsed header fields.

Usage:
  unpack_bootv4.py boot.img outdir
  unpack_bootv4.py vendor_boot.img outdir
"""
import struct
import sys
from pathlib import Path

BOOT_MAGIC = b"ANDROID!"
VENDOR_MAGIC = b"VNDRBOOT"


def align(v, page):
    return (v + page - 1) & ~(page - 1)


def unpack_boot(data, out):
    magic, *f = struct.unpack_from("<8s10I", data, 0)
    assert magic == BOOT_MAGIC, magic
    kernel_sz, ramdisk_sz, hdr_sz, ver = f[0], f[1], f[3], f[8]
    page = f[9] or 4096
    print(f"boot: version={ver} page=0x{page:x} header=0x{hdr_sz:x}")
    print(f"  kernel=0x{kernel_sz:x} ramdisk=0x{ramdisk_sz:x}")
    off = align(hdr_sz, page)
    for name, size in (("kernel", kernel_sz), ("ramdisk", ramdisk_sz)):
        if size:
            (out / f"boot_{name}").write_bytes(data[off:off + size])
            print(f"  wrote boot_{name} @0x{off:x} ({size} bytes)")
            off = align(off + size, page)


def unpack_vendor_boot(data, out):
    magic, ver, page, kernel_addr, ramdisk_addr, vendor_ramdisk_sz = struct.unpack_from(
        "<8sIIIII", data, 0
    )
    assert magic == VENDOR_MAGIC, magic
    cmdline = data[28:28 + 2048].split(b"\0", 1)[0]
    print(f"vendor_boot: version={ver} page=0x{page:x} header=0x{0x1000:x}")
    print(f"  kernel_addr=0x{kernel_addr:x} ramdisk_addr=0x{ramdisk_addr:x}")
    print(f"  vendor_ramdisk=0x{vendor_ramdisk_sz:x}")
    print(f"  cmdline={cmdline.decode('ascii', 'replace')}")
    # v4 vendor header: 2048 cmdline + 16 u32/u64 fields start at 0x820.
    # The DTB table starts after the vendor ramdisk, aligned to page.
    ramdisk_off = align(0x1000, page)
    dtb_off = align(ramdisk_off + vendor_ramdisk_sz, page)
    dtbs = []
    off = dtb_off
    while data[off:off + 4] == b"\xd0\x0d\xfe\xed":
        size = struct.unpack_from(">I", data, off + 4)[0]
        dtbs.append((off, size))
        off = align(off + size, page)
    print(f"  dtb_count={len(dtbs)} first=0x{dtb_off:x}")
    if vendor_ramdisk_sz:
        (out / "vendor_ramdisk").write_bytes(data[ramdisk_off:ramdisk_off + vendor_ramdisk_sz])
        print(f"  wrote vendor_ramdisk @0x{ramdisk_off:x}")
    for i, (o, s) in enumerate(dtbs):
        (out / f"board_{i:02d}.dtb").write_bytes(data[o:o + s])
        print(f"  wrote board_{i:02d}.dtb @0x{o:x} ({s} bytes)")


def main():
    src = Path(sys.argv[1])
    out = Path(sys.argv[2])
    out.mkdir(parents=True, exist_ok=True)
    data = src.read_bytes()
    if data[:8] == BOOT_MAGIC:
        unpack_boot(data, out)
    elif data[:8] == VENDOR_MAGIC:
        unpack_vendor_boot(data, out)
    else:
        raise SystemExit(f"unknown image magic: {data[:8]!r}")


if __name__ == "__main__":
    main()
