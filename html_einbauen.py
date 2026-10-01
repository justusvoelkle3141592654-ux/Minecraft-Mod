#!/usr/bin/env python3
"""Baut Ressourcenpaket und Welt in eine Eaglercraft-1.12.2-Offline-HTML-Datei ein.

Aufruf: python3 html_einbauen.py <Eaglercraft_1.12.2_u3_WASM_Offline.html> <daten.json> <ausgabe.html>

daten.json ist eine Liste [pfad, base64-inhalt] aus der Browser-Datenbank von
Eaglercraft, nachdem Ressourcenpaket und Waffenpack-Welt.zip dort einmal
importiert wurden (Eaglercraft wandelt die Welt beim Import in sein eigenes
Format um).

Die HTML-Datei bekommt ein zusaetzliches Skript. Es laeuft vor dem Spielstart
und legt beim ersten Start Ressourcenpaket und Welt in der Browser-Datenbank an
und schaltet das Ressourcenpaket ein. Danach (Merker im localStorage) nicht mehr.
Die Original-Datei wird nicht veraendert.
"""

import base64
import gzip
import json
import struct
import sys

import welt_bauen

WELT = "Waffenpack-Welt"
PAKET = "Waffenpack-Ressourcenpaket"
DB = "_net_lax1dude_eaglercraft_v1_8_internal_PlatformFilesystem_1_12_2_"
MERKER = "waffenpack_installiert_v1"
ANKER = '<script type="text/javascript">\n"use strict";\n(function(){\n\twindow.eaglercraftXOpts.assetsURI'

SKRIPT = """<script type="text/javascript">
"use strict";
// Waffenpack: legt beim ersten Start Ressourcenpaket und Welt an.
(function(){
	var DATEN = "%(daten)s";
	var DB = "%(db)s", WELT = "%(welt)s", PAKET = "%(paket)s", MERKER = "%(merker)s";
	function req(r) { return new Promise(function(ok, err) { r.onsuccess = function() { ok(r.result); }; r.onerror = function() { err(r.error); }; }); }
	function b64bytes(s) { var b = atob(s), u = new Uint8Array(b.length); for (var i = 0; i < b.length; ++i) u[i] = b.charCodeAt(i); return u; }
	async function installieren() {
		try { if (localStorage.getItem(MERKER)) return; } catch (e) { return; }
		var roh = await new Response(new Blob([b64bytes(DATEN)]).stream().pipeThrough(new DecompressionStream("gzip"))).arrayBuffer();
		var v = new DataView(roh), pos = 0, dateien = [];
		while (pos < roh.byteLength) {
			var pl = v.getUint16(pos); pos += 2;
			var pfad = new TextDecoder().decode(new Uint8Array(roh, pos, pl)); pos += pl;
			var dl = v.getUint32(pos); pos += 4;
			dateien.push({ path: pfad, data: roh.slice(pos, pos + dl) }); pos += dl;
		}
		var open = indexedDB.open(DB, 1);
		open.onupgradeneeded = function() { if (!open.result.objectStoreNames.contains("filesystem")) open.result.createObjectStore("filesystem", { keyPath: ["path"] }); };
		var db = await req(open);
		var st = db.transaction("filesystem", "readonly").objectStore("filesystem");
		var welten = await req(st.get(["worlds_list.txt"]));
		var manifest = await req(st.get(["resourcepacks/manifest.json"]));
		var weltDa = await req(st.get(["eaglercraft/worlds/" + WELT + "/level.dat"]));
		var tx = db.transaction("filesystem", "readwrite"), w = tx.objectStore("filesystem");
		var enc = new TextEncoder(), dec = new TextDecoder();
		for (var i = 0; i < dateien.length; ++i) {
			if (weltDa && dateien[i].path.indexOf("eaglercraft/worlds/") === 0) continue;
			w.put(dateien[i]);
		}
		var liste = welten ? dec.decode(welten.data).split("\\n").filter(function(x) { return x.length > 0; }) : [];
		if (liste.indexOf(WELT) === -1) liste.unshift(WELT);
		w.put({ path: "worlds_list.txt", data: enc.encode(liste.join("\\n")).buffer });
		var m = manifest ? JSON.parse(dec.decode(manifest.data)) : { resourcePacks: [] };
		if (!m.resourcePacks.some(function(p) { return p.folder === PAKET; }))
			m.resourcePacks.push({ timestamp: Date.now(), name: PAKET, folder: PAKET, domains: ["minecraft"] });
		w.put({ path: "resourcepacks/manifest.json", data: enc.encode(JSON.stringify(m)).buffer });
		await new Promise(function(ok, err) { tx.oncomplete = ok; tx.onerror = function() { err(tx.error); }; });
		db.close();
		// Ressourcenpaket in den Optionen einschalten
		var key = "_eaglercraft_1.12.g", text = "";
		try { var alt = localStorage.getItem(key); if (alt) text = dec.decode(b64bytes(alt)); } catch (e) {}
		var zeilen = text.split("\\n").filter(function(x) { return x.length > 0; }), gefunden = false;
		// Ohne diesen Eintrag baut Eaglercraft beim ersten Start die Weltliste neu
		// und traegt dabei falsche Namen ein.
		zeilen = zeilen.filter(function(x) { return x.indexOf("hasWorldListBeenConverted:") !== 0; });
		zeilen.push("hasWorldListBeenConverted:true");
		for (var j = 0; j < zeilen.length; ++j) {
			if (zeilen[j].indexOf("resourcePacks:") === 0) {
				var packs = JSON.parse(zeilen[j].substring(14));
				if (packs.indexOf(PAKET) === -1) packs.push(PAKET);
				zeilen[j] = "resourcePacks:" + JSON.stringify(packs); gefunden = true;
			}
		}
		if (!gefunden) zeilen.push("resourcePacks:" + JSON.stringify([PAKET]));
		var bytes = enc.encode(zeilen.join("\\n") + "\\n"), s = "";
		for (var k = 0; k < bytes.length; ++k) s += String.fromCharCode(bytes[k]);
		localStorage.setItem(key, btoa(s));
		localStorage.setItem(MERKER, "1");
		console.log("Waffenpack: installiert (" + dateien.length + " Dateien)");
	}
	var originalMain = window.main;
	window.main = async function() {
		try { await installieren(); } catch (e) { console.error("Waffenpack: Fehler beim Installieren: " + e); }
		return originalMain.apply(this, arguments);
	};
})();
</script>
"""


