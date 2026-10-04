"""Waffen, Spezial-TNT und Items: Item-Definitionen und Befehle, die jeden Tick laufen.

Alles nutzt nur Minecraft-1.12-Befehle:
- Pistole, Bazooka, Schatten-Bogen, Vernichtungs-Bogen: Boegen; ihre Pfeile werden
  erkannt und veraendert.
- Minigun und Orbital-Kanone: Karottenruten. Haelt man sie, liegt in der zweiten
  Hand Munition (Schneebaelle). Ein Rechtsklick mit der Karottenrute wirft dann den
  Schneeball genau in Blickrichtung; der Schneeball ist das Geschoss.
- Werf-TNT (10 Sorten): Wurftraenke mit eigenem Aussehen. Wo sie aufschlagen, wirkt
  die jeweilige Sorte. Nach jedem Wurf kommt ein neues in die Hand.
- Einschlagstellen findet ein Verfolger: jedes Geschoss bekommt jeden Tick eine
  Markierung an seiner Stelle; verschwindet das Geschoss, bleibt die letzte
  Markierung an der Einschlagstelle zurueck.
- Explosionen sind gezuendete Creeper. Ihre Explosion haengt an der Spielregel
  mobGriefing; die ist in den Backrooms aus, damit dort nichts kaputt geht.
"""

import json

import orte

# ---------------------------------------------------------------------------
# EINSTELLUNGEN
# ---------------------------------------------------------------------------

# Minecraft 1.12 begrenzt den Angriffsschaden-Attributwert auf 2048.
SCHWERT_ATTRIBUT_BONUS = 2047
PFEIL_SCHADEN = 2048          # Pistole und Bazooka (x Pfeilgeschwindigkeit, max. ca. 3)
SCHATTEN_SCHADEN = 60         # Schatten-Bogen
MINIGUN_SCHADEN = 10          # je Treffer (x 3)
MAX_STUFE = 32767

PROTECTION, FEATHER_FALLING, SHARPNESS, EFFICIENCY, INFINITY = 0, 2, 16, 32, 51
RUESTUNG_SCHUTZ = 1000
FEDERFALL = 32000
SCHWERT_STUFE20_VERZAUBERUNG = SHARPNESS   # Annahme, siehe README
SCHWERT_STUFE20_STUFE = 20
SPITZHACKE_EFFIZIENZ = min(727000, MAX_STUFE)

GOLDAEPFEL_ANZAHL = 64
ENDERPERLEN_ANZAHL = 16
PFEILE_ANZAHL = 64

ORBITAL_LADEZEIT = 100        # Ticks (5 Sekunden)
MAX_FLUGZEIT = 160            # Pfeile von Pistole/Bazooka, Raketen
MAX_GESCHOSS_ZEIT = 200       # Schneebaelle, Wurf-TNT, Boegen-Pfeile
VERNICHTUNG_RADIUS = 1000
WELTLOESCHER_HALB = 48        # geloeschte Flaeche: 96 x 96 Bloecke
WELTLOESCHER_UNTEN = 13       # bis zu dieser Hoehe (darunter: Befehlsbloecke)

# Schadenswerte (Metadaten), ueber die das Ressourcenpaket die eigenen Modelle zeigt
BOGEN = {"pistole": 1, "bazooka": 2, "schatten": 3, "vernichter": 4}
RUTE = {"taschenlampe": 1, "minigun": 2, "orbital": 3}
SCHWERT_DAMAGE = 1
HACKE = {"rakete": 10, "meteor": 11}

BOGEN_HALTBARKEIT = 384
KAROTTENRUTE_HALTBARKEIT = 25
DIAMANTSCHWERT_HALTBARKEIT = 1561
DIAMANTHACKE_HALTBARKEIT = 1561

# Kennzahl "wp" im Item, an der die Befehle erkennen, was ein Spieler haelt
WP = {"pistole": 1, "bazooka": 2, "minigun": 3, "orbital": 4, "schatten": 5, "vernichter": 6}
HALTE_TAG = {"pistole": "wp_p", "bazooka": "wp_b", "minigun": "wp_mg", "orbital": "wp_or",
             "schatten": "wp_s", "vernichter": "wp_v"}

# Werf-TNT: Nummer, Name, Farbcode des Namens, Farbe (Wurftrank), Beschreibung
GRANATEN = [
    (1, "Wurf-TNT", "c", 0xE53935, "Explodiert beim Aufprall"),
    (2, "Mega-TNT", "4", 0x8B0000, "Riesige Explosion"),
    (3, "Cluster-TNT", "e", 0xFFC107, "Zerfällt in 8 Bomben"),
    (4, "Feuer-TNT", "6", 0xFF6D00, "Explosion und Feuerregen"),
    (5, "Blitz-TNT", "9", 0x2979FF, "Ruft fünf Blitze"),
    (6, "Frost-TNT", "b", 0x84FFFF, "Friert Gegner und Boden ein"),
    (7, "Schwerkraft-TNT", "d", 0xAA00FF, "Lässt Gegner schweben"),
    (8, "Meteor-TNT", "8", 0x6D4C41, "Ruft einen Meteoriten"),
    (9, "Vernichtungs-TNT", "4", 0x161616, "Löscht alles im Umkreis von 1000 Blöcken aus"),
    (10, "Weltlöscher-TNT", "f", 0xF5F5F5, "Löscht die Welt im Umkreis von 48 Blöcken"),
]

FEINDE = ["zombie", "skeleton", "creeper", "spider", "cave_spider", "enderman", "witch", "slime",
          "magma_cube", "blaze", "ghast", "wither_skeleton", "husk", "stray", "zombie_villager",
          "zombie_pigman", "vindication_illager", "evocation_illager", "illusion_illager", "vex",
          "guardian", "elder_guardian", "shulker", "silverfish", "endermite", "polar_bear", "giant",
          "wither"]


# ---------------------------------------------------------------------------
# Hilfen
# ---------------------------------------------------------------------------

def ench(*paare):
    return "ench:[" + ",".join("{id:%ds,lvl:%ds}" % p for p in paare) + "]"


def give(ziel, item, anzahl, damage, tag):
    cmd = "give %s %s %d %d" % (ziel, item, anzahl, damage)
    return cmd + " " + tag if tag else cmd


