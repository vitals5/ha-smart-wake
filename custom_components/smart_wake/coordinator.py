"""Alarm Coordinator and State Machine for Smart Wake."""
from __future__ import annotations

import asyncio
from datetime import datetime, time as dt_time, timedelta
import logging
from typing import Any, Callable

try:
    from homeassistant.const import (
        EVENT_HOMEASSISTANT_STARTED,
        STATE_HOME,
        STATE_NOT_HOME,
        STATE_OFF,
        STATE_ON,
        STATE_UNAVAILABLE,
        STATE_UNKNOWN,
    )
    from homeassistant.core import CALLBACK_TYPE, Event, HomeAssistant, callback
    from homeassistant.helpers.dispatcher import async_dispatcher_send
    from homeassistant.helpers.event import (
        async_call_later,
        async_track_point_in_utc_time,
        async_track_state_change_event,
        async_track_time_interval,
    )
    from homeassistant.util import dt as dt_util
except Exception:
    # Fallbacks for unit testing / mock environments
    EVENT_HOMEASSISTANT_STARTED = "homeassistant_started"
    STATE_HOME = "home"
    STATE_NOT_HOME = "not_home"
    STATE_OFF = "off"
    STATE_ON = "on"
    STATE_UNAVAILABLE = "unavailable"
    STATE_UNKNOWN = "unknown"
    CALLBACK_TYPE = Any
    Event = Any
    HomeAssistant = Any

    def callback(func: Any) -> Any:
        return func

    def async_dispatcher_send(hass: Any, signal: str, *args: Any) -> None:
        pass

    def async_call_later(hass: Any, delay: float, action: Any) -> Any:
        return lambda: None

    def async_track_point_in_utc_time(hass: Any, action: Any, point_in_time: Any) -> Any:
        return lambda: None

    def async_track_state_change_event(hass: Any, entity_ids: Any, action: Any) -> Any:
        return lambda: None

    def async_track_time_interval(hass: Any, action: Any, interval: Any) -> Any:
        return lambda: None

    class MockDtUtil:
        @staticmethod
        def now() -> datetime:
            return datetime.now().astimezone()

        @staticmethod
        def utcnow() -> datetime:
            return datetime.now(timezone.utc)

        @staticmethod
        def as_utc(d: datetime) -> datetime:
            return d

        @staticmethod
        def as_local(d: datetime) -> datetime:
            return d

    dt_util = MockDtUtil()

from .const import (
    ALL_PHASES,
    ALL_STATUSES,
    CALENDAR_BEHAVIOR_NONE,
    CALENDAR_BEHAVIOR_ONLY_IF_EVENT,
    CALENDAR_BEHAVIOR_SKIP_IF_EVENT,
    CONF_CALENDAR_BEHAVIOR,
    CONF_CALENDAR_ENTITY,
    CONF_DAYS,
    CONF_DISMISS_BUTTON_ENTITY,
    CONF_DISMISS_BUTTON_EVENT,
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
    CONF_ESCALATION_VOLUME_FADE_DURATION,
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
    CONF_SNOOZE_BUTTON_EVENT,
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
    DEFAULT_ESCALATION_VOLUME_FADE_DURATION,
    DEFAULT_MAIN_AUDIO_CONTENT_TYPE,
    DEFAULT_MAIN_AUDIO_FADE_DURATION,
    DEFAULT_MAIN_AUDIO_FADE_IN,
    DEFAULT_MAIN_AUDIO_TARGET_VOLUME,
    DEFAULT_MAIN_TTS_ENABLED,
    DEFAULT_MAIN_TTS_MESSAGE,
    DEFAULT_MAX_SNOOZE_COUNT,
    DEFAULT_NAME,
    DEFAULT_PERSON_HOME_REQUIRED,
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
    DEFAULT_FULL_TEST_SNOOZE_SECONDS,
    DOMAIN,
    EVENT_SMART_WAKE_ALARM_TRIGGERED,
    EVENT_SMART_WAKE_ANTI_CHEAT_BLOCKED,
    EVENT_SMART_WAKE_DISMISSED,
    EVENT_SMART_WAKE_ESCALATION_STARTED,
    EVENT_SMART_WAKE_PRE_ALARM_STARTED,
    EVENT_SMART_WAKE_SKIPPED,
    EVENT_SMART_WAKE_SNOOZED,
    EVENT_SMART_WAKE_STATUS_CHANGED,
    PHASE_ESCALATION,
    PHASE_MAIN_ALARM,
    PHASE_NONE,
    PHASE_PRE_ALARM,
    SIGNAL_SMART_WAKE_ALL_UPDATED,
    SIGNAL_SMART_WAKE_UPDATED,
    STATUS_DISMISSED,
    STATUS_IDLE,
    STATUS_PRE_ALARM,
    STATUS_RINGING,
    STATUS_SKIPPED,
    STATUS_SNOOZED,
    TEST_DRY_RUN_ESCALATION_SECONDS,
    TEST_DRY_RUN_MAIN_SECONDS,
    TEST_DRY_RUN_PRE_ALARM_SECONDS,
    TEST_DRY_RUN_TOTAL_SECONDS,
    WEEKDAYS,
)

_LOGGER = logging.getLogger(__name__)


