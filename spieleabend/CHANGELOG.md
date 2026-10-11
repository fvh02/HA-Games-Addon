# Changelog

## 2.2.1

- Sicherung: Ist kein Zugangscode gesetzt, werden Aufrufe über Cloudflare (Tunnel/Domain)
  abgewiesen. Das Heimnetz und Home Assistant bleiben ohne Code nutzbar.

## 2.2.0

- **Als App installierbar** (Home-Bildschirm auf iPhone und Android): Vollbild, App-Icon,
  Rücksicht auf Notch und Home-Leiste, Hinweis zum Installieren auf der Startseite.
- **Zugangscode** (Option `access_code`) für Mitspieler außerhalb von Home Assistant – nötig,
  wenn die Spiele aus dem Internet erreichbar sind. Anleitung für Cloudflare Tunnel in der Doku.
- **Einladen**-Knopf im Warteraum: teilt einen Link, der den Spielcode schon ausfüllt.
- Schutz für den Betrieb im Internet: Grenzen für Spielräume, Verbindungen und Nachrichten,
  Sperre nach zu vielen falschen Codes.

## 2.1.0

- Neues Spiel **Kritzelpost** (3–10 Spieler): Stille Post mit Stift. Sätze schreiben,
  zeichnen, erraten und am Ende alle Alben gemeinsam aufdecken. Mit Zeichenfläche
  (14 Farben, 4 Stärken, Radierer, Rückgängig), Timer in drei Tempi oder ohne Zeitlimit,
  Computer-Spielern und nachgemalten Zeichnungen beim Aufdecken.

## 2.0.0

- Aus „Stapeljagd“ wird „Spieleabend“: eine Startseite zur Auswahl des Spiels.
- Neues Spiel **Tiefpunkt** (2–8 Spieler) im gleichen Design, mit Computer-Spielern,
  Rundenwertung und Animationen beim Aufdecken, Tauschen und Abräumen von Spalten.
- Neuer Slug: das alte Add-on „Stapeljagd“ bitte deinstallieren.

## 1.2.0

- Neuer Name: Stapeljagd (vorher unter anderem Namen). Die Sonderkarte heißt jetzt Joker.
  Das Add-on hat einen neuen Slug; das alte Add-on bitte deinstallieren.

## 1.1.0

- Neues Design: Glassmorphism über einem bewegten Farbhintergrund, moderne Karten mit
  Verläufen und Glanz.
- Animationen: aufgedeckte Stapelkarten drehen sich um, gespielte Karten fliegen auf die
  Bauflächen, neue Handkarten werden ausgeteilt, fertige Stapel leuchten auf, Konfetti beim Sieg.

## 1.0.0

- Erste Version: Stapeljagd für 2–6 Spieler mit Lobby, Spielcodes, Computer-Spielern und
  Live-Updates; spielbar über die Seitenleiste und im Heimnetz auf Port 8098.
