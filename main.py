#!/usr/bin/env python3
"""Deterministic news-image generator for SPEC.md.

Renders a 1024x1024 RGB PNG to /output/entry.png (falls back to
./out/entry.png if /output is not writable).  Stdlib only.
"""

import os
import struct
import zlib

# ---------------------------------------------------------------------------
# Palette
# ---------------------------------------------------------------------------
PAPER = (0x0A, 0x0A, 0x0C)   # near-black
BANNER = (0xC9, 0xA2, 0x27)  # gold
HEADLINE = (0xE8, 0xE6, 0xE3)  # off-white
FACT = (0x9A, 0xA0, 0xA6)   # grey
NEWSRED = (0x7A, 0x1F, 0x2B)
NAVY = (0x2B, 0x4C, 0x6F)

W = 1024
H = 1024


# ---------------------------------------------------------------------------
# Scalable 5x7 pixel font (ASCII 32..126), bit masks.
# Each row is one int; bit 4..0 (bit 4 = leftmost column) is a 5px row strip.
# Row 0 is the top of the glyph.
# ---------------------------------------------------------------------------
def _g(*rows):
    return list(rows)


FONT = {
    ' ': _g(0b00000, 0b00000, 0b00000, 0b00000, 0b00000, 0b00000, 0b00000),
    '!': _g(0b00100, 0b00100, 0b00100, 0b00100, 0b00100, 0b00000, 0b00100),
    '"': _g(0b01010, 0b01010, 0b01010, 0b00000, 0b00000, 0b00000, 0b00000),
    '#': _g(0b01010, 0b11111, 0b01010, 0b01010, 0b11111, 0b01010, 0b00000),
    '$': _g(0b00100, 0b01110, 0b10101, 0b01110, 0b10101, 0b01110, 0b00100),
    '%': _g(0b11001, 0b11010, 0b00100, 0b01000, 0b01011, 0b10011, 0b00000),
    '&': _g(0b01100, 0b10010, 0b10100, 0b01000, 0b10101, 0b10010, 0b01101),
    "'": _g(0b00100, 0b00100, 0b00100, 0b00000, 0b00000, 0b00000, 0b00000),
    '(': _g(0b00100, 0b01000, 0b01000, 0b01000, 0b01000, 0b01000, 0b00100),
    ')': _g(0b00100, 0b00010, 0b00010, 0b00010, 0b00010, 0b00010, 0b00100),
    '*': _g(0b00000, 0b01010, 0b00100, 0b01110, 0b00100, 0b01010, 0b00000),
    '+': _g(0b00000, 0b00100, 0b00100, 0b11111, 0b00100, 0b00100, 0b00000),
    ',': _g(0b00000, 0b00000, 0b00000, 0b00000, 0b00100, 0b00100, 0b01000),
    '-': _g(0b00000, 0b00000, 0b00000, 0b11111, 0b00000, 0b00000, 0b00000),
    '.': _g(0b00000, 0b00000, 0b00000, 0b00000, 0b00000, 0b00100, 0b00000),
    '/': _g(0b00001, 0b00010, 0b00100, 0b00100, 0b01000, 0b10000, 0b00000),
    '0': _g(0b01110, 0b10001, 0b10011, 0b10101, 0b11001, 0b10001, 0b01110),
    '1': _g(0b00100, 0b01100, 0b00100, 0b00100, 0b00100, 0b00100, 0b01110),
    '2': _g(0b01110, 0b10001, 0b00001, 0b00010, 0b00100, 0b01000, 0b11111),
    '3': _g(0b11111, 0b00010, 0b00100, 0b00010, 0b00001, 0b10001, 0b01110),
    '4': _g(0b00010, 0b00110, 0b01010, 0b10010, 0b11111, 0b00010, 0b00010),
    '5': _g(0b11111, 0b10000, 0b11110, 0b00001, 0b00001, 0b10001, 0b01110),
    '6': _g(0b00110, 0b01000, 0b10000, 0b11110, 0b10001, 0b10001, 0b01110),
    '7': _g(0b11111, 0b00001, 0b00010, 0b00100, 0b01000, 0b01000, 0b01000),
    '8': _g(0b01110, 0b10001, 0b10001, 0b01110, 0b10001, 0b10001, 0b01110),
    '9': _g(0b01110, 0b10001, 0b10001, 0b01111, 0b00001, 0b00010, 0b01100),
    ':': _g(0b00000, 0b00100, 0b00000, 0b00000, 0b00000, 0b00100, 0b00000),
    ';': _g(0b00000, 0b00100, 0b00000, 0b00000, 0b00100, 0b00100, 0b01000),
    '<': _g(0b00010, 0b00100, 0b01000, 0b10000, 0b01000, 0b00100, 0b00010),
    '=': _g(0b00000, 0b00000, 0b11111, 0b00000, 0b11111, 0b00000, 0b00000),
    '>': _g(0b01000, 0b00100, 0b00010, 0b00001, 0b00010, 0b00100, 0b01000),
    '?': _g(0b01110, 0b10001, 0b00001, 0b00010, 0b00100, 0b00000, 0b00100),
    '@': _g(0b01110, 0b10001, 0b10011, 0b10101, 0b10111, 0b10000, 0b01110),
    'A': _g(0b01110, 0b10001, 0b10001, 0b11111, 0b10001, 0b10001, 0b10001),
    'B': _g(0b11110, 0b10001, 0b10001, 0b11110, 0b10001, 0b10001, 0b11110),
    'C': _g(0b01110, 0b10001, 0b10000, 0b10000, 0b10000, 0b10001, 0b01110),
    'D': _g(0b11110, 0b10001, 0b10001, 0b10001, 0b10001, 0b10001, 0b11110),
    'E': _g(0b11111, 0b10000, 0b10000, 0b11110, 0b10000, 0b10000, 0b11111),
    'F': _g(0b11111, 0b10000, 0b10000, 0b11110, 0b10000, 0b10000, 0b10000),
    'G': _g(0b01110, 0b10001, 0b10000, 0b10111, 0b10001, 0b10001, 0b01111),
    'H': _g(0b10001, 0b10001, 0b10001, 0b11111, 0b10001, 0b10001, 0b10001),
    'I': _g(0b01110, 0b00100, 0b00100, 0b00100, 0b00100, 0b00100, 0b01110),
    'J': _g(0b00111, 0b00010, 0b00010, 0b00010, 0b00010, 0b10010, 0b01100),
    'K': _g(0b10001, 0b10010, 0b10100, 0b11000, 0b10100, 0b10010, 0b10001),
    'L': _g(0b10000, 0b10000, 0b10000, 0b10000, 0b10000, 0b10000, 0b11111),
    'M': _g(0b10001, 0b11011, 0b10101, 0b10101, 0b10001, 0b10001, 0b10001),
    'N': _g(0b10001, 0b11001, 0b10101, 0b10011, 0b10001, 0b10001, 0b10001),
    'O': _g(0b01110, 0b10001, 0b10001, 0b10001, 0b10001, 0b10001, 0b01110),
    'P': _g(0b11110, 0b10001, 0b10001, 0b11110, 0b10000, 0b10000, 0b10000),
    'Q': _g(0b01110, 0b10001, 0b10001, 0b10001, 0b10101, 0b10010, 0b01101),
    'R': _g(0b11110, 0b10001, 0b10001, 0b11110, 0b10100, 0b10010, 0b10001),
    'S': _g(0b01111, 0b10000, 0b10000, 0b01110, 0b00001, 0b00001, 0b11110),
    'T': _g(0b11111, 0b00100, 0b00100, 0b00100, 0b00100, 0b00100, 0b00100),
    'U': _g(0b10001, 0b10001, 0b10001, 0b10001, 0b10001, 0b10001, 0b01110),
    'V': _g(0b10001, 0b10001, 0b10001, 0b10001, 0b10001, 0b01010, 0b00100),
    'W': _g(0b10001, 0b10001, 0b10001, 0b10101, 0b10101, 0b11011, 0b10001),
    'X': _g(0b10001, 0b10001, 0b01010, 0b00100, 0b01010, 0b10001, 0b10001),
    'Y': _g(0b10001, 0b10001, 0b01010, 0b00100, 0b00100, 0b00100, 0b00100),
    'Z': _g(0b11111, 0b00001, 0b00010, 0b00100, 0b01000, 0b10000, 0b11111),
    '[': _g(0b01110, 0b01000, 0b01000, 0b01000, 0b01000, 0b01000, 0b01110),
    '\\': _g(0b10000, 0b01000, 0b00100, 0b00100, 0b00010, 0b00001, 0b00000),
    ']': _g(0b01110, 0b00010, 0b00010, 0b00010, 0b00010, 0b00010, 0b01110),
    '^': _g(0b00100, 0b01010, 0b10001, 0b00000, 0b00000, 0b00000, 0b00000),
    '_': _g(0b00000, 0b00000, 0b00000, 0b00000, 0b00000, 0b00000, 0b11111),
    '`': _g(0b01000, 0b00100, 0b00010, 0b00000, 0b00000, 0b00000, 0b00000),
    'a': _g(0b00000, 0b00000, 0b01110, 0b00001, 0b01111, 0b10001, 0b01111),
    'b': _g(0b10000, 0b10000, 0b11110, 0b10001, 0b10001, 0b10001, 0b11110),
    'c': _g(0b00000, 0b00000, 0b01110, 0b10000, 0b10000, 0b10001, 0b01110),
    'd': _g(0b00001, 0b00001, 0b01111, 0b10001, 0b10001, 0b10001, 0b01111),
    'e': _g(0b00000, 0b00000, 0b01110, 0b10001, 0b11111, 0b10000, 0b01110),
    'f': _g(0b00110, 0b01001, 0b01000, 0b11110, 0b01000, 0b01000, 0b01000),
    'g': _g(0b00000, 0b01111, 0b10001, 0b10001, 0b01111, 0b00001, 0b01110),
    'h': _g(0b10000, 0b10000, 0b11110, 0b10001, 0b10001, 0b10001, 0b10001),
    'i': _g(0b00100, 0b00000, 0b01100, 0b00100, 0b00100, 0b00100, 0b01110),
    'j': _g(0b00010, 0b00000, 0b00110, 0b00010, 0b00010, 0b10010, 0b01100),
    'k': _g(0b10000, 0b10000, 0b10010, 0b10100, 0b11000, 0b10100, 0b10010),
    'l': _g(0b01100, 0b00100, 0b00100, 0b00100, 0b00100, 0b00100, 0b01110),
    'm': _g(0b00000, 0b00000, 0b11010, 0b10101, 0b10101, 0b10101, 0b10001),
    'n': _g(0b00000, 0b00000, 0b11110, 0b10001, 0b10001, 0b10001, 0b10001),
    'o': _g(0b00000, 0b00000, 0b01110, 0b10001, 0b10001, 0b10001, 0b01110),
    'p': _g(0b00000, 0b11110, 0b10001, 0b10001, 0b11110, 0b10000, 0b10000),
    'q': _g(0b00000, 0b01111, 0b10001, 0b10001, 0b01111, 0b00001, 0b00001),
    'r': _g(0b00000, 0b00000, 0b10110, 0b11001, 0b10000, 0b10000, 0b10000),
    's': _g(0b00000, 0b00000, 0b01111, 0b10000, 0b01110, 0b00001, 0b11110),
    't': _g(0b01000, 0b01000, 0b11110, 0b01000, 0b01000, 0b01001, 0b00110),
    'u': _g(0b00000, 0b00000, 0b10001, 0b10001, 0b10001, 0b10011, 0b01101),
    'v': _g(0b00000, 0b00000, 0b10001, 0b10001, 0b10001, 0b01010, 0b00100),
    'w': _g(0b00000, 0b00000, 0b10001, 0b10001, 0b10101, 0b10101, 0b01010),
    'x': _g(0b00000, 0b00000, 0b10001, 0b01010, 0b00100, 0b01010, 0b10001),
    'y': _g(0b00000, 0b10001, 0b10001, 0b10001, 0b01111, 0b00001, 0b01110),
    'z': _g(0b00000, 0b00000, 0b11111, 0b00010, 0b00100, 0b01000, 0b11111),
    '{': _g(0b00010, 0b00100, 0b00100, 0b01000, 0b00100, 0b00100, 0b00010),
    '|': _g(0b00100, 0b00100, 0b00100, 0b00100, 0b00100, 0b00100, 0b00100),
    '}': _g(0b01000, 0b00100, 0b00100, 0b00010, 0b00100, 0b00100, 0b01000),
    '~': _g(0b00000, 0b01101, 0b10010, 0b00000, 0b00000, 0b00000, 0b00000),
}