class SmartWakeAlarm:
    """Coordinator and state engine for a single Smart Wake instance."""

    def __init__(self, hass: HomeAssistant, entry_id: str, config: dict[str, Any]) -> None:
        """Initialize the Smart Wake instance."""
        self.hass = hass
        self.entry_id = entry_id
        self._config: dict[str, Any] = dict(config)

        # Core state
        self._name: str = self._config.get(CONF_NAME, DEFAULT_NAME)
        self._enabled: bool = bool(self._config.get(CONF_ENABLED, True))
        self._time_str: str = self._config.get(CONF_TIME, DEFAULT_TIME)
        self._days: list[str] = list(self._config.get(CONF_DAYS, DEFAULT_DAYS))

        self._status: str = STATUS_IDLE
        self._active_phase: str = PHASE_NONE
        self._snooze_count: int = 0
        self._skip_next: bool = False
        self._skip_reason: str = ""

        # Calculated timestamps
        self._next_alarm: datetime | None = None
        self._pre_alarm_time: datetime | None = None
        self._dynamic_offset_minutes: int = 0
        self._offset_reasons: list[str] = []

        # Timer & listener unsubs
        self._unsub_schedule: CALLBACK_TYPE | None = None
        self._unsub_phase_timer: CALLBACK_TYPE | None = None
        self._unsub_dry_run: CALLBACK_TYPE | None = None
        self._unsub_listeners: list[CALLBACK_TYPE] = []
        self._fade_tasks: list[asyncio.Task] = []

        # Testing state
        self._is_dry_run: bool = False
        self._dry_run_progress: int = 0
        self._is_full_test: bool = False
        self._full_test_snooze_seconds: int | None = None

        # Anti-cheat tracking
        self._anti_cheat_nfc_scanned: bool = False
        self._snooze_until: datetime | None = None

    # -------------------------------------------------------------------------
    # Properties
    # -------------------------------------------------------------------------
    @property
    def name(self) -> str:
        """Return the alarm instance name."""
        return self._name

    @property
    def enabled(self) -> bool:
        """Return whether alarm is enabled."""
        return self._enabled

    @property
    def time_str(self) -> str:
        """Return target time string (HH:MM)."""
        return self._time_str

    @property
    def days(self) -> list[str]:
        """Return active days of week."""
        return self._days

    @property
    def status(self) -> str:
        """Return current alarm status."""
        return self._status

    @property
    def active_phase(self) -> str:
        """Return current active phase."""
        return self._active_phase

    @property
    def snooze_count(self) -> int:
        """Return current snooze count."""
        return self._snooze_count

    @property
    def snooze_duration(self) -> int:
        """Return snooze duration in minutes."""
        return int(self._config.get(CONF_SNOOZE_DURATION, DEFAULT_SNOOZE_DURATION))

    @property
    def max_snooze_count(self) -> int:
        """Return max snooze count."""
        return int(self._config.get(CONF_MAX_SNOOZE_COUNT, DEFAULT_MAX_SNOOZE_COUNT))

    @property
    def pre_alarm_duration(self) -> int:
        """Return pre-alarm duration in minutes."""
        return int(self._config.get(CONF_PRE_ALARM_DURATION, DEFAULT_PRE_ALARM_DURATION))

    @property
    def next_alarm(self) -> datetime | None:
        """Return next scheduled alarm datetime."""
        return self._next_alarm

    @property
    def pre_alarm_time(self) -> datetime | None:
        """Return pre-alarm start datetime."""
        return self._pre_alarm_time

    @property
    def dynamic_offset_minutes(self) -> int:
        """Return calculated early offset in minutes."""
        return self._dynamic_offset_minutes

    @property
    def offset_reasons(self) -> list[str]:
        """Return human-readable offset explanations."""
        return list(self._offset_reasons)

    @property
    def skip_next(self) -> bool:
        """Return skip next flag."""
        return self._skip_next

    @property
    def skip_reason(self) -> str:
        """Return reason why alarm was skipped."""
        return self._skip_reason

    @property
    def is_dry_run(self) -> bool:
        """Return whether dry run is active."""
        return self._is_dry_run

    @property
    def dry_run_progress(self) -> int:
        """Return dry run test progress in seconds (0-30)."""
        return self._dry_run_progress

    @property
    def is_full_test(self) -> bool:
        """Return whether full real-time test run is active."""
        return self._is_full_test

    @property
    def is_testing(self) -> bool:
        """Return whether any test run (dry-run or full test) is active."""
        return self._is_dry_run or self._is_full_test

    @property
    def snooze_until(self) -> datetime | None:
        """Return when snooze ends, if snoozed."""
        return self._snooze_until

    def has_anti_cheat_configured(self) -> bool:
        """Return True if any anti-cheat condition is configured."""
        motion = self._config.get(CONF_DISMISS_MOTION_ENTITIES)
        if motion:
            if isinstance(motion, list) and any(str(m).strip() for m in motion):
                return True
            elif isinstance(motion, str) and motion.strip():
                return True

        power = self._config.get(CONF_DISMISS_POWER_SENSOR)
        if power and str(power).strip():
            return True

        nfc = self._config.get(CONF_DISMISS_NFC_TAGS)
        if nfc:
            if isinstance(nfc, list) and any(str(t).strip() for t in nfc):
                return True
            elif isinstance(nfc, str) and nfc.strip():
                return True

        return False

    def is_anti_cheat_fulfilled(self) -> bool:
        """Check if any configured anti-cheat condition is currently met."""
        if not hasattr(self.hass, "states"):
            return False

        # 1. Motion sensors (bathroom / kitchen)
        motion_entities = self._config.get(CONF_DISMISS_MOTION_ENTITIES, [])
        if isinstance(motion_entities, str):
            motion_entities = [m.strip() for m in motion_entities.split(",") if m.strip()]
        for ent_id in motion_entities:
            if not ent_id:
                continue
            st = self.hass.states.get(ent_id)
            if st and str(st.state).lower() in (STATE_ON, "on", "detected", "motion", "true"):
                _LOGGER.info(
                    "Smart Wake [%s] Anti-Cheat verified via motion sensor %s (state: %s)",
                    self._name,
                    ent_id,
                    st.state,
                )
                return True

        # 2. Power sensor (coffee machine / bathroom light > threshold)
        power_sensor = self._config.get(CONF_DISMISS_POWER_SENSOR)
        if power_sensor and str(power_sensor).strip():
            st = self.hass.states.get(str(power_sensor).strip())
            if st:
                try:
                    threshold = float(
                        self._config.get(
                            CONF_DISMISS_POWER_THRESHOLD, DEFAULT_DISMISS_POWER_THRESHOLD
                        )
                    )
                    val = float(st.state)
                    if val >= threshold:
                        _LOGGER.info(
                            "Smart Wake [%s] Anti-Cheat verified via power sensor %s (%.1fW >= %.1fW)",
                            self._name,
                            power_sensor,
                            val,
                            threshold,
                        )
                        return True
                except (ValueError, TypeError):
                    pass

        # 3. NFC Tag scanned recently during this cycle
        if getattr(self, "_anti_cheat_nfc_scanned", False):
            _LOGGER.info("Smart Wake [%s] Anti-Cheat verified via NFC tag scan", self._name)
            return True

        return False

    @property
    def config(self) -> dict[str, Any]:
        """Return current configuration copy."""
        return dict(self._config)

    # -------------------------------------------------------------------------
    # Lifecycle
    # -------------------------------------------------------------------------
    async def async_setup(self) -> None:
        """Set up listeners and schedule initial calculation."""
        _LOGGER.debug("Setting up Smart Wake alarm [%s]", self._name)
        self._setup_dynamic_sensors_listener()
        await self.async_recalculate_schedule()

    async def async_unload(self) -> None:
        """Clean up all running timers and listeners."""
        _LOGGER.debug("Unloading Smart Wake alarm [%s]", self._name)
        self._cancel_schedule()
        self._cancel_phase_timer()
        self._cancel_dry_run()
        self._cleanup_listeners()
        self._cancel_fade_tasks()

    def update_config(self, new_config: dict[str, Any]) -> None:
        """Update instance configuration and recalculate schedule."""
        self._config.update(new_config)
        self._name = self._config.get(CONF_NAME, self._name)
        self._enabled = bool(self._config.get(CONF_ENABLED, self._enabled))
        self._time_str = self._config.get(CONF_TIME, self._time_str)
        self._days = list(self._config.get(CONF_DAYS, self._days))
        self.hass.async_create_task(self.async_recalculate_schedule())

    # -------------------------------------------------------------------------
    # Schedule & Next Alarm Calculation
    # -------------------------------------------------------------------------
    async def async_recalculate_schedule(self) -> None:
        """Calculate next alarm and pre-alarm times based on rules and sensors."""
        self._cancel_schedule()

        if not self._enabled:
            self._next_alarm = None
            self._pre_alarm_time = None
            self._dynamic_offset_minutes = 0
            self._offset_reasons = []
            self._notify_update()
            return

        now = dt_util.now()
        target_hour, target_minute = self._parse_time(self._time_str)

        # 1. Compute dynamic weather offset
        offset_mins, reasons = self._calculate_dynamic_offset()
        self._dynamic_offset_minutes = offset_mins
        self._offset_reasons = reasons

        pre_alarm_enabled = self._config.get(CONF_PRE_ALARM_ENABLED, DEFAULT_PRE_ALARM_ENABLED)
        pre_alarm_duration = self.pre_alarm_duration if pre_alarm_enabled else 0

        # 2. Find next matching active day (check up to 8 days in advance)
        found_target: datetime | None = None
        found_pre_alarm: datetime | None = None

        for day_offset in range(8):
            candidate_date = (now + timedelta(days=day_offset)).date()
            weekday_code = WEEKDAYS[candidate_date.weekday()]

            if weekday_code not in self._days:
                continue

            # Candidate target time on that date
            candidate_target = datetime.combine(
                candidate_date,
                dt_time(hour=target_hour, minute=target_minute),
                tzinfo=now.tzinfo,
            )

            # Apply early weather offset
            shifted_target = candidate_target - timedelta(minutes=offset_mins)
            shifted_pre_alarm = shifted_target - timedelta(minutes=pre_alarm_duration)

            # Determine check threshold: if pre-alarm enabled, must be in future;
            # otherwise shifted_target must be in future.
            threshold = shifted_pre_alarm if pre_alarm_enabled else shifted_target

            if threshold > now:
                found_target = shifted_target
                found_pre_alarm = shifted_pre_alarm
                break

        self._next_alarm = found_target
        self._pre_alarm_time = found_pre_alarm if pre_alarm_enabled else found_target

        if self._next_alarm and self._pre_alarm_time:
            _LOGGER.info(
                "Smart Wake [%s] next scheduled: Main=%s, PreAlarm=%s (Offset: -%dm, Reasons: %s)",
                self._name,
                self._next_alarm.isoformat(),
                self._pre_alarm_time.isoformat(),
                self._dynamic_offset_minutes,
                ", ".join(self._offset_reasons) or "None",
            )
            self._arm_schedule_timer()

        self._notify_update()

    def _parse_time(self, time_val: str) -> tuple[int, int]:
        """Parse HH:MM string safely."""
        try:
            parts = str(time_val).strip().split(":")
            return int(parts[0]), int(parts[1])
        except Exception:
            return 6, 30

    def _calculate_dynamic_offset(self) -> tuple[int, list[str]]:
        """Evaluate outdoor temperature and precipitation to compute early wake offset."""
        total_offset = 0
        reasons: list[str] = []

        # Outside temperature check
        temp_entity = self._config.get(CONF_WEATHER_TEMP_ENTITY)
        if temp_entity and hasattr(self.hass, "states"):
            temp_state = self.hass.states.get(temp_entity)
            if temp_state and temp_state.state not in (STATE_UNAVAILABLE, STATE_UNKNOWN):
                try:
                    current_temp = float(temp_state.state)
                    threshold = float(
                        self._config.get(
                            CONF_WEATHER_TEMP_THRESHOLD, DEFAULT_WEATHER_TEMP_THRESHOLD
                        )
                    )
                    if current_temp <= threshold:
                        offset = int(
                            self._config.get(
                                CONF_WEATHER_TEMP_OFFSET, DEFAULT_WEATHER_TEMP_OFFSET
                            )
                        )
                        total_offset += offset
                        reasons.append(
                            f"Frost/Kälte ({current_temp:.1f}°C ≤ {threshold}°C: -{offset}m)"
                        )
                except (ValueError, TypeError):
                    pass

        # Rain / precipitation check
        rain_entity = self._config.get(CONF_WEATHER_RAIN_ENTITY)
        if rain_entity and hasattr(self.hass, "states"):
            rain_state = self.hass.states.get(rain_entity)
            if rain_state and rain_state.state not in (STATE_UNAVAILABLE, STATE_UNKNOWN):
                is_rain = False
                if rain_state.state in (STATE_ON, "true", "True"):
                    is_rain = True
                else:
                    try:
                        if float(rain_state.state) > 0.0:
                            is_rain = True
                    except (ValueError, TypeError):
                        pass

                if is_rain:
                    offset = int(
                        self._config.get(
                            CONF_WEATHER_RAIN_OFFSET, DEFAULT_WEATHER_RAIN_OFFSET
                        )
                    )
                    total_offset += offset
                    reasons.append(f"Regen/Niederschlag aktiv (-{offset}m)")

        return total_offset, reasons

    def _setup_dynamic_sensors_listener(self) -> None:
        """Listen to sensor changes that affect schedule recalculation."""
        sensor_entities: list[str] = []
        for key in (CONF_WEATHER_TEMP_ENTITY, CONF_WEATHER_RAIN_ENTITY):
            ent = self._config.get(key)
            if ent and isinstance(ent, str):
                sensor_entities.append(ent)

        if sensor_entities and hasattr(self.hass, "states"):
            @callback
            def _sensor_state_changed(_event: Event) -> None:
                self.hass.async_create_task(self.async_recalculate_schedule())

            try:
                unsub = async_track_state_change_event(
                    self.hass, sensor_entities, _sensor_state_changed
                )
                self._unsub_listeners.append(unsub)
            except Exception as err:
                _LOGGER.debug("Could not attach state change tracker: %s", err)

    def _arm_schedule_timer(self) -> None:
        """Arm exact point-in-time callback for pre-alarm or main alarm."""
        self._cancel_schedule()
        if not self._pre_alarm_time:
            return

        now = dt_util.now()
        delay_seconds = (self._pre_alarm_time - now).total_seconds()
        if delay_seconds < 0:
            delay_seconds = 0

        @callback
        def _schedule_fired(_point: Any = None) -> None:
            self.hass.async_create_task(self.async_on_schedule_fired())

        try:
            self._unsub_schedule = async_call_later(self.hass, delay_seconds, _schedule_fired)
        except Exception:
            try:
                self._unsub_schedule = async_track_point_in_utc_time(
                    self.hass, _schedule_fired, dt_util.as_utc(self._pre_alarm_time)
                )
            except Exception as err:
                _LOGGER.error("Failed to arm schedule timer: %s", err)

    # -------------------------------------------------------------------------
    # Condition Pipeline
    # -------------------------------------------------------------------------
    async def async_evaluate_conditions(self) -> tuple[bool, str]:
        """Evaluate condition pipeline before triggering alarm."""
        # 1. Manual skip next check
        if self._skip_next:
            self._skip_next = False
            return False, "Manuell übersprungen (Skip Next)"

        # 2. Workday check
        workday_only = self._config.get(CONF_WORKDAY_ONLY, DEFAULT_WORKDAY_ONLY)
        workday_entity = self._config.get(CONF_WORKDAY_ENTITY)
        if workday_only and workday_entity and hasattr(self.hass, "states"):
            wd_state = self.hass.states.get(workday_entity)
            if wd_state and wd_state.state not in (STATE_ON, "true", "True"):
                return False, f"Kein Werktag laut {workday_entity} ({wd_state.state})"

        # 3. Calendar check
        calendar_entity = self._config.get(CONF_CALENDAR_ENTITY)
        calendar_behavior = self._config.get(CONF_CALENDAR_BEHAVIOR, CALENDAR_BEHAVIOR_NONE)
        if calendar_entity and calendar_behavior != CALENDAR_BEHAVIOR_NONE and hasattr(self.hass, "states"):
            cal_state = self.hass.states.get(calendar_entity)
            is_active = cal_state and cal_state.state in (STATE_ON, "true", "True")
            if calendar_behavior == CALENDAR_BEHAVIOR_ONLY_IF_EVENT and not is_active:
                return False, f"Kein passender Termin in Kalender {calendar_entity}"
            if calendar_behavior == CALENDAR_BEHAVIOR_SKIP_IF_EVENT and is_active:
                return False, f"Termin in Kalender {calendar_entity} aktiv (z.B. Urlaub/Ferien)"

        # 4. Person presence tracking
        person_required = self._config.get(
            CONF_PERSON_HOME_REQUIRED, DEFAULT_PERSON_HOME_REQUIRED
        )
        person_entities = self._config.get(CONF_PERSON_ENTITIES, [])
        if isinstance(person_entities, str):
            person_entities = [person_entities]

        if person_required and person_entities and hasattr(self.hass, "states"):
            any_home = False
            for p_ent in person_entities:
                p_state = self.hass.states.get(p_ent)
                if p_state and p_state.state == STATE_HOME:
                    any_home = True
                    break
            if not any_home:
                return False, f"Zugewiesene Person(en) ({', '.join(person_entities)}) nicht zu Hause"

        return True, ""

    # -------------------------------------------------------------------------
    # State Machine & Alarm Run Cycle
    # -------------------------------------------------------------------------
    async def async_on_schedule_fired(self) -> None:
        """Handle wake timer firing: check conditions, then start Pre-Alarm or Main Alarm."""
        if not self._enabled:
            return

        # Run condition pipeline
        allowed, reason = await self.async_evaluate_conditions()
        if not allowed:
            _LOGGER.info("Smart Wake [%s] skipped: %s", self._name, reason)
            self._status = STATUS_SKIPPED
            self._skip_reason = reason
            self._active_phase = PHASE_NONE
            self._fire_event(EVENT_SMART_WAKE_SKIPPED, {"reason": reason})
            self._notify_update()
            # Reschedule for next day after brief status display
            await asyncio.sleep(5)
            self._status = STATUS_IDLE
            await self.async_recalculate_schedule()
            return

        # Start phase progression
        pre_alarm_enabled = self._config.get(CONF_PRE_ALARM_ENABLED, DEFAULT_PRE_ALARM_ENABLED)
        now = dt_util.now()

        # If pre-alarm enabled and target is still in future
        if pre_alarm_enabled and self._next_alarm and self._next_alarm > now:
            await self.async_start_pre_alarm()
        else:
            await self.async_start_main_alarm()

    async def async_start_pre_alarm(self) -> None:
        """Trigger Phase 1: Pre-Alarm (Sanftes Wecken)."""
        _LOGGER.info("Smart Wake [%s] starting Phase 1: Pre-Alarm", self._name)
        self._status = STATUS_PRE_ALARM
        self._active_phase = PHASE_PRE_ALARM
        self._fire_event(EVENT_SMART_WAKE_PRE_ALARM_STARTED)
        self._notify_update()

        # Attach hardware dismiss listeners during active cycle
        self._setup_active_alarm_listeners()
        self._setup_sleep_tracker_listener()

        # Execute configured pre-alarm actions
        await self._execute_pre_alarm_actions()

        # Schedule transition to Main Alarm
        now = dt_util.now()
        delay = (self._next_alarm - now).total_seconds() if self._next_alarm else 0
        if delay < 0:
            delay = 0

        @callback
        def _to_main_alarm(_point: Any = None) -> None:
            self.hass.async_create_task(self.async_start_main_alarm())

        self._unsub_phase_timer = async_call_later(self.hass, delay, _to_main_alarm)

    async def async_start_main_alarm(self) -> None:
        """Trigger Phase 2: Main Alarm (Weckzeitpunkt)."""
        _LOGGER.info("Smart Wake [%s] starting Phase 2: Main Alarm", self._name)
        self._cancel_phase_timer()
        self._status = STATUS_RINGING
        self._active_phase = PHASE_MAIN_ALARM
        self._fire_event(EVENT_SMART_WAKE_ALARM_TRIGGERED)
        self._notify_update()

        # Ensure active listeners are connected
        self._setup_active_alarm_listeners()

        # Execute main alarm actions
        await self._execute_main_alarm_actions()

        # Schedule escalation timer if enabled
        escalation_enabled = self._config.get(
            CONF_ESCALATION_ENABLED, DEFAULT_ESCALATION_ENABLED
        )
        if escalation_enabled:
            delay_mins = int(
                self._config.get(CONF_ESCALATION_DELAY, DEFAULT_ESCALATION_DELAY)
            )

            @callback
            def _to_escalation(_point: Any = None) -> None:
                self.hass.async_create_task(self.async_start_escalation())

            self._unsub_phase_timer = async_call_later(
                self.hass, delay_mins * 60, _to_escalation
            )

    async def async_start_escalation(self) -> None:
        """Trigger Phase 3: Escalation (Anti-Verschlaf-Schutz)."""
        if self._status != STATUS_RINGING:
            return

        _LOGGER.warning("Smart Wake [%s] entering Phase 3: Escalation!", self._name)
        self._active_phase = PHASE_ESCALATION
        self._fire_event(EVENT_SMART_WAKE_ESCALATION_STARTED)
        self._notify_update()

        # Execute escalation actions
        await self._execute_escalation_actions()

    # -------------------------------------------------------------------------
    # Snooze, Dismiss & Skip Actions
    # -------------------------------------------------------------------------
    async def async_snooze(self, custom_duration: int | None = None) -> bool:
        """Perform snooze action if within maximum snooze limit."""
        if self._status not in (STATUS_RINGING, STATUS_PRE_ALARM):
            _LOGGER.debug("Cannot snooze Smart Wake [%s] while in %s", self._name, self._status)
            return False

        if self._snooze_count >= self.max_snooze_count:
            _LOGGER.warning(
                "Smart Wake [%s] maximum snooze limit (%d) reached! Snooze blocked.",
                self._name,
                self.max_snooze_count,
            )
            return False

        self._snooze_count += 1
        self._cancel_phase_timer()
        self._cancel_fade_tasks()
        await self._stop_media_players()

        if custom_duration is not None:
            delay_seconds = custom_duration * 60
            display_duration = custom_duration
        elif self._is_full_test and self._full_test_snooze_seconds is not None:
            delay_seconds = self._full_test_snooze_seconds
            display_duration = max(1, self._full_test_snooze_seconds // 60)
        else:
            delay_seconds = self.snooze_duration * 60
            display_duration = self.snooze_duration

        now = dt_util.now()
        self._snooze_until = now + timedelta(seconds=delay_seconds)
        self._status = STATUS_SNOOZED
        self._active_phase = PHASE_NONE
        _LOGGER.info(
            "Smart Wake [%s] snoozed for %s (Count: %d/%d)",
            self._name,
            f"{delay_seconds}s" if (self._is_full_test and self._full_test_snooze_seconds) else f"{display_duration}m",
            self._snooze_count,
            self.max_snooze_count,
        )

        # Keep active hardware, motion and NFC listeners attached during snooze
        self._setup_active_alarm_listeners()

        self._fire_event(
            EVENT_SMART_WAKE_SNOOZED,
            {
                "snooze_count": self._snooze_count,
                "duration": display_duration,
                "duration_seconds": delay_seconds,
                "snooze_until": self._snooze_until.isoformat() if self._snooze_until else None,
                "is_full_test": self._is_full_test,
            },
        )
        self._notify_update()

        @callback
        def _resume_after_snooze(_point: Any = None) -> None:
            self._snooze_until = None
            self.hass.async_create_task(self.async_start_main_alarm())

        self._unsub_phase_timer = async_call_later(
            self.hass, delay_seconds, _resume_after_snooze
        )
        return True

    async def async_dismiss(self, forced: bool = False) -> bool:
        """Dismiss active alarm or pre-alarm, restoring normal state.

        If Anti-Cheat conditions are configured and forced is False:
        - If anti-cheat is currently fulfilled: final dismissal.
        - If anti-cheat is NOT fulfilled: acts as snooze!
        """
        if self._status in (STATUS_IDLE, STATUS_DISMISSED, STATUS_SKIPPED):
            return True

        # Check Anti-Cheat gating if not forced
        if not forced and self.has_anti_cheat_configured():
            if self.is_anti_cheat_fulfilled():
                _LOGGER.info(
                    "Smart Wake [%s] Anti-Cheat conditions verified! Proceeding with final dismissal.",
                    self._name,
                )
            else:
                _LOGGER.warning(
                    "Smart Wake [%s] Anti-Cheat conditions NOT fulfilled! Dismiss action acting as Snooze.",
                    self._name,
                )
                self._fire_event(
                    EVENT_SMART_WAKE_ANTI_CHEAT_BLOCKED,
                    {
                        "action": "diverted_to_snooze",
                        "status": self._status,
                        "snooze_count": self._snooze_count,
                        "max_snooze_count": self.max_snooze_count,
                    },
                )
                # If already snoozed, remain snoozed
                if self._status == STATUS_SNOOZED:
                    _LOGGER.info(
                        "Smart Wake [%s] already snoozed; remains snoozed until Anti-Cheat condition met.",
                        self._name,
                    )
                    return False

                # Divert to snooze
                snoozed = await self.async_snooze()
                if not snoozed:
                    _LOGGER.warning(
                        "Smart Wake [%s] Anti-Cheat not fulfilled and maximum snooze limit (%d) reached! Dismiss blocked, alarm continues.",
                        self._name,
                        self.max_snooze_count,
                    )
                return False

        # Final dismissal
        return await self._dismiss_final()

    async def _dismiss_final(self) -> bool:
        """Execute final dismissal, cleaning up state and timers."""
        _LOGGER.info("Smart Wake [%s] dismissed", self._name)
        self._is_full_test = False
        self._full_test_snooze_seconds = None
        self._anti_cheat_nfc_scanned = False
        self._snooze_until = None
        self._cancel_phase_timer()
        self._cancel_fade_tasks()
        self._cleanup_listeners()
        await self._stop_media_players()

        self._status = STATUS_DISMISSED
        self._active_phase = PHASE_NONE
        self._snooze_count = 0
        self._fire_event(EVENT_SMART_WAKE_DISMISSED)
        self._notify_update()

        # Recalculate and arm next scheduled occurrence
        await self.async_recalculate_schedule()
        self._status = STATUS_IDLE
        self._notify_update()
        return True

    def set_skip_next(self, skip: bool = True) -> None:
        """Mark next alarm cycle to be skipped."""
        self._skip_next = skip
        _LOGGER.info("Smart Wake [%s] skip next set to %s", self._name, skip)
        self._notify_update()

    async def async_set_time(self, new_time: str) -> None:
        """Set new target time and recalculate schedule."""
        self._time_str = new_time
        self._config[CONF_TIME] = new_time
        await self.async_recalculate_schedule()

    async def async_set_enabled(self, enabled: bool) -> None:
        """Enable or disable alarm."""
        self._enabled = enabled
        self._config[CONF_ENABLED] = enabled
        if not enabled:
            if self._status in (STATUS_RINGING, STATUS_PRE_ALARM, STATUS_SNOOZED):
                await self.async_dismiss(forced=True)
            self._status = STATUS_IDLE
            self._active_phase = PHASE_NONE
        await self.async_recalculate_schedule()

    # -------------------------------------------------------------------------
    # Hardware, NFC, Motion & Sleep-Tracker Anti-Cheat Listeners
    # -------------------------------------------------------------------------
    def _setup_active_alarm_listeners(self) -> None:
        """Subscribe to configured anti-cheat motion detectors, NFC tags, power sensors and buttons."""
        self._cleanup_listeners()
        if not hasattr(self.hass, "states"):
            return

        # 1. Motion sensors (e.g. bathroom / kitchen) -> Dismiss
        motion_entities = self._config.get(CONF_DISMISS_MOTION_ENTITIES, [])
        if isinstance(motion_entities, str):
            motion_entities = [motion_entities]

        if motion_entities:
            @callback
            def _on_motion(event: Event) -> None:
                new_state = getattr(event.data, "get", lambda _: None)("new_state") if hasattr(event, "data") else None
                state_val = str(getattr(new_state, "state", "")).lower() if new_state else ""
                if state_val in (STATE_ON, "on", "detected", "motion"):
                    _LOGGER.info(
                        "Smart Wake [%s] motion anti-cheat triggered via %s -> Dismissing",
                        self._name,
                        getattr(new_state, "entity_id", "motion_sensor"),
                    )
                    self.hass.async_create_task(self.async_dismiss(forced=True))

            try:
                unsub = async_track_state_change_event(
                    self.hass, motion_entities, _on_motion
                )
                self._unsub_listeners.append(unsub)
            except Exception as err:
                _LOGGER.debug("Could not attach motion sensor tracker: %s", err)

        # 2. Power sensor (e.g. coffee machine / bathroom light > threshold) -> Dismiss
        power_sensor = self._config.get(CONF_DISMISS_POWER_SENSOR)
        if power_sensor:
            threshold = float(
                self._config.get(
                    CONF_DISMISS_POWER_THRESHOLD, DEFAULT_DISMISS_POWER_THRESHOLD
                )
            )

            @callback
            def _on_power_change(event: Event) -> None:
                new_state = getattr(event.data, "get", lambda _: None)("new_state") if hasattr(event, "data") else None
                if not new_state:
                    return
                try:
                    val = float(new_state.state)
                    if val >= threshold:
                        _LOGGER.info(
                            "Smart Wake [%s] power anti-cheat triggered (%.1fW >= %.1fW) -> Dismissing",
                            self._name,
                            val,
                            threshold,
                        )
                        self.hass.async_create_task(self.async_dismiss(forced=True))
                except (ValueError, TypeError):
                    pass

            try:
                unsub = async_track_state_change_event(
                    self.hass, [power_sensor], _on_power_change
                )
                self._unsub_listeners.append(unsub)
            except Exception as err:
                _LOGGER.debug("Could not attach power sensor tracker: %s", err)

        # 3. NFC Tag scanned event -> Dismiss
        nfc_tags = self._config.get(CONF_DISMISS_NFC_TAGS, [])
        if isinstance(nfc_tags, str):
            nfc_tags = [nfc_tags]

        if nfc_tags and hasattr(self.hass, "bus"):
            @callback
            def _on_tag_scanned(event: Event) -> None:
                tag_id = event.data.get("tag_id") if hasattr(event, "data") else None
                if tag_id and tag_id in nfc_tags:
                    self._anti_cheat_nfc_scanned = True
                    _LOGGER.info(
                        "Smart Wake [%s] NFC Tag [%s] scanned -> Dismissing",
                        self._name,
                        tag_id,
                    )
                    self.hass.async_create_task(self.async_dismiss(forced=True))

            try:
                unsub = self.hass.bus.async_listen("tag_scanned", _on_tag_scanned)
                self._unsub_listeners.append(unsub)
            except Exception as err:
                _LOGGER.debug("Could not attach tag_scanned listener: %s", err)

        # 4. Hardware button entity / events (Single click = Snooze, Double click = Dismiss)
        btn_dismiss = self._config.get(CONF_DISMISS_BUTTON_ENTITY)
        btn_snooze = self._config.get(CONF_SNOOZE_BUTTON_ENTITY)
        tracked_btns = [b for b in (btn_dismiss, btn_snooze) if b]

        if tracked_btns:
            @callback
            def _on_btn_event(event: Event) -> None:
                new_state = getattr(event.data, "get", lambda _: None)("new_state") if hasattr(event, "data") else None
                if not new_state:
                    return
                ent_id = getattr(new_state, "entity_id", "")
                val = getattr(new_state, "state", "").lower()
                event_type = str(getattr(new_state, "attributes", {}).get("event_type", "")).lower()

                # Dismiss button (undergoes Anti-Cheat gating)
                if ent_id == btn_dismiss or "double" in val or "double" in event_type:
                    self.hass.async_create_task(self.async_dismiss(forced=False))
                # Snooze button
                elif ent_id == btn_snooze or "single" in val or "single" in event_type or val == STATE_ON:
                    self.hass.async_create_task(self.async_snooze())

            try:
                unsub = async_track_state_change_event(
                    self.hass, tracked_btns, _on_btn_event
                )
                self._unsub_listeners.append(unsub)
            except Exception as err:
                _LOGGER.debug("Could not attach button tracker: %s", err)

    def _setup_sleep_tracker_listener(self) -> None:
        """Monitor sleep tracker stage within early wake window to trigger in light sleep."""
        sleep_ent = self._config.get(CONF_SLEEP_STAGE_ENTITY)
        if not sleep_ent or not hasattr(self.hass, "states"):
            return

        target_stages = self._config.get(
            CONF_SLEEP_STAGE_VALUES, DEFAULT_SLEEP_STAGE_VALUES
        )

        @callback
        def _on_sleep_stage(event: Event) -> None:
            if self._status != STATUS_PRE_ALARM:
                return
            new_state = getattr(event.data, "get", lambda _: None)("new_state") if hasattr(event, "data") else None
            if not new_state:
                return
            current_stage = str(getattr(new_state, "state", "")).lower()
            if any(stage.lower() == current_stage for stage in target_stages):
                _LOGGER.info(
                    "Smart Wake [%s] sleep tracker detected light sleep stage '%s' -> Early Wake Trigger!",
                    self._name,
                    current_stage,
                )
                self.hass.async_create_task(self.async_start_main_alarm())

        try:
            unsub = async_track_state_change_event(
                self.hass, [sleep_ent], _on_sleep_stage
            )
            self._unsub_listeners.append(unsub)
        except Exception as err:
            _LOGGER.debug("Could not attach sleep tracker listener: %s", err)

    # -------------------------------------------------------------------------
    # Action Execution (Phases 1, 2, 3)
    # -------------------------------------------------------------------------
    async def _execute_pre_alarm_actions(self) -> None:
        """Execute Phase 1 hardware actions: smooth light ramp, heating delta, cover tilt."""
        # Lights: Smooth ramp from 1% warm red to 80% daylight white
        lights = self._config.get(CONF_PRE_ALARM_LIGHT_ENTITIES, [])
        if isinstance(lights, str):
            lights = [lights]

        duration_secs = self.pre_alarm_duration * 60
        start_bri = int(
            self._config.get(
                CONF_PRE_ALARM_LIGHT_START_BRIGHTNESS,
                DEFAULT_PRE_ALARM_LIGHT_START_BRIGHTNESS,
            )
        )
        end_bri = int(
            self._config.get(
                CONF_PRE_ALARM_LIGHT_END_BRIGHTNESS,
                DEFAULT_PRE_ALARM_LIGHT_END_BRIGHTNESS,
            )
        )

        for l_ent in lights:
            try:
                # Initial start
                await self.hass.services.async_call(
                    "light",
                    "turn_on",
                    {
                        "entity_id": l_ent,
                        "brightness_pct": max(1, start_bri),
                        "rgb_color": [255, 60, 20],  # Warm sunrise red
                    },
                    blocking=False,
                )
                # Transition to end brightness and daylight
                await self.hass.services.async_call(
                    "light",
                    "turn_on",
                    {
                        "entity_id": l_ent,
                        "brightness_pct": min(100, end_bri),
                        "color_temp_kelvin": 4000,
                        "transition": max(1, duration_secs),
                    },
                    blocking=False,
                )
            except Exception as err:
                _LOGGER.debug("Pre-alarm light service call failed on %s: %s", l_ent, err)

        # Covers tilt (20%)
        covers = self._config.get(CONF_PRE_ALARM_COVER_ENTITIES, [])
        if isinstance(covers, str):
            covers = [covers]

        cover_pos = int(
            self._config.get(
                CONF_PRE_ALARM_COVER_POSITION, DEFAULT_PRE_ALARM_COVER_POSITION
            )
        )
        for cov_ent in covers:
            try:
                await self.hass.services.async_call(
                    "cover",
                    "set_cover_position",
                    {"entity_id": cov_ent, "position": cover_pos},
                    blocking=False,
                )
            except Exception as err:
                _LOGGER.debug("Pre-alarm cover call failed on %s: %s", cov_ent, err)

        # Custom pre-alarm script
        pre_script = self._config.get(CONF_PRE_ALARM_SCRIPT_ENTITY)
        if pre_script:
            await self._run_script(pre_script)

    async def _execute_main_alarm_actions(self) -> None:
        """Execute Phase 2: Media player audio fade-in, TTS greeting and custom script."""
        media_players = self._config.get(CONF_MAIN_MEDIA_PLAYER_ENTITIES, [])
        if isinstance(media_players, str):
            media_players = [media_players]

        content_id = self._config.get(CONF_MAIN_AUDIO_CONTENT_ID)
        content_type = self._config.get(
            CONF_MAIN_AUDIO_CONTENT_TYPE, DEFAULT_MAIN_AUDIO_CONTENT_TYPE
        )
        fade_in = self._config.get(CONF_MAIN_AUDIO_FADE_IN, DEFAULT_MAIN_AUDIO_FADE_IN)
        target_vol = float(
            self._config.get(
                CONF_MAIN_AUDIO_TARGET_VOLUME, DEFAULT_MAIN_AUDIO_TARGET_VOLUME
            )
        )
        fade_duration = int(
            self._config.get(
                CONF_MAIN_AUDIO_FADE_DURATION, DEFAULT_MAIN_AUDIO_FADE_DURATION
            )
        )

        for mp_ent in media_players:
            if content_id:
                try:
                    await self.hass.services.async_call(
                        "media_player",
                        "play_media",
                        {
                            "entity_id": mp_ent,
                            "media_content_id": content_id,
                            "media_content_type": content_type,
                        },
                        blocking=False,
                    )
                except Exception as err:
                    _LOGGER.debug("Main alarm media play failed on %s: %s", mp_ent, err)

            if fade_in:
                task = self.hass.async_create_task(
                    self._fade_volume(mp_ent, 0.05, target_vol, fade_duration)
                )
                self._fade_tasks.append(task)
            else:
                try:
                    await self.hass.services.async_call(
                        "media_player",
                        "volume_set",
                        {"entity_id": mp_ent, "volume_level": target_vol},
                        blocking=False,
                    )
                except Exception as err:
                    _LOGGER.debug("Main alarm volume call failed on %s: %s", mp_ent, err)

        # TTS Greeting
        tts_enabled = self._config.get(CONF_MAIN_TTS_ENABLED, DEFAULT_MAIN_TTS_ENABLED)
        if tts_enabled and media_players:
            await self._speak_greeting(media_players[0])

        # Custom main script
        main_script = self._config.get(CONF_MAIN_SCRIPT_ENTITY)
        if main_script:
            await self._run_script(main_script)

    async def _execute_escalation_actions(self) -> None:
        """Execute Phase 3: Max audio volume 90%, 100% cold white light, open covers."""
        # 1. Media Player volume escalation (gentle volume rise)
        media_players = self._config.get(CONF_MAIN_MEDIA_PLAYER_ENTITIES, [])
        if isinstance(media_players, str):
            media_players = [media_players]

        esc_vol = float(
            self._config.get(CONF_ESCALATION_VOLUME, DEFAULT_ESCALATION_VOLUME)
        )
        fade_duration = 3 if self._is_dry_run else int(
            self._config.get(
                CONF_ESCALATION_VOLUME_FADE_DURATION,
                DEFAULT_ESCALATION_VOLUME_FADE_DURATION,
            )
        )

        for mp_ent in media_players:
            start_vol = 0.5
            state = self.hass.states.get(mp_ent) if hasattr(self.hass, "states") else None
            if state and "volume_level" in getattr(state, "attributes", {}) and state.attributes["volume_level"] is not None:
                try:
                    start_vol = float(state.attributes["volume_level"])
                except (ValueError, TypeError):
                    start_vol = float(
                        self._config.get(
                            CONF_MAIN_AUDIO_TARGET_VOLUME, DEFAULT_MAIN_AUDIO_TARGET_VOLUME
                        )
                    )
            else:
                start_vol = float(
                    self._config.get(
                        CONF_MAIN_AUDIO_TARGET_VOLUME, DEFAULT_MAIN_AUDIO_TARGET_VOLUME
                    )
                )

            if fade_duration > 0 and esc_vol > start_vol:
                task = self.hass.async_create_task(
                    self._fade_volume(mp_ent, start_vol, esc_vol, fade_duration)
                )
                self._fade_tasks.append(task)
            else:
                try:
                    await self.hass.services.async_call(
                        "media_player",
                        "volume_set",
                        {"entity_id": mp_ent, "volume_level": esc_vol},
                        blocking=False,
                    )
                except Exception as err:
                    _LOGGER.debug("Escalation volume call failed on %s: %s", mp_ent, err)

        # 2. Lighting: 100% Cold White
        esc_lights = self._config.get(
            CONF_ESCALATION_LIGHT_ENTITIES,
            self._config.get(CONF_PRE_ALARM_LIGHT_ENTITIES, []),
        )
        if isinstance(esc_lights, str):
            esc_lights = [esc_lights]

        bri = int(
            self._config.get(
                CONF_ESCALATION_LIGHT_BRIGHTNESS, DEFAULT_ESCALATION_LIGHT_BRIGHTNESS
            )
        )
        for l_ent in esc_lights:
            try:
                await self.hass.services.async_call(
                    "light",
                    "turn_on",
                    {
                        "entity_id": l_ent,
                        "brightness_pct": min(100, bri),
                        "color_temp_kelvin": 6500,  # Cold white
                    },
                    blocking=False,
                )
            except Exception as err:
                _LOGGER.debug("Escalation light call failed on %s: %s", l_ent, err)

        # 3. Covers: 100% open
        esc_covers = self._config.get(
            CONF_ESCALATION_COVER_ENTITIES,
            self._config.get(CONF_PRE_ALARM_COVER_ENTITIES, []),
        )
        if isinstance(esc_covers, str):
            esc_covers = [esc_covers]

        cov_pos = int(
            self._config.get(
                CONF_ESCALATION_COVER_POSITION, DEFAULT_ESCALATION_COVER_POSITION
            )
        )
        for cov_ent in esc_covers:
            try:
                await self.hass.services.async_call(
                    "cover",
                    "set_cover_position",
                    {"entity_id": cov_ent, "position": cov_pos},
                    blocking=False,
                )
            except Exception as err:
                _LOGGER.debug("Escalation cover call failed on %s: %s", cov_ent, err)

        # Custom escalation script
        esc_script = self._config.get(CONF_ESCALATION_SCRIPT_ENTITY)
        if esc_script:
            await self._run_script(esc_script)

    async def _fade_volume(
        self, entity_id: str, start_vol: float, end_vol: float, duration: int
    ) -> None:
        """Ramp volume smoothly over specified seconds."""
        steps = max(1, min(duration, 30))
        step_interval = duration / steps
        vol_step = (end_vol - start_vol) / steps
        cur_vol = start_vol

        try:
            for _ in range(steps):
                if self._status not in (STATUS_RINGING, STATUS_PRE_ALARM) and not self._is_dry_run:
                    break
                await self.hass.services.async_call(
                    "media_player",
                    "volume_set",
                    {"entity_id": entity_id, "volume_level": round(cur_vol, 2)},
                    blocking=False,
                )
                cur_vol += vol_step
                await asyncio.sleep(step_interval)
        except asyncio.CancelledError:
            pass
        except Exception as err:
            _LOGGER.debug("Volume fade error on %s: %s", entity_id, err)

    async def _speak_greeting(self, media_player_entity: str) -> None:
        """Compose and speak morning briefing via TTS."""
        raw_msg = self._config.get(CONF_MAIN_TTS_MESSAGE, DEFAULT_MAIN_TTS_MESSAGE)

        # Substitute dynamic variables
        time_text = dt_util.now().strftime("%H:%M")
        outdoor_temp = ""
        temp_ent = self._config.get(CONF_WEATHER_TEMP_ENTITY)
        if temp_ent and hasattr(self.hass, "states"):
            s = self.hass.states.get(temp_ent)
            if s and s.state not in (STATE_UNAVAILABLE, STATE_UNKNOWN):
                outdoor_temp = f"{s.state} °C"

        formatted = (
            raw_msg.replace("{time}", time_text)
            .replace("{temp}", outdoor_temp)
            .replace("{name}", self._name)
        )

        tts_engine = self._config.get(CONF_MAIN_TTS_ENGINE, "tts.speak")
        try:
            domain, service = tts_engine.split(".", 1) if "." in tts_engine else ("tts", "speak")
            await self.hass.services.async_call(
                domain,
                service,
                {"media_player_entity_id": media_player_entity, "message": formatted},
                blocking=False,
            )
        except Exception as err:
            _LOGGER.debug("TTS greeting call failed: %s", err)

    async def _stop_media_players(self) -> None:
        """Stop all media players configured for this alarm."""
        media_players = self._config.get(CONF_MAIN_MEDIA_PLAYER_ENTITIES, [])
        if isinstance(media_players, str):
            media_players = [media_players]

        for mp_ent in media_players:
            try:
                await self.hass.services.async_call(
                    "media_player",
                    "media_stop",
                    {"entity_id": mp_ent},
                    blocking=False,
                )
            except Exception:
                pass

    async def _run_script(self, script_entity: str) -> None:
        """Execute a custom HA script."""
        try:
            parts = script_entity.split(".")
            service_name = parts[1] if len(parts) == 2 else parts[0]
            await self.hass.services.async_call("script", service_name, {}, blocking=False)
        except Exception as err:
            _LOGGER.debug("Script execution error for %s: %s", script_entity, err)

    # -------------------------------------------------------------------------
    # Testlauf / Dry-Run Modus (30-Sekunden-Zeitraffer)
    # -------------------------------------------------------------------------
    async def async_start_dry_run(self) -> None:
        """Start a compressed 30-second time-lapse test of all 3 alarm phases."""
        if self._is_dry_run:
            return

        _LOGGER.info("Starting 30-second dry-run test for Smart Wake [%s]", self._name)
        self._is_dry_run = True
        self._dry_run_progress = 0
        self._status = STATUS_PRE_ALARM
        self._active_phase = PHASE_PRE_ALARM
        self._notify_update()

        async def _run_loop() -> None:
            try:
                # Phase 1 Preview (0 - 10s)
                await self._execute_pre_alarm_actions()
                for sec in range(TEST_DRY_RUN_PRE_ALARM_SECONDS):
                    self._dry_run_progress = sec
                    self._notify_update()
                    await asyncio.sleep(1)

                # Phase 2 Preview (10 - 20s)
                self._status = STATUS_RINGING
                self._active_phase = PHASE_MAIN_ALARM
                await self._execute_main_alarm_actions()
                for sec in range(TEST_DRY_RUN_PRE_ALARM_SECONDS, TEST_DRY_RUN_PRE_ALARM_SECONDS + TEST_DRY_RUN_MAIN_SECONDS):
                    self._dry_run_progress = sec
                    self._notify_update()
                    await asyncio.sleep(1)

                # Phase 3 Preview (20 - 30s)
                self._active_phase = PHASE_ESCALATION
                await self._execute_escalation_actions()
                for sec in range(
                    TEST_DRY_RUN_PRE_ALARM_SECONDS + TEST_DRY_RUN_MAIN_SECONDS,
                    TEST_DRY_RUN_TOTAL_SECONDS,
                ):
                    self._dry_run_progress = sec
                    self._notify_update()
                    await asyncio.sleep(1)

                # Restore
                await self.async_stop_dry_run()
            except asyncio.CancelledError:
                pass
            except Exception as err:
                _LOGGER.error("Dry run error: %s", err)
                await self.async_stop_dry_run()

        self._unsub_dry_run = self.hass.async_create_task(_run_loop())

    async def async_stop_dry_run(self) -> None:
        """Stop running dry run test and restore idle state."""
        _LOGGER.info("Stopping dry-run test for Smart Wake [%s]", self._name)
        self._cancel_dry_run()
        self._is_dry_run = False
        self._dry_run_progress = 0
        self._cancel_fade_tasks()
        await self._stop_media_players()
        self._status = STATUS_IDLE
        self._active_phase = PHASE_NONE
        self._notify_update()

    async def async_start_full_test(
        self,
        start_from_pre_alarm: bool | None = None,
        pre_alarm_seconds: int | None = None,
        snooze_seconds: int | None = DEFAULT_FULL_TEST_SNOOZE_SECONDS,
    ) -> None:
        """Start a full, real-time test run of the alarm sequence."""
        if self._is_dry_run:
            await self.async_stop_dry_run()

        _LOGGER.info("Starting full real-time test run for Smart Wake [%s]", self._name)
        self._is_full_test = True
        self._full_test_snooze_seconds = snooze_seconds
        self._anti_cheat_nfc_scanned = False
        self._snooze_count = 0

        pre_alarm_enabled = self._config.get(CONF_PRE_ALARM_ENABLED, DEFAULT_PRE_ALARM_ENABLED)
        if start_from_pre_alarm is None:
            start_from_pre_alarm = pre_alarm_enabled

        if start_from_pre_alarm and pre_alarm_enabled:
            _LOGGER.info("Full test run: Starting Phase 1 (Pre-Alarm)")
            self._status = STATUS_PRE_ALARM
            self._active_phase = PHASE_PRE_ALARM
            self._fire_event(EVENT_SMART_WAKE_PRE_ALARM_STARTED, {"test": True})
            self._notify_update()

            self._setup_active_alarm_listeners()
            self._setup_sleep_tracker_listener()
            await self._execute_pre_alarm_actions()

            delay = pre_alarm_seconds if pre_alarm_seconds is not None else (self.pre_alarm_duration * 60)
            if delay <= 0:
                delay = 1

            @callback
            def _to_main_alarm(_point: Any = None) -> None:
                self.hass.async_create_task(self.async_start_main_alarm())

            self._cancel_phase_timer()
            self._unsub_phase_timer = async_call_later(self.hass, delay, _to_main_alarm)
        else:
            _LOGGER.info("Full test run: Starting directly in Phase 2 (Main Alarm)")
            await self.async_start_main_alarm()

    async def async_stop_test(self) -> None:
        """Stop any active test run (dry-run or full test) and restore idle state."""
        _LOGGER.info("Stopping test run for Smart Wake [%s]", self._name)
        if self._is_dry_run:
            await self.async_stop_dry_run()
            return

        if self._is_full_test or self._status in (STATUS_RINGING, STATUS_PRE_ALARM, STATUS_SNOOZED):
            self._is_full_test = False
            self._full_test_snooze_seconds = None
            self._anti_cheat_nfc_scanned = False
            await self.async_dismiss(forced=True)

    # -------------------------------------------------------------------------
    # Helper & Notification Utilities
    # -------------------------------------------------------------------------
    def _cancel_schedule(self) -> None:
        if self._unsub_schedule:
            try:
                self._unsub_schedule()
            except Exception:
                pass
            self._unsub_schedule = None

    def _cancel_phase_timer(self) -> None:
        if self._unsub_phase_timer:
            try:
                self._unsub_phase_timer()
            except Exception:
                pass
            self._unsub_phase_timer = None

    def _cancel_dry_run(self) -> None:
        if self._unsub_dry_run:
            try:
                if hasattr(self._unsub_dry_run, "cancel"):
                    self._unsub_dry_run.cancel()
                elif callable(self._unsub_dry_run):
                    self._unsub_dry_run()
            except Exception:
                pass
            self._unsub_dry_run = None

    def _cleanup_listeners(self) -> None:
        for unsub in self._unsub_listeners:
            try:
                unsub()
            except Exception:
                pass
        self._unsub_listeners.clear()

    def _cancel_fade_tasks(self) -> None:
        for t in self._fade_tasks:
            if not t.done():
                t.cancel()
        self._fade_tasks.clear()

    def _notify_update(self) -> None:
        """Broadcast state updates to entities and websocket subscribers."""
        async_dispatcher_send(self.hass, SIGNAL_SMART_WAKE_UPDATED.format(self.entry_id))
        async_dispatcher_send(self.hass, SIGNAL_SMART_WAKE_ALL_UPDATED)

    def _fire_event(self, event_type: str, extra: dict[str, Any] | None = None) -> None:
        """Fire a Home Assistant event on the event bus."""
        if not hasattr(self.hass, "bus"):
            return
        data = {
            "entry_id": self.entry_id,
            "name": self._name,
            "status": self._status,
            "active_phase": self._active_phase,
        }
        if extra:
            data.update(extra)
        try:
            self.hass.bus.async_fire(event_type, data)
            self.hass.bus.async_fire(EVENT_SMART_WAKE_STATUS_CHANGED, data)
        except Exception as err:
            _LOGGER.debug("Could not fire event %s: %s", event_type, err)
