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
# Palette (light cream newspaper)
# ---------------------------------------------------------------------------
PAPER = (0xF6, 0xF1, 0xE7)
INK = (0x14, 0x12, 0x10)
RED = (0xC8, 0x10, 0x2E)
BLUE = (0x1B, 0x4B, 0x8F)
YELLOW = (0xF5, 0xC4, 0x00)
# muted greys for secondary text (light paper needs dark-ish grey)
GREY = (0x6B, 0x63, 0x58)
GREY_LIGHT = (0x8C, 0x84, 0x78)
MUTED = GREY
RULE = (0x3A, 0x34, 0x2E)

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
    ("02", "MARKETS", RED, "tanker",
     "US STRIKES IRANIAN ISLE", "Tankers ablaze in the Strait of Hormuz"),
    ("03", "LAW", BLUE, "scales",
     "ICJ ROHINGYA RULING", "Genocide judgment against Myanmar"),
    ("04", "WORLD", RED, "strike",
     "RUSSIAN HITS ON ODESA", "Historic centre struck, four dead"),
    ("05", "TECH", BLUE, "chip",
     "NVIDIA HALTS H200", "600k chips stalled in Hong Kong"),
    ("06", "CLIMATE", RED, "cyclone",
     "CYCLONE AKVAN HITS", "Odisha red zone braces for surge"),
    ("07", "GAMING", BLUE, "gamepad",
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


def _blit_centered_ls(c, text, size_px, color, style, cx, y, ls=0):
    w = measure_text(text, size_px, style, letter_spacing=ls)
    draw_text(c, cx - w / 2.0, y, text, size_px, color, style, letter_spacing=ls)


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
    c.rect(0, 0, W, H, PAPER)

    M = 48
    CW = W - 2 * M          # content width

    # -- masthead -------------------------------------------------------------
    _blit_centered_ls(c, "THE WORLD IN ONE DAY", 20, RED, "body", W / 2, 24, ls=3)
    # thin double rule above
    c.rect(M, 50, CW, 1, RULE)
    c.rect(M, 54, CW, 1, RULE)
    # huge centred auto-fit display headline
    hsize = fit_size("THURSDAY 19 NOVEMBER 2026", CW - 40, 74, 'display', 2)
    hs_ls = 2
    hsize = fit_size("THURSDAY 19 NOVEMBER 2026", CW - 40, 74, 'display', hs_ls)
    _blit_centered_ls(c, "THURSDAY 19 NOVEMBER 2026", hsize, INK, "display", W / 2, 64, ls=hs_ls)
    # thin double rule below
    c.rect(M, 64 + hsize + 20, CW, 1, RULE)
    c.rect(M, 64 + hsize + 24, CW, 1, RULE)

    # -- deck line ------------------------------------------------------------
    deck_y = 64 + hsize + 34
    deck = "TRUMP-XI-PUTIN SUMMIT OPENS  ·  US STRIKES IRANIAN ISLE  ·  ICJ ROHINGYA RULING"
    _blit_centered(c, deck, 14, INK, "body", W / 2, deck_y)
    c.rect(M, deck_y + 34, CW, 2, RULE)

    # -- region ribbon --------------------------------------------------------
    rib_y = deck_y + 42
    regions = [
        ("CHINA", "SUMMIT"),
        ("GULF", "STRIKE"),
        ("THE HAGUE", "ICJ"),
        ("ODESA", "WAR"),
        ("HONG KONG", "CHIPS"),
        ("ODISHA", "CYCLONE"),
        ("WORLDWIDE", "GTA 6"),
    ]
    total = 7
    c.rect(M, rib_y, CW, 30, INK)
    step = CW / float(total)
    for i, (name, count) in enumerate(regions):
        cx = M + i * step + step / 2
        _blit_centered(c, name + " " + count, 11, PAPER, "body", cx, rib_y + 16)

    # -- stats band -----------------------------------------------------------
    stats_y = rib_y + 40
    stats = [
        ("81.3BN", "IPO RAISED"),
        ("15.9M", "GTA 6 PRE-ORDERS"),
        ("200,000", "EVACUATED"),
        ("730,000", "ROHINGYA"),
        ("16BN", "VOYAGER 1 MILES"),
    ]
    n = len(stats)
    c.rect(M, stats_y, CW, 58, (0xEF, 0xE9, 0xDB))
    c.rect(M, stats_y, CW, 1, RULE)
    c.rect(M, stats_y + 57, CW, 1, RULE)
    step = CW / float(n)
    for i, (num, cap) in enumerate(stats):
        cx = M + i * step + step / 2
        _blit_centered(c, num, 24, RED, "display", cx, stats_y + 6)
        _blit_centered(c, cap, 9, GREY, "body", cx, stats_y + 40)

    # -- placeholder story grid (kept from old layout, temporary) -------------
    gy0 = stats_y + 76
    colw = 456
    colh = 118
    gap = 16
    gx0 = M
    card_positions = [
        (gx0, gy0), (gx0 + colw + gap, gy0),
        (gx0, gy0 + colh + gap), (gx0 + colw + gap, gy0 + colh + gap),
        (gx0, gy0 + 2 * (colh + gap)), (gx0 + colw + gap, gy0 + 2 * (colh + gap)),
        (gx0, gy0 + 3 * (colh + gap)),
    ]
    for idx in range(len(card_positions)):
        num, cat, accent, icon, headline, detail = STORIES[idx]
        x, y = card_positions[idx]
        c.rect(x, y, colw, colh, (0xEE, 0xE8, 0xDA))
        c.rect(x, y, colw, 1, RULE)
        c.rect(x, y + colh - 1, colw, 1, RULE)
        c.rect(x, y, 1, colh, RULE)
        c.rect(x + colw - 1, y, 1, colh, RULE)
        c.rect(x, y, 6, colh, accent)
        draw_text(c, x + 16, y + 30 - 26, num, 26, accent, "display")
        draw_icon(c, icon, x + 62, y + 34, 50, [accent, INK, PAPER])
        c.rect(x + 130, y + 22, 90, 16, accent)
        cat_w = measure_text(cat, 9, "body", letter_spacing=1)
        draw_text(c, x + 130 + (90 - cat_w) // 2, y + 25, cat, 9, PAPER, "body", letter_spacing=1)
        hs = fit_size(headline, 308, 20, 'display', 2)
        draw_text(c, x + 130, y + 42, headline, hs, INK, "display", letter_spacing=2)
        ds = fit_size(detail.upper(), 308, 11, 'body', 0)
        draw_text(c, x + 130, y + 42 + hs + 8, detail.upper(), ds, GREY, "body")

    # -- hero block ------------------------------------------------------------
    draw_text(c, 48, 146, "01", 26, RED, "display")
    c.rect(48, 176, 124, 24, RED)
    _body(c, 48, 181, "TOP STORY", 9, PAPER, ls=1)
    hero_lines = ["TRUMP-XI-PUTIN", "SUMMIT OPENS", "IN SHENZHEN"]
    for i, line in enumerate(hero_lines):
        s = fit_size(line, 596, 52, 'display', 4)
        ls = max(4, int(0.03 * s))
        s = fit_size(line, 596, 52, 'display', ls)
        ls = max(4, int(0.03 * s))
        draw_text(c, 48, (258 + i * (s + 8)) - s, line, s, INK, "display", letter_spacing=ls)
    _body(c, 48, 384, "FIRST-EVER THREE-WAY SUMMIT CAPS ASIA TRIP.", 13, MUTED, ls=1)

    # -- footer ----------------------------------------------------------------
    fy = 992
    c.rect(M, 972, CW, 2, RULE)
    draw_text(c, M, fy - 10, "SOURCES: REUTERS, AP, BLOOMBERG, ICJ", 10, GREY, "body")
    _blit_right(c, "MAKE.FUN / NEWS-IMAGE", 10, RED, "body", W - M, fy - 10)

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