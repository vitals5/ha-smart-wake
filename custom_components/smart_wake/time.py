"""Time platform for Smart Wake."""
from __future__ import annotations

from datetime import time as dt_time
import logging
from typing import Any

try:
    from homeassistant.components.time import TimeEntity
    from homeassistant.config_entries import ConfigEntry
    from homeassistant.core import HomeAssistant, callback
    from homeassistant.helpers.dispatcher import async_dispatcher_connect
    from homeassistant.helpers.entity import DeviceInfo
except Exception:
    class TimeEntity:
        pass
    ConfigEntry = Any
    HomeAssistant = Any
    def callback(func: Any) -> Any:
        return func
    def async_dispatcher_connect(*args: Any) -> Any:
        return lambda: None
    DeviceInfo = dict

from .const import DOMAIN, SIGNAL_SMART_WAKE_UPDATED
from .coordinator import SmartWakeAlarm

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: Any
) -> None:
    """Set up Smart Wake time entity from a config entry."""
    alarm: SmartWakeAlarm = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([SmartWakeTimeEntity(alarm, entry)])


class SmartWakeTimeEntity(TimeEntity):
    """Native Time entity for adjusting the alarm time."""

    _attr_has_entity_name = True
    _attr_translation_key = "time"
    _attr_icon = "mdi:clock-outline"

    def __init__(self, alarm: SmartWakeAlarm, entry: ConfigEntry) -> None:
        """Initialize the time entity."""
        self._alarm = alarm
        self._entry = entry
        self._attr_unique_id = f"{entry.entry_id}_time"
        self._attr_name = "Alarm Time"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry.entry_id)},
            name=alarm.name,
            manufacturer="Smart Wake",
            model="Smart Alarm Clock",
            sw_version="1.0.0",
        )

    @property
    def native_value(self) -> dt_time | None:
        """Return the target alarm time."""
        try:
            parts = self._alarm.time_str.split(":")
            return dt_time(hour=int(parts[0]), minute=int(parts[1]))
        except Exception:
            return dt_time(6, 30)

    async def async_set_value(self, value: dt_time) -> None:
        """Set a new alarm time."""
        time_str = f"{value.hour:02d}:{value.minute:02d}"
        _LOGGER.info("Setting Smart Wake [%s] time to %s", self._alarm.name, time_str)
        await self._alarm.async_set_time(time_str)
        self.async_write_ha_state()

    async def async_added_to_hass(self) -> None:
        """Register update dispatcher."""
        @callback
        def _update() -> None:
            self.async_write_ha_state()

        self.async_on_remove(
            async_dispatcher_connect(
                self.hass, SIGNAL_SMART_WAKE_UPDATED.format(self._entry.entry_id), _update
            )
        )
