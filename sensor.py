"""Steam Achievement Sensor für Home Assistant.

Prüft ob heute bereits ein Achievement auf Steam freigeschaltet wurde.
Konfiguration erfolgt über die GUI (Config Flow).
"""
from __future__ import annotations

import logging
from datetime import datetime, timedelta
from typing import Any

import requests

from homeassistant.components.sensor import SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_API_KEY
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.util import dt as dt_util

from .const import (
    CONF_APP_ID,
    CONF_STEAM_ID,
    STEAM_ACHIEVEMENTS_URL,
    STEAM_RECENTLY_PLAYED_URL,
)

_LOGGER = logging.getLogger(__name__)

SCAN_INTERVAL = timedelta(minutes=15)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Integration über Config Entry einrichten."""
    api_key = entry.data[CONF_API_KEY]
    steam_id = entry.data[CONF_STEAM_ID]
    app_id = entry.data.get(CONF_APP_ID)

    async_add_entities(
        [SteamAchievementSensor(entry.title, api_key, steam_id, app_id)],
        update_before_add=True,
    )


class SteamAchievementSensor(SensorEntity):
    """Sensor der prüft ob heute ein Steam Achievement errungen wurde."""

    def __init__(
        self,
        name: str,
        api_key: str,
        steam_id: str,
        app_id: str | None,
    ) -> None:
        self._attr_name = name
        self._api_key = api_key
        self._steam_id = steam_id
        self._app_id = app_id
        self._attr_unique_id = f"steam_achievement_{steam_id}"
        self._state: str = "unknown"
        self._extra_attrs: dict[str, Any] = {}

    @property
    def state(self) -> str:
        return self._state

    @property
    def icon(self) -> str:
        return "mdi:trophy" if self._state == "true" else "mdi:trophy-outline"

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        return self._extra_attrs

    def update(self) -> None:
        """Daten von der Steam API abrufen und auswerten."""
        try:
            today_achievements = self._fetch_todays_achievements()

            if today_achievements:
                self._state = "true"
                self._extra_attrs = {
                    "achievements_today": len(today_achievements),
                    "achievement_list": today_achievements,
                    "last_updated": datetime.now().isoformat(),
                }
            else:
                self._state = "false"
                self._extra_attrs = {
                    "achievements_today": 0,
                    "achievement_list": [],
                    "last_updated": datetime.now().isoformat(),
                }

        except requests.exceptions.RequestException as err:
            _LOGGER.error("Fehler beim Abrufen der Steam-Daten: %s", err)
            self._state = "unavailable"

    def _fetch_todays_achievements(self) -> list[dict]:
        """Alle heute freigeschalteten Achievements holen."""
        now_local = dt_util.now()
        today_start = now_local.replace(hour=0, minute=0, second=0, microsecond=0)
        today_start_utc = int(today_start.timestamp())

        app_ids_to_check = (
            [self._app_id]
            if self._app_id
            else self._get_recently_played_app_ids()
        )

        todays_achievements: list[dict] = []
        for app_id in app_ids_to_check:
            for ach in self._get_achievements_for_app(app_id):
                if ach.get("achieved") == 1:
                    unlock_time = ach.get("unlocktime", 0)
                    if unlock_time >= today_start_utc:
                        todays_achievements.append(
                            {
                                "game_id": app_id,
                                "name": ach.get("apiname", ""),
                                "unlock_time": datetime.fromtimestamp(
                                    unlock_time
                                ).strftime("%H:%M"),
                            }
                        )
        return todays_achievements

    def _get_recently_played_app_ids(self) -> list[str]:
        """Liste der kürzlich gespielten App-IDs holen."""
        try:
            resp = requests.get(
                STEAM_RECENTLY_PLAYED_URL,
                params={"key": self._api_key, "steamid": self._steam_id, "count": 10},
                timeout=10,
            )
            resp.raise_for_status()
            games = resp.json().get("response", {}).get("games", [])
            return [str(g["appid"]) for g in games]
        except Exception as err:
            _LOGGER.warning(
                "Kürzlich gespielte Spiele konnten nicht geladen werden: %s", err
            )
            return []

    def _get_achievements_for_app(self, app_id: str) -> list[dict]:
        """Achievements für ein bestimmtes Spiel holen."""
        try:
            resp = requests.get(
                STEAM_ACHIEVEMENTS_URL,
                params={
                    "key": self._api_key,
                    "steamid": self._steam_id,
                    "appid": app_id,
                    "l": "german",
                },
                timeout=10,
            )
            resp.raise_for_status()
            return resp.json().get("playerstats", {}).get("achievements", [])
        except requests.exceptions.HTTPError as err:
            if err.response is not None and err.response.status_code == 400:
                return []
            _LOGGER.debug("Achievements für App %s nicht abrufbar: %s", app_id, err)
            return []
        except Exception as err:
            _LOGGER.debug("Achievements für App %s nicht abrufbar: %s", app_id, err)
            return []
