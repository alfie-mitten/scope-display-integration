"""What the display is doing: whether it is playing, and its frame rate."""

from __future__ import annotations

from typing import Any

from homeassistant.components.sensor import SensorDeviceClass, SensorEntity, SensorStateClass
from homeassistant.const import EntityCategory
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from . import ScopeConfigEntry
from .entity import ScopeEntity


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ScopeConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    c = entry.runtime_data.coordinator
    async_add_entities([OutputSensor(c), FpsSensor(c)])


class OutputSensor(ScopeEntity, SensorEntity):
    """playing, stopped or error -- the audio feed into the scope."""

    _attr_device_class = SensorDeviceClass.ENUM
    _attr_options = ["playing", "stopped", "error"]

    def __init__(self, coordinator) -> None:
        super().__init__(coordinator, "output")

    @property
    def native_value(self) -> str:
        d = self.coordinator.data
        if d.get("error"):
            return "error"
        return "playing" if d.get("playing") else "stopped"

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        return {"error": self.coordinator.data.get("error")}


class FpsSensor(ScopeEntity, SensorEntity):
    """Frames per second: long frames run slower, down to the box's floor
    (50 by default), so a drop here means Alfie's picture is near its limit."""

    _attr_entity_category = EntityCategory.DIAGNOSTIC
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_native_unit_of_measurement = "fps"

    def __init__(self, coordinator) -> None:
        super().__init__(coordinator, "fps")

    @property
    def native_value(self) -> float | None:
        return self.coordinator.data.get("fps")

