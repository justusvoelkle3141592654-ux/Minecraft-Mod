"""Waffen und Werf-TNT als Datenpaket fuer Minecraft Java 26.2 (Namensraum "wp").

Technik:
- Pistole, Bazooka, Schatten-Bogen, Vernichtungs-Bogen sind Boegen. Ihre Pfeile
  werden ueber "execute on origin" dem Schuetzen zugeordnet.
- Minigun, Orbital-Kanone und Taschenlampe sind Karottenruten; ein Rechtsklick
  erhoeht den Zaehler minecraft.used:minecraft.carrot_on_a_stick.
- Minigun und Orbital-Kanone treffen per Strahl (Raycast) direkt.
- Werf-TNT sind Schneebaelle mit eigenem Aussehen; fliegend sieht man das TNT.
- Jedes Geschoss traegt einen "Sensor" (Item-Anzeige als Passagier). Verschwindet
  das Geschoss beim Einschlag, bleibt der Sensor an der Einschlagstelle zurueck.
- Explosionen in den Backrooms zerstoeren keine Bloecke (nur Schaden und Effekte).
"""

import json

NS = "waffenpack"
DIM = "br:backrooms"

PFEIL_SCHADEN = 2048
SCHATTEN_SCHADEN = 60
MINIGUN_SCHADEN = 10
MINIGUN_REICHWEITE = 120          # Schritte zu 0,5 Bloecken
ORBITAL_REICHWEITE = 200          # Schritte zu 1 Block
VERNICHTUNG_RADIUS = 1000
WELTLOESCHER_HALB = 48
WELT_UNTEN = -60                  # Weltloescher bis zu dieser Hoehe
STUFE = 255                       # hoechste Verzauberungsstufe in 26.2

GRANATEN = [
    (1, "Wurf-TNT", "red", "Explodiert beim Aufprall"),
    (2, "Mega-TNT", "dark_red", "Riesige Explosion"),
    (3, "Cluster-TNT", "yellow", "Zerfällt in 8 Bomben"),
    (4, "Feuer-TNT", "gold", "Explosion und Feuerregen"),
    (5, "Blitz-TNT", "blue", "Ruft fünf Blitze"),
    (6, "Frost-TNT", "aqua", "Friert Gegner und Boden ein"),
    (7, "Schwerkraft-TNT", "light_purple", "Lässt Gegner schweben"),
    (8, "Meteor-TNT", "dark_gray", "Ruft einen Meteoriten"),
    (9, "Vernichtungs-TNT", "dark_red", "Löscht alles im Umkreis von 1000 Blöcken aus"),
    (10, "Weltlöscher-TNT", "white", "Löscht die Welt im Umkreis von 48 Blöcken"),
]

FEINDE = ["zombie", "husk", "drowned", "skeleton", "stray", "bogged", "parched", "creeper", "spider", "cave_spider",
          "enderman", "witch", "slime", "magma_cube", "blaze", "ghast", "wither_skeleton", "zombie_villager",
          "zombified_piglin", "piglin", "piglin_brute", "hoglin", "zoglin", "vindicator", "evoker", "pillager",
          "illusioner", "ravager", "vex", "phantom", "guardian", "elder_guardian", "shulker", "silverfish",
          "endermite", "warden", "wither", "ender_dragon", "breeze", "creaking", "giant", "zombie_horse",
          "skeleton_horse", "zombie_nautilus"]

KEIN_ZIEL = ["player", "marker", "item_display", "block_display", "text_display", "interaction", "item",
             "experience_orb", "arrow", "spectral_arrow", "trident", "snowball", "egg", "ender_pearl",
             "splash_potion", "lingering_potion", "experience_bottle", "tnt", "falling_block", "area_effect_cloud",
             "lightning_bolt", "painting", "item_frame", "glow_item_frame", "evoker_fangs", "fireball",
             "small_fireball", "wind_charge", "breeze_wind_charge", "firework_rocket", "leash_knot", "llama_spit",
             "shulker_bullet", "dragon_fireball", "wither_skull", "eye_of_ender", "fishing_bobber",
             "ominous_item_spawner", "end_crystal"]

ZIEL = "type=!#wp:kein_ziel,tag=!wp_sys"


def t(text, farbe="white", **kw):
    d = {"text": text, "color": farbe, "italic": False}
    d.update(kw)
    return d


def snbt_text(obj):
    """Textkomponente als SNBT (Schluessel ohne Anfuehrungszeichen)."""
    if isinstance(obj, dict):
        return "{" + ",".join("%s:%s" % (k, snbt_text(v)) for k, v in obj.items()) + "}"
    if isinstance(obj, list):
        return "[" + ",".join(snbt_text(v) for v in obj) + "]"
    if isinstance(obj, bool):
        return "true" if obj else "false"
    if isinstance(obj, str):
        return json.dumps(obj, ensure_ascii=False)
    return str(obj)


def jt(obj):
    return json.dumps(obj, ensure_ascii=False, separators=(",", ":"))


def name_lore(name, farbe, zeilen=()):
    s = "custom_name=%s" % snbt_text(t(name, farbe))
    if zeilen:
        s += ",lore=[%s]" % ",".join(snbt_text(t(z, "gray")) for z in zeilen)
    return s


VERSTECKT = 'tooltip_display={hidden_components:["minecraft:enchantments","minecraft:unbreakable"]}'


def waffe(item, modell, wp, name, farbe, zeilen=(), extra=""):
    teile = ['item_model="%s:%s"' % (NS, modell), name_lore(name, farbe, zeilen), "unbreakable={}",
             "custom_data={wp:%d}" % wp, VERSTECKT, "enchantment_glint_override=false", "max_stack_size=1"]
    if item == "bow":
        teile.append('enchantments={"minecraft:infinity":1}')
    if extra:
        teile.append(extra)
    return "%s[%s]" % (item, ",".join(teile))


