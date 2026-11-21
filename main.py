#!/usr/bin/env python3
"""make.fun entry for news-image-20261120.

Copies the bundled entry.png (a one-page newspaper summarizing the world
news of Friday, 20 November 2026) to /output/entry.png.
Pure standard library, no network. Deterministic: same input, same bytes.
"""
import hashlib
import os
import shutil
import struct

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(HERE, "entry.png")
DST_DIR = "/output"
DST = os.path.join(DST_DIR, "entry.png")


def sha256_of(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def png_dimensions(path):
    """Read width/height from the PNG IHDR header (first 24 bytes)."""
    with open(path, "rb") as f:
        head = f.read(24)
    if head[:8] != b"\x89PNG\r\n\x1a\n" or head[12:16] != b"IHDR":
        raise ValueError("not a PNG file: " + path)
    width, height = struct.unpack(">II", head[16:24])
    return width, height


MAX_BYTES = 1024 * 1024  # bounty limit: entry.png must be at most 1 MiB
EXPECTED_WIDTH = 1024
EXPECTED_HEIGHT = 1024


def main():
    os.makedirs(DST_DIR, exist_ok=True)
    shutil.copyfile(SRC, DST)
    src_hash = sha256_of(SRC)
    dst_hash = sha256_of(DST)
    if src_hash != dst_hash:
        raise SystemExit("copy verification failed: hashes differ")
    size = os.path.getsize(DST)
    width, height = png_dimensions(DST)
    if size > MAX_BYTES:
        raise SystemExit(
            "entry.png too large: {} bytes exceeds 1 MiB limit".format(size)
        )
    if (width, height) != (EXPECTED_WIDTH, EXPECTED_HEIGHT):
        raise SystemExit(
            "entry.png has wrong dimensions: {}x{} px, expected 1024x1024".format(
                width, height
            )
        )
    print(
        "entry.png: {} bytes, {}x{} px, sha256 verified ({})".format(
            size, width, height, dst_hash[:16]
        )
    )


if __name__ == "__main__":
    main()
