"""Backrooms: fuenf Level und das Finale gegen den Warden.

bau_befehle(geo)      -> Konsolenbefehle, die die Level bauen (Spawnbereich muss dort liegen)
marken_befehle(geo)   -> Markierungen fuer nachkommende Monster
ketten(geo)           -> Befehlsblock-Ketten (je Liste von Befehlen) fuer die Spiellogik

Die Level liegen weit weg vom Spawnpunkt in der Luft (orte.py), in geschlossenen
Kaesten. Hinein und weiter geht es nur ueber Portale (End-Gateway-Bloecke; in
Eaglercraft stuerzen /tp-Befehle auf Spieler ab, Gateways funktionieren).
In den Backrooms ist man im Abenteuermodus: dort laesst sich nichts abbauen.

Level 0  Die gelben Raeume   Labyrinth, Smiler, falsche Notausgaenge
Level 1  Die Lagerhalle      Hounds, 3 Notstrom-Hebel oeffnen den Aufzug
Level 2  Die Rohrtunnel      enges Labyrinth, Hautdiebe, Dampffallen
Level 3  Das Hotel           lange Flure, Zimmer, Partygaenger, Hauptschalter
Level 4  Das Buero           Labyrinth aus Bueros, Facelings und Hounds, 4 Sicherungen
Finale   Deep Dark           der Warden
"""

import json
import math
import random
from collections import deque

import modelle
import orte
import waffen
from orte import B, LEVEL

STATE = "@e[tag=br_state]"
ANZAHL_LEVEL = 5          # Level 0-4, dazu das Finale (Nummer 5)
FINALE = 5
WARDEN_LEBEN = 3          # so oft muss der Warden besiegt werden
AUFSTIEG = 100            # Ticks, bis der Warden aus dem Boden gestiegen ist
NACHSCHUB_TAKT = 200      # alle 10 Sekunden kann ein neues Monster kommen


def j(obj):
    return json.dumps(obj, ensure_ascii=False, separators=(",", ":"))


def nbt_text(obj):
    return waffen.nbt_string(j(obj))


class Geo:
    """Spawnpunkt (Rueckweg, Steuerung) und Lage aller Level."""

    def __init__(self, sx, sz, oberflaeche_y):
        self.sx, self.sz, self.sy = sx, sz, oberflaeche_y
        self.zustand = (sx - 1, 10, sz)
        a = LEVEL[FINALE]
        self.ax, self.az = a["x"] + a["r"], a["z"] + a["r"]

    def region(self, lv):
        g = LEVEL[lv]
        return "x=%d,y=%d,z=%d,dx=%d,dy=%d,dz=%d" % (g["x"], B, g["z"], g["w"] - 1, g["h"] + 1, g["d"] - 1)


# ---------------------------------------------------------------------------
# Bau-Hilfen
# ---------------------------------------------------------------------------

def fill(x0, y0, z0, x1, y1, z1, block, extra=""):
    return ("fill %d %d %d %d %d %d %s %s" % (x0, y0, z0, x1, y1, z1, block, extra)).strip()


def gateway(x, y, z, ziel):
    return "setblock %d %d %d end_gateway 0 replace {ExactTeleport:1b,Age:1000L,ExitPortal:{X:%d,Y:%d,Z:%d}}" % (
        x, y, z, ziel[0], ziel[1], ziel[2])


def schild(x, y, z, richtung, zeilen):
    """Wandschild; richtung 2=Nord 3=Sued 4=West 5=Ost (Blickrichtung des Schilds)."""
    tags = ",".join("Text%d:%s" % (i + 1, nbt_text(z)) for i, z in enumerate(zeilen))
    return "setblock %d %d %d wall_sign %d replace {%s}" % (x, y, z, richtung, tags)


def huelle(g):
    """Geschlossene Huelle (dunkles Metall) um ein Level: Boden, Decke, vier Waende
    (einzeln, weil ein fill-Befehl hoechstens 32768 Bloecke setzt)."""
    x0, z0, x1, z1 = g["x"] - 1, g["z"] - 1, g["x"] + g["w"], g["z"] + g["d"]
    y0, y1 = B - 1, B + g["h"] + 2
    return [fill(x0, y0, z0, x1, y0, z1, "concrete 15"), fill(x0, y1, z0, x1, y1, z1, "concrete 15"),
            fill(x0, y0, z0, x1, y1, z0, "concrete 15"), fill(x0, y0, z1, x1, y1, z1, "concrete 15"),
            fill(x0, y0, z0, x0, y1, z1, "concrete 15"), fill(x1, y0, z0, x1, y1, z1, "concrete 15")]


def boden_decke(g, boden, decke):
    x0, z0, x1, z1 = g["x"], g["z"], g["x"] + g["w"] - 1, g["z"] + g["d"] - 1
    return [fill(x0, B, z0, x1, B, z1, boden), fill(x0, B + g["h"] + 1, z0, x1, B + g["h"] + 1, z1, decke)]


def labyrinth(n, seed, extra):
    """Zellen-Labyrinth (Tiefensuche) mit zusaetzlich geoeffneten Waenden.
    Rueckgabe: Menge offener Kanten ((i,j),(i2,j2))."""
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
    """Labyrinth auf einem Zellenraster innerhalb eines Levels."""

    def __init__(self, g, zelle, seed, extra):
        self.g, self.zelle = g, zelle
        self.n = (g["w"] - 1) // zelle
        self.offen = labyrinth(self.n, seed, extra)

    def innen(self, i, jj):
        """Innenraum einer Zelle: (x0, z0, x1, z1)."""
        x = self.g["x"] + i * self.zelle + 1
        z = self.g["z"] + jj * self.zelle + 1
        return x, z, x + self.zelle - 2, z + self.zelle - 2

    def mitte(self, i, jj):
        x0, z0, x1, z1 = self.innen(i, jj)
        return (x0 + x1) // 2, (z0 + z1) // 2

    def kante_offen(self, a, b):
        return tuple(sorted((a, b))) in self.offen

    def bauen(self, material):
        g, n, z = self.g, self.n, self.zelle
        bef = [fill(g["x"], B + 1, g["z"], g["x"] + g["w"] - 1, B + g["h"], g["z"] + g["d"] - 1, material)]
        for i in range(n):
            for jj in range(n):
                x0, z0, x1, z1 = self.innen(i, jj)
                bef.append(fill(x0, B + 1, z0, x1, B + g["h"], z1, "air"))
        for (a, b) in self.offen:
            (i, jj), (i2, j2) = a, b
            if i2 > i:
                x0, z0, x1, z1 = self.innen(i, jj)
                bef.append(fill(x1 + 1, B + 1, z0, x1 + 1, B + g["h"], z1, "air"))
            else:
                x0, z0, x1, z1 = self.innen(i, jj)
                bef.append(fill(x0, B + 1, z1 + 1, x1, B + g["h"], z1 + 1, "air"))
        return bef

    def saal(self, i, jj):
        """2x2 Zellen ohne Innenwaende."""
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
        """Eine Wand der Zelle, die nicht offen ist: (x, z, schild_richtung, hebel_meta_aus)."""
        x0, z0, x1, z1 = self.innen(i, jj)
        cx, cz = self.mitte(i, jj)
        seiten = []
        if jj == 0 or not self.kante_offen((i, jj), (i, jj - 1)):
            seiten.append((cx, z0, 3, 3))       # Nordwand, Schild/Hebel zeigen nach Sueden
        if jj == self.n - 1 or not self.kante_offen((i, jj), (i, jj + 1)):
            seiten.append((cx, z1, 2, 4))       # Suedwand
        if i == 0 or not self.kante_offen((i, jj), (i - 1, jj)):
            seiten.append((x0, cz, 5, 1))       # Westwand
        if i == self.n - 1 or not self.kante_offen((i, jj), (i + 1, jj)):
            seiten.append((x1, cz, 4, 2))       # Ostwand
        return seiten[0] if seiten else None


