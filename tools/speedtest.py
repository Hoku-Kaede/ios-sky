#!/usr/bin/env python3
"""Measure HTTP range-download speed for Xiaomi mirrors in parallel."""
import concurrent.futures
import time
import urllib.request

NAME = "sky_in_global_images_OS2.0.205.0.VMWINXM_20261020.0000.00_15.0_in_ed5de7b334.tgz"
PATH = "/OS2.0.205.0.VMWINXM/" + NAME
HOSTS = [
    "https://bigota.d.miui.com",
    "https://bn.d.miui.com",
    "https://cdnorg.d.miui.com",
    "https://hugeota.d.miui.com",
    "https://cdn-ota.azureedge.net",
]
N = 512 * 1024


def test(host):
    t0 = time.time()
    try:
        req = urllib.request.Request(host + PATH, headers={"Range": f"bytes=0-{N-1}", "User-Agent": "curl/8"})
        with urllib.request.urlopen(req, timeout=20) as r:
            data = r.read(N)
            dt = time.time() - t0
            return f"{host:32s} status={r.status} bytes={len(data)} sec={dt:.1f} speed={len(data)/dt/1e6:.2f} MB/s"
    except Exception as e:
        return f"{host:32s} FAIL {type(e).__name__}: {e}"


with concurrent.futures.ThreadPoolExecutor(max_workers=5) as ex:
    for line in ex.map(test, HOSTS):
        print(line)
