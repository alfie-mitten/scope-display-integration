"""Setting up a box, and picking its outlet."""

from homeassistant.config_entries import SOURCE_USER
from homeassistant.const import CONF_HOST, CONF_PORT, CONF_TOKEN
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.xy_scope.const import DOMAIN

DATA = {CONF_HOST: "192.0.2.10", CONF_PORT: 8080, CONF_TOKEN: "secret"}


async def _start(hass):
    return await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER})


async def test_user_flow_creates_entry_with_outlet_guess(hass: HomeAssistant, box):
    hass.states.async_set("switch.kitchen_kettle", "off")
    hass.states.async_set("switch.living_room_oscilloscope", "on")
    result = await _start(hass)
    assert result["type"] is FlowResultType.FORM
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], DATA)
    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["data"] == DATA
    assert result["options"] == {"power_switch": "switch.living_room_oscilloscope"}


async def test_user_flow_errors(hass: HomeAssistant, box):
    for setup, error in (
        (lambda: setattr(box, "down", True), "cannot_connect"),
        (lambda: setattr(box, "token_ok", False), "invalid_auth"),
        (lambda: setattr(box, "api", 99), "unsupported_version"),
    ):
        box.down, box.token_ok, box.api = False, True, 1
        setup()
        result = await _start(hass)
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], DATA)
        assert result["type"] is FlowResultType.FORM
        assert result["errors"] == {"base": error}


async def test_same_box_twice_aborts(hass: HomeAssistant, box):
    MockConfigEntry(domain=DOMAIN, data=DATA).add_to_hass(hass)
    result = await _start(hass)
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], DATA)
    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "already_configured"


async def test_options_flow_saves_outlet(hass: HomeAssistant, box):
    entry = MockConfigEntry(domain=DOMAIN, data=DATA,
                            options={"power_switch": "switch.a"})
    entry.add_to_hass(hass)
    await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()
    result = await hass.config_entries.options.async_init(entry.entry_id)
    assert result["type"] is FlowResultType.FORM
    result = await hass.config_entries.options.async_configure(
        result["flow_id"], {"power_switch": "switch.b"})
    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert entry.options == {"power_switch": "switch.b"}


async def test_reauth_takes_a_new_token(hass: HomeAssistant, box):
    entry = MockConfigEntry(domain=DOMAIN, data=DATA)
    entry.add_to_hass(hass)
    result = await entry.start_reauth_flow(hass)
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {CONF_TOKEN: "new"})
    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "reauth_successful"
    assert entry.data[CONF_TOKEN] == "new"
    await hass.async_block_till_done()
    await hass.config_entries.async_unload(entry.entry_id)

