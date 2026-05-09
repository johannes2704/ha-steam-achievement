"""Config Flow für den Steam Achievement Sensor.

Ermöglicht die Einrichtung über die Home Assistant GUI unter
Einstellungen → Integrationen → Integration hinzufügen.
"""
from __future__ import annotations

import logging
from typing import Any

import requests
import voluptuous as vol

from homeassistant import config_entries
from homeassistant.const import CONF_API_KEY, CONF_NAME
from homeassistant.core import callback
from homeassistant.data_entry_flow import FlowResult

from .const import CONF_APP_ID, CONF_STEAM_ID, DOMAIN, STEAM_RECENTLY_PLAYED_URL

_LOGGER = logging.getLogger(__name__)

DEFAULT_NAME = "Steam Achievement Heute"


def _validate_steam_credentials(api_key: str, steam_id: str) -> str | None:
    """Prüft ob API Key und Steam ID gültig sind.

    Gibt einen Fehlercode zurück oder None bei Erfolg.
    """
    try:
        resp = requests.get(
            STEAM_RECENTLY_PLAYED_URL,
            params={"key": api_key, "steamid": steam_id, "count": 1},
            timeout=10,
        )
        if resp.status_code == 403:
            return "invalid_api_key"
        if resp.status_code == 400:
            return "invalid_steam_id"
        resp.raise_for_status()
        return None
    except requests.exceptions.Timeout:
        return "cannot_connect"
    except requests.exceptions.RequestException:
        return "cannot_connect"


class SteamAchievementConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Führt den Benutzer durch die GUI-Einrichtung."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Schritt 1: API Key, Steam ID und optionale App-ID abfragen."""
        errors: dict[str, str] = {}

        if user_input is not None:
            api_key = user_input[CONF_API_KEY].strip()
            steam_id = user_input[CONF_STEAM_ID].strip()
            app_id = user_input.get(CONF_APP_ID, "").strip() or None
            name = user_input.get(CONF_NAME, DEFAULT_NAME).strip()

            # Eindeutigkeit sicherstellen (keine doppelten Einträge)
            await self.async_set_unique_id(steam_id)
            self._abort_if_unique_id_configured()

            # Zugangsdaten im Hintergrund prüfen
            error = await self.hass.async_add_executor_job(
                _validate_steam_credentials, api_key, steam_id
            )

            if error:
                errors["base"] = error
            else:
                return self.async_create_entry(
                    title=name,
                    data={
                        CONF_API_KEY: api_key,
                        CONF_STEAM_ID: steam_id,
                        CONF_APP_ID: app_id,
                        CONF_NAME: name,
                    },
                )

        # Formular anzeigen
        schema = vol.Schema(
            {
                vol.Required(CONF_API_KEY): str,
                vol.Required(CONF_STEAM_ID): str,
                vol.Optional(CONF_APP_ID, default=""): str,
                vol.Optional(CONF_NAME, default=DEFAULT_NAME): str,
            }
        )

        return self.async_show_form(
            step_id="user",
            data_schema=schema,
            errors=errors,
            description_placeholders={
                "api_key_url": "https://steamcommunity.com/dev/apikey",
                "steam_id_url": "https://steamid.io",
            },
        )

    @staticmethod
    @callback
    def async_get_options_flow(
        config_entry: config_entries.ConfigEntry,
    ) -> SteamAchievementOptionsFlow:
        """Options Flow für nachträgliche Änderungen."""
        return SteamAchievementOptionsFlow(config_entry)


class SteamAchievementOptionsFlow(config_entries.OptionsFlow):
    """Ermöglicht nachträgliche Änderungen über Einstellungen → Integration → Konfigurieren."""

    def __init__(self, config_entry: config_entries.ConfigEntry) -> None:
        self._config_entry = config_entry

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Einstellungen bearbeiten."""
        errors: dict[str, str] = {}

        if user_input is not None:
            api_key = user_input[CONF_API_KEY].strip()
            steam_id = user_input[CONF_STEAM_ID].strip()
            app_id = user_input.get(CONF_APP_ID, "").strip() or None

            error = await self.hass.async_add_executor_job(
                _validate_steam_credentials, api_key, steam_id
            )

            if error:
                errors["base"] = error
            else:
                # Gespeicherte Daten aktualisieren
                self.hass.config_entries.async_update_entry(
                    self._config_entry,
                    data={
                        **self._config_entry.data,
                        CONF_API_KEY: api_key,
                        CONF_STEAM_ID: steam_id,
                        CONF_APP_ID: app_id,
                    },
                )
                return self.async_create_entry(title="", data={})

        current = self._config_entry.data
        schema = vol.Schema(
            {
                vol.Required(CONF_API_KEY, default=current.get(CONF_API_KEY, "")): str,
                vol.Required(
                    CONF_STEAM_ID, default=current.get(CONF_STEAM_ID, "")
                ): str,
                vol.Optional(
                    CONF_APP_ID, default=current.get(CONF_APP_ID) or ""
                ): str,
            }
        )

        return self.async_show_form(
            step_id="init",
            data_schema=schema,
            errors=errors,
        )
