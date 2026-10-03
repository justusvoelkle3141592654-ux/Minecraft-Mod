"""3D-Modelle: Monster der Backrooms, Warden, Pistole, Bazooka, Taschenlampe.

Monster-Modelle werden von unsichtbaren Zombies auf dem Kopf getragen
(Diamanthacke mit bestimmtem Schadenswert). Jedes Monster hat zwei Bilder
(A/B) fuer eine einfache Lauf-Animation.
"""

import random

from grafik import Atlas, Bild, Koerper, Modell, gespiegelt, hell, mix

# Schadenswerte der Diamanthacke -> Modell
MONSTER_DAMAGE = {
    "warden": (20, 21),
    "smiler": (22, 23),
    "hound": (24, 25),
    "hautdieb": (26, 27),
}


def kachel(farbe, staerke, seed, flecken=None):
    b = Bild(16, 16)
    b.rauschen(0, 0, 16, 16, farbe, staerke, seed, flecken)
    return b


# ---------------------------------------------------------------------------
# Warden (nach dem Vorbild des echten Wardens aus Minecraft 1.19)
# ---------------------------------------------------------------------------

def warden_atlas():
    a = Atlas()
    haut = (20, 50, 60)
    a.kachel("haut", kachel(haut, 0.12, 101, ((10, 30, 38), 0.16)))
    a.kachel("haut_dunkel", kachel((13, 36, 44), 0.12, 102, ((8, 22, 28), 0.16)))
    # Brust: leuchtender Brustkorb mit Seelen
    b = kachel(haut, 0.1, 103, ((10, 30, 38), 0.12))
    for i, y in enumerate((2, 6, 10)):
        for x in range(1, 15):
            krumm = 1 if x in (1, 2, 13, 14) else 0
            b.set(x, y + krumm, (46, 214, 204))
            b.set(x, y + krumm + 1, (20, 120, 118))
    for y in range(1, 15):
        b.set(7, y, (60, 230, 220))
        b.set(8, y, (40, 190, 182))
    for cx, cy in ((4, 4), (11, 8), (5, 12)):
        b.ellipse(cx, cy, 1.6, 1.3, (170, 255, 246))
        b.set(cx - 1, cy, (40, 110, 110))
        b.set(cx + 1, cy, (40, 110, 110))
    a.kachel("brust", b)
    # Gesicht: keine Augen, grosses Maul mit Zaehnen
    g = kachel(haut, 0.1, 104, ((10, 30, 38), 0.1))
    for x in range(16):
        g.set(x, 3, (10, 28, 34))
    g.rechteck(2, 7, 12, 8, (6, 12, 14))
    for x in range(2, 14):
        if x % 2 == 0:
            g.set(x, 7, (196, 214, 206))
            g.set(x, 14, (176, 196, 188))
    g.rechteck(2, 6, 12, 1, (32, 80, 86))
    g.rechteck(5, 10, 6, 2, (60, 18, 22))
    a.kachel("gesicht", g)
    # Tentakel (Fuehler) am Kopf: tuerkis mit hellen Spitzen
    t = Bild(16, 16)
    for y in range(16):
        for x in range(16):
            t.set(x, y, mix((24, 120, 118), (200, 255, 250), x / 15))
    for x in range(0, 16, 4):
        for y in range(16):
            t.set(x, y, hell(t.get(x, y), 0.7))
    a.kachel("fuehler", t)
    o = kachel((14, 38, 46), 0.12, 105, ((50, 200, 190), 0.05))
    a.kachel("kopf_oben", o)
    h = kachel((10, 26, 32), 0.1, 106)
    for x in range(1, 16, 3):
        for y in range(12, 16):
            h.set(x, y, (150, 170, 160))
    a.kachel("hand", h)
    return a


