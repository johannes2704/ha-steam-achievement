"""Config Flow für den Steam Achievement Sensor."""

from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.const import CONF_API_KEY, CONF_NAME
from homeassistant.core import callback
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .api import (
    SteamClient,
    SteamConnectionError,
    SteamInvalidIdError,
    SteamInvalidKeyError,
)
from .const import CONF_APP_ID, CONF_STEAM_ID, DOMAIN

_LOGGER = logging.getLogger(__name__)

DEFAULT_NAME = "Steam Achievement Heute"


async def _validate(hass, api_key: str, steam_id: str) -> str | None:
    """Fehlercode zurückgeben oder None bei Erfolg."""
    client = SteamClient(async_get_clientsession(hass), api_key, steam_id)
    try:
        profile = await client.get_profile()
    except SteamInvalidKeyError:
        return "invalid_api_key"
    except SteamInvalidIdError:
        return "invalid_steam_id"
    except SteamConnectionError:
        return "cannot_connect"
    # communityvisibilitystate: 3 = öffentlich
    if profile.get("communityvisibilitystate") != 3:
        return "profile_private"
    return None


class SteamAchievementConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """GUI-Einrichtung."""

    VERSION = 1

    async def async_step_user(self, user_input: dict[str, Any] | None = None):
        errors: dict[str, str] = {}

        if user_input is not None:
            api_key = user_input[CONF_API_KEY].strip()
            steam_id = user_input[CONF_STEAM_ID].strip()
            app_id = (user_input.get(CONF_APP_ID) or "").strip() or None
            name = (user_input.get(CONF_NAME) or DEFAULT_NAME).strip()

            await self.async_set_unique_id(steam_id)
            self._abort_if_unique_id_configured()

            error = await _validate(self.hass, api_key, steam_id)
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

        schema = vol.Schema(
            {
                vol.Required(CONF_API_KEY): str,
                vol.Required(CONF_STEAM_ID): str,
                vol.Optional(CONF_APP_ID, default=""): str,
                vol.Optional(CONF_NAME, default=DEFAULT_NAME): str,
            }
        )
        return self.async_show_form(step_id="user", data_schema=schema, errors=errors)

    @staticmethod
    @callback
    def async_get_options_flow(config_entry: config_entries.ConfigEntry):
        return SteamAchievementOptionsFlow(config_entry)


class SteamAchievementOptionsFlow(config_entries.OptionsFlow):
    """Nachträgliche Änderungen (löst automatisch ein Neuladen aus)."""

    def __init__(self, config_entry: config_entries.ConfigEntry) -> None:
        # bewusst nicht self.config_entry setzen (in neuen HA-Versionen schreibgeschützt)
        self._entry = config_entry

    async def async_step_init(self, user_input: dict[str, Any] | None = None):
        errors: dict[str, str] = {}

        if user_input is not None:
            api_key = user_input[CONF_API_KEY].strip()
            steam_id = user_input[CONF_STEAM_ID].strip()
            app_id = (user_input.get(CONF_APP_ID) or "").strip() or None

            error = await _validate(self.hass, api_key, steam_id)
            if error:
                errors["base"] = error
            else:
                self.hass.config_entries.async_update_entry(
                    self._entry,
                    data={
                        **self._entry.data,
                        CONF_API_KEY: api_key,
                        CONF_STEAM_ID: steam_id,
                        CONF_APP_ID: app_id,
                    },
                )
                return self.async_create_entry(title="", data={})

        current = self._entry.data
        schema = vol.Schema(
            {
                vol.Required(CONF_API_KEY, default=current.get(CONF_API_KEY, "")): str,
                vol.Required(CONF_STEAM_ID, default=current.get(CONF_STEAM_ID, "")): str,
                vol.Optional(CONF_APP_ID, default=current.get(CONF_APP_ID) or ""): str,
            }
        )
        return self.async_show_form(step_id="init", data_schema=schema, errors=errors)
