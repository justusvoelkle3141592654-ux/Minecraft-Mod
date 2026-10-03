#!/usr/bin/env python3
"""Erzeugt alle Dateien des Waffenpacks fuer Minecraft 1.12 (Eaglercraft 1.12.x).

Aufruf: python3 build.py

Erzeugt:
  ressourcenpaket/                     Ressourcenpaket (Ordner)
  Waffenpack-Ressourcenpaket.zip       Ressourcenpaket (ZIP zum Importieren)
  befehle/einzelbefehle.txt            Einzelne Chat-Befehle (je max. 256 Zeichen)

Die fertige Welt (Waffenpack-Welt.zip) baut welt_bauen.py mit den Befehlen aus kette().

Alle Werte stehen unten in EINSTELLUNGEN und koennen dort geaendert werden.
"""

import json
import os
import shutil
import struct
import zipfile
import zlib

import grafik
import modelle

ROOT = os.path.dirname(os.path.abspath(__file__))

# ---------------------------------------------------------------------------
# EINSTELLUNGEN
# ---------------------------------------------------------------------------

# Minecraft 1.12 begrenzt den Angriffsschaden-Attributwert auf 2048.
# Grundschaden des Spielers ist 1, daher 2047 -> Gesamtschaden 2048.
SCHWERT_ATTRIBUT_BONUS = 2047

# Grundschaden der Pfeile aus Pistole und Bazooka (Vanilla-Pfeil: 2).
# Der tatsaechliche Schaden ist Grundschaden x Pfeilgeschwindigkeit (max. ca. 3).
PFEIL_SCHADEN = 2048

# Verzauberungsstufen werden in 1.12 als "short" gespeichert: Maximum 32767.
MAX_STUFE = 32767

# Verzauberungs-IDs aus Minecraft 1.12
PROTECTION = 0        # Schutz
FEATHER_FALLING = 2   # Federfall
SHARPNESS = 16        # Schaerfe
EFFICIENCY = 32       # Effizienz

RUESTUNG_SCHUTZ = 1000
FEDERFALL = 32000
SCHWERT_STUFE20_VERZAUBERUNG = SHARPNESS   # Annahme, siehe README
SCHWERT_STUFE20_STUFE = 20
SPITZHACKE_EFFIZIENZ = min(727000, MAX_STUFE)

GOLDAEPFEL_ANZAHL = 64
ENDERPERLEN_ANZAHL = 16
PFEILE_ANZAHL = 64

# Schadenswert (Metadaten), ueber den das Ressourcenpaket die eigenen Modelle zeigt
PISTOLE_DAMAGE = 1   # Bogen
BAZOOKA_DAMAGE = 2   # Bogen
SCHWERT_DAMAGE = 1   # Diamantschwert

LAMPE_DAMAGE = 1     # Karottenrute
KAROTTENRUTE_HALTBARKEIT = 25
BOGEN_HALTBARKEIT = 384
DIAMANTSCHWERT_HALTBARKEIT = 1561

# ---------------------------------------------------------------------------
# Items (NBT im Format von Minecraft 1.12, ohne Anfuehrungszeichen)
# ---------------------------------------------------------------------------


def ench(*paare):
    return "ench:[" + ",".join("{id:%ds,lvl:%ds}" % p for p in paare) + "]"


# (item, anzahl, damage, tag)
LAMPE = ("carrot_on_a_stick", 1, LAMPE_DAMAGE, "{Unbreakable:1b,br:1b,display:{Name:Taschenlampe}}")

