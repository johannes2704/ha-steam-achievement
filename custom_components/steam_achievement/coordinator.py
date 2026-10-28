"""DataUpdateCoordinator für den Steam Achievement Sensor."""

from __future__ import annotations

import asyncio
import logging
from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_API_KEY
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from homeassistant.util import dt as dt_util

from .api import (
    SteamClient,
    SteamConnectionError,
    SteamError,
    SteamInvalidKeyError,
    SteamNoStatsError,
    SteamPrivateProfileError,
)
from .const import CONF_APP_ID, CONF_STEAM_ID, DOMAIN, SCAN_INTERVAL

_LOGGER = logging.getLogger(__name__)


class SteamAchievementCoordinator(DataUpdateCoordinator[dict[str, Any]]):
    """Holt alle heute freigeschalteten Achievements."""

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        super().__init__(
            hass,
            _LOGGER,
            config_entry=entry,
            name=DOMAIN,
            update_interval=SCAN_INTERVAL,
        )
        self._client = SteamClient(
            async_get_clientsession(hass),
            entry.data[CONF_API_KEY],
            entry.data[CONF_STEAM_ID],
        )
        self._app_id: str | None = entry.data.get(CONF_APP_ID) or None

    async def _async_update_data(self) -> dict[str, Any]:
        try:
            if self._app_id:
                games = [{"appid": self._app_id, "name": None}]
            else:
                games = await self._client.get_recent_games()
        except SteamInvalidKeyError as err:
            raise UpdateFailed(
                "Steam hat den API Key abgelehnt – bitte Key in den Optionen prüfen"
            ) from err
        except SteamPrivateProfileError as err:
            raise UpdateFailed(
                "Steam-Profil bzw. 'Spieldetails' sind nicht öffentlich "
                "(Steam → Profil bearbeiten → Datenschutzeinstellungen)"
            ) from err
        except SteamConnectionError as err:
            raise UpdateFailed(f"Steam nicht erreichbar: {err}") from err

        today_start = int(dt_util.start_of_local_day().timestamp())
        semaphore = asyncio.Semaphore(5)
        problems: list[str] = []

        async def fetch(game: dict[str, Any]) -> list[dict[str, Any]]:
            app_id = str(game["appid"])
            async with semaphore:
                try:
                    achievements = await self._client.get_achievements(app_id)
                except SteamNoStatsError:
                    return []  # Spiel ohne Achievements – normal
                except SteamPrivateProfileError:
                    raise
                except SteamError as err:
                    problems.append(f"{app_id}: {err}")
                    return []
            result = []
            for ach in achievements:
                unlock = int(ach.get("unlocktime", 0) or 0)
                if ach.get("achieved") == 1 and unlock >= today_start:
                    local = dt_util.as_local(dt_util.utc_from_timestamp(unlock))
                    result.append(
                        {
                            "game_id": app_id,
                            "game_name": game.get("name"),
                            "name": ach.get("name") or ach.get("apiname", ""),
                            "api_name": ach.get("apiname", ""),
                            "unlock_time": local.strftime("%H:%M"),
                            "_ts": unlock,
                        }
                    )
            return result

        try:
            results = await asyncio.gather(*(fetch(g) for g in games))
        except SteamPrivateProfileError as err:
            raise UpdateFailed(
                "Achievements sind nicht öffentlich "
                "(Steam → Datenschutz → 'Spieldetails' auf Öffentlich)"
            ) from err

        if games and problems and len(problems) == len(games):
            raise UpdateFailed(f"Alle Abfragen fehlgeschlagen: {problems[0]}")
        if problems:
            _LOGGER.warning("Teilweise Fehler bei Steam-Abfrage: %s", problems)

        achievements = sorted(
            (a for r in results for a in r), key=lambda a: a["_ts"]
        )
        for a in achievements:
            a.pop("_ts")

        return {
            "achievements": achievements,
            "games_checked": len(games),
            "problems": problems,
            "last_updated": dt_util.now().isoformat(),
        }