def nbt_string(s):
    return '"' + s.replace("\\", "\\\\").replace('"', '\\"') + '"'


def j(obj):
    return json.dumps(obj, ensure_ascii=False, separators=(",", ":"))


def anzeige(name, farbe, zeilen=()):
    """display-Tag mit farbigem Namen (Farbcode) und Beschreibungszeilen."""
    lore = ",".join('"§7%s"' % z for z in zeilen)
    return 'display:{Name:"§%s%s",Lore:[%s]}' % (farbe, name, lore)


def boom(staerke):
    """Explosion an der aktuellen Stelle (gezuendeter Creeper, explodiert sofort)."""
    return ("summon creeper ~ ~ ~ {NoAI:1b,Silent:1b,Fuse:0s,ignited:1b,ExplosionRadius:%db,"
            "Tags:[wp_sys]}" % staerke)


def marke(*tags):
    """Unsichtbarer Ruestungsstaender als Markierung."""
    return ("summon armor_stand ~ ~ ~ {Marker:1b,Invisible:1b,NoGravity:1b,Invulnerable:1b,Tags:[%s]}"
            % ",".join(("wp_sys",) + tags))


# ---------------------------------------------------------------------------
# Items
# ---------------------------------------------------------------------------

def granate(nr):
    _, name, farbe, rgb, text = GRANATEN[nr - 1]
    return ("splash_potion", 1, 0,
            '{Potion:"minecraft:mundane",CustomPotionColor:%d,HideFlags:63,wt:%db,wtx:1b,%s}'
            % (rgb, nr, anzeige(name, farbe, [text, "Rechtsklick: werfen"])))


LAMPE = ("carrot_on_a_stick", 1, RUTE["taschenlampe"],
         "{Unbreakable:1b,HideFlags:63,br:1b,%s}" % anzeige("Taschenlampe", "e", ["Nachtsicht, solange in der Hand"]))

ITEMS = [
    ("bow", 1, BOGEN["pistole"], "{Unbreakable:1b,HideFlags:63,wp:1b,%s}" % anzeige("Pistole", "7")),
    ("bow", 1, BOGEN["bazooka"], "{Unbreakable:1b,HideFlags:63,wp:2b,%s}" % anzeige("Bazooka", "2")),
    ("carrot_on_a_stick", 1, RUTE["minigun"], "{Unbreakable:1b,HideFlags:63,wp:3b,%s}"
     % anzeige("Minigun", "6", ["Rechte Maustaste gedrückt halten"])),
    ("carrot_on_a_stick", 1, RUTE["orbital"], "{Unbreakable:1b,HideFlags:63,wp:4b,%s}"
     % anzeige("Orbital-TNT-Kanone", "b", ["Ziel anvisieren, Rechtsklick:", "TNT-Regen aus dem All"])),
    ("bow", 1, BOGEN["schatten"], "{Unbreakable:1b,HideFlags:63,wp:5b,%s,%s}"
     % (ench((INFINITY, 1)), anzeige("Ultimativer Schatten-Bogen", "5", ["Zielsuchende Schattenpfeile"]))),
    ("bow", 1, BOGEN["vernichter"], "{Unbreakable:1b,HideFlags:63,wp:6b,%s,%s}"
     % (ench((INFINITY, 1)), anzeige("Vernichtungs-Bogen", "4", ["Löscht beim Einschlag alles im",
                                                                  "Umkreis von 1000 Blöcken aus"]))),
    ("diamond_sword", 1, SCHWERT_DAMAGE,
     "{Unbreakable:1b,HideFlags:2,display:{Name:Schwert},AttributeModifiers:[{AttributeName:generic.attackDamage,"
     "Name:wp,Amount:%dd,Operation:0,UUIDLeast:1L,UUIDMost:1L,Slot:mainhand}]}" % SCHWERT_ATTRIBUT_BONUS),
    LAMPE,
    granate(1),
] + [granate(n) for n in range(2, 11)] + [
    ("tnt", 64, 0, "{%s}" % anzeige("Sonder-TNT", "c", ["Jede Explosion löst vier weitere aus"])),
    ("flint_and_steel", 1, 0, "{Unbreakable:1b}"),
    ("arrow", PFEILE_ANZAHL, 0, None),
    ("golden_apple", GOLDAEPFEL_ANZAHL, 1, None),
    ("ender_pearl", ENDERPERLEN_ANZAHL, 0, None),
    ("diamond_sword", 1, 0, "{%s}" % ench((SCHWERT_STUFE20_VERZAUBERUNG, SCHWERT_STUFE20_STUFE))),
    ("diamond_pickaxe", 1, 0, "{%s}" % ench((EFFICIENCY, SPITZHACKE_EFFIZIENZ))),
]

RUESTUNG = [
    ("slot.armor.head", "diamond_helmet", ench((PROTECTION, RUESTUNG_SCHUTZ))),
    ("slot.armor.chest", "diamond_chestplate", ench((PROTECTION, RUESTUNG_SCHUTZ))),
    ("slot.armor.legs", "diamond_leggings", ench((PROTECTION, RUESTUNG_SCHUTZ))),
    ("slot.armor.feet", "diamond_boots", ench((PROTECTION, RUESTUNG_SCHUTZ), (FEATHER_FALLING, FEDERFALL))),
]


def items_befehle():
    """Neue Spieler (ohne Markierung wp_hat) bekommen einmal alle Items und tragen die Ruestung."""
    befehle = ["scoreboard players tag @a[tag=!wp_hat] add wp_neu"]
    befehle += [give("@a[tag=wp_neu]", *i) for i in ITEMS]
    befehle += ["replaceitem entity @a[tag=wp_neu] %s %s 1 0 {%s}" % r for r in RUESTUNG]
    befehle += [
        "tellraw @a[tag=wp_neu] " + j(
            [{"text": "Willkommen! ", "color": "gold", "bold": True},
             {"text": "Tippe ", "color": "white"}, {"text": "/start", "color": "yellow", "bold": True},
             {"text": ", um die Backrooms zu betreten.", "color": "white"}]),
        "scoreboard players tag @a[tag=wp_neu] add wp_hat",
        "scoreboard players tag @a[tag=wp_neu] remove wp_neu",
    ]
    return befehle


