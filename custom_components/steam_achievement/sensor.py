"""Sensor: Wurde heute ein Steam Achievement freigeschaltet?"""

from __future__ import annotations

from typing import Any

from homeassistant.components.sensor import SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import CONF_STEAM_ID, DOMAIN
from .coordinator import SteamAchievementCoordinator


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Sensor einrichten."""
    coordinator: SteamAchievementCoordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([SteamAchievementSensor(coordinator, entry)])


class SteamAchievementSensor(CoordinatorEntity[SteamAchievementCoordinator], SensorEntity):
    """Zustand "true" wenn heute mindestens ein Achievement freigeschaltet wurde."""

    def __init__(self, coordinator: SteamAchievementCoordinator, entry: ConfigEntry) -> None:
        super().__init__(coordinator)
        self._attr_name = entry.title
        # unverändert zur Vorgängerversion, damit die Entität erhalten bleibt
        self._attr_unique_id = f"steam_achievement_{entry.data[CONF_STEAM_ID]}"

    @property
    def native_value(self) -> str | None:
        if not self.coordinator.data:
            return None
        return "true" if self.coordinator.data["achievements"] else "false"

    @property
    def icon(self) -> str:
        return "mdi:trophy" if self.native_value == "true" else "mdi:trophy-outline"

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        data = self.coordinator.data
        if not data:
            return {}
        attrs: dict[str, Any] = {
            "achievements_today": len(data["achievements"]),
            "achievement_list": data["achievements"],
            "games_checked": data["games_checked"],
            "last_updated": data["last_updated"],
        }
        if data["problems"]:
            attrs["problems"] = data["problems"]
        return attrs