ITEMS = {
    "pistole": waffe("bow", "pistole", 1, "Pistole", "gray", ["Wie einen Bogen spannen und loslassen"]),
    "bazooka": waffe("bow", "bazooka", 2, "Bazooka", "dark_green", ["Feuert eine Rakete"]),
    "minigun": waffe("stick", "minigun", 3, "Minigun", "gold", ["Rechte Maustaste gedrückt halten"],
                     'consumable={consume_seconds:100000,animation:"none",sound:"minecraft:intentionally_empty",'
                     'has_consume_particles:false}'),
    "orbital": waffe("carrot_on_a_stick", "orbital", 4, "Orbital-TNT-Kanone", "aqua",
                     ["Ziel anvisieren, Rechtsklick:", "TNT-Regen aus dem All"],
                     'use_cooldown={seconds:5,cooldown_group:"waffenpack:orbital"}'),
    "schatten": waffe("bow", "schatten", 5, "Ultimativer Schatten-Bogen", "dark_purple",
                      ["Zielsuchende Schattenpfeile"]),
    "vernichter": waffe("bow", "vernichter", 6, "Vernichtungs-Bogen", "dark_red",
                        ["Löscht beim Einschlag alles im", "Umkreis von 1000 Blöcken aus"]),
    "lampe": waffe("carrot_on_a_stick", "taschenlampe", 9, "Taschenlampe", "yellow", ["Leuchtet, solange du sie hältst"]),
    "schwert": ('diamond_sword[item_model="%s:schwert",%s,unbreakable={},%s,attribute_modifiers=[{type:"minecraft:attack_damage",'
                'amount:2047,id:"%s:schwert",operation:"add_value",slot:"mainhand"}]]'
                % (NS, name_lore("Schwert", "red"), VERSTECKT, NS)),
}


def granate(nr, anzahl):
    _, name, farbe, text = GRANATEN[nr - 1]
    return ('snowball[item_model="%s:granate_%d",max_stack_size=64,%s,custom_data={wt:%d}] %d'
            % (NS, nr, name_lore(name, farbe, [text, "Rechtsklick: werfen"]), nr, anzahl))


RUESTUNG = [
    ("armor.head", 'diamond_helmet[enchantments={"minecraft:protection":%d}]' % STUFE),
    ("armor.chest", 'diamond_chestplate[enchantments={"minecraft:protection":%d}]' % STUFE),
    ("armor.legs", 'diamond_leggings[enchantments={"minecraft:protection":%d}]' % STUFE),
    ("armor.feet", 'diamond_boots[enchantments={"minecraft:protection":%d,"minecraft:feather_falling":%d}]'
     % (STUFE, STUFE)),
]


# ---------------------------------------------------------------------------

class Paket:
    def __init__(self):
        self.f = {}          # Funktionsname (ns:pfad) -> Zeilen
        self.d = {}          # weitere Dateien (Pfad -> bytes)

    def fn(self, name, *zeilen):
        self.f.setdefault(name, []).extend(z for z in zeilen if z)
        return name

    def datei(self, pfad, obj):
        self.d[pfad] = json.dumps(obj, indent=1, ensure_ascii=False).encode("utf-8")


