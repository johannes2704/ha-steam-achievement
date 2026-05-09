"""Konstanten für den Steam Achievement Sensor."""

DOMAIN = "steam_achievement"

CONF_STEAM_ID = "steam_id"
CONF_APP_ID = "app_id"

STEAM_RECENTLY_PLAYED_URL = (
    "https://api.steampowered.com/IPlayerService/GetRecentlyPlayedGames/v1/"
)
STEAM_ACHIEVEMENTS_URL = (
    "https://api.steampowered.com/ISteamUserStats/GetPlayerAchievements/v1/"
)
