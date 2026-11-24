"""The display's entities: power through the outlet, scale, status."""

from homeassistant.const import CONF_HOST, CONF_PORT, CONF_TOKEN
from homeassistant.core import HomeAssistant
from pytest_homeassistant_custom_component.common import MockConfigEntry, async_mock_service

from custom_components.xy_scope.const import DOMAIN

DATA = {CONF_HOST: "192.0.2.10", CONF_PORT: 8080, CONF_TOKEN: "secret"}


async def _setup(hass, options):
    entry = MockConfigEntry(domain=DOMAIN, data=DATA, options=options)
    entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()
    return entry


def _ids(hass, domain):
    return sorted(s.entity_id for s in hass.states.async_all(domain))


async def test_entities(hass: HomeAssistant, box):
    hass.states.async_set("switch.outlet", "on")
    await _setup(hass, {"power_switch": "switch.outlet", "inside_temp": "sensor.old"})
    assert _ids(hass, "select") == []
    assert _ids(hass, "number") == ["number.xy_scope_scale"]
    assert _ids(hass, "sensor") == ["sensor.xy_scope_frame_rate", "sensor.xy_scope_output"]
    assert hass.states.get("switch.xy_scope_display_power").state == "on"
    assert hass.states.get("sensor.xy_scope_output").state == "playing"


async def test_power_goes_to_the_outlet(hass: HomeAssistant, box):
    hass.states.async_set("light.outlet", "on")
    await _setup(hass, {"power_switch": "light.outlet"})
    calls = async_mock_service(hass, "light", "turn_off")
    await hass.services.async_call("switch", "turn_off",
                                   {"entity_id": "switch.xy_scope_display_power"}, blocking=True)
    assert [c.data["entity_id"] for c in calls] == ["light.outlet"]


async def test_no_outlet_no_power_switch(hass: HomeAssistant, box):
    await _setup(hass, {})
    assert _ids(hass, "switch") == []


async def test_scale(hass: HomeAssistant, box):
    await _setup(hass, {})
    await hass.services.async_call("number", "set_value",
                                   {"entity_id": "number.xy_scope_scale", "value": 0.5}, blocking=True)
    assert box.writes == [0.5]
    assert hass.states.get("number.xy_scope_scale").state == "0.5"
