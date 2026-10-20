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
        "спальня", "спальне", "спальни", "спальню", "спальной", "спальная",
        "chambre", "chambre à coucher",
        "dormitorio", "habitación", "cuarto",
        "camera", "camera da letto", "stanza",
        "slaapkamer",
        "sypialnia", "sypialni", "sypialnię",
        "quarto", "dormitório",
    ),
    "kinderzimmer": (
        "kinderzimmer", "kids room", "children's room", "nursery",
        "детская", "детской", "детскую", "детскую комнату", "детской комнате",
        "chambre des enfants", "chambre d'enfant", "chambre enfants",
        "habitación de los niños", "cuarto de los niños",
        "camera dei bambini", "cameretta",
        "kinderkamer",
        "pokój dziecięcy", "pokój dzieci", "pokoju dziecięcym",
        "quarto das crianças", "quarto dos miúdos",
    ),
    "büro": (
        "büro", "arbeitszimmer", "office", "study", "workroom",
        "кабинет", "кабинете", "офис", "офисе",
        "bureau",
        "oficina", "despacho",
        "ufficio", "studio",
        "kantoor", "werkkamer",
        "biuro", "biurze", "gabinet", "gabinecie",
        "escritório",
    ),
    "wohnzimmer": (
        "wohnzimmer", "living room",
        "гостиная", "гостиной", "гостиную", "зал", "зале",
        "salon", "séjour",
        "salón", "sala de estar", "sala",
        "salotto", "soggiorno",
        "woonkamer",
        "pokój dzienny", "salonie",
        "sala",
    ),
    "küche": (
        "küche", "kitchen",
        "кухня", "кухне", "кухни", "кухню",
        "cuisine",
        "cocina",
        "cucina",
        "keuken",
        "kuchnia", "kuchni", "kuchnię",
        "cozinha",
    ),
    "bad": (
        "bad", "badezimmer", "bathroom",
        "ванная", "ванной", "ванну", "ванная комната",
        "salle de bain", "salle de bains",
        "baño", "cuarto de baño",
        "bagno",
        "badkamer",
        "łazienka", "łazience", "łazienkę",
        "casa de banho", "banheiro",
    ),
}

WORD_TO_HOUR: dict[str, str] = {
    # Russian
    "один": "01:00", "два": "02:00", "три": "03:00", "четыre": "04:00", "пять": "05:00",
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
    # French
    "un": "01:00", "deux": "02:00", "trois": "03:00", "quatre": "04:00", "cinq": "05:00",
    "six": "06:00", "sept": "07:00", "huit": "08:00", "neuf": "09:00", "dix": "10:00",
    "onze": "11:00", "douze": "12:00",
    # Spanish
    "una": "01:00", "uno": "01:00", "dos": "02:00", "tres": "03:00", "cuatro": "04:00",
    "cinco": "05:00", "seis": "06:00", "siete": "07:00", "ocho": "08:00", "nueve": "09:00",
    "diez": "10:00", "once": "11:00", "doce": "12:00",
    # Italian
    "due": "02:00", "tre": "03:00", "quattro": "04:00", "cinque": "05:00", "sei": "06:00",
    "sette": "07:00", "otto": "08:00", "nove": "09:00", "dieci": "10:00", "undici": "11:00",
    "dodici": "12:00",
    # Dutch
    "een": "01:00", "twee": "02:00", "drie": "03:00", "vier": "04:00", "vijf": "05:00",
    "zes": "06:00", "zeven": "07:00", "acht": "08:00", "negen": "09:00", "tien": "10:00",
    "elf": "11:00", "twaalf": "12:00",
    # Polish
    "pierwsza": "01:00", "druga": "02:00", "trzecia": "03:00", "czwarta": "04:00",
    "piąta": "05:00", "szósta": "06:00", "siódma": "07:00", "ósma": "08:00",
    "dziewiąta": "09:00", "dziesiąta": "10:00", "jedenasta": "11:00", "dwunasta": "12:00",
    # Portuguese
    "duas": "02:00", "dois": "02:00", "três": "03:00", "quatro": "04:00", "cinco": "05:00",
    "seis": "06:00", "sete": "07:00", "oito": "08:00", "nove": "09:00", "dez": "10:00",
    "onze": "11:00", "doze": "12:00",
}

RESPONSES_SET_TIME_NO_SLOT = {
    "de": "Bitte nenne eine Uhrzeit, auf die der Wecker gestellt werden soll.",
    "en": "Please specify a time to set the alarm to.",
    "ru": "Пожалуйста, назовите время для установки будильника.",
    "fr": "Veuillez préciser une heure pour régler le réveil.",
    "es": "Por favor, indica una hora para el despertador.",
    "it": "Per favore, specifica un'ora per la sveglia.",
    "nl": "Geef een tijd op waarop de wekker moet worden gezet.",
    "pl": "Proszę podać godzinę, na którą ma być ustawiony budzik.",
    "pt": "Por favor, indique uma hora para o despertador.",
}