ITEMS = [
    ("bow", 1, PISTOLE_DAMAGE, "{Unbreakable:1b,wp:1b,display:{Name:Pistole}}"),
    ("bow", 1, BAZOOKA_DAMAGE, "{Unbreakable:1b,wp:2b,display:{Name:Bazooka}}"),
    ("diamond_sword", 1, SCHWERT_DAMAGE,
     "{Unbreakable:1b,display:{Name:Schwert},AttributeModifiers:[{AttributeName:generic.attackDamage,"
     "Name:wp,Amount:%dd,Operation:0,UUIDLeast:1L,UUIDMost:1L,Slot:mainhand}]}" % SCHWERT_ATTRIBUT_BONUS),
    LAMPE,
    ("tnt", 64, 0, "{display:{Name:Sonder-TNT}}"),
    ("flint_and_steel", 1, 0, "{Unbreakable:1b}"),
    ("arrow", PFEILE_ANZAHL, 0, None),
    ("golden_apple", GOLDAEPFEL_ANZAHL, 1, None),
    ("ender_pearl", ENDERPERLEN_ANZAHL, 0, None),
    ("diamond_helmet", 1, 0, "{%s}" % ench((PROTECTION, RUESTUNG_SCHUTZ))),
    ("diamond_chestplate", 1, 0, "{%s}" % ench((PROTECTION, RUESTUNG_SCHUTZ))),
    ("diamond_leggings", 1, 0, "{%s}" % ench((PROTECTION, RUESTUNG_SCHUTZ))),
    ("diamond_boots", 1, 0, "{%s}" % ench((PROTECTION, RUESTUNG_SCHUTZ), (FEATHER_FALLING, FEDERFALL))),
    ("diamond_sword", 1, 0, "{%s}" % ench((SCHWERT_STUFE20_VERZAUBERUNG, SCHWERT_STUFE20_STUFE))),
    ("diamond_pickaxe", 1, 0, "{%s}" % ench((EFFICIENCY, SPITZHACKE_EFFIZIENZ))),
]


def give(ziel, item, anzahl, damage, tag):
    cmd = "give %s %s %d %d" % (ziel, item, anzahl, damage)
    return cmd + " " + tag if tag else cmd


# ---------------------------------------------------------------------------
# Pistole / Bazooka: Befehle, die jeden Tick laufen
# ---------------------------------------------------------------------------

# Rakete der Bazooka: unsichtbarer Ruestungsstaender, der das Raketenmodell
# (Diamanthacke mit Schadenswert RAKETE_DAMAGE) auf dem Kopf traegt und jeden
# Tick zum Bazooka-Pfeil versetzt wird. Die Neigung wird beim Abschuss aus der
# Blickrichtung des Spielers gewaehlt (7 Stufen), die Drehung vom Spieler kopiert.
RAKETE_DAMAGE = 10   # Diamanthacke
DIAMANTHACKE_HALTBARKEIT = 1561
RAKETE_KOPF_Y = 1.6  # Kopfhoehe ueber den Fuessen des Ruestungsstaenders
MAX_FLUGZEIT = 160   # Ticks (8 Sekunden)

NEIGUNGEN = [(-90, -60, -75), (-60, -30, -45), (-30, -10, -20), (-10, 10, 0),
             (10, 30, 20), (30, 60, 45), (60, 90, 75)]

RAKETE_NBT = ("{Invisible:1b,Marker:1b,NoGravity:1b,Invulnerable:1b,Tags:[wp_r,wp_rn],"
              "ArmorItems:[{},{},{},{id:\"minecraft:diamond_hoe\",Count:1b,Damage:%ds,tag:{Unbreakable:1b}}],"
              "Pose:{Head:[%%.1ff,0f,0f]}}" % RAKETE_DAMAGE)

