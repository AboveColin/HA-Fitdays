"""Config flow for the Fitdays integration."""

from __future__ import annotations

import logging
from collections.abc import Mapping
from typing import Any

import voluptuous as vol
from homeassistant.config_entries import ConfigFlow, ConfigFlowResult
from homeassistant.const import CONF_EMAIL, CONF_PASSWORD
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .const import CONF_COUNTRY, DEFAULT_COUNTRY, DOMAIN

_LOGGER = logging.getLogger(__name__)

try:
    from fitdays import FitdaysClient
    from fitdays.exceptions import FitdaysAuthError, FitdaysError, FitdaysNetworkError
except ImportError as err:  # pragma: no cover - handled by manifest requirements
    _LOGGER.error("Failed to import the fitdays package: %s", err)
    raise

STEP_USER_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_EMAIL): str,
        vol.Required(CONF_PASSWORD): str,
        vol.Optional(CONF_COUNTRY, default=DEFAULT_COUNTRY): str,
    }
)


class FitdaysConfigFlow(ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Fitdays."""

    VERSION = 1

    def __init__(self) -> None:
        self._reauth_entry_data: Mapping[str, Any] | None = None

    async def _async_try_login(
        self, email: str, password: str, country: str
    ) -> tuple[dict[str, Any] | None, str | None]:
        """Attempt a login. Returns (entry_data, error_key)."""
        # Import here so the module stays importable when the requirement is
        # still being installed.
        from . import entry_data_from_session  # pylint: disable=import-outside-toplevel

        session = async_get_clientsession(self.hass)
        try:
            client = await FitdaysClient.login(
                email,
                password,
                http_session=session,
                country=country or DEFAULT_COUNTRY,
            )
        except FitdaysAuthError:
            return None, "invalid_auth"
        except FitdaysNetworkError:
            return None, "cannot_connect"
        except FitdaysError as err:
            _LOGGER.error("Unexpected Fitdays error during login: %s", err)
            return None, "unknown"

        return entry_data_from_session(client.session), None

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle the initial step."""
        errors: dict[str, str] = {}

        if user_input is not None:
            email = user_input[CONF_EMAIL].strip()
            entry_data, error = await self._async_try_login(
                email,
                user_input[CONF_PASSWORD],
                user_input.get(CONF_COUNTRY, DEFAULT_COUNTRY),
            )
            if error:
                errors["base"] = error
            else:
                await self.async_set_unique_id(str(entry_data.get("uid")))
                self._abort_if_unique_id_configured()
                return self.async_create_entry(title=email, data=entry_data)

        return self.async_show_form(
            step_id="user", data_schema=STEP_USER_SCHEMA, errors=errors
        )

    async def async_step_reauth(
        self, entry_data: Mapping[str, Any]
    ) -> ConfigFlowResult:
        """Handle a re-authentication request."""
        self._reauth_entry_data = entry_data
        return await self.async_step_reauth_confirm()

    async def async_step_reauth_confirm(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Ask for the password again and refresh the stored session."""
        errors: dict[str, str] = {}
        existing = self._reauth_entry_data or {}
        email = existing.get(CONF_EMAIL) or ""

        if user_input is not None:
            new_data, error = await self._async_try_login(
                email,
                user_input[CONF_PASSWORD],
                existing.get(CONF_COUNTRY) or DEFAULT_COUNTRY,
            )
            if error:
                errors["base"] = error
            else:
                return self.async_update_reload_and_abort(
                    self._get_reauth_entry(),
                    data={**existing, **new_data},
                )

        return self.async_show_form(
            step_id="reauth_confirm",
            data_schema=vol.Schema({vol.Required(CONF_PASSWORD): str}),
            description_placeholders={"email": email},
            errors=errors,
        )
