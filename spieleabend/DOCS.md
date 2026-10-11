# Spieleabend

Kartenspiele für mehrere Spieler im Browser. Auf der Startseite wählst du das Spiel:

- **Stapeljagd** (2–6 Spieler): Baut gemeinsam Stapel von 1 bis 12; wer seinen eigenen Stapel
  zuerst los ist, gewinnt.
- **Tiefpunkt** (2–8 Spieler): Jeder hat ein Raster aus 12 Karten; tauschen, aufdecken und am
  Ende möglichst wenige Punkte haben.

## Mitspielen

- **Über Home Assistant:** Spieleabend in der Seitenleiste öffnen.
- **Ohne Home-Assistant-Zugang** (z. B. Familie und Freunde am Handy): im Heimnetz
  `http://<home-assistant-ip>:8098` öffnen. Den Port kannst du im Reiter **Netzwerk** ändern.

Einer erstellt ein Spiel und bekommt einen vierstelligen Code. Die anderen geben ihren Namen ein
und treten mit dem Code bei (offene Spiele stehen auch direkt in der Liste). Der Gastgeber kann
Computer-Spieler hinzufügen, Einstellungen wählen und das Spiel starten.

Lädt jemand die Seite neu oder verliert kurz die Verbindung, kommt er automatisch an seinen
Platz zurück. Verlässt jemand ein laufendes Spiel, spielt ein Computer-Spieler für ihn weiter.
Laufende Spiele werden nicht gespeichert; ein Neustart des Add-ons beendet sie.

## Stapeljagd – Regeln

- 162 Karten: je zwölfmal 1 bis 12 und 18 Joker.
- Jeder hat einen eigenen Stapel (30 Karten, ab 5 Spielern 20; einstellbar). Wer ihn zuerst
  leer spielt, gewinnt.
- Zu Beginn des Zuges wird die Hand auf 5 Karten aufgefüllt.
- In der Mitte liegen 4 Bauflächen: Sie beginnen mit 1 und gehen aufwärts bis 12. Ein Joker
  ersetzt jede Zahl. Volle Stapel (bis 12) kommen weg und werden später neu gemischt.
- Spielen darfst du von der Hand, die oberste Karte deines Stapels und die obersten Karten
  deiner 4 Ablagestapel. Hast du alle Handkarten gespielt, ziehst du 5 neue.
- Der Zug endet, wenn du eine Handkarte auf einen deiner Ablagestapel legst.
- Kann keiner mehr legen, gewinnt, wer die wenigsten Karten auf seinem Stapel hat.

## Tiefpunkt – Regeln

- 150 Karten mit den Werten −2 bis 12. Jeder bekommt 12 verdeckte Karten in 3 Reihen × 4 Spalten
  und deckt zu Beginn 2 davon auf. Wer die höchste Summe aufgedeckt hat, beginnt die erste Runde.
- Im Zug ziehst du entweder vom Stapel oder nimmst die oberste Ablagekarte:
  - **Vom Stapel:** Tausche die Karte gegen eine deiner Karten (offen oder verdeckt) – oder lege
    sie ab und decke dafür eine verdeckte Karte auf.
  - **Von der Ablage:** Du musst sie gegen eine deiner Karten tauschen.
- Drei gleiche offene Karten in einer Spalte werden abgeräumt.
- Hat jemand alle Karten offen, hat jeder andere noch einen Zug. Dann wird abgerechnet. Hat der
  Spieler, der die Runde beendet hat, nicht allein die wenigsten Punkte, zählen seine doppelt
  (nur wenn sie positiv sind). Er beginnt die nächste Runde.
- Erreicht jemand die Zielpunktzahl (100, einstellbar), endet das Spiel. Es gewinnt, wer
  insgesamt die wenigsten Punkte hat.

## Bedienung

Karte oder Stapel antippen, dann das Ziel antippen. Was gerade möglich ist, leuchtet grün.

## Konfiguration

| Option  | Beschreibung         |
| ------- | -------------------- |
| `theme` | `dark` oder `light`. |
