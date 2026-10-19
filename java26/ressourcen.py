"""Ressourcenpaket fuer Minecraft Java 26.2 (Ressourcenpaket-Format 88).

Eigene Gegenstaende nutzen die Komponente item_model mit Modellen im Namensraum
"waffenpack". Vanilla-Gegenstaende (Bogen, Karottenrute, ...) bleiben dadurch
unveraendert. Nur fuer die Backrooms werden einige Bloecke neu gestaltet, die
man im Ueberlebensmodus nicht bekommt (Konstruktions-, Test-, Verbundbloecke,
verstaerkter Tiefenschiefer), dazu TNT (Sonder-TNT).
"""

import json
import os
import sys

HIER = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HIER))

import build      # noqa: E402  (Schwert-Raster, Rakete, Palette)
import grafik     # noqa: E402
import modelle    # noqa: E402
from grafik import Bild  # noqa: E402

FORMAT = 88
NS = "waffenpack"

# Monster-Modelle (ohne Warden: in 26.2 gibt es den echten Warden)
MONSTER = ["smiler", "hound", "hautdieb", "partygaenger", "faceling"]

# Granaten-Farben (Werf-TNT 1..10)
GRANATEN_FARBEN = [0xE53935, 0x8B0000, 0xFFC107, 0xFF6D00, 0x2979FF,
                   0x84FFFF, 0xAA00FF, 0x6D4C41, 0x161616, 0xF5F5F5]

# Neu gestaltete Bloecke (Blockmodell -> Textur)
BLOECKE = {
    "structure_block_save": "tapete",
    "structure_block_load": "deckenplatte",
    "structure_block_corner": "leuchtpanel",
    "structure_block_data": "teppich",
    "test_block_start": "hotel_tapete",
    "test_block_log": "hotel_teppich",
    "test_block_fail": "buerowand",
    "test_block_accept": "buero_teppich",
}


def j(obj):
    return json.dumps(obj, indent=1, ensure_ascii=False).encode("utf-8")


def raster_bild(raster):
    b = Bild(len(raster[0]), len(raster))
    for y, zeile in enumerate(raster):
        for x, c in enumerate(zeile):
            b.set(x, y, build.PALETTE[c])
    return b


def textur_pfade(modell):
    """Texturverweise des alten Formats (items/waffenpack/x) auf waffenpack:item/x umstellen."""
    t = modell.get("textures", {})
    for k, v in list(t.items()):
        if v.startswith("items/waffenpack/"):
            t[k] = "%s:item/%s" % (NS, v[len("items/waffenpack/"):])
    return modell


