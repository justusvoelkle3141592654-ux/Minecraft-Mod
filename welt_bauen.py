#!/usr/bin/env python3
"""Baut Waffenpack-Welt.zip: eine Minecraft-1.12.2-Welt mit eingebauter Befehlsblock-Kette.

Aufruf: python3 welt_bauen.py <pfad/zu/minecraft_server.1.12.2.jar>

Die Welt wird mit dem originalen 1.12.2-Server erzeugt. Unter dem Spawnpunkt
(Hoehe 10) entsteht die Kette aus build.kette(): neue Spieler bekommen einmal
alle Items, danach laufen Pistole und Bazooka. Cheats sind eingeschaltet,
Spielmodus Ueberleben.
"""

import gzip
import io
import os
import shutil
import struct
import subprocess
import sys
import tempfile
import threading
import time
import zipfile

import backrooms
import build

WELTNAME = "Waffenpack"
KETTE_Y = 10


# --- NBT (nur was fuer level.dat gebraucht wird) ----------------------------

def _rd(f, t):
    if t == 1: return struct.unpack(">b", f.read(1))[0]
    if t == 2: return struct.unpack(">h", f.read(2))[0]
    if t == 3: return struct.unpack(">i", f.read(4))[0]
    if t == 4: return struct.unpack(">q", f.read(8))[0]
    if t == 5: return struct.unpack(">f", f.read(4))[0]
    if t == 6: return struct.unpack(">d", f.read(8))[0]
    if t == 7: return f.read(struct.unpack(">i", f.read(4))[0])
    if t == 8: return f.read(struct.unpack(">H", f.read(2))[0]).decode("utf-8")
    if t == 9:
        et = f.read(1)[0]
        return et, [_rd(f, et) for _ in range(struct.unpack(">i", f.read(4))[0])]
    if t == 10:
        d = {}
        while True:
            tt = f.read(1)[0]
            if tt == 0:
                return d
            k = f.read(struct.unpack(">H", f.read(2))[0]).decode("utf-8")
            d[k] = (tt, _rd(f, tt))
    if t == 11:
        n = struct.unpack(">i", f.read(4))[0]
        return list(struct.unpack(">%di" % n, f.read(4 * n)))
    if t == 12:
        n = struct.unpack(">i", f.read(4))[0]
        return list(struct.unpack(">%dq" % n, f.read(8 * n)))
    raise ValueError(t)


def _wr(f, t, v):
    if t in (1, 2, 3, 4, 5, 6):
        f.write(struct.pack(">" + "bhiqfd"[t - 1], v))
    elif t == 7:
        f.write(struct.pack(">i", len(v)) + v)
    elif t == 8:
        b = v.encode("utf-8")
        f.write(struct.pack(">H", len(b)) + b)
    elif t == 9:
        et, items = v
        f.write(bytes([et]) + struct.pack(">i", len(items)))
        for i in items:
            _wr(f, et, i)
    elif t == 10:
        for k, (tt, vv) in v.items():
            b = k.encode("utf-8")
            f.write(bytes([tt]) + struct.pack(">H", len(b)) + b)
            _wr(f, tt, vv)
        f.write(b"\x00")
    elif t == 11:
        f.write(struct.pack(">i", len(v)) + struct.pack(">%di" % len(v), *v))
    elif t == 12:
        f.write(struct.pack(">i", len(v)) + struct.pack(">%dq" % len(v), *v))


def lade_nbt_bytes(daten):
    f = io.BytesIO(gzip.decompress(daten))
    t = f.read(1)[0]
    name = f.read(struct.unpack(">H", f.read(2))[0]).decode("utf-8")
    return name, _rd(f, t)


def nbt_bytes(name, wurzel):
    f = io.BytesIO()
    b = name.encode("utf-8")
    f.write(b"\x0a" + struct.pack(">H", len(b)) + b)
    _wr(f, 10, wurzel)
    return gzip.compress(f.getvalue())


def lade_nbt(pfad):
    with open(pfad, "rb") as f:
        return lade_nbt_bytes(f.read())


def speichere_nbt(pfad, name, wurzel):
    with open(pfad, "wb") as f:
        f.write(nbt_bytes(name, wurzel))


# --- Server steuern -----------------------------------------------------------

class Server:
    def __init__(self, jar, ordner):
        self.log = []
        self.p = subprocess.Popen(["java", "-Xmx1G", "-Dfile.encoding=UTF-8", "-Dstdin.encoding=UTF-8",
                                   "-jar", jar, "nogui"], cwd=ordner,
                                  stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                  stderr=subprocess.STDOUT, text=True, encoding="utf-8", bufsize=1)
        threading.Thread(target=self._lesen, daemon=True).start()
        self.warte("Done (")

    def _lesen(self):
        for zeile in self.p.stdout:
            self.log.append(zeile.rstrip())

    def warte(self, text, sekunden=300):
        ende = time.time() + sekunden
        while time.time() < ende:
            if any(text in z for z in self.log):
                return
            time.sleep(0.2)
        raise RuntimeError("Server: '%s' nicht erreicht" % text)

    def befehl(self, cmd, pause=0.05):
        n = len(self.log)
        self.p.stdin.write(cmd + "\n")
        self.p.stdin.flush()
        time.sleep(pause)
        return n

    def stop(self):
        self.befehl("save-all", 2)
        self.befehl("stop")
        self.p.wait(120)