TICK = [
    # Wer haelt gerade Pistole oder Bazooka?
    "scoreboard players tag @a remove wp_p",
    "scoreboard players tag @a remove wp_b",
    "scoreboard players tag @a add wp_p {SelectedItem:{tag:{wp:1b}}}",
    "scoreboard players tag @a add wp_b {SelectedItem:{tag:{wp:2b}}}",
    # Neue Pfeile in der Naehe dieser Spieler markieren (wp_pn / wp_bn = gerade abgefeuert)
    "execute @a[tag=wp_p] ~ ~ ~ scoreboard players tag @e[type=arrow,r=6,tag=!wp_alt] add wp_pn",
    "execute @a[tag=wp_b] ~ ~ ~ scoreboard players tag @e[type=arrow,r=6,tag=!wp_alt] add wp_bn",
    "scoreboard players tag @e[type=arrow] add wp_alt",
    # Pistole: Knall und Muendungsfeuer beim Schuss
    "execute @e[tag=wp_pn] ~ ~ ~ playsound entity.generic.explode master @a ~ ~ ~ 0.6 2",
    "execute @e[tag=wp_pn] ~ ~ ~ particle flame ~ ~ ~ 0.1 0.1 0.1 0.05 15 force",
    "scoreboard players tag @e[tag=wp_pn] add wp_p",
    "scoreboard players tag @e[tag=wp_p] remove wp_pn",
    # Bazooka: Rakete erzeugen, Rauch beim Abschuss
] + [
    "execute @e[tag=wp_bn] ~ ~ ~ execute @p[tag=wp_b,rxm=%d,rx=%d] ~ ~ ~ summon armor_stand ~ ~ ~ %s"
    % (von, bis, RAKETE_NBT % neigung) for von, bis, neigung in NEIGUNGEN
] + [
    "execute @e[tag=wp_rn] ~ ~ ~ tp @s @p[tag=wp_b]",
    "scoreboard players tag @e[tag=wp_rn] remove wp_rn",
    "execute @e[tag=wp_bn] ~ ~ ~ playsound entity.firework.launch master @a ~ ~ ~ 2 0.5",
    "execute @e[tag=wp_bn] ~ ~ ~ particle smoke ~ ~ ~ 0.2 0.2 0.2 0.02 10 force",
    "scoreboard players tag @e[tag=wp_bn] add wp_b",
    "scoreboard players tag @e[tag=wp_b] remove wp_bn",
    # Schaden erhoehen
    "entitydata @e[type=arrow,tag=wp_p] {damage:%dd}" % PFEIL_SCHADEN,
    "entitydata @e[type=arrow,tag=wp_b] {damage:%dd}" % PFEIL_SCHADEN,
    # Pistole: Funkenspur, Kugel verschwindet beim Einschlag in einer Rauchwolke
    "execute @e[type=arrow,tag=wp_p] ~ ~ ~ particle crit ~ ~ ~ 0 0 0 0 2 force",
    "scoreboard players tag @e[type=arrow,tag=wp_p] add wp_pweg {inGround:1b}",
    "execute @e[tag=wp_pweg] ~ ~ ~ particle smoke ~ ~ ~ 0.1 0.1 0.1 0.02 10 force",
    "kill @e[tag=wp_pweg]",
    # Bazooka-Pfeil im Boden: Explosion, Rakete und Pfeil entfernen
    "scoreboard players tag @e[type=arrow,tag=wp_b] add wp_boom {inGround:1b}",
    "execute @e[tag=wp_boom] ~ ~ ~ summon tnt ~ ~ ~ {Fuse:0}",
    "execute @e[tag=wp_boom] ~ ~ ~ particle hugeexplosion ~ ~ ~ 1 1 1 0 3 force",
    "execute @e[tag=wp_boom] ~ ~ ~ kill @e[tag=wp_r,c=1,r=6]",
    "kill @e[tag=wp_boom]",
    # Rakete fliegt mit dem Pfeil, Feuer- und Rauchspur. "teleport" statt "tp":
    # bei tp waeren ~ ~ ~ relativ zur Rakete selbst, bei teleport relativ zum Pfeil.
    "execute @e[type=arrow,tag=wp_b] ~ ~ ~ teleport @e[tag=wp_r,c=1] ~ ~-%.1f ~" % RAKETE_KOPF_Y,
    "execute @e[type=arrow,tag=wp_b] ~ ~ ~ particle flame ~ ~ ~ 0.15 0.15 0.15 0.01 4 force",
    "execute @e[type=arrow,tag=wp_b] ~ ~ ~ particle smoke ~ ~ ~ 0.15 0.15 0.15 0.01 3 force",
    # Rakete ohne Pfeil (Pfeil hat ein Lebewesen getroffen): dort explodieren
    "scoreboard players tag @e[tag=wp_r] add wp_rlos",
    "execute @e[type=arrow,tag=wp_b] ~ ~ ~ scoreboard players tag @e[tag=wp_r,r=4] remove wp_rlos",
    "execute @e[tag=wp_rlos] ~ ~%.1f ~ summon tnt ~ ~ ~ {Fuse:0}" % RAKETE_KOPF_Y,
    "kill @e[tag=wp_rlos]",
    # Aufraeumen: Geschosse, die laenger als MAX_FLUGZEIT Ticks fliegen, verschwinden.
    # (In Eaglercraft bewegen sich Objekte am Rand der Sichtweite nicht; sie blieben sonst
    # in der Luft haengen.) Das Ziel wp_alter legt welt_bauen.py an.
    "scoreboard players add @e[tag=wp_r] wp_alter 1",
    "scoreboard players add @e[type=arrow,tag=wp_b] wp_alter 1",
    "scoreboard players add @e[type=arrow,tag=wp_p] wp_alter 1",
    "execute @e[score_wp_alter_min=%d] ~ ~ ~ particle cloud ~ ~ ~ 0.3 0.3 0.3 0.02 10 force" % MAX_FLUGZEIT,
    "kill @e[score_wp_alter_min=%d]" % MAX_FLUGZEIT,
]