def text_width(text, scale, spacing=None):
    """Width in pixels of a string at the given scale (5px + gap per char)."""
    if not text:
        return 0
    gap = scale if spacing is None else spacing
    return len(text) * 5 * scale + (len(text) - 1) * gap


# ---------------------------------------------------------------------------
# Canvas (RGB pixel buffer)
# ---------------------------------------------------------------------------
class Canvas:
    def __init__(self, w, h):
        self.w = w
        self.h = h
        self.buf = bytearray()
        for _ in range(w * h):
            self.buf += bytes(PAPER)

    def rect(self, x, y, w, h, color):
        for yy in range(h):
            row = (y + yy) * self.w
            for xx in range(w):
                i = (row + x + xx) * 3
                self.buf[i] = color[0]
                self.buf[i + 1] = color[1]
                self.buf[i + 2] = color[2]

    def glyph(self, x, y, ch, scale, color):
        rows = FONT.get(ch, FONT[' '])
        for ry, mask in enumerate(rows):
            for cx in range(5):
                if mask & (0b10000 >> cx):
                    self.rect(x + cx * scale, y + ry * scale, scale, scale, color)

    def text(self, x, y, text, scale, color, uppercase=False, spacing=None):
        if uppercase:
            text = text.upper()
        cx = x
        gap = scale if spacing is None else spacing
        for ch in text:
            self.glyph(cx, y, ch, scale, color)
            cx += 5 * scale + gap


