"""Pixelgrafik und 3D-Modelle fuer das Waffenpack (Minecraft 1.12).

Alle Texturen werden hier per Code gezeichnet (kein Bildeditor noetig),
damit sie reproduzierbar und leicht aenderbar sind.
"""

import json
import os
import random
import struct
import zlib


# ---------------------------------------------------------------------------
# Kleine Malbibliothek
# ---------------------------------------------------------------------------

def mix(a, b, t):
    return tuple(int(round(a[i] + (b[i] - a[i]) * t)) for i in range(len(a)))


def hell(c, f):
    """f > 1 heller, f < 1 dunkler (Alpha bleibt)."""
    r = tuple(max(0, min(255, int(c[i] * f))) for i in range(3))
    return r + tuple(c[3:]) if len(c) > 3 else r + (255,)


def rgba(c):
    return tuple(c) if len(c) == 4 else tuple(c) + (255,)


class Bild:
    def __init__(self, w, h, farbe=(0, 0, 0, 0)):
        self.w, self.h = w, h
        self.p = [[rgba(farbe)] * w for _ in range(h)]

    def set(self, x, y, c):
        if 0 <= x < self.w and 0 <= y < self.h:
            self.p[y][x] = rgba(c)

    def get(self, x, y):
        return self.p[y % self.h][x % self.w]

    def rechteck(self, x, y, w, h, c):
        for yy in range(y, y + h):
            for xx in range(x, x + w):
                self.set(xx, yy, c)

    def rahmen(self, x, y, w, h, c):
        for xx in range(x, x + w):
            self.set(xx, y, c)
            self.set(xx, y + h - 1, c)
        for yy in range(y, y + h):
            self.set(x, yy, c)
            self.set(x + w - 1, yy, c)

    def rauschen(self, x, y, w, h, c, staerke, seed, flecken=None):
        """Grundfarbe mit Helligkeitsrauschen; flecken=(farbe, anteil) fuer Sprenkel."""
        r = random.Random(seed)
        for yy in range(y, y + h):
            for xx in range(x, x + w):
                f = 1 + r.uniform(-staerke, staerke)
                farbe = hell(c, f)
                if flecken and r.random() < flecken[1]:
                    farbe = rgba(flecken[0])
                self.set(xx, yy, farbe)

    def linie(self, x0, y0, x1, y1, c):
        n = max(abs(x1 - x0), abs(y1 - y0), 1)
        for i in range(n + 1):
            self.set(int(round(x0 + (x1 - x0) * i / n)), int(round(y0 + (y1 - y0) * i / n)), c)

    def ellipse(self, cx, cy, rx, ry, c):
        for yy in range(int(cy - ry) - 1, int(cy + ry) + 2):
            for xx in range(int(cx - rx) - 1, int(cx + rx) + 2):
                if ((xx + 0.5 - cx) / rx) ** 2 + ((yy + 0.5 - cy) / ry) ** 2 <= 1:
                    self.set(xx, yy, c)

    def kopie_von(self, quelle, sx, sy, w, h, dx, dy):
        for yy in range(h):
            for xx in range(w):
                self.set(dx + xx, dy + yy, quelle.get(sx + xx, sy + yy))

    def png_bytes(self):
        roh = b"".join(b"\x00" + b"".join(bytes(px) for px in z) for z in self.p)

        def chunk(typ, daten):
            return struct.pack(">I", len(daten)) + typ + daten + struct.pack(">I", zlib.crc32(typ + daten) & 0xFFFFFFFF)

        return (b"\x89PNG\r\n\x1a\n"
                + chunk(b"IHDR", struct.pack(">IIBBBBB", self.w, self.h, 8, 6, 0, 0, 0))
                + chunk(b"IDAT", zlib.compress(roh, 9))
                + chunk(b"IEND", b""))

    def speichern(self, pfad):
        if os.path.dirname(pfad):
            os.makedirs(os.path.dirname(pfad), exist_ok=True)
        with open(pfad, "wb") as f:
            f.write(self.png_bytes())


def animation(frames):
    """Mehrere 16x16-Bilder zu einem senkrechten Animationsstreifen."""
    b = Bild(frames[0].w, frames[0].h * len(frames))
    for i, f in enumerate(frames):
        b.kopie_von(f, 0, 0, f.w, f.h, 0, i * f.h)
    return b


