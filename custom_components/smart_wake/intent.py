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


ROOM_ALIASES: dict[str, tuple[str, ...]] = {
    "schlafzimmer": (
        "schlafzimmer", "bedroom",
        "спальня", "спальне", "спальни", "спальню", "спальной", "спальная"
    ),
    "kinderzimmer": (
        "kinderzimmer", "kids room", "nursery",
        "детская", "детской", "детскую", "детскую комнату", "детской комнате"
    ),
    "büro": (
        "büro", "arbeitszimmer", "office", "study",
        "кабинет", "кабинете", "офис", "офисе"
    ),
    "wohnzimmer": (
        "wohnzimmer", "living room",
        "гостиная", "гостиной", "гостиную", "зал", "зале"
    ),
    "küche": (
        "küche", "kitchen",
        "кухня", "кухне", "кухни", "кухню"
    ),
    "bad": (
        "bad", "badezimmer", "bathroom",
        "ванная", "ванной", "ванну", "ванная комната"
    ),
}

WORD_TO_HOUR: dict[str, str] = {
    # Russian
    "один": "01:00", "два": "02:00", "три": "03:00", "четыре": "04:00", "пять": "05:00",
    "шесть": "06:00", "семь": "07:00", "восемь": "08:00", "девять": "09:00", "десять": "10:00",
    "одиннадцать": "11:00", "двенадцать": "12:00",
    # German
    "eins": "01:00", "zwei": "02:00", "drei": "03:00", "vier": "04:00", "fünf": "05:00",
    "sechs": "06:00", "sieben": "07:00", "acht": "08:00", "neun": "09:00", "zehn": "10:00",
    "elf": "11:00", "zwölf": "12:00",
    # English
    "one": "01:00", "two": "02:00", "three": "03:00", "four": "04:00", "five": "05:00",
    "six": "06:00", "seven": "07:00", "eight": "08:00", "nine": "09:00", "ten": "10:00",
    "eleven": "11:00", "twelve": "12:00",
}


def _find_alarm(hass: HomeAssistant, name: str | None) -> SmartWakeAlarm | None:
    """Find alarm instance by name or return the first available one."""
    domain_data: dict[str, SmartWakeAlarm] = hass.data.get(DOMAIN, {})
    if not domain_data:
        return None

    if name:
        target_name = name.strip().lower()
        # 1. Direct substring match
        for alarm in domain_data.values():
            alarm_lower = alarm.name.lower()
            if target_name in alarm_lower or alarm_lower in target_name:
                return alarm

        # 2. Multilingual room alias match (e.g. Russian "спальня" <-> German "Schlafzimmer")
        for group in ROOM_ALIASES.values():
            if any(alias in target_name for alias in group):
                for alarm in domain_data.values():
                    alarm_lower = alarm.name.lower()
                    if any(alias in alarm_lower for alias in group):
                        return alarm

    # Default to first available alarm
    return next(iter(domain_data.values()), None)


class SmartWakeSetTimeHandler(intent.IntentHandler):
    """Handle SmartWakeSetTime intent."""

    intent_type = INTENT_SET_TIME

    async def async_handle(self, intent_obj: Any) -> Any:
        """Handle setting alarm time via Voice Assist."""
        hass = intent_obj.hass
        lang = getattr(intent_obj, "language", "de")
        slots = self.async_validate_slots(intent_obj.slots)
        time_slot = slots.get("time", {}).get("value")
        alarm_slot = slots.get("alarm", {}).get("value")

        if not time_slot:
            response = intent_obj.create_response()
            if lang == "ru":
                response.async_set_speech("Пожалуйста, назовите время для установки будильника.")
            elif lang == "en":
                response.async_set_speech("Please specify a time to set the alarm to.")
            else:
                response.async_set_speech("Bitte nenne eine Uhrzeit, auf die der Wecker gestellt werden soll.")
            return response

        alarm = _find_alarm(hass, alarm_slot)
        if not alarm:
            response = intent_obj.create_response()
            if lang == "ru":
                response.async_set_speech("Подходящий будильник Smart Wake не найден.")
            elif lang == "en":
                response.async_set_speech("No matching Smart Wake alarm was found.")
            else:
                response.async_set_speech("Es wurde kein passender Smart Wake Wecker gefunden.")
            return response

        # Clean and format time to HH:MM
        clean_time = str(time_slot).strip().lower()
        for suffix in ("часов", "часа", "час", "uhr", "o'clock", "am", "pm"):
            if clean_time.endswith(suffix):
                clean_time = clean_time[:-len(suffix)].strip()

        if clean_time in WORD_TO_HOUR:
            clean_time = WORD_TO_HOUR[clean_time]
        elif len(clean_time) == 4 and clean_time.isdigit():
            clean_time = f"{clean_time[:2]}:{clean_time[2:]}"
        elif ":" not in clean_time and clean_time.isdigit():
            clean_time = f"{int(clean_time):02d}:00"

        await alarm.async_set_time(clean_time)

        response = intent_obj.create_response()
        if lang == "ru":
            response.async_set_speech(f"Будильник {alarm.name} установлен на {clean_time}.")
        elif lang == "en":
            response.async_set_speech(f"{alarm.name} set to {clean_time}.")
        else:
            response.async_set_speech(f"{alarm.name} wurde auf {clean_time} Uhr gestellt.")
        return response