def warden(atlas, bild):
    m = Modell(atlas, "items/waffenpack/warden")
    k = Koerper(m, 2.6, 1.2)   # Traeger: Wither-Skelett (hoehere Trefferflaeche)
    s = 22.5 if bild == "a" else -22.5
    w = 22.5 if bild == "a" else 0
    # Beine
    k.quader([-0.44, 0, -0.19], [-0.05, 0.86, 0.19], {"alle": "haut_dunkel", "down": "hand"},
             ("x", s, [-0.25, 0.86, 0]))
    k.quader([0.05, 0, -0.19], [0.44, 0.86, 0.19], {"alle": "haut_dunkel", "down": "hand"},
             ("x", -s, [0.25, 0.86, 0]))
    # Rumpf mit leuchtendem Brustkorb
    k.quader([-0.56, 0.82, -0.3], [0.56, 2.02, 0.3], {"alle": "haut", "north": "brust"})
    k.quader([-0.36, 1.12, -0.34], [0.36, 1.86, -0.3], "brust")
    # Arme (lang, bis zu den Knien)
    for x0, x1, rx, v in ((-0.9, -0.56, -0.73, -s), (0.56, 0.9, 0.73, s)):
        k.quader([x0, 0.5, -0.17], [x1, 1.98, 0.17], {"alle": "haut", "down": "hand"},
                 ("x", v, [rx, 1.9, 0]))
        k.quader([x0 - 0.02, 0.32, -0.19], [x1 + 0.02, 0.52, 0.19], "hand", ("x", v, [rx, 1.9, 0]))
    # Kopf
    k.quader([-0.5, 2.0, -0.42], [0.5, 2.92, 0.38], {"alle": "haut", "north": "gesicht", "up": "kopf_oben"})
    # Fuehler links und rechts
    for seite in (-1, 1):
        a0, a1 = sorted((seite * 0.5, seite * 0.86))
        b0, b1 = sorted((seite * 0.84, seite * 0.98))
        dreh = ("z", -seite * w if w else 0, [seite * 0.5, 2.68, 0])
        dreh = dreh if w else None
        k.quader([a0, 2.62, -0.05], [a1, 2.75, 0.05], "fuehler", dreh)
        k.quader([b0, 2.62, -0.05], [b1, 3.18, 0.05], "fuehler", dreh)
    return m.json(k.display())


# ---------------------------------------------------------------------------
# Smiler (Level 0): Schattenwesen mit leuchtendem Grinsen
# ---------------------------------------------------------------------------

def smiler_atlas():
    a = Atlas()
    a.kachel("schatten", kachel((22, 16, 30), 0.3, 201, ((6, 4, 10), 0.25)))
    g = Bild(16, 16)
    g.rauschen(0, 0, 16, 16, (10, 8, 14), 0.3, 202)
    g.ellipse(4.5, 4.5, 2.2, 1.6, (255, 255, 240))
    g.ellipse(11.5, 4.5, 2.2, 1.6, (255, 255, 240))
    g.set(4, 4, (30, 20, 30))
    g.set(11, 4, (30, 20, 30))
    for x in range(1, 15):
        y = 10 if 3 <= x <= 12 else 9
        hoehe = 3 if 3 <= x <= 12 else 2
        for yy in range(y, y + hoehe):
            g.set(x, yy, (255, 255, 236) if x % 2 else (200, 196, 180))
    for x in range(2, 14):
        g.set(x, 11 if 3 <= x <= 12 else 10, (20, 10, 16))
    a.kachel("gesicht", g)
    a.kachel("klaue", kachel((40, 34, 48), 0.2, 203))
    return a