# ---------------------------------------------------------------------------
# Icons: each is a function(canvas, x, y, scale) drawing a 16x16 grid glyph
# (scaled by `scale`).  x,y is the top-left of the 16x16 area.
# ---------------------------------------------------------------------------
def _px(c, x, y, scale, dx, dy, color):
    c.rect(x + dx * scale, y + dy * scale, scale, scale, color)


def _dot(c, x, y, scale, dx, dy, color):
    c.rect(x + dx * scale, y + dy * scale, scale, scale, color)


def icon_leaders(c, x, y, scale):
    """Three leader figure silhouettes (head + shoulders)."""
    # Three figures, each ~4px wide, laid across the 16x16 grid.
    heads = [(1, 1), (6, 1), (11, 1)]
    for hx, hy in heads:
        for dy in range(3):
            for dx in range(3):
                _dot(c, x, y, scale, hx + dx, hy + dy, NEWSRED)
    # shoulders (a broader trapezoid per figure)
    bodies = [(0, 5), (5, 5), (10, 5)]
    for bx, by in bodies:
        for dy in range(5):
            width = 5 if dy < 1 else (3 if dy < 3 else 2)
            left = bx + (2 if dy >= 3 else 1 if dy >= 1 else 0)
            for dx in range(width):
                _dot(c, x, y, scale, left + dx, by + dy, NEWSRED)