RESPONSES_ALARM_NOT_FOUND = {
    "de": "Es wurde kein passender Smart Wake Wecker gefunden.",
    "en": "No matching Smart Wake alarm was found.",
    "ru": "Подходящий будильник Smart Wake не найден.",
    "fr": "Aucun réveil Smart Wake correspondant n'a été trouvé.",
    "es": "No se encontró ningún despertador Smart Wake coincidente.",
    "it": "Nessuna sveglia Smart Wake corrispondente trovata.",
    "nl": "Geen passende Smart Wake wekker gevonden.",
    "pl": "Nie znaleziono pasującego budzika Smart Wake.",
    "pt": "Nenhum despertador Smart Wake correspondente foi encontrado.",
}

RESPONSES_SET_TIME_DONE = {
    "de": "{name} wurde auf {time} Uhr gestellt.",
    "en": "{name} set to {time}.",
    "ru": "Будильник {name} установлен на {time}.",
    "fr": "{name} a été réglé à {time}.",
    "es": "{name} se ha configurado a las {time}.",
    "it": "{name} impostata alle {time}.",
    "nl": "{name} is ingesteld op {time} uur.",
    "pl": "{name} ustawiony na {time}.",
    "pt": "{name} definido para as {time}.",
}

RESPONSES_SET_STATUS_ON = {
    "de": "{name} wurde aktiviert.",
    "en": "{name} enabled.",
    "ru": "Будильник {name} включён.",
    "fr": "{name} a été activé.",
    "es": "{name} activado.",
    "it": "{name} attivata.",
    "nl": "{name} is ingeschakeld.",
    "pl": "{name} został włączony.",
    "pt": "{name} ativado.",
}

RESPONSES_SET_STATUS_OFF = {
    "de": "{name} wurde ausgeschaltet.",
    "en": "{name} disabled.",
    "ru": "Будильник {name} выключен.",
    "fr": "{name} a été désactivé.",
    "es": "{name} desactivado.",
    "it": "{name} disattivata.",
    "nl": "{name} is uitgeschakeld.",
    "pl": "{name} został wyłączony.",
    "pt": "{name} desativado.",
}

RESPONSES_SNOOZE_DONE = {
    "de": "In Ordnung, noch {duration} Minuten weiterschlafen.",
    "en": "Alright, snoozing for {duration} more minutes.",
    "ru": "Хорошо, ещё {duration} минут сна.",
    "fr": "D'accord, encore {duration} minutes de sommeil.",
    "es": "De acuerdo, pospuesto por {duration} minutos más.",
    "it": "Va bene, rinvio di altri {duration} minuti.",
    "nl": "In orde, nog {duration} minuten doorslapen.",
    "pl": "W porządku, jeszcze {duration} minut drzemki.",
    "pt": "Tudo bem, adiado por mais {duration} minutos.",
}

RESPONSES_SNOOZE_FAILED = {
    "de": "Schlummern für {name} ist nicht möglich oder das Schlummer-Limit wurde erreicht.",
    "en": "Cannot snooze {name} or maximum snooze limit reached.",
    "ru": "Отложить будильник {name} невозможно или достигнут лимит откладываний.",
    "fr": "Impossible de répéter {name} ou limite maximale de répétitions atteinte.",
    "es": "No se puede posponer {name} o se alcanzó el límite máximo de posposiciones.",
    "it": "Impossibile posporre {name} o limite massimo di rinvii raggiunto.",
    "nl": "Snoozen voor {name} is niet mogelijk of het maximale aantal snoozes is bereikt.",
    "pl": "Nie można włączyć drzemki dla {name} lub osiągnięto limit drzemek.",
    "pt": "Não é possível adiar {name} ou o limite máximo de adiamentos foi atingido.",
}

RESPONSES_DISMISS_DONE = {
    "de": "Guten Morgen! {name} wurde beendet.",
    "en": "Good morning! {name} dismissed.",
    "ru": "Доброе утро! Будильник {name} отключён.",
    "fr": "Bonjour ! {name} a été arrêté.",
    "es": "¡Buenos días! {name} ha sido apagado.",
    "it": "Buongiorno! {name} è stata spenta.",
    "nl": "Goedemorgen! {name} is uitgeschakeld.",
    "pl": "Dzień dobry! {name} został wyłączony.",
    "pt": "Bom dia! {name} foi desligado.",
}

RESPONSES_DISMISS_ANTI_CHEAT = {
    "de": "Anti-Cheat aktiv! {name} schlummert weiter, bis die Aufsteh-Bedingung erfüllt ist.",
    "en": "Anti-Cheat active! {name} keeps snoozing until the wake-up condition is met.",
    "ru": "Защита от отключения активна! {name} продолжит звенеть, пока условие не выполнено.",
    "fr": "Anti-triche actif ! {name} continue de répéter jusqu'à ce que la condition soit remplie.",
    "es": "¡Antitrampas activo! {name} seguirá posponiéndose hasta cumplir la condición de levantarse.",
    "it": "Anti-inganno attivo! {name} continua a rinviare finché la condizione non è soddisfatta.",
    "nl": "Anti-cheat actief! {name} blijft snoozen totdat aan de opsta-voorwaarde is voldaan.",
    "pl": "Anty-oszustwo aktywne! {name} będzie drzemać, dopóki warunek wstawania nie zostanie spełniony.",
    "pt": "Anti-batota ativo! {name} continuará a adiar até que a condição de levantar seja cumprida.",
}


