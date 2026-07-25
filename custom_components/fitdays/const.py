"""Constants for the Fitdays integration."""

DOMAIN = "fitdays"

# Config entry keys
CONF_TOKEN = "token"
CONF_REFRESH_TOKEN = "refresh_token"
CONF_UID = "uid"
CONF_ACTIVE_SUID = "active_suid"
CONF_EMAIL = "email"
CONF_PASSWORD_HASH = "password_hash"
CONF_API_BASE = "api_base"
CONF_COUNTRY = "country"
CONF_LANGUAGE = "language"

# Config flow input keys
CONF_PASSWORD = "password"

# How far back measurement history is fetched on every refresh.
HISTORY_DAYS = 400

# Manufacturer string used for the Home Assistant device registry entry.
MANUFACTURER = "Fitdays"

DEFAULT_COUNTRY = "NL"
