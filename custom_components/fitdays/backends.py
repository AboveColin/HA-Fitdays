"""Which cloud a config entry talks to, read from its data alone."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from .const import (
    BACKEND_FITDAYS,
    BACKEND_PLUS,
    CONF_ACCOUNT_ID,
    CONF_BACKEND,
    CONF_UID,
)


def entry_backend(data: Mapping[str, Any]) -> str:
    """The cloud an entry talks to. Entries without the key predate Fitdays+."""
    return data.get(CONF_BACKEND) or BACKEND_FITDAYS


def entry_unique_id(data: Mapping[str, Any]) -> str:
    """
    The config-entry unique id for an account.

    Fitdays and Fitdays+ number their accounts separately, so a Fitdays+ id gets
    a prefix and cannot collide with an existing Fitdays entry.
    """
    if entry_backend(data) == BACKEND_PLUS:
        return f"plus_{data.get(CONF_ACCOUNT_ID)}"
    return str(data.get(CONF_UID))