def main():
    if len(sys.argv) != 2:
        sys.exit(__doc__)
    jar = os.path.abspath(sys.argv[1])
    arbeit = tempfile.mkdtemp(prefix="waffenpack-welt-")
    with open(os.path.join(arbeit, "eula.txt"), "w") as f:
        f.write("eula=true\n")
    with open(os.path.join(arbeit, "server.properties"), "w") as f:
        f.write("online-mode=false\nlevel-name=%s\nlevel-type=DEFAULT\nserver-port=25590\n"
                "gamemode=0\nenable-command-block=true\nspawn-protection=0\n" % WELTNAME)
    welt = os.path.join(arbeit, WELTNAME)

    # 1. Welt erzeugen, Spawnpunkt lesen, Oberflaeche am Spawnpunkt suchen (Ziel fuer
    #    den Rueckweg aus den Backrooms). Liegt der Spawnpunkt im Wasser, neue Welt.
    for versuch in range(8):
        s = Server(jar, arbeit)
        s.stop()
        _, wurzel = lade_nbt(os.path.join(welt, "level.dat"))
        daten = wurzel["Data"][1]
        x, z = daten["SpawnX"][1], daten["SpawnZ"][1]
        print("Spawnpunkt:", x, z)
        s = Server(jar, arbeit)
        oben = None
        for y in range(140, 50, -1):
            n = s.befehl("testforblock %d %d %d air" % (x, y, z), 0.15)
            if any("is " in zeile and "expected" in zeile for zeile in s.log[n:]):
                oben = y + 1
                break
        if oben is None:
            sys.exit("Oberflaeche nicht gefunden")
        n = s.befehl("testforblock %d %d %d water" % (x, oben - 1, z), 1)
        if not any("Successfully found" in zeile for zeile in s.log[n:]):
            break
        print("Spawnpunkt im Wasser, neue Welt")
        s.stop()
        shutil.rmtree(welt)
    else:
        sys.exit("Keine Welt mit Spawnpunkt an Land gefunden")
    print("Oberflaeche:", oben)
    geo = backrooms.Geo(x, z, oben)

    # 2. Backrooms bauen
    # logAdminCommands aus: sonst schreibt der Server jede Befehlsblock-Ausgabe ins
    # Protokoll (in Eaglercraft in die Browser-Konsole, das kostet Leistung).
    for cmd in ["gamerule commandBlockOutput false", "gamerule logAdminCommands false", "gamerule keepInventory true",
                "scoreboard objectives add wp_alter dummy"] + backrooms.objectives():
        s.befehl(cmd)
    bau = backrooms.bau_befehle(geo)
    fehler_vorher = len(s.log)
    for cmd in bau:
        s.befehl(cmd, 0)
    s.befehl("say BAU_FERTIG", 0)
    s.warte("BAU_FERTIG", 600)
    fehler = [z for z in s.log[fehler_vorher:] if "outside of the world" in z or "Unknown" in z or "Invalid" in z
              or "Couldn't" in z or "cannot" in z.lower()]
    if fehler:
        print("\n".join(fehler[:10]))
        sys.exit("Fehler beim Bau der Backrooms")

    # 3. Befehlsketten unter dem Spawnpunkt (je Reihe ein Wiederhol-Block, Richtung Osten)
    reihen = [build.kette()] + backrooms.ketten(geo)
    gesamt = 0
    for r, befehle in enumerate(reihen):
        zr = z + 2 * r
        s.befehl("fill %d %d %d %d %d %d stone" % (x - 1, KETTE_Y - 1, zr - 1, x + len(befehle), KETTE_Y + 1, zr + 1), 0.3)
        for i, cmd in enumerate(befehle):
            block = "repeating_command_block" if i == 0 else "chain_command_block"
            s.befehl("setblock %d %d %d %s 5 replace {auto:1b,Command:%s}"
                     % (x + i, KETTE_Y, zr, block, build.nbt_string(cmd)), 0)
        gesamt += len(befehle)
    s.befehl("summon armor_stand %d %d %d {Marker:1b,Invisible:1b,NoGravity:1b,Tags:[br_state]}" % geo.zustand)
    time.sleep(2)
    for r, befehle in enumerate(reihen):
        n = s.befehl("testforblock %d %d %d chain_command_block" % (x + len(befehle) - 1, KETTE_Y, z + 2 * r), 1)
        if not any("Successfully found" in zeile for zeile in s.log[n:]):
            sys.exit("Kette %d wurde nicht vollstaendig gebaut" % r)
    s.stop()

    # 4. level.dat: Cheats an, Ueberleben
    name, wurzel = lade_nbt(os.path.join(welt, "level.dat"))
    daten = wurzel["Data"][1]
    daten["allowCommands"] = (1, 1)
    daten["GameType"] = (3, 0)
    daten["LevelName"] = (8, WELTNAME)
    # Der Server hat beim Start das Ende geladen und den Drachenkampf als beendet
    # gespeichert. Ende-Daten entfernen, damit es wie in einer neuen Welt beim
    # ersten Besuch entsteht (mit Drache).
    daten.pop("DimensionData", None)
    speichere_nbt(os.path.join(welt, "level.dat"), name, wurzel)
    shutil.rmtree(os.path.join(welt, "DIM1"), ignore_errors=True)
    for rest in ("session.lock", "level.dat_old"):
        if os.path.exists(os.path.join(welt, rest)):
            os.remove(os.path.join(welt, rest))

    # 5. Packen
    ziel = os.path.join(build.ROOT, "Waffenpack-Welt.zip")
    with zipfile.ZipFile(ziel, "w", zipfile.ZIP_DEFLATED) as zf:
        for ordner, _, dateien in sorted(os.walk(welt)):
            for d in sorted(dateien):
                voll = os.path.join(ordner, d)
                zf.write(voll, os.path.relpath(voll, arbeit).replace(os.sep, "/"))
    shutil.rmtree(arbeit)
    print("Fertig:", ziel, "(%d Befehlsbloecke in %d Reihen)" % (gesamt, len(reihen)))


if __name__ == "__main__":
    main()
