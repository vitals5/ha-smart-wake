"""Services for Smart Wake integration."""
from __future__ import annotations

import logging
from typing import Any

try:
    import voluptuous as vol
except ImportError:
    class vol:  # type: ignore
        @staticmethod
        def Schema(s: Any) -> Any:
            return s
        @staticmethod
        def Required(k: Any, **kwargs: Any) -> Any:
            return k
        @staticmethod
        def Optional(k: Any, **kwargs: Any) -> Any:
            return k
        @staticmethod
        def Coerce(t: Any) -> Any:
            return t

try:
    from homeassistant.core import HomeAssistant, ServiceCall
    from homeassistant.helpers import config_validation as cv
except Exception:
    HomeAssistant = Any
    ServiceCall = Any
    class cv:
        @staticmethod
        def string(v: Any) -> str:
            return str(v)
        @staticmethod
        def boolean(v: Any) -> bool:
            return bool(v)
        @staticmethod
        def positive_int(v: Any) -> int:
            return int(v)

from .const import DOMAIN
from .coordinator import SmartWakeAlarm

_LOGGER = logging.getLogger(__name__)

SERVICE_SNOOZE = "snooze"
SERVICE_DISMISS = "dismiss"
SERVICE_TEST_ALARM = "test_alarm"
SERVICE_STOP_TEST = "stop_test"
SERVICE_SKIP_NEXT = "skip_next"
SERVICE_SET_TIME = "set_time"

SCHEMA_SNOOZE = vol.Schema(
    {
        vol.Optional("alarm_id"): str,
        vol.Optional("duration"): vol.Coerce(int),
    }
)

SCHEMA_DISMISS = vol.Schema(
    {
        vol.Optional("alarm_id"): str,
    }
)

SCHEMA_TEST_ALARM = vol.Schema(
    {
        vol.Optional("alarm_id"): str,
    }
)

SCHEMA_STOP_TEST = vol.Schema(
    {
        vol.Optional("alarm_id"): str,
    }
)

SCHEMA_SKIP_NEXT = vol.Schema(
    {
        vol.Optional("alarm_id"): str,
        vol.Optional("skip", default=True): cv.boolean if hasattr(cv, "boolean") else bool,
    }
)

SCHEMA_SET_TIME = vol.Schema(
    {
        vol.Required("time"): str,
        vol.Optional("alarm_id"): str,
    }
)


def _get_target_alarms(hass: HomeAssistant, alarm_id: str | None) -> list[SmartWakeAlarm]:
    """Find target alarms by entry_id, name, or all matching active ones."""
    domain_data: dict[str, SmartWakeAlarm] = hass.data.get(DOMAIN, {})
    if not domain_data:
        return []

    if alarm_id:
        # Match by entry_id directly
        if alarm_id in domain_data:
            return [domain_data[alarm_id]]
        # Match by name or entity_id suffix
        cleaned = alarm_id.lower().replace("switch.", "").replace("time.", "").replace("sensor.", "").replace("button.", "")
        for alarm in domain_data.values():
            if alarm.entry_id == alarm_id or alarm.name.lower() == alarm_id.lower() or cleaned in alarm.name.lower():
                return [alarm]
        _LOGGER.warning("Smart Wake alarm '%s' not found", alarm_id)
        return []

    # If no target specified, return all active alarms (or all alarms)
    return list(domain_data.values())


def async_register_services(hass: HomeAssistant) -> None:
    """Register all Smart Wake services."""

    async def handle_snooze(call: ServiceCall) -> None:
        """Handle snooze service call."""
        alarm_id = call.data.get("alarm_id")
        duration = call.data.get("duration")
        alarms = _get_target_alarms(hass, alarm_id)
        for alarm in alarms:
            await alarm.async_snooze(custom_duration=duration)

    async def handle_dismiss(call: ServiceCall) -> None:
        """Handle dismiss service call."""
        alarm_id = call.data.get("alarm_id")
        alarms = _get_target_alarms(hass, alarm_id)
        for alarm in alarms:
            await alarm.async_dismiss()

    async def handle_test_alarm(call: ServiceCall) -> None:
        """Handle test alarm (dry-run) call."""
        alarm_id = call.data.get("alarm_id")
        alarms = _get_target_alarms(hass, alarm_id)
        for alarm in alarms:
            await alarm.async_start_dry_run()

    async def handle_stop_test(call: ServiceCall) -> None:
        """Handle stop test call."""
        alarm_id = call.data.get("alarm_id")
        alarms = _get_target_alarms(hass, alarm_id)
        for alarm in alarms:
            await alarm.async_stop_dry_run()

    async def handle_skip_next(call: ServiceCall) -> None:
        """Handle skip next alarm call."""
        alarm_id = call.data.get("alarm_id")
        skip = call.data.get("skip", True)
        alarms = _get_target_alarms(hass, alarm_id)
        for alarm in alarms:
            alarm.set_skip_next(skip)

    async def handle_set_time(call: ServiceCall) -> None:
        """Handle set time service call."""
        new_time = call.data["time"]
        alarm_id = call.data.get("alarm_id")
        alarms = _get_target_alarms(hass, alarm_id)
        for alarm in alarms:
            await alarm.async_set_time(new_time)

    if hasattr(hass, "services"):
        hass.services.async_register(DOMAIN, SERVICE_SNOOZE, handle_snooze, schema=SCHEMA_SNOOZE)
        hass.services.async_register(DOMAIN, SERVICE_DISMISS, handle_dismiss, schema=SCHEMA_DISMISS)
        hass.services.async_register(DOMAIN, SERVICE_TEST_ALARM, handle_test_alarm, schema=SCHEMA_TEST_ALARM)
        hass.services.async_register(DOMAIN, SERVICE_STOP_TEST, handle_stop_test, schema=SCHEMA_STOP_TEST)
        hass.services.async_register(DOMAIN, SERVICE_SKIP_NEXT, handle_skip_next, schema=SCHEMA_SKIP_NEXT)
        hass.services.async_register(DOMAIN, SERVICE_SET_TIME, handle_set_time, schema=SCHEMA_SET_TIME)


def async_unregister_services(hass: HomeAssistant) -> None:
    """Unregister Smart Wake services when all entries are removed."""
    if hasattr(hass, "services"):
        for s in (
            SERVICE_SNOOZE,
            SERVICE_DISMISS,
            SERVICE_TEST_ALARM,
            SERVICE_STOP_TEST,
            SERVICE_SKIP_NEXT,
            SERVICE_SET_TIME,
        ):
            if hass.services.has_service(DOMAIN, s):
                hass.services.async_remove(DOMAIN, s)
