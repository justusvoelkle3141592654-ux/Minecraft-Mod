# Waffenpack für Eaglercraft 1.12

Pistole, Bazooka, Schwert mit eigenem Design und sehr starke Items.
Besteht aus zwei Dateien: einem Ressourcenpaket (Aussehen) und einer fertigen Welt (Items und Waffenfunktion).

## Machbarkeit

- **Forge-Mods:** gehen nicht. Eaglercraft läuft als nach JavaScript/WebAssembly übersetztes Programm im Browser und kann keine Java-Mods nachladen.
- **Client-Datei verändern:** nicht nötig. Ressourcenpaket und Welt werden einmal in Eaglercraft importiert und bleiben im Browser gespeichert.
- **Gewählter Weg: Ressourcenpaket + Welt mit eingebauten Befehlsblöcken.** Das nutzt nur Funktionen, die Minecraft 1.12 selbst mitbringt.

Getestet:

- In **Eaglercraft 1.12.2 (u3), WASM-Offline-Version**: Ressourcenpaket importiert und aktiv, Welt importiert, alle Items automatisch im Inventar, eigenes Aussehen der Waffen, Bazooka explodiert, Pistole tötet einen Zombie mit 1000 Lebenspunkten mit einem Schuss.
- Auf einem originalen Minecraft-1.12.2-Server zusätzlich: alle Items mit den richtigen Werten, Schwert tötet denselben Zombie mit einem Schlag, Items erneut holen.
- Eine Minecraft-Version „1.12.4“ gibt es nicht; alles ist im Format von Minecraft 1.12.2 gebaut.

## Dateien

| Datei | Zweck |
|---|---|
| `Waffenpack-Ressourcenpaket.zip` | Ressourcenpaket: Texturen und Modelle für Pistole, Bazooka, Schwert |
| `Waffenpack-Welt.zip` | Fertige Welt: Items beim ersten Betreten, Steuerung für Pistole und Bazooka |
| `befehle/einzelbefehle.txt` | Jedes Item als einzelner Chat-Befehl, für andere Welten (Notlösung) |
| `ressourcenpaket/` | Inhalt der Ressourcenpaket-ZIP als Ordner |
| `build.py` | Erzeugt Ressourcenpaket und Befehle neu. Alle Werte stehen oben in der Datei. |
| `welt_bauen.py` | Baut `Waffenpack-Welt.zip` neu (braucht den originalen 1.12.2-Server). |
| `html_einbauen.py` | Baut Ressourcenpaket und Welt in eine eigene Eaglercraft-1.12.2-Offline-HTML-Datei ein. |
| `eaglercraft-daten.json` | Ressourcenpaket und Welt im Speicherformat von Eaglercraft (Eingabe für `html_einbauen.py`). |

## Variante 1: HTML-Datei mit eingebautem Waffenpack

`html_einbauen.py` ergänzt die Datei `Eaglercraft_1.12.2_u3_WASM_Offline.html` um ein Skript. Beim ersten Start legt es Ressourcenpaket und Welt im Browser an und schaltet das Ressourcenpaket ein, als wären sie von Hand importiert worden. Danach tut es nichts mehr.

```
python3 html_einbauen.py Eaglercraft_1.12.2_u3_WASM_Offline.html eaglercraft-daten.json Eaglercraft_1.12.2_u3_WASM_Offline_Waffenpack.html
```

Benutzen: die neue HTML-Datei öffnen, **Singleplayer → Waffenpack-Welt-2 → Play Selected World**. Die Items liegen sofort im Inventar.

Die HTML-Datei selbst liegt nicht in diesem Repository, weil sie den Programmcode von Eaglercraft/Minecraft enthält.

Getestet in einem leeren Browser-Profil und in einem Profil mit der vorigen Version: Ressourcenpaket aktiv, Welt in der Liste (eine vorhandene „Waffenpack-Welt“ bleibt erhalten), Items beim Betreten im Inventar, eigenes Aussehen der Waffen, Rakete fliegt und explodiert.