# ---------------------------------------------------------------------------
# Pistole und Bazooka (Rakete folgt dem Pfeil)
# ---------------------------------------------------------------------------

RAKETE_KOPF_Y = 1.6
NEIGUNGEN = [(-90, -60, -75), (-60, -30, -45), (-30, -10, -20), (-10, 10, 0),
             (10, 30, 20), (30, 60, 45), (60, 90, 75)]
RAKETE_NBT = ("{Invisible:1b,Marker:1b,NoGravity:1b,Invulnerable:1b,Tags:[wp_r,wp_rn],"
              "ArmorItems:[{},{},{},{id:\"minecraft:diamond_hoe\",Count:1b,Damage:%ds,tag:{Unbreakable:1b}}],"
              "Pose:{Head:[%%.1ff,0f,0f]}}" % HACKE["rakete"])


def pistole_bazooka():
    c = [
        # Neue Pfeile in der Naehe von Spielern mit der Waffe in der Hand markieren
        "execute @a[tag=wp_p] ~ ~ ~ scoreboard players tag @e[type=arrow,r=6,tag=!wp_alt] add wp_pn",
        "execute @a[tag=wp_b] ~ ~ ~ scoreboard players tag @e[type=arrow,r=6,tag=!wp_alt] add wp_bn",
        "execute @a[tag=wp_s] ~ ~ ~ scoreboard players tag @e[type=arrow,r=6,tag=!wp_alt] add wp_sa",
        "execute @a[tag=wp_v] ~ ~ ~ scoreboard players tag @e[type=arrow,r=6,tag=!wp_alt] add wp_va",
        "scoreboard players tag @e[type=arrow] add wp_alt",
        # Pistole: Knall und Muendungsfeuer
        "execute @e[tag=wp_pn] ~ ~ ~ playsound entity.generic.explode master @a ~ ~ ~ 0.6 2",
        "execute @e[tag=wp_pn] ~ ~ ~ particle flame ~ ~ ~ 0.1 0.1 0.1 0.05 15 force",
        "scoreboard players tag @e[tag=wp_pn] add wp_p",
        "scoreboard players tag @e[tag=wp_p] remove wp_pn",
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
        "entitydata @e[type=arrow,tag=wp_p] {damage:%dd}" % PFEIL_SCHADEN,
        "entitydata @e[type=arrow,tag=wp_b] {damage:%dd}" % PFEIL_SCHADEN,
        "execute @e[type=arrow,tag=wp_p] ~ ~ ~ particle crit ~ ~ ~ 0 0 0 0 2 force",
        "scoreboard players tag @e[type=arrow,tag=wp_p] add wp_pweg {inGround:1b}",
        "execute @e[tag=wp_pweg] ~ ~ ~ particle smoke ~ ~ ~ 0.1 0.1 0.1 0.02 10 force",
        "kill @e[tag=wp_pweg]",
        # Bazooka-Pfeil im Boden: Explosion
        "scoreboard players tag @e[type=arrow,tag=wp_b] add wp_boom {inGround:1b}",
        "execute @e[tag=wp_boom] ~ ~ ~ " + boom(4),
        "execute @e[tag=wp_boom] ~ ~ ~ particle hugeexplosion ~ ~ ~ 1 1 1 0 3 force",
        "execute @e[tag=wp_boom] ~ ~ ~ kill @e[tag=wp_r,c=1,r=6]",
        "kill @e[tag=wp_boom]",
        # Rakete fliegt mit dem Pfeil ("teleport": ~ relativ zum Pfeil)
        "execute @e[type=arrow,tag=wp_b] ~ ~ ~ teleport @e[tag=wp_r,c=1] ~ ~-%.1f ~" % RAKETE_KOPF_Y,
        "execute @e[type=arrow,tag=wp_b] ~ ~ ~ particle flame ~ ~ ~ 0.15 0.15 0.15 0.01 4 force",
        "execute @e[type=arrow,tag=wp_b] ~ ~ ~ particle smoke ~ ~ ~ 0.15 0.15 0.15 0.01 3 force",
        # Rakete ohne Pfeil (Pfeil hat ein Lebewesen getroffen): dort explodieren
        "scoreboard players tag @e[tag=wp_r] add wp_rlos",
        "execute @e[type=arrow,tag=wp_b] ~ ~ ~ scoreboard players tag @e[tag=wp_r,r=4] remove wp_rlos",
        "execute @e[tag=wp_rlos] ~ ~%.1f ~ %s" % (RAKETE_KOPF_Y, boom(4)),
        "kill @e[tag=wp_rlos]",
        # Aufraeumen (in Eaglercraft bewegen sich Objekte am Rand der Sichtweite nicht)
        "scoreboard players add @e[tag=wp_r] wp_alter 1",
        "scoreboard players add @e[type=arrow,tag=wp_b] wp_alter 1",
        "scoreboard players add @e[type=arrow,tag=wp_p] wp_alter 1",
        "execute @e[score_wp_alter_min=%d] ~ ~ ~ particle cloud ~ ~ ~ 0.3 0.3 0.3 0.02 10 force" % MAX_FLUGZEIT,
        "kill @e[score_wp_alter_min=%d]" % MAX_FLUGZEIT,
    ]
    return c


# ---------------------------------------------------------------------------
# Geschosse mit Einschlag-Wirkung
# ---------------------------------------------------------------------------

# Art -> (Markierung des Geschosses, Markierung der Spur)
ARTEN = {"mg": "wp_mgk", "or": "wp_ork", "sa": "wp_sa", "va": "wp_va"}
ARTEN.update({"w%d" % n: "wt%d" % n for n in range(1, 11)})


def spur(art):
    return "wp_m" + art


