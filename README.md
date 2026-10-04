# Waffenpack + Backrooms für Eaglercraft 1.12

Sonderwaffen, 10 Sorten Werf-TNT, sehr starke Items und eine Backrooms-Mod mit fünf Leveln und dem Warden als Endgegner.
Besteht aus zwei Dateien: einem Ressourcenpaket (Aussehen) und einer fertigen Welt (Items, Waffen, Backrooms).

## Machbarkeit

- **Forge-Mods:** gehen nicht. Eaglercraft läuft als nach JavaScript/WebAssembly übersetztes Programm im Browser und kann keine Java-Mods nachladen.
- **Gewählter Weg: Ressourcenpaket + Welt mit eingebauten Befehlsblöcken.** Das nutzt nur Funktionen, die Minecraft 1.12 selbst mitbringt. Monster, Waffen und Effekte sind daraus zusammengesetzt (siehe „Technische Grenzen“).
- Eine Minecraft-Version „1.12.4“ gibt es nicht; alles ist im Format von Minecraft 1.12.2 gebaut.

## Dateien

| Datei | Zweck |
|---|---|
| `Waffenpack-Ressourcenpaket.zip` | Ressourcenpaket: Texturen und 3D-Modelle für Waffen, Werf-TNT, Monster und Backrooms |
| `Waffenpack-Welt.zip` | Fertige Welt: Items beim ersten Betreten, Steuerung der Waffen, Backrooms |
| `befehle/einzelbefehle.txt` | Jedes Item als einzelner Chat-Befehl, für andere Welten (Notlösung, ohne Waffen-Wirkung) |
| `ressourcenpaket/` | Inhalt der Ressourcenpaket-ZIP als Ordner |
| `waffen.py` | Items, Werte und die Befehle aller Waffen und Werf-TNTs |
| `backrooms.py`, `orte.py` | Aufbau der fünf Level und des Finales, Spiellogik der Backrooms, ihre Lage |
| `build.py`, `grafik.py`, `modelle.py` | Ressourcenpaket: Texturen und 3D-Modelle |
| `welt_bauen.py` | Baut `Waffenpack-Welt.zip` neu (braucht den originalen 1.12.2-Server). |
| `html_einbauen.py` | Baut Ressourcenpaket und Welt in eine eigene Eaglercraft-1.12.2-Offline-HTML-Datei ein. |
| `eaglercraft-daten.json` | Ressourcenpaket und Welt im Speicherformat von Eaglercraft (Eingabe für `html_einbauen.py`). |

## Variante 1: HTML-Datei mit eingebautem Waffenpack

`html_einbauen.py` ergänzt die Datei `Eaglercraft_1.12.2_u3_WASM_Offline.html` um ein Skript. Beim ersten Start legt es Ressourcenpaket und Welt im Browser an und schaltet das Ressourcenpaket ein. Außerdem macht es im Einzelspieler den Chatbefehl **`/start`** verfügbar.

```
python3 html_einbauen.py Eaglercraft_1.12.2_u3_WASM_Offline.html eaglercraft-daten.json Eaglercraft_1.12.2_u3_WASM_Offline_Waffenpack.html
```

Benutzen: die neue HTML-Datei öffnen, **Singleplayer → Waffenpack-Welt-4 → Play Selected World**. Die Items liegen sofort im Inventar, die Rüstung ist angezogen. Im Chat `/start` eingeben, um die Backrooms zu betreten.

Ältere Welten („Waffenpack-Welt“ bis „Waffenpack-Welt-3“) bleiben erhalten. Die HTML-Datei selbst liegt nicht in diesem Repository, weil sie den Programmcode von Eaglercraft/Minecraft enthält.

## Variante 2: Dateien von Hand importieren (Eaglercraft 1.12.2)

