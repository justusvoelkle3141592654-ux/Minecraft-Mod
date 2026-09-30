# Waffenpack für Eaglercraft 1.12

Pistole, Bazooka, Schwert mit eigenem Design und sehr starke Items.
Besteht aus einem Ressourcenpaket (Aussehen) und Befehlen (Items und Funktion).

## Machbarkeit

- **Forge-Mods:** gehen nicht. Eaglercraft läuft als nach JavaScript übersetztes Programm im Browser und kann keine Java-Mods nachladen.
- **Eigener Client-Build:** wäre möglich, ist aber ein großes Projekt und hier nicht umgesetzt.
- **Gewählter Weg: Ressourcenpaket + Befehle.** Das nutzt nur Funktionen, die Minecraft 1.12 selbst mitbringt.

Wichtig:

- Eine Minecraft-Version „1.12.4“ gibt es nicht (1.12 endet bei 1.12.2). Alles ist im Format von Minecraft 1.12.2 gebaut.
- Getestet wurde auf einem originalen Minecraft-1.12.2-Server mit einem Testspieler: alle Items, Pistole, Bazooka, Schwert und der Befehlsblock-Installer funktionieren dort.
- **In Eaglercraft selbst konnte ich nicht testen**, und auch das Ressourcenpaket (Aussehen) ist nicht im Spiel geprüft. Wenn der Eaglercraft-Client sich wie Minecraft 1.12.2 verhält, sollte alles gleich funktionieren.

## Dateien

| Datei | Zweck |
|---|---|
| `Waffenpack-Ressourcenpaket.zip` | Ressourcenpaket: Texturen und Modelle für Pistole, Bazooka, Schwert |
| `befehle/installer-befehlsblock.txt` | Ein Befehl für einen Befehlsblock: gibt alle Items und aktiviert Pistole/Bazooka (Weg A) |
| `welt/data/functions/waffenpack/` | Dieselbe Funktion als Weltdateien, Start mit `/function waffenpack:start` (Weg B) |
| `befehle/einzelbefehle.txt` | Jedes Item als einzelner Chat-Befehl (Weg C) |
| `ressourcenpaket/` | Inhalt der ZIP-Datei als Ordner |
| `build.py` | Erzeugt alle Dateien neu (`python3 build.py`). Alle Werte stehen oben in der Datei. |

## Anleitung

### 1. Ressourcenpaket aktivieren

1. In Eaglercraft: **Optionen → Ressourcenpakete**.
2. `Waffenpack-Ressourcenpaket.zip` hinzufügen und aktivieren. (Der genaue Name des Buttons kann je nach Eaglercraft-Version abweichen.)

Ohne Ressourcenpaket funktionieren die Waffen trotzdem, sehen aber aus wie Bogen und Diamantschwert.

### 2. Welt vorbereiten

1. Neue Einzelspielerwelt erstellen, dabei **Cheats erlauben: AN**.
2. In der Welt `/gamemode 1` eingeben (Kreativmodus, nötig zum Bearbeiten von Befehlsblöcken).

### 3. Items bekommen – Weg A (empfohlen): Befehlsblock

1. Am Spawnpunkt (dort, wo man zuerst erscheint) auf freier, ebener Fläche stehen.
2. `/give @p command_block` eingeben und den Befehlsblock auf den Boden setzen.
3. Rechtsklick auf den Befehlsblock. Den kompletten Inhalt von `befehle/installer-befehlsblock.txt` einfügen (Strg+V) und **Fertig** klicken.
4. Einen Knopf an den Befehlsblock setzen und drücken.

Danach sind alle Items im Inventar. Rechts daneben (Richtung Osten) entsteht eine Reihe aus 12 Befehlsblöcken; sie steuert Pistole und Bazooka und darf nicht abgebaut werden. Erneutes Drücken des Knopfes gibt alle Items noch einmal.

Für den Überlebensmodus danach `/gamemode 0` eingeben.

Hinweise:
- Der Befehl ist zu lang für den Chat (dort sind höchstens 256 Zeichen erlaubt), deshalb der Befehlsblock.
- Befehlsblöcke laufen nur, solange ihr Gebiet geladen ist. Der Bereich um den Spawnpunkt bleibt in Minecraft 1.12 immer geladen, deshalb dort bauen.
- Falls der Client kein Einfügen mit Strg+V unterstützt, geht dieser Weg nicht. Dann Weg C.

### 3. Items bekommen – Weg B: Funktion (nur mit Weltimport)

Nur möglich, wenn dein Eaglercraft-Client Welten als ZIP exportieren und wieder importieren kann:

1. Welt exportieren und entpacken.
2. Den Ordner `welt/data/functions` in den Ordner `data` der Welt kopieren (Ergebnis: `<Welt>/data/functions/waffenpack/start.mcfunction`).
3. Welt wieder packen und importieren.
4. In der Welt eingeben: `/function waffenpack:start`

