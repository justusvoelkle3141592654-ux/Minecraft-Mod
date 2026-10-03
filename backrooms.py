"""Backrooms: drei Level und eine Boss-Arena mit dem Warden.

bau_befehle(geo)    -> Konsolenbefehle, die die Level in die Welt bauen
ketten(geo)         -> Befehlsblock-Ketten (je Liste von Befehlen) fuer die Spiellogik

Alle Level liegen unter dem Spawnpunkt (y ~ 20-35), damit ihre Chunks immer
geladen sind. Uebergaenge sind End-Gateway-Bloecke (in Eaglercraft stuerzen
/tp-Befehle auf Spieler ab, Gateways funktionieren).
"""

import json
import math
import random

import build
import modelle

B = 22                      # Hoehe des Fussbodens aller Level
STATE = "@e[tag=br_state]"


def j(obj):
    return json.dumps(obj, ensure_ascii=False, separators=(",", ":"))


def nbt_text(obj):
    return build.nbt_string(j(obj))


class Geo:
    """Lage aller Level relativ zum Spawnpunkt."""

    def __init__(self, sx, sz, oberflaeche_y):
        self.sx, self.sz, self.sy = sx, sz, oberflaeche_y
        z0 = sz - 18
        self.l0 = dict(x=sx - 102, z=z0, w=41, d=41, h=5)
        self.l1 = dict(x=sx - 56, z=z0, w=49, d=49, h=7)
        self.l2 = dict(x=sx - 2, z=z0, w=40, d=40, h=4)
        r = 17
        self.arena = dict(x=sx + 44, z=z0, w=2 * r + 1, d=2 * r + 1, h=12, r=r)
        self.ax, self.az = self.arena["x"] + r, self.arena["z"] + r
        self.start = {
            0: (self.l0["x"] + 2, B + 1, self.l0["z"] + 2),
            1: (self.l1["x"] + 3, B + 1, self.l1["z"] + 3),
            2: (self.l2["x"] + 1, B + 1, self.l2["z"] + 1),
            3: (self.ax, B + 1, self.az + r - 3),
        }
        self.zustand = (sx - 1, 10, sz)

    def region(self, lv):
        """Zielauswahl-Bereich (x,y,z,dx,dy,dz) eines Levels."""
        g = [self.l0, self.l1, self.l2, self.arena][lv]
        return "x=%d,y=%d,z=%d,dx=%d,dy=%d,dz=%d" % (g["x"], B, g["z"], g["w"] - 1, g["h"] + 1, g["d"] - 1)


# ---------------------------------------------------------------------------
# Bau
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
    """Geschlossene Huelle (dunkles Metall) um ein Level."""
    x0, z0, x1, z1 = g["x"] - 1, g["z"] - 1, g["x"] + g["w"], g["z"] + g["d"]
    return [fill(x0, B - 1, z0, x1, B + g["h"] + 2, z1, "concrete 15")]


def labyrinth(n, seed, extra):
    """Zellen-Labyrinth (Tiefensuche) mit zusaetzlich geoeffneten Waenden.
    Rueckgabe: Menge offener Kanten ((i,j),(i2,j2))."""
    r = random.Random(seed)
    besucht = {(0, 0)}
    stapel = [(0, 0)]
    offen = set()
    while stapel:
        i, j = stapel[-1]
        nb = [(i + di, j + dj) for di, dj in ((1, 0), (-1, 0), (0, 1), (0, -1))
              if 0 <= i + di < n and 0 <= j + dj < n and (i + di, j + dj) not in besucht]
        if not nb:
            stapel.pop()
            continue
        k = r.choice(nb)
        offen.add(tuple(sorted(((i, j), k))))
        besucht.add(k)
        stapel.append(k)
    for i in range(n):
        for j in range(n):
            for k in ((i + 1, j), (i, j + 1)):
                if k[0] < n and k[1] < n and r.random() < extra:
                    offen.add(tuple(sorted(((i, j), k))))
    return offen


def maze_bauen(g, zelle, material, seed, extra):
    """Fuellt das Level mit Wandmaterial und schneidet ein Labyrinth heraus."""
    x0, z0, h = g["x"], g["z"], g["h"]
    n = (g["w"] - 1) // zelle
    befehle = [fill(x0, B + 1, z0, x0 + g["w"] - 1, B + h, z0 + g["d"] - 1, material)]
    for i in range(n):
        for j in range(n):
            ax, az = x0 + i * zelle + 1, z0 + j * zelle + 1
            befehle.append(fill(ax, B + 1, az, ax + zelle - 2, B + h, az + zelle - 2, "air"))
    for (a, b) in labyrinth(n, seed, extra):
        (i, j), (i2, j2) = a, b
        if i2 > i:   # Wand in x-Richtung
            wx = x0 + i2 * zelle
            az = z0 + j * zelle + 1
            befehle.append(fill(wx, B + 1, az, wx, B + h, az + zelle - 2, "air"))
        else:
            wz = z0 + j2 * zelle
            ax = x0 + i * zelle + 1
            befehle.append(fill(ax, B + 1, wz, ax + zelle - 2, B + h, wz, "air"))
    return befehle, n