1. **Options... → Resource Packs... → Open Resource Pack Folder**, `Waffenpack-Ressourcenpaket.zip` auswählen, links anklicken, **Select this resource pack**, **Done**.
2. **Singleplayer → Create New World → Import Vanilla World**, `Waffenpack-Welt.zip` auswählen, **Continue**.
3. Welt „Waffenpack“ auswählen, **Play Selected World**.

Ohne die HTML-Datei gibt es `/start` nicht. Die Backrooms startet man dann mit `/trigger start set 1`.

## Waffen

| Waffe | Benutzung | Wirkung |
|---|---|---|
| Pistole | wie ein Bogen | Goldene Patronen (Grundschaden 2048) mit Knall und Funkenspur |
| Bazooka | wie ein Bogen | Riesige rot-weiße Rakete, explodiert beim Einschlag |
| **Minigun** | rechte Maustaste gedrückt halten | etwa 5 Schuss pro Sekunde, jeder Treffer 30 Schaden; sechs Läufe, die sich drehen |
| **Orbital-TNT-Kanone** | Ziel anvisieren, Rechtsklick | Zielstrahl; 2 Sekunden später fallen 13 TNT aus 30 Blöcken Höhe auf das Ziel. Lädt 5 Sekunden nach. |
| **Ultimativer Schatten-Bogen** | wie ein Bogen | Animierter dunkelvioletter Bogen mit leuchtenden Runen. Schattenpfeile (60 Grundschaden) suchen den nächsten Gegner in 7 Blöcken, beim Einschlag Schattenzähne, Verdorrung und Blindheit |
| **Vernichtungs-Bogen** | wie ein Bogen | Beim Einschlag wird alles im Umkreis von 1000 Blöcken ausgelöscht (siehe Vernichtungs-TNT) |
| Schwert | | Rote Klinge, Angriffsschaden 2048 |
| Taschenlampe | in der Hand halten | Nachtsicht |

Minigun und Orbital-Kanone legen ihre Munition (Schneebälle) automatisch in die zweite Hand. Sie ist dort unsichtbar und verschwindet wieder, wenn man die Waffe weglegt. Was vorher in der zweiten Hand lag, bleibt liegen – dann schießt die Waffe nicht, bis die zweite Hand frei ist.

## Werf-TNT (10 Sorten)

Rechtsklick wirft das TNT. Nach jedem Wurf kommt sofort ein neues in die Hand (im Überlebensmodus; unbegrenzt).

| Sorte | Wirkung beim Aufprall |
|---|---|
| Wurf-TNT | Explosion wie normales TNT |
| Mega-TNT | Riesige Explosion (Stärke 10) |
| Cluster-TNT | Explosion, dann fliegen 8 kleine Bomben nach außen |
| Feuer-TNT | Explosion und Feuerregen |
| Blitz-TNT | Fünf Blitze |
| Frost-TNT | Gegner eingefroren (10 Sekunden), Wasser wird Eis, Lava wird Obsidian, Boden wird Packeis |
| Schwerkraft-TNT | Alle Gegner im Umkreis von 10 Blöcken schweben hoch und fallen wieder |
| Meteor-TNT | Ein glühender Meteorit stürzt aus 60 Blöcken Höhe herab, Explosion und Magma-Krater |
| Vernichtungs-TNT | Löscht alles im Umkreis von 1000 Blöcken aus: Monster, Tiere, Dorfbewohner, liegende Items, Boote, Loren, Bilder … – nur Spieler nicht. Danach steht die Anzahl auf dem Bildschirm. |
| Weltlöscher-TNT | Löscht die Welt in einem Bereich von 96 × 96 Blöcken, Schicht für Schicht von oben bis hinunter auf Höhe 13 |

Außerdem gibt es weiterhin das **Sonder-TNT** (Block zum Hinstellen und Anzünden): jede Explosion löst vier weitere aus.

## Die Backrooms

**Start:** `/start` (Variante 1) oder `/trigger start set 1`. Man fällt „durch den Boden der Realität“ und landet in Level 0. `/start` setzt alles zurück und beginnt wieder bei Level 0.