# ---------------------------------------------------------------------------
# Ausgabe: Funktionen, Befehle
# ---------------------------------------------------------------------------


def nbt_string(s):
    return '"' + s.replace("\\", "\\\\").replace('"', '\\"') + '"'


def schreibe(pfad, text):
    pfad = os.path.join(ROOT, pfad)
    os.makedirs(os.path.dirname(pfad), exist_ok=True)
    with open(pfad, "w", encoding="utf-8", newline="\n") as f:
        f.write(text)


def kette():
    """Befehle der Befehlsblock-Kette in der Welt (1 Wiederhol-Block, dann Ketten-Bloecke).

    Neue Spieler (ohne Markierung wp_hat) bekommen einmal alle Items,
    danach folgt die Logik fuer Pistole und Bazooka.
    """
    befehle = ["scoreboard players tag @a[tag=!wp_hat] add wp_neu"]
    befehle += [give("@a[tag=wp_neu]", *i) for i in ITEMS]
    befehle += [
        "tellraw @a[tag=wp_neu] " + json.dumps(
            [{"text": "Willkommen! ", "color": "gold", "bold": True},
             {"text": "Tippe ", "color": "white"}, {"text": "/start", "color": "yellow", "bold": True},
             {"text": ", um die Backrooms zu betreten.", "color": "white"}], ensure_ascii=False),
        "scoreboard players tag @a[tag=wp_neu] add wp_hat",
        "scoreboard players tag @a[tag=wp_neu] remove wp_neu",
    ]
    return befehle + TICK


def einzelbefehle():
    zeilen = ["/" + give("@p", *i) for i in ITEMS]
    for z in zeilen:
        assert len(z) <= 256, "Chat-Befehl zu lang (%d Zeichen): %s" % (len(z), z)
    schreibe("befehle/einzelbefehle.txt", "\n".join(zeilen) + "\n")


# ---------------------------------------------------------------------------
# Ressourcenpaket
# ---------------------------------------------------------------------------

PALETTE = {
    ".": (0, 0, 0, 0),
    "k": (25, 25, 28, 255),      # Umriss
    "g": (105, 108, 115, 255),   # Metall
    "h": (150, 154, 160, 255),   # Metall hell
    "b": (95, 62, 35, 255),      # Griff braun
    "o": (78, 94, 48, 255),      # Oliv
    "l": (110, 130, 70, 255),    # Oliv hell
    "r": (200, 30, 30, 255),     # Rot
    "d": (110, 10, 15, 255),     # Dunkelrot
    "y": (225, 180, 40, 255),    # Gold
    "W": (235, 235, 235, 255),   # Weiss
    "O": (245, 140, 20, 255),    # Flamme orange
    "F": (255, 230, 80, 255),    # Flamme gelb
    "M": (220, 180, 70, 255),    # Messing hell
    "N": (160, 120, 40, 255),    # Messing dunkel
    "C": (190, 95, 45, 255),     # Kupfer
}

