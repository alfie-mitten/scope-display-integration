"""Set up a box (host, port, token), and pick the scope's outlet."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

import voluptuous as vol

from homeassistant.config_entries import ConfigFlow, ConfigFlowResult, OptionsFlow
from homeassistant.const import CONF_HOST, CONF_PORT, CONF_TOKEN
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.selector import (
    EntitySelector,
    EntitySelectorConfig,
    TextSelector,
    TextSelectorConfig,
    TextSelectorType,
)

from .api import ScopeAuthError, ScopeClient, ScopeConnectionError, ScopeVersionError
from .const import DEFAULT_PORT, DOMAIN, LOGGER, OPT_POWER

_POWER = EntitySelector(EntitySelectorConfig(domain=["switch", "light"]))


def _suggest_power(hass: HomeAssistant) -> dict[str, Any]:
    """A switch or light with "scope" in its id or name, as a first guess."""
    for state in hass.states.async_all(["switch", "light"]):
        words = f"{state.entity_id} {state.attributes.get('friendly_name', '')}".lower()
        if "scope" in words:
            return {OPT_POWER: state.entity_id}
    return {}


def _box_schema(defaults: Mapping[str, Any]) -> vol.Schema:
    return vol.Schema({
        vol.Required(CONF_HOST, default=defaults.get(CONF_HOST, vol.UNDEFINED)): str,
        vol.Required(CONF_PORT, default=defaults.get(CONF_PORT, DEFAULT_PORT)):
            cv.port,
        vol.Required(CONF_TOKEN): TextSelector(
            TextSelectorConfig(type=TextSelectorType.PASSWORD)),
    })


async def _validate(hass: HomeAssistant, data: Mapping[str, Any]) -> dict[str, str]:
    """Errors for the form, empty when the box answers and takes the token."""
    client = ScopeClient(async_get_clientsession(hass), data[CONF_HOST],
                         data[CONF_PORT], data[CONF_TOKEN])
    try:
        await client.status()
        await client.check_token()
    except ScopeConnectionError:
        return {"base": "cannot_connect"}
    except ScopeAuthError:
        return {"base": "invalid_auth"}
    except ScopeVersionError:
        return {"base": "unsupported_version"}
    except Exception:  # noqa: BLE001 -- show the form again, log the surprise
        LOGGER.exception("Unexpected error talking to the scope box")
        return {"base": "unknown"}
    return {}


class ScopeConfigFlow(ConfigFlow, domain=DOMAIN):
    """Host, port and token, typed once and checked against the box."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        errors: dict[str, str] = {}
        if user_input is not None:
            self._async_abort_entries_match(
                {CONF_HOST: user_input[CONF_HOST], CONF_PORT: user_input[CONF_PORT]})
            errors = await _validate(self.hass, user_input)
            if not errors:
                return self.async_create_entry(
                    title=f"XY Scope ({user_input[CONF_HOST]})",
                    data=user_input,
                    # A guess at the outlet; Configure shows it and can change it.
                    options=_suggest_power(self.hass),
                )
        return self.async_show_form(
            step_id="user",
            data_schema=self.add_suggested_values_to_schema(
                _box_schema({}), user_input or {}),
            errors=errors,
        )

    async def async_step_reconfigure(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        entry = self._get_reconfigure_entry()
        errors: dict[str, str] = {}
        if user_input is not None:
            errors = await _validate(self.hass, user_input)
            if not errors:
                return self.async_update_reload_and_abort(entry, data=user_input)
        return self.async_show_form(
            step_id="reconfigure", data_schema=_box_schema(entry.data),
            errors=errors)

    async def async_step_reauth(
        self, entry_data: Mapping[str, Any]
    ) -> ConfigFlowResult:
        return await self.async_step_reauth_confirm()

    async def async_step_reauth_confirm(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        entry = self._get_reauth_entry()
        errors: dict[str, str] = {}
        if user_input is not None:
            data = {**entry.data, CONF_TOKEN: user_input[CONF_TOKEN]}
            errors = await _validate(self.hass, data)
            if not errors:
                return self.async_update_reload_and_abort(entry, data=data)
        return self.async_show_form(
            step_id="reauth_confirm",
            data_schema=vol.Schema({vol.Required(CONF_TOKEN): TextSelector(
                TextSelectorConfig(type=TextSelectorType.PASSWORD))}),
            errors=errors,
        )

    @staticmethod
    @callback
    def async_get_options_flow(config_entry) -> ScopeOptionsFlow:
        return ScopeOptionsFlow()


class ScopeOptionsFlow(OptionsFlow):
    """The display's outlet (optional: without it there is no power switch)."""

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        if user_input is not None:
            return self.async_create_entry(data=user_input)
        schema = vol.Schema({vol.Optional(OPT_POWER): _POWER})
        return self.async_show_form(
            step_id="init",
            data_schema=self.add_suggested_values_to_schema(
                schema, self.config_entry.options),
        )
