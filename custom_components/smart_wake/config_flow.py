"""Config flow and Options flow for Smart Wake."""
from __future__ import annotations

import logging
from typing import Any

try:
    from homeassistant import config_entries
    from homeassistant.core import callback
    from homeassistant.data_entry_flow import FlowResult
    from homeassistant.helpers.selector import (
        BooleanSelector,
        EntitySelector,
        EntitySelectorConfig,
        NumberSelector,
        NumberSelectorConfig,
        NumberSelectorMode,
        SelectOptionDict,
        SelectSelector,
        SelectSelectorConfig,
        SelectSelectorMode,
        TextSelector,
        TextSelectorConfig,
        TimeSelector,
    )
except Exception:
    class config_entries:
        class ConfigFlow:
            def __init_subclass__(cls, domain=None, **kwargs):
                super().__init_subclass__()
                cls.domain = domain
            def _async_current_entries(self):
                return []
            def async_create_entry(self, title, data):
                return {"type": "create_entry", "title": title, "data": data}
            def async_show_form(self, step_id, data_schema, errors=None):
                return {"type": "form", "step_id": step_id, "data_schema": data_schema, "errors": errors or {}}
            def async_show_menu(self, step_id, menu_options):
                return {"type": "menu", "step_id": step_id, "menu_options": menu_options}

        class OptionsFlow:
            def __init__(self, entry=None):
                self.config_entry = entry
            def async_create_entry(self, title, data):
                return {"type": "create_entry", "title": title, "data": data}
            def async_show_form(self, step_id, data_schema, errors=None):
                return {"type": "form", "step_id": step_id, "data_schema": data_schema, "errors": errors or {}}
            def async_show_menu(self, step_id, menu_options):
                return {"type": "menu", "step_id": step_id, "menu_options": menu_options}

        class ConfigEntry:
            pass
    FlowResult = Any
    def callback(func: Any) -> Any:
        return func
    BooleanSelector = None
    EntitySelector = None
    EntitySelectorConfig = None
    NumberSelector = None
    NumberSelectorConfig = None
    NumberSelectorMode = None
    SelectOptionDict = None
    SelectSelector = None
    SelectSelectorConfig = None
    SelectSelectorMode = None
    TextSelector = None
    TextSelectorConfig = None
    TimeSelector = None

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
        @staticmethod
        def All(*args: Any) -> Any:
            return args[0]
        @staticmethod
        def Range(**kwargs: Any) -> Any:
            return lambda x: x
        @staticmethod
        def In(l: Any) -> Any:
            return lambda x: x