SCHWERT = [
    "..............kk",
    ".............krk",
    "............krdk",
    "...........krdk.",
    "..........krdk..",
    ".........krdk...",
    "........krdk....",
    ".......krdk.....",
    "..kk..krdk......",
    "..kyykrdk.......",
    "...kyydk........",
    "....kyyk........",
    "...kbkyyk.......",
    "..kbk.kkyk......",
    "kkbk....kk......",
    "kyk.............",
]


# Farbfelder (je 4x4) fuer das Raketenmodell
RAKETE_TEXTUR = ["rrrrWWWWggggOOOO"] * 4 + ["FFFFddddkkkkhhhh"] * 4 + ["." * 16] * 8
FELD = {"r": (0, 0), "W": (4, 0), "g": (8, 0), "O": (12, 0),
        "F": (0, 4), "d": (4, 4), "k": (8, 4), "h": (12, 4)}

# Raketenmodell: Spitze zeigt nach Norden (-z), Laenge 48 Pixel
RAKETE_TEILE = [
    ([7, 7, -16], [9, 9, -13], "d"),           # Spitze
    ([5.5, 5.5, -13], [10.5, 10.5, -9], "r"),
    ([4, 4, -9], [12, 12, -5], "r"),
    ([3, 3, -5], [13, 13, 22], "r"),           # Rumpf
    ([2.5, 2.5, -1], [13.5, 13.5, 3], "W"),    # Streifen
    ([2.5, 2.5, 12], [13.5, 13.5, 15], "W"),
    ([7.5, 13, 14], [8.5, 19, 24], "d"),       # Flossen
    ([7.5, -3, 14], [8.5, 3, 24], "d"),
    ([-3, 7.5, 14], [3, 8.5, 24], "d"),
    ([13, 7.5, 14], [19, 8.5, 24], "d"),
    ([4.5, 4.5, 22], [11.5, 11.5, 25], "g"),   # Duese
    ([5.5, 5.5, 25], [10.5, 10.5, 29], "O"),   # Flamme
    ([6.5, 6.5, 29], [9.5, 9.5, 32], "F"),
]
RAKETE_GROESSE = 3   # Faktor auf dem Kopf (max. 4); 48 px * 3 * 0.625 / 16 = 5,6 Bloecke


def raketen_modell():
    teile = []
    for von, bis, farbe in RAKETE_TEILE:
        u, v = FELD[farbe]
        uv = [u + 0.5, v + 0.5, u + 3.5, v + 3.5]
        teile.append({"from": von, "to": bis,
                      "faces": {seite: {"uv": uv, "texture": "#t"}
                                for seite in ("north", "south", "east", "west", "up", "down")}})
    return {
        "textures": {"t": "items/waffenpack/rakete", "particle": "items/waffenpack/rakete"},
        "elements": teile,
        "display": {
            "head": {"rotation": [0, 0, 0], "translation": [0, 0, 0], "scale": [RAKETE_GROESSE] * 3},
            "gui": {"rotation": [30, 45, 0], "translation": [0, 0, 0], "scale": [0.35] * 3},
        },
    }


# Pfeil-Textur (32x32) als Patrone: Seitenansicht oben links (16x5), Rueckseite leer.
# Gilt fuer alle Pfeile im Spiel.
KUGEL_TEXTUR = ["." * 32,
                "......MMMMMMMCC." + "." * 16,
                "......MMMMMMMCCC" + "." * 16,
                "......NNNNNNNCC." + "." * 16] + ["." * 32] * 28


