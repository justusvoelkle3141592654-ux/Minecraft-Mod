#!/usr/bin/env python3
"""Erzeugt alle Dateien des Waffenpacks fuer Minecraft 1.12 (Eaglercraft 1.12.x).

Aufruf: python3 build.py

Erzeugt:
  ressourcenpaket/                     Ressourcenpaket (Ordner)
  Waffenpack-Ressourcenpaket.zip       Ressourcenpaket (ZIP zum Importieren)
  welt/data/functions/waffenpack/      Funktionen fuer den Weltordner
  befehle/installer-befehlsblock.txt   Ein Befehl fuer einen Befehlsblock
  befehle/einzelbefehle.txt            Einzelne Chat-Befehle (je max. 256 Zeichen)

Alle Werte stehen unten in EINSTELLUNGEN und koennen dort geaendert werden.
"""

import json
import os
import shutil
import struct
import zipfile
import zlib

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

BOGEN_HALTBARKEIT = 384
DIAMANTSCHWERT_HALTBARKEIT = 1561

# ---------------------------------------------------------------------------
# Items (NBT im Format von Minecraft 1.12, ohne Anfuehrungszeichen)
# ---------------------------------------------------------------------------


def ench(*paare):
    return "ench:[" + ",".join("{id:%ds,lvl:%ds}" % p for p in paare) + "]"