def level0(geo):
    """Die gelben Raeume: Tapete, feuchter Teppich, Rasterdecke mit Leuchtstoffroehren."""
    g = geo.l0
    x0, z0, h = g["x"], g["z"], g["h"]
    bef = huelle(g)
    bef.append(fill(x0, B, z0, x0 + g["w"] - 1, B, z0 + g["d"] - 1, "stained_glass 12"))
    bef.append(fill(x0, B + h + 1, z0, x0 + g["w"] - 1, B + h + 1, z0 + g["d"] - 1, "concrete 0"))
    m, n = maze_bauen(g, 4, "sponge 0", 11, 0.38)
    bef += m
    r = random.Random(12)
    # ein paar grosse offene Saele (2x2 Zellen ohne Waende)
    for _ in range(4):
        i, j = r.randrange(1, n - 2), r.randrange(1, n - 2)
        bef.append(fill(x0 + i * 4 + 1, B + 1, z0 + j * 4 + 1, x0 + i * 4 + 7, B + h, z0 + j * 4 + 7, "air"))
    lampen, dunkel = [], []
    for i in range(n):
        for j in range(n):
            p = (x0 + i * 4 + 2, B + h + 1, z0 + j * 4 + 2)
            if r.random() < 0.72 or (i, j) in ((0, 0), (n - 1, n - 1)):
                lampen.append(p)
                bef.append("setblock %d %d %d sea_lantern" % p)
            else:
                dunkel.append((p[0], B + 1, p[2]))
    ex = (x0 + (n - 1) * 4 + 2, B + 1, z0 + (n - 1) * 4 + 2)
    bef.append(gateway(*ex, geo.start[1]))
    bef.append(schild(ex[0] + 1, B + 3, ex[2], 4, ["", {"text": "NOTAUSGANG", "color": "dark_green", "bold": True},
                                                   {"text": "→ Level 1"}, ""]))
    flacker = r.sample(lampen[1:-1], 5)
    return bef, ex, flacker, dunkel


def hound_punkte(geo):
    g = geo.l1
    return [(g["x"] + 18, B + 1, g["z"] + 26), (g["x"] + 34, B + 1, g["z"] + 10),
            (g["x"] + 26, B + 1, g["z"] + 42), (g["x"] + 42, B + 1, g["z"] + 34)]