# Pixel-Schrift 3x5 fuer Beschriftungen
SCHRIFT = {
    "T": ["###", ".#.", ".#.", ".#.", ".#."],
    "N": ["#.#", "###", "###", "###", "#.#"],
    "X": ["#.#", "#.#", ".#.", "#.#", "#.#"],
    "!": [".#.", ".#.", ".#.", "...", ".#."],
}


def schrift(bild, text, x, y, c):
    for i, ch in enumerate(text):
        for yy, zeile in enumerate(SCHRIFT[ch]):
            for xx, z in enumerate(zeile):
                if z == "#":
                    bild.set(x + i * 4 + xx, y + yy, c)


# ---------------------------------------------------------------------------
# Block-Texturen fuer die Backrooms (ersetzen seltene Vanilla-Bloecke)
# ---------------------------------------------------------------------------

def tapete():
    """Level 0: vergilbte Tapete mit feinem Streifenmuster und Flecken."""
    b = Bild(16, 16)
    basis = (196, 178, 96)
    b.rauschen(0, 0, 16, 16, basis, 0.04, 1)
    for x in range(16):
        if x % 4 == 0:
            for y in range(16):
                b.set(x, y, hell(b.get(x, y), 0.9))
        if x % 4 == 2:
            for y in range(0, 16, 4):
                b.set(x, y + 1, hell(basis, 0.86))
                b.set(x, y + 2, hell(basis, 0.92))
    r = random.Random(7)
    for _ in range(5):
        x, y = r.randrange(16), r.randrange(16)
        for dy in range(r.randrange(2, 6)):
            b.set(x, (y + dy) % 16, hell(b.get(x, y + dy), 0.83))
    return b


def teppich():
    """Level 0: feuchter, gelbbrauner Teppich."""
    b = Bild(16, 16)
    b.rauschen(0, 0, 16, 16, (148, 128, 66), 0.09, 2, flecken=((122, 104, 52), 0.08))
    r = random.Random(3)
    for _ in range(2):
        cx, cy = r.randrange(16), r.randrange(16)
        for yy in range(-2, 3):
            for xx in range(-3, 4):
                if xx * xx / 9 + yy * yy / 4 <= 1:
                    px, py = (cx + xx) % 16, (cy + yy) % 16
                    b.set(px, py, hell(b.get(px, py), 0.85))
    return b


def deckenplatte():
    """Level 0: Rasterdecke mit perforierten Platten."""
    b = Bild(16, 16)
    b.rauschen(0, 0, 16, 16, (214, 206, 176), 0.03, 4)
    for i in range(16):
        b.set(i, 0, (150, 146, 128))
        b.set(0, i, (150, 146, 128))
        b.set(i, 15, (176, 170, 148))
        b.set(15, i, (176, 170, 148))
    r = random.Random(5)
    for _ in range(26):
        b.set(r.randrange(2, 14), r.randrange(2, 14), (184, 176, 150))
    return b


def leuchtpanel(hell_an=True):
    """Leuchtstoffroehren-Panel (Seelaterne)."""
    b = Bild(16, 16)
    b.rechteck(0, 0, 16, 16, (172, 172, 166))
    b.rahmen(0, 0, 16, 16, (128, 128, 122))
    innen = (252, 252, 236) if hell_an else (206, 206, 192)
    b.rechteck(2, 2, 12, 12, innen)
    for y in (4, 8, 12):
        for x in range(2, 14):
            b.set(x, y - 1, hell(innen, 0.95))
    for x in range(2, 14):
        b.set(x, 2, (255, 255, 255) if hell_an else (220, 220, 208))
    return b


def betonwand():
    """Level 1: fleckige Betonwand mit Schalungsfugen."""
    b = Bild(16, 16)
    b.rauschen(0, 0, 16, 16, (124, 124, 120), 0.07, 8, flecken=((104, 104, 100), 0.05))
    for x in range(16):
        b.set(x, 7, (98, 98, 95))
    for p in ((3, 3), (12, 3), (3, 11), (12, 11)):
        b.set(*p, (70, 70, 68))
    r = random.Random(9)
    x, y = 10, 9
    for _ in range(6):
        b.set(x, y, (84, 84, 80))
        x += r.choice((-1, 0, 1))
        y += 1
    for xx in range(4, 7):
        for yy in range(8, 16):
            if r.random() < 0.35:
                b.set(xx, yy, hell(b.get(xx, yy), 0.86))
    return b


