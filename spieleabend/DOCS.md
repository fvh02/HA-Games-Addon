# Spieleabend

Spiele für mehrere Spieler im Browser. Auf der Startseite wählst du das Spiel:

- **Stapeljagd** (2–6 Spieler): Baut gemeinsam Stapel von 1 bis 12; wer seinen eigenen Stapel
  zuerst los ist, gewinnt.
- **Tiefpunkt** (2–8 Spieler): Jeder hat ein Raster aus 12 Karten; tauschen, aufdecken und am
  Ende möglichst wenige Punkte haben.
- **Kritzelpost** (3–10 Spieler): Stille Post mit Stift – Sätze schreiben, zeichnen, erraten.

## Mitspielen

- **Über Home Assistant:** Spieleabend in der Seitenleiste öffnen.
- **Ohne Home-Assistant-Zugang** (z. B. Familie und Freunde am Handy): im Heimnetz
  `http://<home-assistant-ip>:8098` öffnen. Den Port kannst du im Reiter **Netzwerk** ändern.
- **Von überall über deine Domain**, z. B. `https://spiele.deine-domain.de` – siehe
  [Über das Internet spielen](#über-das-internet-spielen).

Im Warteraum schickt **📨 Einladen** einen Link mit dem Spielcode per WhatsApp, iMessage usw.

Einer erstellt ein Spiel und bekommt einen vierstelligen Code. Die anderen geben ihren Namen ein
und treten mit dem Code bei (offene Spiele stehen auch direkt in der Liste). Der Gastgeber kann
Computer-Spieler hinzufügen, Einstellungen wählen und das Spiel starten.

Lädt jemand die Seite neu oder verliert kurz die Verbindung, kommt er automatisch an seinen
Platz zurück. Verlässt jemand ein laufendes Spiel, spielt ein Computer-Spieler für ihn weiter.
Laufende Spiele werden nicht gespeichert; ein Neustart des Add-ons beendet sie.

## Als App installieren

Spieleabend lässt sich wie eine App auf den Home-Bildschirm legen (Vollbild, eigenes Icon):

- **iPhone/iPad:** Seite in Safari öffnen → Teilen → **Zum Home-Bildschirm**.
- **Android:** Seite in Chrome öffnen → Menü ⋮ → **App installieren**.

Das klappt am besten über die HTTPS-Adresse deiner Domain (siehe unten).

## Über das Internet spielen

Mit einem **Cloudflare Tunnel** erreichen deine Freunde die Spiele unter deiner eigenen Domain –
ohne Portfreigabe im Router, ohne Tailscale, mit HTTPS. Nur die Spiele werden freigegeben, dein
Home Assistant bleibt privat. Voraussetzung: Die Domain wird bei Cloudflare verwaltet
(kostenloser Tarif reicht).

1. **Zugangscode setzen:** Hier unter **Konfiguration** einen **Zugangscode** eintragen (z. B. ein
   Wort, das du deinen Freunden sagst) und das Add-on neu starten. Wer die Spiele nicht über Home
   Assistant öffnet, gibt ihn einmal ein; das Handy merkt ihn sich.
2. **Domain zu Cloudflare:** Auf [dash.cloudflare.com](https://dash.cloudflare.com) **Domain
   hinzufügen**, den Free-Tarif wählen und bei deinem Domain-Anbieter die beiden angezeigten
   Cloudflare-Nameserver eintragen. Warten, bis Cloudflare „Aktiv“ meldet (Minuten bis Stunden).
3. **Tunnel anlegen:** In Cloudflare **Zero Trust → Networks → Tunnels → Create a tunnel →
   Cloudflared**, Namen eingeben (z. B. `homeassistant`). Den angezeigten **Token** (die lange
   Zeichenkette nach `--token`) kopieren.
4. **Tunnel-Add-on installieren:** In Home Assistant das Repository
   `https://github.com/brenner-tobias/ha-addons` hinzufügen und **Cloudflared** installieren.
   In dessen Konfiguration **Optionale Konfigurationsoptionen anzeigen** einschalten, bei
   **Cloudflare Tunnel Token** den Token einfügen (die übrigen Felder leer lassen), speichern
   und starten.
5. **Adresse festlegen:** Zurück bei Cloudflare im Tunnel unter **Public Hostname → Add a public
   hostname**: Subdomain `spiele`, deine Domain, Service **HTTP** und URL
   `<home-assistant-ip>:8098` (z. B. `192.168.178.103:8098`). Speichern.
6. `https://spiele.deine-domain.de` öffnen, Zugangscode eingeben, spielen. Als App installieren
   wie oben beschrieben.

Zusätzlicher Schutz ist eingebaut: begrenzte Anzahl an Spielräumen und Verbindungen, Schutz
gegen Nachrichtenfluten und eine Sperre nach 8 falschen Code-Eingaben (15 Minuten).

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

## Kritzelpost – Regeln

- Jeder schreibt einen lustigen Satz (oder nimmt einen der 💡-Vorschläge).
- Jedes Album wandert weiter: Der Nächste zeichnet den Satz, der Übernächste beschreibt die
  Zeichnung, der Nächste zeichnet die Beschreibung … bis jedes Album bei jedem Spieler war.
- Wer „Fertig“ gedrückt hat, kann bis zum Ende des Schritts noch auf „Bearbeiten“ tippen.
- **Tempo:** Schnell (35 s schreiben / 70 s zeichnen), Normal (50 s / 100 s), Gemütlich
  (70 s / 160 s) oder ohne Zeitlimit. Läuft die Zeit ab, wird abgegeben, was da ist.
- Zum Schluss blättert der Gastgeber alle Alben Schritt für Schritt auf, die Zeichnungen
  werden dabei Strich für Strich nachgemalt.
- Computer-Spieler schreiben Sätze, kritzeln einfache Bilder und raten mit. Wer das Spiel
  verlässt, wird von einem Computer-Spieler ersetzt.
- Zeichnungen gehen beim Neuladen der Seite nicht verloren.

## Bedienung

Kartenspiele: Karte oder Stapel antippen, dann das Ziel antippen. Was gerade möglich ist, leuchtet grün.

## Konfiguration

| Option  | Beschreibung         |
| ------- | -------------------- |
| `theme` | `dark` oder `light`. |
| `access_code` | Code für alle, die nicht über Home Assistant spielen. Leer = kein Code. |
