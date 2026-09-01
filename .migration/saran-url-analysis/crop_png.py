#!/usr/bin/env python3
"""Crop top N rows of an 8-bit truecolor (RGB) PNG using only stdlib.
Decodes IDAT, unfilters scanlines, keeps the top `rows`, re-encodes filter 0."""
import struct, zlib, sys, os

def read_png(fn):
    data = open(fn, "rb").read()
    assert data[:8] == b"\x89PNG\r\n\x1a\n"
    pos = 8
    w = h = bd = ct = None
    idat = b""
    while pos < len(data):
        ln = struct.unpack(">I", data[pos:pos+4])[0]
        typ = data[pos+4:pos+8]
        chunk = data[pos+8:pos+8+ln]
        if typ == b"IHDR":
            w, h, bd, ct = struct.unpack(">IIBB", chunk[:10])
        elif typ == b"IDAT":
            idat += chunk
        pos += 12 + ln
    return w, h, bd, ct, idat

def paeth(a, b, c):
    p = a + b - c
    pa, pb, pc = abs(p-a), abs(p-b), abs(p-c)
    if pa <= pb and pa <= pc: return a
    if pb <= pc: return b
    return c

def unfilter(raw, w, h, bpp):
    stride = w * bpp
    out = bytearray()
    prev = bytearray(stride)
    pos = 0
    for _ in range(h):
        ft = raw[pos]; pos += 1
        line = bytearray(raw[pos:pos+stride]); pos += stride
        if ft == 1:
            for i in range(bpp, stride): line[i] = (line[i] + line[i-bpp]) & 255
        elif ft == 2:
            for i in range(stride): line[i] = (line[i] + prev[i]) & 255
        elif ft == 3:
            for i in range(stride):
                a = line[i-bpp] if i >= bpp else 0
                line[i] = (line[i] + ((a + prev[i]) >> 1)) & 255
        elif ft == 4:
            for i in range(stride):
                a = line[i-bpp] if i >= bpp else 0
                c = prev[i-bpp] if i >= bpp else 0
                line[i] = (line[i] + paeth(a, prev[i], c)) & 255
        out += line
        prev = line
    return out, stride

def crop_top(fn, out_fn, rows):
    w, h, bd, ct, idat = read_png(fn)
    assert bd == 8 and ct == 2, f"need 8-bit RGB, got bd={bd} ct={ct}"
    bpp = 3
    raw = zlib.decompress(idat)
    pixels, stride = unfilter(raw, w, h, bpp)
    rows = min(rows, h)
    body = bytearray()
    for r in range(rows):
        body.append(0)  # filter None
        body += pixels[r*stride:(r+1)*stride]
    comp = zlib.compress(bytes(body), 9)
    def chunk(typ, dat):
        return struct.pack(">I", len(dat)) + typ + dat + struct.pack(">I", zlib.crc32(typ+dat) & 0xffffffff)
    ihdr = struct.pack(">IIBBBBB", w, rows, 8, 2, 0, 0, 0)
    with open(out_fn, "wb") as f:
        f.write(b"\x89PNG\r\n\x1a\n")
        f.write(chunk(b"IHDR", ihdr))
        f.write(chunk(b"IDAT", comp))
        f.write(chunk(b"IEND", b""))
    return w, rows

if __name__ == "__main__":
    fn, out_fn, rows = sys.argv[1], sys.argv[2], int(sys.argv[3])
    w, r = crop_top(fn, out_fn, rows)
    print(f"{out_fn} {w}x{r}")