def _get_msg(catalog: dict[str, str], lang: str, **kwargs: Any) -> str:
    """Retrieve localized message template and format with kwargs."""
    prefix = lang.split("-")[0].lower() if lang else "en"
    template = catalog.get(prefix, catalog.get("en", catalog.get("de", "")))
    return template.format(**kwargs)


def _find_alarm(hass: HomeAssistant, name: str | None) -> SmartWakeAlarm | None:
    """Find alarm instance by name or return the first available one when no name was specified."""
    domain_data: dict[str, SmartWakeAlarm] = hass.data.get(DOMAIN, {})
    if not domain_data:
        return None

    if name and name.strip():
        target_name = name.strip().lower()

        # Strip common prepositions / articles if captured in slot
        for prep in (
            "im ", "in der ", "in dem ", "in ", "für das ", "für die ", "für den ", "für ",
            "del ", "della ", "de la ", "dans la ", "dans le ", "dans ", "в ", "na ", "no ", "na "
        ):
            if target_name.startswith(prep):
                target_name = target_name[len(prep):].strip()

        # 1. Direct substring match
        for alarm in domain_data.values():
            alarm_lower = alarm.name.lower()
            if target_name in alarm_lower or alarm_lower in target_name:
                return alarm

        # 2. Multilingual room alias match (e.g. Russian "спальня" <-> German "Schlafzimmer" <-> French "chambre")
        for group in ROOM_ALIASES.values():
            if any(alias in target_name for alias in group):
                for alarm in domain_data.values():
                    alarm_lower = alarm.name.lower()
                    if any(alias in alarm_lower for alias in group):
                        return alarm

        # Explicit alarm name/room requested, but no matching alarm found.
        # Do NOT fall back to a random or unrelated alarm instance!
        return None

    # Default to first available alarm only if no specific name was given
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
            response.async_set_speech(_get_msg(RESPONSES_SET_TIME_NO_SLOT, lang))
            return response

        alarm = _find_alarm(hass, alarm_slot)
        if not alarm:
            response = intent_obj.create_response()
            response.async_set_speech(_get_msg(RESPONSES_ALARM_NOT_FOUND, lang))
            return response

        # Clean and format time to HH:MM
        clean_time = str(time_slot).strip().lower()
        suffixes = (
            "часов", "часа", "час", "uhr", "o'clock", "am", "pm",
            "heures", "heure", "h", "horas", "hora", "ore", "ora",
            "uur", "godzinie", "godzina", "godziny"
        )
        for suffix in suffixes:
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
        response.async_set_speech(_get_msg(RESPONSES_SET_TIME_DONE, lang, name=alarm.name, time=clean_time))
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
            response.async_set_speech(_get_msg(RESPONSES_ALARM_NOT_FOUND, lang))
            return response

        disable_keywords = (
            "aus", "deaktiviert", "off", "disable", "disabled", "ausschalten",
            "отключить", "выключить", "désactiver", "éteindre", "desactivar", "apagar",
            "disattivare", "spegnere", "uit", "deactiveren", "wyłącz", "deaktywuj",
            "desativar", "desligar"
        )
        enable = not any(kw in status_slot for kw in disable_keywords)
        await alarm.async_set_enabled(enable)

        response = intent_obj.create_response()
        catalog = RESPONSES_SET_STATUS_ON if enable else RESPONSES_SET_STATUS_OFF
        response.async_set_speech(_get_msg(catalog, lang, name=alarm.name))
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
            response.async_set_speech(_get_msg(RESPONSES_ALARM_NOT_FOUND, lang))
            return response

        duration = int(duration_slot) if duration_slot and str(duration_slot).isdigit() else None
        res = await alarm.async_snooze(custom_duration=duration)

        response = intent_obj.create_response()
        dur_text = duration or alarm.snooze_duration
        if res:
            response.async_set_speech(_get_msg(RESPONSES_SNOOZE_DONE, lang, duration=dur_text, name=alarm.name))
        else:
            response.async_set_speech(_get_msg(RESPONSES_SNOOZE_FAILED, lang, name=alarm.name))
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
            response.async_set_speech(_get_msg(RESPONSES_ALARM_NOT_FOUND, lang))
            return response

        dismissed = await alarm.async_dismiss()
        response = intent_obj.create_response()
        if dismissed:
            response.async_set_speech(_get_msg(RESPONSES_DISMISS_DONE, lang, name=alarm.name))
        else:
            response.async_set_speech(_get_msg(RESPONSES_DISMISS_ANTI_CHEAT, lang, name=alarm.name))
        return response
