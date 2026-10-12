"""Voice Assist Intent Handlers for Smart Wake."""
from __future__ import annotations

import logging
from typing import Any

try:
    from homeassistant.core import HomeAssistant
    from homeassistant.helpers import intent
except Exception:
    HomeAssistant = Any
    class intent:
        class IntentHandler:
            pass
        class IntentResponse:
            def __init__(self, *args: Any, **kwargs: Any) -> None:
                pass
            def async_set_speech(self, text: str) -> None:
                pass
        IntentError = Exception

from .const import DOMAIN
from .coordinator import SmartWakeAlarm

_LOGGER = logging.getLogger(__name__)

INTENT_SET_TIME = "SmartWakeSetTime"
INTENT_SET_STATUS = "SmartWakeSetStatus"
INTENT_SNOOZE = "SmartWakeSnooze"
INTENT_DISMISS = "SmartWakeDismiss"


def async_setup_intents(hass: HomeAssistant) -> None:
    """Register custom intents for Home Assistant Assist."""
    if not hasattr(intent, "async_register"):
        return

    intent.async_register(hass, SmartWakeSetTimeHandler())
    intent.async_register(hass, SmartWakeSetStatusHandler())
    intent.async_register(hass, SmartWakeSnoozeHandler())
    intent.async_register(hass, SmartWakeDismissHandler())


def _find_alarm(hass: HomeAssistant, name: str | None) -> SmartWakeAlarm | None:
    """Find alarm instance by name or return the first available one."""
    domain_data: dict[str, SmartWakeAlarm] = hass.data.get(DOMAIN, {})
    if not domain_data:
        return None

    if name:
        target_name = name.strip().lower()
        for alarm in domain_data.values():
            if target_name in alarm.name.lower() or alarm.name.lower() in target_name:
                return alarm

    # Default to first available alarm
    return next(iter(domain_data.values()), None)


class SmartWakeSetTimeHandler(intent.IntentHandler):
    """Handle SmartWakeSetTime intent."""

    intent_type = INTENT_SET_TIME

    async def async_handle(self, intent_obj: Any) -> Any:
        """Handle setting alarm time via Voice Assist."""
        hass = intent_obj.hass
        slots = self.async_validate_slots(intent_obj.slots)
        time_slot = slots.get("time", {}).get("value")
        alarm_slot = slots.get("alarm", {}).get("value")

        if not time_slot:
            response = intent_obj.create_response()
            response.async_set_speech("Bitte nenne eine Uhrzeit, auf die der Wecker gestellt werden soll.")
            return response

        alarm = _find_alarm(hass, alarm_slot)
        if not alarm:
            response = intent_obj.create_response()
            response.async_set_speech("Es wurde kein passender Smart Wake Wecker gefunden.")
            return response

        # Format time to HH:MM
        clean_time = str(time_slot).strip()
        if len(clean_time) == 4 and clean_time.isdigit():
            clean_time = f"{clean_time[:2]}:{clean_time[2:]}"
        elif ":" not in clean_time and clean_time.isdigit():
            clean_time = f"{int(clean_time):02d}:00"

        await alarm.async_set_time(clean_time)

        response = intent_obj.create_response()
        response.async_set_speech(f"{alarm.name} wurde auf {clean_time} Uhr gestellt.")
        return response


class SmartWakeSetStatusHandler(intent.IntentHandler):
    """Handle SmartWakeSetStatus intent."""

    intent_type = INTENT_SET_STATUS

    async def async_handle(self, intent_obj: Any) -> Any:
        """Handle enabling/disabling alarm via Voice Assist."""
        hass = intent_obj.hass
        slots = self.async_validate_slots(intent_obj.slots)
        status_slot = str(slots.get("status", {}).get("value", "")).lower()
        alarm_slot = slots.get("alarm", {}).get("value")

        alarm = _find_alarm(hass, alarm_slot)
        if not alarm:
            response = intent_obj.create_response()
            response.async_set_speech("Es wurde kein Smart Wake Wecker gefunden.")
            return response

        enable = status_slot not in ("aus", "deaktiviert", "off", "disable", "disabled", "ausschalten")
        await alarm.async_set_enabled(enable)

        action_text = "aktiviert" if enable else "ausgeschaltet"
        response = intent_obj.create_response()
        response.async_set_speech(f"{alarm.name} wurde {action_text}.")
        return response


class SmartWakeSnoozeHandler(intent.IntentHandler):
    """Handle SmartWakeSnooze intent."""

    intent_type = INTENT_SNOOZE

    async def async_handle(self, intent_obj: Any) -> Any:
        """Handle snooze command via Voice Assist."""
        hass = intent_obj.hass
        slots = self.async_validate_slots(intent_obj.slots)
        alarm_slot = slots.get("alarm", {}).get("value")
        duration_slot = slots.get("duration", {}).get("value")

        alarm = _find_alarm(hass, alarm_slot)
        if not alarm:
            response = intent_obj.create_response()
            response.async_set_speech("Es wurde kein Smart Wake Wecker gefunden.")
            return response

        duration = int(duration_slot) if duration_slot and str(duration_slot).isdigit() else None
        res = await alarm.async_snooze(custom_duration=duration)

        response = intent_obj.create_response()
        if res:
            dur_text = duration or alarm.snooze_duration
            response.async_set_speech(f"In Ordnung, noch {dur_text} Minuten weiterschlafen.")
        else:
            response.async_set_speech(f"Schlummern für {alarm.name} ist nicht möglich oder das Schlummer-Limit wurde erreicht.")
        return response


class SmartWakeDismissHandler(intent.IntentHandler):
    """Handle SmartWakeDismiss intent."""

    intent_type = INTENT_DISMISS

    async def async_handle(self, intent_obj: Any) -> Any:
        """Handle dismiss / stop alarm command via Voice Assist."""
        hass = intent_obj.hass
        slots = self.async_validate_slots(intent_obj.slots)
        alarm_slot = slots.get("alarm", {}).get("value")

        alarm = _find_alarm(hass, alarm_slot)
        if not alarm:
            response = intent_obj.create_response()
            response.async_set_speech("Es wurde kein Smart Wake Wecker gefunden.")
            return response

        dismissed = await alarm.async_dismiss()
        response = intent_obj.create_response()
        if dismissed:
            response.async_set_speech(f"Guten Morgen! {alarm.name} wurde beendet.")
        else:
            response.async_set_speech(f"Anti-Cheat aktiv! {alarm.name} schlummert weiter, bis die Aufsteh-Bedingung erfüllt ist.")
        return response