def png(pfad, raster):
    breite, hoehe = len(raster[0]), len(raster)
    assert all(len(z) == breite for z in raster)
    roh = b"".join(b"\x00" + b"".join(bytes(PALETTE[c]) for c in z) for z in raster)

    def chunk(typ, daten):
        return struct.pack(">I", len(daten)) + typ + daten + struct.pack(">I", zlib.crc32(typ + daten) & 0xFFFFFFFF)

    daten = (b"\x89PNG\r\n\x1a\n"
             + chunk(b"IHDR", struct.pack(">IIBBBBB", breite, hoehe, 8, 6, 0, 0, 0))
             + chunk(b"IDAT", zlib.compress(roh, 9))
             + chunk(b"IEND", b""))
    os.makedirs(os.path.dirname(pfad), exist_ok=True)
    with open(pfad, "wb") as f:
        f.write(daten)


def json_datei(pfad, obj):
    os.makedirs(os.path.dirname(pfad), exist_ok=True)
    with open(pfad, "w", encoding="utf-8", newline="\n") as f:
        json.dump(obj, f, indent=2)
        f.write("\n")


def unter(damage, haltbarkeit):
    # Das Praedikat "damage" ist Schaden / Haltbarkeit. Etwas kleiner waehlen,
    # damit Rundungsfehler nicht stoeren.
    return round(damage / haltbarkeit - 0.00001, 6)