def smiler(atlas, bild):
    m = Modell(atlas, "items/waffenpack/smiler")
    k = Koerper(m, 2.0)
    dy = 0 if bild == "a" else 0.08
    w = 22.5 if bild == "a" else 45
    k.quader([-0.15, 0.05 + dy, -0.1], [0.15, 0.3 + dy, 0.1], "schatten")
    k.quader([-0.3, 0.25 + dy, -0.2], [0.3, 0.55 + dy, 0.2], "schatten")
    k.quader([-0.42, 0.5 + dy, -0.28], [0.42, 1.55 + dy, 0.28], "schatten")
    k.quader([-0.55, 1.5 + dy, -0.45], [0.55, 2.42 + dy, 0.45], {"alle": "schatten", "north": "gesicht"})
    for seite in (-1, 1):
        x0, x1 = sorted((seite * 0.42, seite * 0.62))
        k.quader([x0, 0.55 + dy, -0.08], [x1, 1.5 + dy, 0.08], "schatten",
                 ("z", seite * w, [seite * 0.45, 1.45 + dy, 0]))
        c0, c1 = sorted((seite * 0.44, seite * 0.66))
        k.quader([c0, 0.4 + dy, -0.1], [c1, 0.58 + dy, 0.1], "klaue",
                 ("z", seite * w, [seite * 0.45, 1.45 + dy, 0]))
    return m.json(k.display())


# ---------------------------------------------------------------------------
# Hound (Level 1): ausgemergelte Kreatur auf allen Vieren, langes schwarzes Haar
# ---------------------------------------------------------------------------

def hound_atlas():
    a = Atlas()
    a.kachel("haut", kachel((132, 126, 116), 0.1, 301, ((104, 98, 90), 0.12)))
    haar = Bild(16, 16)
    r = random.Random(302)
    for x in range(16):
        c = r.choice([(14, 12, 12), (24, 22, 22), (10, 9, 9), (34, 30, 30)])
        for y in range(16):
            haar.set(x, y, hell(c, 1 + r.uniform(-0.15, 0.15)))
    a.kachel("haar", haar)
    g = Bild(16, 16)
    g.kopie_von(haar, 0, 0, 16, 16, 0, 0)
    g.set(5, 6, (230, 210, 120))
    g.set(10, 6, (230, 210, 120))
    g.rechteck(3, 11, 10, 3, (20, 6, 6))
    for x in range(3, 13, 2):
        g.set(x, 11, (230, 224, 200))
        g.set(x + 1, 13, (210, 204, 180))
    a.kachel("gesicht", g)
    a.kachel("ruecken", kachel((96, 90, 84), 0.12, 303))
    return a


def hound(atlas, bild):
    m = Modell(atlas, "items/waffenpack/hound")
    k = Koerper(m, 2.0)
    s = 22.5 if bild == "a" else -22.5
    k.quader([-0.3, 0.55, -0.45], [0.3, 0.95, 0.55], {"alle": "haut", "up": "ruecken"})
    k.quader([-0.06, 0.95, -0.4], [0.06, 1.0, 0.5], "ruecken")
    k.quader([-0.26, 0.6, -0.86], [0.26, 1.05, -0.45], {"alle": "haar", "north": "gesicht"})
    k.quader([-0.29, 0.98, -0.89], [0.29, 1.1, -0.4], "haar")
    for seite in (-1, 1):
        x0, x1 = sorted((seite * 0.26, seite * 0.3))
        k.quader([x0, 0.42, -0.89], [x1, 1.05, -0.42], "haar")
    for xs, zs, v in ((-1, -1, s), (1, 1, s), (1, -1, -s), (-1, 1, -s)):
        x0, x1 = sorted((xs * 0.12, xs * 0.29))
        z0, z1 = (-0.44, -0.28) if zs < 0 else (0.36, 0.52)
        k.quader([x0, 0, z0], [x1, 0.62, z1], "haut", ("x", v, [xs * 0.2, 0.6, (z0 + z1) / 2]))
    return m.json(k.display())


# ---------------------------------------------------------------------------
# Hautdieb (Level 2, "Skin-Stealer"): grosse, duerre Gestalt aus fremder Haut
# ---------------------------------------------------------------------------