def geschosse():
    c = []
    # Alter der bekannten Geschosse
    c.append("scoreboard players add @e[tag=wp_proj] wp_flug 1")
    # Neue Schneebaelle von Minigun und Orbital-Kanone
    c += [
        "execute @a[tag=wp_mg] ~ ~ ~ scoreboard players tag @e[type=snowball,r=4,tag=!wp_proj] add wp_mgk",
        "execute @a[tag=wp_or] ~ ~ ~ scoreboard players tag @e[type=snowball,r=4,tag=!wp_proj] add wp_ork",
    ]
    # Neue Wurf-TNT
    for n in range(1, 11):
        c.append("scoreboard players tag @e[type=potion,tag=!wp_proj] add wt%d {Potion:{tag:{wt:%db}}}" % (n, n))
    for tag in ARTEN.values():
        c.append("scoreboard players tag @e[tag=%s] add wp_proj" % tag)
    c.append("scoreboard players add @e[tag=wp_proj] wp_flug 0")
    neu = "score_wp_flug=0"
    # Abschuss-Wirkungen
    c += [
        "execute @e[tag=wp_mgk,%s] ~ ~ ~ playsound entity.firework.blast master @a ~ ~ ~ 0.7 2" % neu,
        "execute @e[tag=wp_mgk,%s] ~ ~ ~ playsound entity.generic.explode master @a ~ ~ ~ 0.2 2" % neu,
        # Muendungsfeuer erst einen Tick spaeter (sonst direkt vor der Kamera)
        "execute @e[tag=wp_mgk,score_wp_flug_min=1,score_wp_flug=1] ~ ~ ~ particle flame ~ ~ ~ 0.05 0.05 0.05 0.02 2 force",
        "execute @e[tag=wp_mgk,score_wp_flug_min=1,score_wp_flug=1] ~ ~ ~ particle smoke ~ ~ ~ 0.05 0.05 0.05 0.01 2 force",
        # Zielstrahl und Minigun-Kugeln fliegen geradeaus (ohne Schwerkraft): grosse Reichweite
        "entitydata @e[tag=wp_ork,%s] {NoGravity:1b}" % neu,
        "entitydata @e[tag=wp_mgk,%s] {NoGravity:1b}" % neu,
        "execute @e[tag=wp_ork,%s] ~ ~ ~ playsound entity.firework.launch master @a ~ ~ ~ 1 1.6" % neu,
        "execute @e[tag=wp_ork,%s] ~ ~ ~ scoreboard players set @p[tag=wp_or,r=4] wp_ocd %d" % (neu, ORBITAL_LADEZEIT),
        "execute @e[tag=wp_sa,%s] ~ ~ ~ playsound entity.wither.shoot master @a ~ ~ ~ 0.6 1.6" % neu,
        "entitydata @e[type=arrow,tag=wp_sa] {damage:%dd}" % SCHATTEN_SCHADEN,
        "execute @e[tag=wp_va,%s] ~ ~ ~ playsound entity.enderdragon.shoot master @a ~ ~ ~ 1 0.6" % neu,
    ]
    # Werf-TNT nachfuellen: neues TNT in die (leere) Hand des Werfers
    for n in range(1, 11):
        item, anz, dmg, tag = granate(n)
        c.append("execute @e[tag=wt%d,%s] ~ ~ ~ replaceitem entity @p[r=4,score_wp_hand_min=1,m=!1] "
                 "slot.weapon.mainhand %s %d %d %s" % (n, neu, item, anz, dmg, tag))
    # Zu alte Geschosse entfernen (ohne Einschlag-Wirkung)
    c += [
        "execute @e[tag=wp_proj,score_wp_flug_min=%d] ~ ~ ~ kill @e[tag=wp_spur,r=3]" % MAX_GESCHOSS_ZEIT,
        "kill @e[tag=wp_proj,score_wp_flug_min=%d]" % MAX_GESCHOSS_ZEIT,
    ]
    # Verfolger: alte Markierungen altern, neue an jedes Geschoss
    c.append("scoreboard players add @e[tag=wp_spur] wp_alter 1")
    for art, tag in ARTEN.items():
        c.append("execute @e[tag=%s] ~ ~ ~ %s" % (tag, marke("wp_spur", spur(art))))
    c.append("kill @e[tag=wp_treffer]")
    # Fliegt das Geschoss noch, ist die alte Markierung ueberfluessig
    c.append("execute @e[tag=wp_proj] ~ ~ ~ kill @e[tag=wp_spur,r=2.5,score_wp_alter_min=1]")
    # Uebrig gebliebene alte Markierungen sind Einschlagstellen
    alt = "score_wp_alter_min=1"
    c += [
        "scoreboard players set @e[tag=wp_spur,%s] wp_inbr 0" % alt,
        "scoreboard players set @e[tag=wp_spur,%s,%s] wp_inbr 1" % (alt, orte.BEREICH),
    ]
    c += einschlaege(alt)
    c.append("kill @e[tag=wp_spur,%s]" % alt)
    # Boegen-Pfeile im Boden entfernen (ihr Einschlag wird im naechsten Tick ausgeloest)
    c += [
        "scoreboard players tag @e[type=arrow,tag=wp_proj] add wp_steckt {inGround:1b}",
        "kill @e[tag=wp_steckt]",
    ]
    # Flugspuren
    # (erst ab dem zweiten Flug-Tick: vorher ist das Geschoss noch am Kopf des Schuetzen)
    weg = "score_wp_flug_min=2"
    c += [
        "execute @e[tag=wp_mgk,%s] ~ ~ ~ particle crit ~ ~ ~ 0 0 0 0 1 force" % weg,
        "execute @e[tag=wp_ork,%s] ~ ~ ~ particle endRod ~ ~ ~ 0 0 0 0 1 force" % weg,
        "execute @e[tag=wp_ork,%s] ~ ~ ~ particle reddust ~ ~ ~ 0 0 0 0 2 force" % weg,
        "execute @e[tag=wp_sa,%s] ~ ~ ~ particle dragonbreath ~ ~ ~ 0.05 0.05 0.05 0.01 3 force" % weg,
        "execute @e[tag=wp_sa,%s] ~ ~ ~ particle portal ~ ~ ~ 0.2 0.2 0.2 0.6 4 force" % weg,
        "execute @e[tag=wp_va,%s] ~ ~ ~ particle endRod ~ ~ ~ 0.05 0.05 0.05 0.01 2 force" % weg,
        "execute @e[tag=wp_va,%s] ~ ~ ~ particle reddust ~ ~ ~ 0.1 0.1 0.1 0 4 force" % weg,
        "execute @e[type=potion,tag=wp_proj,%s] ~ ~ ~ particle flame ~ ~0.3 ~ 0 0 0 0 1 force" % weg,
        "execute @e[type=potion,tag=wp_proj,%s] ~ ~ ~ particle smoke ~ ~0.3 ~ 0 0 0 0 1 force" % weg,
    ]
    # Schatten-Pfeile suchen ihr Ziel: naechster Gegner in 7 Bloecken
    c.append("scoreboard players tag @e[tag=wp_feind] remove wp_feind")
    for typ in FEINDE:
        c.append("execute @e[tag=wp_sa] ~ ~ ~ scoreboard players tag @e[type=%s,r=8,tag=!wp_sys] add wp_feind" % typ)
    # Erfasster Gegner: Treffer von oben, Schattenpfeil springt zum Gegner (dort wirkt der Einschlag)
    erfasst = "execute @e[type=arrow,tag=wp_sa] ~ ~ ~ execute @e[tag=wp_feind,r=7,c=1] ~ ~ ~ "
    c += [
        erfasst + "summon arrow ~ ~2.6 ~ {Motion:[0d,-3d,0d],damage:%dd,Tags:[wp_sys,wp_alt]}" % SCHATTEN_SCHADEN,
        erfasst + "particle portal ~ ~1 ~ 0.3 0.6 0.3 1 30 force",
        "execute @e[type=arrow,tag=wp_sa] ~ ~ ~ execute @e[tag=wp_feind,r=7,c=1] ~ ~ ~ "
        "scoreboard players tag @e[type=arrow,tag=wp_sa,r=8,c=1] add wp_treffer",
        "execute @e[tag=wp_treffer] ~ ~ ~ kill @e[tag=wp_spur,r=2.5]",
        "execute @e[tag=wp_treffer] ~ ~ ~ tp @s @e[tag=wp_feind,r=8,c=1]",
        "entitydata @e[tag=wp_treffer] {NoGravity:1b,Motion:[0d,0d,0d]}",
    ]
    return c


