"""Sensor platform for Smart Wake."""
from __future__ import annotations

from datetime import datetime
import logging
from typing import Any

try:
    from homeassistant.components.sensor import (
        SensorDeviceClass,
        SensorEntity,
    )
    from homeassistant.config_entries import ConfigEntry
    from homeassistant.core import HomeAssistant, callback
    from homeassistant.helpers.dispatcher import async_dispatcher_connect
    from homeassistant.helpers.entity import DeviceInfo
except Exception:
    class SensorEntity:
        pass
    class SensorDeviceClass:
        TIMESTAMP = "timestamp"
    ConfigEntry = Any
    HomeAssistant = Any
    def callback(func: Any) -> Any:
        return func
    def async_dispatcher_connect(*args: Any) -> Any:
        return lambda: None
    DeviceInfo = dict

from .const import (
    DOMAIN,
    SIGNAL_SMART_WAKE_UPDATED,
    STATUS_DISMISSED,
    STATUS_IDLE,
    STATUS_PRE_ALARM,
    STATUS_RINGING,
    STATUS_SKIPPED,
    STATUS_SNOOZED,
    VERSION,
)
from .coordinator import SmartWakeAlarm

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: Any
) -> None:
    """Set up Smart Wake sensors from a config entry."""
    alarm: SmartWakeAlarm = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([
        SmartWakeStatusSensor(alarm, entry),
        SmartWakeNextAlarmSensor(alarm, entry),
        SmartWakeActivePhaseSensor(alarm, entry),
        SmartWakeSnoozeCountSensor(alarm, entry),
        SmartWakeDynamicOffsetSensor(alarm, entry),
    ])


class SmartWakeBaseSensor(SensorEntity):
    """Base sensor class for Smart Wake."""

    _attr_has_entity_name = True

    def __init__(self, alarm: SmartWakeAlarm, entry: ConfigEntry, key: str, name: str) -> None:
        """Initialize the base sensor."""
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


class SmartWakeStatusSensor(SmartWakeBaseSensor):
    """Sensor reporting the current state machine status."""

    _attr_translation_key = "status"

    def __init__(self, alarm: SmartWakeAlarm, entry: ConfigEntry) -> None:
        super().__init__(alarm, entry, "status", "Status")

    @property
    def native_value(self) -> str:
        """Return the current alarm status."""
        return self._alarm.status

    @property
    def icon(self) -> str:
        """Return status-dependent icon."""
        status = self._alarm.status
        if status == STATUS_RINGING:
            return "mdi:alarm-bell"
        if status == STATUS_PRE_ALARM:
            return "mdi:weather-sunset-up"
        if status == STATUS_SNOOZED:
            return "mdi:alarm-snooze"
        if status == STATUS_SKIPPED:
            return "mdi:alarm-off"
        if status == STATUS_DISMISSED:
            return "mdi:alarm-check"
        return "mdi:alarm"

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return extra status metadata."""
        return {
            "active_phase": self._alarm.active_phase,
            "skip_reason": self._alarm.skip_reason if self._alarm.status == STATUS_SKIPPED else None,
            "is_dry_run": self._alarm.is_dry_run,
            "is_full_test": getattr(self._alarm, "is_full_test", False),
            "anti_cheat_active": self._alarm.has_anti_cheat_configured(),
            "anti_cheat_fulfilled": self._alarm.is_anti_cheat_fulfilled(),
            "snooze_until": self._alarm.snooze_until.isoformat() if self._alarm.snooze_until else None,
        }


class SmartWakeNextAlarmSensor(SmartWakeBaseSensor):
    """Timestamp sensor reporting the next scheduled alarm trigger."""

    _attr_device_class = getattr(SensorDeviceClass, "TIMESTAMP", "timestamp")
    _attr_translation_key = "next_alarm"
    _attr_icon = "mdi:calendar-clock"

    def __init__(self, alarm: SmartWakeAlarm, entry: ConfigEntry) -> None:
        super().__init__(alarm, entry, "next_alarm", "Next Alarm")

    @property
    def native_value(self) -> datetime | None:
        """Return next alarm timestamp (or snooze resume time if snoozed)."""
        if self._alarm.status == STATUS_SNOOZED and self._alarm.snooze_until:
            return self._alarm.snooze_until
        return self._alarm.next_alarm

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return extra schedule details."""
        return {
            "target_time": self._alarm.time_str,
            "pre_alarm_time": self._alarm.pre_alarm_time.isoformat() if self._alarm.pre_alarm_time else None,
            "dynamic_offset_minutes": self._alarm.dynamic_offset_minutes,
            "offset_reasons": self._alarm.offset_reasons,
            "active_days": self._alarm.days,
            "snooze_until": self._alarm.snooze_until.isoformat() if self._alarm.snooze_until else None,
            "alarm_source": getattr(self._alarm, "active_alarm_source", "fixed"),
            "alarm_source_mode": getattr(self._alarm, "alarm_source_mode", "mobile_priority"),
            "mobile_dismiss_sync": getattr(self._alarm, "mobile_dismiss_sync", True),
            "mobile_alarm_entity": getattr(self._alarm, "mobile_alarm_entity", None),
            "mobile_alarm_time": self._alarm.mobile_alarm_time.isoformat() if getattr(self._alarm, "mobile_alarm_time", None) else None,
        }


class SmartWakeActivePhaseSensor(SmartWakeBaseSensor):
    """Sensor showing which phase is currently running."""

    _attr_translation_key = "active_phase"
    _attr_icon = "mdi:progress-clock"

    def __init__(self, alarm: SmartWakeAlarm, entry: ConfigEntry) -> None:
        super().__init__(alarm, entry, "active_phase", "Active Phase")

    @property
    def native_value(self) -> str:
        """Return current active phase."""
        return self._alarm.active_phase


class SmartWakeSnoozeCountSensor(SmartWakeBaseSensor):
    """Sensor reporting current snooze count in the active cycle."""

    _attr_translation_key = "snooze_count"
    _attr_icon = "mdi:counter"

    def __init__(self, alarm: SmartWakeAlarm, entry: ConfigEntry) -> None:
        super().__init__(alarm, entry, "snooze_count", "Snooze Count")

    @property
    def native_value(self) -> int:
        """Return current snooze count."""
        return self._alarm.snooze_count

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return max snooze info."""
        return {
            "max_snooze_count": self._alarm.max_snooze_count,
            "snooze_limit_reached": self._alarm.snooze_count >= self._alarm.max_snooze_count,
        }


class SmartWakeDynamicOffsetSensor(SmartWakeBaseSensor):
    """Sensor reporting weather-driven early wake shift in minutes."""

    _attr_translation_key = "dynamic_offset"
    _attr_native_unit_of_measurement = "min"
    _attr_icon = "mdi:weather-partly-snowy-rainy"

    def __init__(self, alarm: SmartWakeAlarm, entry: ConfigEntry) -> None:
        super().__init__(alarm, entry, "dynamic_offset", "Dynamic Offset")

    @property
    def native_value(self) -> int:
        """Return dynamic offset minutes."""
        return self._alarm.dynamic_offset_minutes

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return reasons for offset."""
        return {
            "reasons": self._alarm.offset_reasons,
        }