def marke_befehl(x, y, z, *tags):
    return ("summon armor_stand %.1f %d %.1f {Marker:1b,Invisible:1b,NoGravity:1b,Invulnerable:1b,Tags:[%s]}"
            % (x + 0.5, y, z + 0.5, ",".join(("wp_sys",) + tags)))


def weit_verteilt(kandidaten, anzahl, mindest):
    """Waehlt Zellen, die untereinander mindestens 'mindest' Zellen Abstand haben."""
    gew = []
    for k in kandidaten:
        if all(abs(k[0] - g[0]) + abs(k[1] - g[1]) >= mindest for g in gew):
            gew.append(k)
        if len(gew) == anzahl:
            break
    return gew


# ---------------------------------------------------------------------------
# Monster
# ---------------------------------------------------------------------------

def monster_nbt(name, anzeigename, leben, tempo, schaden, extra_effekte=""):
    dmg = modelle.MONSTER_DAMAGE[name][0]
    zombie = "IsBaby:0b,CanBreakDoors:0b," if name != "warden" else ""
    verstaerkung = "{Name:zombie.spawnReinforcements,Base:0d}," if name != "warden" else ""
    return ("{CustomName:%s,Tags:[br_mob,br_%s],Silent:1b,PersistenceRequired:1b,CanPickUpLoot:0b,"
            "DeathLootTable:\"minecraft:empty\"," + zombie +
            "ArmorItems:[{},{},{},{id:\"minecraft:diamond_hoe\",Count:1b,Damage:%ds,tag:{Unbreakable:1b}}],"
            "ArmorDropChances:[0f,0f,0f,0f],HandDropChances:[0f,0f],"
            "ActiveEffects:[{Id:14b,Amplifier:0b,Duration:2147483647,ShowParticles:0b},"
            "{Id:12b,Amplifier:0b,Duration:2147483647,ShowParticles:0b}%s],"
            "Attributes:[{Name:generic.maxHealth,Base:%dd},{Name:generic.movementSpeed,Base:%sd},"
            "{Name:generic.followRange,Base:48d},{Name:generic.attackDamage,Base:%dd},"
            + verstaerkung + "{Name:generic.knockbackResistance,Base:%sd}],"
            "Health:%df}") % (j(anzeigename), name, dmg, extra_effekte, leben, tempo, schaden,
                              "1" if name == "warden" else "0.3", leben)


SMILER = monster_nbt("smiler", "Smiler", 80, "0.28", 8)
HOUND = monster_nbt("hound", "Hound", 60, "0.34", 6)
HAUTDIEB = monster_nbt("hautdieb", "Hautdieb", 100, "0.32", 10)
PARTY = monster_nbt("partygaenger", "Partygänger", 70, "0.31", 8)
FACELING = monster_nbt("faceling", "Faceling", 90, "0.29", 9)
WARDEN = monster_nbt("warden", "Warden", 1000, "0.3", 16,
                     ",{Id:11b,Amplifier:3b,Duration:2147483647,ShowParticles:0b}")


def zombie(x, y, z, nbt):
    return "summon zombie %d %d %d %s" % (x, y, z, nbt)


# ---------------------------------------------------------------------------
# Level 0: Die gelben Raeume
# ---------------------------------------------------------------------------

def level0():
    g = LEVEL[0]
    info = dict(bef=huelle(g) + boden_decke(g, "stained_glass 12", "concrete 0"))
    ras = Raster(g, 4, 11, 0.30)
    r = random.Random(12)
    saele = [ras.saal(r.randrange(1, ras.n - 2), r.randrange(1, ras.n - 2)) for _ in range(6)]
    info["bef"] += ras.bauen("sponge 0") + saele
    lampen, dunkel = [], []
    for i in range(ras.n):
        for jj in range(ras.n):
            cx, cz = ras.mitte(i, jj)
            if r.random() < 0.7 or (i, jj) == (0, 0):
                lampen.append((cx, B + g["h"] + 1, cz))
                info["bef"].append("setblock %d %d %d sea_lantern" % lampen[-1])
            else:
                dunkel.append((i, jj))
    d = ras.abstaende()
    start = ras.mitte(0, 0)
    info["start"] = (start[0], B + 1, start[1])
    weit = sorted(d, key=lambda k: -d[k])
    ausgang = weit[0]
    maxd = d[ausgang]
    falsch = [k for k in weit if 0.45 * maxd <= d[k] <= 0.8 * maxd
              and abs(k[0] - ausgang[0]) + abs(k[1] - ausgang[1]) >= 4]
    falsch = weit_verteilt(falsch, 2, 4)
    info["ausgang"] = ausgang
    info["ziele"] = []        # (Zelle, Ziel-Level oder "zurueck")
    for zelle, ziel in [(ausgang, 1)] + [(f, 0) for f in falsch]:
        cx, cz = ras.mitte(*zelle)
        info["ziele"].append((cx, B + 1, cz, ziel))
        seite = ras.geschlossene_seite(*zelle)
        if seite:
            sx, sz, richtung, _ = seite
            info["bef"].append(schild(sx, B + 3, sz, richtung, [
                "", {"text": "NOTAUSGANG", "color": "dark_green", "bold": True}, {"text": "→ Level 1"}, ""]))
        info["bef"].append("setblock %d %d %d sea_lantern" % (cx, B + g["h"] + 1, cz))
    fern = [k for k in dunkel if d.get(k, 0) >= 5]
    r.shuffle(fern)
    info["monster"] = [(ras.mitte(*k)[0], B + 1, ras.mitte(*k)[1], SMILER) for k in fern[:8]]
    info["nachschub"] = ([(ras.mitte(*k)[0], B + 1, ras.mitte(*k)[1]) for k in fern[:12]], SMILER, 11)
    info["flacker"] = [(p, "concrete 0") for p in r.sample(lampen[1:], 7)]
    return info


# ---------------------------------------------------------------------------
# Level 1: Die Lagerhalle (3 Notstrom-Hebel oeffnen den Aufzug)
# ---------------------------------------------------------------------------