Nicht geprüft: ob Pistole und Bazooka auch weit weg vom Spawnpunkt funktionieren. Die Einstellung „Keep spawn chunks loaded“ aus dem Import (Variante 2) lässt sich nicht mit einbauen; Eaglercraft speichert sie nirgends, wo das Skript sie setzen könnte.

## Variante 2: Dateien von Hand importieren (Eaglercraft 1.12.2)

### 1. Ressourcenpaket laden (einmalig)

1. Eaglercraft öffnen.
2. **Options... → Resource Packs...**
3. **Open Resource Pack Folder** klicken und `Waffenpack-Ressourcenpaket.zip` auswählen.
4. Links erscheint „Waffenpack-Ressourcenpaket“. Darauf klicken und **Select this resource pack** wählen.
5. **Done** klicken.

### 2. Welt importieren (einmalig)

1. **Singleplayer → Create New World → Import Vanilla World**.
2. `Waffenpack-Welt.zip` auswählen.
3. **Keep spawn chunks loaded** auf **Yes** stellen (siehe Hinweise unten).
4. **Continue** klicken.

### 3. Spielen

1. Die Welt „Waffenpack-Welt“ auswählen und **Play Selected World** klicken.
2. Alle Items liegen sofort im Inventar.

Die Welt startet im Überlebensmodus, Cheats sind an. Kreativmodus: `/gamemode 1`, zurück: `/gamemode 0`.

**Items noch einmal bekommen:** im Chat eingeben:

```
/scoreboard players tag @p remove wp_hat
```

Hinweise:
- **Unter dem Spawnpunkt** (Höhe 10) liegt eine Reihe aus 62 Befehlsblöcken, eingeschlossen in Stein. Sie steuert alles; dort nicht graben.
- **Keep spawn chunks loaded: Yes** soll den Bereich um den Spawnpunkt geladen halten, damit diese Befehlsblöcke auch weit weg laufen. Geprüft habe ich nur, dass alles in der Nähe des Spawnpunkts funktioniert.
- **Bazooka:** Die Explosion verletzt auch dich. Nicht auf den Boden direkt vor dir schießen.
- Die Items gibt es nur in dieser Welt. Für eine andere Welt: die Befehle aus `befehle/einzelbefehle.txt` einzeln in den Chat eingeben (dann sind Pistole und Bazooka nur normale Bögen).

## Inhalt

| Item | Umsetzung |
|---|---|
| Pistole | Bogen mit eigenem Aussehen, unzerbrechlich. Schießt goldene Patronen (Grundschaden 2048) mit Knall, Mündungsfeuer und Funkenspur; beim Einschlag verschwindet die Kugel in einer Rauchwolke. |
| Bazooka | Bogen mit eigenem Aussehen, unzerbrechlich. Schießt eine riesige rot-weiße Rakete (ca. 5,6 Blöcke lang, mit Flossen und Flamme) mit Feuer- und Rauchspur. Explodiert beim Einschlag in einen Block oder ein Lebewesen. |
| Schwert (eigenes Design) | Diamantschwert mit eigenem Aussehen (rote Klinge, goldener Griff), unzerbrechlich, Angriffsschaden 2048. |
| Pfeile | 64 Stück, Munition für Pistole und Bazooka im Überlebensmodus (sehen als Patronen aus). |
| OP-Goldäpfel | 64 verzauberte goldene Äpfel |
| Enderperlen | 16 (ein voller Stapel) |
| OP-Rüstung | Diamant-Helm, -Brustplatte, -Hose, -Stiefel, jeweils Schutz 1000 |
| Federfall | Federfall 32000 auf den Stiefeln |
| Schwert Stufe 20 | Diamantschwert mit Schärfe 20 (Annahme, siehe unten) |
| Spitzhacke | Diamantspitzhacke, nur Effizienz 32767 |

Pistole und Bazooka werden wie ein Bogen benutzt: rechte Maustaste halten, loslassen.