from .const import (
    CALENDAR_BEHAVIOR_NONE,
    CALENDAR_BEHAVIOR_ONLY_IF_EVENT,
    CALENDAR_BEHAVIOR_SKIP_IF_EVENT,
    CONF_CALENDAR_BEHAVIOR,
    CONF_CALENDAR_ENTITY,
    CONF_DAYS,
    CONF_DISMISS_BUTTON_ENTITY,
    CONF_DISMISS_MOTION_ENTITIES,
    CONF_DISMISS_NFC_TAGS,
    CONF_DISMISS_POWER_SENSOR,
    CONF_DISMISS_POWER_THRESHOLD,
    CONF_ENABLED,
    CONF_ESCALATION_COVER_ENTITIES,
    CONF_ESCALATION_COVER_POSITION,
    CONF_ESCALATION_DELAY,
    CONF_ESCALATION_ENABLED,
    CONF_ESCALATION_LIGHT_BRIGHTNESS,
    CONF_ESCALATION_LIGHT_COLD_WHITE,
    CONF_ESCALATION_LIGHT_ENTITIES,
    CONF_ESCALATION_SCRIPT_ENTITY,
    CONF_ESCALATION_VOLUME,
    CONF_MAIN_AUDIO_CONTENT_ID,
    CONF_MAIN_AUDIO_CONTENT_TYPE,
    CONF_MAIN_AUDIO_FADE_DURATION,
    CONF_MAIN_AUDIO_FADE_IN,
    CONF_MAIN_AUDIO_TARGET_VOLUME,
    CONF_MAIN_MEDIA_PLAYER_ENTITIES,
    CONF_MAIN_SCRIPT_ENTITY,
    CONF_MAIN_TTS_ENGINE,
    CONF_MAIN_TTS_ENABLED,
    CONF_MAIN_TTS_MESSAGE,
    CONF_MAX_SNOOZE_COUNT,
    CONF_NAME,
    CONF_PERSON_ENTITIES,
    CONF_PERSON_HOME_REQUIRED,
    CONF_PRE_ALARM_CLIMATE_ENTITIES,
    CONF_PRE_ALARM_CLIMATE_TEMP_DELTA,
    CONF_PRE_ALARM_COVER_ENTITIES,
    CONF_PRE_ALARM_COVER_POSITION,
    CONF_PRE_ALARM_DURATION,
    CONF_PRE_ALARM_ENABLED,
    CONF_PRE_ALARM_LIGHT_END_BRIGHTNESS,
    CONF_PRE_ALARM_LIGHT_ENTITIES,
    CONF_PRE_ALARM_LIGHT_START_BRIGHTNESS,
    CONF_PRE_ALARM_SCRIPT_ENTITY,
    CONF_SLEEP_STAGE_ENTITY,
    CONF_SLEEP_STAGE_VALUES,
    CONF_SLEEP_STAGE_WINDOW,
    CONF_SNOOZE_BUTTON_ENTITY,
    CONF_SNOOZE_DURATION,
    CONF_TIME,
    CONF_WEATHER_RAIN_ENTITY,
    CONF_WEATHER_RAIN_OFFSET,
    CONF_WEATHER_TEMP_ENTITY,
    CONF_WEATHER_TEMP_OFFSET,
    CONF_WEATHER_TEMP_THRESHOLD,
    CONF_WORKDAY_ENTITY,
    CONF_WORKDAY_ONLY,
    DEFAULT_DAYS,
    DEFAULT_DISMISS_POWER_THRESHOLD,
    DEFAULT_ESCALATION_COVER_POSITION,
    DEFAULT_ESCALATION_DELAY,
    DEFAULT_ESCALATION_ENABLED,
    DEFAULT_ESCALATION_LIGHT_BRIGHTNESS,
    DEFAULT_ESCALATION_LIGHT_COLD_WHITE,
    DEFAULT_ESCALATION_VOLUME,
    DEFAULT_MAIN_AUDIO_CONTENT_TYPE,
    DEFAULT_MAIN_AUDIO_FADE_DURATION,
    DEFAULT_MAIN_AUDIO_FADE_IN,
    DEFAULT_MAIN_AUDIO_TARGET_VOLUME,
    DEFAULT_MAIN_TTS_ENABLED,
    DEFAULT_MAIN_TTS_MESSAGE,
    DEFAULT_MAX_SNOOZE_COUNT,
    DEFAULT_NAME,
    DEFAULT_PERSON_HOME_REQUIRED,
    DEFAULT_PRE_ALARM_CLIMATE_TEMP_DELTA,
    DEFAULT_PRE_ALARM_COVER_POSITION,
    DEFAULT_PRE_ALARM_DURATION,
    DEFAULT_PRE_ALARM_ENABLED,
    DEFAULT_PRE_ALARM_LIGHT_END_BRIGHTNESS,
    DEFAULT_PRE_ALARM_LIGHT_START_BRIGHTNESS,
    DEFAULT_SLEEP_STAGE_VALUES,
    DEFAULT_SLEEP_STAGE_WINDOW,
    DEFAULT_SNOOZE_DURATION,
    DEFAULT_TIME,
    DEFAULT_WEATHER_RAIN_OFFSET,
    DEFAULT_WEATHER_TEMP_OFFSET,
    DEFAULT_WEATHER_TEMP_THRESHOLD,
    DEFAULT_WORKDAY_ONLY,
    DOMAIN,
    WEEKDAY_NAMES_DE,
    WEEKDAYS,
)

_LOGGER = logging.getLogger(__name__)

