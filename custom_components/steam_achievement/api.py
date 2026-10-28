"""Schlanker Steam-Web-API-Client (nur aiohttp, keine Home-Assistant-Abhängigkeit)."""

from __future__ import annotations

import asyncio
from typing import Any

import aiohttp

from .const import (
    STEAM_ACHIEVEMENTS_URL,
    STEAM_PLAYER_SUMMARIES_URL,
    STEAM_RECENTLY_PLAYED_URL,
)

TIMEOUT = aiohttp.ClientTimeout(total=20)


class SteamError(Exception):
    """Basisklasse für Steam-API-Fehler."""


class SteamConnectionError(SteamError):
    """Steam ist nicht erreichbar oder liefert einen Serverfehler."""


class SteamInvalidKeyError(SteamError):
    """API Key wurde von Steam abgelehnt."""


class SteamInvalidIdError(SteamError):
    """Zur Steam ID existiert kein Profil."""


class SteamPrivateProfileError(SteamError):
    """Profil bzw. Spieldetails sind nicht öffentlich."""


class SteamNoStatsError(SteamError):
    """Das Spiel hat keine Achievements / Statistiken."""


class SteamClient:
    """Fragt die Steam Web API ab."""

    def __init__(self, session: aiohttp.ClientSession, api_key: str, steam_id: str) -> None:
        self._session = session
        self._api_key = api_key
        self._steam_id = steam_id

    async def _get(self, url: str, params: dict[str, Any]) -> tuple[int, str, Any]:
        """GET-Request; gibt (Status, Text, JSON-oder-None) zurück."""
        params = {"key": self._api_key, "steamid": self._steam_id, **params}
        try:
            async with self._session.get(url, params=params, timeout=TIMEOUT) as resp:
                text = await resp.text()
                status = resp.status
                try:
                    data = await resp.json(content_type=None)
                except (aiohttp.ContentTypeError, ValueError):
                    data = None
        except (aiohttp.ClientError, asyncio.TimeoutError) as err:
            raise SteamConnectionError(str(err)) from err

        if status in (401, 403) and "not public" not in text.lower():
            raise SteamInvalidKeyError(f"HTTP {status}")
        if status >= 500 or status == 429:
            raise SteamConnectionError(f"HTTP {status}")
        return status, text, data

    async def get_profile(self) -> dict[str, Any]:
        """Profil abrufen (prüft API Key und Steam ID)."""
        # GetPlayerSummaries erwartet "steamids" statt "steamid"
        try:
            async with self._session.get(
                STEAM_PLAYER_SUMMARIES_URL,
                params={"key": self._api_key, "steamids": self._steam_id},
                timeout=TIMEOUT,
            ) as resp:
                status = resp.status
                if status in (401, 403):
                    raise SteamInvalidKeyError(f"HTTP {status}")
                if status >= 400:
                    raise SteamConnectionError(f"HTTP {status}")
                data = await resp.json(content_type=None)
        except (aiohttp.ClientError, asyncio.TimeoutError, ValueError) as err:
            raise SteamConnectionError(str(err)) from err

        players = (data or {}).get("response", {}).get("players", [])
        if not players:
            raise SteamInvalidIdError(self._steam_id)
        return players[0]

    async def get_recent_games(self) -> list[dict[str, Any]]:
        """Kürzlich gespielte Spiele (letzte 2 Wochen)."""
        status, _text, data = await self._get(STEAM_RECENTLY_PLAYED_URL, {})
        if status != 200 or not isinstance(data, dict):
            raise SteamConnectionError(f"HTTP {status}")
        response = data.get("response", {})
        # Ist "Spieldetails" privat, liefert Steam ein leeres Objekt ohne total_count.
        if "total_count" not in response and "games" not in response:
            raise SteamPrivateProfileError("Keine Spieldaten – Spieldetails nicht öffentlich?")
        return response.get("games", [])

    async def get_achievements(self, app_id: str) -> list[dict[str, Any]]:
        """Achievements eines Spiels."""
        status, text, data = await self._get(
            STEAM_ACHIEVEMENTS_URL, {"appid": app_id, "l": "german"}
        )
        if status in (401, 403):  # "Profile is not public"
            raise SteamPrivateProfileError(text[:200])
        playerstats = (data or {}).get("playerstats", {}) if isinstance(data, dict) else {}
        if status == 400:
            raise SteamNoStatsError(playerstats.get("error", "Keine Statistiken"))
        if status != 200:
            raise SteamConnectionError(f"HTTP {status}")
        if playerstats.get("success") is False:
            error = str(playerstats.get("error", ""))
            if "not public" in error.lower():
                raise SteamPrivateProfileError(error)
            raise SteamNoStatsError(error)
        return playerstats.get("achievements", [])