def betonboden():
    """Level 1: nasser Betonboden mit Pfuetzenglanz."""
    b = Bild(16, 16)
    b.rauschen(0, 0, 16, 16, (92, 92, 90), 0.08, 11)
    b.ellipse(5, 10, 4, 2.5, (104, 110, 118))
    b.ellipse(12, 4, 2.5, 1.6, (104, 110, 118))
    for p in ((3, 9), (4, 9), (11, 3)):
        b.set(*p, (140, 148, 158))
    for i in range(16):
        b.set(i, 15, (80, 80, 78))
    return b


def betonsaeule():
    """Level 1: hellerer Beton fuer Saeulen und Decke."""
    b = Bild(16, 16)
    b.rauschen(0, 0, 16, 16, (156, 156, 150), 0.05, 12)
    for x in range(16):
        b.set(x, 0, (128, 128, 124))
    b.set(7, 7, (110, 110, 106))
    b.set(8, 8, (118, 118, 114))
    return b


def kiste():
    """Level 1: Pappkarton mit Klebeband und Aufkleber."""
    b = Bild(16, 16)
    b.rauschen(0, 0, 16, 16, (158, 118, 72), 0.06, 15)
    b.rahmen(0, 0, 16, 16, (118, 84, 48))
    b.rechteck(6, 0, 4, 16, (196, 170, 120))
    for y in range(0, 16, 3):
        b.set(6, y, (176, 150, 102))
    b.rechteck(1, 10, 4, 4, (226, 222, 210))
    for x in range(2, 4):
        b.set(x, 11, (60, 60, 60))
        b.set(x + 1, 12, (60, 60, 60))
    return b


def metallwand():
    """Level 2: Wartungstunnel, genietete Stahlplatten mit Rost."""
    b = Bild(16, 16)
    b.rauschen(0, 0, 16, 16, (58, 74, 76), 0.07, 13)
    b.rahmen(0, 0, 16, 16, (40, 52, 54))
    for x in range(16):
        b.set(x, 8, (40, 52, 54))
    for p in ((2, 2), (13, 2), (2, 5), (13, 5), (2, 10), (13, 10), (2, 13), (13, 13)):
        b.set(*p, (110, 122, 120))
    r = random.Random(14)
    for _ in range(3):
        x = r.randrange(3, 13)
        for y in range(r.randrange(1, 9), 16):
            if r.random() < 0.7:
                b.set(x, y, (108, 62, 34))
    return b


def rohr():
    """Level 2: rostiges Rohr, waagerecht, mit Flanschen."""
    b = Bild(16, 16)
    verlauf = [0.55, 0.7, 0.85, 0.95, 1.05, 1.1, 1.05, 1.0, 0.95, 0.9, 0.85, 0.78, 0.7, 0.62, 0.55, 0.48]
    basis = (150, 84, 44)
    r = random.Random(15)
    for y in range(16):
        for x in range(16):
            c = hell(basis, verlauf[y] * (1 + r.uniform(-0.05, 0.05)))
            if r.random() < 0.06:
                c = (96, 52, 30)
            b.set(x, y, c)
    for x in (0, 1):
        for y in range(16):
            b.set(x, y, hell((120, 120, 116), verlauf[y]))
    return b


def gitterboden():
    """Level 2: Riffelblech-Gitterrost."""
    b = Bild(16, 16)
    b.rauschen(0, 0, 16, 16, (46, 48, 50), 0.06, 16)
    for y in range(0, 16, 4):
        for x in range(0, 16, 4):
            b.rechteck(x + 1, y + 1, 2, 2, (18, 18, 20))
    for x in range(16):
        b.set(x, 0, (70, 72, 74))
    return b


def dunkelmetall():
    """Level 2: dunkle Decke, auch Huelle aller Level."""
    b = Bild(16, 16)
    b.rauschen(0, 0, 16, 16, (34, 36, 38), 0.08, 17)
    for x in range(16):
        b.set(x, 15, (24, 25, 26))
    return b


def sculk(frame=0, seed=20):
    """Level 3: Sculk, dunkles Tuerkis mit pulsierenden Punkten (4 Frames)."""
    b = Bild(16, 16)
    b.rauschen(0, 0, 16, 16, (12, 40, 50), 0.12, seed, flecken=((8, 28, 36), 0.12))
    r = random.Random(seed + 1)
    punkte = [(r.randrange(16), r.randrange(16)) for _ in range(7)]
    staerke = [0.35, 0.65, 1.0, 0.65][frame]
    for i, (x, y) in enumerate(punkte):
        t = staerke if i % 2 == 0 else 1.35 - staerke
        b.set(x, y, mix((20, 70, 80), (60, 230, 220), max(0, min(1, t))))
    return b


