# Waffenpack + Backrooms für Eaglercraft 1.12

Pistole, Bazooka, Schwert, Taschenlampe und Sonder-TNT mit eigenem Design, sehr starke Items und eine Backrooms-Mod mit drei Leveln und dem Warden als Endgegner.
Besteht aus zwei Dateien: einem Ressourcenpaket (Aussehen) und einer fertigen Welt (Items, Waffen, Backrooms).

## Machbarkeit

- **Forge-Mods:** gehen nicht. Eaglercraft läuft als nach JavaScript/WebAssembly übersetztes Programm im Browser und kann keine Java-Mods nachladen.
- **Gewählter Weg: Ressourcenpaket + Welt mit eingebauten Befehlsblöcken.** Das nutzt nur Funktionen, die Minecraft 1.12 selbst mitbringt. Monster, Waffen und Effekte sind daraus zusammengesetzt (siehe „Technische Grenzen“).
- Eine Minecraft-Version „1.12.4“ gibt es nicht; alles ist im Format von Minecraft 1.12.2 gebaut.

## Dateien

| Datei | Zweck |
|---|---|
| `Waffenpack-Ressourcenpaket.zip` | Ressourcenpaket: Texturen und 3D-Modelle für Waffen, Taschenlampe, TNT, Monster und Backrooms |
| `Waffenpack-Welt.zip` | Fertige Welt: Items beim ersten Betreten, Steuerung der Waffen, Backrooms unter dem Spawnpunkt |
| `befehle/einzelbefehle.txt` | Jedes Item als einzelner Chat-Befehl, für andere Welten (Notlösung) |
| `ressourcenpaket/` | Inhalt der Ressourcenpaket-ZIP als Ordner |
| `build.py` | Erzeugt Ressourcenpaket und Befehle neu. Werte der Items stehen oben in der Datei. |
| `grafik.py`, `modelle.py` | Texturen und 3D-Modelle (Monster, Pistole, Bazooka, Taschenlampe, Blöcke) |
| `backrooms.py` | Aufbau der drei Level und der Arena, Spiellogik der Backrooms |
| `welt_bauen.py` | Baut `Waffenpack-Welt.zip` neu (braucht den originalen 1.12.2-Server). |
| `html_einbauen.py` | Baut Ressourcenpaket und Welt in eine eigene Eaglercraft-1.12.2-Offline-HTML-Datei ein. |
| `eaglercraft-daten.json` | Ressourcenpaket und Welt im Speicherformat von Eaglercraft (Eingabe für `html_einbauen.py`). |

## Variante 1: HTML-Datei mit eingebautem Waffenpack

`html_einbauen.py` ergänzt die Datei `Eaglercraft_1.12.2_u3_WASM_Offline.html` um ein Skript. Beim ersten Start legt es Ressourcenpaket und Welt im Browser an und schaltet das Ressourcenpaket ein. Außerdem macht es im Einzelspieler den Chatbefehl **`/start`** verfügbar.

```
python3 html_einbauen.py Eaglercraft_1.12.2_u3_WASM_Offline.html eaglercraft-daten.json Eaglercraft_1.12.2_u3_WASM_Offline_Waffenpack.html
```

Benutzen: die neue HTML-Datei öffnen, **Singleplayer → Waffenpack-Welt-3 → Play Selected World**. Die Items liegen sofort im Inventar. Im Chat `/start` eingeben, um die Backrooms zu betreten.

Ältere Welten („Waffenpack-Welt“, „Waffenpack-Welt-2“) bleiben erhalten. Die HTML-Datei selbst liegt nicht in diesem Repository, weil sie den Programmcode von Eaglercraft/Minecraft enthält.

## Variante 2: Dateien von Hand importieren (Eaglercraft 1.12.2)

1. **Options... → Resource Packs... → Open Resource Pack Folder**, `Waffenpack-Ressourcenpaket.zip` auswählen, links anklicken, **Select this resource pack**, **Done**.
2. **Singleplayer → Create New World → Import Vanilla World**, `Waffenpack-Welt.zip` auswählen, **Continue**.
3. Welt „Waffenpack“ auswählen, **Play Selected World**.

Ohne die HTML-Datei gibt es `/start` nicht. Die Backrooms startet man dann mit:

```
/trigger start set 1
```

## Die Backrooms

**Start:** `/start` (Variante 1) oder `/trigger start set 1`. Man fällt „durch den Boden der Realität“ nach Level 0 und bekommt eine Taschenlampe. `/start` setzt die Backrooms jederzeit komplett zurück (alle Monster neu, wieder ab Level 0).

