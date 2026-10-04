"""Lage der Backrooms: weit weg vom Spawnpunkt, hoch ueber dem Boden.

Die Backrooms liegen nicht mehr unter dem Spawnpunkt, sondern an einem festen,
weit entfernten Ort in der Luft (in geschlossenen Kaesten). Hinein kommt man
nur ueber Portale. Der Spawnbereich mit den Befehlsbloecken bleibt in
Minecraft und in Eaglercraft immer geladen (in Eaglercraft getestet: der
Zaehler lief auch 3000 Bloecke entfernt weiter).
"""

BRX, BRZ = 12000, 12000      # Mitte der Backrooms
B = 200                      # Hoehe des Fussbodens aller Level

# Level 0-4 und die Arena (5): Ecke x/z, Breite w, Tiefe d, Hoehe h
LEVEL = {
    0: dict(x=BRX - 120, z=BRZ - 80, w=61, d=61, h=5),
    1: dict(x=BRX - 40, z=BRZ - 80, w=61, d=61, h=7),
    2: dict(x=BRX + 40, z=BRZ - 80, w=52, d=52, h=4),
    3: dict(x=BRX - 120, z=BRZ + 10, w=61, d=61, h=5),
    4: dict(x=BRX - 40, z=BRZ + 10, w=61, d=61, h=4),
    5: dict(x=BRX + 40, z=BRZ + 10, w=35, d=35, h=12, r=17),
}


def _bereich():
    x0 = min(g["x"] for g in LEVEL.values()) - 4
    z0 = min(g["z"] for g in LEVEL.values()) - 4
    x1 = max(g["x"] + g["w"] for g in LEVEL.values()) + 4
    z1 = max(g["z"] + g["d"] for g in LEVEL.values()) + 4
    return "x=%d,y=%d,z=%d,dx=%d,dy=%d,dz=%d" % (x0, B - 4, z0, x1 - x0, 22, z1 - z0)


# Zielauswahl-Bereich, der alle Backrooms einschliesst (fuer @a[...] / @e[...])
BEREICH = _bereich()
