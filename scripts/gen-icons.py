#!/usr/bin/env python3
"""Generate the theme's default icons and OpenGraph image into static/.

The mark is a proofreader's insertion mark: a short line of text with a caret
under it. It is generic on purpose (no text, no likeness), and every file is
drawn from the same geometry, so the SVG and the rasters always match:

    static/favicon.svg           scalable icon for current browsers
    static/favicon.ico           16, 32 and 48px, for everything else
    static/apple-touch-icon.png  180px, full bleed (iOS rounds the corners)
    static/og-image.png          1200x630 share preview

A site overrides any of them by shipping a file with the same name.
Standard library only. Usage: gen-icons.py  (or `mise run icons`)
"""
import struct
import zlib
from pathlib import Path

STATIC = Path(__file__).resolve().parent.parent / "static"
BACKGROUND = (20, 20, 20)     # the default palette's dark background
FOREGROUND = (245, 245, 245)
# Geometry in a unit square: stroke width, corner radius, then line segments.
STROKE = 0.085
RADIUS = 0.22
SEGMENTS = [
    ((0.28, 0.36), (0.72, 0.36)),  # the line of text
    ((0.30, 0.74), (0.50, 0.47)),  # caret, left stroke
    ((0.50, 0.47), (0.70, 0.74)),  # caret, right stroke
]
SAMPLES = 4  # supersampling per axis, for smooth edges


def on_mark(x, y):
    """True when the point lies on a stroke (round caps and joins)."""
    for (ax, ay), (bx, by) in SEGMENTS:
        dx, dy = bx - ax, by - ay
        t = max(0.0, min(1.0, ((x - ax) * dx + (y - ay) * dy) / (dx * dx + dy * dy)))
        if (x - ax - t * dx) ** 2 + (y - ay - t * dy) ** 2 <= (STROKE / 2) ** 2:
            return True
    return False


def in_rounded_square(x, y, radius):
    qx, qy = abs(x - 0.5) - (0.5 - radius), abs(y - 0.5) - (0.5 - radius)
    return max(qx, 0.0) ** 2 + max(qy, 0.0) ** 2 <= radius ** 2 if qx > 0 or qy > 0 else True


def png(width, height, pixel):
    """Encode RGBA rows from pixel(x, y) -> (r, g, b, a)."""
    rows = bytearray()
    for y in range(height):
        rows.append(0)
        for x in range(width):
            rows += bytes(pixel(x, y))

    def chunk(kind, data):
        body = kind + data
        return struct.pack(">I", len(data)) + body + struct.pack(">I", zlib.crc32(body))

    header = struct.pack(">IIBBBBB", width, height, 8, 6, 0, 0, 0)
    return (b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", header)
            + chunk(b"IDAT", zlib.compress(bytes(rows), 9)) + chunk(b"IEND", b""))


def mark(size, radius, offset=(0, 0), canvas=None):
    """pixel() for the mark drawn size px square at offset on an optional canvas."""
    width, height = canvas or (size, size)

    def pixel(px, py):
        x0, y0 = px - offset[0], py - offset[1]
        if not (0 <= x0 < size and 0 <= y0 < size):
            return (*BACKGROUND, 255)  # only reached on a larger canvas
        inside = strokes = 0
        for sy in range(SAMPLES):
            for sx in range(SAMPLES):
                x = (x0 + (sx + 0.5) / SAMPLES) / size
                y = (y0 + (sy + 0.5) / SAMPLES) / size
                if canvas or in_rounded_square(x, y, radius):
                    inside += 1
                    strokes += on_mark(x, y)
        if not inside:
            return (0, 0, 0, 0)
        mix = strokes / inside
        colour = tuple(round(b + (f - b) * mix) for b, f in zip(BACKGROUND, FOREGROUND))
        return (*colour, round(255 * inside / SAMPLES ** 2))

    return width, height, pixel


def ico(sizes):
    """An .ico whose entries are PNGs, which every current browser accepts."""
    images = [png(*mark(size, RADIUS)) for size in sizes]
    header = struct.pack("<HHH", 0, 1, len(images))
    offset = len(header) + 16 * len(images)
    entries = b""
    for size, image in zip(sizes, images):
        entries += struct.pack("<BBBBHHII", size, size, 0, 0, 1, 32, len(image), offset)
        offset += len(image)
    return header + entries + b"".join(images)


def svg():
    scale = lambda v: f"{v * 100:g}"
    (l0, l1), (c0, c1), (_, c2) = SEGMENTS
    path = (f"M{scale(l0[0])} {scale(l0[1])}H{scale(l1[0])}"
            f"M{scale(c0[0])} {scale(c0[1])} {scale(c1[0])} {scale(c1[1])} {scale(c2[0])} {scale(c2[1])}")
    return (
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100">'
        f'<rect width="100" height="100" rx="{scale(RADIUS)}" fill="#{bytes(BACKGROUND).hex()}"/>'
        f'<path d="{path}" fill="none" stroke="#{bytes(FOREGROUND).hex()}" stroke-width="{scale(STROKE)}" '
        'stroke-linecap="round" stroke-linejoin="round"/></svg>\n'
    )


def main():
    STATIC.mkdir(exist_ok=True)
    (STATIC / "favicon.svg").write_text(svg())
    (STATIC / "favicon.ico").write_bytes(ico([16, 32, 48]))
    (STATIC / "apple-touch-icon.png").write_bytes(png(*mark(180, 0.0, canvas=(180, 180))))
    # The mark, centred on a 1200x630 card.
    (STATIC / "og-image.png").write_bytes(png(*mark(340, 0.0, offset=(430, 145), canvas=(1200, 630))))
    for name in ("favicon.svg", "favicon.ico", "apple-touch-icon.png", "og-image.png"):
        print(f"static/{name}: {(STATIC / name).stat().st_size} bytes")


if __name__ == "__main__":
    main()