class SmartWakeSetStatusHandler(intent.IntentHandler):
    """Handle SmartWakeSetStatus intent."""

    intent_type = INTENT_SET_STATUS

    async def async_handle(self, intent_obj: Any) -> Any:
        """Handle enabling/disabling alarm via Voice Assist."""
        hass = intent_obj.hass
        lang = getattr(intent_obj, "language", "de")
        slots = self.async_validate_slots(intent_obj.slots)
        status_slot = str(slots.get("status", {}).get("value", "")).lower()
        alarm_slot = slots.get("alarm", {}).get("value")

        alarm = _find_alarm(hass, alarm_slot)
        if not alarm:
            response = intent_obj.create_response()
            if lang == "ru":
                response.async_set_speech("Будильник Smart Wake не найден.")
            elif lang == "en":
                response.async_set_speech("Smart Wake alarm not found.")
            else:
                response.async_set_speech("Es wurde kein Smart Wake Wecker gefunden.")
            return response

        enable = status_slot not in ("aus", "deaktiviert", "off", "disable", "disabled", "ausschalten", "отключить", "выключить")
        await alarm.async_set_enabled(enable)

        response = intent_obj.create_response()
        if lang == "ru":
            action_text = "включён" if enable else "выключен"
            response.async_set_speech(f"Будильник {alarm.name} {action_text}.")
        elif lang == "en":
            action_text = "enabled" if enable else "disabled"
            response.async_set_speech(f"{alarm.name} {action_text}.")
        else:
            action_text = "aktiviert" if enable else "ausgeschaltet"
            response.async_set_speech(f"{alarm.name} wurde {action_text}.")
        return response


class SmartWakeSnoozeHandler(intent.IntentHandler):
    """Handle SmartWakeSnooze intent."""

    intent_type = INTENT_SNOOZE

    async def async_handle(self, intent_obj: Any) -> Any:
        """Handle snooze command via Voice Assist."""
        hass = intent_obj.hass
        lang = getattr(intent_obj, "language", "de")
        slots = self.async_validate_slots(intent_obj.slots)
        alarm_slot = slots.get("alarm", {}).get("value")
        duration_slot = slots.get("duration", {}).get("value")

        alarm = _find_alarm(hass, alarm_slot)
        if not alarm:
            response = intent_obj.create_response()
            if lang == "ru":
                response.async_set_speech("Будильник Smart Wake не найден.")
            elif lang == "en":
                response.async_set_speech("Smart Wake alarm not found.")
            else:
                response.async_set_speech("Es wurde kein Smart Wake Wecker gefunden.")
            return response

        duration = int(duration_slot) if duration_slot and str(duration_slot).isdigit() else None
        res = await alarm.async_snooze(custom_duration=duration)

        response = intent_obj.create_response()
        dur_text = duration or alarm.snooze_duration
        if res:
            if lang == "ru":
                response.async_set_speech(f"Хорошо, ещё {dur_text} минут сна.")
            elif lang == "en":
                response.async_set_speech(f"Alright, snoozing for {dur_text} more minutes.")
            else:
                response.async_set_speech(f"In Ordnung, noch {dur_text} Minuten weiterschlafen.")
        else:
            if lang == "ru":
                response.async_set_speech(f"Отложить будильник {alarm.name} невозможно или достигнут лимит откладываний.")
            elif lang == "en":
                response.async_set_speech(f"Cannot snooze {alarm.name} or maximum snooze limit reached.")
            else:
                response.async_set_speech(f"Schlummern für {alarm.name} ist nicht möglich oder das Schlummer-Limit wurde erreicht.")
        return response


class SmartWakeDismissHandler(intent.IntentHandler):
    """Handle SmartWakeDismiss intent."""

    intent_type = INTENT_DISMISS

    async def async_handle(self, intent_obj: Any) -> Any:
        """Handle dismiss / stop alarm command via Voice Assist."""
        hass = intent_obj.hass
        lang = getattr(intent_obj, "language", "de")
        slots = self.async_validate_slots(intent_obj.slots)
        alarm_slot = slots.get("alarm", {}).get("value")

        alarm = _find_alarm(hass, alarm_slot)
        if not alarm:
            response = intent_obj.create_response()
            if lang == "ru":
                response.async_set_speech("Будильник Smart Wake не найден.")
            elif lang == "en":
                response.async_set_speech("Smart Wake alarm not found.")
            else:
                response.async_set_speech("Es wurde kein Smart Wake Wecker gefunden.")
            return response

        dismissed = await alarm.async_dismiss()
        response = intent_obj.create_response()
        if dismissed:
            if lang == "ru":
                response.async_set_speech(f"Доброе утро! Будильник {alarm.name} отключён.")
            elif lang == "en":
                response.async_set_speech(f"Good morning! {alarm.name} dismissed.")
            else:
                response.async_set_speech(f"Guten Morgen! {alarm.name} wurde beendet.")
        else:
            if lang == "ru":
                response.async_set_speech(f"Защита от отключения активна! {alarm.name} продолжит звенеть, пока условие не выполнено.")
            elif lang == "en":
                response.async_set_speech(f"Anti-Cheat active! {alarm.name} keeps snoozing until the wake-up condition is met.")
            else:
                response.async_set_speech(f"Anti-Cheat aktiv! {alarm.name} schlummert weiter, bis die Aufsteh-Bedingung erfüllt ist.")
        return response