## Getroffene Entscheidungen zu den offenen Punkten

Du wolltest keine Rückfragen. Deshalb habe ich so entschieden; alles lässt sich in `build.py` ändern (danach `python3 build.py` und `python3 welt_bauen.py <server.jar>` ausführen):

1. **Anzahl der Items:** alle sechs genannten Items sind enthalten.
2. **2 Milliarden Schaden:** für alle drei Waffen, so hoch wie technisch möglich (siehe Grenzen).
3. **Pistole und Bazooka:** als Bogen umgesetzt, Munition sind Pfeile, kein eigenes Nachladen. Pistole: Patronen mit Knall und Funken. Bazooka: eigene riesige Rakete, Explosion beim Einschlag.
4. **Enderperlen:** 16.
5. **Rüstung:** alle vier Teile aus Diamant, jeweils Schutz 1000.
6. **Federfall:** auf den Stiefeln.
7. **„Anstarr“ Stufe 20:** Das Wort passt zu keiner Verzauberung. Ich habe **Schärfe 20** auf einem normalen Diamantschwert angenommen. Das ist geraten – bitte prüfen und ggf. in `build.py` (`SCHWERT_STUFE20_VERZAUBERUNG`) ändern.
8. **„Nur Effizienz“:** Die Spitzhacke hat nur Effizienz. Kein Item bekommt Verzauberungen außer den oben genannten (kein Glück, keine Haltbarkeit usw.).
9. **Auslöser:** Die Items kommen automatisch beim ersten Betreten der Welt; erneut mit `/scoreboard players tag @p remove wp_hat`.
10. **Anleitung:** verstanden als Schritt-für-Schritt-Anleitung zum Aktivieren – das ist diese Datei.
11. **Design des Schwerts:** schlicht, rote Klinge mit dunkelrotem Rand, goldener Griff.

## Technische Grenzen (Minecraft 1.12)

- **Schaden 2 Milliarden geht nicht.** Der Angriffsschaden ist auf 2048 begrenzt. Das reicht, um jedes Monster mit einem Schlag zu töten (Enderdrache: 200 Lebenspunkte).
- **Effizienz 727.000 geht nicht.** Verzauberungsstufen sind auf 32767 begrenzt. Größere Werte übernimmt das Spiel nicht korrekt, deshalb 32767. Blöcke werden damit sofort abgebaut.
- **Schutz 1000 und Federfall 32000** werden gespeichert, das Spiel verringert Schaden durch Verzauberungen aber höchstens um 80 %. Fallschaden und anderer Schaden sind also nicht vollständig aufgehoben.
- **Kreativ-Inventar:** Eigene Items können ohne Mod nicht in die Kreativ-Reiter eingetragen werden. Sie kommen nur über die Welt oder die Befehle ins Inventar.
- **Rakete:** Technisch fliegt unsichtbar ein Pfeil, und ein unsichtbarer Rüstungsständer mit dem Raketenmodell auf dem Kopf wird jeden Tick zu ihm versetzt. Die Neigung der Rakete wird beim Abschuss in 7 Stufen aus der Blickrichtung gewählt und bleibt im Flug gleich.
- **Patronen-Aussehen gilt für alle Pfeile:** Ohne Mod kann ein Ressourcenpaket Pfeile nicht unterscheiden. Auch Pfeile aus normalen Bögen und von Skeletten sehen deshalb wie Patronen aus.
- **Geschosse verschwinden nach 8 Sekunden Flug.** In Eaglercraft bewegen sich Objekte am Rand der Sichtweite nicht weiter; ohne diese Regel blieben Raketen dort in der Luft hängen.
- **Pistole/Bazooka:** Pfeile werden erkannt, wenn sie in bis zu 6 Blöcken Abstand zum Spieler mit der Waffe in der Hand fliegen. Andere Pfeile in dieser Nähe (z. B. von Skeletten) können ebenfalls verstärkt werden.
