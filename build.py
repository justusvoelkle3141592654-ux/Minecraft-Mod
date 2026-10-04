#!/usr/bin/env python3
"""Erzeugt das Ressourcenpaket und die Einzelbefehle des Waffenpacks (Minecraft 1.12 / Eaglercraft 1.12).

Aufruf: python3 build.py

Erzeugt:
  ressourcenpaket/                     Ressourcenpaket (Ordner)
  Waffenpack-Ressourcenpaket.zip       Ressourcenpaket (ZIP zum Importieren)
  befehle/einzelbefehle.txt            Einzelne Chat-Befehle (je max. 256 Zeichen)

Items und Waffen-Logik stehen in waffen.py, die Backrooms in backrooms.py.
Die fertige Welt (Waffenpack-Welt.zip) baut welt_bauen.py.
"""

import json
import os
import shutil
import struct
import zipfile
import zlib

import grafik
import modelle
import waffen
from waffen import BOGEN, RUTE, HACKE, SCHWERT_DAMAGE, nbt_string  # noqa: F401 (nbt_string fuer welt_bauen)

ROOT = os.path.dirname(os.path.abspath(__file__))


def schreibe(pfad, text):
    pfad = os.path.join(ROOT, pfad)
    os.makedirs(os.path.dirname(pfad), exist_ok=True)
    with open(pfad, "w", encoding="utf-8", newline="\n") as f:
        f.write(text)


def einzelbefehle():
    zeilen = waffen.einzelbefehle()
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


BOGEN_ANZEIGE = {
    "thirdperson_righthand": {"rotation": [-80, 260, -40], "translation": [-1, -2, 2.5], "scale": [0.9, 0.9, 0.9]},
    "thirdperson_lefthand": {"rotation": [-80, -280, 40], "translation": [-1, -2, 2.5], "scale": [0.9, 0.9, 0.9]},
    "firstperson_righthand": {"rotation": [0, -90, 25], "translation": [1.13, 3.2, 1.13], "scale": [0.68, 0.68, 0.68]},
    "firstperson_lefthand": {"rotation": [0, 90, -25], "translation": [1.13, 3.2, 1.13], "scale": [0.68, 0.68, 0.68]},
}
UNSICHTBAR = {"rotation": [0, 0, 0], "translation": [0, 0, 0], "scale": [0, 0, 0]}


