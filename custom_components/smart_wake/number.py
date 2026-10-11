"""Number platform for Smart Wake."""
from __future__ import annotations

import logging
from typing import Any

try:
    from homeassistant.components.number import NumberEntity, NumberMode
    from homeassistant.config_entries import ConfigEntry
    from homeassistant.core import HomeAssistant, callback
    from homeassistant.helpers.dispatcher import async_dispatcher_connect
    from homeassistant.helpers.entity import DeviceInfo
except Exception:
    class NumberEntity:
        pass
    class NumberMode:
        BOX = "box"
        SLIDER = "slider"
    ConfigEntry = Any
    HomeAssistant = Any
    def callback(func: Any) -> Any:
        return func
    def async_dispatcher_connect(*args: Any) -> Any:
        return lambda: None
    DeviceInfo = dict

from .const import (
    CONF_MAX_SNOOZE_COUNT,
    CONF_PRE_ALARM_DURATION,
    CONF_SNOOZE_DURATION,
    DEFAULT_MAX_SNOOZE_COUNT,
    DEFAULT_PRE_ALARM_DURATION,
    DEFAULT_SNOOZE_DURATION,
    DOMAIN,
    SIGNAL_SMART_WAKE_UPDATED,
)
from .coordinator import SmartWakeAlarm

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: Any
) -> None:
    """Set up Smart Wake numbers from a config entry."""
    alarm: SmartWakeAlarm = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([
        SmartWakeSnoozeDurationNumber(alarm, entry),
        SmartWakeMaxSnoozeCountNumber(alarm, entry),
        SmartWakePreAlarmDurationNumber(alarm, entry),
    ])


class SmartWakeBaseNumber(NumberEntity):
    """Base number entity for Smart Wake."""

    _attr_has_entity_name = True

    def __init__(self, alarm: SmartWakeAlarm, entry: ConfigEntry, key: str, name: str) -> None:
        """Initialize base number."""
        self._alarm = alarm
        self._entry = entry
        self._key = key
        self._attr_unique_id = f"{entry.entry_id}_{key}"
        self._attr_name = name
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry.entry_id)},
            name=alarm.name,
            manufacturer="Smart Wake",
            model="Smart Alarm Clock",
            sw_version="1.0.0",
        )

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


class SmartWakeSnoozeDurationNumber(SmartWakeBaseNumber):
    """Number entity for snooze duration in minutes."""

    _attr_translation_key = "snooze_duration"
    _attr_native_unit_of_measurement = "min"
    _attr_native_min_value = 1
    _attr_native_max_value = 60
    _attr_native_step = 1
    _attr_icon = "mdi:timer-outline"

    def __init__(self, alarm: SmartWakeAlarm, entry: ConfigEntry) -> None:
        super().__init__(alarm, entry, "snooze_duration", "Snooze Duration")

    @property
    def native_value(self) -> float:
        """Return the snooze duration."""
        return float(self._alarm.snooze_duration)

    async def async_set_native_value(self, value: float) -> None:
        """Update snooze duration."""
        _LOGGER.info("Setting Smart Wake [%s] snooze duration to %d min", self._alarm.name, int(value))
        self._alarm.update_config({CONF_SNOOZE_DURATION: int(value)})
        self.async_write_ha_state()


class SmartWakeMaxSnoozeCountNumber(SmartWakeBaseNumber):
    """Number entity for maximum snooze count."""

    _attr_translation_key = "max_snooze_count"
    _attr_native_min_value = 0
    _attr_native_max_value = 10
    _attr_native_step = 1
    _attr_icon = "mdi:numeric"

    def __init__(self, alarm: SmartWakeAlarm, entry: ConfigEntry) -> None:
        super().__init__(alarm, entry, "max_snooze_count", "Max Snooze Count")

    @property
    def native_value(self) -> float:
        """Return max snooze count."""
        return float(self._alarm.max_snooze_count)

    async def async_set_native_value(self, value: float) -> None:
        """Update max snooze count."""
        _LOGGER.info("Setting Smart Wake [%s] max snooze count to %d", self._alarm.name, int(value))
        self._alarm.update_config({CONF_MAX_SNOOZE_COUNT: int(value)})
        self.async_write_ha_state()


class SmartWakePreAlarmDurationNumber(SmartWakeBaseNumber):
    """Number entity for pre-alarm duration in minutes."""

    _attr_translation_key = "pre_alarm_duration"
    _attr_native_unit_of_measurement = "min"
    _attr_native_min_value = 0
    _attr_native_max_value = 60
    _attr_native_step = 1
    _attr_icon = "mdi:weather-sunset-up"

    def __init__(self, alarm: SmartWakeAlarm, entry: ConfigEntry) -> None:
        super().__init__(alarm, entry, "pre_alarm_duration", "Pre-Alarm Duration")

    @property
    def native_value(self) -> float:
        """Return pre-alarm duration."""
        return float(self._alarm.pre_alarm_duration)

    async def async_set_native_value(self, value: float) -> None:
        """Update pre-alarm duration."""
        _LOGGER.info("Setting Smart Wake [%s] pre-alarm duration to %d min", self._alarm.name, int(value))
        self._alarm.update_config({CONF_PRE_ALARM_DURATION: int(value)})
        self.async_write_ha_state()
