#!/usr/bin/env python3
"""make.fun entry for news-image-20261120.

Copies the bundled entry.png (a one-page newspaper summarizing the world
news of Friday, 20 November 2026) to /output/entry.png.
Pure standard library, no network. Deterministic: same input, same bytes.
"""
import os
import shutil

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(HERE, "entry.png")
DST_DIR = "/output"
DST = os.path.join(DST_DIR, "entry.png")


def main():
    os.makedirs(DST_DIR, exist_ok=True)
    shutil.copyfile(SRC, DST)
    print("wrote", DST)


if __name__ == "__main__":
    main()