def boom(p, staerke):
    """Explosion: in den Backrooms ohne Blockschaden."""
    name = "wp:boom/%d" % staerke
    if name in p.f:
        return "function " + name
    r = max(3, staerke + 2)
    p.fn(name,
         "execute if dimension %s run function wp:boom/sicher_%d" % (DIM, staerke),
         "execute unless dimension %s run summon tnt ~ ~ ~ {fuse:0,explosion_power:%d.0f,Tags:[\"wp_tx\"]}" % (DIM, staerke))
    p.fn("wp:boom/sicher_%d" % staerke,
         "execute as @e[distance=..%d,%s] run damage @s %d minecraft:explosion" % (r, ZIEL + ",type=!player", staerke * 6),
         "particle minecraft:explosion_emitter ~ ~ ~ %.1f %.1f %.1f 0 %d force" % (staerke / 4, staerke / 4, staerke / 4,
                                                                                   max(1, staerke // 3)),
         "particle minecraft:explosion ~ ~ ~ %d 1 %d 0 %d force" % (staerke // 2, staerke // 2, staerke * 3),
         "playsound minecraft:entity.generic.explode block @a ~ ~ ~ %d 0.8" % max(2, staerke // 2))
    return "function " + name


def items(p):
    geben = ["give @s %s" % ITEMS[n] for n in ("pistole", "bazooka", "minigun", "orbital", "schatten", "vernichter",
                                                "schwert", "lampe")]
    geben += ["give @s %s" % granate(n, 64) for n in range(1, 11)]
    geben += [
        "give @s tnt[%s] 64" % name_lore("Sonder-TNT", "red", ["Jede Explosion löst vier weitere aus"]),
        "give @s flint_and_steel[unbreakable={}]",
        "give @s arrow 1",
        "give @s enchanted_golden_apple 64",
        "give @s ender_pearl 16",
        'give @s diamond_sword[enchantments={"minecraft:sharpness":20}]',
        'give @s diamond_pickaxe[enchantments={"minecraft:efficiency":%d}]' % STUFE,
    ]
    geben += ["item replace entity @s %s with %s" % r for r in RUESTUNG]
    p.fn("wp:items/alle", *geben)
    p.fn("wp:items/erstausstattung",
         "function wp:items/alle",
         "tag @s add wp_hat",
         "tellraw @s %s" % jt([t("Willkommen! ", "gold", bold=True), t("Alle Waffen liegen im Inventar. ", "white"),
                              t("Backrooms: ", "white"),
                              {"text": "[KLICK HIER]", "color": "yellow", "bold": True,
                               "click_event": {"action": "run_command", "command": "/trigger start"},
                               "hover_event": {"action": "show_text", "value": "Backrooms betreten"}},
                              t(" oder tippe ", "white"), t("/trigger start", "yellow")]))
    for n in range(1, 11):
        p.fn("wp:items/granate_%d" % n, "give @s[gamemode=!creative] %s" % granate(n, 1))


def halten(p):
    z = ["tag @a remove wp_h%d" % n for n in (1, 2, 3, 4, 5, 6, 9)]
    for n in (1, 2, 3, 4, 5, 6, 9):
        z.append("execute as @a if items entity @s weapon.mainhand *[custom_data~{wp:%d}] run tag @s add wp_h%d" % (n, n))
    p.fn("wp:halten", *z)


def pfeile(p):
    arten = {1: "p", 2: "b", 5: "s", 6: "v"}
    z = []
    for wp, a in arten.items():
        z.append("execute as @e[type=arrow,tag=!wp_alt] at @s on origin if items entity @s weapon.mainhand "
                 "*[custom_data~{wp:%d}] as @e[type=arrow,tag=!wp_alt,limit=1,sort=nearest] run function wp:pfeil/neu_%s"
                 % (wp, a))
    z.append("execute as @e[type=arrow,tag=!wp_alt] at @s on origin if items entity @s weapon.mainhand "
             "*[custom_data~{wp:3}] run kill @e[type=arrow,tag=!wp_alt,limit=1,sort=nearest]")
    z.append("tag @e[type=arrow,tag=!wp_alt] add wp_alt")
    p.fn("wp:pfeil/neu", *z)

    def sensor(art, modell=None, scale=1.0):
        item = ('item:{id:"minecraft:stick",count:1,components:{"minecraft:item_model":"%s:%s"}},' % (NS, modell)
                if modell else "")
        trans = ("transformation:{left_rotation:[0f,0f,0f,1f],right_rotation:[0f,0f,0f,1f],translation:[0f,0f,0f],"
                 "scale:[%.2ff,%.2ff,%.2ff]}," % (scale, scale, scale)) if modell else ""
        return [
            "summon item_display ~ ~ ~ {%s%steleport_duration:1,Tags:[\"wp_sys\",\"wp_sensor\",\"wp_dreh\",\"wp_neu\",\"wp_s%s\"]}"
            % (item, trans, art),
            "ride @e[type=item_display,tag=wp_neu,limit=1,sort=nearest] mount @s",
            "tag @e[type=item_display,tag=wp_neu] remove wp_neu",
        ]
    p.fn("wp:pfeil/neu_p",
         "tag @s add wp_proj", "tag @s add wp_pp",
         "data merge entity @s {damage:%d.0d,pickup:0b}" % PFEIL_SCHADEN,
         *sensor("p", "kugel", 0.7),
         "playsound minecraft:entity.generic.explode player @a ~ ~ ~ 0.6 2",
         "playsound minecraft:block.anvil.land player @a ~ ~ ~ 0.25 2",
         "execute on origin at @s anchored eyes positioned ^-0.4 ^-0.25 ^2.2 run particle minecraft:flame ~ ~ ~ 0.03 0.03 0.03 0.02 4",
         "execute on origin at @s anchored eyes positioned ^-0.4 ^-0.25 ^2.4 run particle minecraft:smoke ~ ~ ~ 0.03 0.03 0.03 0.01 3")
    p.fn("wp:pfeil/neu_b",
         "tag @s add wp_proj", "tag @s add wp_pb",
         "data merge entity @s {damage:%d.0d,pickup:0b}" % PFEIL_SCHADEN,
         *sensor("b", "rakete", 1.0),
         "playsound minecraft:entity.firework_rocket.launch player @a ~ ~ ~ 2 0.5",
         "playsound minecraft:entity.blaze.shoot player @a ~ ~ ~ 1 0.6",
         "execute on origin at @s anchored eyes positioned ^ ^ ^-1.5 run particle minecraft:large_smoke ~ ~ ~ 0.2 0.2 0.2 0.02 8")
    p.fn("wp:pfeil/neu_s",
         "tag @s add wp_proj", "tag @s add wp_ps",
         "data merge entity @s {damage:%d.0d,pickup:0b}" % SCHATTEN_SCHADEN,
         *sensor("s"),
         "playsound minecraft:entity.wither.shoot player @a ~ ~ ~ 0.6 1.6",
         "execute on origin at @s anchored eyes positioned ^ ^ ^2.5 run particle minecraft:reverse_portal ~ ~ ~ 0.2 0.2 0.2 0.05 20")
    p.fn("wp:pfeil/neu_v",
         "tag @s add wp_proj", "tag @s add wp_pv",
         "data merge entity @s {pickup:0b}",
         *sensor("v"),
         "playsound minecraft:entity.ender_dragon.shoot player @a ~ ~ ~ 1 0.6")


def wurf(p):
    p.fn("wp:wurf/neu",
         "execute as @e[type=snowball,tag=!wp_alt] if data entity @s Item.components.\"minecraft:custom_data\".wt "
         "at @s run function wp:wurf/start",
         "tag @e[type=snowball,tag=!wp_alt] add wp_alt")
    z = ["tag @s add wp_proj",
         "execute store result score @s wp_art run data get entity @s Item.components.\"minecraft:custom_data\".wt",
         "summon item_display ~ ~ ~ {teleport_duration:1,Tags:[\"wp_sys\",\"wp_sensor\",\"wp_neu\",\"wp_sw\"]}",
         "scoreboard players operation @e[type=item_display,tag=wp_neu,limit=1,sort=nearest] wp_art = @s wp_art",
         "ride @e[type=item_display,tag=wp_neu,limit=1,sort=nearest] mount @s",
         "tag @e[type=item_display,tag=wp_neu] remove wp_neu",
         "playsound minecraft:entity.snowball.throw player @a ~ ~ ~ 1 0.6"]
    for n in range(1, 11):
        z.append("execute if score @s wp_art matches %d on origin run function wp:items/granate_%d" % (n, n))
    p.fn("wp:wurf/start", *z)


def fahrzeug(p):
    p.datei("data/wp/predicate/hat_fahrzeug.json",
            {"condition": "minecraft:entity_properties", "entity": "this", "predicate": {"vehicle": {}}})
    p.fn("wp:fahrzeug",
         "scoreboard players add @e[tag=wp_proj] wp_alter 1",
         # Item-Anzeigen drehen sich mit dem Pfeil (Pfeil-Drehung ist gespiegelt)
         "execute as @e[type=item_display,tag=wp_dreh] store result entity @s Rotation[0] float -0.01 on vehicle "
         "run data get entity @s Rotation[0] 100",
         "execute as @e[type=item_display,tag=wp_dreh] store result entity @s Rotation[1] float -0.01 on vehicle "
         "run data get entity @s Rotation[1] 100",
         # Pfeile im Boden: Einschlag
         "execute as @e[type=arrow,tag=wp_proj] if data entity @s {inGround:1b} at @s run function wp:einschlag/pfeil",
         # Sensoren ohne Geschoss: Einschlag an dieser Stelle
         "execute as @e[type=item_display,tag=wp_sensor] at @s unless predicate wp:hat_fahrzeug "
         "run function wp:einschlag/sensor",
         # Spuren
         "execute as @e[type=arrow,tag=wp_pp] at @s run particle minecraft:crit ~ ~ ~ 0 0 0 0 1 force",
         "execute as @e[type=arrow,tag=wp_pb,scores={wp_alter=3..}] at @s run particle minecraft:flame ~ ~ ~ 0.1 0.1 0.1 0.01 4 force",
         "execute as @e[type=arrow,tag=wp_pb,scores={wp_alter=3..}] at @s run particle minecraft:smoke ~ ~ ~ 0.15 0.15 0.15 0.01 3 force",
         "execute as @e[type=arrow,tag=wp_ps,scores={wp_alter=2..}] at @s run particle minecraft:dragon_breath ~ ~ ~ 0.05 0.05 0.05 0.01 3 force",
         "execute as @e[type=arrow,tag=wp_ps,scores={wp_alter=2..}] at @s run particle minecraft:portal ~ ~ ~ 0.2 0.2 0.2 0.6 4 force",
         "execute as @e[type=arrow,tag=wp_pv,scores={wp_alter=2..}] at @s run particle minecraft:end_rod ~ ~ ~ 0.05 0.05 0.05 0.01 2 force",
         "execute as @e[type=arrow,tag=wp_pv,scores={wp_alter=2..}] at @s run particle minecraft:dust{color:[1.0,0.1,0.1],scale:1.5} ~ ~ ~ 0.1 0.1 0.1 0 3 force",
         "execute as @e[type=snowball,tag=wp_proj,scores={wp_alter=2..}] at @s run particle minecraft:flame ~ ~ ~ 0 0 0 0 1 force",
         "execute as @e[type=snowball,tag=wp_proj,scores={wp_alter=2..}] at @s run particle minecraft:smoke ~ ~ ~ 0 0 0 0 1 force",
         # Zu alte Geschosse entfernen (10 Sekunden)
         "execute as @e[tag=wp_proj,scores={wp_alter=200..}] run function wp:einschlag/weg")
    p.fn("wp:einschlag/weg", "execute on passengers run kill @s", "kill @s")
    p.fn("wp:einschlag/pfeil",
         "execute if entity @s[tag=wp_pb] run function wp:wirkung/rakete",
         "execute if entity @s[tag=wp_ps] run function wp:wirkung/schatten",
         "execute if entity @s[tag=wp_pv] run function wp:wirkung/vernichtung",
         "execute if entity @s[tag=wp_pp] run particle minecraft:smoke ~ ~ ~ 0.1 0.1 0.1 0.02 8 force",
         "execute on passengers run kill @s",
         "kill @s")
    z = ["execute if entity @s[tag=wp_sb] run function wp:wirkung/rakete",
         "execute if entity @s[tag=wp_ss] run function wp:wirkung/schatten",
         "execute if entity @s[tag=wp_sv] run function wp:wirkung/vernichtung"]
    for n in range(1, 11):
        z.append("execute if entity @s[tag=wp_sw,scores={wp_art=%d}] run function wp:wirkung/w%d" % (n, n))
    z.append("kill @s")
    p.fn("wp:einschlag/sensor", *z)


def strahlen(p):
    # Minigun
    p.fn("wp:rute",
         "execute if entity @s[tag=wp_h4] anchored eyes positioned ^ ^ ^ run function wp:orbital/schuss")
    # Dauerfeuer: solange die Minigun "benutzt" wird (Taste gehalten), jeden 2. Tick ein Schuss
    p.datei("data/wp/advancement/minigun.json", {
        "criteria": {"feuer": {"trigger": "minecraft:using_item", "conditions": {"item": {
            "items": "minecraft:stick", "predicates": {"minecraft:custom_data": {"wp": 3}}}}}},
        "rewards": {"function": "wp:mg/halten"}})
    p.fn("wp:mg/halten",
         "advancement revoke @s only wp:minigun",
         "scoreboard players add @s wp_mg 1",
         "execute if score @s wp_mg matches 2.. at @s anchored eyes positioned ^ ^ ^ run function wp:mg/schuss",
         "execute if score @s wp_mg matches 2.. run scoreboard players set @s wp_mg 0")
    p.fn("wp:mg/schuss",
         "playsound minecraft:entity.firework_rocket.blast player @a ~ ~ ~ 0.9 1.9",
         "playsound minecraft:entity.generic.explode player @a ~ ~ ~ 0.15 2",
         "particle minecraft:flame ^-0.45 ^-0.3 ^1.6 0.02 0.02 0.02 0.01 2",
         "particle minecraft:smoke ^-0.45 ^-0.3 ^1.8 0.03 0.03 0.03 0.01 2",
         "scoreboard players set #schritt wp_t 0",
         "function wp:mg/strahl")
    p.fn("wp:mg/strahl",
         "scoreboard players add #schritt wp_t 1",
         "execute if score #schritt wp_t matches 5.. run particle minecraft:dust{color:[1.0,0.85,0.35],scale:0.6} ~ ~ ~ 0 0 0 0 1 force",
         "execute positioned ~-0.5 ~-0.5 ~-0.5 if entity @e[dx=0,dy=0,dz=0,%s] positioned ~0.5 ~0.5 ~0.5 "
         "run return run function wp:mg/treffer" % ZIEL,
         "execute unless block ~ ~ ~ #wp:durchlaessig run return run function wp:mg/block",
         "execute if score #schritt wp_t matches ..%d positioned ^ ^ ^0.5 run function wp:mg/strahl" % MINIGUN_REICHWEITE)
    p.fn("wp:mg/treffer",
         "execute positioned ~-0.5 ~-0.5 ~-0.5 run damage @e[dx=0,dy=0,dz=0,%s,limit=1] %d minecraft:arrow by @s"
         % (ZIEL, MINIGUN_SCHADEN),
         "particle minecraft:crit ~ ~ ~ 0.2 0.2 0.2 0.3 8 force",
         "particle minecraft:damage_indicator ~ ~ ~ 0.1 0.1 0.1 0.1 2 force",
         "playsound minecraft:entity.arrow.hit_player player @a ~ ~ ~ 0.4 1.6")
    p.fn("wp:mg/block",
         "particle minecraft:smoke ^ ^ ^-0.3 0.05 0.05 0.05 0.02 4 force",
         "particle minecraft:crit ^ ^ ^-0.3 0.05 0.05 0.05 0.2 4 force",
         "playsound minecraft:block.stone.hit block @a ~ ~ ~ 0.4 1.5")
    # Orbital-Kanone: Zielpunkt suchen
    p.fn("wp:orbital/schuss",
         "playsound minecraft:block.beacon.activate player @a ~ ~ ~ 1 1.8",
         "playsound minecraft:entity.firework_rocket.launch player @a ~ ~ ~ 1 1.6",
         "scoreboard players set #schritt wp_t 0",
         "function wp:orbital/strahl")
    p.fn("wp:orbital/strahl",
         "scoreboard players add #schritt wp_t 1",
         "execute if score #schritt wp_t matches 3.. run particle minecraft:end_rod ~ ~ ~ 0 0 0 0 1 force",
         "execute positioned ~-0.5 ~-0.5 ~-0.5 if entity @e[dx=0,dy=0,dz=0,%s] positioned ~0.5 ~0.5 ~0.5 "
         "run return run function wp:orbital/ziel" % ZIEL,
         "execute unless block ~ ~ ~ #wp:durchlaessig positioned ^ ^ ^-1 run return run function wp:orbital/ziel",
         "execute if score #schritt wp_t matches ..%d positioned ^ ^ ^1 run function wp:orbital/strahl" % ORBITAL_REICHWEITE)
    p.fn("wp:orbital/ziel",
         "execute align xyz positioned ~0.5 ~ ~0.5 run summon marker ~ ~ ~ {Tags:[\"wp_sys\",\"wp_fx\",\"wp_orb\"]}",
         "title @s actionbar %s" % jt(t("ORBITALSCHLAG IN 2 SEKUNDEN", "red", bold=True)))


def wirkungen(p):
    w = "wp:wirkung/"
    p.fn(w + "rakete", boom(p, 4), "particle minecraft:flame ~ ~ ~ 1 1 1 0.1 40 force")
    p.fn(w + "schatten",
         "execute as @e[distance=..4,%s,type=!player,limit=4,sort=nearest] at @s run summon evoker_fangs ~ ~ ~" % ZIEL,
         "effect give @e[distance=..4,%s,type=!player] wither 6 2" % ZIEL,
         "effect give @e[distance=..4,%s,type=!player] blindness 4 0" % ZIEL,
         "effect give @e[distance=..4,%s,type=!player] slowness 4 2" % ZIEL,
         "particle minecraft:dragon_breath ~ ~ ~ 1.2 0.8 1.2 0.02 70 force",
         "particle minecraft:reverse_portal ~ ~ ~ 1 1 1 0.2 60 force",
         "playsound minecraft:entity.evoker_fangs.attack player @a ~ ~ ~ 1 0.7",
         "playsound minecraft:entity.wither.hurt player @a ~ ~ ~ 0.6 1.5")
    p.fn(w + "vernichtung", "summon marker ~ ~ ~ {Tags:[\"wp_sys\",\"wp_fx\",\"wp_vn\"]}")
    p.fn(w + "w1", boom(p, 4))
    p.fn(w + "w2", boom(p, 10), "particle minecraft:explosion_emitter ~ ~ ~ 4 2 4 0 10 force",
         "playsound minecraft:entity.generic.explode block @a ~ ~ ~ 8 0.5")
    z = [boom(p, 3)]
    for dx, dz in ((1, 0), (-1, 0), (0, 1), (0, -1), (0.7, 0.7), (-0.7, 0.7), (0.7, -0.7), (-0.7, -0.7)):
        z.append("execute unless dimension %s run summon tnt ~ ~0.5 ~ {fuse:30,explosion_power:3.0f,Motion:[%.2fd,0.55d,%.2fd],Tags:[\"wp_tx\"]}"
                 % (DIM, dx * 0.45, dz * 0.45))
        z.append("execute if dimension %s positioned ~%.1f ~ ~%.1f run function wp:boom/sicher_3" % (DIM, dx * 4, dz * 4))
    p.fn(w + "w3", *z)
    z = [boom(p, 3), "particle minecraft:lava ~ ~ ~ 2 1 2 0 40 force", "particle minecraft:flame ~ ~1 ~ 2 1 2 0.05 80 force",
         "execute as @e[distance=..6,%s,type=!player] run data merge entity @s {Fire:200s}" % ZIEL]
    for dx, dz in ((3, 0), (-3, 0), (0, 3), (0, -3), (2, 2), (-2, 2), (2, -2), (-2, -2)):
        z.append("execute unless dimension %s run summon small_fireball ~%d ~4 ~%d {Motion:[0.0d,-1.0d,0.0d],acceleration_power:0.1d}"
                 % (DIM, dx, dz))
    p.fn(w + "w4", *z)
    z = [boom(p, 2)]
    for dx, dz in ((0, 0), (4, 0), (-4, 0), (0, 4), (0, -4)):
        z.append("summon lightning_bolt ~%d ~ ~%d" % (dx, dz))
    p.fn(w + "w5", *z)
    z = ["effect give @e[distance=..8,%s,type=!player] slowness 10 6 true" % ZIEL,
         "effect give @e[distance=..8,%s,type=!player] weakness 10 2 true" % ZIEL,
         "execute as @e[distance=..8,%s,type=!player] run data merge entity @s {TicksFrozen:300}" % ZIEL,
         "particle minecraft:snowflake ~ ~1 ~ 4 2 4 0.05 300 force",
         "particle minecraft:block{block_state:\"minecraft:ice\"} ~ ~1 ~ 3 1 3 0.1 150 force",
         "playsound minecraft:block.glass.break block @a ~ ~ ~ 2 0.6",
         "playsound minecraft:entity.player.hurt_freeze block @a ~ ~ ~ 2 0.8"]
    draussen = "execute unless dimension %s run " % DIM
    z += [draussen + "fill ~-6 ~-3 ~-6 ~6 ~2 ~6 ice replace water",
          draussen + "fill ~-6 ~-3 ~-6 ~6 ~2 ~6 obsidian replace lava",
          draussen + "fill ~-5 ~-2 ~-5 ~5 ~ ~5 packed_ice replace #minecraft:dirt",
          draussen + "fill ~-5 ~-2 ~-5 ~5 ~ ~5 packed_ice replace #minecraft:base_stone_overworld",
          draussen + "fill ~-5 ~-2 ~-5 ~5 ~ ~5 packed_ice replace #minecraft:sand",
          draussen + "fill ~-5 ~-1 ~-5 ~5 ~2 ~5 snow replace #minecraft:replaceable"]
    p.fn(w + "w6", *z)
    p.fn(w + "w7",
         "effect give @e[distance=..10,%s,type=!player] levitation 3 6 true" % ZIEL,
         "particle minecraft:portal ~ ~1 ~ 3 2 3 1 200 force",
         "particle minecraft:witch ~ ~1 ~ 3 2 3 0.1 60 force",
         "playsound minecraft:entity.shulker.shoot block @a ~ ~ ~ 2 0.5",
         "playsound minecraft:entity.illusioner.cast_spell block @a ~ ~ ~ 2 0.7")
    p.fn(w + "w8", "summon marker ~ ~ ~ {Tags:[\"wp_sys\",\"wp_fx\",\"wp_met\"]}")
    p.fn(w + "w9", "function " + w + "vernichtung")
    p.fn(w + "w10",
         "execute unless dimension %s run summon marker ~ ~ ~ {Tags:[\"wp_sys\",\"wp_fx\",\"wp_wl\"]}" % DIM,
         "execute if dimension %s run tellraw @a[distance=..30] %s"
         % (DIM, jt(t("Der Weltlöscher wirkt in den Backrooms nicht.", "gray", italic=True))))


def fx(p):
    """Laengere Wirkungen, gesteuert ueber das Alter der Markierung (wp_t)."""
    def bei(tag, t0, t1=None):
        t1 = t0 if t1 is None else t1
        return "execute as @e[type=marker,tag=%s,scores={wp_t=%d..%d}] at @s run " % (tag, t0, t1)
    z = ["scoreboard players add @e[type=marker,tag=wp_fx] wp_t 1"]
    # Orbitalschlag
    z += [bei("wp_orb", 1) + "playsound minecraft:block.end_portal.spawn block @a ~ ~ ~ 4 1.6",
          bei("wp_orb", 1, 40) + "particle minecraft:end_rod ~ ~15 ~ 0.05 15 0.05 0 25 force",
          bei("wp_orb", 1, 40) + "particle minecraft:dust{color:[1.0,0.1,0.1],scale:2.0} ~ ~0.3 ~ 3 0 3 0 25 force",
          bei("wp_orb", 20) + "playsound minecraft:entity.evoker.prepare_summon block @a ~ ~ ~ 3 0.6",
          bei("wp_orb", 38) + "playsound minecraft:entity.lightning_bolt.thunder block @a ~ ~ ~ 6 1.4",
          bei("wp_orb", 40) + "particle minecraft:firework ~ ~25 ~ 3 3 3 0.2 200 force"]
    ziele = [(0, 0), (3, 0), (-3, 0), (0, 3), (0, -3), (5, 5), (-5, 5), (5, -5), (-5, -5), (7, 0), (-7, 0), (0, 7), (0, -7)]
    for dx, dz in ziele:
        z.append(bei("wp_orb", 40) + "execute unless dimension %s run summon tnt ~%d ~30 ~%d {fuse:52,explosion_power:4.0f,Tags:[\"wp_tx\"]}"
                 % (DIM, dx, dz))
        z.append(bei("wp_orb", 70) + "execute if dimension %s positioned ~%d ~ ~%d run function wp:boom/sicher_4" % (DIM, dx, dz))
    z.append("kill @e[type=marker,tag=wp_orb,scores={wp_t=120..}]")
    # Meteor
    z += [bei("wp_met", 1) + 'summon item_display ~24 ~60 ~ {Tags:["wp_sys","wp_ms"],teleport_duration:2,'
          'item:{id:"minecraft:stick",count:1,components:{"minecraft:item_model":"%s:meteor"}},'
          'transformation:{left_rotation:[0f,0f,0f,1f],right_rotation:[0f,0f,0f,1f],translation:[0f,0f,0f],scale:[5f,5f,5f]},'
          'brightness:{sky:15,block:15}}' % NS,
          bei("wp_met", 1) + "playsound minecraft:entity.ender_dragon.growl block @a ~ ~ ~ 8 0.5",
          bei("wp_met", 1) + "title @a[distance=..80] actionbar %s" % jt(t("METEOR IM ANFLUG!", "gold", bold=True)),
          bei("wp_met", 10) + "playsound minecraft:entity.blaze.shoot block @a ~ ~ ~ 6 0.5",
          bei("wp_met", 25) + "playsound minecraft:entity.blaze.shoot block @a ~ ~ ~ 6 0.5",
          "execute as @e[type=item_display,tag=wp_ms] at @s run tp @s ~-0.6 ~-1.5 ~ ~10 ~",
          "execute as @e[type=item_display,tag=wp_ms] at @s run particle minecraft:flame ~ ~ ~ 1.2 1.2 1.2 0.05 25 force",
          "execute as @e[type=item_display,tag=wp_ms] at @s run particle minecraft:lava ~ ~ ~ 1 1 1 0 4 force",
          "execute as @e[type=item_display,tag=wp_ms] at @s run particle minecraft:large_smoke ~0.6 ~1.5 ~ 1 1 1 0.02 12 force",
          bei("wp_met", 41) + "kill @e[type=item_display,tag=wp_ms,distance=..12]",
          bei("wp_met", 41) + boom(p, 7),
          bei("wp_met", 41) + "particle minecraft:explosion_emitter ~ ~ ~ 3 2 3 0 14 force",
          bei("wp_met", 41) + "particle minecraft:lava ~ ~ ~ 3 1 3 0 60 force",
          bei("wp_met", 41) + "playsound minecraft:entity.lightning_bolt.thunder block @a ~ ~ ~ 10 0.6"]
    for tag in ("#minecraft:dirt", "#minecraft:base_stone_overworld", "#minecraft:sand", "minecraft:gravel"):
        z.append(bei("wp_met", 43) + "execute unless dimension %s run fill ~-4 ~-4 ~-4 ~4 ~-1 ~4 magma_block replace %s"
                 % (DIM, tag))
    for dx, dz in ((2, 0), (-2, 0), (0, 2), (0, -2)):
        z.append(bei("wp_met", 43) + "execute unless dimension %s run summon small_fireball ~%d ~3 ~%d {Motion:[0.0d,-1.0d,0.0d]}"
                 % (DIM, dx, dz))
    z.append("kill @e[type=marker,tag=wp_met,scores={wp_t=50..}]")
    # Vernichtung
    r = VERNICHTUNG_RADIUS
    alles = "@e[distance=..%d,type=!player,tag=!wp_sys,tag=!br_sys]" % r
    z += [bei("wp_vn", 1) + "execute store result score #anz wp_t if entity " + alles,
          bei("wp_vn", 1) + "execute as %s at @s run particle minecraft:cloud ~ ~1 ~ 0.3 0.5 0.3 0.05 6 force" % alles,
          bei("wp_vn", 1) + "kill " + alles,
          bei("wp_vn", 2) + "kill @e[distance=..%d,type=item]" % r,
          bei("wp_vn", 2) + "kill @e[distance=..%d,type=experience_orb]" % r,
          bei("wp_vn", 1) + "particle minecraft:explosion_emitter ~ ~ ~ 4 4 4 0 40 force",
          bei("wp_vn", 1) + "particle minecraft:end_rod ~ ~1 ~ 1 1 1 1.5 400 force",
          bei("wp_vn", 1) + "playsound minecraft:entity.wither.death master @a ~ ~ ~ 100 0.5",
          bei("wp_vn", 1) + "title @a[distance=..%d] times 5 60 20" % r,
          bei("wp_vn", 1) + "title @a[distance=..%d] subtitle %s" % (r, jt(
              [{"score": {"name": "#anz", "objective": "wp_t"}, "color": "red"},
               t(" Ziele im Umkreis von 1000 Blöcken", "gray")])),
          bei("wp_vn", 1) + "title @a[distance=..%d] title %s" % (r, jt(t("AUSGELÖSCHT", "dark_red", bold=True))),
          "kill @e[type=marker,tag=wp_vn,scores={wp_t=3..}]"]
    # Weltloescher: Schichten von oben nach unten, je Schicht 9 Felder (je <= 32768 Bloecke)
    h = WELTLOESCHER_HALB
    xs = [(-h, -h // 3 - 1), (-h // 3, h // 3 - 1), (h // 3, h - 1)]
    felder = sorted(((a, b) for a in xs for b in xs), key=lambda q: abs(q[0][0] + q[0][1]) + abs(q[1][0] + q[1][1]))
    schichten = []
    y = 319
    while y >= WELT_UNTEN:
        y0 = max(WELT_UNTEN, y - 3)
        schichten.append((y0, y))
        y = y0 - 1
    z += [bei("wp_wl", 1) + "title @a[distance=..150] times 5 60 20",
          bei("wp_wl", 1) + "title @a[distance=..150] subtitle %s" % jt(t("Alles im Umkreis von 48 Blöcken verschwindet", "gray")),
          bei("wp_wl", 1) + "title @a[distance=..150] title %s" % jt(t("WELTLÖSCHER", "white", bold=True)),
          bei("wp_wl", 1) + "playsound minecraft:entity.wither.spawn master @a ~ ~ ~ 10 0.5"]
    for i, (y0, y1) in enumerate(schichten):
        zeile = []
        for (x0, x1), (z0, z1) in felder:
            zeile.append("fill ~%d %d ~%d ~%d %d ~%d air" % (x0, y0, z0, x1, y1, z1))
        p.fn("wp:fx/wl_%d" % i, *zeile, "playsound minecraft:entity.generic.explode block @a ~ ~ ~ 4 0.5" if i % 6 == 0 else "")
        z.append(bei("wp_wl", 2 + i) + "function wp:fx/wl_%d" % i)
    z.append("execute as @e[type=marker,tag=wp_wl] at @s run particle minecraft:explosion ~ ~ ~ 20 10 20 0.1 30 force")
    z.append("kill @e[type=marker,tag=wp_wl,scores={wp_t=%d..}]" % (len(schichten) + 4))
    p.fn("wp:fx/tick", *z)


def schatten(p):
    p.fn("wp:schatten/lenken_alle",
         "execute as @e[type=arrow,tag=wp_ps] at @s if entity @e[type=#wp:feinde,distance=..12,tag=!wp_sys] "
         "unless data entity @s {inGround:1b} run function wp:schatten/lenken")
    p.fn("wp:schatten/lenken",
         "execute facing entity @e[type=#wp:feinde,distance=..12,tag=!wp_sys,sort=nearest,limit=1] eyes "
         "positioned 0.0 0.0 0.0 positioned ^ ^ ^2.2 summon marker run function wp:schatten/vektor",
         "data modify entity @s Motion set from storage wp:tmp v")
    p.fn("wp:schatten/vektor", "data modify storage wp:tmp v set from entity @s Pos", "kill @s")


def lampe(p):
    p.datei("data/wp/tags/block/luft.json", {"values": ["minecraft:air", "minecraft:cave_air"]})
    p.fn("wp:lampe/tick",
         "execute as @e[type=marker,tag=wp_licht] at @s if block ~ ~ ~ light run setblock ~ ~ ~ air",
         "kill @e[type=marker,tag=wp_licht]",
         "execute as @a[tag=wp_h9] at @s anchored eyes positioned ^ ^ ^ run function wp:lampe/start")
    p.fn("wp:lampe/start",
         "execute if block ~ ~ ~ #wp:luft run function wp:lampe/setzen_schwach",
         "scoreboard players set #schritt wp_t 0",
         "function wp:lampe/strahl")
    p.fn("wp:lampe/strahl",
         "scoreboard players add #schritt wp_t 1",
         "execute unless block ^ ^ ^0.5 #wp:durchlaessig run return run function wp:lampe/setzen",
         "execute if score #schritt wp_t matches 24.. run return run function wp:lampe/setzen",
         "execute positioned ^ ^ ^0.5 run function wp:lampe/strahl")
    p.fn("wp:lampe/setzen",
         "execute if block ~ ~ ~ #wp:luft run summon marker ~ ~ ~ {Tags:[\"wp_sys\",\"wp_licht\"]}",
         "execute if block ~ ~ ~ #wp:luft run setblock ~ ~ ~ light[level=15]")
    p.fn("wp:lampe/setzen_schwach",
         "summon marker ~ ~ ~ {Tags:[\"wp_sys\",\"wp_licht\"]}",
         "setblock ~ ~ ~ light[level=9]")


def sonder_tnt(p):
    z = ["execute as @e[type=tnt,tag=!wp_tx] at @s run particle minecraft:firework ~ ~1 ~ 0.05 0.05 0.05 0.03 1"]
    for dx, dz in ((3, 0), (-3, 0), (0, 3), (0, -3)):
        z.append("execute as @e[type=tnt,tag=!wp_tx] if data entity @s {fuse:1s} at @s run summon tnt ~%d ~ ~%d "
                 "{fuse:1,Tags:[\"wp_tx\"]}" % (dx, dz))
    z.append("execute as @e[type=tnt,tag=!wp_tx] if data entity @s {fuse:1s} at @s run playsound "
             "minecraft:entity.lightning_bolt.thunder block @a ~ ~ ~ 3 0.8")
    p.fn("wp:sondertnt", *z)


def grundlagen(p):
    p.datei("data/wp/tags/entity_type/feinde.json", {"values": ["minecraft:" + n for n in FEINDE]})
    p.datei("data/wp/tags/entity_type/kein_ziel.json", {"values": ["minecraft:" + n for n in KEIN_ZIEL]})
    p.datei("data/wp/tags/block/durchlaessig.json", {"values": [
        "#minecraft:replaceable", "minecraft:light", "#minecraft:flowers", "#minecraft:saplings",
        "minecraft:torch", "minecraft:wall_torch", "minecraft:soul_torch", "minecraft:soul_wall_torch",
        "minecraft:redstone_torch", "minecraft:redstone_wall_torch", "minecraft:end_rod", "minecraft:lever",
        "#minecraft:wall_signs", "#minecraft:buttons", "minecraft:sculk_vein"]})
    objekte = [("wp_rute", "minecraft.used:minecraft.carrot_on_a_stick"), ("wp_t", "dummy"), ("wp_alter", "dummy"),
               ("wp_art", "dummy"), ("wp_mg", "dummy")]
    p.fn("wp:laden", *["scoreboard objectives add %s %s" % o for o in objekte])
    p.fn("wp:tick",
         "execute as @a[tag=!wp_hat] at @s run function wp:items/erstausstattung",
         "function wp:halten",
         "function wp:pfeil/neu",
         "function wp:wurf/neu",
         "execute as @a[scores={wp_rute=1..}] at @s run function wp:rute",
         "scoreboard players reset @a wp_rute",
         "function wp:fahrzeug",
         "function wp:schatten/lenken_alle",
         "function wp:fx/tick",
         "function wp:lampe/tick",
         "function wp:sondertnt")


def paket(p):
    grundlagen(p)
    items(p)
    halten(p)
    pfeile(p)
    wurf(p)
    fahrzeug(p)
    strahlen(p)
    wirkungen(p)
    fx(p)
    schatten(p)
    lampe(p)
    sonder_tnt(p)
