"""Config flow for the Fitdays integration."""

from __future__ import annotations

import logging
from collections.abc import Mapping
from typing import Any

import voluptuous as vol
from homeassistant.config_entries import ConfigFlow, ConfigFlowResult
from homeassistant.const import CONF_EMAIL, CONF_PASSWORD
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.selector import (
    TextSelector,
    TextSelectorConfig,
    TextSelectorType,
)

from .const import CONF_COUNTRY, DEFAULT_COUNTRY, DOMAIN

_LOGGER = logging.getLogger(__name__)

# A bare `str` renders the secret in clear text in the config form. TextSelector
# with type PASSWORD makes the browser treat it as a password field.
_SECRET = TextSelector(TextSelectorConfig(type=TextSelectorType.PASSWORD))

try:
    from fitdays import FitdaysClient
    from fitdays.exceptions import (
        FitdaysAuthError,
        FitdaysError,
        FitdaysNetworkError,
        FitdaysValidationError,
    )
except ImportError as err:  # pragma: no cover - handled by manifest requirements
    _LOGGER.error("Failed to import the fitdays package: %s", err)
    raise


def _credentials_schema(email: str = "", country: str = DEFAULT_COUNTRY) -> vol.Schema:
    """Build the email/password/country form, prefilled with what we know."""
    return vol.Schema(
        {
            vol.Required(CONF_EMAIL, default=email): str,
            vol.Required(CONF_PASSWORD): _SECRET,
            vol.Optional(CONF_COUNTRY, default=country or DEFAULT_COUNTRY): str,
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
        except FitdaysValidationError:
            # The client rejects blank input before it calls the cloud. That is
            # a form problem, not an outage, so say so instead of "unknown".
            return None, "invalid_auth"
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
            step_id="user", data_schema=_credentials_schema(), errors=errors
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
        """Ask for the credentials again and refresh the stored session."""
        errors: dict[str, str] = {}
        existing = self._reauth_entry_data or {}
        email = existing.get(CONF_EMAIL) or ""

        if user_input is not None:
            email = user_input[CONF_EMAIL].strip()
            new_data, error = await self._async_try_login(
                email,
                user_input[CONF_PASSWORD],
                user_input.get(CONF_COUNTRY) or DEFAULT_COUNTRY,
            )
            if error:
                errors["base"] = error
            else:
                return self.async_update_reload_and_abort(
                    self._get_reauth_entry(),
                    data={**existing, **new_data},
                )

        # The email is asked for rather than taken from the entry, because an
        # entry written before the email was stored has none, and a login with
        # a blank email fails in the client before it reaches the cloud.
        return self.async_show_form(
            step_id="reauth_confirm",
            data_schema=_credentials_schema(
                email, existing.get(CONF_COUNTRY) or DEFAULT_COUNTRY
            ),
            description_placeholders={"email": email or "this account"},
            errors=errors,
        )

    async def async_step_reconfigure(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Let the user point the entry at fresh credentials."""
        errors: dict[str, str] = {}
        entry = self._get_reconfigure_entry()
        email = entry.data.get(CONF_EMAIL) or ""
        country = entry.data.get(CONF_COUNTRY) or DEFAULT_COUNTRY

        if user_input is not None:
            email = user_input[CONF_EMAIL].strip()
            country = user_input.get(CONF_COUNTRY) or DEFAULT_COUNTRY
            new_data, error = await self._async_try_login(
                email, user_input[CONF_PASSWORD], country
            )
            if error:
                errors["base"] = error
            elif str(new_data.get("uid")) != str(entry.unique_id):
                # Reconfigure repairs one account's entry. A different account
                # belongs in its own entry, or its sensors would silently
                # change meaning.
                return self.async_abort(reason="account_mismatch")
            else:
                return self.async_update_reload_and_abort(
                    entry,
                    data={**entry.data, **new_data},
                    title=email,
                )

        return self.async_show_form(
            step_id="reconfigure",
            data_schema=_credentials_schema(email, country),
            errors=errors,
        )