Die Backrooms liegen **nicht mehr in der Erde unter dem Spawnpunkt**, sondern weit weg (bei x = 12000, z = 12000) hoch in der Luft, in geschlossenen Kästen. Man kommt nur über die Portale hinein und weiter. **Drinnen ist man im Abenteuermodus: Wände und Böden lassen sich nicht abbauen, Explosionen machen dort nichts kaputt.** Beim Verlassen schaltet das Spiel wieder auf Überleben.

| Level | Aussehen | Gegner | Ausgang |
|---|---|---|---|
| Level 0 – Die gelben Räume | Großes Labyrinth (61 × 61) mit gelber Tapete, feuchtem Teppich, flackernden Leuchtstoffröhren | 8 Smiler | „NOTAUSGANG“ – Vorsicht: zwei der drei Notausgänge führen zurück an den Anfang |
| Level 1 – Die Lagerhalle | Betonhalle mit 49 Säulen, Pappkartons, Pfützen, flackerndem Licht | 8 Hounds | Der Aufzug fährt erst, wenn alle **3 Notstrom-Hebel** umgelegt sind |
| Level 2 – Die Rohrtunnel | Enges Labyrinth aus rostigen Stahltunneln, rotes Notlicht | 6 Hautdiebe, 2 Smiler | „WARTUNGSSCHACHT“; unterwegs **Dampffallen**, die Schaden machen |
| Level 3 – Das Hotel | Fünf lange Hotelflure mit roter Tapete, Teppich und Wandleuchten, über 100 Zimmer mit Türen | 11 Partygänger (manche warten in Zimmern) | Zimmer 237 ist verschlossen; der **Hauptschalter** liegt in einem der anderen Zimmer. In manchen Zimmern stehen Truhen mit Goldäpfeln und Pfeilen |
| Level 4 – Das Büro | Labyrinth aus Großraumbüros mit Schreibtischen, Röhrenmonitoren, Trennwänden | 6 Facelings, 4 Hounds | Der Wartungsaufzug fährt erst mit allen **4 Sicherungen** |
| Finale – Deep Dark | Runde Sculk-Arena | Der Warden | Nach dem Sieg öffnet sich in der Mitte der Weg nach Hause |

**Mehr und schwerere Gegner:** Alle 10 Sekunden kann im Level, in dem man gerade ist, ein weiteres Monster auftauchen (nicht in der Nähe des Spielers), bis 10 bis 13 Monster im Level sind. Die Monster haben mehr Leben als vorher.

**Der Warden** (nach dem echten Warden gestaltet): steigt in 5 Sekunden aus dem Boden, 1000 Lebenspunkte, Resistenz, Schallangriff alle 5 Sekunden, Dunkelheit-Pulse, **3 Leben**. Nach dem Sieg: Feuerwerk, „Herz des Wardens“ und das Portal nach Hause.

**Tipps:**
- Wer stirbt, erscheint am Anfang des Levels und ist dann 5 Sekunden unverwundbar. Das Inventar bleibt erhalten.
- In den Truhen im Hotel gibt es Nachschub.

## Inhalt (alle Items)

Pistole, Bazooka, Minigun, Orbital-TNT-Kanone, Ultimativer Schatten-Bogen, Vernichtungs-Bogen, Schwert, Taschenlampe, die 10 Werf-TNTs, Sonder-TNT (64), Feuerzeug, Pfeile (64; werden nachgefüllt, wenn sie ausgehen), OP-Goldäpfel (64), Enderperlen (16), OP-Rüstung (angezogen; Schutz 1000, Stiefel mit Federfall 32000), Schwert Stufe 20 (Schärfe 20, Annahme), Spitzhacke (Effizienz 32767).

Die Welt startet im Überlebensmodus, Cheats sind an. Kreativmodus: `/gamemode 1`, zurück: `/gamemode 0`.

**Items noch einmal bekommen:** `/scoreboard players tag @p remove wp_hat`

