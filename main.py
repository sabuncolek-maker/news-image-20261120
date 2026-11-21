#!/usr/bin/env python3
"""Entry runner for make.fun news-image-20261120.

Copies the built front-page image to /output/entry.png, verifies the
copy byte-for-byte against the source with SHA-256, and prints a short
summary (size in bytes, dimensions, SHA-256 prefix).
"""
import hashlib
import os
import shutil
import sys
from PIL import Image

SRC = os.path.join(os.path.dirname(os.path.abspath(__file__)), "entry.png")
DST = "/output/entry.png"


def sha256_of(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def main():
    if not os.path.isfile(SRC):
        print(f"error: source image not found: {SRC}", file=sys.stderr)
        return 1
    os.makedirs(os.path.dirname(DST), exist_ok=True)
    shutil.copyfile(SRC, DST)
    src_hash = sha256_of(SRC)
    dst_hash = sha256_of(DST)
    if src_hash != dst_hash:
        print("error: sha256 mismatch after copy", file=sys.stderr)
        print(f"  source: {src_hash}", file=sys.stderr)
        print(f"  copy:   {dst_hash}", file=sys.stderr)
        return 1
    size = os.path.getsize(DST)
    with Image.open(DST) as im:
        width, height = im.size
    if size > 1024 * 1024:
        print(f"error: entry.png is {size} bytes, over the 1 MiB limit",
              file=sys.stderr)
        return 1
    if (width, height) != (1024, 1024):
        print(f"error: entry.png is {width}x{height}, expected 1024x1024",
              file=sys.stderr)
        return 1
    print(f"copied {SRC} -> {DST}")
    print(f"bytes: {size}")
    print(f"dimensions: {width}x{height}")
    print(f"sha256: {src_hash[:16]}...")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
