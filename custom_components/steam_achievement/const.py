"""Konstanten für den Steam Achievement Sensor."""

from datetime import timedelta

DOMAIN = "steam_achievement"

CONF_STEAM_ID = "steam_id"
CONF_APP_ID = "app_id"

SCAN_INTERVAL = timedelta(minutes=15)

STEAM_API = "https://api.steampowered.com"
STEAM_PLAYER_SUMMARIES_URL = f"{STEAM_API}/ISteamUser/GetPlayerSummaries/v2/"
STEAM_RECENTLY_PLAYED_URL = f"{STEAM_API}/IPlayerService/GetRecentlyPlayedGames/v1/"
STEAM_ACHIEVEMENTS_URL = f"{STEAM_API}/ISteamUserStats/GetPlayerAchievements/v0001/"