WEEKDAY_OPTIONS = [
    {"value": code, "label": f"{WEEKDAY_NAMES_DE.get(code, code)} ({code.capitalize()})"}
    for code in WEEKDAYS
]

CALENDAR_BEHAVIOR_OPTIONS = [
    {"value": CALENDAR_BEHAVIOR_NONE, "label": "Deaktiviert (Immer wecken)"},
    {"value": CALENDAR_BEHAVIOR_ONLY_IF_EVENT, "label": "Nur wecken wenn Termin aktiv ist"},
    {"value": CALENDAR_BEHAVIOR_SKIP_IF_EVENT, "label": "Wecker überspringen wenn Termin aktiv ist (Urlaub/Ferien)"},
]


class SmartWakeConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Smart Wake."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle the initial setup step."""
        errors: dict[str, str] = {}

        if user_input is not None:
            name = user_input.get(CONF_NAME, DEFAULT_NAME).strip()
            if not name:
                errors["base"] = "invalid_name"
            else:
                # Check for duplicate names
                for entry in self._async_current_entries():
                    if entry.data.get(CONF_NAME, "").lower() == name.lower():
                        errors["base"] = "already_configured"
                        break

            if not errors:
                return self.async_create_entry(
                    title=name,
                    data=user_input,
                )

        schema = vol.Schema(
            {
                vol.Required(CONF_NAME, default="Wecker Schlafzimmer"): str,
                vol.Required(CONF_TIME, default=DEFAULT_TIME): str,
                vol.Required(CONF_ENABLED, default=True): bool,
                vol.Required(CONF_DAYS, default=DEFAULT_DAYS): SelectSelector(
                    SelectSelectorConfig(
                        options=WEEKDAY_OPTIONS,
                        multiple=True,
                        mode=SelectSelectorMode.LIST,
                    )
                ) if SelectSelector else vol.All(cv.ensure_list, [vol.In(WEEKDAYS)])
                if "cv" in globals() else list,
            }
        )

        return self.async_show_form(
            step_id="user",
            data_schema=schema,
            errors=errors,
        )

    @staticmethod
    @callback
    def async_get_options_flow(
        config_entry: config_entries.ConfigEntry,
    ) -> config_entries.OptionsFlow:
        """Create the options flow handler."""
        return SmartWakeOptionsFlowHandler(config_entry)


