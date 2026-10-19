"""Backrooms als Datenpaket fuer Minecraft Java 26.2 (Namensraum "br").

Die Backrooms liegen in einer eigenen, leeren Dimension (br:backrooms) ohne
Himmel und ohne Tageslicht. Beim ersten Laden des Datenpakets werden die fuenf
Level und das Finale dort gebaut. /trigger start bringt den Spieler hinein.
In der Dimension ist man im Abenteuermodus; die wichtigsten Waende sind aus
Bloecken, die man auch im Ueberlebensmodus nicht abbauen kann.
"""

import json
import math
import os
import random
import sys
from collections import deque

HIER = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HIER))
import modelle  # noqa: E402

DIM = "br:backrooms"
B = 64
BAU_VERSION = 1
FINALE = 5
ANZAHL_LEVEL = 5
WARDEN_LEBEN = 3
AUFSTIEG = 100
NACHSCHUB_TAKT = 120
NS = "waffenpack"

LEVEL = {
    0: dict(x=-120, z=-80, w=61, d=61, h=5),
    1: dict(x=-40, z=-80, w=61, d=61, h=7),
    2: dict(x=40, z=-80, w=52, d=52, h=4),
    3: dict(x=-120, z=10, w=61, d=61, h=5),
    4: dict(x=-40, z=10, w=61, d=61, h=4),
    5: dict(x=40, z=10, w=35, d=35, h=12, r=17),
}
X0 = min(g["x"] for g in LEVEL.values()) - 4
Z0 = min(g["z"] for g in LEVEL.values()) - 4
X1 = max(g["x"] + g["w"] for g in LEVEL.values()) + 4
Z1 = max(g["z"] + g["d"] for g in LEVEL.values()) + 4

# Bloecke
HUELLE = "reinforced_deepslate"
L0_WAND, L0_BODEN, L0_DECKE = "structure_block[mode=save]", "structure_block[mode=data]", "structure_block[mode=load]"
LAMPE = "structure_block[mode=corner]"
L3_WAND, L3_BODEN = "test_block[mode=start]", "test_block[mode=log]"
L4_WAND, L4_BODEN = "test_block[mode=fail]", "test_block[mode=accept]"
KISTE = "jigsaw[orientation=north_up]"
METALL = "reinforced_deepslate"

LEVER = {1: "east", 2: "west", 3: "south", 4: "north"}       # alte Hebel-Richtungen
SCHILD = {2: "north", 3: "south", 4: "west", 5: "east"}


def jt(obj):
    return json.dumps(obj, ensure_ascii=False, separators=(",", ":"))


def snbt(obj):
    if isinstance(obj, dict):
        return "{" + ",".join("%s:%s" % (k, snbt(v)) for k, v in obj.items()) + "}"
    if isinstance(obj, list):
        return "[" + ",".join(snbt(v) for v in obj) + "]"
    if isinstance(obj, bool):
        return "true" if obj else "false"
    if isinstance(obj, str):
        return json.dumps(obj, ensure_ascii=False)
    return str(obj)


def fill(x0, y0, z0, x1, y1, z1, block, extra=""):
    return ("fill %d %d %d %d %d %d %s %s" % (x0, y0, z0, x1, y1, z1, block, extra)).strip()


def gateway(x, y, z, ziel):
    return ("setblock %d %d %d end_gateway{exit_portal:[I;%d,%d,%d],exact_teleport:1b,Age:1000L}"
            % (x, y, z, ziel[0], ziel[1], ziel[2]))


def schild(x, y, z, richtung, zeilen):
    zeilen = list(zeilen) + [""] * (4 - len(zeilen))
    return "setblock %d %d %d dark_oak_wall_sign[facing=%s]{front_text:{messages:%s}}" % (
        x, y, z, SCHILD[richtung], snbt(zeilen))


def hebel_block(meta, an=False):
    return "lever[face=wall,facing=%s,powered=%s]" % (LEVER[meta], "true" if an else "false")


def licht(x, y, z, stufe=15):
    return "setblock %d %d %d light[level=%d]" % (x, y, z, stufe)


def huelle(g):
    x0, z0, x1, z1 = g["x"] - 1, g["z"] - 1, g["x"] + g["w"], g["z"] + g["d"]
    y0, y1 = B - 1, B + g["h"] + 2
    return [fill(x0, y0, z0, x1, y0, z1, HUELLE), fill(x0, y1, z0, x1, y1, z1, HUELLE),
            fill(x0, y0, z0, x1, y1, z0, HUELLE), fill(x0, y0, z1, x1, y1, z1, HUELLE),
            fill(x0, y0, z0, x0, y1, z1, HUELLE), fill(x1, y0, z0, x1, y1, z1, HUELLE)]


def boden_decke(g, boden, decke):
    x0, z0, x1, z1 = g["x"], g["z"], g["x"] + g["w"] - 1, g["z"] + g["d"] - 1
    return [fill(x0, B, z0, x1, B, z1, boden), fill(x0, B + g["h"] + 1, z0, x1, B + g["h"] + 1, z1, decke)]


def labyrinth(n, seed, extra):
    r = random.Random(seed)
    besucht = {(0, 0)}
    stapel = [(0, 0)]
    offen = set()
    while stapel:
        i, jj = stapel[-1]
        nb = [(i + di, jj + dj) for di, dj in ((1, 0), (-1, 0), (0, 1), (0, -1))
              if 0 <= i + di < n and 0 <= jj + dj < n and (i + di, jj + dj) not in besucht]
        if not nb:
            stapel.pop()
            continue
        k = r.choice(nb)
        offen.add(tuple(sorted(((i, jj), k))))
        besucht.add(k)
        stapel.append(k)
    for i in range(n):
        for jj in range(n):
            for k in ((i + 1, jj), (i, jj + 1)):
                if k[0] < n and k[1] < n and r.random() < extra:
                    offen.add(tuple(sorted(((i, jj), k))))
    return offen


class Raster:
    def __init__(self, g, zelle, seed, extra):
        self.g, self.zelle = g, zelle
        self.n = (g["w"] - 1) // zelle
        self.offen = labyrinth(self.n, seed, extra)

    def innen(self, i, jj):
        x = self.g["x"] + i * self.zelle + 1
        z = self.g["z"] + jj * self.zelle + 1
        return x, z, x + self.zelle - 2, z + self.zelle - 2

    def mitte(self, i, jj):
        x0, z0, x1, z1 = self.innen(i, jj)
        return (x0 + x1) // 2, (z0 + z1) // 2

    def kante_offen(self, a, b):
        return tuple(sorted((a, b))) in self.offen

    def bauen(self, material):
        g, n = self.g, self.n
        bef = [fill(g["x"], B + 1, g["z"], g["x"] + g["w"] - 1, B + g["h"], g["z"] + g["d"] - 1, material)]
        for i in range(n):
            for jj in range(n):
                x0, z0, x1, z1 = self.innen(i, jj)
                bef.append(fill(x0, B + 1, z0, x1, B + g["h"], z1, "air"))
        for (a, b) in sorted(self.offen):
            (i, jj), (i2, j2) = a, b
            x0, z0, x1, z1 = self.innen(i, jj)
            if i2 > i:
                bef.append(fill(x1 + 1, B + 1, z0, x1 + 1, B + g["h"], z1, "air"))
            else:
                bef.append(fill(x0, B + 1, z1 + 1, x1, B + g["h"], z1 + 1, "air"))
        return bef

    def saal(self, i, jj):
        for a, b in (((i, jj), (i + 1, jj)), ((i, jj + 1), (i + 1, jj + 1)), ((i, jj), (i, jj + 1)),
                     ((i + 1, jj), (i + 1, jj + 1))):
            self.offen.add(tuple(sorted((a, b))))
        x0, z0, _, _ = self.innen(i, jj)
        _, _, x1, z1 = self.innen(i + 1, jj + 1)
        return fill(x0, B + 1, z0, x1, B + self.g["h"], z1, "air")

    def abstaende(self, start=(0, 0)):
        d = {start: 0}
        q = deque([start])
        while q:
            i, jj = q.popleft()
            for k in ((i + 1, jj), (i - 1, jj), (i, jj + 1), (i, jj - 1)):
                if k not in d and 0 <= k[0] < self.n and 0 <= k[1] < self.n and self.kante_offen((i, jj), k):
                    d[k] = d[(i, jj)] + 1
                    q.append(k)
        return d

    def geschlossene_seite(self, i, jj):
        x0, z0, x1, z1 = self.innen(i, jj)
        cx, cz = self.mitte(i, jj)
        seiten = []
        if jj == 0 or not self.kante_offen((i, jj), (i, jj - 1)):
            seiten.append((cx, z0, 3, 3))
        if jj == self.n - 1 or not self.kante_offen((i, jj), (i, jj + 1)):
            seiten.append((cx, z1, 2, 4))
        if i == 0 or not self.kante_offen((i, jj), (i - 1, jj)):
            seiten.append((x0, cz, 5, 1))
        if i == self.n - 1 or not self.kante_offen((i, jj), (i + 1, jj)):
            seiten.append((x1, cz, 4, 2))
        return seiten[0] if seiten else None


