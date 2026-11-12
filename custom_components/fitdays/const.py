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

# Which cloud the account lives on. Entries created before Fitdays+ support
# have no backend key and use the original Fitdays cloud.
CONF_BACKEND = "backend"
BACKEND_FITDAYS = "fitdays"
BACKEND_PLUS = "fitdays_plus"

# Fitdays+ session keys
CONF_ACCOUNT_ID = "account_id"
CONF_ACCESS_CODE = "access_code"
CONF_ACCESS_SIGN = "access_sign"
CONF_CLIENT_ID = "client_id"

# Config flow input keys
CONF_PASSWORD = "password"

# How far back measurement history is fetched on every refresh.
HISTORY_DAYS = 400

# Manufacturer string used for the Home Assistant device registry entry.
MANUFACTURER = "Fitdays"

DEFAULT_COUNTRY = "NL"