def getoent(bild, rgb):
    o = Bild(bild.w, bild.h)
    r, g, b = (rgb >> 16) & 255, (rgb >> 8) & 255, rgb & 255
    for y in range(bild.h):
        for x in range(bild.w):
            c = bild.get(x, y)
            if c[3]:
                o.set(x, y, (c[0] * r // 255, c[1] * g // 255, c[2] * b // 255, c[3]))
    return o


def drueber(unten, oben):
    o = Bild(unten.w, unten.h)
    o.kopie_von(unten, 0, 0, unten.w, unten.h, 0, 0)
    for y in range(oben.h):
        for x in range(oben.w):
            c = oben.get(x, y)
            if c[3]:
                o.set(x, y, c)
    return o


def kugel_modell():
    """Goldene Patrone, Spitze nach Norden (-z), Mitte bei 8/8/8."""
    def quader(von, bis, u):
        uv = [u, 0.5, u + 3, 3.5]
        return {"from": von, "to": bis,
                "faces": {s: {"uv": uv, "texture": "#t"} for s in ("north", "south", "east", "west", "up", "down")}}
    return {"textures": {"t": "%s:item/kugel" % NS, "particle": "%s:item/kugel" % NS},
            "elements": [quader([7, 7, 3], [9, 9, 5], 0.5), quader([6.5, 6.5, 5], [9.5, 9.5, 12], 4.5),
                         quader([6.3, 6.3, 12], [9.7, 9.7, 13], 8.5)],
            "display": {}}


def kugel_textur():
    b = Bild(16, 16)
    b.rechteck(0, 0, 4, 4, (236, 200, 90))
    b.rechteck(4, 0, 4, 4, (200, 150, 50))
    b.rechteck(8, 0, 4, 4, (170, 100, 50))
    return b


def monitor_modell():
    """Roehrenmonitor fuer das Buero (wird von einer Item-Anzeige gezeigt)."""
    def f(uv):
        return {"uv": uv, "texture": "#t"}
    seite = [0, 8, 8, 16]
    vorne = [0, 0, 8, 8]
    return {"textures": {"t": "%s:item/monitor" % NS, "particle": "%s:item/monitor" % NS},
            "elements": [
                {"from": [2, 0, 3], "to": [14, 11, 13],
                 "faces": {"north": f(vorne), "south": f(seite), "east": f(seite), "west": f(seite),
                           "up": f(seite), "down": f(seite)}},
                {"from": [5, 0, 13], "to": [11, 8, 15],
                 "faces": {s: f(seite) for s in ("north", "south", "east", "west", "up", "down")}},
            ],
            "display": {}}


def monitor_textur():
    b = Bild(16, 16)
    b.kopie_von(grafik.monitor(), 0, 0, 16, 16, 0, 0)
    gross = Bild(16, 16)
    # oben links: Bildschirm (8x8 aus der 16er-Textur verkleinert), unten links: Gehaeuse
    for y in range(8):
        for x in range(8):
            gross.set(x, y, b.get(x * 2, y * 2))
            gross.set(x, y + 8, (196, 188, 160))
    return gross


def schwert_modell():
    return {"parent": "minecraft:item/handheld", "textures": {"layer0": "%s:item/schwert" % NS}}


def item_def(modell):
    return {"model": {"type": "minecraft:model", "model": modell}}


def bogen_def(name):
    """Bogen mit eigenem Ruhe- und drei Spann-Modellen (wie der Vanilla-Bogen)."""
    m = lambda i: {"type": "minecraft:model", "model": "%s:item/%s_%d" % (NS, name, i)}
    return {"model": {
        "type": "minecraft:condition", "property": "minecraft:using_item",
        "on_false": m(0),
        "on_true": {"type": "minecraft:range_dispatch", "property": "minecraft:use_duration", "scale": 0.05,
                    "fallback": m(1), "entries": [{"threshold": 0.65, "model": m(2)},
                                                   {"threshold": 0.9, "model": m(3)}]}}}


def dateien():
    d = {}
    tex = "assets/%s/textures/item/" % NS
    mod = "assets/%s/models/item/" % NS
    items = "assets/%s/items/" % NS

    def gegenstand(name, modell, bild=None, mcmeta=None, textur=None):
        d[mod + name + ".json"] = j(modell)
        d[items + name + ".json"] = j(item_def("%s:item/%s" % (NS, name)))
        if bild is not None:
            d[tex + (textur or name) + ".png"] = bild.png_bytes()
        if mcmeta:
            d[tex + (textur or name) + ".png.mcmeta"] = j(mcmeta)

    d["pack.mcmeta"] = j({"pack": {"description": "Waffenpack + Backrooms (Minecraft 26.2)",
                                   "min_format": FORMAT, "max_format": FORMAT}})

    # 3D-Waffen aus modelle.py
    for name, datei, funktion in (("pistole", "pistole3d", modelle.pistole),
                                  ("bazooka", "bazooka3d", modelle.bazooka),
                                  ("taschenlampe", "taschenlampe", modelle.taschenlampe)):
        atlas, modell = funktion()
        gegenstand(name, textur_pfade(modell), atlas.bild, textur=datei)
    for name, funktion in (("minigun", modelle.minigun), ("orbital", modelle.orbital), ("meteor", modelle.meteor)):
        streifen, modell, meta = funktion()
        modell = textur_pfade(modell)
        if name == "meteor":
            modell["display"] = {"gui": modell["display"]["gui"]}
        gegenstand(name, modell, streifen, meta)

    # Schwert (2D)
    gegenstand("schwert", schwert_modell(), raster_bild(build.SCHWERT))

    # Rakete der Bazooka und Patrone der Pistole (fliegen als Item-Anzeige mit dem Pfeil)
    rakete = textur_pfade(build.raketen_modell())
    rakete["display"] = {"gui": {"rotation": [30, 45, 0], "translation": [0, 0, 0], "scale": [0.35] * 3}}
    gegenstand("rakete", rakete, raster_bild(build.RAKETE_TEXTUR))
    gegenstand("kugel", kugel_modell(), kugel_textur())
    gegenstand("monitor", monitor_modell(), monitor_textur())

    # Ultimativer Schatten-Bogen und Vernichtungs-Bogen: animiert, mit Spannstufen
    for stil in ("schatten", "vernichter"):
        for zustand in range(4):
            datei = "%s_%d" % (stil, zustand)
            d[tex + datei + ".png"] = grafik.bogen_animation(stil, zustand).png_bytes()
            d[tex + datei + ".png.mcmeta"] = j({"animation": {"frametime": 3}})
            d[mod + datei + ".json"] = j({"parent": "minecraft:item/bow",
                                          "textures": {"layer0": "%s:item/%s" % (NS, datei)}})
        d[items + stil + ".json"] = j(bogen_def(stil))

    # Werf-TNT: Dynamitbuendel in 10 Farben
    huelle, details = grafik.granate_huelle(), grafik.granate_details()
    for nr, farbe in enumerate(GRANATEN_FARBEN, 1):
        name = "granate_%d" % nr
        gegenstand(name, {"parent": "minecraft:item/generated", "textures": {"layer0": "%s:item/%s" % (NS, name)}},
                   drueber(getoent(huelle, farbe), details))

    # Monster (je zwei Bilder fuer die Laufanimation), getragen als Kopf-Gegenstand
    for name in MONSTER:
        atlas_f, modell_f = modelle.MONSTER[name]
        atlas = atlas_f()
        d[tex + name + ".png"] = atlas.bild.png_bytes()
        for bild in ("a", "b"):
            gegenstand("%s_%s" % (name, bild), textur_pfade(modell_f(atlas, bild)))

    # Backrooms-Bloecke
    btex = "assets/%s/textures/block/" % NS
    texturen = dict(grafik.BLOCK_TEXTUREN)
    quellen = {"tapete": grafik.tapete, "deckenplatte": grafik.deckenplatte, "teppich": grafik.teppich,
               "leuchtpanel": lambda: grafik.leuchtpanel(True), "hotel_tapete": grafik.hotel_tapete,
               "hotel_teppich": grafik.hotel_teppich, "buerowand": grafik.buerowand,
               "buero_teppich": grafik.buero_teppich, "kiste": grafik.kiste, "metallwand": grafik.metallwand}
    for name, f in quellen.items():
        d[btex + name + ".png"] = f().png_bytes()
    for block, textur in BLOECKE.items():
        d["assets/minecraft/models/block/%s.json" % block] = j(
            {"parent": "minecraft:block/cube_all", "textures": {"all": "%s:block/%s" % (NS, textur)}})
    kiste = "%s:block/kiste" % NS
    d["assets/minecraft/models/block/jigsaw.json"] = j(
        {"parent": "minecraft:block/cube_directional",
         "textures": {s: kiste for s in ("down", "east", "north", "particle", "south", "up", "west")}})
    metall = "%s:block/metallwand" % NS
    d["assets/minecraft/models/block/reinforced_deepslate.json"] = j(
        {"parent": "minecraft:block/cube_bottom_top",
         "textures": {"top": metall, "bottom": metall, "side": metall}})
    # Sonder-TNT
    for name, vanilla in (("tnt_side", "tnt_seite"), ("tnt_top", "tnt_oben"), ("tnt_bottom", "tnt_unten")):
        d["assets/minecraft/textures/block/%s.png" % name] = texturen[name]().png_bytes()
    return d
