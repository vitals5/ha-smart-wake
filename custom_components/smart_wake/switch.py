"""Switch platform for Smart Wake."""
from __future__ import annotations

import logging
from typing import Any

try:
    from homeassistant.components.switch import SwitchEntity
    from homeassistant.config_entries import ConfigEntry
    from homeassistant.core import HomeAssistant, callback
    from homeassistant.helpers.dispatcher import async_dispatcher_connect
    from homeassistant.helpers.entity import DeviceInfo
except Exception:
    class SwitchEntity:
        pass
    ConfigEntry = Any
    HomeAssistant = Any
    def callback(func: Any) -> Any:
        return func
    def async_dispatcher_connect(*args: Any) -> Any:
        return lambda: None
    DeviceInfo = dict

from .const import DOMAIN, SIGNAL_SMART_WAKE_UPDATED, VERSION
from .coordinator import SmartWakeAlarm

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: Any
) -> None:
    """Set up Smart Wake switch entity from a config entry."""
    alarm: SmartWakeAlarm = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([SmartWakeSwitchEntity(alarm, entry)])


class SmartWakeSwitchEntity(SwitchEntity):
    """Switch entity to enable or disable the alarm."""

    _attr_has_entity_name = True
    _attr_translation_key = "enabled"
    _attr_icon = "mdi:alarm-check"

    def __init__(self, alarm: SmartWakeAlarm, entry: ConfigEntry) -> None:
        """Initialize the switch entity."""
        self._alarm = alarm
        self._entry = entry
        self._attr_unique_id = f"{entry.entry_id}_enabled"
        self._attr_name = "Enabled"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry.entry_id)},
            name=alarm.name,
            manufacturer="Smart Wake",
            model="Smart Alarm Clock",
            sw_version=VERSION,
        )

    @property
    def is_on(self) -> bool:
        """Return True if the alarm is enabled."""
        return self._alarm.enabled

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Enable the alarm."""
        _LOGGER.info("Enabling Smart Wake [%s]", self._alarm.name)
        await self._alarm.async_set_enabled(True)
        self.async_write_ha_state()

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Disable the alarm."""
        _LOGGER.info("Disabling Smart Wake [%s]", self._alarm.name)
        await self._alarm.async_set_enabled(False)
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