def einschlaege(alt):
    """Wirkung an jeder Einschlagstelle, je nach Art."""
    def bei(art, extra=""):
        return "execute @e[tag=%s,%s%s] ~ ~ ~ " % (spur(art), alt, extra)
    draussen = ",score_wp_inbr=0"
    drinnen = ",score_wp_inbr_min=1"
    c = []

    # Minigun: Treffer am naechsten Lebewesen (Pfeil von oben, Schaden 3 x MINIGUN_SCHADEN)
    c += [
        bei("mg") + "execute @e[r=2.5,c=1,type=!player,tag=!wp_sys] ~ ~ ~ summon arrow ~ ~2.6 ~ "
                    "{Motion:[0d,-3d,0d],damage:%dd,Tags:[wp_sys,wp_alt,wp_mgp]}" % MINIGUN_SCHADEN,
        bei("mg") + "particle crit ~ ~ ~ 0.2 0.2 0.2 0.3 6 force",
        bei("mg") + "playsound entity.arrow.hit master @a ~ ~ ~ 0.5 1.4",
    ]
    # Orbital-Kanone: Zielmarkierung fuer den Orbitalschlag
    c.append(bei("or") + marke("wp_fx", "wp_orb"))
    # Schatten-Bogen: Schattenzaehne, Verdorrung, Blindheit
    c += [
        bei("sa") + "execute @e[r=4,c=3,type=!player,tag=!wp_sys] ~ ~ ~ summon evocation_fangs ~ ~ ~",
        bei("sa") + "effect @e[r=4,type=!player,tag=!wp_sys] wither 6 2",
        bei("sa") + "effect @e[r=4,type=!player,tag=!wp_sys] blindness 4 0",
        bei("sa") + "effect @e[r=4,type=!player,tag=!wp_sys] slowness 4 2",
        bei("sa") + "particle dragonbreath ~ ~ ~ 1.2 0.8 1.2 0.02 70 force",
        bei("sa") + "particle portal ~ ~ ~ 1 1 1 1 60 force",
        bei("sa") + "playsound entity.evocation_fangs.attack master @a ~ ~ ~ 1 0.7",
        bei("sa") + "playsound entity.wither.hurt master @a ~ ~ ~ 0.6 1.5",
    ]
    # Vernichtungs-Bogen und Vernichtungs-TNT
    for art in ("va", "w9"):
        c.append(bei(art) + marke("wp_fx", "wp_vn"))
    # 1 Wurf-TNT
    c += [bei("w1") + boom(4)]
    # 2 Mega-TNT
    c += [
        bei("w2") + boom(10),
        bei("w2") + "particle hugeexplosion ~ ~ ~ 4 2 4 0 12 force",
        bei("w2") + "playsound entity.generic.explode master @a ~ ~ ~ 8 0.5",
    ]
    # 3 Cluster-TNT: acht kleine Bomben fliegen nach aussen
    c.append(bei("w3") + boom(3))
    for dx, dz in ((1, 0), (-1, 0), (0, 1), (0, -1), (0.7, 0.7), (-0.7, 0.7), (0.7, -0.7), (-0.7, -0.7)):
        c.append(bei("w3") + "summon tnt ~ ~0.5 ~ {Fuse:30,Motion:[%.2fd,0.55d,%.2fd],Tags:[wp_tx]}"
                 % (dx * 0.45, dz * 0.45))
    # 4 Feuer-TNT: Explosion und Feuerregen
    c += [bei("w4") + boom(3), bei("w4") + "particle lava ~ ~ ~ 2 1 2 0 40 force",
          bei("w4") + "particle flame ~ ~1 ~ 2 1 2 0.05 80 force"]
    for dx, dz in ((3, 0), (-3, 0), (0, 3), (0, -3), (2, 2), (-2, 2), (2, -2), (-2, -2)):
        c.append(bei("w4") + "summon small_fireball ~%d ~4 ~%d {direction:[0.0,-0.6,0.0],power:[0.0,-0.1,0.0]}"
                 % (dx, dz))
    # 5 Blitz-TNT
    c.append(bei("w5") + boom(2))
    for dx, dz in ((0, 0), (4, 0), (-4, 0), (0, 4), (0, -4)):
        c.append(bei("w5") + "summon lightning_bolt ~%d ~ ~%d" % (dx, dz))
    # 6 Frost-TNT: Gegner eingefroren, Wasser wird Eis, Boden wird Packeis
    c += [
        bei("w6") + "effect @e[r=8,type=!player,tag=!wp_sys] slowness 10 6 true",
        bei("w6") + "effect @e[r=8,type=!player,tag=!wp_sys] jump_boost 10 128 true",
        bei("w6") + "effect @e[r=8,type=!player,tag=!wp_sys] weakness 10 2 true",
        bei("w6") + "particle snowshovel ~ ~1 ~ 4 2 4 0.05 300 force",
        bei("w6") + "particle blockcrack ~ ~1 ~ 3 1 3 0.1 150 force 79",
        bei("w6") + "playsound block.glass.break master @a ~ ~ ~ 2 0.6",
    ]
    for block in ("water", "flowing_water"):
        c.append(bei("w6", draussen) + "fill ~-6 ~-3 ~-6 ~6 ~2 ~6 ice 0 replace %s" % block)
    for block in ("lava", "flowing_lava"):
        c.append(bei("w6", draussen) + "fill ~-6 ~-3 ~-6 ~6 ~2 ~6 obsidian 0 replace %s" % block)
    for block in ("grass", "dirt", "stone", "sand", "gravel"):
        c.append(bei("w6", draussen) + "fill ~-5 ~-2 ~-5 ~5 ~ ~5 packed_ice 0 replace %s" % block)
    # 7 Schwerkraft-TNT: alles schwebt nach oben und faellt
    c += [
        bei("w7") + "effect @e[r=10,type=!player,tag=!wp_sys] levitation 3 6 true",
        bei("w7") + "particle portal ~ ~1 ~ 3 2 3 1 200 force",
        bei("w7") + "particle witchMagic ~ ~1 ~ 3 2 3 0.1 60 force",
        bei("w7") + "playsound entity.shulker.shoot master @a ~ ~ ~ 2 0.5",
        bei("w7") + "playsound entity.illusion_illager.cast_spell master @a ~ ~ ~ 2 0.7",
    ]
    # 8 Meteor-TNT
    c.append(bei("w8") + marke("wp_fx", "wp_met"))
    # 10 Weltloescher-TNT (nicht in den Backrooms)
    c += [
        bei("w10", draussen) + marke("wp_fx", "wp_wl"),
        bei("w10", drinnen) + "particle smoke ~ ~ ~ 0.5 0.5 0.5 0.02 40 force",
        bei("w10", drinnen) + "tellraw @a[r=30] " + j({"text": "Der Weltlöscher wirkt in den Backrooms nicht.",
                                                         "color": "gray", "italic": True}),
    ]
    return c


