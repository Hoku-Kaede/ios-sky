#!/usr/bin/env python3
"""Fetch an arbitrary byte range of a URL using parallel HTTP Range requests."""
import argparse
import concurrent.futures
import os
import sys
import time
import urllib.request

HOST = "https://cdnorg.d.miui.com"
NAME = "sky_in_global_images_OS2.0.205.0.VMWINXM_20261020.0000.00_15.0_in_ed5de7b334.tgz"
URL = HOST + "/OS2.0.205.0.VMWINXM/" + NAME


def fetch_chunk(args):
    start, end, out, attempt = args
    for retry in range(4):
        try:
            req = urllib.request.Request(URL, headers={
                "Range": f"bytes={start}-{end}",
                "User-Agent": "curl/8",
                "Accept-Encoding": "identity",
            })
            with urllib.request.urlopen(req, timeout=60) as r:
                data = r.read()
            if len(data) != end - start + 1:
                raise ValueError(f"short read {len(data)} != {end-start+1}")
            with open(out, "r+b") as f:
                f.seek(start)
                f.write(data)
            return (start, len(data), retry)
        except Exception as e:
            if retry == 3:
                raise
            time.sleep(1 + retry)
    raise RuntimeError("unreachable")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("start", type=int)
    ap.add_argument("end", type=int)
    ap.add_argument("out")
    ap.add_argument("--threads", type=int, default=8)
    a = ap.parse_args()
    length = a.end - a.start + 1
    with open(a.out, "wb") as f:
        f.truncate(a.end + 1)
    chunk = (length + a.threads - 1) // a.threads
    jobs = []
    pos = a.start
    while pos <= a.end:
        e = min(pos + chunk - 1, a.end)
        jobs.append((pos, e, a.out, 0))
        pos = e + 1
    t0 = time.time()
    with concurrent.futures.ThreadPoolExecutor(max_workers=a.threads) as ex:
        for start, n, retry in ex.map(fetch_chunk, jobs):
            print(f"chunk {start:#x} +{n} retry={retry}", flush=True)
    dt = time.time() - t0
    print(f"DONE bytes={length} sec={dt:.1f} speed={length/dt/1e6:.2f} MB/s")


if __name__ == "__main__":
    main()