def level1():
    g = LEVEL[1]
    x0, z0, h, w, d = g["x"], g["z"], g["h"], g["w"], g["d"]
    bef = huelle(g) + boden_decke(g, "stained_glass 7", "concrete 8")
    bef.append(fill(x0, B + 1, z0, x0 + w - 1, B + h, z0 + d - 1, "air"))
    for zz in (z0 - 1, z0 + d):
        bef.append(fill(x0 - 1, B + 1, zz, x0 + w, B + h, zz, "concrete 7"))
    for xx in (x0 - 1, x0 + w):
        bef.append(fill(xx, B + 1, z0 - 1, xx, B + h, z0 + d, "concrete 7"))
    r = random.Random(21)
    saeulen = [(x0 + 6 + 8 * i, z0 + 6 + 8 * k) for i in range(7) for k in range(7)]
    for px, pz in saeulen:
        bef.append(fill(px, B + 1, pz, px + 1, B + h, pz + 1, "concrete 8"))
    for _ in range(10):
        if r.random() < 0.5:
            px, pz, l = x0 + r.randrange(8, w - 14), z0 + r.randrange(8, d - 8), r.randrange(6, 12)
            bef.append(fill(px, B + 1, pz, px + l, B + 4, pz, "concrete 7"))
        else:
            px, pz, l = x0 + r.randrange(8, w - 8), z0 + r.randrange(8, d - 14), r.randrange(6, 12)
            bef.append(fill(px, B + 1, pz, px, B + 4, pz + l, "concrete 7"))
    for _ in range(40):
        px, pz = x0 + r.randrange(6, w - 6), z0 + r.randrange(6, d - 6)
        bef.append(fill(px, B + 1, pz, px + r.randrange(0, 2), B + r.randrange(1, 4), pz + r.randrange(0, 2),
                        "stained_glass 8"))
    for _ in range(20):
        bef.append("setblock %d %d %d water" % (x0 + r.randrange(2, w - 2), B, z0 + r.randrange(2, d - 2)))
    lampen = []
    for i in range(10):
        for k in range(10):
            p = (x0 + 3 + 6 * i, B + h + 1, z0 + 3 + 6 * k)
            if r.random() < 0.7 or (i, k) == (0, 0):
                lampen.append(p)
                bef.append("setblock %d %d %d sea_lantern" % p)
    start = (x0 + 2, B + 1, z0 + 2)
    # Hounds und Nachschub: freie Plaetze weit weg vom Start
    plaetze = []
    for i in range(6):
        for k in range(6):
            px, pz = x0 + 10 + 8 * i, z0 + 10 + 8 * k
            if abs(px - start[0]) + abs(pz - start[2]) >= 24:
                plaetze.append((px, B + 1, pz))
    r.shuffle(plaetze)
    for (px, py, pz) in plaetze[:14]:
        bef.append(fill(px - 1, B + 1, pz - 1, px + 1, B + 3, pz + 1, "air"))
    # Drei Notstrom-Hebel an Saeulen in verschiedenen Ecken der Halle
    hebel = []
    for qx, qz in ((1, 0), (0, 1), (1, 1)):
        kand = [(px, pz) for px, pz in saeulen
                if (px - x0 >= w // 2) == bool(qx) and (pz - z0 >= d // 2) == bool(qz)
                and abs(px - start[0]) + abs(pz - start[2]) >= 30]
        px, pz = r.choice(kand)
        bef.append(fill(px - 1, B + 1, pz + 2, px + 2, B + 3, pz + 3, "air"))
        hebel.append((px, B + 2, pz + 2, 3))
        bef.append(schild(px + 1, B + 2, pz + 2, 3, ["", {"text": "NOTSTROM", "color": "dark_red", "bold": True},
                                                     {"text": "Hebel umlegen"}, ""]))
        bef.append("setblock %d %d %d sea_lantern" % (px, B + h + 1, pz + 3))
    # Ausgang: Aufzugstuer an der Suedwand (geschlossen: Eisenblock)
    ex = (x0 + w - 4, B + 1, z0 + d - 1)
    bef.append(fill(ex[0] - 2, B + 1, ex[2] - 2, ex[0] + 2, B + 3, ex[2], "air"))
    bef.append(fill(ex[0] - 1, B + 1, ex[2], ex[0] - 1, B + 4, ex[2], "concrete 8"))
    bef.append(fill(ex[0] + 1, B + 1, ex[2], ex[0] + 1, B + 4, ex[2], "concrete 8"))
    bef.append(fill(ex[0] - 1, B + 4, ex[2], ex[0] + 1, B + 4, ex[2], "concrete 8"))
    bef.append(schild(ex[0], B + 4, ex[2] - 1, 2, ["", {"text": "AUFZUG", "color": "dark_red", "bold": True},
                                                   {"text": "→ Level 2"}, {"text": "(kein Strom)", "color": "gray"}]))
    bef.append("setblock %d %d %d sea_lantern" % (ex[0], B + h + 1, ex[2] - 1))
    zu = [fill(ex[0], B + 1, ex[2], ex[0], B + 3, ex[2], "iron_block")]
    auf = [fill(ex[0], B + 2, ex[2], ex[0], B + 3, ex[2], "air"), gateway(ex[0], ex[1], ex[2], start_von(2))]
    bef += zu
    bef += ["setblock %d %d %d lever %d" % hb for hb in hebel]
    return dict(bef=bef, start=start, hebel=hebel, zu=zu, auf=auf, ausgang_pos=ex,
                monster=[(px, py, pz, HOUND) for (px, py, pz) in plaetze[:8]],
                nachschub=(plaetze[:14], HOUND, 11),
                flacker=[(p, "concrete 8") for p in r.sample(lampen[1:], 8)],
                ziele=[])


# ---------------------------------------------------------------------------
# Level 2: Die Rohrtunnel (Dampffallen)
# ---------------------------------------------------------------------------

def level2():
    g = LEVEL[2]
    x0, z0, h = g["x"], g["z"], g["h"]
    bef = huelle(g) + boden_decke(g, "stained_glass 15", "concrete 15")
    ras = Raster(g, 3, 31, 0.12)
    bef += ras.bauen("concrete 9")
    bef.append(fill(x0, B + 3, z0, x0 + g["w"] - 1, B + 3, z0 + g["d"] - 1, "concrete 1", "replace concrete 9"))
    for zz in range(z0 + 2, z0 + g["d"], 6):
        bef.append(fill(x0, B + h + 1, zz, x0 + g["w"] - 1, B + h + 1, zz, "concrete 1"))
    r = random.Random(32)
    for i in range(ras.n):
        for jj in range(ras.n):
            if r.random() < 0.2 and (i, jj) != (0, 0):
                cx, cz = ras.innen(i, jj)[:2]
                bef.append("setblock %d %d %d redstone_torch 5" % (cx + r.randrange(2), B + 1, cz + r.randrange(2)))
    d = ras.abstaende()
    s = ras.innen(0, 0)
    start = (s[0], B + 1, s[1])
    weit = sorted(d, key=lambda k: -d[k])
    ausgang = weit[0]
    ex = ras.innen(*ausgang)
    seite = ras.geschlossene_seite(*ausgang)
    if seite:
        bef.append(schild(seite[0], B + 3, seite[1], seite[2],
                          ["", {"text": "WARTUNGSSCHACHT", "color": "gold", "bold": True}, {"text": "→ Level 3"}, ""]))
    bef.append("setblock %d %d %d redstone_torch 5" % (ex[2], B + 1, ex[3]))
    fern = [k for k in d if d[k] >= 6]
    r.shuffle(fern)
    monster = [(ras.innen(*k)[0], B + 1, ras.innen(*k)[1], HAUTDIEB) for k in fern[:6]]
    monster += [(ras.innen(*k)[0], B + 1, ras.innen(*k)[1], SMILER) for k in fern[6:8]]
    fallen = []
    kandidaten = sorted((k for k in d if d[k] >= 3 and k != ausgang), key=lambda k: (k[0] * 7 + k[1] * 13) % 17)
    for k in weit_verteilt(kandidaten, 9, 3):
        fx, fz = ras.innen(*k)[:2]
        fallen.append((fx, B + 1, fz))
        bef.append("setblock %d %d %d concrete 1" % (fx, B + h + 1, fz))
    return dict(bef=bef, start=start, ziele=[(ex[0], B + 1, ex[1], 3)], monster=monster,
                nachschub=([(ras.innen(*k)[0], B + 1, ras.innen(*k)[1]) for k in fern[:12]], HAUTDIEB, 10),
                fallen=fallen, flacker=[])


# ---------------------------------------------------------------------------
# Level 3: Das Hotel (Hauptschalter in einem der Zimmer oeffnet Zimmer 237)
# ---------------------------------------------------------------------------

def level3():
    g = LEVEL[3]
    x0, z0, h, w, d = g["x"], g["z"], g["h"], g["w"], g["d"]
    bef = huelle(g) + boden_decke(g, "nether_wart_block 0", "concrete 0")
    bef.append(fill(x0, B + 1, z0, x0 + w - 1, B + h, z0 + d - 1, "red_nether_brick 0"))
    r = random.Random(51)
    flure = [z0 + 1 + 12 * k for k in range(5)]
    for fz in flure:
        bef.append(fill(x0 + 1, B + 1, fz, x0 + w - 2, B + 3, fz + 2, "air"))
    # Verbindungen zwischen den Fluren: abwechselnd am Ost- und am Westende (Schlangenweg)
    durchgang = {}
    for k in range(4):
        xs = (x0 + 56, x0 + 58) if k % 2 == 0 else (x0 + 2, x0 + 4)
        durchgang[k] = xs
        bef.append(fill(xs[0], B + 1, flure[k] + 3, xs[1], B + 3, flure[k] + 11, "air"))
    zimmer = []          # (Reihe, Flur k, Spalte m, innen x0,z0,x1,z1, Tuer x, Tuer z, Tuerwand-Richtung)
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
    # Sockelleiste aus Holz
    bef.append(fill(x0, B + 1, z0, x0 + w - 1, B + 1, z0 + d - 1, "concrete_powder 12", "replace red_nether_brick"))
    # Ausgangszimmer: ganz am Ende des letzten Flurs (Osten), verschlossene Eisentuer
    aus = [zz for zz in zimmer if zz[1] == 4 and zz[2] == 11][0]
    hz = [zz for zz in zimmer if zz[1] in (1, 2, 3) and zz[2] not in (0, 11)]
    schalter = r.choice(hz)
    nummer = {}
    tueren = []
    for zz in zimmer:
        reihe, k, m, ix0, iz0, ix1, iz1, tx, tz = zz
        nr = 100 * (k + 1) + 2 * m + (1 if reihe == "A" else 2)
        if zz is aus:
            nr = 237
        nummer[zz] = nr
        bef.append(fill(tx, B + 1, tz, tx, B + 2, tz, "air"))
        if zz is aus:
            tueren.append(zz)
            continue
        facing = 1 if reihe == "A" else 3
        bef.append("setblock %d %d %d dark_oak_door %d" % (tx, B + 1, tz, facing))
        bef.append("setblock %d %d %d dark_oak_door 8" % (tx, B + 2, tz))
        sz, richtung = (tz - 1, 2) if reihe == "A" else (tz + 1, 3)
        bef.append(schild(tx, B + 3, sz, richtung, ["", {"text": "Zimmer %d" % nr, "color": "gold"}, "", ""]))
        # Einrichtung
        wahl = r.random()
        if wahl < 0.3 and zz is not schalter:
            beute = ('{Items:[{Slot:%db,id:"minecraft:golden_apple",Count:2b,Damage:1s},'
                     '{Slot:%db,id:"minecraft:arrow",Count:16b}]}' % (r.randrange(0, 13), r.randrange(14, 27)))
            bef.append("setblock %d %d %d chest 2 replace %s" % (ix1, B + 1, iz0 if reihe == "B" else iz1, beute))
        if wahl > 0.55:
            bef.append("setblock %d %d %d end_rod 0" % (ix0 + 1, B + 3, (iz0 + iz1) // 2))
    # Hauptschalter (Hebel an der Rueckwand des Zimmers)
    reihe, k, m, ix0, iz0, ix1, iz1, tx, tz = schalter
    if reihe == "A":
        hebel = [(ix0 + 2, B + 2, iz1, 4)]
        sch = (ix0 + 1, B + 2, iz1, 2)
    else:
        hebel = [(ix0 + 2, B + 2, iz0, 3)]
        sch = (ix0 + 1, B + 2, iz0, 3)
    bef.append(schild(sch[0], sch[1], sch[2], sch[3], ["", {"text": "HAUPTSCHALTER", "color": "dark_red", "bold": True},
                                                       {"text": "öffnet Zimmer 237"}, ""]))
    bef.append("setblock %d %d %d end_rod 0" % (ix0 + 2, B + 3, (iz0 + iz1) // 2))
    bef += ["setblock %d %d %d lever %d" % hb for hb in hebel]
    # Ausgangszimmer
    reihe, k, m, ix0, iz0, ix1, iz1, tx, tz = aus
    bef.append(schild(tx, B + 3, tz - 1, 2, ["", {"text": "Zimmer 237", "color": "red", "bold": True},
                                             {"text": "AUSGANG"}, {"text": "verschlossen", "color": "gray"}]))
    zu = ["setblock %d %d %d iron_door 1" % (tx, B + 1, tz), "setblock %d %d %d iron_door 8" % (tx, B + 2, tz)]
    auf = ["setblock %d %d %d iron_door 5" % (tx, B + 1, tz),
           "playsound block.iron_door.open master @a %d %d %d 2 0.8" % (tx, B + 1, tz)]
    bef += [zu[1], zu[0]]
    cx, cz = (ix0 + ix1) // 2, (iz0 + iz1) // 2 + 1
    bef.append("setblock %d %d %d end_rod 0" % (cx, B + 3, cz))
    # Wandleuchten in den Fluren
    for fz in flure:
        for xx in range(x0 + 3, x0 + w - 3, 6):
            bef.append("setblock %d %d %d end_rod 2" % (xx, B + 3, fz + 2))
    lampen = []
    for fz in flure:
        for xx in range(x0 + 6, x0 + w - 3, 12):
            lampen.append((xx, B + 4, fz + 1))
            bef.append("setblock %d %d %d sea_lantern" % lampen[-1])
    start = (x0 + 2, B + 1, z0 + 1)
    # Monster: auf den Fluren und in einigen Zimmern
    flurplaetze = [(xx, B + 1, flure[k] + 1) for k in range(5) for xx in range(x0 + 8, x0 + w - 4, 9)
                   if not (k == 0 and xx < x0 + 30)]
    r.shuffle(flurplaetze)
    zimmerplaetze = [((zz[3] + zz[5]) // 2, B + 1, (zz[4] + zz[6]) // 2) for zz in r.sample(hz, 4)
                     if zz is not schalter]
    monster = [(x, y, z, PARTY) for (x, y, z) in flurplaetze[:7] + zimmerplaetze]
    return dict(bef=bef, start=start, hebel=hebel, zu=zu, auf=auf,
                ziele=[(cx, B + 1, cz, 4)], monster=monster,
                nachschub=(flurplaetze[:12], PARTY, 13),
                flacker=[(p, "concrete 0") for p in r.sample(lampen, 5)])


# ---------------------------------------------------------------------------
# Level 4: Das Buero (4 Sicherungen schalten den Wartungsaufzug frei)
# ---------------------------------------------------------------------------

def level4():
    g = LEVEL[4]
    x0, z0, h = g["x"], g["z"], g["h"]
    bef = huelle(g) + boden_decke(g, "concrete_powder 11", "concrete 0")
    ras = Raster(g, 6, 61, 0.45)
    bef += ras.bauen("concrete_powder 0")
    r = random.Random(62)
    d = ras.abstaende()
    weit = sorted(d, key=lambda k: -d[k])
    ausgang = weit[0]
    hebelzellen = weit_verteilt([k for k in weit[2:] if d[k] >= 4 and ras.geschlossene_seite(*k)], 4, 4)
    lampen = []
    for i in range(ras.n):
        for jj in range(ras.n):
            ix0, iz0, ix1, iz1 = ras.innen(i, jj)
            cx, cz = ras.mitte(i, jj)
            if r.random() < 0.72 or (i, jj) == (0, 0):
                lampen.append((cx, B + h + 1, cz))
                bef.append("setblock %d %d %d sea_lantern" % lampen[-1])
            if (i, jj) in [(0, 0), ausgang] + hebelzellen or r.random() > 0.65:
                continue
            # Arbeitsplatz: Schreibtisch mit Monitor an einer Wand, Trennwaende daneben
            seite = r.choice(("n", "s", "w", "o"))
            if seite in ("n", "s"):
                zz = iz0 if seite == "n" else iz1
                dz = 1 if seite == "n" else -1
                bef.append(fill(ix0 + 1, B + 1, zz, ix0 + 3, B + 1, zz, "concrete_powder 12"))
                bef.append("setblock %d %d %d concrete_powder 15" % (ix0 + 2, B + 2, zz))
                bef.append(fill(ix0, B + 1, zz, ix0, B + 2, zz + dz, "concrete_powder 8"))
                bef.append(fill(ix0 + 4, B + 1, zz, ix0 + 4, B + 2, zz + dz, "concrete_powder 8"))
            else:
                xx = ix0 if seite == "w" else ix1
                dx = 1 if seite == "w" else -1
                bef.append(fill(xx, B + 1, iz0 + 1, xx, B + 1, iz0 + 3, "concrete_powder 12"))
                bef.append("setblock %d %d %d concrete_powder 15" % (xx, B + 2, iz0 + 2))
                bef.append(fill(xx, B + 1, iz0, xx + dx, B + 2, iz0, "concrete_powder 8"))
                bef.append(fill(xx, B + 1, iz0 + 4, xx + dx, B + 2, iz0 + 4, "concrete_powder 8"))
    # Sicherungen (Hebel) an geschlossenen Waenden
    hebel = []
    for zelle in hebelzellen:
        sx, sz, richtung, meta = ras.geschlossene_seite(*zelle)
        hebel.append((sx, B + 2, sz, meta))
        bef.append("setblock %d %d %d lever %d" % hebel[-1])
        bef.append(schild(sx, B + 3, sz, richtung, ["", {"text": "SICHERUNG", "color": "dark_red", "bold": True},
                                                    {"text": "einschalten"}, ""]))
    # Wartungsaufzug in der entferntesten Zelle (geschlossen: Eisenblock)
    cx, cz = ras.mitte(*ausgang)
    seite = ras.geschlossene_seite(*ausgang)
    if seite:
        bef.append(schild(seite[0], B + 3, seite[1], seite[2],
                          ["", {"text": "WARTUNGSAUFZUG", "color": "dark_aqua", "bold": True},
                           {"text": "→ ???"}, {"text": "4 Sicherungen nötig", "color": "gray"}]))
    zu = [fill(cx, B + 1, cz, cx, B + 2, cz, "iron_block")]
    auf = [fill(cx, B + 2, cz, cx, B + 2, cz, "air"), gateway(cx, B + 1, cz, start_von(FINALE))]
    bef += zu
    s = ras.mitte(0, 0)
    fern = [k for k in d if d[k] >= 4 and k not in hebelzellen and k != ausgang]
    r.shuffle(fern)
    monster = [(ras.mitte(*k)[0], B + 1, ras.mitte(*k)[1], FACELING) for k in fern[:6]]
    monster += [(ras.mitte(*k)[0], B + 1, ras.mitte(*k)[1], HOUND) for k in fern[6:10]]
    return dict(bef=bef, start=(s[0], B + 1, s[1]), hebel=hebel, zu=zu, auf=auf, ziele=[], monster=monster,
                nachschub=([(ras.mitte(*k)[0], B + 1, ras.mitte(*k)[1]) for k in fern[:12]], FACELING, 12),
                flacker=[(p, "concrete 0") for p in r.sample(lampen[1:], 6)])


# ---------------------------------------------------------------------------
# Finale: Deep Dark
# ---------------------------------------------------------------------------

def arena():
    g = LEVEL[FINALE]
    rr, h = g["r"], g["h"]
    ax, az = g["x"] + rr, g["z"] + rr
    bef = huelle(g)
    bef.append(fill(g["x"], B, g["z"], g["x"] + g["w"] - 1, B + h + 1, g["z"] + g["d"] - 1, "concrete 3"))
    for dz in range(-rr, rr + 1):
        w = int(math.sqrt(rr * rr - dz * dz))
        bef.append(fill(ax - w, B, az + dz, ax + w, B, az + dz, "stained_glass 9"))
        bef.append(fill(ax - w, B + 1, az + dz, ax + w, B + h, az + dz, "air"))
    rnd = random.Random(41)
    for _ in range(140):
        a = rnd.uniform(0, 2 * math.pi)
        x, z = ax + int(round((rr + 0.6) * math.cos(a))), az + int(round((rr + 0.6) * math.sin(a)))
        bef.append("setblock %d %d %d concrete 11" % (x, B + rnd.randrange(1, h + 1), z))
    for _ in range(60):
        a, d = rnd.uniform(0, 2 * math.pi), rnd.uniform(0, rr - 1)
        bef.append("setblock %d %d %d concrete 11" % (ax + int(d * math.cos(a)), B + h + 1, az + int(d * math.sin(a))))
    for _ in range(14):
        a, d = rnd.uniform(0, 2 * math.pi), rnd.uniform(4, rr - 2)
        bef.append("setblock %d %d %d glowstone" % (ax + int(d * math.cos(a)), B, az + int(d * math.sin(a))))
    for _ in range(8):
        a, d = rnd.uniform(0, 2 * math.pi), rnd.uniform(2, rr - 3)
        bef.append("setblock %d %d %d glowstone" % (ax + int(d * math.cos(a)), B + h + 1, az + int(d * math.sin(a))))
    for dx in range(-2, 3):
        for dz in range(-2, 3):
            if max(abs(dx), abs(dz)) == 2:
                bef.append("setblock %d %d %d glowstone" % (ax + dx, B, az + dz))
    return dict(bef=bef, start=(ax, B + 1, az + rr - 3), ziele=[], monster=[], flacker=[])


BAUER = [level0, level1, level2, level3, level4, arena]
_CACHE = {}


def level(lv):
    if lv not in _CACHE:
        _CACHE[lv] = BAUER[lv]()
    return _CACHE[lv]


def start_von(lv):
    """Startpunkt eines Levels (ohne den ganzen Bau auszuwerten, wo moeglich)."""
    return level(lv)["start"]


def bau_befehle(geo):
    bef = []
    for lv in range(len(BAUER)):
        info = level(lv)
        bef += info["bef"]
        for (x, y, z, ziel) in info.get("ziele", []):
            bef.append(gateway(x, y, z, start_von(ziel)))
    return bef


def marken_befehle(geo):
    """Markierungen fuer nachkommende Monster (bleiben dauerhaft in den Leveln)."""
    bef = []
    for lv in range(ANZAHL_LEVEL):
        plaetze, _, _ = level(lv)["nachschub"]
        for (x, y, z) in plaetze:
            bef.append(marke_befehl(x, y, z, "br_sp", "br_sp%d" % lv))
    for k, (x, y, z) in enumerate(level(2)["fallen"]):
        bef.append(marke_befehl(x, y, z, "br_dampf", "br_dg%d" % (k % 3)))
    return bef


# ---------------------------------------------------------------------------
# Befehlsketten
# ---------------------------------------------------------------------------

def titel(sel, titel_text, farbe, untertitel):
    return [
        "title %s times 10 80 25" % sel,
        "title %s subtitle %s" % (sel, j({"text": untertitel, "color": "gray", "italic": True})),
        "title %s title %s" % (sel, j({"text": titel_text, "color": farbe, "bold": True})),
    ]


INFO = {
    0: ("LEVEL 0", "yellow", "Die gelben Räume – finde den Notausgang", "block.portal.ambient"),
    1: ("LEVEL 1", "gray", "Die Lagerhalle – Notstrom einschalten", "ambient.cave"),
    2: ("LEVEL 2", "dark_red", "Die Rohrtunnel – nimm die Taschenlampe", "block.fire.extinguish"),
    3: ("LEVEL 3", "gold", "Das Hotel – finde den Hauptschalter", "entity.witch.ambient"),
    4: ("LEVEL 4", "aqua", "Das Büro – 4 Sicherungen einschalten", "block.note.bell"),
    5: ("FINALE", "dark_aqua", "Deep Dark – sei leise …", "entity.elder_guardian.curse"),
}

RAETSEL = {1: ("br_h1", "br_auf1", "Notstrom", "Notstrom an – der Aufzug fährt!"),
           3: ("br_h3", "br_auf3", "Hauptschalter", "Ein Schloss klickt – Zimmer 237 ist offen."),
           4: ("br_h4", "br_auf4", "Sicherungen", "Alle Sicherungen drin – der Wartungsaufzug fährt!")}


def ketten(geo):
    zx, zy, zz = geo.zustand
    ax, az = geo.ax, geo.az
    zustand_nbt = "{Marker:1b,Invisible:1b,NoGravity:1b,Tags:[br_state,wp_sys]}"
    S = "@a[score_start_min=1]"

    # --- Start (/start bzw. /trigger start set 1) und Zeitgeber ---
    start = [
        "scoreboard players enable @a start",
    ] + ["scoreboard players add %s %s 0" % (STATE, o) for o in FLAGS] + [
        "scoreboard players add %s br_t 1" % STATE,
        "scoreboard players set @e[tag=br_state,score_br_t_min=16] br_t 0",
        "scoreboard players add %s br_t2 1" % STATE,
        "scoreboard players set @e[tag=br_state,score_br_t2_min=300] br_t2 0",
        "scoreboard players add %s br_t3 1" % STATE,
        "scoreboard players add %s br_t4 1" % STATE,
        "scoreboard players set @e[tag=br_state,score_br_t4_min=60] br_t4 0",
        "scoreboard players set @e[tag=br_state,score_br_t3_min=%d] br_t3 0" % NACHSCHUB_TAKT,
        "execute %s ~ ~ ~ kill @e[tag=br_mob]" % S,
        "execute %s ~ ~ ~ kill %s" % (S, STATE),
        "execute %s ~ ~ ~ summon armor_stand %d %d %d %s" % (S, zx, zy, zz, zustand_nbt),
        "execute %s ~ ~ ~ clear @s carrot_on_a_stick %d" % (S, waffen.RUTE["taschenlampe"]),
        waffen.give(S, *waffen.LAMPE),
        "execute %s ~ ~ ~ summon armor_stand ~ ~ ~ {Marker:1b,Invisible:1b,NoGravity:1b,Tags:[br_gw,wp_sys]}" % S,
        "execute %s ~ ~ ~ %s" % (S, gateway(0, 0, 0, start_von(0)).replace("setblock 0 0 0", "setblock ~ ~ ~")),
        "execute %s ~ ~ ~ playsound entity.endermen.teleport master @s ~ ~ ~ 1 0.5" % S,
        "tellraw %s %s" % (S, j({"text": "Du rutschst durch den Boden der Realität …", "color": "gold", "italic": True})),
        "tellraw %s %s" % (S, j({"text": "Fünf Level und ein Finale. Die Wände sind unzerstörbar.", "color": "gray"})),
        "scoreboard players set %s start 0" % S,
        "scoreboard players add @e[tag=br_gw] wp_alter 1",
        "execute @e[tag=br_gw,score_wp_alter_min=10] ~ ~ ~ setblock ~ ~ ~ air",
        "kill @e[tag=br_gw,score_wp_alter_min=10]",
    ]

    # --- Level betreten: Titel, Ruecksetzen, Monster (einmal pro Durchgang) ---
    eintritt = []
    for lv in range(ANZAHL_LEVEL + 1):
        info = level(lv)
        sel = "@a[tag=br_in%d]" % lv
        eintritt.append("scoreboard players tag @a remove br_in%d" % lv)
        eintritt.append("scoreboard players tag @a[%s] add br_in%d" % (geo.region(lv), lv))
        vor = "execute @e[tag=br_state,score_br_f%d=0] ~ ~ ~ execute %s ~ ~ ~ " % (lv, sel)
        t, farbe, ut, ton = INFO[lv]
        for c in titel("@s", t, farbe, ut):
            eintritt.append(vor + c)
        eintritt.append(vor + "playsound %s master @s ~ ~ ~ 1 0.6" % ton)
        eintritt.append(vor + "spawnpoint @s %d %d %d" % info["start"])
        # Alte Monster dieses Levels (aus einem frueheren Durchgang) entfernen, Raetsel zuruecksetzen
        eintritt.append(vor + "kill @e[tag=br_mob,%s]" % geo.region(lv))
        for (x, y, z, meta) in info.get("hebel", []):
            eintritt.append(vor + "setblock %d %d %d lever %d" % (x, y, z, meta))
        for c in info.get("zu", []):
            eintritt.append(vor + c)
        for x, y, z, nbt in info["monster"]:
            eintritt.append(vor + zombie(x, y, z, nbt))
        if lv == FINALE:
            eintritt.append(vor + "setblock %d %d %d air" % (ax, B + 1, az))
            eintritt.append(vor + "summon wither_skeleton %d %.1f %d {Tags:[br_mob,w_auf,wp_sys],NoAI:1b,NoGravity:1b,"
                            "Silent:1b,Invulnerable:1b,PersistenceRequired:1b,DeathLootTable:\"minecraft:empty\","
                            "ActiveEffects:[{Id:14b,Amplifier:0b,Duration:2147483647,ShowParticles:0b}],"
                            "ArmorDropChances:[0f,0f,0f,0f],Rotation:[0f,0f],ArmorItems:[{},{},{},"
                            "{id:\"minecraft:diamond_hoe\",Count:1b,Damage:%ds,tag:{Unbreakable:1b}}]}"
                            % (ax, B + 1 - 3.0, az, modelle.MONSTER_DAMAGE["warden"][0]))
        eintritt.append("execute %s ~ ~ ~ scoreboard players set %s br_f%d 1" % (sel, STATE, lv))
    # In welchem Level ist gerade jemand?
    eintritt.append("scoreboard players set %s br_lv -1" % STATE)
    for lv in range(ANZAHL_LEVEL + 1):
        eintritt.append("execute @a[tag=br_in%d] ~ ~ ~ scoreboard players set %s br_lv %d" % (lv, STATE, lv))

    # --- Raetsel: Hebel zaehlen, Ausgang oeffnen ---
    raetsel = []
    for lv, (zaehler, flag, wort, meldung) in RAETSEL.items():
        info = level(lv)
        n = len(info["hebel"])
        imlevel = "score_br_lv_min=%d,score_br_lv=%d" % (lv, lv)
        raetsel.append("scoreboard players set %s %s 0" % (STATE, zaehler))
        for (x, y, z, meta) in info["hebel"]:
            raetsel.append("execute @e[tag=br_state,%s] ~ ~ ~ detect %d %d %d lever %d scoreboard players add @s %s 1"
                           % (imlevel, x, y, z, meta + 8, zaehler))
        offen = "execute @e[tag=br_state,%s,score_%s_min=%d,score_%s=0] ~ ~ ~ " % (imlevel, zaehler, n, flag)
        for c in info["auf"]:
            raetsel.append(offen + c)
        raetsel.append(offen + "playsound block.note.pling master @a[tag=br_in%d] ~ ~ ~ 1 1.5" % lv)
        raetsel.append(offen + "playsound entity.lightning.thunder master @a[tag=br_in%d] ~ ~ ~ 0.4 2" % lv)
        raetsel.append(offen + "tellraw @a[tag=br_in%d] %s" % (lv, j({"text": meldung, "color": "green"})))
        raetsel.append(offen + "scoreboard players set @s %s 1" % flag)
        if n > 1:
            raetsel.append("execute @e[tag=br_state,%s,score_br_t_min=0,score_br_t=0,score_%s=0] ~ ~ ~ title @a[tag=br_in%d] "
                           "actionbar %s" % (imlevel, flag, lv, j([
                               {"text": wort + ": ", "color": "yellow"},
                               {"score": {"name": "@e[tag=br_state]", "objective": zaehler}, "color": "white"},
                               {"text": "/%d" % n, "color": "white"}])))
    # Neuer Durchgang: Raetsel wieder zu (wird beim Betreten zurueckgesetzt)
    for lv, (zaehler, flag, _, _) in RAETSEL.items():
        raetsel.append("execute @e[tag=br_state,score_br_f%d=0] ~ ~ ~ scoreboard players set @s %s 0" % (lv, flag))

    # --- Atmosphaere: flackernde Lampen, Geraeusche, Dampf, Fallen ---
    atmo = []
    flacker = []
    for lv in range(ANZAHL_LEVEL):
        flacker += level(lv).get("flacker", [])
    for k, ((x, y, z), aus) in enumerate(flacker):
        t0 = (k * 37) % 280 + 5
        atmo.append("execute @e[tag=br_state,score_br_t2_min=%d,score_br_t2=%d] ~ ~ ~ setblock %d %d %d %s"
                    % (t0, t0, x, y, z, aus))
        atmo.append("execute @e[tag=br_state,score_br_t2_min=%d,score_br_t2=%d] ~ ~ ~ setblock %d %d %d sea_lantern"
                    % (t0 + 3, t0 + 3, x, y, z))
    atmo += [
        "execute @e[tag=br_state,score_br_t2_min=120,score_br_t2=120] ~ ~ ~ execute @a[tag=br_in0] ~ ~ ~ playsound block.portal.ambient ambient @s ~ ~ ~ 0.25 2",
        "execute @e[tag=br_state,score_br_t2_min=200,score_br_t2=200] ~ ~ ~ execute @a[tag=br_in1] ~ ~ ~ playsound ambient.cave ambient @s ~ ~ ~ 0.8 0.7",
        "execute @e[tag=br_state,score_br_t2_min=0,score_br_t2=0] ~ ~ ~ execute @a[tag=br_in2] ~ ~ ~ playsound block.fire.extinguish ambient @s ~ ~2 ~3 0.4 0.5",
        "execute @e[tag=br_state,score_br_t2_min=90,score_br_t2=90] ~ ~ ~ execute @a[tag=br_in3] ~ ~ ~ playsound entity.witch.ambient ambient @s ~6 ~ ~ 0.6 1.4",
        "execute @e[tag=br_state,score_br_t2_min=210,score_br_t2=210] ~ ~ ~ execute @a[tag=br_in3] ~ ~ ~ playsound entity.firework.twinkle_far ambient @s ~ ~ ~-6 0.6 0.8",
        "execute @e[tag=br_state,score_br_t2_min=60,score_br_t2=60] ~ ~ ~ execute @a[tag=br_in4] ~ ~ ~ playsound block.note.bell ambient @s ~5 ~ ~ 0.5 1.2",
        "execute @e[tag=br_state,score_br_t2_min=64,score_br_t2=64] ~ ~ ~ execute @a[tag=br_in4] ~ ~ ~ playsound block.note.bell ambient @s ~5 ~ ~ 0.5 1.2",
        "execute @e[tag=br_state,score_br_t2_min=160,score_br_t2=160] ~ ~ ~ execute @a[tag=br_in4] ~ ~ ~ playsound block.note.hat ambient @s ~ ~ ~4 0.4 1.6",
        "execute @a[tag=br_in2] ~ ~ ~ particle cloud ~ ~2.6 ~ 4 0.1 4 0.005 1",
        "execute @a[tag=br_in0] ~ ~ ~ particle depthsuspend ~ ~1 ~ 4 2 4 0 2",
        "execute @a[tag=br_in%d] ~ ~ ~ particle townaura ~ ~1 ~ 6 3 6 0 6" % FINALE,
    ]
    # Dampffallen in Level 2: drei Gruppen, jede stoesst alle 3 Sekunden Dampf aus
    for gruppe in range(3):
        bed = "execute @e[tag=br_state,score_br_lv_min=2,score_br_lv=2,score_br_t4_min=%d,score_br_t4=%d] ~ ~ ~ execute @e[tag=br_dg%d] ~ ~ ~ " % (
            20 * gruppe, 20 * gruppe, gruppe)
        atmo += [bed + "particle cloud ~ ~ ~ 0.15 1 0.15 0.06 40 force",
                 bed + "playsound block.fire.extinguish master @a ~ ~ ~ 1 0.6",
                 bed + "effect @a[r=1] instant_damage 1 0 true"]

    # --- Monster: Animation, Geraeusche, Nachschub ---
    mon = []
    for name, (a, b) in modelle.MONSTER_DAMAGE.items():
        mon.append("execute @e[tag=br_state,score_br_t_min=0,score_br_t=0] ~ ~ ~ replaceitem entity @e[tag=br_%s] slot.armor.head diamond_hoe 1 %d {Unbreakable:1b}" % (name, a))
        mon.append("execute @e[tag=br_state,score_br_t_min=8,score_br_t=8] ~ ~ ~ replaceitem entity @e[tag=br_%s] slot.armor.head diamond_hoe 1 %d {Unbreakable:1b}" % (name, b))
    for name, ton, t0, hoehe in (("smiler", "entity.vex.ambient", 40, 0.5), ("hound", "entity.wolf.growl", 90, 0.5),
                                 ("hautdieb", "entity.villager.no", 150, 0.5), ("partygaenger", "entity.witch.ambient", 180, 1.6),
                                 ("faceling", "entity.villager.ambient", 250, 0.4)):
        mon.append("execute @e[tag=br_state,score_br_t2_min=%d,score_br_t2=%d] ~ ~ ~ execute @e[tag=br_%s] ~ ~ ~ playsound %s hostile @a ~ ~ ~ 1.2 %s"
                   % (t0, t0, name, ton, hoehe))
    mon.append("execute @e[tag=br_state,score_br_t2_min=220,score_br_t2=220] ~ ~ ~ execute @e[tag=br_hautdieb] ~ ~ ~ playsound entity.player.breath hostile @a ~ ~ ~ 1 0.6")
    takt = "score_br_t3_min=1,score_br_t3=1"
    mon += [
        "execute @e[tag=br_state,%s] ~ ~ ~ scoreboard players set @s br_anz 0" % takt,
        "execute @e[tag=br_state,%s] ~ ~ ~ scoreboard players set @e[tag=br_sp] br_nah 0" % takt,
        "execute @e[tag=br_state,%s] ~ ~ ~ execute @a ~ ~ ~ scoreboard players set @e[tag=br_sp,r=14] br_nah 1" % takt,
    ]
    for lv in range(ANZAHL_LEVEL):
        _, nbt, maximum = level(lv)["nachschub"]
        imlevel = "score_br_lv_min=%d,score_br_lv=%d" % (lv, lv)
        mon.append("execute @e[tag=br_state,%s,%s] ~ ~ ~ execute @e[tag=br_mob,%s] ~ ~ ~ scoreboard players add %s br_anz 1"
                   % (takt, imlevel, geo.region(lv), STATE))
        neu = "execute @e[tag=br_state,%s,%s,score_br_anz=%d] ~ ~ ~ execute @r[type=armor_stand,tag=br_sp%d,score_br_nah=0] ~ ~ ~ " % (
            takt, imlevel, maximum - 1, lv)
        mon += [neu + "summon zombie ~ ~ ~ " + nbt,
                neu + "particle largesmoke ~ ~1 ~ 0.3 0.8 0.3 0.02 30 force"]

    # --- Spieler: Abenteuermodus in den Backrooms, Schutz nach dem Wiedereinstieg, Taschenlampe ---
    spieler = [
        "scoreboard players tag @a remove br_drin",
        "scoreboard players tag @a[%s] add br_drin" % orte.BEREICH,
        "gamemode 2 @a[tag=br_drin,m=0]",
        "gamemode 0 @a[tag=!br_drin,m=2]",
        "scoreboard players tag @a[score_br_tode_min=1] add br_tot",
        "scoreboard players set @a[score_br_tode_min=1] br_tode 0",
        "scoreboard players tag @a[tag=br_tot] add br_lebt",
        "scoreboard players tag @a[tag=br_tot] remove br_lebt {Health:0.0f}",
        "effect @a[tag=br_lebt] resistance 5 4 true",
        "effect @a[tag=br_lebt] regeneration 5 2 true",
        "scoreboard players tag @a[tag=br_lebt] remove br_tot",
        "scoreboard players tag @a[tag=br_lebt] remove br_lebt",
        "scoreboard players set @a br_hold 0",
        "scoreboard players set @a br_hold 1 {SelectedItem:{tag:{br:1b}}}",
        "effect @a[score_br_hold_min=1] night_vision 12 0 true",
        "scoreboard players tag @a[score_br_hold_min=1] add br_nv",
        "effect @a[tag=br_nv,score_br_hold=0] night_vision 0",
        "scoreboard players tag @a[score_br_hold=0] remove br_nv",
    ]

    # --- Finale: der Warden ---
    blockcrack = 251 + (11 << 12)
    W = "@e[tag=br_warden]"
    warden = [
        "scoreboard players add @e[tag=w_auf] br_cd 1",
        "tp @e[tag=w_auf,score_br_cd=%d] ~ ~%.3f ~" % (AUFSTIEG - 1, 3.0 / AUFSTIEG),
        "execute @e[tag=w_auf] ~ ~ ~ particle blockcrack %d %d %d 0.9 0.1 0.9 0.15 14 force @a %d" % (ax, B + 1, az, blockcrack),
        "execute @e[tag=w_auf,score_br_cd_min=1,score_br_cd=1] ~ ~ ~ playsound entity.elder_guardian.curse hostile @a[tag=br_in%d] %d %d %d 3 0.5" % (FINALE, ax, B + 1, az),
        "execute @e[tag=w_auf,score_br_cd_min=%d,score_br_cd=%d] ~ ~ ~ playsound block.gravel.break hostile @a[tag=br_in%d] %d %d %d 3 0.5" % (AUFSTIEG // 3, AUFSTIEG // 3, FINALE, ax, B + 1, az),
        "execute @e[tag=w_auf,score_br_cd_min=%d,score_br_cd=%d] ~ ~ ~ playsound block.gravel.break hostile @a[tag=br_in%d] %d %d %d 3 0.5" % (2 * AUFSTIEG // 3, 2 * AUFSTIEG // 3, FINALE, ax, B + 1, az),
        "execute @e[tag=w_auf,score_br_cd_min=%d] ~ ~ ~ " % AUFSTIEG + "summon wither_skeleton %d %d %d %s" % (ax, B + 1, az, WARDEN),
    ]
    for c in titel("@a[tag=br_in%d]" % FINALE, "DER WARDEN", "dark_aqua", "Er sieht dich nicht. Er hört dich."):
        warden.append("execute @e[tag=w_auf,score_br_cd_min=%d] ~ ~ ~ " % AUFSTIEG + c)
    warden += [
        "execute @e[tag=w_auf,score_br_cd_min=%d] ~ ~ ~ " % AUFSTIEG + "playsound entity.wither.spawn hostile @a[tag=br_in%d] %d %d %d 2 0.5" % (FINALE, ax, B + 1, az),
        "execute @e[tag=w_auf,score_br_cd_min=%d] ~ ~ ~ " % AUFSTIEG + "scoreboard players set %s br_wsp 1" % STATE,
        "execute @e[tag=w_auf,score_br_cd_min=%d] ~ ~ ~ " % AUFSTIEG + "scoreboard players set %s br_wl %d" % (STATE, WARDEN_LEBEN),
        "kill @e[tag=w_auf,score_br_cd_min=%d]" % AUFSTIEG,
        # Schallangriff alle 5 Sekunden (Vorwarnung eine Sekunde vorher)
        "scoreboard players add %s br_cd 1" % W,
        "execute @e[tag=br_warden,score_br_cd_min=80,score_br_cd=80] ~ ~ ~ playsound entity.elder_guardian.ambient hostile @a ~ ~ ~ 2 0.5",
        "execute @e[tag=br_warden,score_br_cd_min=80,score_br_cd=99] ~ ~ ~ particle spell ~ ~2.2 ~ 0.4 0.4 0.4 0.5 6 force",
        "execute @e[tag=br_warden,score_br_cd_min=100] ~ ~ ~ execute @a[r=16] ~ ~ ~ particle crit ~ ~0.2 ~ 0.6 0.1 0.6 0.5 25 force",
        "execute @e[tag=br_warden,score_br_cd_min=100] ~ ~ ~ execute @a[r=16] ~ ~ ~ particle explode ~ ~0.2 ~ 0.6 0.1 0.6 0.05 12 force",
        "execute @e[tag=br_warden,score_br_cd_min=100] ~ ~ ~ particle explode ~ ~2 ~ 0.3 0.3 0.3 0.1 20 force",
        "execute @e[tag=br_warden,score_br_cd_min=100] ~ ~ ~ playsound entity.wither.shoot hostile @a ~ ~ ~ 3 0.5",
        "execute @e[tag=br_warden,score_br_cd_min=100] ~ ~ ~ effect @a[r=16] instant_damage 1 1 true",
        "scoreboard players set @e[tag=br_warden,score_br_cd_min=100] br_cd 0",
        "execute @e[tag=br_state,score_br_t2_min=0,score_br_t2=0] ~ ~ ~ execute %s ~ ~ ~ effect @a[r=28] blindness 2 0 true" % W,
        "execute @e[tag=br_state,score_br_t_min=0,score_br_t=0] ~ ~ ~ execute %s ~ ~ ~ playsound block.note.basedrum hostile @a ~ ~ ~ 2 0.5" % W,
        "execute %s ~ ~ ~ particle depthsuspend ~ ~1.5 ~ 0.6 1 0.6 0 4" % W,
        "execute @e[tag=br_state,score_br_wsp=0,score_br_t_min=0,score_br_t=0] ~ ~ ~ execute @a[tag=br_in%d] ~ ~ ~ playsound block.note.basedrum ambient @s ~ ~ ~ 1 0.5" % FINALE,
        # Sieg (nach allen Leben)
        "scoreboard players set @e[tag=br_state,score_br_wsp_min=1,score_br_sieg=0] br_wtot 1",
        "execute %s ~ ~ ~ scoreboard players set %s br_wtot 0" % (W, STATE),
        "scoreboard players remove @e[tag=br_state,score_br_wtot_min=1] br_wl 1",
    ]
    R = "execute @e[tag=br_state,score_br_wtot_min=1,score_br_wl_min=1] ~ ~ ~ "
    for c in titel("@a[tag=br_in%d]" % FINALE, "ER LEBT NOCH", "dark_aqua", "Der Warden wird nur noch wütender …"):
        warden.append(R + c)
    warden += [
        R + "particle blockcrack %d %d %d 1.2 0.3 1.2 0.2 80 force @a %d" % (ax, B + 1, az, blockcrack),
        R + "playsound entity.wither.spawn hostile @a[tag=br_in%d] %d %d %d 2 0.6" % (FINALE, ax, B + 1, az),
        R + "summon wither_skeleton %d %d %d %s" % (ax, B + 1, az, WARDEN),
        "scoreboard players set @e[tag=br_state,score_br_wtot_min=1,score_br_wl_min=1] br_wtot 0",
    ]
    V = "execute @e[tag=br_state,score_br_wtot_min=1] ~ ~ ~ "
    for c in titel("@a[tag=br_in%d]" % FINALE, "GESCHAFFT!", "gold", "Du bist aus den Backrooms entkommen"):
        warden.append(V + c)
    feuer = ("{LifeTime:%d,FireworksItem:{id:\"minecraft:fireworks\",Count:1b,tag:{Fireworks:{Explosions:"
             "[{Type:1b,Flicker:1b,Colors:[I;3394764,16777215],FadeColors:[I;65535]}]}}}}")
    warden += [
        V + "playsound ui.toast.challenge_complete master @a[tag=br_in%d] %d %d %d 4 1" % (FINALE, ax, B + 1, az),
        V + "summon fireworks_rocket %d %d %d %s" % (ax + 3, B + 1, az, feuer % 25),
        V + "summon fireworks_rocket %d %d %d %s" % (ax - 3, B + 1, az, feuer % 30),
        V + "summon fireworks_rocket %d %d %d %s" % (ax, B + 1, az + 3, feuer % 35),
        V + gateway(ax, B + 1, az, (geo.sx, geo.sy, geo.sz)),
        V + "spawnpoint @a[tag=br_in%d] %d %d %d" % (FINALE, geo.sx, geo.sy, geo.sz),
        V + "give @a[tag=br_in%d] nether_star 1 0 {display:{Name:\"Herz des Wardens\"}}" % FINALE,
        V + "tellraw @a[tag=br_in%d] %s" % (FINALE, j({"text": "In der Mitte der Arena öffnet sich der Weg nach Hause.", "color": "aqua"})),
        V + "scoreboard players set %s br_sieg 1" % STATE,
        "scoreboard players set %s br_wtot 0" % STATE,
    ]

    return [start + eintritt, raetsel + spieler + mon, atmo, warden]


FLAGS = ["br_f%d" % lv for lv in range(ANZAHL_LEVEL + 1)] + [
    "br_wsp", "br_sieg", "br_wtot", "br_wl", "br_auf1", "br_auf3", "br_auf4", "br_t3", "br_t4"]


def objectives():
    return (["scoreboard objectives add start trigger",
             "scoreboard objectives add br_tode deathCount"]
            + ["scoreboard objectives add %s dummy" % o
               for o in ["br_t", "br_t2", "br_cd", "br_hold", "br_lv", "br_anz", "br_nah", "br_h1", "br_h3", "br_h4"]
               + FLAGS])
