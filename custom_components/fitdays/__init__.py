"""The Fitdays integration."""

from __future__ import annotations

import logging
from datetime import timedelta
from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryAuthFailed, ConfigEntryNotReady
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

_LOGGER = logging.getLogger(__name__)

try:
    from fitdays import FitdaysClient, Session
    from fitdays.exceptions import FitdaysAuthError, FitdaysError
except ImportError as err:  # pragma: no cover - handled by manifest requirements
    _LOGGER.error("Failed to import the fitdays package: %s", err)
    raise

from .const import (
    CONF_ACTIVE_SUID,
    CONF_API_BASE,
    CONF_COUNTRY,
    CONF_EMAIL,
    CONF_LANGUAGE,
    CONF_PASSWORD_HASH,
    CONF_REFRESH_TOKEN,
    CONF_TOKEN,
    CONF_UID,
    DOMAIN,
    HISTORY_DAYS,
)

PLATFORMS: list[Platform] = [Platform.SENSOR]

# Scales are weighed at most a handful of times a day, so there is nothing to
# gain from polling hard.
SCAN_INTERVAL = timedelta(minutes=30)


def session_from_entry(entry: ConfigEntry) -> Session:
    """Rebuild a :class:`Session` from the config-entry data."""
    data = entry.data
    return Session(
        token=data.get(CONF_TOKEN),
        refresh_token=data.get(CONF_REFRESH_TOKEN),
        uid=data.get(CONF_UID),
        active_suid=data.get(CONF_ACTIVE_SUID),
        email=data.get(CONF_EMAIL),
        password_hash=data.get(CONF_PASSWORD_HASH),
        api_base=data.get(CONF_API_BASE),
        country=data.get(CONF_COUNTRY),
        language=data.get(CONF_LANGUAGE),
    )


def entry_data_from_session(session: Session) -> dict[str, Any]:
    """Flatten a :class:`Session` back into config-entry data."""
    return {
        CONF_TOKEN: session.token,
        CONF_REFRESH_TOKEN: session.refresh_token,
        CONF_UID: session.uid,
        CONF_ACTIVE_SUID: session.active_suid,
        CONF_EMAIL: session.email,
        CONF_PASSWORD_HASH: session.password_hash,
        CONF_API_BASE: session.api_base,
        CONF_COUNTRY: session.country,
        CONF_LANGUAGE: session.language,
    }


class FitdaysDataUpdateCoordinator(DataUpdateCoordinator):
    """Fetch the account's measurement history on a schedule."""

    def __init__(self, hass: HomeAssistant, client: FitdaysClient) -> None:
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=SCAN_INTERVAL,
        )
        self.client = client

    async def _async_update_data(self) -> dict[str, Any]:
        """Pull the account and reshape it per member profile."""
        try:
            result = await self.client.get_sync(days=HISTORY_DAYS)
        except FitdaysAuthError as err:
            raise ConfigEntryAuthFailed(str(err)) from err
        except FitdaysError as err:
            raise UpdateFailed(f"Error fetching Fitdays data: {err}") from err

        profiles: dict[str, dict[str, Any]] = {}
        for profile in result.profiles:
            if profile.suid is None:
                continue
            measurements = result.for_profile(profile.suid)
            profiles[str(profile.suid)] = {
                "profile": profile,
                "latest": measurements[0] if measurements else None,
                "count": len(measurements),
                "first_measured_at": (
                    measurements[-1].measured_at if measurements else None
                ),
            }

        return {
            "profiles": profiles,
            "devices": result.devices,
            "total_measurements": len(result.measurements),
        }


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Fitdays from a config entry."""
    http_session = async_get_clientsession(hass)

    def save_session(session: Session) -> None:
        """Persist a renewed token back onto the config entry."""
        hass.config_entries.async_update_entry(
            entry,
            data={**entry.data, **entry_data_from_session(session)},
        )

    client = FitdaysClient.from_session(
        session_from_entry(entry),
        http_session=http_session,
        token_updated=save_session,
    )

    coordinator = FitdaysDataUpdateCoordinator(hass, client)
    try:
        await coordinator.async_config_entry_first_refresh()
    except ConfigEntryAuthFailed:
        raise
    except UpdateFailed as err:
        raise ConfigEntryNotReady(str(err)) from err

    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][entry.entry_id] = {
        "client": client,
        "coordinator": coordinator,
    }

    # Deliberately no update listener: renewing a token writes back to the
    # entry, and a reload-on-update listener would turn that into a loop.
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a Fitdays config entry."""
    if await hass.config_entries.async_unload_platforms(entry, PLATFORMS):
        hass.data[DOMAIN].pop(entry.entry_id, None)
        return True
    return False