def icon_tanker(c, x, y, scale):
    """Burning tanker silhouette with flames."""
    # Hull (a long low boat), rows 11..15.
    for dy in range(5):
        for dx in range(14):
            _dot(c, x, y, scale, dx + 1, dy + 10, NAVY)
    # Superstructure / bridge block.
    for dy in range(4):
        for dx in range(5):
            _dot(c, x, y, scale, dx + 5, dy + 7, NAVY)
    # Flames rising from the hull.
    for dx, dy in [(4, 6), (6, 4), (8, 5), (9, 3)]:
        _dot(c, x, y, scale, dx, dy, NEWSRED)


def icon_scales(c, x, y, scale):
    """Scales of justice: centre pole, crossbeam, two hanging pans."""
    # Centre pole.
    for dy in range(12):
        _dot(c, x, y, scale, 7, dy + 1, NAVY)
    # Crossbeam.
    for dx in range(10):
        _dot(c, x, y, scale, dx + 3, 3, NAVY)
    # Suspension lines to pans.
    for dx in range(2):
        _dot(c, x, y, scale, 4, dy + 4, NAVY)  # covered by crossbeam rows
    for dx, dy in [(4, 4), (4, 5), (4, 6), (11, 4), (11, 5), (11, 6)]:
        _dot(c, x, y, scale, dx, dy, NAVY)
    # Left pan.
    for dx in range(7):
        _dot(c, x, y, scale, dx, 7, NAVY)
        _dot(c, x, y, scale, dx, 8, NAVY)
    # Right pan.
    for dx in range(7):
        _dot(c, x, y, scale, dx + 9, 7, NAVY)
        _dot(c, x, y, scale, dx + 9, 8, NAVY)