# ---------------------------------------------------------------------------
# Laengere Wirkungen: Orbitalschlag, Meteor, Vernichtung, Weltloescher
# ---------------------------------------------------------------------------

def bei_t(tag, t0, t1=None, extra=""):
    t1 = t0 if t1 is None else t1
    return "execute @e[tag=%s,score_wp_t_min=%d,score_wp_t=%d%s] ~ ~ ~ " % (tag, t0, t1, extra)


def weltloescher_fuellungen():
    """Loeschbereich in Bloecke <= 32768 zerlegen: Schichten von oben nach unten,
    in jeder Schicht zuerst die Mitte."""
    h = WELTLOESCHER_HALB
    xs = [(-h, -h // 3 - 1), (-h // 3, h // 3 - 1), (h // 3, h - 1)]
    spalten = sorted(((a, b) for a in xs for b in xs),
                     key=lambda p: abs(p[0][0] + p[0][1]) + abs(p[1][0] + p[1][1]))
    schichten = []
    y = 255
    while y >= WELTLOESCHER_UNTEN:
        y0 = max(WELTLOESCHER_UNTEN, y - 31)
        schichten.append((y0, y))
        y = y0 - 1
    return [(sx, sz, y0, y1) for (y0, y1) in schichten for (sx, sz) in spalten]


def wirkungen():
    c = [
        "scoreboard players add @e[tag=wp_fx] wp_t 1",
        "scoreboard players set @e[tag=wp_fx] wp_inbr 0",
        "scoreboard players set @e[tag=wp_fx,%s] wp_inbr 1" % orte.BEREICH,
    ]
    draussen, drinnen = ",score_wp_inbr=0", ",score_wp_inbr_min=1"

    # --- Orbitalschlag: Zielstrahl 2 Sekunden, dann TNT-Regen ---
    c += [
        bei_t("wp_orb", 1) + "playsound block.end_portal.spawn master @a ~ ~ ~ 4 1.6",
        bei_t("wp_orb", 1) + "title @a[r=60] actionbar " + j({"text": "ORBITALSCHLAG IN 2 SEKUNDEN", "color": "red", "bold": True}),
        bei_t("wp_orb", 1, 40) + "particle endRod ~ ~12 ~ 0.05 12 0.05 0 25 force",
        bei_t("wp_orb", 1, 40) + "particle reddust ~ ~0.3 ~ 3 0 3 0 25 force",
        bei_t("wp_orb", 20) + "playsound entity.evocation_illager.prepare_summon master @a ~ ~ ~ 3 0.6",
        bei_t("wp_orb", 38) + "playsound entity.lightning.thunder master @a ~ ~ ~ 6 1.4",
        bei_t("wp_orb", 40) + "particle fireworksSpark ~ ~25 ~ 3 3 3 0.2 200 force",
    ]
    ziele = [(0, 0), (3, 0), (-3, 0), (0, 3), (0, -3), (5, 5), (-5, 5), (5, -5), (-5, -5),
             (7, 0), (-7, 0), (0, 7), (0, -7)]
    for dx, dz in ziele:
        c.append(bei_t("wp_orb", 40, 40, draussen) + "summon tnt ~%d ~30 ~%d {Fuse:52,Tags:[wp_tx]}" % (dx, dz))
        c.append(bei_t("wp_orb", 40, 40, drinnen) + "summon tnt ~%d ~2 ~%d {Fuse:24,Tags:[wp_tx]}" % (dx, dz))
    c.append("kill @e[tag=wp_orb,score_wp_t_min=120]")

    # --- Meteor: faellt schraeg aus 60 Bloecken Hoehe, schlaegt ein ---
    stein = ("summon armor_stand ~24 ~60 ~ {Marker:1b,Invisible:1b,NoGravity:1b,Invulnerable:1b,"
             "Tags:[wp_sys,wp_ms],Pose:{Head:[0f,0f,0f]},ArmorItems:[{},{},{},{id:\"minecraft:diamond_hoe\","
             "Count:1b,Damage:%ds,tag:{Unbreakable:1b}}]}" % HACKE["meteor"])
    c += [
        bei_t("wp_met", 1, 1, draussen) + stein,
        bei_t("wp_met", 1) + "playsound entity.enderdragon.growl master @a ~ ~ ~ 8 0.5",
        bei_t("wp_met", 1) + "title @a[r=80] actionbar " + j({"text": "METEOR IM ANFLUG!", "color": "gold", "bold": True}),
        "execute @e[tag=wp_ms] ~ ~ ~ teleport @s ~-0.6 ~-1.5 ~",
        "execute @e[tag=wp_ms] ~ ~2 ~ particle flame ~ ~ ~ 0.8 0.8 0.8 0.05 14 force",
        "execute @e[tag=wp_ms] ~ ~2 ~ particle lava ~ ~ ~ 0.6 0.6 0.6 0 3 force",
        "execute @e[tag=wp_ms] ~ ~2 ~ particle largesmoke ~ ~ ~ 0.8 0.8 0.8 0.02 8 force",
        bei_t("wp_met", 10) + "playsound entity.blaze.shoot master @a ~ ~ ~ 6 0.5",
        bei_t("wp_met", 25) + "playsound entity.blaze.shoot master @a ~ ~ ~ 6 0.5",
        bei_t("wp_met", 41) + "kill @e[tag=wp_ms,r=8]",
        bei_t("wp_met", 41) + boom(7),
        bei_t("wp_met", 41) + "particle hugeexplosion ~ ~ ~ 3 2 3 0 14 force",
        bei_t("wp_met", 41) + "particle lava ~ ~ ~ 3 1 3 0 60 force",
        bei_t("wp_met", 41) + "playsound entity.generic.explode master @a ~ ~ ~ 10 0.5",
        bei_t("wp_met", 41) + "playsound entity.lightning.thunder master @a ~ ~ ~ 10 0.6",
    ]
    for block in ("grass", "dirt", "stone", "sand", "gravel", "sandstone"):
        c.append(bei_t("wp_met", 43, 43, draussen) + "fill ~-4 ~-4 ~-4 ~4 ~-1 ~4 magma 0 replace %s" % block)
    for dx, dz in ((2, 0), (-2, 0), (0, 2), (0, -2)):
        c.append(bei_t("wp_met", 43, 43, draussen)
                 + "summon small_fireball ~%d ~3 ~%d {direction:[0.0,-0.6,0.0],power:[0.0,-0.1,0.0]}" % (dx, dz))
    c.append("kill @e[tag=wp_met,score_wp_t_min=50]")

    # --- Vernichtung: alles im Umkreis von 1000 Bloecken ausser Spielern ---
    alles = "@e[r=%d,type=!player,tag=!wp_sys]" % VERNICHTUNG_RADIUS
    r = VERNICHTUNG_RADIUS
    c += [
        # Reihenfolge wichtig: wp_anz zaehlt die Getoeteten (stats), der Untertitel zeigt es an
        bei_t("wp_vn", 1) + "execute %s ~ ~ ~ particle cloud ~ ~1 ~ 0.3 0.5 0.3 0.05 6 force" % alles,
        bei_t("wp_vn", 1) + "title @a[r=%d] times 5 60 20" % r,
        bei_t("wp_vn", 1) + "scoreboard players set @s wp_anz 0",
        bei_t("wp_vn", 1) + "execute %s ~ ~ ~ scoreboard players add @e[tag=wp_vn,c=1] wp_anz 1" % alles,
        bei_t("wp_vn", 1) + "kill " + alles,
        bei_t("wp_vn", 1) + "title @a[r=%d] subtitle " % r + j(
            [{"score": {"name": "@e[tag=wp_vn,c=1]", "objective": "wp_anz"}, "color": "red"},
             {"text": " Ziele im Umkreis von 1000 Blöcken", "color": "gray"}]),
        bei_t("wp_vn", 1) + "title @a[r=%d] title " % r + j(
            {"text": "AUSGELÖSCHT", "color": "dark_red", "bold": True}),
        bei_t("wp_vn", 1) + "particle hugeexplosion ~ ~ ~ 4 4 4 0 40 force",
        bei_t("wp_vn", 1) + "particle endRod ~ ~1 ~ 1 1 1 1.5 400 force",
        bei_t("wp_vn", 1) + "playsound entity.wither.death master @a ~ ~ ~ 100 0.5",
        bei_t("wp_vn", 1) + "playsound entity.generic.explode master @a ~ ~ ~ 100 0.5",
        # Beute der Getoeteten ebenfalls entfernen
        bei_t("wp_vn", 2) + "kill @e[r=%d,type=item]" % VERNICHTUNG_RADIUS,
        bei_t("wp_vn", 2) + "kill @e[r=%d,type=xp_orb]" % VERNICHTUNG_RADIUS,
        "kill @e[tag=wp_vn,score_wp_t_min=3]",
    ]

    # --- Weltloescher: Flaeche Schicht fuer Schicht von oben nach unten loeschen ---
    fuellungen = weltloescher_fuellungen()
    c += [
        bei_t("wp_wl", 1) + "title @a[r=100] times 5 60 20",
        bei_t("wp_wl", 1) + "title @a[r=100] subtitle " + j({"text": "Alles im Umkreis von %d Blöcken verschwindet"
                                                                   % WELTLOESCHER_HALB, "color": "gray"}),
        bei_t("wp_wl", 1) + "title @a[r=100] title " + j({"text": "WELTLÖSCHER", "color": "white", "bold": True}),
        bei_t("wp_wl", 1) + "playsound entity.wither.spawn master @a ~ ~ ~ 10 0.5",
    ]
    for i, ((x0, x1), (z0, z1), y0, y1) in enumerate(fuellungen):
        t = 2 + i
        c.append(bei_t("wp_wl", t) + "fill ~%d %d ~%d ~%d %d ~%d air" % (x0, y0, z0, x1, y1, z1))
        if i % 9 == 0:
            c.append(bei_t("wp_wl", t) + "playsound entity.generic.explode master @a ~ ~ ~ 6 0.5")
    c += [
        bei_t("wp_wl", 2, 1 + len(fuellungen)) + "particle explode ~ ~ ~ 20 10 20 0.1 40 force",
        "kill @e[tag=wp_wl,score_wp_t_min=%d]" % (len(fuellungen) + 4),
    ]
    return c


# ---------------------------------------------------------------------------
# Alles zusammen
# ---------------------------------------------------------------------------

def halten():
    """Wer haelt was, Munition fuer Minigun/Orbital-Kanone, Pfeile nachfuellen."""
    c = ["scoreboard players tag @a remove %s" % t for t in list(HALTE_TAG.values()) + ["wp_feuer"]]
    for name, tag in HALTE_TAG.items():
        c.append("scoreboard players tag @a add %s {SelectedItem:{tag:{wp:%db}}}" % (tag, WP[name]))
    c += [
        "scoreboard players tag @a[tag=wp_mg] add wp_feuer",
        "scoreboard players tag @a[tag=wp_or] add wp_feuer",
        # leere Hand? (wp_hand 1 = nichts in der Hand)
        "scoreboard players set @a wp_hand 1",
        "scoreboard players set @a wp_hand 0 {SelectedItem:{}}",
        # zweite Hand frei (oder schon Munition)?
        "scoreboard players set @a wp_off 0",
        "scoreboard players set @a wp_off 1 {Inventory:[{Slot:-106b}]}",
        "scoreboard players set @a wp_off 0 {Inventory:[{Slot:-106b,tag:{wpm:1b}}]}",
        "scoreboard players add @a wp_ocd 0",
        "scoreboard players remove @a[score_wp_ocd_min=1] wp_ocd 1",
        "replaceitem entity @a[tag=wp_mg,score_wp_off=0] slot.weapon.offhand snowball 16 0 "
        "{wpm:1b,%s}" % anzeige("Munition", "6"),
        "replaceitem entity @a[tag=wp_or,score_wp_off=0,score_wp_ocd=0] slot.weapon.offhand snowball 1 0 "
        "{wpm:1b,%s}" % anzeige("Zielstrahl", "b"),
        "clear @a[tag=!wp_feuer] snowball -1 -1 {wpm:1b}",
        "clear @a[tag=wp_or,score_wp_ocd_min=1] snowball -1 -1 {wpm:1b}",
        "scoreboard players tag @e[type=item] add wp_mweg {Item:{tag:{wpm:1b}}}",
        "kill @e[tag=wp_mweg]",
        "execute @e[tag=br_state,score_br_t_min=0,score_br_t=0] ~ ~ ~ title @a[tag=wp_or,score_wp_ocd_min=1] "
        "actionbar " + j({"text": "Orbital-Kanone lädt …", "color": "aqua"}),
        "execute @e[tag=br_state,score_br_t_min=0,score_br_t=0] ~ ~ ~ title @a[tag=wp_or,score_wp_ocd=0] "
        "actionbar " + j({"text": "Orbital-Kanone bereit: Ziel anvisieren, Rechtsklick", "color": "green"}),
        # Pfeile nachfuellen, wenn keine mehr da sind
        "scoreboard players set @a wp_pf 0",
        "scoreboard players set @a wp_pf 1 {Inventory:[{id:\"minecraft:arrow\"}]}",
    ]
    for tag in ("wp_p", "wp_b", "wp_s", "wp_v"):
        c.append("give @a[tag=%s,score_wp_pf=0] arrow %d" % (tag, PFEILE_ANZAHL))
    return c


def schutz_backrooms():
    """In den Backrooms geht nichts kaputt: TNT explodiert dort wie ein Creeper."""
    return [
        "gamerule mobGriefing true",
        "execute @a[%s] ~ ~ ~ gamerule mobGriefing false" % orte.BEREICH,
        "scoreboard players tag @e[type=tnt,%s] add wp_tbr {Fuse:1s}" % orte.BEREICH,
        "execute @e[tag=wp_tbr] ~ ~ ~ " + boom(4),
        "kill @e[tag=wp_tbr]",
    ]


def sonder_tnt():
    """Sonder-TNT (Block): jede Explosion loest vier weitere aus."""
    c = [
        "execute @e[type=tnt,tag=!wp_tx] ~ ~ ~ particle fireworksSpark ~ ~1 ~ 0.05 0.05 0.05 0.03 1",
        "scoreboard players tag @e[type=tnt,tag=!wp_tx] add wp_mega {Fuse:2s}",
    ]
    for dx, dz in ((3, 0), (-3, 0), (0, 3), (0, -3)):
        c.append("execute @e[tag=wp_mega] ~ ~ ~ summon tnt ~%d ~ ~%d {Fuse:1s,Tags:[wp_tx]}" % (dx, dz))
    c += [
        "execute @e[tag=wp_mega] ~ ~ ~ particle lava ~ ~ ~ 2 1 2 0 40 force",
        "execute @e[tag=wp_mega] ~ ~ ~ playsound entity.lightning.thunder block @a ~ ~ ~ 3 0.8",
        "scoreboard players tag @e[tag=wp_mega] remove wp_mega",
    ]
    return c


def ketten():
    """Befehlsketten der Waffen (jede Liste wird eine eigene Kette)."""
    return [items_befehle() + halten(),
            pistole_bazooka() + geschosse(),
            wirkungen() + sonder_tnt() + schutz_backrooms()]


def objectives():
    return ["scoreboard objectives add %s dummy" % o
            for o in ("wp_alter", "wp_flug", "wp_t", "wp_hand", "wp_off", "wp_ocd", "wp_inbr", "wp_anz", "wp_pf")]


def einzelbefehle():
    """Chat-Befehle (je max. 256 Zeichen) fuer andere Welten. Im Chat ist das Zeichen
    fuer Farbcodes nicht erlaubt, deshalb ohne Farben."""
    zeilen = []
    for i in ITEMS:
        z = "/" + give("@p", *i)
        z = z.replace("§", "")
        for f in "0123456789abcdef":
            z = z.replace('Name:"%s' % f, 'Name:"').replace('"7', '"')
        zeilen.append(z)
    return zeilen