def level1(geo):
    """Die Lagerhalle: Beton, Saeulen, Kistenstapel, Pfuetzen, flackerndes Licht."""
    g = geo.l1
    x0, z0, h, w, d = g["x"], g["z"], g["h"], g["w"], g["d"]
    bef = huelle(g)
    bef.append(fill(x0, B, z0, x0 + w - 1, B, z0 + d - 1, "stained_glass 7"))
    bef.append(fill(x0, B + h + 1, z0, x0 + w - 1, B + h + 1, z0 + d - 1, "concrete 8"))
    bef.append(fill(x0, B + 1, z0, x0 + w - 1, B + h, z0 + d - 1, "air"))
    bef.append(fill(x0 - 1, B + 1, z0 - 1, x0 + w, B + h, z0 - 1, "concrete 7"))
    bef.append(fill(x0 - 1, B + 1, z0 + d, x0 + w, B + h, z0 + d, "concrete 7"))
    bef.append(fill(x0 - 1, B + 1, z0 - 1, x0 - 1, B + h, z0 + d, "concrete 7"))
    bef.append(fill(x0 + w, B + 1, z0 - 1, x0 + w, B + h, z0 + d, "concrete 7"))
    r = random.Random(21)
    for i in range(5):
        for j in range(5):
            px, pz = x0 + 6 + 8 * i, z0 + 6 + 8 * j
            bef.append(fill(px, B + 1, pz, px + 1, B + h, pz + 1, "concrete 8"))
    # halbhohe Trennwaende
    for _ in range(7):
        if r.random() < 0.5:
            px, pz, l = x0 + r.randrange(8, w - 12), z0 + r.randrange(8, d - 8), r.randrange(5, 10)
            bef.append(fill(px, B + 1, pz, px + l, B + 4, pz, "concrete 7"))
        else:
            px, pz, l = x0 + r.randrange(8, w - 8), z0 + r.randrange(8, d - 12), r.randrange(5, 10)
            bef.append(fill(px, B + 1, pz, px, B + 4, pz + l, "concrete 7"))
    # Kistenstapel
    for _ in range(26):
        px, pz = x0 + r.randrange(6, w - 6), z0 + r.randrange(6, d - 6)
        bef.append(fill(px, B + 1, pz, px + r.randrange(0, 2), B + r.randrange(1, 4), pz + r.randrange(0, 2), "stained_glass 8"))
    # Pfuetzen
    for _ in range(14):
        px, pz = x0 + r.randrange(2, w - 2), z0 + r.randrange(2, d - 2)
        bef.append("setblock %d %d %d water" % (px, B, pz))
    lampen = []
    for i in range(8):
        for j in range(8):
            p = (x0 + 3 + 6 * i, B + h + 1, z0 + 3 + 6 * j)
            if r.random() < 0.7 or (i, j) == (0, 0):
                lampen.append(p)
                bef.append("setblock %d %d %d sea_lantern" % p)
    # Spawnpunkte der Hounds freiraeumen
    for (px, py, pz) in hound_punkte(geo):
        bef.append(fill(px - 1, B + 1, pz - 1, px + 1, B + 3, pz + 1, "air"))
    # Ausgang: Aufzugstuer an der Suedwand
    ex = (x0 + w - 4, B + 1, z0 + d - 1)
    bef.append(fill(ex[0] - 2, B + 1, ex[2] - 2, ex[0] + 2, B + 3, ex[2], "air"))
    bef.append(fill(ex[0] - 1, B + 1, ex[2], ex[0] - 1, B + 3, ex[2], "concrete 8"))
    bef.append(fill(ex[0] + 1, B + 1, ex[2], ex[0] + 1, B + 3, ex[2], "concrete 8"))
    bef.append(fill(ex[0] - 1, B + 4, ex[2], ex[0] + 1, B + 4, ex[2], "concrete 8"))
    bef.append(gateway(*ex, geo.start[2]))
    bef.append(schild(ex[0], B + 3, ex[2], 2, ["", {"text": "AUFZUG", "color": "dark_red", "bold": True},
                                               {"text": "→ Level 2"}, ""]))
    bef.append("setblock %d %d %d sea_lantern" % (ex[0], B + h + 1, ex[2] - 1))
    flacker = r.sample(lampen[1:], 6)
    return bef, ex, flacker


def level2(geo):
    """Die Rohrtunnel: enge Gaenge, Rohre, rotes Notlicht."""
    g = geo.l2
    x0, z0, h = g["x"], g["z"], g["h"]
    bef = huelle(g)
    bef.append(fill(x0, B, z0, x0 + g["w"] - 1, B, z0 + g["d"] - 1, "stained_glass 15"))
    bef.append(fill(x0, B + h + 1, z0, x0 + g["w"] - 1, B + h + 1, z0 + g["d"] - 1, "concrete 15"))
    m, n = maze_bauen(g, 3, "concrete 9", 31, 0.12)
    bef += m
    bef.append(fill(x0, B + 3, z0, x0 + g["w"] - 1, B + 3, z0 + g["d"] - 1, "concrete 1", "replace concrete 9"))
    for zz in range(z0 + 2, z0 + g["d"], 6):
        bef.append(fill(x0, B + h + 1, zz, x0 + g["w"] - 1, B + h + 1, zz, "concrete 1"))
    r = random.Random(32)
    for i in range(n):
        for j in range(n):
            if r.random() < 0.22 and (i, j) != (0, 0):
                bef.append("setblock %d %d %d redstone_torch 5" % (x0 + i * 3 + 1 + r.randrange(2), B + 1, z0 + j * 3 + 1 + r.randrange(2)))
    ex = (x0 + (n - 1) * 3 + 2, B + 1, z0 + (n - 1) * 3 + 2)
    bef.append(gateway(*ex, geo.start[3]))
    bef.append(schild(ex[0], B + 3, ex[2], 2, ["", {"text": "WARTUNGSSCHACHT", "color": "gold", "bold": True},
                                                   {"text": "→ ???"}, ""]))
    bef.append("setblock %d %d %d redstone_torch 5" % (ex[0] - 1, B + 1, ex[2]))
    return bef, ex


