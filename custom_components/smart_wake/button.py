"""Button platform for Smart Wake."""
from __future__ import annotations

import logging
from typing import Any

try:
    from homeassistant.components.button import ButtonEntity
    from homeassistant.config_entries import ConfigEntry
    from homeassistant.core import HomeAssistant
    from homeassistant.helpers.entity import DeviceInfo
except Exception:
    class ButtonEntity:
        pass
    ConfigEntry = Any
    HomeAssistant = Any
    DeviceInfo = dict

from .const import DOMAIN, VERSION
from .coordinator import SmartWakeAlarm

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: Any
) -> None:
    """Set up Smart Wake buttons from a config entry."""
    alarm: SmartWakeAlarm = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([
        SmartWakeSnoozeButton(alarm, entry),
        SmartWakeDismissButton(alarm, entry),
        SmartWakeTestButton(alarm, entry),
        SmartWakeSkipNextButton(alarm, entry),
    ])


class SmartWakeBaseButton(ButtonEntity):
    """Base button for Smart Wake."""

    _attr_has_entity_name = True

    def __init__(self, alarm: SmartWakeAlarm, entry: ConfigEntry, key: str, name: str) -> None:
        """Initialize the base button."""
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
            sw_version=VERSION,
        )


class SmartWakeSnoozeButton(SmartWakeBaseButton):
    """Button triggering snooze action."""

    _attr_translation_key = "snooze"
    _attr_icon = "mdi:alarm-snooze"

    def __init__(self, alarm: SmartWakeAlarm, entry: ConfigEntry) -> None:
        super().__init__(alarm, entry, "snooze", "Snooze")

    async def async_press(self) -> None:
        """Press the snooze button."""
        _LOGGER.info("Snooze button pressed for Smart Wake [%s]", self._alarm.name)
        await self._alarm.async_snooze()


class SmartWakeDismissButton(SmartWakeBaseButton):
    """Button triggering dismiss action."""

    _attr_translation_key = "dismiss"
    _attr_icon = "mdi:alarm-off"

    def __init__(self, alarm: SmartWakeAlarm, entry: ConfigEntry) -> None:
        super().__init__(alarm, entry, "dismiss", "Dismiss")

    async def async_press(self) -> None:
        """Press the dismiss button."""
        _LOGGER.info("Dismiss button pressed for Smart Wake [%s]", self._alarm.name)
        await self._alarm.async_dismiss()


class SmartWakeTestButton(SmartWakeBaseButton):
    """Button triggering 30s dry-run test mode."""

    _attr_translation_key = "test"
    _attr_icon = "mdi:play-circle-outline"

    def __init__(self, alarm: SmartWakeAlarm, entry: ConfigEntry) -> None:
        super().__init__(alarm, entry, "test", "Test Alarm (Dry-Run)")

    async def async_press(self) -> None:
        """Press the test button."""
        _LOGGER.info("Test button pressed for Smart Wake [%s]", self._alarm.name)
        if self._alarm.is_dry_run:
            await self._alarm.async_stop_dry_run()
        else:
            await self._alarm.async_start_dry_run()


class SmartWakeSkipNextButton(SmartWakeBaseButton):
    """Button toggling skip next run."""

    _attr_translation_key = "skip_next"
    _attr_icon = "mdi:skip-next"

    def __init__(self, alarm: SmartWakeAlarm, entry: ConfigEntry) -> None:
        super().__init__(alarm, entry, "skip_next", "Skip Next Alarm")

    async def async_press(self) -> None:
        """Press the skip next button."""
        _LOGGER.info("Skip next pressed for Smart Wake [%s]", self._alarm.name)
        self._alarm.set_skip_next(not self._alarm.skip_next)