def hautdieb_atlas():
    a = Atlas()
    a.kachel("haut", kachel((214, 184, 164), 0.08, 401, ((160, 70, 64), 0.06)))
    n = kachel((210, 180, 160), 0.08, 402, ((150, 60, 56), 0.05))
    for i in range(16):
        n.set(i, 8, (110, 30, 30))
        n.set(5, i, (110, 30, 30))
        if i % 2 == 0:
            n.set(i, 7, (90, 20, 20))
            n.set(4, i, (90, 20, 20))
    a.kachel("naht", n)
    g = kachel((222, 196, 178), 0.06, 403)
    g.ellipse(4.5, 5.5, 1.6, 3, (16, 8, 8))
    g.ellipse(11.5, 5.5, 1.6, 3, (16, 8, 8))
    g.set(4, 5, (240, 240, 230))
    g.set(11, 5, (240, 240, 230))
    g.linie(8, 5, 8, 9, (180, 150, 136))
    g.ellipse(8, 12.5, 2.2, 2.8, (40, 10, 12))
    for x in (6, 8, 10):
        g.set(x, 10, (230, 220, 200))
    a.kachel("gesicht", g)
    a.kachel("roh", kachel((150, 44, 42), 0.15, 404, ((200, 150, 140), 0.08)))
    return a


def hautdieb(atlas, bild):
    m = Modell(atlas, "items/waffenpack/hautdieb")
    k = Koerper(m, 2.4)
    s = 22.5 if bild == "a" else -22.5
    k.quader([-0.25, 0, -0.08], [-0.08, 1.25, 0.08], "haut", ("x", s, [-0.16, 1.22, 0]))
    k.quader([0.08, 0, -0.08], [0.25, 1.25, 0.08], "haut", ("x", -s, [0.16, 1.22, 0]))
    k.quader([-0.3, 1.2, -0.14], [0.3, 2.04, 0.14], {"alle": "haut", "north": "naht", "south": "roh"})
    k.quader([-0.07, 1.98, -0.07], [0.07, 2.1, 0.07], "roh")
    k.quader([-0.22, 2.06, -0.2], [0.22, 2.72, 0.2], {"alle": "haut", "north": "gesicht"})
    for xs, v in ((-1, -s), (1, s)):
        x0, x1 = sorted((xs * 0.3, xs * 0.43))
        k.quader([x0, 0.75, -0.06], [x1, 2.0, 0.06], "haut", ("x", v, [xs * 0.36, 1.95, 0]))
        f0, f1 = sorted((xs * 0.29, xs * 0.45))
        k.quader([f0, 0.45, -0.07], [f1, 0.77, 0.07], "roh", ("x", v, [xs * 0.36, 1.95, 0]))
    return m.json(k.display())


MONSTER = {
    "warden": (warden_atlas, warden),
    "smiler": (smiler_atlas, smiler),
    "hound": (hound_atlas, hound),
    "hautdieb": (hautdieb_atlas, hautdieb),
}


# ---------------------------------------------------------------------------
# Gegenstaende in 3D: Pistole, Bazooka, Taschenlampe (Muendung zeigt nach +x)
# ---------------------------------------------------------------------------

def pistole_atlas():
    a = Atlas()
    s = kachel((52, 54, 58), 0.05, 501)
    for x in range(10, 16, 2):
        for y in range(16):
            s.set(x, y, (30, 31, 34))
    for x in range(16):
        s.set(x, 0, (96, 98, 104))
    a.kachel("schlitten", s)
    a.kachel("rahmen", kachel((40, 41, 44), 0.06, 502))
    g = kachel((38, 30, 24), 0.1, 503, ((22, 18, 14), 0.25))
    a.kachel("griff", g)
    a.kachel("schwarz", kachel((16, 16, 18), 0.05, 504))
    v = kachel((16, 16, 18), 0.05, 505)
    v.ellipse(8, 8, 3, 3, (90, 255, 120))
    a.kachel("visier", v)
    return a