| Level | Aussehen | Monster | Ausgang |
|---|---|---|---|
| Level 0 – Die gelben Räume | Labyrinth mit gelber Tapete, feuchtem Teppich, Rasterdecke, flackernden Leuchtstoffröhren | 4 Smiler (schwarze Schatten mit leuchtendem Grinsen) in den dunklen Räumen | Grünes Schild „NOTAUSGANG“ in der hintersten Ecke |
| Level 1 – Die Lagerhalle | Betonhalle mit Säulen, Pappkarton-Stapeln, Pfützen, flackerndem Licht | 4 Hounds (kriechen auf allen vieren, schnell) | Aufzugstür „AUFZUG“ an der Südwand |
| Level 2 – Die Rohrtunnel | Enge Wartungstunnel mit rostigen Stahlwänden, Rohren, rotem Notlicht, Dampf | 4 Hautdiebe (große, hautfarbene Gestalten) | „WARTUNGSSCHACHT“ in der hintersten Ecke |
| Level 3 – Deep Dark | Runde Sculk-Arena, Endkampf | Der Warden | Nach dem Sieg öffnet sich in der Mitte der Weg zurück an die Oberfläche |

Die Ausgänge sind schwarze, funkelnde Portalblöcke; man läuft einfach hinein.

**Der Warden** (nach dem echten Warden gestaltet: dunkelgrün-blauer Körper, leuchtender Brustkorb, augenloser Kopf mit großem Maul, zwei Fühler):

- steigt beim Betreten der Arena in 5 Sekunden aus dem Boden,
- 1000 Lebenspunkte, Resistenz (nimmt 80 % weniger Schaden), kein Rückstoß,
- Schallangriff alle 5 Sekunden auf alle Spieler im Umkreis von 16 Blöcken (Vorwarnung: Geräusch und Partikel am Warden eine Sekunde vorher),
- Dunkelheit: alle 15 Sekunden kurz Blindheit in seiner Nähe, dazu ein Herzschlag-Geräusch,
- Nahkampf 16 Schaden, Treffer verursachen Verdorrung,
- **hat 3 Leben:** nach dem ersten und zweiten Tod steigt er erneut auf („ER LEBT NOCH“).

Nach dem Sieg: Titel „GESCHAFFT!“, Feuerwerk, ein Nether-Stern „Herz des Wardens“ und ein Portal in der Arenamitte zurück an die Oberfläche.

**Tipps:**
- Vor dem Start die Rüstung anziehen. Ohne Rüstung tötet der Warden mit zwei Schlägen.
- Wer stirbt, erscheint am Anfang des Levels, in dem er gestorben ist. Das Inventar bleibt erhalten.
- Die Taschenlampe gibt Nachtsicht, solange sie in der Hand ist.

## Inhalt (Items)

| Item | Umsetzung |
|---|---|
| Pistole | Bogen mit eigenem 3D-Modell (schwarze Pistole), unzerbrechlich. Schießt goldene Patronen (Grundschaden 2048) mit Knall, Mündungsfeuer und Funkenspur. |
| Bazooka | Bogen mit eigenem 3D-Modell (olivgrünes Rohr mit Visier und Griff), unzerbrechlich. Schießt eine riesige rot-weiße Rakete mit Feuer- und Rauchspur, die beim Einschlag explodiert. |
| Schwert (eigenes Design) | Diamantschwert mit eigenem Aussehen (rote Klinge, goldener Griff), unzerbrechlich, Angriffsschaden 2048. |
| Taschenlampe | Karottenrute mit eigenem 3D-Modell (schwarzer Griff, Metallkopf, roter Schalter), unzerbrechlich. Nachtsicht, solange sie in der Hand ist. |
| Sonder-TNT | 64 Stück, neu gestaltet (rot-schwarzes Gehäuse mit Warnstreifen, Zünder oben). Funkt nach dem Anzünden; beim Explodieren entstehen vier weitere Explosionen im Abstand von 3 Blöcken. |
| Feuerzeug | Unzerbrechliches Feuerzeug zum Anzünden des TNT. |
| Pfeile | 64 Stück, Munition für Pistole und Bazooka im Überlebensmodus. |
| OP-Goldäpfel | 64 verzauberte goldene Äpfel |
| Enderperlen | 16 (ein voller Stapel) |
| OP-Rüstung | Diamant-Helm, -Brustplatte, -Hose, -Stiefel, jeweils Schutz 1000 |
| Federfall | Federfall 32000 auf den Stiefeln |
| Schwert Stufe 20 | Diamantschwert mit Schärfe 20 (Annahme, siehe unten) |
| Spitzhacke | Diamantspitzhacke, nur Effizienz 32767 |

Die Welt startet im Überlebensmodus, Cheats sind an. Kreativmodus: `/gamemode 1`, zurück: `/gamemode 0`.

**Items noch einmal bekommen:** `/scoreboard players tag @p remove wp_hat`

## Getestet