def arena(geo):
    """Deep Dark: runde Sculk-Arena, aus deren Mitte der Warden steigt."""
    g = geo.arena
    r, h, ax, az = g["r"], g["h"], geo.ax, geo.az
    bef = huelle(g)
    bef.append(fill(g["x"], B, g["z"], g["x"] + g["w"] - 1, B + h + 1, g["z"] + g["d"] - 1, "concrete 3"))
    for dz in range(-r, r + 1):
        w = int(math.sqrt(r * r - dz * dz))
        bef.append(fill(ax - w, B, az + dz, ax + w, B, az + dz, "stained_glass 9"))
        bef.append(fill(ax - w, B + 1, az + dz, ax + w, B + h, az + dz, "air"))
    rnd = random.Random(41)
    # Sculk an den Waenden und an der Decke
    for _ in range(140):
        a = rnd.uniform(0, 2 * math.pi)
        x, z = ax + int(round((r + 0.6) * math.cos(a))), az + int(round((r + 0.6) * math.sin(a)))
        y = B + rnd.randrange(1, h + 1)
        bef.append("setblock %d %d %d concrete 11" % (x, y, z))
    for _ in range(60):
        a, rr = rnd.uniform(0, 2 * math.pi), rnd.uniform(0, r - 1)
        bef.append("setblock %d %d %d concrete 11" % (ax + int(rr * math.cos(a)), B + h + 1, az + int(rr * math.sin(a))))
    # leuchtende Sculk-Katalysatoren im Boden und an der Decke
    for _ in range(14):
        a, rr = rnd.uniform(0, 2 * math.pi), rnd.uniform(4, r - 2)
        bef.append("setblock %d %d %d glowstone" % (ax + int(rr * math.cos(a)), B, az + int(rr * math.sin(a))))
    for _ in range(8):
        a, rr = rnd.uniform(0, 2 * math.pi), rnd.uniform(2, r - 3)
        bef.append("setblock %d %d %d glowstone" % (ax + int(rr * math.cos(a)), B + h + 1, az + int(rr * math.sin(a))))
    # Ring um die Mitte (dort erscheint der Warden)
    for dx in range(-2, 3):
        for dz in range(-2, 3):
            if max(abs(dx), abs(dz)) == 2:
                bef.append("setblock %d %d %d glowstone" % (ax + dx, B, az + dz))
    return bef


def bau_befehle(geo):
    b0, _, _, _ = level0(geo)
    b1, _, _ = level1(geo)
    b2, _ = level2(geo)
    return b0 + b1 + b2 + arena(geo)


# ---------------------------------------------------------------------------
# Monster
# ---------------------------------------------------------------------------

def monster_nbt(name, anzeigename, leben, tempo, schaden, extra_effekte=""):
    dmg = modelle.MONSTER_DAMAGE[name][0]
    zombie = "IsBaby:0b," if name != "warden" else ""
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


SMILER = monster_nbt("smiler", "Smiler", 60, "0.27", 7)
HOUND = monster_nbt("hound", "Hound", 50, "0.34", 5)
HAUTDIEB = monster_nbt("hautdieb", "Hautdieb", 90, "0.32", 10)
WARDEN = monster_nbt("warden", "Warden", 1000, "0.3", 16,
                     ",{Id:11b,Amplifier:3b,Duration:2147483647,ShowParticles:0b}")


WARDEN_LEBEN = 3            # so oft muss der Warden besiegt werden
AUFSTIEG = 100              # Ticks, bis der Warden aus dem Boden gestiegen ist


def titel(sel, titel_text, farbe, untertitel):
    return [
        "title %s times 10 80 25" % sel,
        "title %s subtitle %s" % (sel, j({"text": untertitel, "color": "gray", "italic": True})),
        "title %s title %s" % (sel, j({"text": titel_text, "color": farbe, "bold": True})),
    ]


# ---------------------------------------------------------------------------
# Befehlsketten
# ---------------------------------------------------------------------------

