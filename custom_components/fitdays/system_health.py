"""Provide info to system health for the Fitdays integration."""

from __future__ import annotations

from typing import Any

from homeassistant.components import system_health
from homeassistant.core import HomeAssistant, callback

from .const import DOMAIN

try:
    from fitdays.constants import DEFAULT_API_BASE
except ImportError:  # pragma: no cover - handled by manifest requirements
    DEFAULT_API_BASE = "https://online-eu.fitdays.cn/api"


@callback
def async_register(
    hass: HomeAssistant, register: system_health.SystemHealthRegistration
) -> None:
    """Register system health callbacks."""
    register.async_register_info(system_health_info)


async def system_health_info(hass: HomeAssistant) -> dict[str, Any]:
    """Get info for the info page."""
    entries = hass.data.get(DOMAIN) or {}

    api_base = DEFAULT_API_BASE
    profile_count = 0
    healthy = 0
    for stored in entries.values():
        coordinator = stored.get("coordinator")
        client = stored.get("client")
        if client is not None and client.session.api_base:
            api_base = client.session.api_base
        if coordinator is not None:
            profile_count += len((coordinator.data or {}).get("profiles") or {})
            if coordinator.last_update_success:
                healthy += 1

    return {
        "can_reach_server": system_health.async_check_can_reach_url(hass, api_base),
        "accounts": len(entries),
        "accounts_updating": healthy,
        "member_profiles": profile_count,
    }