- **Originaler Minecraft-1.12.2-Client mit Server:** alle drei Level und die Arena; Übergänge durch die Ausgänge; Monster sichtbar und greifen an; Warden steigt auf, Schallangriff, Blindheit, 3 Leben (mit der Pistole erschossen), Sieg mit Feuerwerk und Rückweg an die Oberfläche; Kampf mit angelegter Rüstung überlebbar; Taschenlampe; Sonder-TNT löst Kettenexplosion aus; normale Monster (Zombies, Creeper usw.) entstehen nicht in den Backrooms.
- **Eaglercraft 1.12.2 (u3), WASM-Offline-HTML aus Variante 1:** neues Browser-Profil und Profil mit der vorigen Version; `/start` im Chat führt nach Level 0; Ausgang von Level 0 nach Level 1; Arena mit Warden (über ein Test-Portal erreicht); Taschenlampe; 3D-Modelle von Pistole und Taschenlampe in der Hand.
- **Nicht in Eaglercraft geprüft:** den kompletten Weg durch Level 1 und 2 zu Fuß und den Warden-Kampf bis zum Sieg. Beides läuft über dieselben Befehle und Portale, die in Eaglercraft getestet sind.

## Getroffene Entscheidungen zu den offenen Punkten

Du wolltest keine Rückfragen. Deshalb habe ich so entschieden; alles lässt sich in `build.py` bzw. `backrooms.py` ändern (danach `python3 build.py` und `python3 welt_bauen.py <server.jar>` ausführen):

1. **Backrooms-Level:** Level 0, 1 und 2 nach den bekannten Backrooms-Beschreibungen, dazu die Warden-Arena als Level 3.
2. **Monster:** Smiler (Level 0), Hounds (Level 1), Hautdiebe (Level 2), Warden (Endgegner). Alle mit eigenem 3D-Modell.
3. **Sonder-TNT:** als Kettenexplosion umgesetzt (jede Explosion löst vier weitere aus).
4. **„Anstarr“ Stufe 20:** Das Wort passt zu keiner Verzauberung. Ich habe **Schärfe 20** auf einem normalen Diamantschwert angenommen – bitte prüfen und ggf. in `build.py` (`SCHWERT_STUFE20_VERZAUBERUNG`) ändern.
5. **2 Milliarden Schaden:** für alle drei Waffen so hoch wie technisch möglich (siehe Grenzen).
6. **Enderperlen:** 16. **Rüstung:** alle vier Teile aus Diamant, Schutz 1000. **Federfall:** auf den Stiefeln.

## Technische Grenzen (Minecraft 1.12)

- **Schaden 2 Milliarden geht nicht.** Der Angriffsschaden ist auf 2048 begrenzt. **Effizienz 727.000 geht nicht**, Verzauberungsstufen sind auf 32767 begrenzt. **Schutz 1000 und Federfall 32000** werden gespeichert, das Spiel verringert Schaden durch Verzauberungen aber höchstens um 80 %.
- **Monster:** Ohne Mod kann man keine neuen Lebewesen hinzufügen. Jedes Monster ist ein unsichtbarer Zombie (der Warden ein unsichtbares Wither-Skelett, wegen der größeren Trefferfläche), der sein 3D-Modell als „Hut“ trägt. Die Modelle wechseln alle 0,4 Sekunden zwischen zwei Haltungen, Beine bewegen sich nicht einzeln. Die Trefferfläche ist kleiner als das Modell: auf den Körper zielen, nicht auf den Kopf.
- **Warden-Geräusche:** Minecraft 1.12 hat keine Warden-Geräusche. Verwendet werden passende vorhandene Geräusche (Elder Guardian, Wither, Herzschlag).
- **Umgestaltete Blöcke gelten überall.** Für die Backrooms bekommen seltene Blöcke ein neues Aussehen, auch außerhalb der Backrooms: Schwamm (Tapete), gefärbtes Glas braun/grau/schwarz/hellgrau/türkis (Teppich, Betonboden, Gitter, Pappkarton, Sculk), Beton weiß/grau/hellgrau/türkis/orange/schwarz/hellblau/blau (Decke, Wände, Rohre, Sculk), Seelaterne (flackernde Deckenlampe), Leuchtstein (Sculk-Leuchten), TNT.
- **Unter dem Spawnpunkt** liegen die Backrooms (Höhe 21–36) und 5 Reihen mit 253 Befehlsblöcken (Höhe 10). Dort nicht graben.
- **Sonder-TNT:** gilt für jedes gezündete TNT in dieser Welt, auch für normales.
- **Kreativ-Inventar:** Eigene Items können ohne Mod nicht in die Kreativ-Reiter eingetragen werden.
- **Rakete:** Technisch fliegt unsichtbar ein Pfeil, ein unsichtbarer Rüstungsständer mit dem Raketenmodell wird jeden Tick zu ihm versetzt. Die Neigung der Rakete wird beim Abschuss in 7 Stufen gewählt.
- **Patronen-Aussehen gilt für alle Pfeile**, auch für Pfeile von Skeletten.
- **Geschosse verschwinden nach 8 Sekunden Flug.** In Eaglercraft bewegen sich Objekte am Rand der Sichtweite nicht weiter.
- **`/tp` auf Spieler** bringt Eaglercraft 1.12 (u3) zum Absturz. Deshalb laufen alle Wechsel zwischen den Leveln über End-Portal-Blöcke.