def ressourcenpaket():
    rp = os.path.join(ROOT, "ressourcenpaket")
    if os.path.isdir(rp):
        shutil.rmtree(rp)
    json_datei(os.path.join(rp, "pack.mcmeta"),
               {"pack": {"pack_format": 3, "description": "Waffenpack + Backrooms"}})

    tex = os.path.join(rp, "assets/minecraft/textures/items/waffenpack")
    mod = os.path.join(rp, "assets/minecraft/models/item")
    W = waffen
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
    for name, funktion in (("minigun", modelle.minigun), ("orbital", modelle.orbital),
                           ("meteor", modelle.meteor)):
        streifen, modell, meta = funktion()
        streifen.speichern(os.path.join(tex, name + ".png"))
        json_datei(os.path.join(tex, name + ".png.mcmeta"), meta)
        json_datei(os.path.join(mod, "waffenpack", name + ".json"), modell)

    rute = [{"predicate": {"damaged": 0, "damage": unter(RUTE[n], W.KAROTTENRUTE_HALTBARKEIT)},
             "model": "item/waffenpack/" + n} for n in ("taschenlampe", "minigun", "orbital")]
    rute.append({"predicate": {"damaged": 1, "damage": 0}, "model": "item/carrot_on_a_stick"})
    json_datei(os.path.join(mod, "carrot_on_a_stick.json"), {
        "parent": "item/handheld_rod", "textures": {"layer0": "items/carrot_on_a_stick"}, "overrides": rute})

    # Monster (je zwei Animationsbilder), Rakete, Meteor
    hacke = [{"predicate": {"damaged": 0, "damage": unter(HACKE[n], W.DIAMANTHACKE_HALTBARKEIT)},
              "model": "item/waffenpack/" + n} for n in ("rakete", "meteor")]
    for name, (atlas_f, modell_f) in modelle.MONSTER.items():
        atlas = atlas_f()
        atlas.bild.speichern(os.path.join(tex, name + ".png"))
        for bild, dmg in zip(("a", "b"), modelle.MONSTER_DAMAGE[name]):
            json_datei(os.path.join(mod, "waffenpack", "%s_%s.json" % (name, bild)), modell_f(atlas, bild))
            hacke.append({"predicate": {"damaged": 0, "damage": unter(dmg, W.DIAMANTHACKE_HALTBARKEIT)},
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

    # Boegen: Schatten-Bogen und Vernichtungs-Bogen (je Ruhe + 3 Spannstufen, animiert)
    for stil in ("schatten", "vernichter"):
        for zustand in range(4):
            datei = "%s_%d" % (stil, zustand)
            grafik.bogen_animation(stil, zustand).speichern(os.path.join(tex, datei + ".png"))
            json_datei(os.path.join(tex, datei + ".png.mcmeta"), {"animation": {"frametime": 3}})
            json_datei(os.path.join(mod, "waffenpack", datei + ".json"),
                       {"parent": "item/generated", "textures": {"layer0": "items/waffenpack/" + datei},
                        "display": BOGEN_ANZEIGE})

    # Vanilla-Modell des Bogens (1.12.2) plus eigene Eintraege. Es gilt der letzte
    # passende Eintrag. "damaged": 0 trifft nur auf unzerbrechliche oder unbeschaedigte
    # Boegen zu; beschaedigte normale Boegen bleiben normal.
    def ziehen(modell_basis, extra):
        return [
            {"predicate": dict(extra, pulling=1), "model": modell_basis % 0},
            {"predicate": dict(extra, pulling=1, pull=0.65), "model": modell_basis % 1},
            {"predicate": dict(extra, pulling=1, pull=0.9), "model": modell_basis % 2},
        ]
    overrides = ziehen("item/bow_pulling_%d", {})
    for name in ("pistole", "bazooka"):
        overrides.append({"predicate": {"damaged": 0, "damage": unter(BOGEN[name], W.BOGEN_HALTBARKEIT)},
                          "model": "item/waffenpack/" + name})
    for stil in ("schatten", "vernichter"):
        bed = {"damaged": 0, "damage": unter(BOGEN[stil], W.BOGEN_HALTBARKEIT)}
        overrides.append({"predicate": dict(bed), "model": "item/waffenpack/%s_0" % stil})
        for o in ziehen("item/waffenpack/" + stil + "_%d", bed):
            o["model"] = o["model"][:-1] + str(int(o["model"][-1]) + 1)
            overrides.append(o)
    overrides.append({"predicate": {"damaged": 1, "damage": 0}, "model": "item/bow"})
    overrides += ziehen("item/bow_pulling_%d", {"damaged": 1})
    json_datei(os.path.join(mod, "bow.json"), {
        "parent": "item/generated", "textures": {"layer0": "items/bow_standby"},
        "display": BOGEN_ANZEIGE, "overrides": overrides})

    json_datei(os.path.join(mod, "diamond_sword.json"), {
        "parent": "item/handheld",
        "textures": {"layer0": "items/diamond_sword"},
        "overrides": [
            {"predicate": {"damaged": 0, "damage": unter(SCHWERT_DAMAGE, W.DIAMANTSCHWERT_HALTBARKEIT)},
             "model": "item/waffenpack/schwert"},
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

    # Werf-TNT: Wurftraenke sehen wie Dynamitbuendel aus (Farbe = Trankfarbe)
    grafik.granate_huelle().speichern(os.path.join(tex, "granate_huelle.png"))
    grafik.granate_details().speichern(os.path.join(tex, "granate_details.png"))
    json_datei(os.path.join(mod, "bottle_splash.json"), {
        "parent": "item/generated",
        "textures": {"layer0": "items/waffenpack/granate_huelle", "layer1": "items/waffenpack/granate_details"}})
    # Munition der Minigun liegt in der zweiten Hand: dort unsichtbar
    json_datei(os.path.join(mod, "snowball.json"), {
        "parent": "item/generated", "textures": {"layer0": "items/snowball"},
        "display": {"thirdperson_lefthand": UNSICHTBAR, "firstperson_lefthand": UNSICHTBAR,
                    "ground": {"rotation": [0, 0, 0], "translation": [0, 2, 0], "scale": [0.22, 0.22, 0.22]}}})
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