def marke(x, y, z, *tags):
    return ("summon marker %.1f %d %.1f {Tags:[%s]}" % (x + 0.5, y, z + 0.5,
                                                          ",".join('"%s"' % t for t in ("br_sys",) + tags)))


def weit_verteilt(kandidaten, anzahl, mindest):
    gew = []
    for k in kandidaten:
        if all(abs(k[0] - g[0]) + abs(k[1] - g[1]) >= mindest for g in gew):
            gew.append(k)
        if len(gew) == anzahl:
            break
    return gew


def lampe(bef, x, y_decke, z, lampen):
    """Leuchtpanel in der Decke, darunter ein unsichtbarer Lichtblock."""
    bef.append("setblock %d %d %d %s" % (x, y_decke, z, LAMPE))
    bef.append(licht(x, y_decke - 1, z))
    lampen.append((x, y_decke, z))


# ---------------------------------------------------------------------------
# Monster
# ---------------------------------------------------------------------------

def monster_nbt(name, anzeige, leben, tempo, schaden):
    return ("{CustomName:%s,Tags:[\"br_mob\",\"br_%s\"],Silent:1b,PersistenceRequired:1b,CanPickUpLoot:0b,"
            "CanBreakDoors:0b,IsBaby:0b,DeathLootTable:\"minecraft:empty\","
            "equipment:{head:{id:\"minecraft:diamond_hoe\",count:1,components:{\"minecraft:item_model\":\"%s:%s_a\"}}},"
            "drop_chances:{head:0.0f},"
            "active_effects:[{id:\"minecraft:invisibility\",amplifier:0b,duration:-1,show_particles:0b}],"
            "attributes:[{id:\"minecraft:max_health\",base:%d},{id:\"minecraft:movement_speed\",base:%s},"
            "{id:\"minecraft:follow_range\",base:48},{id:\"minecraft:attack_damage\",base:%d},"
            "{id:\"minecraft:spawn_reinforcements\",base:0},{id:\"minecraft:knockback_resistance\",base:0.3}],"
            "Health:%d.0f}") % (snbt(anzeige), name, NS, name, leben, tempo, schaden, leben)


SMILER = monster_nbt("smiler", "Smiler", 80, "0.28", 8)
HOUND = monster_nbt("hound", "Hound", 60, "0.34", 6)
HAUTDIEB = monster_nbt("hautdieb", "Hautdieb", 100, "0.32", 10)
PARTY = monster_nbt("partygaenger", "Partygänger", 70, "0.31", 8)
FACELING = monster_nbt("faceling", "Faceling", 90, "0.29", 9)
MONSTERARTEN = ["smiler", "hound", "hautdieb", "partygaenger", "faceling"]

WARDEN = ('{Tags:["br_mob","br_warden"],PersistenceRequired:1b,CustomName:"Warden",'
          'attributes:[{id:"minecraft:max_health",base:1000},{id:"minecraft:knockback_resistance",base:1}],'
          'Health:1000.0f,Brain:{memories:{"minecraft:dig_cooldown":{value:{},ttl:2147483647L}}}}')


def zombie(x, y, z, nbt):
    return "summon zombie %d %d %d %s" % (x, y, z, nbt)


# ---------------------------------------------------------------------------
# Level
# ---------------------------------------------------------------------------

def level0():
    g = LEVEL[0]
    bef = huelle(g) + boden_decke(g, L0_BODEN, L0_DECKE)
    ras = Raster(g, 4, 11, 0.30)
    r = random.Random(12)
    saele = [ras.saal(r.randrange(1, ras.n - 2), r.randrange(1, ras.n - 2)) for _ in range(6)]
    bef += ras.bauen(L0_WAND) + saele
    lampen, dunkel = [], []
    for i in range(ras.n):
        for jj in range(ras.n):
            cx, cz = ras.mitte(i, jj)
            if r.random() < 0.7 or (i, jj) == (0, 0):
                lampe(bef, cx, B + g["h"] + 1, cz, lampen)
            else:
                dunkel.append((i, jj))
    d = ras.abstaende()
    start = ras.mitte(0, 0)
    weit = sorted(d, key=lambda k: -d[k])
    ausgang = weit[0]
    maxd = d[ausgang]
    falsch = [k for k in weit if 0.45 * maxd <= d[k] <= 0.8 * maxd
              and abs(k[0] - ausgang[0]) + abs(k[1] - ausgang[1]) >= 4]
    falsch = weit_verteilt(falsch, 2, 4)
    ziele = []
    for zelle, ziel in [(ausgang, 1)] + [(f, 0) for f in falsch]:
        cx, cz = ras.mitte(*zelle)
        ziele.append((cx, B + 1, cz, ziel))
        seite = ras.geschlossene_seite(*zelle)
        if seite:
            bef.append(schild(seite[0], B + 3, seite[1], seite[2],
                              ["", {"text": "NOTAUSGANG", "color": "dark_green", "bold": True}, "→ Level 1"]))
        if (cx, B + g["h"] + 1, cz) not in lampen:
            lampe(bef, cx, B + g["h"] + 1, cz, lampen)
    fern = [k for k in dunkel if d.get(k, 0) >= 5]
    r.shuffle(fern)
    pos = [(ras.mitte(*k)[0], B + 1, ras.mitte(*k)[1]) for k in fern]
    return dict(bef=bef, start=(start[0], B + 1, start[1]), ziele=ziele,
                monster=[p + (SMILER,) for p in pos[:8]], nachschub=(pos[:12], SMILER, 11),
                flacker=r.sample(lampen[1:], 7), decke=L0_DECKE)


