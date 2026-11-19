# SPEC.md — /workspace/entries/news-image/entry

## a) One-line story summaries
1. First-ever Trump–Xi–Putin trilateral summit, Shenzhen, China (APEC, Nov 19).
2. US strike on an Iranian island; Gulf states intercepting fire; tankers ablaze in the Strait of Hormuz.
3. ICJ, The Hague: landmark Rohingya genocide judgment against Myanmar (case by Gambia).
4. Russian strikes hit historic Odesa, Ukraine, killing four.
5. Nvidia halts H200 shipments to China; 600,000 chips stalled in Hong Kong; first all-hands since Huang's exit.
6. Cyclone Akvan bears down on Odisha, India (red zone: Kendrapara, Jagatsinghpur, Puri).
7. Grand Theft Auto 6 launches overnight after a 13-year wait.
8. Global alarm over a critical Java flaw; NSA locks down Fort Meade after a patch broke NSANet.

## b) Layout
- Dark front-page style, 1024x1024 RGB PNG to /output/entry.png.
- Banner: "THURSDAY 19 NOVEMBER 2026".
- Story blocks in 2 columns x 4 rows. Each block: pixel icon (16x16), headline, 1-2 short fact lines.

## c) Bitmap font
- 5x7 embedded glyphs (ASCII 32-126), stored as list of ints (bit masks), stdlib only.

## d) PNG writer
- zlib compress raw rows. Each row: filter byte 0 + RGB triplets.
- Chunks IHDR / IDAT / IEND with struct-packed lengths and CRC (zlib.crc32).

## e) Hex color palette
- Paper: #0A0A0C (near-black)
- Banner: #C9A227 (gold)
- Headline: #E8E6E3 (off-white)
- Fact text: #9AA0A6 (grey)
- Icon: #7A1F2B (newsred) / #2B4C6F (navy)