## Getestet

Siehe Abschnitt am Ende dieser Datei (wird nach jedem Test aktualisiert).

## Getroffene Entscheidungen

Du wolltest keine Rückfragen. Deshalb habe ich so entschieden; alles lässt sich in `waffen.py`, `backrooms.py` und `orte.py` ändern (danach `python3 build.py` und `python3 welt_bauen.py <server.jar>` ausführen):

1. **„Unwerfbares TNT“** habe ich als **werfbares TNT** verstanden (10 Sorten, unbegrenzt).
2. **„Mini-Gang“ / „Orbital-TNT-Gang“** = Minigun und Orbital-TNT-Kanone.
3. **„Bogen und TNT, die alles im Umkreis von 1000 Blöcken auslöschen“:** Vernichtungs-Bogen und Vernichtungs-TNT. Spieler werden nicht getötet, sonst würde man sich selbst auslöschen.
4. **„Welt-Löscher-TNT“:** Eine ganze Welt lässt sich mit Befehlen nicht löschen. Er löscht einen großen Bereich (96 × 96 Blöcke) bis kurz über dem Grundgestein.
5. **5 Level:** Level 0–4, dazu das Finale mit dem Warden.
6. **„Anstarr“ Stufe 20:** Das Wort passt zu keiner Verzauberung. Ich habe **Schärfe 20** angenommen.

## Technische Grenzen (Minecraft 1.12)

- **Schaden 2 Milliarden geht nicht.** Der Angriffsschaden ist auf 2048 begrenzt. **Effizienz 727.000 geht nicht**, Verzauberungsstufen sind auf 32767 begrenzt. **Schutz 1000 und Federfall 32000** werden gespeichert, das Spiel verringert Schaden durch Verzauberungen aber höchstens um 80 %.
- **Monster:** Ohne Mod kann man keine neuen Lebewesen hinzufügen. Jedes Monster ist ein unsichtbarer Zombie (der Warden ein unsichtbares Wither-Skelett), der sein 3D-Modell als „Hut“ trägt. Die Trefferfläche ist kleiner als das Modell: auf den Körper zielen.
- **Vernichtung (1000 Blöcke):** wirkt nur auf das, was gerade geladen ist (in Sichtweite). Weiter entfernte Gebiete sind im Spiel nicht geladen und werden nicht erfasst. Auch eigene Haustiere und Pferde im Bereich werden ausgelöscht.
- **Weltlöscher:** sehr rechenintensiv; das Spiel kann dabei einige Sekunden ruckeln. Wasser und Lava am Rand fließen danach in das Loch.
- **Werf-TNT sind für das Spiel Wurftränke.** Normale Wurftränke haben deshalb ebenfalls das TNT-Aussehen.
- **Schneebälle in der zweiten Hand** sind unsichtbar (das ist die Munition der Minigun).
- **Umgestaltete Blöcke gelten überall.** Für die Backrooms bekommen seltene Blöcke ein neues Aussehen, auch außerhalb der Backrooms: Schwamm, gefärbtes Glas (braun, grau, schwarz, hellgrau, türkis), Beton (weiß, grau, hellgrau, türkis, orange, schwarz, hellblau, blau), Trockenbeton (braun, blau, hellgrau, weiß, schwarz), rote Netherziegel, Netherwarzenblock, Seelaterne, Leuchtstein, TNT.
- **Spielregel mobGriefing** wird von der Welt gesteuert: aus, solange ein Spieler in den Backrooms ist, sonst an.
- **Unter dem Spawnpunkt** (Höhe 9–11) liegen rund 840 Befehlsblöcke, eingeschlossen in Stein. Sie steuern alles; dort nicht graben. Der Weltlöscher lässt diese Höhe aus.
- **`/tp` auf Spieler** bringt Eaglercraft 1.12 (u3) zum Absturz. Deshalb laufen alle Wechsel zwischen den Leveln über End-Portal-Blöcke.