def tiefschiefer():
    """Level 3: verstaerkter Tiefenschiefer, Fliesen fuer die Arena-Waende."""
    b = Bild(16, 16)
    b.rauschen(0, 0, 16, 16, (54, 56, 62), 0.07, 22)
    for i in range(16):
        b.set(i, 7, (34, 35, 40))
        b.set(i, 15, (34, 35, 40))
    for y in range(0, 8):
        b.set(7, y, (34, 35, 40))
    for y in range(8, 16):
        b.set(15, y, (34, 35, 40))
        b.set(0, y, (66, 68, 74))
    return b


def sculk_leuchten():
    """Level 3: leuchtender Sculk-Katalysator (Glowstone)."""
    b = Bild(16, 16)
    b.rauschen(0, 0, 16, 16, (16, 50, 58), 0.1, 23)
    b.ellipse(8, 8, 5, 5, (40, 150, 150))
    b.ellipse(8, 8, 3.2, 3.2, (120, 240, 230))
    b.ellipse(8, 8, 1.6, 1.6, (230, 255, 250))
    return b


def tnt_seite():
    """Sonder-TNT: dunkelrotes Gehaeuse, Warnstreifen, Beschriftung."""
    b = Bild(16, 16)
    b.rauschen(0, 0, 16, 16, (150, 24, 22), 0.06, 30)
    for x in range(16):
        b.set(x, 0, (90, 92, 96))
        b.set(x, 1, (130, 132, 136))
        b.set(x, 14, (130, 132, 136))
        b.set(x, 15, (90, 92, 96))
        for y in (2, 13):
            b.set(x, y, (24, 24, 24) if ((x + y) // 2) % 2 else (236, 196, 32))
    b.rechteck(1, 5, 14, 7, (28, 26, 26))
    b.rahmen(1, 5, 14, 7, (236, 196, 32))
    schrift(b, "TNT", 3, 6, (255, 255, 255))
    for x in (4, 8, 12):
        b.set(x, 3, (110, 18, 16))
        b.set(x, 4, (110, 18, 16))
    return b


def tnt_oben():
    b = Bild(16, 16)
    b.rauschen(0, 0, 16, 16, (100, 102, 106), 0.05, 31)
    b.rahmen(0, 0, 16, 16, (70, 72, 76))
    b.ellipse(8, 8, 5, 5, (150, 24, 22))
    b.ellipse(8, 8, 3, 3, (28, 26, 26))
    b.rechteck(7, 7, 2, 2, (236, 196, 32))
    b.set(8, 6, (255, 140, 30))
    for p in ((2, 2), (13, 2), (2, 13), (13, 13)):
        b.set(*p, (160, 162, 166))
    return b


def tnt_unten():
    b = Bild(16, 16)
    b.rauschen(0, 0, 16, 16, (84, 86, 90), 0.05, 32)
    b.rahmen(0, 0, 16, 16, (60, 62, 66))
    for p in ((2, 2), (13, 2), (2, 13), (13, 13), (7, 7), (8, 8)):
        b.set(*p, (140, 142, 146))
    return b


# ---------------------------------------------------------------------------
# Level 3 (Hotel) und Level 4 (Buero)
# ---------------------------------------------------------------------------

def hotel_tapete():
    """Level 3: dunkelrote Damast-Tapete mit goldenen Streifen."""
    b = Bild(16, 16)
    basis = (112, 22, 30)
    b.rauschen(0, 0, 16, 16, basis, 0.04, 40)
    muster = ["....#...", "...###..", "..#.#.#.", ".#..#..#", "..#.#.#.", "...###..", "....#...", "........"]
    for y in range(16):
        for x in range(16):
            if muster[y % 8][(x + (4 if (y // 8) % 2 else 0)) % 8] == "#":
                b.set(x, y, hell(basis, 1.32))
    for y in range(16):
        b.set(0, y, (176, 136, 60))
        b.set(15, y, (92, 18, 24))
    return b


def hotel_teppich():
    """Level 3: roter Hotelteppich mit goldenem Rautenmuster."""
    b = Bild(16, 16)
    b.rauschen(0, 0, 16, 16, (128, 20, 26), 0.06, 41)
    for y in range(16):
        for x in range(16):
            d = abs(x - 7.5) + abs(y - 7.5)
            if 6.5 <= d <= 7.5:
                b.set(x, y, (196, 150, 64))
            elif 3 <= d <= 3.6:
                b.set(x, y, (60, 10, 14))
    b.ellipse(8, 8, 1.4, 1.4, (214, 170, 80))
    for p in ((0, 0), (15, 0), (0, 15), (15, 15)):
        b.set(*p, (214, 170, 80))
    return b


def holzpaneel():
    """Level 3/4: dunkle Holzvertaefelung (auch Schreibtische)."""
    b = Bild(16, 16)
    r = random.Random(42)
    for x in range(16):
        brett = x // 4
        c = hell((92, 58, 32), 0.9 + 0.08 * (brett % 2))
        for y in range(16):
            b.set(x, y, hell(c, 1 + r.uniform(-0.06, 0.06)))
        if x % 4 == 0:
            for y in range(16):
                b.set(x, y, (54, 32, 18))
    for y in (0, 15):
        for x in range(16):
            b.set(x, y, (64, 40, 22))
    for _ in range(6):
        x, y = r.randrange(1, 15), r.randrange(2, 14)
        b.set(x, y, (70, 44, 24))
        b.set(x, y + 1, (70, 44, 24))
    return b


def buero_teppich():
    """Level 4: blaugrauer Buero-Teppich in Fliesen."""
    b = Bild(16, 16)
    b.rauschen(0, 0, 16, 16, (74, 86, 108), 0.09, 43, flecken=((60, 68, 86), 0.1))
    for i in range(16):
        b.set(i, 0, (60, 70, 88))
        b.set(0, i, (60, 70, 88))
    r = random.Random(44)
    for _ in range(3):
        b.set(r.randrange(16), r.randrange(16), (104, 98, 84))
    return b


def kabinenwand():
    """Level 4: Stoffbespannte Trennwand mit Alu-Rahmen."""
    b = Bild(16, 16)
    b.rauschen(0, 0, 16, 16, (128, 132, 140), 0.07, 45)
    b.rahmen(0, 0, 16, 16, (178, 180, 184))
    for y in range(1, 15, 2):
        for x in range(1, 15):
            if (x + y) % 4 == 0:
                b.set(x, y, hell(b.get(x, y), 0.9))
    return b


def buerowand():
    """Level 4: weiss gestrichene, angegraute Buerowand."""
    b = Bild(16, 16)
    b.rauschen(0, 0, 16, 16, (206, 204, 194), 0.03, 46)
    r = random.Random(47)
    for _ in range(4):
        x, y = r.randrange(16), r.randrange(16)
        b.set(x, y, (186, 184, 172))
    for x in range(16):
        b.set(x, 15, (170, 168, 158))
    return b


def monitor():
    """Level 4: alter Roehrenmonitor (beiges Gehaeuse, gruener Text)."""
    b = Bild(16, 16)
    b.rechteck(0, 0, 16, 16, (196, 188, 160))
    b.rahmen(0, 0, 16, 16, (150, 142, 116))
    b.rechteck(2, 2, 12, 10, (16, 22, 18))
    r = random.Random(48)
    for y in range(3, 11, 2):
        laenge = r.randrange(3, 10)
        for x in range(3, 3 + laenge):
            b.set(x, y, (60, 210, 90) if r.random() < 0.8 else (30, 120, 50))
    b.rechteck(6, 13, 4, 1, (120, 114, 92))
    b.set(12, 13, (60, 200, 60))
    return b


# ---------------------------------------------------------------------------
# Boegen (32x32, animiert): Ultimativer Schatten-Bogen und Vernichtungs-Bogen
# ---------------------------------------------------------------------------

BOGEN_STILE = {
    "schatten": dict(
        holz=(26, 14, 44), kante=(150, 60, 255), glanz=(214, 160, 255), griff=(10, 6, 16),
        juwel=(200, 60, 255), sehne=[(170, 90, 255), (230, 190, 255)], spitze=(240, 210, 255),
        pfeil=(20, 12, 30), pfeilspitze=(190, 90, 255), feder=(120, 40, 200), rune=(200, 120, 255)),
    "vernichter": dict(
        holz=(236, 228, 206), kante=(230, 168, 36), glanz=(255, 244, 200), griff=(70, 20, 20),
        juwel=(255, 30, 50), sehne=[(255, 70, 70), (255, 220, 200)], spitze=(255, 214, 90),
        pfeil=(220, 170, 50), pfeilspitze=(255, 40, 40), feder=(255, 255, 255), rune=(255, 60, 60)),
}


def _bogen_bogenpunkte():
    """Punkte auf dem Bogenarm (Viertelkreis um die Ecke unten rechts)."""
    import math
    pkt = []
    for i in range(200):
        a = math.pi / 2 * i / 199
        pkt.append((31 - 27.5 * math.sin(a) - 0.5, 31 - 27.5 * math.cos(a) - 0.5, i / 199))
    return pkt


def bogen_bild(stil, zustand, frame, frames=8):
    """zustand: 0 = Ruhe, 1..3 = gespannt (wie bow_pulling_0..2)."""
    import math
    s = BOGEN_STILE[stil]
    b = Bild(32, 32)
    puls = 0.5 + 0.5 * math.sin(2 * math.pi * frame / frames)
    punkte = _bogen_bogenpunkte()

    def normale(x, y):
        nx, ny = x - 31, y - 31
        laenge = math.hypot(nx, ny) or 1
        return nx / laenge, ny / laenge          # zeigt nach aussen (oben links)

    # Leuchtender Schein um den Arm (halbdurchsichtig)
    schein = s["kante"] + (int(70 + 60 * puls),)
    for (x, y, t) in punkte[::2]:
        nx, ny = normale(x, y)
        dicke = 1.2 + 2.6 * math.sin(math.pi * t)
        for d in (dicke / 2 + 1.2, -dicke / 2 - 1.0):
            px, py = int(round(x + nx * d)), int(round(y + ny * d))
            if b.get(px, py)[3] == 0:
                b.set(px, py, schein)
    # Stacheln an der Aussenseite
    for ts in (0.18, 0.3, 0.7, 0.82):
        x, y, t = punkte[int(ts * 199)]
        nx, ny = normale(x, y)
        for k in range(1, 5):
            breite = 1 if k < 3 else 0
            for q in range(-breite, breite + 1):
                px = int(round(x + nx * (1.5 + k) + ny * q * 0.7))
                py = int(round(y + ny * (1.5 + k) - nx * q * 0.7))
                b.set(px, py, s["spitze"] if k == 4 else hell(s["kante"], 0.8 + 0.1 * k))
    # Arm: Dicke zur Mitte hin 4, an den Spitzen 1
    for (x, y, t) in punkte:
        nx, ny = normale(x, y)
        dicke = 1.2 + 2.6 * math.sin(math.pi * t)
        for d10 in range(-25, 26):
            d = d10 / 10
            if abs(d) <= dicke / 2:
                px, py = int(round(x + nx * d)), int(round(y + ny * d))
                if d > dicke / 2 - 0.6:
                    farbe = s["kante"]
                elif d < -dicke / 2 + 0.6:
                    farbe = hell(s["holz"], 0.7)
                else:
                    farbe = s["holz"]
                b.set(px, py, farbe)
    # Leuchtende Linie im Arm und Runen
    for (x, y, t) in punkte[::2]:
        if 0.06 < t < 0.94:
            b.set(int(round(x)), int(round(y)), mix(s["holz"], s["glanz"], 0.25 + 0.45 * puls))
    for i, (x, y, t) in enumerate(punkte[8::16]):
        if 0.1 < t < 0.9 and not (0.4 < t < 0.6):
            an = ((i + frame) % 4) == 0
            b.set(int(round(x)), int(round(y)), s["rune"] if an else mix(s["rune"], s["holz"], 0.55))
    # Griff in der Mitte mit Juwel
    gx, gy = 31 - 27.5 * math.sin(math.pi / 4) - 0.5, 31 - 27.5 * math.cos(math.pi / 4) - 0.5
    for dx in range(-3, 4):
        for dy in range(-3, 4):
            if abs(dx - dy) <= 1 and abs(dx + dy) <= 5:
                b.set(int(gx) + dx, int(gy) + dy, s["griff"] if (dx + dy) % 2 else hell(s["griff"], 1.6))
    b.ellipse(gx + 0.5, gy + 0.5, 1.8, 1.8, mix(s["juwel"], (255, 255, 255), 0.35 * puls))
    b.set(int(gx), int(gy), (255, 255, 255))
    # Klingen an den Spitzen
    for (x0, y0, dx, dy) in ((30, 3, 1, -1), (3, 30, -1, 1)):
        for k in range(3):
            b.set(x0 + dx * k, y0 + dy * k, s["spitze"])
            b.set(x0 + dx * k - 1, y0 + dy * k, hell(s["spitze"], 0.7))
    # Sehne (flimmernde Energie)
    zug = [0, 3, 6, 8][zustand]
    sx, sy = 17 + zug, 17 + zug
    for (ax, ay) in ((30, 4), (4, 30)):
        n = max(abs(sx - ax), abs(sy - ay))
        for i in range(n + 1):
            px = int(round(ax + (sx - ax) * i / n))
            py = int(round(ay + (sy - ay) * i / n))
            b.set(px, py, s["sehne"][(i + frame) % 2])
    # Pfeil beim Spannen
    if zustand:
        lang = 22
        for i in range(lang):
            px, py = sx - i, sy - i
            b.set(px, py, s["pfeil"])
            b.set(px + 1, py, hell(s["pfeil"], 1.5))
            if i < 4:
                b.set(px + 1, py - 1, s["feder"])
                b.set(px - 1, py + 1, s["feder"])
        tx, ty = sx - lang, sy - lang
        for (dx, dy) in ((0, 0), (-1, 0), (0, -1), (-1, -1), (1, -1), (-1, 1), (1, 0), (0, 1)):
            b.set(tx + dx, ty + dy, s["pfeilspitze"])
        b.set(tx - 2, ty - 2, mix(s["pfeilspitze"], (255, 255, 255), puls))
        b.set(tx - 1, ty - 1, (255, 255, 255))
    return b


def bogen_animation(stil, zustand, frames=8):
    return animation([bogen_bild(stil, zustand, f, frames) for f in range(frames)])


# ---------------------------------------------------------------------------
# Werf-TNT (Wurftrank): getoente Stangen + Details
# ---------------------------------------------------------------------------

def granate_huelle():
    """Ebene 0 (wird in der Farbe der Sorte getoent): drei Dynamitstangen."""
    b = Bild(16, 16)
    for x0 in (3, 7, 11):
        for y in range(5, 15):
            for dx, f in enumerate((235, 205, 165)):
                b.set(x0 + dx, y, (f, f, f))
        b.set(x0, 14, (200, 200, 200))
    return b


def granate_details():
    """Ebene 1: Klebeband mit Warnfeld, Kappen, Zuendschnur mit Funken."""
    b = Bild(16, 16)
    for x in range(3, 14):
        b.set(x, 9, (30, 30, 32))
        b.set(x, 10, (52, 52, 56))
    b.rechteck(6, 8, 5, 4, (236, 232, 220))
    b.set(7, 9, (20, 20, 20))
    b.set(8, 10, (20, 20, 20))
    b.set(9, 9, (20, 20, 20))
    for x0 in (3, 7, 11):
        for dx in range(3):
            b.set(x0 + dx, 4, (150, 150, 156))
    b.set(8, 3, (60, 50, 40))
    b.set(9, 2, (60, 50, 40))
    b.set(10, 2, (60, 50, 40))
    b.set(11, 1, (255, 200, 40))
    b.set(12, 0, (255, 120, 20))
    b.set(12, 1, (255, 240, 160))
    return b


# Block-Textur-Ersatz: Vanilla-Textur -> (Funktion, Animations-Frames oder None)
BLOCK_TEXTUREN = {
    "sponge": tapete,
    "glass_brown": teppich,
    "concrete_white": deckenplatte,
    "concrete_gray": betonwand,
    "glass_gray": betonboden,
    "concrete_silver": betonsaeule,
    "glass_silver": kiste,
    "concrete_cyan": metallwand,
    "concrete_orange": rohr,
    "glass_black": gitterboden,
    "concrete_black": dunkelmetall,
    "concrete_light_blue": tiefschiefer,
    "glowstone": sculk_leuchten,
    "tnt_side": tnt_seite,
    "tnt_top": tnt_oben,
    "tnt_bottom": tnt_unten,
    "red_nether_brick": hotel_tapete,
    "nether_wart_block": hotel_teppich,
    "concrete_powder_brown": holzpaneel,
    "concrete_powder_blue": buero_teppich,
    "concrete_powder_silver": kabinenwand,
    "concrete_powder_white": buerowand,
    "concrete_powder_black": monitor,
}


def animierte_bloecke():
    """Animierte Block-Texturen: name -> (Bild-Streifen, mcmeta)."""
    an, aus = leuchtpanel(True), leuchtpanel(False)
    flackern = [0] * 30 + [1, 0, 1] + [0] * 40 + [1] + [0] * 20
    return {
        "sea_lantern": (animation([an, aus]), {"animation": {"frametime": 2, "frames": flackern}}),
        "concrete_blue": (animation([sculk(i, 20) for i in range(4)]), {"animation": {"frametime": 8}}),
        "glass_cyan": (animation([sculk(i, 40) for i in range(4)]), {"animation": {"frametime": 9}}),
    }


# ---------------------------------------------------------------------------
# 3D-Modelle aus Quadern
# ---------------------------------------------------------------------------

class Atlas:
    """64x64-Textur aus 16 Kacheln (je 16x16). Kachel n -> UV-Bereich 4x4."""

    def __init__(self):
        self.bild = Bild(64, 64)
        self.frei = 0
        self.namen = {}

    def kachel(self, name, bild16):
        n = self.frei
        self.frei += 1
        x, y = (n % 4) * 16, (n // 4) * 16
        self.bild.kopie_von(bild16, 0, 0, 16, 16, x, y)
        self.namen[name] = ((n % 4) * 4, (n // 4) * 4)
        return name

    def uv(self, name):
        u, v = self.namen[name]
        return [u + 0.05, v + 0.05, u + 3.95, v + 3.95]


class Modell:
    """Sammelt Quader in Pixel-Koordinaten (0..16 = ein Block, erlaubt -16..32)."""

    def __init__(self, atlas, textur):
        self.atlas = atlas
        self.textur = textur
        self.elemente = []

    def quader(self, von, bis, kacheln, drehung=None):
        """kacheln: Kachelname fuer alle Seiten oder dict seite->name (Rest: 'alle')."""
        if isinstance(kacheln, str):
            kacheln = {"alle": kacheln}
        von = [round(max(-16, min(32, v)), 3) for v in von]
        bis = [round(max(-16, min(32, v)), 3) for v in bis]
        faces = {}
        for seite in ("north", "south", "east", "west", "up", "down"):
            name = kacheln.get(seite, kacheln.get("alle"))
            faces[seite] = {"uv": self.atlas.uv(name), "texture": "#t"}
        e = {"from": von, "to": bis, "faces": faces}
        if drehung:
            achse, winkel, ursprung = drehung
            e["rotation"] = {"origin": [round(v, 3) for v in ursprung], "axis": achse, "angle": winkel}
        self.elemente.append(e)

    def json(self, display):
        return {"textures": {"t": self.textur, "particle": self.textur},
                "elements": self.elemente, "display": display}


class Koerper:
    """Monster-Modelle: Masse in Bloecken, Fuesse bei y=0, Blickrichtung -z.

    Das Modell wird als Kopf-Gegenstand eines unsichtbaren Zombies (Warden:
    Wither-Skelett, 1,2-fach gross) getragen.
    Kopfmitte des Zombies: 1,75 Bloecke ueber den Fuessen; Gegenstaende auf dem
    Kopf werden mit 0,625 skaliert, dazu kommt die eigene Skalierung s.
    """

    def __init__(self, modell, s, f=1.0):
        # f: Skalierung des Traeger-Monsters (Zombie 1,0, Wither-Skelett 1,2)
        self.m = modell
        self.s = s / f
        self.k = 16 / (0.625 * s)          # Pixel pro Block
        self.fuss = 8 - 1.75 * f * self.k  # Pixel-y der Fuesse

    def px(self, x, y, z):
        return [8 + x * self.k, self.fuss + y * self.k, 8 + z * self.k]

    def quader(self, von, bis, kacheln, drehung=None):
        if drehung:
            achse, winkel, ursprung = drehung
            drehung = (achse, winkel, self.px(*ursprung))
        self.m.quader(self.px(*von), self.px(*bis), kacheln, drehung)

    def display(self):
        return {"head": {"rotation": [0, 0, 0], "translation": [0, 0, 0], "scale": [self.s] * 3},
                "gui": {"rotation": [20, 200, 0], "translation": [0, -2, 0], "scale": [0.38 * 16 / (0.625 * self.k * 2.6)] * 3}}


def gespiegelt(von, bis):
    return [-bis[0], von[1], von[2]], [-von[0], bis[1], bis[2]]