def icon_odessa(c, x, y, scale):
    """Damaged building with blast."""
    # Main building facade.
    for dy in range(9):
        for dx in range(8):
            _dot(c, x, y, scale, dx + 3, dy + 3, NAVY)
    # Missing/broken windows (paper-colored holes).
    for dx, dy in [(4, 4), (6, 4), (8, 4), (5, 6), (9, 6), (7, 8), (5, 8)]:
        _dot(c, x, y, scale, dx, dy, PAPER)
    # Blast burst in red near the top.
    for dx, dy in [(1, 1), (2, 0), (3, 1), (12, 1), (13, 2), (13, 5)]:
        _dot(c, x, y, scale, dx, dy, NEWSRED)


def icon_nvidia(c, x, y, scale):
    """Chip with eye-like logo."""
    # Chip body.
    for dy in range(11):
        for dx in range(11):
            _dot(c, x, y, scale, dx + 2, dy + 2, NAVY)
    # Eye-like logo: a white ring with a dark pupil (the "eye").
    for dy in range(5):
        for dx in range(6):
            if (dx == 0 or dx == 5 or dy == 0 or dy == 4) and not (0 < dx < 5 and 0 < dy < 4):
                _dot(c, x, y, scale, dx + 4, dy + 4, HEADLINE)
    _dot(c, x, y, scale, 6, 6, HEADLINE)  # pupil glint
    # Pins on left and right edges.
    for dy in range(3):
        for dx in range(2):
            _dot(c, x, y, scale, 1, dy + 7, HEADLINE)
            _dot(c, x, y, scale, 13, dy + 7, HEADLINE)


def icon_cyclone(c, x, y, scale):
    """Spiral cyclone symbol."""
    # Outer spiral rings (a cyclone eye).
    ring = [(2, 2), (3, 2), (4, 2), (5, 2), (6, 2),
            (2, 3), (6, 3), (2, 4), (6, 4), (2, 5), (6, 5),
            (2, 6), (3, 6), (4, 6), (5, 6), (6, 6)]
    for dx, dy in ring:
        _dot(c, x, y, scale, dx + 1, dy + 1, NAVY)
    # Spiral arm accent in red.
    for dx, dy in [(3, 3), (5, 4), (4, 5)]:
        _dot(c, x, y, scale, dx + 1, dy + 1, NEWSRED)


def icon_gta(c, x, y, scale):
    """Gamepad."""
    # Main body.
    for dy in range(5):
        for dx in range(10):
            _dot(c, x, y, scale, dx + 3, dy + 5, NAVY)
    # Left / right grips.
    for dy in range(3):
        for dx in range(3):
            _dot(c, x, y, scale, dx + 1, dy + 7, NAVY)
            _dot(c, x, y, scale, dx + 12, dy + 7, NAVY)
    # D-pad.
    for dy in range(3):
        for dx in range(1):
            _dot(c, x, y, scale, dx + 6, dy + 6, PAPER)
    _dot(c, x, y, scale, 5, 7, PAPER)
    _dot(c, x, y, scale, 7, 7, PAPER)
    # Face buttons.
    _dot(c, x, y, scale, 9, 6, PAPER)
    _dot(c, x, y, scale, 10, 7, PAPER)