def ressourcenpaket():
    rp = os.path.join(ROOT, "ressourcenpaket")
    if os.path.isdir(rp):
        shutil.rmtree(rp)
    json_datei(os.path.join(rp, "pack.mcmeta"),
               {"pack": {"pack_format": 3, "description": "Waffenpack + Backrooms"}})

    tex = os.path.join(rp, "assets/minecraft/textures/items/waffenpack")
    mod = os.path.join(rp, "assets/minecraft/models/item")
    png(os.path.join(tex, "schwert.png"), SCHWERT)
    json_datei(os.path.join(mod, "waffenpack", "schwert.json"),
               {"parent": "item/handheld", "textures": {"layer0": "items/waffenpack/schwert"}})

    # 3D-Gegenstaende
    for name, datei, funktion in (("pistole", "pistole3d", modelle.pistole),
                                  ("bazooka", "bazooka3d", modelle.bazooka),
                                  ("taschenlampe", "taschenlampe", modelle.taschenlampe)):
        atlas, modell = funktion()
        atlas.bild.speichern(os.path.join(tex, datei + ".png"))
        json_datei(os.path.join(mod, "waffenpack", name + ".json"), modell)
    json_datei(os.path.join(mod, "carrot_on_a_stick.json"), {
        "parent": "item/handheld_rod",
        "textures": {"layer0": "items/carrot_on_a_stick"},
        "overrides": [
            {"predicate": {"damaged": 0, "damage": unter(LAMPE_DAMAGE, KAROTTENRUTE_HALTBARKEIT)}, "model": "item/waffenpack/taschenlampe"},
            {"predicate": {"damaged": 1, "damage": 0}, "model": "item/carrot_on_a_stick"},
        ],
    })

    # Monster (je zwei Animationsbilder)
    hacke = [{"predicate": {"damaged": 0, "damage": unter(RAKETE_DAMAGE, DIAMANTHACKE_HALTBARKEIT)}, "model": "item/waffenpack/rakete"}]
    for name, (atlas_f, modell_f) in modelle.MONSTER.items():
        atlas = atlas_f()
        atlas.bild.speichern(os.path.join(tex, name + ".png"))
        for bild, dmg in zip(("a", "b"), modelle.MONSTER_DAMAGE[name]):
            json_datei(os.path.join(mod, "waffenpack", "%s_%s.json" % (name, bild)), modell_f(atlas, bild))
            hacke.append({"predicate": {"damaged": 0, "damage": unter(dmg, DIAMANTHACKE_HALTBARKEIT)},
                          "model": "item/waffenpack/%s_%s" % (name, bild)})
    hacke.sort(key=lambda o: o["predicate"]["damage"])
    hacke.append({"predicate": {"damaged": 1, "damage": 0}, "model": "item/diamond_hoe"})

    # Block-Texturen der Backrooms und das Sonder-TNT
    btex = os.path.join(rp, "assets/minecraft/textures/blocks")
    for name, funktion in grafik.BLOCK_TEXTUREN.items():
        funktion().speichern(os.path.join(btex, name + ".png"))
    for name, (streifen, meta) in grafik.animierte_bloecke().items():
        streifen.speichern(os.path.join(btex, name + ".png"))
        json_datei(os.path.join(btex, name + ".png.mcmeta"), meta)

    # Vanilla-Modell des Bogens (1.12.2) plus eigene Eintraege.
    # Es gilt der letzte passende Eintrag. "damaged": 0 trifft nur auf unzerbrechliche
    # oder unbeschaedigte Boegen zu; beschaedigte normale Boegen bleiben normal.
    bogen_ziehen = [
        ({"pulling": 1}, "item/bow_pulling_0"),
        ({"pulling": 1, "pull": 0.65}, "item/bow_pulling_1"),
        ({"pulling": 1, "pull": 0.9}, "item/bow_pulling_2"),
    ]
    overrides = [{"predicate": p, "model": m} for p, m in bogen_ziehen]
    overrides += [
        {"predicate": {"damaged": 0, "damage": unter(PISTOLE_DAMAGE, BOGEN_HALTBARKEIT)}, "model": "item/waffenpack/pistole"},
        {"predicate": {"damaged": 0, "damage": unter(BAZOOKA_DAMAGE, BOGEN_HALTBARKEIT)}, "model": "item/waffenpack/bazooka"},
        {"predicate": {"damaged": 1, "damage": 0}, "model": "item/bow"},
    ]
    overrides += [{"predicate": dict({"damaged": 1}, **p), "model": m} for p, m in bogen_ziehen]
    json_datei(os.path.join(mod, "bow.json"), {
        "parent": "item/generated",
        "textures": {"layer0": "items/bow_standby"},
        "display": {
            "thirdperson_righthand": {"rotation": [-80, 260, -40], "translation": [-1, -2, 2.5], "scale": [0.9, 0.9, 0.9]},
            "thirdperson_lefthand": {"rotation": [-80, -280, 40], "translation": [-1, -2, 2.5], "scale": [0.9, 0.9, 0.9]},
            "firstperson_righthand": {"rotation": [0, -90, 25], "translation": [1.13, 3.2, 1.13], "scale": [0.68, 0.68, 0.68]},
            "firstperson_lefthand": {"rotation": [0, 90, -25], "translation": [1.13, 3.2, 1.13], "scale": [0.68, 0.68, 0.68]},
        },
        "overrides": overrides,
    })

    json_datei(os.path.join(mod, "diamond_sword.json"), {
        "parent": "item/handheld",
        "textures": {"layer0": "items/diamond_sword"},
        "overrides": [
            {"predicate": {"damaged": 0, "damage": unter(SCHWERT_DAMAGE, DIAMANTSCHWERT_HALTBARKEIT)}, "model": "item/waffenpack/schwert"},
            {"predicate": {"damaged": 1, "damage": 0}, "model": "item/diamond_sword"},
        ],
    })

    png(os.path.join(tex, "rakete.png"), RAKETE_TEXTUR)
    json_datei(os.path.join(mod, "waffenpack", "rakete.json"), raketen_modell())
    json_datei(os.path.join(mod, "diamond_hoe.json"), {
        "parent": "item/handheld",
        "textures": {"layer0": "items/diamond_hoe"},
        "overrides": hacke,
    })
    png(os.path.join(rp, "assets/minecraft/textures/entity/projectiles/arrow.png"), KUGEL_TEXTUR)

    # ZIP: pack.mcmeta muss direkt im Hauptverzeichnis liegen
    zpfad = os.path.join(ROOT, "Waffenpack-Ressourcenpaket.zip")
    with zipfile.ZipFile(zpfad, "w", zipfile.ZIP_DEFLATED) as z:
        for ordner, _, dateien in sorted(os.walk(rp)):
            for d in sorted(dateien):
                voll = os.path.join(ordner, d)
                z.write(voll, os.path.relpath(voll, rp).replace(os.sep, "/"))


if __name__ == "__main__":
    ressourcenpaket()
    einzelbefehle()
    print("Fertig. Die Welt baut welt_bauen.py.")
