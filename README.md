# 🏆 Steam Achievement Sensor – Home Assistant Integration

Custom Integration, die prüft, ob du heute bereits ein Steam Achievement freigeschaltet hast.

## Installation

Den Ordner `custom_components/steam_achievement/` aus diesem Repo nach
`/config/custom_components/steam_achievement/` kopieren und Home Assistant neu starten
(oder per HACS als benutzerdefiniertes Repository hinzufügen).

> Wichtig: Die Dateien müssen direkt in `custom_components/steam_achievement/` liegen
> (inkl. Unterordner `translations/`).

## Voraussetzungen

- Steam Web API Key: https://steamcommunity.com/dev/apikey
- Steam ID (64-bit): https://steamid.io
- Steam-Profil **und** „Spieldetails“ müssen auf **Öffentlich** stehen
  (Steam → Profil bearbeiten → Datenschutzeinstellungen). Achievements werden sonst von Steam nicht geliefert.

## Sensor

State: `true` (heute ≥ 1 Achievement), `false` (keins), `unavailable` (Abfrage fehlgeschlagen –
Ursache steht im Home-Assistant-Log unter `steam_achievement`).

Attribute: `achievements_today`, `achievement_list`, `games_checked`, `last_updated`, ggf. `problems`.

Aktualisierung alle 15 Minuten. Änderungen unter *Konfigurieren* laden die Integration automatisch neu.

## Änderungen in 2.1.0

- Fehler werden nicht mehr verschluckt: private Profile / ungültiger Key → Sensor `unavailable` + Logmeldung statt dauerhaft `false`
- Umstellung auf `DataUpdateCoordinator` und `aiohttp`
- Ordnerstruktur und `translations/` korrigiert
- Options-Änderungen wirken sofort (automatischer Reload)
