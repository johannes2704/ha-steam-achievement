# 🏆 Steam Achievement Sensor – Home Assistant Integration

Eine Custom Integration für [Home Assistant](https://www.home-assistant.io/), die prüft ob du heute bereits ein Steam Achievement freigeschaltet hast.

---

## ✨ Features

- ✅ Erkennt automatisch alle heute freigeschalteten Achievements
- 🎮 Prüft alle kürzlich gespielten Spiele **oder** ein bestimmtes Spiel (per App-ID)
- 🖥️ Vollständige **GUI-Konfiguration** – keine `configuration.yaml` nötig
- 🔄 Aktualisiert sich alle 15 Minuten automatisch
- 🛡️ Live-Validierung von API Key und Steam ID beim Einrichten
- 🇩🇪 Deutsche Benutzeroberfläche

---

## 📋 Voraussetzungen

- Home Assistant (getestet ab Version 2023.x)
- Ein öffentliches Steam-Profil (Achievements müssen in den Datenschutzeinstellungen auf **Öffentlich** stehen)
- [Steam Web API Key](https://steamcommunity.com/dev/apikey) (kostenlos)
- Deine [Steam ID (64-bit)](https://steamid.io)

---

## 📁 Installation

### Manuell

1. Lade dieses Repository als ZIP herunter oder klone es:
   ```bash
   git clone https://github.com/johannes2704/ha-steam-achievement
   ```

2. Kopiere den Ordner `custom_components/steam_achievement/` in dein Home Assistant Konfigurationsverzeichnis:
   ```
   /config/custom_components/steam_achievement/
   ```

3. Starte Home Assistant neu.

### Dateistruktur

```
custom_components/steam_achievement/
├── __init__.py
├── config_flow.py
├── const.py
├── manifest.json
├── sensor.py
├── strings.json
└── translations/
    └── de.json
```

---

## ⚙️ Einrichtung

1. Gehe zu **Einstellungen → Geräte & Dienste**
2. Klicke auf **+ Integration hinzufügen**
3. Suche nach **„Steam Achievement"**
4. Fülle das Formular aus:

| Feld | Beschreibung |
|------|-------------|
| **Steam API Key** | Von [steamcommunity.com/dev/apikey](https://steamcommunity.com/dev/apikey) |
| **Steam ID (64-bit)** | 17-stellige ID, z.B. via [steamid.io](https://steamid.io) ermitteln |
| **App-ID** *(optional)* | Nur ein bestimmtes Spiel prüfen, z.B. `730` für CS2. Leer lassen für alle Spiele. |
| **Name** | Anzeigename des Sensors in Home Assistant |

> 💡 Die Steam App-ID findest du in der URL der Spielseite auf Steam: `store.steampowered.com/app/**730**/Counter_Strike_2`

---

## 📊 Sensor-Daten

### State

| Wert | Bedeutung |
|------|-----------|
| `true` | Heute mindestens 1 Achievement freigeschaltet |
| `false` | Heute noch kein Achievement |
| `unavailable` | Steam API nicht erreichbar |

### Attribute

| Attribut | Typ | Beschreibung |
|----------|-----|-------------|
| `achievements_today` | `int` | Anzahl der heutigen Achievements |
| `achievement_list` | `list` | Liste mit Details zu jedem Achievement |
| `last_updated` | `string` | Zeitstempel der letzten Aktualisierung |

#### Beispiel `achievement_list`:
```json
[
  {
    "game_id": "730",
    "name": "KILL_ENEMY_WITHBOMB",
    "unlock_time": "14:23"
  }
]
```

---

## 🤖 Beispiel-Automation

Benachrichtigung sobald ein Achievement errungen wurde:

```yaml
automation:
  - alias: "Steam Achievement Benachrichtigung"
    trigger:
      - platform: state
        entity_id: sensor.steam_achievement_heute
        to: "true"
    action:
      - service: notify.notify
        data:
          title: "🏆 Steam Achievement!"
          message: >
            Du hast heute {{ state_attr('sensor.steam_achievement_heute', 'achievements_today') }}
            Achievement(s) freigeschaltet!
```

---

## 🃏 Lovelace Dashboard-Karte

```yaml
type: entities
title: Steam Achievements
entities:
  - entity: sensor.steam_achievement_heute
    name: Heute Achievement errungen?
    icon: mdi:trophy
```

Oder als Conditional Card – nur anzeigen wenn ein Achievement da ist:

```yaml
type: conditional
conditions:
  - entity: sensor.steam_achievement_heute
    state: "true"
card:
  type: markdown
  content: >
    ## 🏆 Achievement heute!
    Du hast **{{ state_attr('sensor.steam_achievement_heute', 'achievements_today') }}**
    Achievement(s) freigeschaltet.
```

---

## 🔧 Einstellungen nachträglich ändern

Unter **Einstellungen → Geräte & Dienste → Steam Achievement → Konfigurieren** kannst du API Key, Steam ID und App-ID jederzeit ändern – ohne Neustart.

---

## ❓ Häufige Fehler

| Fehler | Ursache | Lösung |
|--------|---------|--------|
| `invalid_api_key` | API Key falsch oder abgelaufen | Neuen Key unter [steamcommunity.com/dev/apikey](https://steamcommunity.com/dev/apikey) erstellen |
| `invalid_steam_id` | Steam ID falsch | 17-stellige ID64 prüfen via [steamid.io](https://steamid.io) |
| `cannot_connect` | Keine Verbindung zu Steam | Internetverbindung und Steam-Status prüfen |
| Keine Achievements gefunden | Profil nicht öffentlich | Steam-Datenschutzeinstellungen auf **Öffentlich** setzen |

---

## 📜 Lizenz

MIT License – frei verwendbar und anpassbar.

---

## 🙏 Danke

Erstellt mit ❤️ und [Claude](https://claude.ai).