def pistole():
    a = pistole_atlas()
    m = Modell(a, "items/waffenpack/pistole3d")
    m.quader([2, 9, 7], [14.5, 12, 9], "schlitten")
    m.quader([4, 8, 7.2], [13.6, 9, 8.8], "rahmen")
    m.quader([14.5, 9.8, 7.4], [15.2, 11.2, 8.6], {"alle": "schwarz"})
    m.quader([2.6, 2.6, 6.9], [6.2, 8.4, 9.1], "griff", ("z", -22.5, [4.4, 8.4, 8]))
    m.quader([2.4, 2.0, 6.8], [6.4, 2.7, 9.2], "schwarz", ("z", -22.5, [4.4, 8.4, 8]))
    m.quader([6.4, 5.4, 7.6], [10, 6, 8.4], "rahmen")
    m.quader([9.5, 5.4, 7.6], [10, 8, 8.4], "rahmen")
    m.quader([7.6, 6, 7.75], [8.1, 8, 8.25], "schwarz")
    m.quader([13.4, 12, 7.7], [14, 12.6, 8.3], "visier")
    m.quader([2.4, 12, 7.2], [3.4, 12.7, 8.8], {"alle": "schwarz", "east": "visier"})
    disp = {
        "thirdperson_righthand": {"rotation": [0, 90, 0], "translation": [0, 2.5, 1.5], "scale": [0.6, 0.6, 0.6]},
        "thirdperson_lefthand": {"rotation": [0, -90, 0], "translation": [0, 2.5, 1.5], "scale": [0.6, 0.6, 0.6]},
        "firstperson_righthand": {"rotation": [0, 90, 0], "translation": [0, 2.5, 0], "scale": [0.55, 0.55, 0.55]},
        "firstperson_lefthand": {"rotation": [0, -90, 0], "translation": [0, 2.5, 0], "scale": [0.55, 0.55, 0.55]},
        "gui": {"rotation": [0, 0, 0], "translation": [0, 0.5, 0], "scale": [1.05, 1.05, 1.05]},
        "ground": {"rotation": [0, 0, 0], "translation": [0, 2, 0], "scale": [0.5, 0.5, 0.5]},
        "fixed": {"rotation": [0, 180, 0], "translation": [0, 0, 0], "scale": [1, 1, 1]},
    }
    return a, m.json(disp)