class SmartWakeOptionsFlowHandler(config_entries.OptionsFlow):
    """Handle options flow for detailed Smart Wake alarm configuration."""

    def __init__(self, config_entry: config_entries.ConfigEntry) -> None:
        """Initialize options flow."""
        self.config_entry = config_entry
        self._options: dict[str, Any] = dict(config_entry.options or config_entry.data)

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Display options navigation menu."""
        return self.async_show_menu(
            step_id="init",
            menu_options=[
                "schedule",
                "conditions",
                "phase1_pre_alarm",
                "phase2_main_alarm",
                "phase3_escalation",
                "snooze_dismiss",
            ],
        )

    # 1. Schedule & Calendar
    async def async_step_schedule(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Configure scheduling, workdays and calendar filters."""
        if user_input is not None:
            self._options.update(user_input)
            return self.async_create_entry(title="", data=self._options)

        schema = vol.Schema(
            {
                vol.Required(
                    CONF_TIME, default=self._options.get(CONF_TIME, DEFAULT_TIME)
                ): str,
                vol.Required(
                    CONF_DAYS, default=self._options.get(CONF_DAYS, DEFAULT_DAYS)
                ): SelectSelector(
                    SelectSelectorConfig(
                        options=WEEKDAY_OPTIONS,
                        multiple=True,
                        mode=SelectSelectorMode.LIST,
                    )
                ) if SelectSelector else list,
                vol.Optional(
                    CONF_WORKDAY_ENTITY,
                    description={"suggested_value": self._options.get(CONF_WORKDAY_ENTITY)},
                ): EntitySelector(
                    EntitySelectorConfig(domain="binary_sensor")
                ) if EntitySelector else str,
                vol.Required(
                    CONF_WORKDAY_ONLY,
                    default=self._options.get(CONF_WORKDAY_ONLY, DEFAULT_WORKDAY_ONLY),
                ): bool,
                vol.Optional(
                    CONF_CALENDAR_ENTITY,
                    description={"suggested_value": self._options.get(CONF_CALENDAR_ENTITY)},
                ): EntitySelector(
                    EntitySelectorConfig(domain="calendar")
                ) if EntitySelector else str,
                vol.Required(
                    CONF_CALENDAR_BEHAVIOR,
                    default=self._options.get(
                        CONF_CALENDAR_BEHAVIOR, CALENDAR_BEHAVIOR_NONE
                    ),
                ): SelectSelector(
                    SelectSelectorConfig(
                        options=CALENDAR_BEHAVIOR_OPTIONS,
                        mode=SelectSelectorMode.DROPDOWN,
                    )
                ) if SelectSelector else str,
            }
        )
        return self.async_show_form(step_id="schedule", data_schema=schema)

    # 2. Presence & Dynamic Sensors (Winter-Offset, Rain, Sleep-Tracker)
    async def async_step_conditions(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Configure presence gating and weather/sleep dynamic shift."""
        if user_input is not None:
            self._options.update(user_input)
            return self.async_create_entry(title="", data=self._options)

        schema = vol.Schema(
            {
                vol.Optional(
                    CONF_PERSON_ENTITIES,
                    description={"suggested_value": self._options.get(CONF_PERSON_ENTITIES, [])},
                ): EntitySelector(
                    EntitySelectorConfig(domain="person", multiple=True)
                ) if EntitySelector else list,
                vol.Required(
                    CONF_PERSON_HOME_REQUIRED,
                    default=self._options.get(
                        CONF_PERSON_HOME_REQUIRED, DEFAULT_PERSON_HOME_REQUIRED
                    ),
                ): bool,
                vol.Optional(
                    CONF_WEATHER_TEMP_ENTITY,
                    description={"suggested_value": self._options.get(CONF_WEATHER_TEMP_ENTITY)},
                ): EntitySelector(
                    EntitySelectorConfig(domain="sensor")
                ) if EntitySelector else str,
                vol.Required(
                    CONF_WEATHER_TEMP_THRESHOLD,
                    default=float(
                        self._options.get(
                            CONF_WEATHER_TEMP_THRESHOLD, DEFAULT_WEATHER_TEMP_THRESHOLD
                        )
                    ),
                ): vol.Coerce(float),
                vol.Required(
                    CONF_WEATHER_TEMP_OFFSET,
                    default=int(
                        self._options.get(
                            CONF_WEATHER_TEMP_OFFSET, DEFAULT_WEATHER_TEMP_OFFSET
                        )
                    ),
                ): vol.Coerce(int),
                vol.Optional(
                    CONF_WEATHER_RAIN_ENTITY,
                    description={"suggested_value": self._options.get(CONF_WEATHER_RAIN_ENTITY)},
                ): EntitySelector(
                    EntitySelectorConfig(domain=["binary_sensor", "sensor"])
                ) if EntitySelector else str,
                vol.Required(
                    CONF_WEATHER_RAIN_OFFSET,
                    default=int(
                        self._options.get(
                            CONF_WEATHER_RAIN_OFFSET, DEFAULT_WEATHER_RAIN_OFFSET
                        )
                    ),
                ): vol.Coerce(int),
                vol.Optional(
                    CONF_SLEEP_STAGE_ENTITY,
                    description={"suggested_value": self._options.get(CONF_SLEEP_STAGE_ENTITY)},
                ): EntitySelector(
                    EntitySelectorConfig(domain="sensor")
                ) if EntitySelector else str,
                vol.Required(
                    CONF_SLEEP_STAGE_WINDOW,
                    default=int(
                        self._options.get(
                            CONF_SLEEP_STAGE_WINDOW, DEFAULT_SLEEP_STAGE_WINDOW
                        )
                    ),
                ): vol.Coerce(int),
            }
        )
        return self.async_show_form(step_id="conditions", data_schema=schema)

    # 3. Phase 1: Pre-Alarm
    async def async_step_phase1_pre_alarm(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Configure Phase 1: Pre-Alarm soft wake actions."""
        if user_input is not None:
            self._options.update(user_input)
            return self.async_create_entry(title="", data=self._options)

        schema = vol.Schema(
            {
                vol.Required(
                    CONF_PRE_ALARM_ENABLED,
                    default=self._options.get(
                        CONF_PRE_ALARM_ENABLED, DEFAULT_PRE_ALARM_ENABLED
                    ),
                ): bool,
                vol.Required(
                    CONF_PRE_ALARM_DURATION,
                    default=int(
                        self._options.get(
                            CONF_PRE_ALARM_DURATION, DEFAULT_PRE_ALARM_DURATION
                        )
                    ),
                ): vol.Coerce(int),
                vol.Optional(
                    CONF_PRE_ALARM_LIGHT_ENTITIES,
                    description={"suggested_value": self._options.get(CONF_PRE_ALARM_LIGHT_ENTITIES, [])},
                ): EntitySelector(
                    EntitySelectorConfig(domain="light", multiple=True)
                ) if EntitySelector else list,
                vol.Required(
                    CONF_PRE_ALARM_LIGHT_START_BRIGHTNESS,
                    default=int(
                        self._options.get(
                            CONF_PRE_ALARM_LIGHT_START_BRIGHTNESS,
                            DEFAULT_PRE_ALARM_LIGHT_START_BRIGHTNESS,
                        )
                    ),
                ): vol.All(vol.Coerce(int), vol.Range(min=1, max=100)),
                vol.Required(
                    CONF_PRE_ALARM_LIGHT_END_BRIGHTNESS,
                    default=int(
                        self._options.get(
                            CONF_PRE_ALARM_LIGHT_END_BRIGHTNESS,
                            DEFAULT_PRE_ALARM_LIGHT_END_BRIGHTNESS,
                        )
                    ),
                ): vol.All(vol.Coerce(int), vol.Range(min=1, max=100)),
                vol.Optional(
                    CONF_PRE_ALARM_CLIMATE_ENTITIES,
                    description={"suggested_value": self._options.get(CONF_PRE_ALARM_CLIMATE_ENTITIES, [])},
                ): EntitySelector(
                    EntitySelectorConfig(domain="climate", multiple=True)
                ) if EntitySelector else list,
                vol.Required(
                    CONF_PRE_ALARM_CLIMATE_TEMP_DELTA,
                    default=float(
                        self._options.get(
                            CONF_PRE_ALARM_CLIMATE_TEMP_DELTA,
                            DEFAULT_PRE_ALARM_CLIMATE_TEMP_DELTA,
                        )
                    ),
                ): vol.Coerce(float),
                vol.Optional(
                    CONF_PRE_ALARM_COVER_ENTITIES,
                    description={"suggested_value": self._options.get(CONF_PRE_ALARM_COVER_ENTITIES, [])},
                ): EntitySelector(
                    EntitySelectorConfig(domain="cover", multiple=True)
                ) if EntitySelector else list,
                vol.Required(
                    CONF_PRE_ALARM_COVER_POSITION,
                    default=int(
                        self._options.get(
                            CONF_PRE_ALARM_COVER_POSITION,
                            DEFAULT_PRE_ALARM_COVER_POSITION,
                        )
                    ),
                ): vol.All(vol.Coerce(int), vol.Range(min=0, max=100)),
                vol.Optional(
                    CONF_PRE_ALARM_SCRIPT_ENTITY,
                    description={"suggested_value": self._options.get(CONF_PRE_ALARM_SCRIPT_ENTITY)},
                ): EntitySelector(
                    EntitySelectorConfig(domain="script")
                ) if EntitySelector else str,
            }
        )
        return self.async_show_form(step_id="phase1_pre_alarm", data_schema=schema)

    # 4. Phase 2: Main Alarm
    async def async_step_phase2_main_alarm(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Configure Phase 2: Main Alarm audio, TTS and script actions."""
        if user_input is not None:
            self._options.update(user_input)
            return self.async_create_entry(title="", data=self._options)

        schema = vol.Schema(
            {
                vol.Optional(
                    CONF_MAIN_MEDIA_PLAYER_ENTITIES,
                    description={"suggested_value": self._options.get(CONF_MAIN_MEDIA_PLAYER_ENTITIES, [])},
                ): EntitySelector(
                    EntitySelectorConfig(domain="media_player", multiple=True)
                ) if EntitySelector else list,
                vol.Optional(
                    CONF_MAIN_AUDIO_CONTENT_ID,
                    description={"suggested_value": self._options.get(CONF_MAIN_AUDIO_CONTENT_ID, "")},
                ): str,
                vol.Required(
                    CONF_MAIN_AUDIO_FADE_IN,
                    default=self._options.get(
                        CONF_MAIN_AUDIO_FADE_IN, DEFAULT_MAIN_AUDIO_FADE_IN
                    ),
                ): bool,
                vol.Required(
                    CONF_MAIN_AUDIO_FADE_DURATION,
                    default=int(
                        self._options.get(
                            CONF_MAIN_AUDIO_FADE_DURATION,
                            DEFAULT_MAIN_AUDIO_FADE_DURATION,
                        )
                    ),
                ): vol.Coerce(int),
                vol.Required(
                    CONF_MAIN_AUDIO_TARGET_VOLUME,
                    default=float(
                        self._options.get(
                            CONF_MAIN_AUDIO_TARGET_VOLUME,
                            DEFAULT_MAIN_AUDIO_TARGET_VOLUME,
                        )
                    ),
                ): vol.All(vol.Coerce(float), vol.Range(min=0.05, max=1.0)),
                vol.Required(
                    CONF_MAIN_TTS_ENABLED,
                    default=self._options.get(
                        CONF_MAIN_TTS_ENABLED, DEFAULT_MAIN_TTS_ENABLED
                    ),
                ): bool,
                vol.Required(
                    CONF_MAIN_TTS_MESSAGE,
                    default=self._options.get(
                        CONF_MAIN_TTS_MESSAGE, DEFAULT_MAIN_TTS_MESSAGE
                    ),
                ): str,
                vol.Optional(
                    CONF_MAIN_SCRIPT_ENTITY,
                    description={"suggested_value": self._options.get(CONF_MAIN_SCRIPT_ENTITY)},
                ): EntitySelector(
                    EntitySelectorConfig(domain="script")
                ) if EntitySelector else str,
            }
        )
        return self.async_show_form(step_id="phase2_main_alarm", data_schema=schema)

    # 5. Phase 3: Escalation
    async def async_step_phase3_escalation(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Configure Phase 3: Escalation mode anti-oversleep."""
        if user_input is not None:
            self._options.update(user_input)
            return self.async_create_entry(title="", data=self._options)

        schema = vol.Schema(
            {
                vol.Required(
                    CONF_ESCALATION_ENABLED,
                    default=self._options.get(
                        CONF_ESCALATION_ENABLED, DEFAULT_ESCALATION_ENABLED
                    ),
                ): bool,
                vol.Required(
                    CONF_ESCALATION_DELAY,
                    default=int(
                        self._options.get(
                            CONF_ESCALATION_DELAY, DEFAULT_ESCALATION_DELAY
                        )
                    ),
                ): vol.Coerce(int),
                vol.Required(
                    CONF_ESCALATION_VOLUME,
                    default=float(
                        self._options.get(
                            CONF_ESCALATION_VOLUME, DEFAULT_ESCALATION_VOLUME
                        )
                    ),
                ): vol.All(vol.Coerce(float), vol.Range(min=0.1, max=1.0)),
                vol.Optional(
                    CONF_ESCALATION_LIGHT_ENTITIES,
                    description={"suggested_value": self._options.get(CONF_ESCALATION_LIGHT_ENTITIES, [])},
                ): EntitySelector(
                    EntitySelectorConfig(domain="light", multiple=True)
                ) if EntitySelector else list,
                vol.Required(
                    CONF_ESCALATION_LIGHT_BRIGHTNESS,
                    default=int(
                        self._options.get(
                            CONF_ESCALATION_LIGHT_BRIGHTNESS,
                            DEFAULT_ESCALATION_LIGHT_BRIGHTNESS,
                        )
                    ),
                ): vol.All(vol.Coerce(int), vol.Range(min=10, max=100)),
                vol.Optional(
                    CONF_ESCALATION_COVER_ENTITIES,
                    description={"suggested_value": self._options.get(CONF_ESCALATION_COVER_ENTITIES, [])},
                ): EntitySelector(
                    EntitySelectorConfig(domain="cover", multiple=True)
                ) if EntitySelector else list,
                vol.Required(
                    CONF_ESCALATION_COVER_POSITION,
                    default=int(
                        self._options.get(
                            CONF_ESCALATION_COVER_POSITION,
                            DEFAULT_ESCALATION_COVER_POSITION,
                        )
                    ),
                ): vol.All(vol.Coerce(int), vol.Range(min=0, max=100)),
                vol.Optional(
                    CONF_ESCALATION_SCRIPT_ENTITY,
                    description={"suggested_value": self._options.get(CONF_ESCALATION_SCRIPT_ENTITY)},
                ): EntitySelector(
                    EntitySelectorConfig(domain="script")
                ) if EntitySelector else str,
            }
        )
        return self.async_show_form(step_id="phase3_escalation", data_schema=schema)

    # 6. Snooze & Dismiss Anti-Cheat
    async def async_step_snooze_dismiss(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Configure snooze duration, max snooze limit and anti-cheat dismiss triggers."""
        if user_input is not None:
            self._options.update(user_input)
            return self.async_create_entry(title="", data=self._options)

        schema = vol.Schema(
            {
                vol.Required(
                    CONF_SNOOZE_DURATION,
                    default=int(
                        self._options.get(CONF_SNOOZE_DURATION, DEFAULT_SNOOZE_DURATION)
                    ),
                ): vol.All(vol.Coerce(int), vol.Range(min=1, max=60)),
                vol.Required(
                    CONF_MAX_SNOOZE_COUNT,
                    default=int(
                        self._options.get(
                            CONF_MAX_SNOOZE_COUNT, DEFAULT_MAX_SNOOZE_COUNT
                        )
                    ),
                ): vol.All(vol.Coerce(int), vol.Range(min=0, max=10)),
                vol.Optional(
                    CONF_DISMISS_BUTTON_ENTITY,
                    description={"suggested_value": self._options.get(CONF_DISMISS_BUTTON_ENTITY)},
                ): EntitySelector(
                    EntitySelectorConfig(domain=["event", "sensor", "binary_sensor"])
                ) if EntitySelector else str,
                vol.Optional(
                    CONF_SNOOZE_BUTTON_ENTITY,
                    description={"suggested_value": self._options.get(CONF_SNOOZE_BUTTON_ENTITY)},
                ): EntitySelector(
                    EntitySelectorConfig(domain=["event", "sensor", "binary_sensor"])
                ) if EntitySelector else str,
                vol.Optional(
                    CONF_DISMISS_MOTION_ENTITIES,
                    description={"suggested_value": self._options.get(CONF_DISMISS_MOTION_ENTITIES, [])},
                ): EntitySelector(
                    EntitySelectorConfig(domain="binary_sensor", multiple=True)
                ) if EntitySelector else list,
                vol.Optional(
                    CONF_DISMISS_POWER_SENSOR,
                    description={"suggested_value": self._options.get(CONF_DISMISS_POWER_SENSOR)},
                ): EntitySelector(
                    EntitySelectorConfig(domain="sensor")
                ) if EntitySelector else str,
                vol.Required(
                    CONF_DISMISS_POWER_THRESHOLD,
                    default=float(
                        self._options.get(
                            CONF_DISMISS_POWER_THRESHOLD,
                            DEFAULT_DISMISS_POWER_THRESHOLD,
                        )
                    ),
                ): vol.Coerce(float),
            }
        )
        return self.async_show_form(step_id="snooze_dismiss", data_schema=schema)