def level1():
    g = LEVEL[1]
    x0, z0, h, w, d = g["x"], g["z"], g["h"], g["w"], g["d"]
    bef = huelle(g) + boden_decke(g, "polished_andesite", "smooth_stone")
    bef.append(fill(x0, B + 1, z0, x0 + w - 1, B + h, z0 + d - 1, "air"))
    for zz in (z0 - 1, z0 + d):
        bef.append(fill(x0 - 1, B + 1, zz, x0 + w, B + h, zz, "light_gray_concrete"))
    for xx in (x0 - 1, x0 + w):
        bef.append(fill(xx, B + 1, z0 - 1, xx, B + h, z0 + d, "light_gray_concrete"))
    r = random.Random(21)
    saeulen = [(x0 + 6 + 8 * i, z0 + 6 + 8 * k) for i in range(7) for k in range(7)]
    for px, pz in saeulen:
        bef.append(fill(px, B + 1, pz, px + 1, B + h, pz + 1, "smooth_stone"))
    for _ in range(10):
        if r.random() < 0.5:
            px, pz, l = x0 + r.randrange(8, w - 14), z0 + r.randrange(8, d - 8), r.randrange(6, 12)
            bef.append(fill(px, B + 1, pz, px + l, B + 4, pz, "light_gray_concrete"))
        else:
            px, pz, l = x0 + r.randrange(8, w - 8), z0 + r.randrange(8, d - 14), r.randrange(6, 12)
            bef.append(fill(px, B + 1, pz, px, B + 4, pz + l, "light_gray_concrete"))
    for _ in range(40):
        px, pz = x0 + r.randrange(6, w - 6), z0 + r.randrange(6, d - 6)
        bef.append(fill(px, B + 1, pz, px + r.randrange(0, 2), B + r.randrange(1, 4), pz + r.randrange(0, 2), KISTE))
    for _ in range(20):
        bef.append("setblock %d %d %d water" % (x0 + r.randrange(2, w - 2), B, z0 + r.randrange(2, d - 2)))
    lampen = []
    for i in range(10):
        for k in range(10):
            if r.random() < 0.7 or (i, k) == (0, 0):
                lampe(bef, x0 + 3 + 6 * i, B + h + 1, z0 + 3 + 6 * k, lampen)
    start = (x0 + 2, B + 1, z0 + 2)
    plaetze = []
    for i in range(6):
        for k in range(6):
            px, pz = x0 + 10 + 8 * i, z0 + 10 + 8 * k
            if abs(px - start[0]) + abs(pz - start[2]) >= 24:
                plaetze.append((px, B + 1, pz))
    r.shuffle(plaetze)
    for (px, py, pz) in plaetze[:14]:
        bef.append(fill(px - 1, B + 1, pz - 1, px + 1, B + 3, pz + 1, "air"))
    hebel = []
    for qx, qz in ((1, 0), (0, 1), (1, 1)):
        kand = [(px, pz) for px, pz in saeulen
                if (px - x0 >= w // 2) == bool(qx) and (pz - z0 >= d // 2) == bool(qz)
                and abs(px - start[0]) + abs(pz - start[2]) >= 30]
        px, pz = r.choice(kand)
        bef.append(fill(px - 1, B + 1, pz + 2, px + 2, B + 3, pz + 3, "air"))
        hebel.append((px, B + 2, pz + 2, 3))
        bef.append(schild(px + 1, B + 2, pz + 2, 3, ["", {"text": "NOTSTROM", "color": "dark_red", "bold": True},
                                                     "Hebel umlegen"]))
        lampe(bef, px, B + h + 1, pz + 3, lampen)
    ex = (x0 + w - 4, B + 1, z0 + d - 1)
    bef.append(fill(ex[0] - 2, B + 1, ex[2] - 2, ex[0] + 2, B + 3, ex[2], "air"))
    bef.append(fill(ex[0] - 1, B + 1, ex[2], ex[0] - 1, B + 4, ex[2], "smooth_stone"))
    bef.append(fill(ex[0] + 1, B + 1, ex[2], ex[0] + 1, B + 4, ex[2], "smooth_stone"))
    bef.append(fill(ex[0] - 1, B + 4, ex[2], ex[0] + 1, B + 4, ex[2], "smooth_stone"))
    bef.append(schild(ex[0], B + 4, ex[2] - 1, 2, ["", {"text": "AUFZUG", "color": "dark_red", "bold": True},
                                                   "→ Level 2", {"text": "(kein Strom)", "color": "gray"}]))
    lampe(bef, ex[0], B + h + 1, ex[2] - 1, lampen)
    zu = [fill(ex[0], B + 1, ex[2], ex[0], B + 3, ex[2], "iron_block")]
    auf = [fill(ex[0], B + 2, ex[2], ex[0], B + 3, ex[2], "air"), gateway(ex[0], ex[1], ex[2], start_von(2))]
    bef += zu
    bef += ["setblock %d %d %d %s" % (x, y, z, hebel_block(m)) for (x, y, z, m) in hebel]
    return dict(bef=bef, start=start, hebel=hebel, zu=zu, auf=auf, ziele=[],
                monster=[p + (HOUND,) for p in plaetze[:8]], nachschub=(plaetze[:14], HOUND, 11),
                flacker=r.sample(lampen[1:], 8), decke="smooth_stone")


def level2():
    g = LEVEL[2]
    x0, z0, h = g["x"], g["z"], g["h"]
    bef = huelle(g) + boden_decke(g, "polished_deepslate", "deepslate_tiles")
    ras = Raster(g, 3, 31, 0.12)
    bef += ras.bauen(METALL)
    bef.append(fill(x0, B + 3, z0, x0 + g["w"] - 1, B + 3, z0 + g["d"] - 1, "waxed_exposed_cut_copper",
                    "replace " + METALL))
    for zz in range(z0 + 2, z0 + g["d"], 6):
        bef.append(fill(x0, B + h + 1, zz, x0 + g["w"] - 1, B + h + 1, zz, "waxed_oxidized_cut_copper"))
    r = random.Random(32)
    for i in range(ras.n):
        for jj in range(ras.n):
            if r.random() < 0.2 and (i, jj) != (0, 0):
                cx, cz = ras.innen(i, jj)[:2]
                bef.append("setblock %d %d %d redstone_torch" % (cx + r.randrange(2), B + 1, cz + r.randrange(2)))
    d = ras.abstaende()
    s = ras.innen(0, 0)
    start = (s[0], B + 1, s[1])
    weit = sorted(d, key=lambda k: -d[k])
    ausgang = weit[0]
    ex = ras.innen(*ausgang)
    seite = ras.geschlossene_seite(*ausgang)
    if seite:
        bef.append(schild(seite[0], B + 3, seite[1], seite[2],
                          ["", {"text": "WARTUNGSSCHACHT", "color": "gold"}, "→ Level 3"]))
    bef.append("setblock %d %d %d redstone_torch" % (ex[2], B + 1, ex[3]))
    fern = [k for k in d if d[k] >= 6]
    r.shuffle(fern)
    pos = [(ras.innen(*k)[0], B + 1, ras.innen(*k)[1]) for k in fern]
    monster = [p + (HAUTDIEB,) for p in pos[:6]] + [p + (SMILER,) for p in pos[6:8]]
    fallen = []
    kandidaten = sorted((k for k in d if d[k] >= 3 and k != ausgang), key=lambda k: (k[0] * 7 + k[1] * 13) % 17)
    for k in weit_verteilt(kandidaten, 9, 3):
        fx, fz = ras.innen(*k)[:2]
        fallen.append((fx, B + 1, fz))
        bef.append("setblock %d %d %d waxed_exposed_copper_grate" % (fx, B + h + 1, fz))
    return dict(bef=bef, start=start, ziele=[(ex[0], B + 1, ex[1], 3)], monster=monster,
                nachschub=(pos[:12], HAUTDIEB, 10), fallen=fallen, flacker=[])


def level3():
    g = LEVEL[3]
    x0, z0, h, w, d = g["x"], g["z"], g["h"], g["w"], g["d"]
    bef = huelle(g) + boden_decke(g, L3_BODEN, "smooth_quartz")
    bef.append(fill(x0, B + 1, z0, x0 + w - 1, B + h, z0 + d - 1, L3_WAND))
    r = random.Random(51)
    flure = [z0 + 1 + 12 * k for k in range(5)]
    for fz in flure:
        bef.append(fill(x0 + 1, B + 1, fz, x0 + w - 2, B + 3, fz + 2, "air"))
    durchgang = {}
    for k in range(4):
        xs = (x0 + 56, x0 + 58) if k % 2 == 0 else (x0 + 2, x0 + 4)
        durchgang[k] = xs
        bef.append(fill(xs[0], B + 1, flure[k] + 3, xs[1], B + 3, flure[k] + 11, "air"))
    zimmer = []
    for k in range(5):
        reihen = [("A", flure[k] + 4, flure[k] + 6, flure[k] + 3)]
        if k < 4:
            reihen.append(("B", flure[k] + 8, flure[k] + 10, flure[k] + 11))
        else:
            reihen = [("A", flure[k] + 4, flure[k] + 8, flure[k] + 3)]
        for reihe, iz0, iz1, tz in reihen:
            for m in range(12):
                ix0, ix1 = x0 + 5 * m + 1, x0 + 5 * m + 4
                if k < 4 and ix1 >= durchgang[k][0] and ix0 <= durchgang[k][1]:
                    continue
                zimmer.append((reihe, k, m, ix0, iz0, ix1, iz1, ix0 + 2, tz))
    for (reihe, k, m, ix0, iz0, ix1, iz1, tx, tz) in zimmer:
        bef.append(fill(ix0, B + 1, iz0, ix1, B + 3, iz1, "air"))
    # Sockelleiste aus dunklem Holz
    bef.append(fill(x0, B + 1, z0, x0 + w - 1, B + 1, z0 + d - 1, "dark_oak_planks", "replace " + L3_WAND))
    aus = [zz for zz in zimmer if zz[1] == 4 and zz[2] == 11][0]
    hz = [zz for zz in zimmer if zz[1] in (1, 2, 3) and zz[2] not in (0, 11)]
    schalter = r.choice(hz)
    for zz in zimmer:
        reihe, k, m, ix0, iz0, ix1, iz1, tx, tz = zz
        nr = 100 * (k + 1) + 2 * m + (1 if reihe == "A" else 2)
        bef.append(fill(tx, B + 1, tz, tx, B + 2, tz, "air"))
        if zz is aus:
            continue
        facing = "south" if reihe == "A" else "north"
        bef.append("setblock %d %d %d dark_oak_door[facing=%s,half=upper]" % (tx, B + 2, tz, facing))
        bef.append("setblock %d %d %d dark_oak_door[facing=%s,half=lower]" % (tx, B + 1, tz, facing))
        sz, richtung = (tz - 1, 2) if reihe == "A" else (tz + 1, 3)
        bef.append(schild(tx, B + 3, sz, richtung, ["", {"text": "Zimmer %d" % nr, "color": "gold"}]))
        wahl = r.random()
        if wahl < 0.3 and zz is not schalter:
            beute = ('{Items:[{Slot:%db,id:"minecraft:enchanted_golden_apple",count:2},'
                     '{Slot:%db,id:"minecraft:arrow",count:16}]}' % (r.randrange(0, 13), r.randrange(14, 27)))
            bef.append("setblock %d %d %d chest[facing=%s]%s" % (ix1, B + 1, iz0 if reihe == "B" else iz1,
                                                                 "south" if reihe == "B" else "north", beute))
        if wahl > 0.55:
            bef.append("setblock %d %d %d end_rod[facing=up]" % (ix0 + 1, B + 3, (iz0 + iz1) // 2))
            bef.append(licht(ix0 + 1, B + 2, (iz0 + iz1) // 2, 12))
    reihe, k, m, ix0, iz0, ix1, iz1, tx, tz = schalter
    if reihe == "A":
        hebel = [(ix0 + 2, B + 2, iz1, 4)]
        sch = (ix0 + 1, B + 2, iz1, 2)
    else:
        hebel = [(ix0 + 2, B + 2, iz0, 3)]
        sch = (ix0 + 1, B + 2, iz0, 3)
    bef.append(schild(sch[0], sch[1], sch[2], sch[3], ["", {"text": "HAUPTSCHALTER", "color": "dark_red"},
                                                       "öffnet Zimmer 237"]))
    bef.append("setblock %d %d %d end_rod[facing=up]" % (ix0 + 2, B + 3, (iz0 + iz1) // 2))
    bef.append(licht(ix0 + 3, B + 2, (iz0 + iz1) // 2, 13))
    bef += ["setblock %d %d %d %s" % (x, y, z, hebel_block(mm)) for (x, y, z, mm) in hebel]
    reihe, k, m, ix0, iz0, ix1, iz1, tx, tz = aus
    bef.append(schild(tx, B + 3, tz - 1, 2, ["", {"text": "Zimmer 237", "color": "red", "bold": True},
                                             "AUSGANG", {"text": "verschlossen", "color": "gray"}]))
    zu = ["setblock %d %d %d iron_door[facing=south,half=upper,open=false]" % (tx, B + 2, tz),
          "setblock %d %d %d iron_door[facing=south,half=lower,open=false]" % (tx, B + 1, tz)]
    auf = ["setblock %d %d %d iron_door[facing=south,half=upper,open=true]" % (tx, B + 2, tz),
           "setblock %d %d %d iron_door[facing=south,half=lower,open=true]" % (tx, B + 1, tz),
           "playsound minecraft:block.iron_door.open block @a %d %d %d 2 0.8" % (tx, B + 1, tz)]
    bef += zu
    cx, cz = tx, (iz0 + iz1) // 2 + 1
    bef.append("setblock %d %d %d end_rod[facing=up]" % (cx + 1, B + 3, cz))
    bef.append(licht(cx - 1, B + 2, cz, 12))
    for fz in flure:
        for xx in range(x0 + 3, x0 + w - 3, 6):
            bef.append("setblock %d %d %d wall_torch[facing=south]" % (xx, B + 3, fz))
    lampen = []
    for fz in flure:
        for xx in range(x0 + 6, x0 + w - 3, 12):
            lampe(bef, xx, B + 4, fz + 1, lampen)
    start = (x0 + 2, B + 1, z0 + 2)
    flurplaetze = [(xx, B + 1, flure[k] + 1) for k in range(5) for xx in range(x0 + 8, x0 + w - 4, 9)
                   if not (k == 0 and xx < x0 + 30)]
    r.shuffle(flurplaetze)
    zimmerplaetze = [((zz[3] + zz[5]) // 2, B + 1, (zz[4] + zz[6]) // 2) for zz in r.sample(hz, 4)
                     if zz is not schalter]
    monster = [p + (PARTY,) for p in flurplaetze[:7] + zimmerplaetze]
    return dict(bef=bef, start=start, hebel=hebel, zu=zu, auf=auf, ziele=[(cx, B + 1, cz, 4)], monster=monster,
                nachschub=(flurplaetze[:12], PARTY, 13), flacker=r.sample(lampen, 5), decke=L3_WAND)


def level4():
    g = LEVEL[4]
    x0, z0, h = g["x"], g["z"], g["h"]
    bef = huelle(g) + boden_decke(g, L4_BODEN, L0_DECKE)
    ras = Raster(g, 6, 61, 0.45)
    bef += ras.bauen(L4_WAND)
    r = random.Random(62)
    d = ras.abstaende()
    weit = sorted(d, key=lambda k: -d[k])
    ausgang = weit[0]
    hebelzellen = weit_verteilt([k for k in weit[2:] if d[k] >= 4 and ras.geschlossene_seite(*k)], 4, 4)
    lampen = []
    monitore = []
    for i in range(ras.n):
        for jj in range(ras.n):
            ix0, iz0, ix1, iz1 = ras.innen(i, jj)
            cx, cz = ras.mitte(i, jj)
            if r.random() < 0.72 or (i, jj) == (0, 0):
                lampe(bef, cx, B + h + 1, cz, lampen)
            if (i, jj) in [(0, 0), ausgang] + hebelzellen or r.random() > 0.65:
                continue
            seite = r.choice(("n", "s", "w", "o"))
            if seite in ("n", "s"):
                zz = iz0 if seite == "n" else iz1
                dz = 1 if seite == "n" else -1
                bef.append(fill(ix0 + 1, B + 1, zz, ix0 + 3, B + 1, zz, "dark_oak_slab[type=top]"))
                bef.append(fill(ix0, B + 1, zz, ix0, B + 2, zz + dz, "light_gray_wool"))
                bef.append(fill(ix0 + 4, B + 1, zz, ix0 + 4, B + 2, zz + dz, "light_gray_wool"))
                monitore.append((ix0 + 2.5, B + 2, zz + 0.5, 180 if seite == "n" else 0))
            else:
                xx = ix0 if seite == "w" else ix1
                dx = 1 if seite == "w" else -1
                bef.append(fill(xx, B + 1, iz0 + 1, xx, B + 1, iz0 + 3, "dark_oak_slab[type=top]"))
                bef.append(fill(xx, B + 1, iz0, xx + dx, B + 2, iz0, "light_gray_wool"))
                bef.append(fill(xx, B + 1, iz0 + 4, xx + dx, B + 2, iz0 + 4, "light_gray_wool"))
                monitore.append((xx + 0.5, B + 2, iz0 + 2.5, 90 if seite == "w" else -90))
    hebel = []
    for zelle in hebelzellen:
        sx, sz, richtung, meta = ras.geschlossene_seite(*zelle)
        hebel.append((sx, B + 2, sz, meta))
        bef.append("setblock %d %d %d %s" % (sx, B + 2, sz, hebel_block(meta)))
        bef.append(schild(sx, B + 3, sz, richtung, ["", {"text": "SICHERUNG", "color": "dark_red", "bold": True},
                                                    "einschalten"]))
    cx, cz = ras.mitte(*ausgang)
    seite = ras.geschlossene_seite(*ausgang)
    if seite:
        bef.append(schild(seite[0], B + 3, seite[1], seite[2],
                          ["", {"text": "AUFZUG", "color": "dark_aqua", "bold": True}, "→ ???",
                           {"text": "4 Sicherungen nötig", "color": "gray"}]))
    zu = [fill(cx, B + 1, cz, cx, B + 2, cz, "iron_block")]
    auf = [fill(cx, B + 2, cz, cx, B + 2, cz, "air"), gateway(cx, B + 1, cz, start_von(FINALE))]
    bef += zu
    s = ras.mitte(0, 0)
    fern = [k for k in d if d[k] >= 4 and k not in hebelzellen and k != ausgang]
    r.shuffle(fern)
    pos = [(ras.mitte(*k)[0], B + 1, ras.mitte(*k)[1]) for k in fern]
    monster = [p + (FACELING,) for p in pos[:6]] + [p + (HOUND,) for p in pos[6:10]]
    for (mx, my, mz, yaw) in monitore:
        bef.append('summon item_display %.1f %.2f %.1f {Tags:["br_sys"],Rotation:[%df,0f],'
                   'item:{id:"minecraft:stick",count:1,components:{"minecraft:item_model":"%s:monitor"}},'
                   'transformation:{left_rotation:[0f,0f,0f,1f],right_rotation:[0f,0f,0f,1f],translation:[0f,0f,0f],'
                   'scale:[0.8f,0.8f,0.8f]},brightness:{sky:0,block:12}}' % (mx, my - 0.15, mz, yaw, NS))
    return dict(bef=bef, start=(s[0], B + 1, s[1]), hebel=hebel, zu=zu, auf=auf, ziele=[], monster=monster,
                nachschub=(pos[:12], FACELING, 12), flacker=r.sample(lampen[1:], 6), decke=L0_DECKE)


def arena():
    g = LEVEL[FINALE]
    rr, h = g["r"], g["h"]
    ax, az = g["x"] + rr, g["z"] + rr
    bef = huelle(g)
    bef.append(fill(g["x"], B, g["z"], g["x"] + g["w"] - 1, B + h + 1, g["z"] + g["d"] - 1, "deepslate_tiles"))
    for dz in range(-rr, rr + 1):
        w = int(math.sqrt(rr * rr - dz * dz))
        bef.append(fill(ax - w, B, az + dz, ax + w, B, az + dz, "sculk"))
        bef.append(fill(ax - w, B + 1, az + dz, ax + w, B + h, az + dz, "air"))
    rnd = random.Random(41)
    for _ in range(160):
        a = rnd.uniform(0, 2 * math.pi)
        x, z = ax + int(round((rr + 0.6) * math.cos(a))), az + int(round((rr + 0.6) * math.sin(a)))
        bef.append("setblock %d %d %d sculk" % (x, B + rnd.randrange(1, h + 1), z))
    for _ in range(80):
        a, d = rnd.uniform(0, 2 * math.pi), rnd.uniform(0, rr - 1)
        bef.append("setblock %d %d %d sculk" % (ax + int(d * math.cos(a)), B + h + 1, az + int(d * math.sin(a))))
    for _ in range(12):
        a, d = rnd.uniform(0, 2 * math.pi), rnd.uniform(4, rr - 2)
        x, z = ax + int(d * math.cos(a)), az + int(d * math.sin(a))
        bef.append("setblock %d %d %d sculk_catalyst" % (x, B, z))
        bef.append(licht(x, B + 1, z, 8))
    for _ in range(8):
        a, d = rnd.uniform(0, 2 * math.pi), rnd.uniform(5, rr - 3)
        bef.append("setblock %d %d %d sculk_shrieker[can_summon=false]" % (ax + int(d * math.cos(a)), B + 1,
                                                                         az + int(d * math.sin(a))))
    for _ in range(14):
        a = rnd.uniform(0, 2 * math.pi)
        x, z = ax + int(round((rr - 1) * math.cos(a))), az + int(round((rr - 1) * math.sin(a)))
        bef.append("setblock %d %d %d soul_lantern" % (x, B + 1, z))
    for dx in range(-2, 3):
        for dz in range(-2, 3):
            if max(abs(dx), abs(dz)) == 2:
                bef.append("setblock %d %d %d sculk_catalyst" % (ax + dx, B, az + dz))
    return dict(bef=bef, start=(ax, B + 1, az + rr - 3), ziele=[], monster=[], flacker=[])


BAUER = [level0, level1, level2, level3, level4, arena]
_CACHE = {}


def level(lv):
    if lv not in _CACHE:
        _CACHE[lv] = BAUER[lv]()
    return _CACHE[lv]


def start_von(lv):
    return level(lv)["start"]


def region(lv):
    g = LEVEL[lv]
    return "x=%d,y=%d,z=%d,dx=%d,dy=%d,dz=%d" % (g["x"], B, g["z"], g["w"] - 1, g["h"] + 1, g["d"] - 1)


GANZ = "x=%d,y=%d,z=%d,dx=%d,dy=30,dz=%d" % (X0, B - 4, Z0, X1 - X0, Z1 - Z0)


# ---------------------------------------------------------------------------
# Datenpaket
# ---------------------------------------------------------------------------

def titel(sel, text, farbe, unter):
    return ["title %s times 10 80 25" % sel,
            "title %s subtitle %s" % (sel, jt({"text": unter, "color": "gray", "italic": True})),
            "title %s title %s" % (sel, jt({"text": text, "color": farbe, "bold": True}))]


INFO = {
    0: ("LEVEL 0", "yellow", "Die gelben Räume – finde den Notausgang", "minecraft:block.portal.ambient"),
    1: ("LEVEL 1", "gray", "Die Lagerhalle – Notstrom einschalten", "minecraft:ambient.cave"),
    2: ("LEVEL 2", "dark_red", "Die Rohrtunnel – nimm die Taschenlampe", "minecraft:block.fire.extinguish"),
    3: ("LEVEL 3", "gold", "Das Hotel – finde den Hauptschalter", "minecraft:entity.witch.ambient"),
    4: ("LEVEL 4", "aqua", "Das Büro – 4 Sicherungen einschalten", "minecraft:block.note_block.bell"),
    5: ("FINALE", "dark_aqua", "Deep Dark – sei leise …", "minecraft:entity.warden.ambient"),
}
RAETSEL = {1: ("Notstrom", "Notstrom an – der Aufzug fährt!"),
           3: ("Hauptschalter", "Ein Schloss klickt – Zimmer 237 ist offen."),
           4: ("Sicherungen", "Alle Sicherungen drin – der Aufzug fährt!")}


def bau_teile(p):
    """Bau in Teilen (je ein Tick), damit der Server nicht haengt."""
    alle = []
    for lv in range(len(BAUER)):
        info = level(lv)
        alle += info["bef"]
        for (x, y, z, ziel) in info.get("ziele", []):
            alle.append(gateway(x, y, z, start_von(ziel)))
    for lv in range(ANZAHL_LEVEL):
        for (x, y, z) in level(lv)["nachschub"][0]:
            alle.append(marke(x, y, z, "br_sp", "br_sp%d" % lv))
    for k, (x, y, z) in enumerate(level(2)["fallen"]):
        alle.append(marke(x, y, z, "br_dampf", "br_dg%d" % (k % 3)))
    teile = [alle[i:i + 250] for i in range(0, len(alle), 250)]
    for i, t in enumerate(teile):
        p.fn("br:bau/teil_%d" % i, *t)
    z = ["scoreboard players add #bau br 1"]
    for i in range(len(teile)):
        z.append("execute if score #bau br matches %d in %s run function br:bau/teil_%d" % (i + 1, DIM, i))
    z += ["execute if score #bau br matches ..%d run return run schedule function br:bau/schritt 1t" % (len(teile) - 1),
          "scoreboard players set #gebaut br %d" % BAU_VERSION,
          "tellraw @a %s" % jt({"text": "Die Backrooms sind bereit. Klicke [START] oder tippe /trigger start.",
                                "color": "gold"})]
    p.fn("br:bau/schritt", *z)
    ecken = [(X0, Z0), (X1, Z0), (X0, Z1), (X1, Z1), ((X0 + X1) // 2, (Z0 + Z1) // 2)]
    p.fn("br:bau/start",
         "execute in %s run forceload add %d %d %d %d" % (DIM, X0, Z0, X1, Z1),
         "scoreboard players set #bau br 0",
         "tellraw @a %s" % jt({"text": "Die Backrooms werden gebaut …", "color": "gray", "italic": True}),
         "schedule function br:bau/warten 2s")
    p.fn("br:bau/warten",
         *["execute in %s unless loaded %d %d %d run return run schedule function br:bau/warten 1s" % (DIM, x, B, z)
           for x, z in ecken],
         "function br:bau/schritt")
    return len(teile)


def ketten(p):
    S = "br"
    # Laden
    p.fn("br:laden",
         "scoreboard objectives add br dummy",
         "scoreboard objectives add start trigger",
         "scoreboard objectives add br_tode deathCount",
         "scoreboard objectives add br_rx dummy",
         "scoreboard objectives add br_ry dummy",
         "scoreboard objectives add br_rz dummy",
         "scoreboard objectives add br_rd dummy",
         "scoreboard objectives add br_nah dummy",
         "scoreboard objectives add br_cd dummy",
         "gamerule keep_inventory true",
         "execute unless score #gebaut br matches %d run function br:bau/start" % BAU_VERSION)

    # Start
    lampe = "give @s carrot_on_a_stick[%s]" % ITEM_LAMPE
    s0 = start_von(0)
    p.fn("br:start",
         "scoreboard players set @s start 0",
         "execute unless score #gebaut br matches %d run return run tellraw @s %s"
         % (BAU_VERSION, jt({"text": "Die Backrooms werden noch gebaut – bitte einen Moment warten.", "color": "gray"})),
         "execute unless dimension %s run function br:merken" % DIM,
         "function br:zuruecksetzen",
         "clear @s *[custom_data~{wp:9}]",
         lampe,
         "effect give @s blindness 2 0 true",
         "execute in %s run tp @s %d.5 %d %d.5 -45 0" % (DIM, s0[0], s0[1], s0[2]),
         "playsound minecraft:entity.enderman.teleport player @s ~ ~ ~ 1 0.5",
         "tellraw @s %s" % jt({"text": "Du rutschst durch den Boden der Realität …", "color": "gold", "italic": True}),
         "tellraw @s %s" % jt({"text": "Fünf Level und ein Finale. Die Wände sind unzerstörbar.", "color": "gray"}))
    p.fn("br:merken",
         "execute store result score @s br_rx run data get entity @s Pos[0]",
         "execute store result score @s br_ry run data get entity @s Pos[1]",
         "execute store result score @s br_rz run data get entity @s Pos[2]",
         "scoreboard players set @s br_rd 0",
         "execute if dimension minecraft:the_nether run scoreboard players set @s br_rd 1",
         "execute if dimension minecraft:the_end run scoreboard players set @s br_rd 2")
    z = ["execute in %s run kill @e[tag=br_mob,%s]" % (DIM, GANZ),
         "execute in %s run kill @e[type=item,%s]" % (DIM, GANZ),
         "scoreboard players set #wauf br 0", "scoreboard players set #wsp br 0", "scoreboard players set #wl br 0",
         "scoreboard players set #sieg br 0"]
    z += ["scoreboard players set #f%d br 0" % lv for lv in range(ANZAHL_LEVEL + 1)]
    z += ["scoreboard players set #auf%d br 0" % lv for lv in RAETSEL]
    p.fn("br:zuruecksetzen", *z)

    # Heimweg (nach dem Sieg): zurueck an die Stelle, an der /trigger start benutzt wurde
    p.fn("br:heimweg",
         "execute store result storage br:tmp x int 1 run scoreboard players get @s br_rx",
         "execute store result storage br:tmp y int 1 run scoreboard players get @s br_ry",
         "execute store result storage br:tmp z int 1 run scoreboard players get @s br_rz",
         "execute if score @s br_rd matches 1 run return run function br:heimweg_ne with storage br:tmp",
         "execute if score @s br_rd matches 2 run return run function br:heimweg_end with storage br:tmp",
         "function br:heimweg_ow with storage br:tmp")
    for kurz, dim in (("ow", "minecraft:overworld"), ("end", "minecraft:the_end"), ("ne", "minecraft:the_nether")):
        p.fn("br:heimweg_%s" % kurz, "$execute in %s run tp @s $(x) $(y) $(z)" % dim)

    # Tick
    p.fn("br:tick",
         "scoreboard players enable @a start",
         "execute as @a[scores={start=1..}] at @s run function br:start",
         "execute as @a[gamemode=survival] at @s if dimension %s run function br:abenteuer_an" % DIM,
         "execute as @a[tag=br_adv] at @s unless dimension %s run function br:abenteuer_aus" % DIM,
         "execute as @e[type=player,scores={br_tode=1..}] run function br:wiederbelebt",
         "execute if score #gebaut br matches %d in %s positioned 0 %d 0 run function br:innen" % (BAU_VERSION, DIM, B))
    p.fn("br:abenteuer_an", "gamemode adventure @s", "tag @s add br_adv")
    p.fn("br:abenteuer_aus", "gamemode survival @s", "tag @s remove br_adv")
    p.fn("br:wiederbelebt", "scoreboard players set @s br_tode 0",
         "execute at @s if dimension %s run effect give @s resistance 5 4 true" % DIM,
         "execute at @s if dimension %s run effect give @s regeneration 5 2 true" % DIM)

    innen = [
        "scoreboard players add #t br 1", "execute if score #t br matches 16.. run scoreboard players set #t br 0",
        "scoreboard players add #t2 br 1", "execute if score #t2 br matches 300.. run scoreboard players set #t2 br 0",
        "scoreboard players add #t3 br 1",
        "execute if score #t3 br matches %d.. run scoreboard players set #t3 br 0" % NACHSCHUB_TAKT,
        "scoreboard players add #t4 br 1", "execute if score #t4 br matches 60.. run scoreboard players set #t4 br 0",
        "scoreboard players set #lv br -1",
    ]
    for lv in range(ANZAHL_LEVEL + 1):
        innen += ["tag @a remove br_in%d" % lv, "tag @a[%s] add br_in%d" % (region(lv), lv),
                  "execute if entity @a[tag=br_in%d] run scoreboard players set #lv br %d" % (lv, lv),
                  "execute if score #f%d br matches 0 if entity @a[tag=br_in%d] run function br:level/%d/betreten"
                  % (lv, lv, lv)]
    innen += ["function br:raetsel", "function br:atmo", "function br:monster", "function br:warden"]
    p.fn("br:innen", *innen)

    for lv in range(ANZAHL_LEVEL + 1):
        info = level(lv)
        t, farbe, ut, ton = INFO[lv]
        sel = "@a[tag=br_in%d]" % lv
        z = ["scoreboard players set #f%d br 1" % lv] + titel(sel, t, farbe, ut) + [
            "playsound %s ambient %s ~ ~ ~ 1 0.6" % (ton, sel),
            "execute as %s run spawnpoint @s %d %d %d" % ((sel,) + info["start"]),
            "kill @e[tag=br_mob,%s]" % region(lv)]
        z += ["setblock %d %d %d %s" % (x, y, zz, hebel_block(m)) for (x, y, zz, m) in info.get("hebel", [])]
        z += info.get("zu", [])
        if lv in RAETSEL:
            z.append("scoreboard players set #auf%d br 0" % lv)
        if info["monster"]:
            z.append("schedule function br:level/%d/monster 3s" % lv)
        if lv == FINALE:
            z += ["scoreboard players set #wauf br 1", "scoreboard players set #wsp br 0",
                  "scoreboard players set #sieg br 0", "setblock %d %d %d air" % (geo_ax(), B + 1, geo_az())]
        p.fn("br:level/%d/betreten" % lv, *z)
        if info["monster"]:
            p.fn("br:level/%d/monster" % lv,
                 *["execute in %s run %s" % (DIM, zombie(x, y, zz, nbt)) for (x, y, zz, nbt) in info["monster"]])

    # Raetsel
    z = []
    for lv, (wort, meldung) in RAETSEL.items():
        info = level(lv)
        n = len(info["hebel"])
        z.append("scoreboard players set #h%d br 0" % lv)
        for (x, y, zz, m) in info["hebel"]:
            z.append("execute if block %d %d %d lever[powered=true] run scoreboard players add #h%d br 1" % (x, y, zz, lv))
        z.append("execute if score #lv br matches %d if score #auf%d br matches 0 if score #h%d br matches %d.. "
                 "run function br:level/%d/oeffnen" % (lv, lv, lv, n, lv))
        if n > 1:
            z.append("execute if score #t br matches 0 if score #auf%d br matches 0 run title @a[tag=br_in%d] actionbar %s"
                     % (lv, lv, jt([{"text": wort + ": ", "color": "yellow"},
                                    {"score": {"name": "#h%d" % lv, "objective": "br"}, "color": "white"},
                                    {"text": "/%d" % n, "color": "white"}])))
        p.fn("br:level/%d/oeffnen" % lv, *info["auf"],
             "scoreboard players set #auf%d br 1" % lv,
             "execute as @a[tag=br_in%d] at @s run playsound minecraft:block.note_block.pling master @s ~ ~ ~ 1 1.5" % lv,
             "tellraw @a[tag=br_in%d] %s" % (lv, jt({"text": meldung, "color": "green"})))
    p.fn("br:raetsel", *z)

    # Atmosphaere
    z = []
    flacker = []
    for lv in range(ANZAHL_LEVEL):
        info = level(lv)
        for pos in info.get("flacker", []):
            flacker.append((pos, info.get("decke", L0_DECKE)))
    for k, ((x, y, zz), aus) in enumerate(flacker):
        t0 = (k * 37) % 280 + 5
        z.append("execute if score #t2 br matches %d run setblock %d %d %d %s" % (t0, x, y, zz, aus))
        z.append("execute if score #t2 br matches %d run setblock %d %d %d air" % (t0, x, y - 1, zz))
        z.append("execute if score #t2 br matches %d run setblock %d %d %d %s" % (t0 + 3, x, y, zz, LAMPE))
        z.append("execute if score #t2 br matches %d run setblock %d %d %d light[level=15]" % (t0 + 3, x, y - 1, zz))
    z += [
        "execute if score #t2 br matches 120 as @a[tag=br_in0] at @s run playsound minecraft:block.portal.ambient ambient @s ~ ~ ~ 0.25 2",
        "execute if score #t2 br matches 200 as @a[tag=br_in1] at @s run playsound minecraft:ambient.cave ambient @s ~ ~ ~ 0.8 0.7",
        "execute if score #t2 br matches 0 as @a[tag=br_in2] at @s run playsound minecraft:block.fire.extinguish ambient @s ~ ~2 ~3 0.4 0.5",
        "execute if score #t2 br matches 90 as @a[tag=br_in3] at @s run playsound minecraft:entity.witch.ambient ambient @s ~6 ~ ~ 0.6 1.4",
        "execute if score #t2 br matches 210 as @a[tag=br_in3] at @s run playsound minecraft:entity.firework_rocket.twinkle_far ambient @s ~ ~ ~-6 0.6 0.8",
        "execute if score #t2 br matches 60 as @a[tag=br_in4] at @s run playsound minecraft:block.note_block.bell ambient @s ~5 ~ ~ 0.5 1.2",
        "execute if score #t2 br matches 64 as @a[tag=br_in4] at @s run playsound minecraft:block.note_block.bell ambient @s ~5 ~ ~ 0.5 1.2",
        "execute if score #t2 br matches 160 as @a[tag=br_in4] at @s run playsound minecraft:block.note_block.hat ambient @s ~ ~ ~4 0.4 1.6",
        "execute as @a[tag=br_in2] at @s run particle minecraft:cloud ~ ~2.6 ~ 4 0.1 4 0.005 1",
        "execute as @a[tag=br_in0] at @s run particle minecraft:white_ash ~ ~1 ~ 4 2 4 0 4",
        "execute as @a[tag=br_in%d] at @s run particle minecraft:sculk_soul ~ ~1 ~ 6 3 6 0.01 1" % FINALE,
    ]
    for gruppe in range(3):
        bed = "execute if score #lv br matches 2 if score #t4 br matches %d as @e[type=marker,tag=br_dg%d] at @s run " % (
            20 * gruppe, gruppe)
        z += [bed + "particle minecraft:cloud ~ ~ ~ 0.15 1 0.15 0.06 40 force",
              bed + "playsound minecraft:block.fire.extinguish block @a ~ ~ ~ 1 0.6",
              bed + "execute as @a[distance=..1.2] run damage @s 3 minecraft:hot_floor"]
    p.fn("br:atmo", *z)

    # Monster
    z = []
    for name in MONSTERARTEN:
        z.append("execute if score #t br matches 0 run item replace entity @e[tag=br_%s,%s] armor.head with "
                 "diamond_hoe[item_model=\"%s:%s_a\"]" % (name, GANZ, NS, name))
        z.append("execute if score #t br matches 8 run item replace entity @e[tag=br_%s,%s] armor.head with "
                 "diamond_hoe[item_model=\"%s:%s_b\"]" % (name, GANZ, NS, name))
    for name, ton, t0, hoehe in (("smiler", "entity.vex.ambient", 40, 0.5), ("hound", "entity.wolf.growl", 90, 0.5),
                                 ("hautdieb", "entity.villager.no", 150, 0.5),
                                 ("partygaenger", "entity.witch.celebrate", 180, 1.6),
                                 ("faceling", "entity.villager.ambient", 250, 0.4)):
        z.append("execute if score #t2 br matches %d as @e[tag=br_%s,%s] at @s run playsound minecraft:%s hostile @a ~ ~ ~ 1.2 %s"
                 % (t0, name, GANZ, ton, hoehe))
    z += ["execute if score #t3 br matches 1 run function br:nachschub"]
    p.fn("br:monster", *z)
    z = ["scoreboard players set #anz br 0",
         "scoreboard players set @e[type=marker,tag=br_sp,%s] br_nah 0" % GANZ,
         "execute as @a[%s] at @s run scoreboard players set @e[type=marker,tag=br_sp,distance=..14] br_nah 1" % GANZ]
    for lv in range(ANZAHL_LEVEL):
        _, nbt, maximum = level(lv)["nachschub"]
        z.append("execute if score #lv br matches %d run execute store result score #anz br if entity @e[tag=br_mob,%s]"
                 % (lv, region(lv)))
        neu = ("execute if score #lv br matches %d if score #anz br matches ..%d as @e[type=marker,tag=br_sp%d,"
               "scores={br_nah=0},sort=random,limit=1] at @s run " % (lv, maximum - 1, lv))
        z += [neu + "summon zombie ~ ~ ~ " + nbt, neu + "particle minecraft:large_smoke ~ ~1 ~ 0.3 0.8 0.3 0.02 30 force"]
    p.fn("br:nachschub", *z)

    # Warden
    ax, az = geo_ax(), geo_az()
    W = "@e[type=warden,tag=br_warden,%s]" % GANZ
    z = ["execute if score #wauf br matches 1.. run function br:warden_auf",
         "execute if score #wsp br matches 1 if score #sieg br matches 0 unless entity %s run function br:warden_tot" % W,
         "execute if score #sieg br matches 1 as @a[x=%d,y=%d,z=%d,distance=..1.6] run function br:heimweg_start"
         % (ax, B + 1, az),
         "execute if score #sieg br matches 1 run particle minecraft:end_rod %d %d %d 0.2 1.5 0.2 0.02 6 force"
         % (ax, B + 2, az),
         "execute if score #wsp br matches 0 if score #t br matches 0 as @a[tag=br_in%d] at @s run playsound "
         "minecraft:entity.warden.heartbeat hostile @s ~ ~ ~ 1 1" % FINALE]
    p.fn("br:warden", *z)
    blockteile = "minecraft:block{block_state:\"minecraft:sculk\"}"
    p.fn("br:warden_auf",
         "scoreboard players add #wauf br 1",
         "particle %s %d %d %d 0.9 0.1 0.9 0.15 14 force" % (blockteile, ax, B + 1, az),
         "particle minecraft:sculk_soul %d %d %d 0.6 0.4 0.6 0.02 3 force" % (ax, B + 1, az),
         "execute if score #wauf br matches 2 run playsound minecraft:entity.warden.emerge hostile @a[tag=br_in%d] %d %d %d 3 1"
         % (FINALE, ax, B + 1, az),
         "execute if score #wauf br matches 40 run playsound minecraft:entity.warden.roar hostile @a[tag=br_in%d] %d %d %d 3 0.8"
         % (FINALE, ax, B + 1, az),
         "execute if score #wauf br matches %d.. run function br:warden_spawn" % AUFSTIEG)
    p.fn("br:warden_spawn",
         "scoreboard players set #wauf br 0",
         "execute unless score #wl br matches 1.. run scoreboard players set #wl br %d" % WARDEN_LEBEN,
         "summon warden %d %d %d %s" % (ax, B + 1, az, WARDEN),
         "execute as %s at @s run damage @s 0.1 minecraft:player_attack by @p[tag=br_in%d]" % (W, FINALE),
         "scoreboard players set #wsp br 1",
         *titel("@a[tag=br_in%d]" % FINALE, "DER WARDEN", "dark_aqua", "Er sieht dich nicht. Er hört dich."))
    feuer = ('{LifeTime:%d,FireworksItem:{id:"minecraft:firework_rocket",count:1,components:{"minecraft:fireworks":'
             '{explosions:[{shape:"large_ball",colors:[I;3394764,16777215],fade_colors:[I;65535],has_twinkle:true}]}}}}')
    p.fn("br:warden_tot",
         "scoreboard players remove #wl br 1",
         "execute if score #wl br matches 1.. run return run function br:warden_nochmal",
         "scoreboard players set #sieg br 1",
         *titel("@a[tag=br_in%d]" % FINALE, "GESCHAFFT!", "gold", "Du bist aus den Backrooms entkommen"),
         "execute as @a[tag=br_in%d] at @s run playsound minecraft:ui.toast.challenge_complete master @s ~ ~ ~ 1 1" % FINALE,
         "summon firework_rocket %d %d %d %s" % (ax + 3, B + 1, az, feuer % 25),
         "summon firework_rocket %d %d %d %s" % (ax - 3, B + 1, az, feuer % 30),
         "summon firework_rocket %d %d %d %s" % (ax, B + 1, az + 3, feuer % 35),
         "give @a[tag=br_in%d] nether_star[custom_name={text:\"Herz des Wardens\",color:\"aqua\",italic:false}]" % FINALE,
         "tellraw @a[tag=br_in%d] %s" % (FINALE, jt({"text": "In der Mitte der Arena öffnet sich der Weg nach Hause.",
                                                     "color": "aqua"})),
         "setblock %d %d %d crying_obsidian" % (ax, B, az),
         "setblock %d %d %d light[level=15]" % (ax, B + 2, az))
    p.fn("br:warden_nochmal",
         *titel("@a[tag=br_in%d]" % FINALE, "ER LEBT NOCH", "dark_aqua", "Der Warden wird nur noch wütender …"),
         "particle %s %d %d %d 1.2 0.3 1.2 0.2 80 force" % (blockteile, ax, B + 1, az),
         "scoreboard players set #wauf br 60",
         "scoreboard players set #wsp br 0")
    p.fn("br:heimweg_start",
         "effect give @s blindness 1 0 true",
         "playsound minecraft:entity.enderman.teleport player @s ~ ~ ~ 1 1",
         "function br:heimweg",
         "execute at @s run spawnpoint @s ~ ~ ~")


ITEM_LAMPE = ('item_model="%s:taschenlampe",custom_name={text:"Taschenlampe",color:"yellow",italic:false},'
              'unbreakable={},custom_data={wp:9},tooltip_display={hidden_components:["minecraft:unbreakable"]}' % NS)


def geo_ax():
    g = LEVEL[FINALE]
    return g["x"] + g["r"]


def geo_az():
    g = LEVEL[FINALE]
    return g["z"] + g["r"]


def dimension(p):
    p.datei("data/br/dimension_type/backrooms.json", {
        "ambient_light": 0.0,
        "attributes": {
            "minecraft:gameplay/bed_rule": {"can_set_spawn": "never", "can_sleep": "never", "explodes": False},
            "minecraft:gameplay/respawn_anchor_works": False,
            "minecraft:gameplay/sky_light_level": 0.0,
            "minecraft:visual/ambient_light_color": "#1a1a14",
            "minecraft:visual/fog_color": "#0c0b08",
            "minecraft:visual/sky_color": "#000000",
            "minecraft:visual/sky_light_color": "#000000",
            "minecraft:visual/sky_light_factor": 0.0,
            "minecraft:visual/fog_start_distance": 8.0,
            "minecraft:visual/fog_end_distance": 64.0,
        },
        "coordinate_scale": 1.0,
        "has_ceiling": True,
        "has_ender_dragon_fight": False,
        "has_fixed_time": True,
        "has_skylight": False,
        "height": 256,
        "infiniburn": "#minecraft:infiniburn_overworld",
        "logical_height": 256,
        "min_y": 0,
        "monster_spawn_block_light_limit": 0,
        "monster_spawn_light_level": 0,
        "skybox": "none",
        "timelines": "#minecraft:in_nether",
    })
    p.datei("data/br/dimension/backrooms.json", {
        "type": "br:backrooms",
        "generator": {"type": "minecraft:flat", "settings": {
            "biome": "minecraft:the_void", "features": False, "lakes": False,
            "layers": [{"block": "minecraft:air", "height": 1}], "structure_overrides": []}}})


def paket(p):
    dimension(p)
    n = bau_teile(p)
    ketten(p)
    return n