def bazooka_atlas():
    a = Atlas()
    a.kachel("rohr", kachel((80, 96, 50), 0.07, 601, ((64, 78, 40), 0.1)))
    w = Bild(16, 16)
    for y in range(16):
        for x in range(16):
            w.set(x, y, (236, 196, 32) if ((x + y) // 3) % 2 else (24, 24, 24))
    a.kachel("warn", w)
    a.kachel("schwarz", kachel((18, 18, 20), 0.05, 602))
    o = Bild(16, 16)
    o.rechteck(0, 0, 16, 16, (10, 10, 12))
    o.ellipse(8, 8, 5, 5, (30, 30, 34))
    o.ellipse(8, 8, 2.5, 2.5, (120, 40, 20))
    a.kachel("oeffnung", o)
    l = Bild(16, 16)
    l.rechteck(0, 0, 16, 16, (20, 20, 22))
    l.ellipse(8, 8, 5, 5, (90, 160, 220))
    l.set(6, 6, (220, 240, 255))
    a.kachel("linse", l)
    a.kachel("griff", kachel((40, 34, 28), 0.1, 603))
    return a


def bazooka():
    a = bazooka_atlas()
    m = Modell(a, "items/waffenpack/bazooka3d")
    m.quader([-12, 5, 6], [28, 11, 10], "rohr")
    m.quader([-12, 6, 5], [28, 10, 11], "rohr")
    m.quader([27, 4.5, 4.5], [30, 11.5, 11.5], {"alle": "schwarz", "east": "oeffnung"})
    m.quader([-14, 4.5, 4.5], [-11, 11.5, 11.5], {"alle": "schwarz", "west": "oeffnung"})
    m.quader([16, 4.9, 4.9], [19, 11.1, 11.1], "warn")
    m.quader([2, 11, 6.6], [9, 13, 8.4], {"alle": "schwarz", "east": "linse", "west": "linse"})
    m.quader([9.5, 0.5, 7], [12, 5, 9], "griff", ("z", -22.5, [10.7, 5, 8]))
    m.quader([17.5, 1.5, 7], [19.5, 5, 9], "griff")
    m.quader([7.5, 3.5, 7.6], [8, 5, 8.4], "schwarz")
    disp = {
        "thirdperson_righthand": {"rotation": [0, 90, 0], "translation": [0, 4, 2], "scale": [0.55, 0.55, 0.55]},
        "thirdperson_lefthand": {"rotation": [0, -90, 0], "translation": [0, 4, 2], "scale": [0.55, 0.55, 0.55]},
        "firstperson_righthand": {"rotation": [0, 90, 0], "translation": [0, 2, 0], "scale": [0.5, 0.5, 0.5]},
        "firstperson_lefthand": {"rotation": [0, -90, 0], "translation": [0, 2, 0], "scale": [0.5, 0.5, 0.5]},
        "gui": {"rotation": [0, 0, -30], "translation": [0, 0, 0], "scale": [0.42, 0.42, 0.42]},
        "ground": {"rotation": [0, 0, 0], "translation": [0, 2, 0], "scale": [0.35, 0.35, 0.35]},
        "fixed": {"rotation": [0, 180, -30], "translation": [0, 0, 0], "scale": [0.45, 0.45, 0.45]},
    }
    return a, m.json(disp)


def lampe_atlas():
    a = Atlas()
    k = kachel((28, 28, 32), 0.05, 701)
    for y in range(0, 16, 2):
        for x in range(0, 16, 2):
            k.set(x + (y // 2) % 2, y, (52, 52, 58))
    a.kachel("koerper", k)
    a.kachel("kopf", kachel((150, 152, 158), 0.05, 702))
    l = Bild(16, 16)
    l.rechteck(0, 0, 16, 16, (120, 122, 128))
    l.ellipse(8, 8, 7, 7, (250, 244, 200))
    l.ellipse(8, 8, 4.5, 4.5, (255, 252, 230))
    l.ellipse(8, 8, 1.6, 1.6, (255, 230, 140))
    a.kachel("linse", l)
    a.kachel("knopf", kachel((170, 30, 26), 0.05, 703))
    a.kachel("schwarz", kachel((18, 18, 20), 0.05, 704))
    return a


def taschenlampe():
    a = lampe_atlas()
    m = Modell(a, "items/waffenpack/taschenlampe")
    m.quader([2, 6.6, 6.6], [12.5, 9.4, 9.4], {"alle": "koerper", "west": "schwarz"})
    m.quader([12.5, 6.2, 6.2], [13.5, 9.8, 9.8], "kopf")
    m.quader([13.5, 5.4, 5.4], [16, 10.6, 10.6], {"alle": "kopf", "east": "linse"})
    m.quader([1.4, 7, 7], [2, 9, 9], "schwarz")
    m.quader([8, 9.4, 7.4], [9.6, 9.9, 8.6], "knopf")
    m.quader([4, 9.4, 8.1], [8, 9.7, 8.7], "kopf")
    disp = {
        "thirdperson_righthand": {"rotation": [0, 90, 0], "translation": [0, 2.5, 1.5], "scale": [0.6, 0.6, 0.6]},
        "thirdperson_lefthand": {"rotation": [0, -90, 0], "translation": [0, 2.5, 1.5], "scale": [0.6, 0.6, 0.6]},
        "firstperson_righthand": {"rotation": [0, 90, 0], "translation": [0, 2.5, 0], "scale": [0.55, 0.55, 0.55]},
        "firstperson_lefthand": {"rotation": [0, -90, 0], "translation": [0, 2.5, 0], "scale": [0.55, 0.55, 0.55]},
        "gui": {"rotation": [0, 0, -30], "translation": [0, 0, 0], "scale": [1.25, 1.25, 1.25]},
        "ground": {"rotation": [0, 0, 0], "translation": [0, 2, 0], "scale": [0.5, 0.5, 0.5]},
        "fixed": {"rotation": [0, 180, 0], "translation": [0, 0, 0], "scale": [1, 1, 1]},
    }
    return a, m.json(disp)
