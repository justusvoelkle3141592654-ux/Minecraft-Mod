#!/usr/bin/env python3
"""Baut das Waffenpack fuer Minecraft Java 26.2.

Aufruf: python3 java26/bauen.py

Erzeugt im Hauptordner:
  Waffenpack-26.2-Datenpaket.zip       Datenpaket (Waffen, Werf-TNT, Backrooms-Dimension)
  Waffenpack-26.2-Ressourcenpaket.zip  Ressourcenpaket (Aussehen)
"""

import json
import os
import sys
import zipfile

HIER = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HIER)
sys.path.insert(0, os.path.dirname(HIER))

import backrooms26  # noqa: E402
import ressourcen   # noqa: E402
import waffen26     # noqa: E402

DATEN_FORMAT = [107, 1]
ROOT = os.path.dirname(HIER)


def schreibe_zip(pfad, dateien):
    with zipfile.ZipFile(pfad, "w", zipfile.ZIP_DEFLATED) as z:
        for name in sorted(dateien):
            info = zipfile.ZipInfo(name, date_time=(2026, 1, 1, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            z.writestr(info, dateien[name])


def datenpaket():
    p = waffen26.Paket()
    waffen26.paket(p)
    teile = backrooms26.paket(p)
    p.f["wp:laden"].append("function br:laden")
    p.f["wp:tick"].append("function br:tick")
    d = dict(p.d)
    d["pack.mcmeta"] = json.dumps({"pack": {
        "description": "Waffenpack + Backrooms (Minecraft 26.2)",
        "min_format": DATEN_FORMAT, "max_format": DATEN_FORMAT[0]}}, indent=1, ensure_ascii=False).encode("utf-8")
    d["data/minecraft/tags/function/load.json"] = json.dumps({"values": ["wp:laden"]}).encode()
    d["data/minecraft/tags/function/tick.json"] = json.dumps({"values": ["wp:tick"]}).encode()
    for name, zeilen in p.f.items():
        ns, pfad = name.split(":", 1)
        d["data/%s/function/%s.mcfunction" % (ns, pfad)] = ("\n".join(zeilen) + "\n").encode("utf-8")
    return d, teile


def main():
    daten, teile = datenpaket()
    schreibe_zip(os.path.join(ROOT, "Waffenpack-26.2-Datenpaket.zip"), daten)
    res = ressourcen.dateien()
    schreibe_zip(os.path.join(ROOT, "Waffenpack-26.2-Ressourcenpaket.zip"), res)
    befehle = sum(v.count(b"\n") for k, v in daten.items() if k.endswith(".mcfunction"))
    print("Datenpaket: %d Dateien, %d Befehle (Bau in %d Teilen)" % (len(daten), befehle, teile))
    print("Ressourcenpaket: %d Dateien" % len(res))


if __name__ == "__main__":
    main()
