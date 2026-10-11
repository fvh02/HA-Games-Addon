# Stapeljagd

Das Kartenspiel Stapeljagd für 2 bis 6 Spieler im Browser. Alle Mitspieler sehen jeden Zug sofort.

## Mitspielen

- **Über Home Assistant:** Stapeljagd in der Seitenleiste öffnen.
- **Ohne Home-Assistant-Zugang** (z. B. Familie und Freunde am Handy): im Heimnetz
  `http://<home-assistant-ip>:8098` öffnen. Den Port kannst du im Reiter **Netzwerk** ändern.

Einer erstellt ein Spiel und bekommt einen vierstelligen Code. Die anderen geben ihren Namen ein
und treten mit dem Code bei (offene Spiele stehen auch direkt in der Liste). Der Gastgeber kann
Computer-Spieler hinzufügen, die Stapelgröße wählen und das Spiel starten.

Lädt jemand die Seite neu oder verliert kurz die Verbindung, kommt er automatisch an seinen
Platz zurück. Verlässt jemand ein laufendes Spiel, spielt ein Computer-Spieler für ihn weiter.

## Regeln

- 162 Karten: je zwölfmal 1 bis 12 und 18 Stapeljagd-Joker.
- Jeder hat einen eigenen Stapel (30 Karten, ab 5 Spielern 20; einstellbar). Wer ihn zuerst
  leer spielt, gewinnt.
- Zu Beginn des Zuges wird die Hand auf 5 Karten aufgefüllt.
- In der Mitte liegen 4 Bauflächen: Sie beginnen mit 1 und gehen aufwärts bis 12. Ein Joker
  ersetzt jede Zahl. Volle Stapel (bis 12) kommen weg und werden später neu gemischt.
- Spielen darfst du von der Hand, die oberste Karte deines Stapels und die obersten Karten
  deiner 4 Ablagestapel. Hast du alle Handkarten gespielt, ziehst du 5 neue.
- Der Zug endet, wenn du eine Handkarte auf einen deiner Ablagestapel legst.
- Bedienung: Karte antippen, dann das Ziel antippen. Passende Ziele leuchten grün.

## Konfiguration

| Option  | Beschreibung              |
| ------- | ------------------------- |
| `theme` | `dark` oder `light`.      |
