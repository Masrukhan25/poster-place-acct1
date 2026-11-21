#!/usr/bin/env python3
"""KALDRIS — The Harbor Inside the Glacier.

Entry program for make.fun "The Poster for a Place That Isn't There".
Copies the travel poster (entry.png, 1024x1024, at most 1,048,576 bytes)
from this repository to $MAKEFUN_OUTPUT_DIR/entry.png.

Standard library only.
"""

import os
import shutil
import struct
import sys
from pathlib import Path

MAX_BYTES = 1_048_576
EXPECTED_WIDTH = 1024
EXPECTED_HEIGHT = 1024


def read_png_dimensions(data: bytes) -> tuple[int, int]:
    """Return (width, height) from a PNG byte string (IHDR chunk)."""
    if len(data) < 24 or data[:8] != b"\x89PNG\r\n\x1a\n":
        raise ValueError("not a PNG file")
    width, height = struct.unpack(">II", data[16:24])
    return width, height


def read_jpeg_dimensions(data: bytes) -> tuple[int, int]:
    """Return (width, height) from a JPEG byte string (first SOF segment)."""
    if len(data) < 4 or data[0:2] != b"\xff\xd8":
        raise ValueError("not a JPEG file")
    pos = 2
    while pos + 9 < len(data):
        if data[pos] != 0xFF:
            pos += 1
            continue
        marker = data[pos + 1]
        if marker in (0xC0, 0xC1, 0xC2, 0xC3, 0xC5, 0xC6, 0xC7,
                      0xC9, 0xCA, 0xCB, 0xCD, 0xCE, 0xCF):
            height, width = struct.unpack(">HH", data[pos + 5:pos + 9])
            return width, height
        if marker in (0xD8, 0xD9) or 0xD0 <= marker <= 0xD7:
            pos += 2
            continue
        length = struct.unpack(">H", data[pos + 2:pos + 4])[0]
        pos += 2 + length
    raise ValueError("no JPEG SOF segment found")


def read_dimensions(data: bytes) -> tuple[int, int]:
    """Detect PNG or JPEG content and return (width, height)."""
    if data[:8] == b"\x89PNG\r\n\x1a\n":
        return read_png_dimensions(data)
    if data[:2] == b"\xff\xd8":
        return read_jpeg_dimensions(data)
    raise ValueError("entry.png is neither PNG nor JPEG content")


def validate(data: bytes) -> tuple[int, int]:
    """Validate size and dimensions; return (width, height)."""
    if len(data) > MAX_BYTES:
        raise ValueError(f"entry.png is {len(data)} bytes, over {MAX_BYTES}")
    width, height = read_dimensions(data)
    if (width, height) != (EXPECTED_WIDTH, EXPECTED_HEIGHT):
        raise ValueError(f"entry.png is {width}x{height}, "
                         f"expected {EXPECTED_WIDTH}x{EXPECTED_HEIGHT}")
    return width, height


def main() -> int:
    repo_dir = Path(__file__).resolve().parent
    src = repo_dir / "entry.png"
    if not src.is_file():
        print(f"error: {src} not found", file=sys.stderr)
        return 1

    data = src.read_bytes()
    try:
        width, height = validate(data)
    except ValueError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

    out_dir = Path(os.environ.get("MAKEFUN_OUTPUT_DIR", "/output"))
    out_dir.mkdir(parents=True, exist_ok=True)
    dest = out_dir / "entry.png"
    shutil.copyfile(src, dest)

    # Round-trip check: the written file must be byte-identical to the repo file
    # and must still parse as the same 1024x1024 image.
    written = dest.read_bytes()
    if written != data:
        print("error: round-trip mismatch for entry.png", file=sys.stderr)
        return 1
    out_width, out_height = read_dimensions(written)
    if (out_width, out_height) != (EXPECTED_WIDTH, EXPECTED_HEIGHT):
        print(f"error: written entry.png is {out_width}x{out_height}",
              file=sys.stderr)
        return 1

    print(f"wrote entry.png ({len(data)} bytes, "
          f"{width}x{height}, {len(written)} bytes verified)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
