#!/usr/bin/env python3
"""Deterministic news-image generator for SPEC.md.

Renders a 1024x1024 RGB PNG to /output/entry.png (falls back to
./out/entry.png if /output is not writable).  Stdlib only.
"""

import os
import struct
import zlib

from typography import draw_text, measure_text
from icons import draw_icon

# ---------------------------------------------------------------------------
# Palette
# ---------------------------------------------------------------------------
BG = (11, 11, 15)
CARD = (20, 20, 27)
LINE = (42, 42, 53)
IVORY = (242, 239, 230)
MUTED = (139, 139, 152)
RED = (255, 61, 0)
AMBER = (255, 212, 0)
TEAL = (0, 229, 160)

W = 1024
H = 1024


def fit_size(text, box_w, size, style='display', ls=0):
    s = size
    while s > 10 and measure_text(text, s, style, letter_spacing=ls) > box_w * 0.99:
        s -= 2
    return s


# ---------------------------------------------------------------------------
# Story facts (kept from SPEC.md)
# ---------------------------------------------------------------------------
STORIES = [
    # (number, category, accent, icon_name, headline, detail)
    ("02", "MARKETS", AMBER, "tanker",
     "US STRIKES IRANIAN ISLE", "Tankers ablaze in the Strait of Hormuz"),
    ("03", "LAW", IVORY, "scales",
     "ICJ ROHINGYA RULING", "Genocide judgment against Myanmar"),
    ("04", "WORLD", RED, "strike",
     "RUSSIAN HITS ON ODESA", "Historic centre struck, four dead"),
    ("05", "TECH", TEAL, "chip",
     "NVIDIA HALTS H200", "600k chips stalled in Hong Kong"),
    ("06", "CLIMATE", TEAL, "cyclone",
     "CYCLONE AKVAN HITS", "Odisha red zone braces for surge"),
    ("07", "GAMING", AMBER, "gamepad",
     "GTA 6 IS OUT", "Launches overnight after 13 years"),
    ("08", "TECH", RED, "cyber",
     "JAVA FLAW ALARM", "NSA locks Fort Meade after patch"),
]


# ---------------------------------------------------------------------------
# Canvas (RGB pixel buffer)
# ---------------------------------------------------------------------------
class Canvas:
    def __init__(self, w, h):
        self.w = w
        self.h = h
        self.buf = bytearray(w * h * 3)

    def rect(self, x, y, w, h, color):
        x, y, w, h = int(x), int(y), int(w), int(h)
        if x < 0:
            w += x
            x = 0
        if y < 0:
            h += y
            y = 0
        if x + w > self.w:
            w = self.w - x
        if y + h > self.h:
            h = self.h - y
        if w <= 0 or h <= 0:
            return
        for yy in range(h):
            row = (y + yy) * self.w
            for xx in range(w):
                i = (row + x + xx) * 3
                self.buf[i] = color[0]
                self.buf[i + 1] = color[1]
                self.buf[i + 2] = color[2]


def _body(c, x, y, t, s, col, ls=0):
    draw_text(c, x, y, str(t).upper(), s, col, "body", letter_spacing=ls)


def _blit_centered(c, text, size_px, color, style, cx, y):
    w = measure_text(text, size_px, style)
    draw_text(c, cx - w / 2.0, y, text, size_px, color, style)


def _blit_right(c, text, size_px, color, style, rx, y, ls=0):
    w = measure_text(text, size_px, style, letter_spacing=ls)
    draw_text(c, rx - w, y, text, size_px, color, style, letter_spacing=ls)


# ---------------------------------------------------------------------------
# PNG writer
# ---------------------------------------------------------------------------
def write_png(path, canvas):
    raw = bytearray()
    for y in range(canvas.h):
        raw.append(0)  # filter byte 0 (None)
        row_start = y * canvas.w * 3
        raw += canvas.buf[row_start:row_start + canvas.w * 3]

    def chunk(tag, data):
        c = struct.pack(">I", len(data)) + tag + data
        c += struct.pack(">I", zlib.crc32(tag + data) & 0xFFFFFFFF)
        return c

    sig = b"\x89PNG\r\n\x1a\n"
    ihdr = struct.pack(">IIBBBBB", canvas.w, canvas.h, 8, 2, 0, 0, 0)
    idat = zlib.compress(bytes(raw), 9)

    with open(path, "wb") as f:
        f.write(sig)
        f.write(chunk(b"IHDR", ihdr))
        f.write(chunk(b"IDAT", idat))
        f.write(chunk(b"IEND", b""))