def icon_cyber(c, x, y, scale):
    """Padlock with warning."""
    # Shackle (open at the bottom).
    for dy in range(4):
        for dx in range(2):
            _dot(c, x, y, scale, dx + 4, dy + 3, NEWSRED)
            _dot(c, x, y, scale, dx + 9, dy + 3, NEWSRED)
    # Body.
    for dy in range(6):
        for dx in range(7):
            _dot(c, x, y, scale, dx + 4, dy + 7, NEWSRED)
    # Keyhole.
    for dy in range(2):
        for dx in range(1):
            _dot(c, x, y, scale, dx + 7, dy + 9, PAPER)
    # Warning exclamation on the body.
    _dot(c, x, y, scale, 7, 8, PAPER)
    _dot(c, x, y, scale, 7, 10, PAPER)


# ---------------------------------------------------------------------------
# Story data
# ---------------------------------------------------------------------------
STORIES = [
    ("SHENZHEN SUMMIT", icon_leaders,
     ["TRUMP-XI-PUTIN MEET", "First-ever 3-power summit", "Shenzhen, APEC - Nov 19"]),
    ("GULF CRISIS", icon_tanker,
     ["US STRIKES IRANIAN ISLE", "Tankers ablaze in Hormuz", "Gulf states intercept fire"]),
    ("WORLD COURT", icon_scales,
     ["ICJ ROHINGYA RULING", "Genocide case vs Myanmar", "The Hague, Gambia v Myanmar"]),
    ("ODESA STRUCK", icon_odessa,
     ["RUSSIAN HITS ON ODESA", "Historic centre struck, 4 dead"]),
    ("NVIDIA", icon_nvidia,
     ["NVIDIA HALTS H200", "600k chips stuck in HK", "US closes China chip loophole"]),
    ("CYCLONE AKVAN", icon_cyclone,
     ["CYCLONE AKVAN HITS", "Odisha red zone", "India braces for surge"]),
    ("GTA 6", icon_gta,
     ["GTA 6 IS OUT", "After a 13-year wait"]),
    ("CYBER ALERT", icon_cyber,
     ["JAVA FLAW ALARM", "NSA locks Fort Meade", "Global patch scramble"]),
]


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

    # Banner: top headline, gold, large (scale 4), centered.
    banner = "THURSDAY 19 NOVEMBER 2026"
    bs = 4
    bw = text_width(banner, bs)
    bx = (W - bw) // 2
    by = 24
    c.text(bx, by, banner, bs, BANNER)

    # Subtitle beneath the banner.
    sub = "THE WORLD IN EIGHT STORIES"
    ss = 2
    sw = text_width(sub, ss)
    sx = (W - sw) // 2
    c.text(sx, by + 7 * bs + 24, sub, ss, FACT)

    # A gold rule under the subtitle.
    c.rect(80, by + 7 * bs + 24 + 7 * ss + 14, W - 160, 3, BANNER)

    # Story grid: 2 columns x 4 rows.
    cols = 2
    rows = 4
    margin = 60
    gap = 30
    cell_w = (W - 2 * margin - (cols - 1) * gap) // cols
    cell_h = (H - 260 - (rows - 1) * gap) // rows

    icon_scale = 3
    icon_area = 16 * icon_scale  # 48

    headline_scale = 2
    fact_scale = 2

    top = 260
    for r in range(rows):
        for col in range(cols):
            idx = r * cols + col
            name, draw_icon, lines = STORIES[idx]

            cell_x = margin + col * (cell_w + gap)
            cell_y = top + r * (cell_h + gap)

            # Icon (48x48) at top-left of the cell.
            draw_icon(c, cell_x, cell_y, icon_scale)

            # Text block to the right of the icon.
            tx = cell_x + icon_area + 20
            ty = cell_y

            # Headline in off-white.
            c.text(tx, ty, lines[0], headline_scale, HEADLINE)
            ty += 7 * headline_scale + 14

            # Fact lines in grey.
            for line in lines[1:]:
                c.text(tx, ty, line, fact_scale, FACT)
                ty += 7 * fact_scale + 10

            # thin divider under each block
            c.rect(cell_x, cell_y + cell_h - 2, cell_w, 2, (0x20, 0x22, 0x26))

    # Write output with fallback path.
    path = "/output/entry.png"
    if not _writable("/output"):
        os.makedirs("./out", exist_ok=True)
        path = "./out/entry.png"
    write_png(path, c)
    print("Wrote", path)


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