def ketten(geo):
    _, ex0, flacker0, dunkel0 = level0(geo)
    _, ex1, flacker1 = level1(geo)
    sx, sy, sz = geo.sx, geo.sy, geo.sz
    ax, az = geo.ax, geo.az
    l0, l1, l2 = geo.l0, geo.l1, geo.l2
    zx, zy, zz = geo.zustand
    zustand_nbt = "{Marker:1b,Invisible:1b,NoGravity:1b,Tags:[br_state]}"
    S = "@a[score_start_min=1]"

    # --- Start (/start bzw. /trigger start set 1) und Zeitgeber ---
    start = [
        "scoreboard players enable @a start",
    ] + ["scoreboard players add %s %s 0" % (STATE, o) for o in FLAGS] + [
        "scoreboard players add %s br_t 1" % STATE,
        "scoreboard players set @e[tag=br_state,score_br_t_min=16] br_t 0",
        "scoreboard players add %s br_t2 1" % STATE,
        "scoreboard players set @e[tag=br_state,score_br_t2_min=300] br_t2 0",
        "execute %s ~ ~ ~ kill @e[tag=br_mob]" % S,
        "execute %s ~ ~ ~ kill %s" % (S, STATE),
        "execute %s ~ ~ ~ summon armor_stand %d %d %d %s" % (S, zx, zy, zz, zustand_nbt),
        "execute %s ~ ~ ~ setblock %d %d %d air" % (S, ax, B + 1, az),
        "execute %s ~ ~ ~ clear @s carrot_on_a_stick %d" % (S, build.LAMPE_DAMAGE),
        build.give(S, *build.LAMPE),
        "execute %s ~ ~ ~ summon armor_stand ~ ~ ~ {Marker:1b,Invisible:1b,NoGravity:1b,Tags:[br_gw]}" % S,
        "execute %s ~ ~ ~ %s" % (S, gateway(0, 0, 0, geo.start[0]).replace("setblock 0 0 0", "setblock ~ ~ ~")),
        "execute %s ~ ~ ~ playsound entity.endermen.teleport master @s ~ ~ ~ 1 0.5" % S,
        "tellraw %s %s" % (S, j({"text": "Du rutschst durch den Boden der Realität …", "color": "gold", "italic": True})),
        "tellraw %s %s" % (S, j({"text": "Tipp: Zieh die Rüstung an – in den Backrooms ist es gefährlich.", "color": "gray"})),
        "scoreboard players set %s start 0" % S,
        "scoreboard players add @e[tag=br_gw] wp_alter 1",
        "execute @e[tag=br_gw,score_wp_alter_min=10] ~ ~ ~ setblock ~ ~ ~ air",
        "kill @e[tag=br_gw,score_wp_alter_min=10]",
    ]

    # --- Level betreten: Titel, Monster (einmal pro Durchgang) ---
    info = {
        0: ("LEVEL 0", "yellow", "Die gelben Räume – finde den Notausgang", "block.portal.ambient"),
        1: ("LEVEL 1", "gray", "Die Lagerhalle – das Licht flackert", "ambient.cave"),
        2: ("LEVEL 2", "dark_red", "Die Rohrtunnel – nimm die Taschenlampe", "block.fire.extinguish"),
        3: ("LEVEL 3", "dark_aqua", "Deep Dark – sei leise …", "entity.elder_guardian.curse"),
    }
    r = random.Random(77)
    spawns = {
        0: [(p[0], B + 1, p[2], SMILER) for p in r.sample(dunkel0, min(4, len(dunkel0)))],
        1: [(x, y, z, HOUND) for (x, y, z) in hound_punkte(geo)],
        2: [(l2["x"] + i * 3 + 1, B + 1, l2["z"] + jj * 3 + 1, HAUTDIEB) for i, jj in ((6, 6), (11, 3), (3, 11), (10, 10))],
        3: [],
    }
    level = []
    for lv in range(4):
        sel = "@a[tag=br_in%d]" % lv
        level.append("scoreboard players tag @a remove br_in%d" % lv)
        level.append("scoreboard players tag @a[%s] add br_in%d" % (geo.region(lv), lv))
        vor = "execute @e[tag=br_state,score_br_f%d=0] ~ ~ ~ execute %s ~ ~ ~ " % (lv, sel)
        t, farbe, ut, ton = info[lv]
        for c in titel("@s", t, farbe, ut):
            level.append(vor + c)
        level.append(vor + "playsound %s master @s ~ ~ ~ 1 0.6" % ton)
        level.append(vor + "spawnpoint @s %d %d %d" % geo.start[lv])
        for x, y, z, nbt in spawns[lv]:
            level.append(vor + "summon zombie %d %d %d %s" % (x, y, z, nbt))
        if lv == 3:
            # Der Warden steigt aus dem Boden (reglose Huelle mit Modell, 3 Sekunden)
            level.append(vor + "summon wither_skeleton %d %.1f %d {Tags:[br_mob,w_auf],NoAI:1b,NoGravity:1b,Silent:1b,"
                         "Invulnerable:1b,PersistenceRequired:1b,DeathLootTable:\"minecraft:empty\","
                         "ActiveEffects:[{Id:14b,Amplifier:0b,Duration:2147483647,ShowParticles:0b}],"
                         "ArmorDropChances:[0f,0f,0f,0f],Rotation:[0f,0f],ArmorItems:[{},{},{},{id:\"minecraft:diamond_hoe\",Count:1b,Damage:%ds,"
                         "tag:{Unbreakable:1b}}]}" % (ax, B + 1 - 3.0, az, modelle.MONSTER_DAMAGE["warden"][0]))
        level.append("execute %s ~ ~ ~ scoreboard players set %s br_f%d 1" % (sel, STATE, lv))

    # --- Atmosphaere: flackernde Lampen, Geraeusche, Dampf ---
    atmo = []
    for k, (x, y, z) in enumerate(flacker0 + flacker1):
        t0 = (k * 47) % 280 + 5
        atmo.append("execute @e[tag=br_state,score_br_t2_min=%d,score_br_t2=%d] ~ ~ ~ setblock %d %d %d concrete %d"
                    % (t0, t0, x, y, z, 0 if k < len(flacker0) else 8))
        atmo.append("execute @e[tag=br_state,score_br_t2_min=%d,score_br_t2=%d] ~ ~ ~ setblock %d %d %d sea_lantern"
                    % (t0 + 3, t0 + 3, x, y, z))
    atmo += [
        "execute @e[tag=br_state,score_br_t2_min=120,score_br_t2=120] ~ ~ ~ execute @a[tag=br_in0] ~ ~ ~ playsound block.portal.ambient ambient @s ~ ~ ~ 0.25 2",
        "execute @e[tag=br_state,score_br_t2_min=200,score_br_t2=200] ~ ~ ~ execute @a[tag=br_in1] ~ ~ ~ playsound ambient.cave ambient @s ~ ~ ~ 0.8 0.7",
        "execute @e[tag=br_state,score_br_t2_min=0,score_br_t2=0] ~ ~ ~ execute @a[tag=br_in2] ~ ~ ~ playsound block.fire.extinguish ambient @s ~ ~2 ~3 0.4 0.5",
        "execute @a[tag=br_in2] ~ ~ ~ particle cloud ~ ~2.6 ~ 4 0.1 4 0.005 1",
        "execute @a[tag=br_in0] ~ ~ ~ particle depthsuspend ~ ~1 ~ 4 2 4 0 2",
        "execute @a[tag=br_in3] ~ ~ ~ particle townaura ~ ~1 ~ 6 3 6 0 6",
    ]

    # --- Normale Monster, die in den dunklen Leveln entstehen, sofort entfernen ---
    alles = "x=%d,y=%d,z=%d,dx=%d,dy=%d,dz=%d" % (l0["x"] - 1, B - 1, l0["z"] - 1,
                                                  geo.arena["x"] + geo.arena["w"] - l0["x"] + 1, 16, 50)
    mon = ["tp @e[type=%s,tag=!br_mob,%s] ~ -100 ~" % (t, alles)
           for t in ("zombie", "skeleton", "creeper", "spider", "enderman", "witch", "slime",
                     "zombie_villager", "bat")]
    # --- Monster: Animation und Geraeusche ---
    for name, (a, b) in modelle.MONSTER_DAMAGE.items():
        mon.append("execute @e[tag=br_state,score_br_t_min=0,score_br_t=0] ~ ~ ~ replaceitem entity @e[tag=br_%s] slot.armor.head diamond_hoe 1 %d {Unbreakable:1b}" % (name, a))
        mon.append("execute @e[tag=br_state,score_br_t_min=8,score_br_t=8] ~ ~ ~ replaceitem entity @e[tag=br_%s] slot.armor.head diamond_hoe 1 %d {Unbreakable:1b}" % (name, b))
    for name, ton, t0 in (("smiler", "entity.vex.ambient", 40), ("hound", "entity.wolf.growl", 90),
                          ("hautdieb", "entity.villager.no", 150)):
        mon.append("execute @e[tag=br_state,score_br_t2_min=%d,score_br_t2=%d] ~ ~ ~ execute @e[tag=br_%s] ~ ~ ~ playsound %s hostile @a ~ ~ ~ 1.2 0.5" % (t0, t0, name, ton))
    mon.append("execute @e[tag=br_state,score_br_t2_min=%d,score_br_t2=%d] ~ ~ ~ execute @e[tag=br_hautdieb] ~ ~ ~ playsound entity.player.breath hostile @a ~ ~ ~ 1 0.6" % (220, 220))

    # --- Warden ---
    blockcrack = 251 + (11 << 12)   # Sculk-Block (blauer Beton) fuer Bruchpartikel
    W = "@e[tag=br_warden]"
    warden = [
        "scoreboard players add @e[tag=w_auf] br_cd 1",
        "tp @e[tag=w_auf,score_br_cd=%d] ~ ~%.3f ~" % (AUFSTIEG - 1, 3.0 / AUFSTIEG),
        "execute @e[tag=w_auf] ~ ~ ~ particle blockcrack %d %d %d 0.9 0.1 0.9 0.15 14 force @a %d" % (ax, B + 1, az, blockcrack),
        "execute @e[tag=w_auf,score_br_cd_min=1,score_br_cd=1] ~ ~ ~ playsound entity.elder_guardian.curse hostile @a[tag=br_in3] %d %d %d 3 0.5" % (ax, B + 1, az),
        "execute @e[tag=w_auf,score_br_cd_min=%d,score_br_cd=%d] ~ ~ ~ playsound block.gravel.break hostile @a[tag=br_in3] %d %d %d 3 0.5" % (AUFSTIEG // 3, AUFSTIEG // 3, ax, B + 1, az),
        "execute @e[tag=w_auf,score_br_cd_min=%d,score_br_cd=%d] ~ ~ ~ playsound block.gravel.break hostile @a[tag=br_in3] %d %d %d 3 0.5" % (2 * AUFSTIEG // 3, 2 * AUFSTIEG // 3, ax, B + 1, az),
        "execute @e[tag=w_auf,score_br_cd_min=%d] ~ ~ ~ " % AUFSTIEG + "summon wither_skeleton %d %d %d %s" % (ax, B + 1, az, WARDEN),
    ]
    for c in titel("@a[tag=br_in3]", "DER WARDEN", "dark_aqua", "Er sieht dich nicht. Er hört dich."):
        warden.append("execute @e[tag=w_auf,score_br_cd_min=%d] ~ ~ ~ " % AUFSTIEG + c)
    warden += [
        "execute @e[tag=w_auf,score_br_cd_min=%d] ~ ~ ~ " % AUFSTIEG + "playsound entity.wither.spawn hostile @a[tag=br_in3] %d %d %d 2 0.5" % (ax, B + 1, az),
        "execute @e[tag=w_auf,score_br_cd_min=%d] ~ ~ ~ " % AUFSTIEG + "scoreboard players set %s br_wsp 1" % STATE,
        "execute @e[tag=w_auf,score_br_cd_min=%d] ~ ~ ~ " % AUFSTIEG + "scoreboard players set %s br_wl %d" % (STATE, WARDEN_LEBEN),
        "kill @e[tag=w_auf,score_br_cd_min=%d]" % AUFSTIEG,
        # Schallangriff alle 5 Sekunden (Vorwarnung nach 4 Sekunden)
        "scoreboard players add %s br_cd 1" % W,
        "execute @e[tag=br_warden,score_br_cd_min=80,score_br_cd=80] ~ ~ ~ playsound entity.elder_guardian.ambient hostile @a ~ ~ ~ 2 0.5",
        "execute @e[tag=br_warden,score_br_cd_min=80,score_br_cd=99] ~ ~ ~ particle spell ~ ~2.2 ~ 0.4 0.4 0.4 0.5 6 force",
        "execute @e[tag=br_warden,score_br_cd_min=100] ~ ~ ~ execute @a[r=16] ~ ~ ~ particle crit ~ ~0.2 ~ 0.6 0.1 0.6 0.5 25 force",
        "execute @e[tag=br_warden,score_br_cd_min=100] ~ ~ ~ execute @a[r=16] ~ ~ ~ particle explode ~ ~0.2 ~ 0.6 0.1 0.6 0.05 12 force",
        "execute @e[tag=br_warden,score_br_cd_min=100] ~ ~ ~ particle explode ~ ~2 ~ 0.3 0.3 0.3 0.1 20 force",
        "execute @e[tag=br_warden,score_br_cd_min=100] ~ ~ ~ playsound entity.wither.shoot hostile @a ~ ~ ~ 3 0.5",
        "execute @e[tag=br_warden,score_br_cd_min=100] ~ ~ ~ effect @a[r=16] instant_damage 1 1 true",
        "scoreboard players set @e[tag=br_warden,score_br_cd_min=100] br_cd 0",
        # Dunkelheit-Pulse und Herzschlag
        "execute @e[tag=br_state,score_br_t2_min=0,score_br_t2=0] ~ ~ ~ execute %s ~ ~ ~ effect @a[r=28] blindness 2 0 true" % W,
        "execute @e[tag=br_state,score_br_t_min=0,score_br_t=0] ~ ~ ~ execute %s ~ ~ ~ playsound block.note.basedrum hostile @a ~ ~ ~ 2 0.5" % W,
        "execute %s ~ ~ ~ particle depthsuspend ~ ~1.5 ~ 0.6 1 0.6 0 4" % W,
        # Herzschlag in der Arena, solange der Warden noch schlaeft
        "execute @e[tag=br_state,score_br_wsp=0,score_br_t_min=0,score_br_t=0] ~ ~ ~ execute @a[tag=br_in3] ~ ~ ~ playsound block.note.basedrum ambient @s ~ ~ ~ 1 0.5",
        # Sieg
        "scoreboard players set @e[tag=br_state,score_br_wsp_min=1,score_br_sieg=0] br_wtot 1",
        "execute %s ~ ~ ~ scoreboard players set %s br_wtot 0" % (W, STATE),
        # Der Warden hat mehrere Leben: er steigt wieder aus dem Boden, bis keines mehr uebrig ist
        "scoreboard players remove @e[tag=br_state,score_br_wtot_min=1] br_wl 1",
    ]
    R = "execute @e[tag=br_state,score_br_wtot_min=1,score_br_wl_min=1] ~ ~ ~ "
    for c in titel("@a[tag=br_in3]", "ER LEBT NOCH", "dark_aqua", "Der Warden wird nur noch wütender …"):
        warden.append(R + c)
    warden += [
        R + "particle blockcrack %d %d %d 1.2 0.3 1.2 0.2 80 force @a %d" % (ax, B + 1, az, blockcrack),
        R + "playsound entity.wither.spawn hostile @a[tag=br_in3] %d %d %d 2 0.6" % (ax, B + 1, az),
        R + "summon wither_skeleton %d %d %d %s" % (ax, B + 1, az, WARDEN),
        "scoreboard players set @e[tag=br_state,score_br_wtot_min=1,score_br_wl_min=1] br_wtot 0",
    ]
    V = "execute @e[tag=br_state,score_br_wtot_min=1] ~ ~ ~ "
    for c in titel("@a[tag=br_in3]", "GESCHAFFT!", "gold", "Du hast den Warden besiegt"):
        warden.append(V + c)
    feuer = ("{LifeTime:%d,FireworksItem:{id:\"minecraft:fireworks\",Count:1b,tag:{Fireworks:{Explosions:"
             "[{Type:1b,Flicker:1b,Colors:[I;3394764,16777215],FadeColors:[I;65535]}]}}}}")
    warden += [
        V + "playsound ui.toast.challenge_complete master @a[tag=br_in3] %d %d %d 4 1" % (ax, B + 1, az),
        V + "summon fireworks_rocket %d %d %d %s" % (ax + 3, B + 1, az, feuer % 25),
        V + "summon fireworks_rocket %d %d %d %s" % (ax - 3, B + 1, az, feuer % 30),
        V + "summon fireworks_rocket %d %d %d %s" % (ax, B + 1, az + 3, feuer % 35),
        V + gateway(ax, B + 1, az, (sx, sy, sz)),
        V + "spawnpoint @a[tag=br_in3] %d %d %d" % (sx, sy, sz),
        V + "give @a[tag=br_in3] nether_star 1 0 {display:{Name:\"Herz des Wardens\"}}",
        V + "tellraw @a[tag=br_in3] %s" % j({"text": "In der Mitte der Arena öffnet sich der Weg zurück.", "color": "aqua"}),
        V + "scoreboard players set %s br_sieg 1" % STATE,
        "scoreboard players set %s br_wtot 0" % STATE,
    ]

    # --- Taschenlampe: Nachtsicht, solange sie in der Hand ist ---
    lampe = [
        "scoreboard players set @a br_hold 0",
        "scoreboard players set @a br_hold 1 {SelectedItem:{tag:{br:1b}}}",
        "effect @a[score_br_hold_min=1] night_vision 12 0 true",
        "scoreboard players tag @a[score_br_hold_min=1] add br_nv",
        "effect @a[tag=br_nv,score_br_hold=0] night_vision 0",
        "scoreboard players tag @a[score_br_hold=0] remove br_nv",
    ]

    # --- Sonder-TNT: jede Explosion loest vier weitere aus ---
    tnt = [
        "execute @e[type=tnt,tag=!wp_tx] ~ ~ ~ particle fireworksSpark ~ ~1 ~ 0.05 0.05 0.05 0.03 1",
        "scoreboard players tag @e[type=tnt,tag=!wp_tx] add wp_mega {Fuse:2s}",
    ]
    for dx, dz in ((3, 0), (-3, 0), (0, 3), (0, -3)):
        tnt.append("execute @e[tag=wp_mega] ~ ~ ~ summon tnt ~%d ~ ~%d {Fuse:1s,Tags:[wp_tx]}" % (dx, dz))
    tnt += [
        "execute @e[tag=wp_mega] ~ ~ ~ particle lava ~ ~ ~ 2 1 2 0 40 force",
        "execute @e[tag=wp_mega] ~ ~ ~ playsound entity.lightning.thunder block @a ~ ~ ~ 3 0.8",
        "scoreboard players tag @e[tag=wp_mega] remove wp_mega",
    ]

    return [start + level, atmo + mon, warden, lampe + tnt]


FLAGS = ["br_f0", "br_f1", "br_f2", "br_f3", "br_wsp", "br_sieg", "br_wtot", "br_wl"]


def objectives():
    return (["scoreboard objectives add start trigger"]
            + ["scoreboard objectives add %s dummy" % o for o in ["br_t", "br_t2", "br_cd", "br_hold"] + FLAGS])