def main():
    if len(sys.argv) != 4:
        sys.exit(__doc__)
    html_pfad, daten_pfad, ziel = sys.argv[1:]
    html = open(html_pfad, encoding="utf-8").read()
    if ANKER not in html:
        sys.exit("Unbekannter Aufbau der HTML-Datei (Einfuegestelle nicht gefunden)")

    eintraege = json.load(open(daten_pfad))
    paket = bytearray()
    anzahl = 0
    for pfad, inhalt in eintraege:
        daten = base64.b64decode(inhalt)
        if pfad.startswith("eaglercraft/worlds/"):
            teile = pfad.split("/", 3)
            if teile[3] == "level.dat_old":
                continue
            pfad = "eaglercraft/worlds/%s/%s" % (WELT, teile[3])
            if teile[3] == "level.dat":
                name, wurzel = welt_bauen.lade_nbt_bytes(daten)
                wurzel["Data"][1]["LevelName"] = (8, WELT)
                daten = welt_bauen.nbt_bytes(name, wurzel)
        elif not pfad.startswith("resourcepacks/%s/" % PAKET):
            continue
        p = pfad.encode("utf-8")
        paket += struct.pack(">H", len(p)) + p + struct.pack(">I", len(daten)) + daten
        anzahl += 1
    gz = base64.b64encode(gzip.compress(bytes(paket), 9)).decode("ascii")

    skript = SKRIPT % {"daten": gz, "db": DB, "welt": WELT, "paket": PAKET, "merker": MERKER}
    html = html.replace(ANKER, skript + ANKER, 1)
    with open(ziel, "w", encoding="utf-8", newline="") as f:
        f.write(html)
    print("Fertig: %s (%d Dateien eingebaut, %.1f MB)" % (ziel, anzahl, len(html) / 1e6))


if __name__ == "__main__":
    main()
