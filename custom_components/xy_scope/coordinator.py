"""Polls the box's status."""

from __future__ import annotations

from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import ScopeClient, ScopeError
from .const import DOMAIN, LOGGER, STATUS_INTERVAL


class ScopeCoordinator(DataUpdateCoordinator[dict[str, Any]]):
    """The box's last status. Entities read it; a push reply refreshes it early."""

    config_entry: ConfigEntry

    def __init__(
        self, hass: HomeAssistant, entry: ConfigEntry, client: ScopeClient
    ) -> None:
        super().__init__(
            hass,
            LOGGER,
            config_entry=entry,
            name=DOMAIN,
            update_interval=STATUS_INTERVAL,
        )
        self.client = client

    async def _async_update_data(self) -> dict[str, Any]:
        try:
            return await self.client.status()
        except ScopeError as err:
            raise UpdateFailed(str(err)) from err

    @callback
    def push_result(self, status: dict[str, Any]) -> None:
        """A push came back with fresh status: use it, no need to wait."""
        self.async_set_updated_data(status)