# (item, anzahl, damage, tag)
ITEMS = [
    ("bow", 1, PISTOLE_DAMAGE, "{Unbreakable:1b,wp:1b,display:{Name:Pistole}}"),
    ("bow", 1, BAZOOKA_DAMAGE, "{Unbreakable:1b,wp:2b,display:{Name:Bazooka}}"),
    ("diamond_sword", 1, SCHWERT_DAMAGE,
     "{Unbreakable:1b,display:{Name:Schwert},AttributeModifiers:[{AttributeName:generic.attackDamage,"
     "Name:wp,Amount:%dd,Operation:0,UUIDLeast:1L,UUIDMost:1L,Slot:mainhand}]}" % SCHWERT_ATTRIBUT_BONUS),
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

TICK = [
    # Wer haelt gerade Pistole oder Bazooka?
    "scoreboard players tag @a remove wp_p",
    "scoreboard players tag @a remove wp_b",
    "scoreboard players tag @a add wp_p {SelectedItem:{tag:{wp:1b}}}",
    "scoreboard players tag @a add wp_b {SelectedItem:{tag:{wp:2b}}}",
    # Neue Pfeile in der Naehe dieser Spieler markieren
    "execute @a[tag=wp_p] ~ ~ ~ scoreboard players tag @e[type=arrow,r=6,tag=!wp_alt] add wp_p",
    "execute @a[tag=wp_b] ~ ~ ~ scoreboard players tag @e[type=arrow,r=6,tag=!wp_alt] add wp_b",
    "scoreboard players tag @e[type=arrow] add wp_alt",
    # Pfeilschaden erhoehen
    "entitydata @e[type=arrow,tag=wp_p] {damage:%dd}" % PFEIL_SCHADEN,
    "entitydata @e[type=arrow,tag=wp_b] {damage:%dd}" % PFEIL_SCHADEN,
    # Bazooka-Pfeil im Boden: Explosion
    "scoreboard players tag @e[type=arrow,tag=wp_b] add wp_boom {inGround:1b}",
    "execute @e[type=arrow,tag=wp_boom] ~ ~ ~ summon tnt ~ ~ ~ {Fuse:0}",
    "kill @e[type=arrow,tag=wp_boom]",
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


def funktionen():
    start = [give("@s", *i) for i in ITEMS]
    start.append("gamerule commandBlockOutput false")
    start.append("gamerule gameLoopFunction waffenpack:tick")
    schreibe("welt/data/functions/waffenpack/start.mcfunction", "\n".join(start) + "\n")
    schreibe("welt/data/functions/waffenpack/tick.mcfunction", "\n".join(TICK) + "\n")


def installer():
    """Ein Befehl fuer einen Befehlsblock: gibt alle Items und baut die Tick-Anlage.

    Aufbau (Technik "one command"): Ueber dem Befehlsblock landen ein
    Redstone-Block und eine Aktivierungsschiene. Darauf fahren Befehlsblock-Loren,
    die nacheinander ihre Befehle ausfuehren und danach alles wieder entfernen.
    Die Loren stehen 2 Bloecke ueber dem Befehlsblock.
    Die Tick-Anlage entsteht in der Reihe ab 2 Bloecke oestlich des Befehlsblocks.
    """
    befehle = [give("@p", *i) for i in ITEMS]
    befehle.append("gamerule commandBlockOutput false")
    for n, cmd in enumerate(TICK):
        block = "repeating_command_block" if n == 0 else "chain_command_block"
        befehle.append("setblock ~%d ~-2 ~ %s 5 replace {auto:1b,Command:%s}" % (2 + n, block, nbt_string(cmd)))
    # Aufraeumen: ein Befehlsblock ueber den Loren entfernt sich selbst, Schiene und Redstone-Block
    befehle.append("setblock ~ ~1 ~ command_block 0 replace {auto:1b,Command:%s}" % nbt_string("fill ~ ~ ~ ~ ~-2 ~ air"))
    befehle.append("kill @e[type=commandblock_minecart,r=1]")
    loren = ",".join("{id:commandblock_minecart,Command:%s}" % nbt_string(c) for c in befehle)
    cmd = ("summon falling_block ~ ~1 ~ {Block:redstone_block,Time:1,Passengers:["
           "{id:falling_block,Block:activator_rail,Time:1,Passengers:[%s]}]}" % loren)
    schreibe("befehle/installer-befehlsblock.txt", cmd + "\n")
    return cmd


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
}

PISTOLE = [
    "................",
    "................",
    "................",
    "................",
    "..kkkkkkkkkkkk..",
    "..khhhhhhhhhhhk.",
    "..kggggggggggggk",
    "..kkkkkkkkkkkkk.",
    "...kbbk.kk......",
    "...kbbk..k......",
    "...kbbkkkk......",
    "..kbbbk.........",
    "..kbbbk.........",
    "..kbbbk.........",
    "..kkkkk.........",
    "................",
]

BAZOOKA = [
    "................",
    "............kkk.",
    "...........kolkk",
    "..........kollok",
    ".........kollok.",
    "........kollok..",
    ".......kollok...",
    "......kollok....",
    ".....kollok.....",
    "....kollokk.....",
    "...kollokbk.....",
    "..kollok.kbk....",
    ".kollok...kk....",
    "kkollok.........",
    "kkkok...........",
    ".kkk............",
]

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


def png(pfad, raster):
    assert len(raster) == 16 and all(len(z) == 16 for z in raster)
    roh = b"".join(b"\x00" + b"".join(bytes(PALETTE[c]) for c in z) for z in raster)

    def chunk(typ, daten):
        return struct.pack(">I", len(daten)) + typ + daten + struct.pack(">I", zlib.crc32(typ + daten) & 0xFFFFFFFF)

    daten = (b"\x89PNG\r\n\x1a\n"
             + chunk(b"IHDR", struct.pack(">IIBBBBB", 16, 16, 8, 6, 0, 0, 0))
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
               {"pack": {"pack_format": 3, "description": "Waffenpack: Pistole, Bazooka, Schwert"}})

    tex = os.path.join(rp, "assets/minecraft/textures/items/waffenpack")
    mod = os.path.join(rp, "assets/minecraft/models/item")
    for name, raster in (("pistole", PISTOLE), ("bazooka", BAZOOKA), ("schwert", SCHWERT)):
        png(os.path.join(tex, name + ".png"), raster)
        json_datei(os.path.join(mod, "waffenpack", name + ".json"),
                   {"parent": "item/handheld", "textures": {"layer0": "items/waffenpack/" + name}})

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

    # ZIP: pack.mcmeta muss direkt im Hauptverzeichnis liegen
    zpfad = os.path.join(ROOT, "Waffenpack-Ressourcenpaket.zip")
    with zipfile.ZipFile(zpfad, "w", zipfile.ZIP_DEFLATED) as z:
        for ordner, _, dateien in sorted(os.walk(rp)):
            for d in sorted(dateien):
                voll = os.path.join(ordner, d)
                z.write(voll, os.path.relpath(voll, rp).replace(os.sep, "/"))


if __name__ == "__main__":
    ressourcenpaket()
    funktionen()
    einzelbefehle()
    cmd = installer()
    print("Fertig. Installer-Befehl: %d Zeichen" % len(cmd))
