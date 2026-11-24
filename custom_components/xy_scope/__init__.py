"""XY Scope Display: the oscilloscope that shows Alfie.

The box (xy-bench) draws one thing: the frames the Alfie integration's scope
card pushes to it. This integration exposes the display as a device: display
power (a switch wrapping the scope's outlet), the scale (number) and two
status sensors. Alfie decides what is on it; automations decide when it is on.
"""

from __future__ import annotations

from dataclasses import dataclass

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_HOST, CONF_PORT, CONF_TOKEN, Platform
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .api import ScopeClient
from .coordinator import ScopeCoordinator

PLATFORMS = [Platform.NUMBER, Platform.SENSOR, Platform.SWITCH]


@dataclass
class ScopeData:
    client: ScopeClient
    coordinator: ScopeCoordinator


type ScopeConfigEntry = ConfigEntry[ScopeData]


async def async_setup_entry(hass: HomeAssistant, entry: ScopeConfigEntry) -> bool:
    client = ScopeClient(
        async_get_clientsession(hass),
        entry.data[CONF_HOST],
        entry.data[CONF_PORT],
        entry.data[CONF_TOKEN],
    )
    coordinator = ScopeCoordinator(hass, entry, client)
    # Not ready (and retried by HA) until the box answers.
    await coordinator.async_config_entry_first_refresh()
    entry.runtime_data = ScopeData(client, coordinator)
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    entry.async_on_unload(entry.add_update_listener(_options_changed))
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ScopeConfigEntry) -> bool:
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)


async def _options_changed(hass: HomeAssistant, entry: ScopeConfigEntry) -> None:
    await hass.config_entries.async_reload(entry.entry_id)