### 3. Items bekommen – Weg C: Einzelbefehle

Jede Zeile aus `befehle/einzelbefehle.txt` in den Chat eingeben. Alle Items kommen so ins Inventar, **aber Pistole und Bazooka verhalten sich dann wie normale Bögen** (kein erhöhter Schaden, keine Explosion).

## Inhalt

| Item | Umsetzung |
|---|---|
| Pistole | Bogen mit eigenem Aussehen, unzerbrechlich. Pfeile bekommen Grundschaden 2048. |
| Bazooka | Bogen mit eigenem Aussehen, unzerbrechlich. Pfeile bekommen Grundschaden 2048 und explodieren beim Einschlag in einen Block (wie TNT). |
| Schwert (eigenes Design) | Diamantschwert mit eigenem Aussehen (rote Klinge, goldener Griff), unzerbrechlich, Angriffsschaden 2048. |
| Pfeile | 64 Stück, Munition für Pistole und Bazooka im Überlebensmodus. |
| OP-Goldäpfel | 64 verzauberte goldene Äpfel |
| Enderperlen | 16 (ein voller Stapel) |
| OP-Rüstung | Diamant-Helm, -Brustplatte, -Hose, -Stiefel, jeweils Schutz 1000 |
| Federfall | Federfall 32000 auf den Stiefeln |
| Schwert Stufe 20 | Diamantschwert mit Schärfe 20 (Annahme, siehe unten) |
| Spitzhacke | Diamantspitzhacke, nur Effizienz 32767 |

Pistole und Bazooka werden wie ein Bogen benutzt: rechte Maustaste halten, loslassen.

## Getroffene Entscheidungen zu den offenen Punkten

Du wolltest keine Rückfragen. Deshalb habe ich so entschieden; alles lässt sich in `build.py` ändern:

1. **Anzahl der Items:** alle sechs genannten Items sind enthalten.
2. **2 Milliarden Schaden:** für alle drei Waffen, so hoch wie technisch möglich (siehe Grenzen).
3. **Pistole und Bazooka:** als Bogen umgesetzt, Munition sind normale Pfeile, kein eigenes Nachladen. Die Bazooka explodiert beim Einschlag.
4. **Enderperlen:** 16.
5. **Rüstung:** alle vier Teile aus Diamant, jeweils Schutz 1000.
6. **Federfall:** auf den Stiefeln.
7. **„Anstarr“ Stufe 20:** Das Wort passt zu keiner Verzauberung. Ich habe **Schärfe 20** auf einem normalen Diamantschwert angenommen. Das ist geraten – bitte prüfen und ggf. in `build.py` (`SCHWERT_STUFE20_VERZAUBERUNG`) ändern.
8. **„Nur Effizienz“:** Die Spitzhacke hat nur Effizienz. Kein Item bekommt Verzauberungen außer den oben genannten (kein Glück, keine Haltbarkeit usw.).
9. **Auslöser:** Weg A: Knopf am Befehlsblock. Weg B: `/function waffenpack:start`.
10. **Anleitung:** verstanden als Schritt-für-Schritt-Anleitung zum Aktivieren – das ist diese Datei.
11. **Design des Schwerts:** schlicht, rote Klinge mit dunkelrotem Rand, goldener Griff.

## Technische Grenzen (Minecraft 1.12)

- **Schaden 2 Milliarden geht nicht.** Der Angriffsschaden ist auf 2048 begrenzt. Das reicht, um jedes Monster mit einem Schlag zu töten (Enderdrache: 200 Lebenspunkte).
- **Effizienz 727.000 geht nicht.** Verzauberungsstufen sind auf 32767 begrenzt. Größere Werte übernimmt das Spiel nicht korrekt, deshalb 32767. Blöcke werden damit sofort abgebaut.
- **Schutz 1000 und Federfall 32000** werden gespeichert, das Spiel verringert Schaden durch Verzauberungen aber höchstens um 80 %. Fallschaden und anderer Schaden sind also nicht vollständig aufgehoben.
- **Kreativ-Inventar:** Eigene Items können ohne Mod nicht in die Kreativ-Reiter eingetragen werden. Sie kommen nur über die Befehle ins Inventar.
- **Bazooka:** explodiert nur bei Einschlag in einen Block. Trifft der Pfeil ein Lebewesen, macht er nur den (hohen) Pfeilschaden.
- **Pistole/Bazooka:** Pfeile werden erkannt, wenn sie in bis zu 6 Blöcken Abstand zum Spieler mit der Waffe in der Hand fliegen. Andere Pfeile in dieser Nähe (z. B. von Skeletten) können ebenfalls verstärkt werden.