# ---------------------------------------------------------------------------
# Layout / rendering
# ---------------------------------------------------------------------------
def main():
    c = Canvas(W, H)

    # -- texture: 1px lines every 64px ------------------------------------
    for x in range(0, W, 64):
        c.rect(x, 0, 1, H, (18, 18, 24))
    for y in range(0, H, 64):
        c.rect(0, y, W, 1, (18, 18, 24))

    # -- crop marks (LINE, 24px inset) -------------------------------------
    cm = 24
    L = 16
    for cx, cy, dx, dy in [
        (cm, cm, 1, 1), (cm, cm, 1, 1),  # top-left
    ]:
        pass
    # top-left
    c.rect(cm, cm - 1, L, 1, LINE)
    c.rect(cm - 1, cm, 1, L, LINE)
    # top-right
    c.rect(W - cm - L, cm - 1, L, 1, LINE)
    c.rect(W - cm, cm, 1, L, LINE)
    # bottom-left
    c.rect(cm, H - cm, L, 1, LINE)
    c.rect(cm - 1, H - cm - L, 1, L, LINE)
    # bottom-right
    c.rect(W - cm - L, H - cm, L, 1, LINE)
    c.rect(W - cm, H - cm - L, 1, L, LINE)

    # -- masthead -----------------------------------------------------------
    draw_icon(c, "masthead", 48, 40, 34, [RED, IVORY])
    draw_text(c, 96, 84 - 46, "WORLD NEWS", 46, IVORY, "display", letter_spacing=2)
    _blit_right(c, "THU 19 NOV 2026", 15, MUTED, "body", 976, 72 - 15, ls=2)
    _blit_right(c, "ISSUE 08 / 2026", 11, RED, "body", 976, 92 - 11, ls=2)
    c.rect(48, 108, 928, 6, RED)

    # -- strap --------------------------------------------------------------
    draw_text(c, 48, 138 - 12, "THE WORLD IN EIGHT STORIES", 12, AMBER, "body", letter_spacing=3)
    _blit_right(c, "GLOBAL BRIEF / 01-08", 11, MUTED, "body", 976, 138 - 11)

    # -- hero ---------------------------------------------------------------
    draw_text(c, 48, 146, "01", 30, RED, "display")
    c.rect(48, 176, 124, 24, RED)
    ts_w = measure_text("TOP STORY", 11, "body")
    draw_text(c, 48 + (124 - ts_w) // 2, 181, "TOP STORY", 11, BG, "body")
    hero_lines = ["TRUMP-XI-PUTIN", "SUMMIT OPENS", "IN SHENZHEN"]
    hero_sizes = []; hero_lss = []
    for line in hero_lines:
        s = fit_size(line, 596, 52, 'display', 4)
        ls = max(4, int(0.03 * s))
        s = fit_size(line, 596, 52, 'display', ls)
        ls = max(4, int(0.03 * s))
        hero_sizes.append(s); hero_lss.append(ls)
    hero_baselines = [258 + i * (s + 8) for i, s in enumerate(hero_sizes)]
    for line, bl, s, ls in zip(hero_lines, hero_baselines, hero_sizes, hero_lss):
        draw_text(c, 48, bl - s, line, s, IVORY, "display", letter_spacing=ls)
    _body(c, 48, 384, 'FIRST-EVER THREE-WAY SUMMIT CAPS ASIA TRIP.', 13, MUTED, ls=1)

    # right panel
    c.rect(700, 150, 276, 240, RED)
    draw_icon(c, "summit", 726, 180, 224, [BG, IVORY, AMBER])
    draw_text(c, 724, 380 - 11, "APEC 2026", 11, IVORY, "body")

    # hero hairline
    c.rect(48, 408, 928, 2, LINE)

    # -- grid of cards 02-08 ------------------------------------------------
    colw = 456
    colh = 120
    gap = 16
    gx0 = 48
    gy0 = 428
    card_positions = [
        # (x, y) for cards 02..08
        (gx0, gy0), (gx0 + colw + gap, gy0),          # row1: 02, 03
        (gx0, gy0 + colh + gap), (gx0 + colw + gap, gy0 + colh + gap),  # row2: 04, 05
        (gx0, gy0 + 2 * (colh + gap)), (gx0 + colw + gap, gy0 + 2 * (colh + gap)),  # row3: 06, 07
        (gx0, gy0 + 3 * (colh + gap)),  # row4 col1: 08
    ]
    for idx in range(len(card_positions)):
        num, cat, accent, icon, headline, detail = STORIES[idx]
        x, y = card_positions[idx]
        # card body + border
        c.rect(x, y, colw, colh, CARD)
        c.rect(x, y, colw, 2, LINE)
        c.rect(x, y + colh - 2, colw, 2, LINE)
        c.rect(x, y, 2, colh, LINE)
        c.rect(x + colw - 2, y, 2, colh, LINE)
        # left accent bar (6px)
        c.rect(x, y, 6, colh, accent)
        # number
        draw_text(c, x + 18, y + 42 - 26, num, 26, accent, "display")
        # icon 50 at x+64,y+34
        draw_icon(c, icon, x + 64, y + 34, 50, [accent, IVORY, CARD])
        # chip accent rect 90x18 at x+134,y+22, BG 10px category
        c.rect(x + 134, y + 22, 90, 18, accent)
        cat_w = measure_text(cat, 10, "body", letter_spacing=1)
        draw_text(c, x + 134 + (90 - cat_w) // 2, y + 26, cat, 10, BG, "body", letter_spacing=1)
        # headline display fitted, top-aligned at y+43 x+134
        hs = fit_size(headline, 308, 21, 'display', 2)
        draw_text(c, x + 134, y + 43, headline, hs, IVORY, "display", letter_spacing=2)
        # detail body fitted, top-aligned at y+43+hs+10
        ds = fit_size(detail.upper(), 308, 12, 'body', 0)
        draw_text(c, x + 134, y + 43 + hs + 10, detail.upper(), ds, MUTED, "body")

    # -- special 8th cell (amber accent) ------------------------------------
    x = gx0 + colw + gap
    y = gy0 + 3 * (colh + gap)
    c.rect(x, y, colw, colh, AMBER)
    c.rect(x, y, colw, 2, (0, 0, 0))
    c.rect(x, y + colh - 2, colw, 2, (0, 0, 0))
    c.rect(x, y, 2, colh, (0, 0, 0))
    c.rect(x + colw - 2, y, 2, colh, (0, 0, 0))
    draw_text(c, x + 22, y + 92 - 84, "8", 84, BG, "display")
    draw_text(c, x + 120, y + 54 - 12, "STORIES / 24H", 12, BG, "body")
    draw_text(c, x + 120, y + 78 - 10, "REPORT 19.11.26", 10, BG, "body")

    # -- footer --------------------------------------------------------------
    c.rect(48, 958, 928, 2, LINE)
    draw_text(c, 48, 992 - 10, "SOURCES: REUTERS, AP, BLOOMBERG, ICJ", 10, MUTED, "body")
    _blit_right(c, "MAKE.FUN / NEWS-IMAGE", 10, AMBER, "body", 976, 992 - 10)

    # Write output with fallback path.
    path = "/output/entry.png"
    if not _writable("/output"):
        os.makedirs("./out", exist_ok=True)
        path = "./out/entry.png"
    write_png(path, c)
    print("rendered", os.path.getsize(path))


def _writable(d):
    try:
        with open(os.path.join(d, ".wtest"), "w"):
            pass
        os.remove(os.path.join(d, ".wtest"))
        return True
    except Exception:
        return False


if __name__ == "__main__":
    main()