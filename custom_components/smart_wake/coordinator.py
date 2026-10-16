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
    CONF_DISMISS_INPUT_BOOLEAN,
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
    CONF_MAIN_TTS_MEDIA_PLAYER,
    CONF_MAIN_TTS_MESSAGE,
    CONF_MAIN_TTS_DELAY,
    CONF_MAIN_TTS_VOLUME,
    CONF_MAX_SNOOZE_COUNT,
    CONF_MOBILE_ALARM_ENTITY,
    CONF_ALARM_SOURCE_MODE,
    CONF_MOBILE_DISMISS_SYNC,
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
    ALARM_SOURCE_MOBILE_PRIORITY,
    ALARM_SOURCE_EARLIEST,
    ALARM_SOURCE_MOBILE_ONLY,
    ALARM_SOURCE_FIXED_ONLY,
    DEFAULT_ALARM_SOURCE_MODE,
    DEFAULT_MOBILE_DISMISS_SYNC,
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
    DEFAULT_MAIN_TTS_DELAY,
    DEFAULT_MAIN_TTS_VOLUME,
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
        self._unsub_dynamic_sensors: CALLBACK_TYPE | None = None
        self._unsub_listeners: list[CALLBACK_TYPE] = []
        self._fade_tasks: list[asyncio.Task] = []
        self._tts_task: asyncio.Task | None = None

        # Testing state
        self._is_dry_run: bool = False
        self._dry_run_progress: int = 0
        self._is_full_test: bool = False
        self._full_test_snooze_seconds: int | None = None

        # Anti-cheat tracking
        self._anti_cheat_nfc_scanned: bool = False
        self._snooze_until: datetime | None = None

        # Mobile alarm tracking & source
        self._mobile_alarm_time: datetime | None = None
        self._active_alarm_source: str = "fixed"
        self._active_alarm_target: datetime | None = None

    # -------------------------------------------------------------------------
    # Properties
    # -------------------------------------------------------------------------
    @property
    def mobile_alarm_entity(self) -> str | None:
        """Return configured mobile alarm sensor entity ID."""
        return self._config.get(CONF_MOBILE_ALARM_ENTITY)

    @property
    def alarm_source_mode(self) -> str:
        """Return configured alarm source mode."""
        return self._config.get(CONF_ALARM_SOURCE_MODE, DEFAULT_ALARM_SOURCE_MODE)

    @property
    def mobile_dismiss_sync(self) -> bool:
        """Return whether mobile alarm dismiss/snooze sync is enabled."""
        return bool(self._config.get(CONF_MOBILE_DISMISS_SYNC, DEFAULT_MOBILE_DISMISS_SYNC))

    @property
    def mobile_alarm_time(self) -> datetime | None:
        """Return parsed next mobile phone alarm datetime."""
        return self._mobile_alarm_time

    @property
    def active_alarm_source(self) -> str:
        """Return active alarm source: 'mobile', 'fixed', 'fixed_fallback', or 'none'."""
        return self._active_alarm_source

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

        ib = self._config.get(CONF_DISMISS_INPUT_BOOLEAN)
        if ib and str(ib).strip():
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

        # 4. Input boolean helper entity (state == on)
        ib = self._config.get(CONF_DISMISS_INPUT_BOOLEAN)
        if ib and str(ib).strip():
            st = self.hass.states.get(str(ib).strip())
            if st and str(st.state).lower() in (STATE_ON, "on", "true"):
                _LOGGER.info(
                    "Smart Wake [%s] Anti-Cheat verified via input_boolean %s (state: %s)",
                    self._name,
                    ib,
                    st.state,
                )
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
        self._active_alarm_target = None

    def update_config(self, new_config: dict[str, Any]) -> None:
        """Update instance configuration and recalculate schedule."""
        self._config.update(new_config)
        self._name = self._config.get(CONF_NAME, self._name)
        self._enabled = bool(self._config.get(CONF_ENABLED, self._enabled))
        self._time_str = self._config.get(CONF_TIME, self._time_str)
        self._days = list(self._config.get(CONF_DAYS, self._days))
        self._setup_dynamic_sensors_listener()
        self.hass.async_create_task(self.async_recalculate_schedule())

    # -------------------------------------------------------------------------
    # Schedule & Next Alarm Calculation
    # -------------------------------------------------------------------------
    async def async_recalculate_schedule(self) -> None:
        """Calculate next alarm and pre-alarm times based on rules, mobile phone sensor, and source modes."""
        self._cancel_schedule()

        if not self._enabled:
            self._next_alarm = None
            self._pre_alarm_time = None
            self._dynamic_offset_minutes = 0
            self._offset_reasons = []
            self._active_alarm_source = "none"
            self._mobile_alarm_time = None
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

        # 2. Compute candidate for fixed alarm schedule (check up to 8 days in advance)
        fixed_target: datetime | None = None
        fixed_pre_alarm: datetime | None = None

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

            threshold = shifted_pre_alarm if pre_alarm_enabled else shifted_target

            if threshold > now:
                fixed_target = shifted_target
                fixed_pre_alarm = shifted_pre_alarm
                break

        # 3. Check mobile phone alarm sensor
        mobile_dt = self._parse_mobile_alarm_time()
        self._mobile_alarm_time = mobile_dt
        source_mode = self.alarm_source_mode

        mobile_target: datetime | None = None
        mobile_pre_alarm: datetime | None = None
        if mobile_dt:
            shifted_mob_target = mobile_dt - timedelta(minutes=offset_mins)
            shifted_mob_pre = shifted_mob_target - timedelta(minutes=pre_alarm_duration)
            mob_threshold = shifted_mob_pre if pre_alarm_enabled else shifted_mob_target

            if mob_threshold > now:
                mobile_target = shifted_mob_target
                mobile_pre_alarm = shifted_mob_pre
            elif shifted_mob_target > now:
                # Target is in the future, start pre-alarm immediately
                mobile_target = shifted_mob_target
                mobile_pre_alarm = now

        chosen_target: datetime | None = None
        chosen_pre_alarm: datetime | None = None
        chosen_source = "fixed"

        if source_mode == ALARM_SOURCE_FIXED_ONLY:
            chosen_target = fixed_target
            chosen_pre_alarm = fixed_pre_alarm
            chosen_source = "fixed"

        elif source_mode == ALARM_SOURCE_MOBILE_ONLY:
            if mobile_target:
                chosen_target = mobile_target
                chosen_pre_alarm = mobile_pre_alarm
                chosen_source = "mobile"
            else:
                chosen_target = None
                chosen_pre_alarm = None
                chosen_source = "none"

        elif source_mode == ALARM_SOURCE_EARLIEST:
            if mobile_target and fixed_target:
                if mobile_target <= fixed_target:
                    chosen_target = mobile_target
                    chosen_pre_alarm = mobile_pre_alarm
                    chosen_source = "mobile"
                else:
                    chosen_target = fixed_target
                    chosen_pre_alarm = fixed_pre_alarm
                    chosen_source = "fixed"
            elif mobile_target:
                chosen_target = mobile_target
                chosen_pre_alarm = mobile_pre_alarm
                chosen_source = "mobile"
            elif fixed_target:
                chosen_target = fixed_target
                chosen_pre_alarm = fixed_pre_alarm
                chosen_source = "fixed"
            else:
                chosen_target = None
                chosen_pre_alarm = None
                chosen_source = "none"

        else:  # ALARM_SOURCE_MOBILE_PRIORITY (default)
            if mobile_target:
                chosen_target = mobile_target
                chosen_pre_alarm = mobile_pre_alarm
                chosen_source = "mobile"
            else:
                chosen_target = fixed_target
                chosen_pre_alarm = fixed_pre_alarm
                chosen_source = "fixed_fallback" if self.mobile_alarm_entity else "fixed"

        self._next_alarm = chosen_target
        self._pre_alarm_time = chosen_pre_alarm if pre_alarm_enabled else chosen_target
        self._active_alarm_source = chosen_source

        if self._next_alarm and self._pre_alarm_time:
            _LOGGER.info(
                "Smart Wake [%s] next scheduled (%s): Main=%s, PreAlarm=%s (Offset: -%dm, Reasons: %s)",
                self._name,
                self._active_alarm_source,
                self._next_alarm.isoformat(),
                self._pre_alarm_time.isoformat(),
                self._dynamic_offset_minutes,
                ", ".join(self._offset_reasons) or "None",
            )
            self._arm_schedule_timer()

        self._notify_update()

    def _parse_mobile_alarm_time(self) -> datetime | None:
        """Parse next alarm timestamp from mobile phone alarm sensor."""
        entity_id = self._config.get(CONF_MOBILE_ALARM_ENTITY)
        if not entity_id or not hasattr(self.hass, "states"):
            return None

        state_obj = self.hass.states.get(entity_id)
        if not state_obj or state_obj.state in (
            STATE_UNAVAILABLE,
            STATE_UNKNOWN,
            "none",
            "None",
            "",
            "not available",
            "not_available",
            "off",
        ):
            return None

        raw_val = str(state_obj.state).strip()

        # 1. Standard ISO-8601 parsing
        parsed_dt = dt_util.parse_datetime(raw_val)

        # 2. Try parsing numeric unix timestamp
        if parsed_dt is None:
            try:
                val_float = float(raw_val)
                if val_float > 1e11:  # milliseconds
                    val_float /= 1000.0
                parsed_dt = dt_util.utc_from_timestamp(val_float)
            except (ValueError, TypeError):
                pass

        # 3. Check attributes if state was not parseable
        if parsed_dt is None and hasattr(state_obj, "attributes"):
            for attr_key in ("Time Stamp", "timestamp", "next_alarm"):
                attr_val = state_obj.attributes.get(attr_key)
                if attr_val:
                    if isinstance(attr_val, (int, float)):
                        ts = attr_val / 1000.0 if attr_val > 1e11 else float(attr_val)
                        parsed_dt = dt_util.utc_from_timestamp(ts)
                        break
                    elif isinstance(attr_val, datetime):
                        parsed_dt = attr_val
                        break
                    elif isinstance(attr_val, str):
                        parsed_dt = dt_util.parse_datetime(attr_val)
                        if parsed_dt:
                            break

        if parsed_dt is None or not isinstance(parsed_dt, datetime):
            return None

        # Convert to local timezone
        if parsed_dt.tzinfo is None:
            parsed_dt = parsed_dt.replace(tzinfo=dt_util.DEFAULT_TIME_ZONE)
        else:
            parsed_dt = dt_util.as_local(parsed_dt)

        # Ensure it is in the future (grace period of 60 seconds)
        now = dt_util.now()
        if parsed_dt <= now - timedelta(seconds=60):
            return None

        return parsed_dt

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
        if self._unsub_dynamic_sensors is not None:
            try:
                self._unsub_dynamic_sensors()
            except Exception:
                pass
            self._unsub_dynamic_sensors = None

        sensor_entities: list[str] = []
        for key in (CONF_WEATHER_TEMP_ENTITY, CONF_WEATHER_RAIN_ENTITY, CONF_MOBILE_ALARM_ENTITY):
            ent = self._config.get(key)
            if ent and isinstance(ent, str):
                sensor_entities.append(ent)

        if sensor_entities and hasattr(self.hass, "states"):
            @callback
            def _sensor_state_changed(event: Event) -> None:
                entity_id = getattr(event, "data", {}).get("entity_id") if event and hasattr(event, "data") else None
                mobile_ent = self._config.get(CONF_MOBILE_ALARM_ENTITY)
                if entity_id and mobile_ent and entity_id == mobile_ent:
                    self.hass.async_create_task(self._handle_mobile_alarm_state_change())
                elif not entity_id and mobile_ent:
                    self.hass.async_create_task(self._handle_mobile_alarm_state_change())
                else:
                    self.hass.async_create_task(self.async_recalculate_schedule())

            try:
                self._unsub_dynamic_sensors = async_track_state_change_event(
                    self.hass, sensor_entities, _sensor_state_changed
                )
            except Exception as err:
                _LOGGER.debug("Could not attach state change tracker: %s", err)

    async def _handle_mobile_alarm_state_change(self) -> None:
        """Handle state change of the mobile phone alarm sensor (supports bidirectional dismiss/snooze)."""
        if not self._enabled:
            return

        sync_dismiss = self.mobile_dismiss_sync
        is_active = self._status in (STATUS_PRE_ALARM, STATUS_RINGING, STATUS_SNOOZED)

        if is_active and sync_dismiss and self._active_alarm_target:
            new_mobile_dt = self._parse_mobile_alarm_time()
            now = dt_util.now()

            # Target difference: seconds between the new mobile alarm time and the active target
            target_diff = abs((new_mobile_dt - self._active_alarm_target).total_seconds()) if new_mobile_dt else None

            # If the phone alarm time changed from the active target (or became unavailable/None)
            if new_mobile_dt is None or (target_diff is not None and target_diff > 60):
                # Check if it was a snooze on the phone (ringing and new alarm within next 25 minutes)
                is_phone_snooze = (
                    new_mobile_dt is not None
                    and self._status == STATUS_RINGING
                    and now < new_mobile_dt <= now + timedelta(minutes=25)
                )

                if is_phone_snooze:
                    _LOGGER.info(
                        "Smart Wake [%s] Mobile phone alarm was snoozed on device (new time: %s). Synchronizing snooze.",
                        self._name,
                        new_mobile_dt.strftime("%H:%M"),
                    )
                    await self.async_snooze()
                    return
                else:
                    _LOGGER.info(
                        "Smart Wake [%s] Mobile phone alarm was dismissed/turned off on device. Dismissing Smart Wake.",
                        self._name,
                    )
                    await self.async_dismiss()
                    return

        # If not active or after sync check, recalculate normal schedule
        await self.async_recalculate_schedule()

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
        self._active_alarm_target = self._next_alarm

        # If pre-alarm enabled and target is still in future
        if pre_alarm_enabled and self._next_alarm and self._next_alarm > now:
            await self.async_start_pre_alarm()
        else:
            await self.async_start_main_alarm()

    async def async_start_pre_alarm(self) -> None:
        """Trigger Phase 1: Pre-Alarm (Sanftes Wecken)."""
        _LOGGER.info("Smart Wake [%s] starting Phase 1: Pre-Alarm", self._name)
        if not self._active_alarm_target:
            self._active_alarm_target = self._next_alarm
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
        if not self._active_alarm_target:
            self._active_alarm_target = self._next_alarm or dt_util.now()
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
    async def async_snooze(
        self, custom_duration: int | None = None, bypass_max_limit: bool = False
    ) -> bool:
        """Perform snooze action if within maximum snooze limit."""
        if self._status not in (STATUS_RINGING, STATUS_PRE_ALARM):
            _LOGGER.debug("Cannot snooze Smart Wake [%s] while in %s", self._name, self._status)
            return False

        if not bypass_max_limit and self._snooze_count >= self.max_snooze_count:
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
        elif self._is_dry_run:
            self._cancel_dry_run()
            delay_seconds = 10
            display_duration = 1
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
        - If anti-cheat is NOT fulfilled: acts as snooze (even if max snooze reached)!
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
                _LOGGER.info(
                    "Smart Wake [%s] Anti-Cheat conditions not yet fulfilled. Dismiss action pauses/snoozes alarm.",
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

                # Divert to snooze (bypassing max snooze count so audio stops while user gets up to fulfill anti-cheat)
                await self.async_snooze(bypass_max_limit=True)
                return False

        # Final dismissal
        return await self._dismiss_final()

    async def _dismiss_final(self) -> bool:
        """Execute final dismissal, cleaning up state and timers."""
        _LOGGER.info("Smart Wake [%s] dismissed", self._name)
        if self._is_dry_run:
            self._cancel_dry_run()
            self._is_dry_run = False
        self._is_full_test = False
        self._full_test_snooze_seconds = None
        self._anti_cheat_nfc_scanned = False
        self._snooze_until = None
        self._active_alarm_target = None
        self._cancel_phase_timer()
        self._cancel_fade_tasks()
        self._cleanup_listeners()
        await self._stop_media_players()

        # Reset input_boolean helper if configured and ON
        ib = self._config.get(CONF_DISMISS_INPUT_BOOLEAN)
        if ib and hasattr(self.hass, "services") and hasattr(self.hass, "states"):
            st = self.hass.states.get(str(ib).strip())
            if st and str(st.state).lower() in (STATE_ON, "on", "true"):
                try:
                    await self.hass.services.async_call(
                        "input_boolean",
                        "turn_off",
                        {"entity_id": str(ib).strip()},
                        blocking=False,
                    )
                except Exception as err:
                    _LOGGER.debug("Could not reset input_boolean %s: %s", ib, err)

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
        if hasattr(self.hass, "config_entries") and hasattr(self.hass.config_entries, "async_get_entry"):
            entry = self.hass.config_entries.async_get_entry(self.entry_id)
            if entry:
                new_options = dict(getattr(entry, "options", {}))
                new_options[CONF_TIME] = new_time
                self.hass.config_entries.async_update_entry(entry, options=new_options)
        await self.async_recalculate_schedule()
        if hasattr(self.hass, "bus"):
            try:
                self.hass.bus.async_fire(
                    EVENT_SMART_WAKE_STATUS_CHANGED,
                    {
                        "entry_id": self.entry_id,
                        "name": self._name,
                        "status": self._status,
                        "active_phase": self._active_phase,
                        "time": self._time_str,
                    },
                )
            except Exception as err:
                _LOGGER.debug("Could not fire status changed event: %s", err)

    async def async_set_enabled(self, enabled: bool) -> None:
        """Enable or disable alarm."""
        self._enabled = enabled
        self._config[CONF_ENABLED] = enabled
        if hasattr(self.hass, "config_entries") and hasattr(self.hass.config_entries, "async_get_entry"):
            entry = self.hass.config_entries.async_get_entry(self.entry_id)
            if entry:
                new_options = dict(getattr(entry, "options", {}))
                new_options[CONF_ENABLED] = enabled
                self.hass.config_entries.async_update_entry(entry, options=new_options)
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
        tracked_btns = list(dict.fromkeys(b for b in (btn_dismiss, btn_snooze) if b))

        cfg_snooze_events = [
            e.strip().lower()
            for e in str(self._config.get(CONF_SNOOZE_BUTTON_EVENT, "")).split(",")
            if e.strip()
        ]
        cfg_dismiss_events = [
            e.strip().lower()
            for e in str(self._config.get(CONF_DISMISS_BUTTON_EVENT, "")).split(",")
            if e.strip()
        ]

        if tracked_btns:
            @callback
            def _on_btn_event(event: Event) -> None:
                new_state = getattr(event.data, "get", lambda _: None)("new_state") if hasattr(event, "data") else None
                if not new_state:
                    return
                ent_id = getattr(new_state, "entity_id", "")
                val = str(getattr(new_state, "state", "")).lower().strip()

                # Ignore transient/empty or release state transitions
                if not val or val in ("", "unavailable", "unknown", "none", "null", "off", "idle", "standby", "released", "clear"):
                    return

                # Detect if state is an ISO timestamp (e.g. event.*, button.* platforms in Home Assistant)
                is_timestamp = (
                    any(val.startswith(y) for y in ("19", "20"))
                    and ("-" in val or ":" in val or "t" in val)
                )

                attrs = getattr(new_state, "attributes", {}) or {}
                raw_tokens: list[str] = []
                if not is_timestamp:
                    raw_tokens.append(val)

                for k in ("event_type", "action", "click", "command", "press_type", "subtype", "last_action"):
                    val_k = attrs.get(k)
                    if isinstance(val_k, (str, int, float)):
                        s = str(val_k).strip().lower()
                        if s and s not in ("none", "null", "unknown", "unavailable"):
                            raw_tokens.append(s)
                    elif isinstance(val_k, dict):
                        for sub_k in ("event_type", "action", "command", "click"):
                            sub_v = val_k.get(sub_k)
                            if isinstance(sub_v, (str, int, float)):
                                s = str(sub_v).strip().lower()
                                if s and s not in ("none", "null", "unknown", "unavailable"):
                                    raw_tokens.append(s)

                token_words: set[str] = set()
                for tok in raw_tokens:
                    token_words.add(tok)
                    for part in tok.replace("_", " ").replace("-", " ").replace(".", " ").split():
                        token_words.add(part)

                action_text = " ".join(raw_tokens).lower().strip()

                def matches_configured(event_list: list[str]) -> bool:
                    for target in event_list:
                        target = target.strip().lower()
                        if not target:
                            continue
                        if target in token_words:
                            return True
                        if any(target == tok or f"_{target}" in tok or f"{target}_" in tok for tok in raw_tokens):
                            return True
                    return False

                is_configured_dismiss = matches_configured(cfg_dismiss_events)
                is_configured_snooze = matches_configured(cfg_snooze_events)

                # 1. Custom configured event types have highest priority
                if is_configured_dismiss:
                    _LOGGER.info(
                        "Smart Wake [%s] Configured dismiss event detected on %s (%s) -> Dismiss",
                        self._name,
                        ent_id,
                        action_text,
                    )
                    self.hass.async_create_task(self.async_dismiss(forced=False))
                    return

                if is_configured_snooze:
                    _LOGGER.info(
                        "Smart Wake [%s] Configured snooze event detected on %s (%s) -> Snooze",
                        self._name,
                        ent_id,
                        action_text,
                    )
                    self.hass.async_create_task(self.async_snooze())
                    return

                # If a dismiss event was configured (e.g. 'hold'), any press on this button
                # that did NOT match the dismiss event MUST snooze! It must NEVER dismiss!
                if cfg_dismiss_events:
                    _LOGGER.info(
                        "Smart Wake [%s] Non-dismiss event (%s) on button %s with configured dismiss event -> Snooze",
                        self._name,
                        action_text,
                        ent_id,
                    )
                    self.hass.async_create_task(self.async_snooze())
                    return

                # 2. Check dedicated distinct buttons (only if no custom dismiss event was configured)
                if btn_snooze and btn_dismiss and btn_snooze != btn_dismiss:
                    if ent_id == btn_dismiss:
                        _LOGGER.info(
                            "Smart Wake [%s] Dedicated Dismiss button triggered on %s -> Dismiss",
                            self._name,
                            ent_id,
                        )
                        self.hass.async_create_task(self.async_dismiss(forced=False))
                    else:
                        _LOGGER.info(
                            "Smart Wake [%s] Dedicated Snooze button triggered on %s -> Snooze",
                            self._name,
                            ent_id,
                        )
                        self.hass.async_create_task(self.async_snooze())
                    return

                # 3. Default keyword matching (Shared button or single button configured in either field)
                # Check for explicit double-click / multi-click / hold keywords
                is_explicit_dismiss = any(
                    kw in token_words
                    for kw in ("double", "triple", "multi", "hold", "long", "2_click", "double_press", "long_press")
                )

                if is_explicit_dismiss:
                    _LOGGER.info(
                        "Smart Wake [%s] Double-click / Hold detected on %s (%s) -> Dismiss",
                        self._name,
                        ent_id,
                        action_text,
                    )
                    self.hass.async_create_task(self.async_dismiss(forced=False))
                    return

                # Default for single press / any regular button action on button: Snooze!
                _LOGGER.info(
                    "Smart Wake [%s] Single click / press on button %s (%s) -> Snooze",
                    self._name,
                    ent_id,
                    action_text,
                )
                self.hass.async_create_task(self.async_snooze())

            try:
                unsub = async_track_state_change_event(
                    self.hass, tracked_btns, _on_btn_event
                )
                self._unsub_listeners.append(unsub)
            except Exception as err:
                _LOGGER.debug("Could not attach button tracker: %s", err)

        # 5. Input Boolean helper entity -> Dismiss when turned ON
        ib = self._config.get(CONF_DISMISS_INPUT_BOOLEAN)
        if ib and str(ib).strip():
            ib_ent = str(ib).strip()
            @callback
            def _on_ib_change(event: Event) -> None:
                new_state = getattr(event.data, "get", lambda _: None)("new_state") if hasattr(event, "data") else None
                if not new_state:
                    return
                val = str(getattr(new_state, "state", "")).lower()
                if val in (STATE_ON, "on", "true"):
                    _LOGGER.info(
                        "Smart Wake [%s] Input boolean %s turned ON -> Anti-Cheat fulfilled, Dismissing!",
                        self._name,
                        ib_ent,
                    )
                    self.hass.async_create_task(self.async_dismiss(forced=True))

            try:
                unsub = async_track_state_change_event(
                    self.hass, [ib_ent], _on_ib_change
                )
                self._unsub_listeners.append(unsub)
            except Exception as err:
                _LOGGER.debug("Could not attach input_boolean tracker: %s", err)

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

        initial_vol = 0.05 if fade_in else target_vol

        # 1. Set initial quiet volume on all media players first
        for mp_ent in media_players:
            try:
                await self.hass.services.async_call(
                    "media_player",
                    "volume_set",
                    {"entity_id": mp_ent, "volume_level": initial_vol},
                    blocking=False,
                )
            except Exception as err:
                _LOGGER.debug("Initial volume_set failed on %s: %s", mp_ent, err)

        # 2. Wait 0.5s so media players apply the quiet volume BEFORE starting playback
        await asyncio.sleep(0.5)

        # 3. Start playback at the quiet initial volume
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

            # 4. If fade-in is enabled, gently fade volume from initial_vol up to target_vol
            if fade_in:
                task = self.hass.async_create_task(
                    self._fade_volume(mp_ent, initial_vol, target_vol, fade_duration)
                )
                self._fade_tasks.append(task)

        # TTS Greeting (zeitverzögert, pausiert Medienwiedergabe vorher, spricht, setzt danach fort)
        tts_enabled = self._config.get(CONF_MAIN_TTS_ENABLED, DEFAULT_MAIN_TTS_ENABLED)
        tts_player = self._config.get(CONF_MAIN_TTS_MEDIA_PLAYER) or (media_players[0] if media_players else None)
        if tts_enabled and tts_player:
            tts_delay = int(self._config.get(CONF_MAIN_TTS_DELAY, DEFAULT_MAIN_TTS_DELAY))
            if self._is_dry_run:
                tts_delay = min(2, tts_delay)
            self._tts_task = self.hass.async_create_task(
                self._run_tts_sequence(media_players, tts_delay)
            )

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

    async def _run_tts_sequence(
        self, media_players: list[str], delay_seconds: int
    ) -> None:
        """Wait configured delay, pause media playback, speak TTS greeting on dedicated TTS player with custom volume, and resume music playback at original volume."""
        try:
            if delay_seconds > 0:
                await asyncio.sleep(delay_seconds)

            if self._status != STATUS_RINGING and not self._is_dry_run:
                return

            dedicated_tts_player = self._config.get(CONF_MAIN_TTS_MEDIA_PLAYER)
            tts_player = dedicated_tts_player or (media_players[0] if media_players else None)
            if not tts_player:
                _LOGGER.warning("Smart Wake [%s] No media player available for TTS", self._name)
                return

            # A. Record current/target volume of each alarm music player before pause
            target_vol = float(
                self._config.get(
                    CONF_MAIN_AUDIO_TARGET_VOLUME, DEFAULT_MAIN_AUDIO_TARGET_VOLUME
                )
            )
            saved_volumes: dict[str, float] = {}
            for mp_ent in media_players:
                cur_vol = target_vol
                if hasattr(self.hass, "states"):
                    st = self.hass.states.get(mp_ent)
                    if st and "volume_level" in getattr(st, "attributes", {}) and st.attributes["volume_level"] is not None:
                        try:
                            cur_vol = float(st.attributes["volume_level"])
                        except (ValueError, TypeError):
                            pass
                saved_volumes[mp_ent] = cur_vol

            # B. Pause alarm media player(s) before speaking
            for mp_ent in media_players:
                try:
                    await self.hass.services.async_call(
                        "media_player",
                        "media_pause",
                        {"entity_id": mp_ent},
                        blocking=False,
                    )
                except Exception as err:
                    _LOGGER.debug("Could not pause media player %s before TTS: %s", mp_ent, err)

            # Short pause after pause command
            await asyncio.sleep(0.5)

            if self._status != STATUS_RINGING and not self._is_dry_run:
                return

            # C. Set dedicated TTS volume on tts_player
            tts_vol = float(
                self._config.get(CONF_MAIN_TTS_VOLUME, DEFAULT_MAIN_TTS_VOLUME)
            )
            try:
                await self.hass.services.async_call(
                    "media_player",
                    "volume_set",
                    {"entity_id": tts_player, "volume_level": tts_vol},
                    blocking=False,
                )
                await asyncio.sleep(0.3)
            except Exception as err:
                _LOGGER.debug("Could not set volume on TTS player %s: %s", tts_player, err)

            if self._status != STATUS_RINGING and not self._is_dry_run:
                return

            # D. Speak greeting on dedicated TTS player
            await self._speak_greeting(tts_player)

            # E. Wait for TTS output to finish speaking
            raw_msg = self._config.get(CONF_MAIN_TTS_MESSAGE, DEFAULT_MAIN_TTS_MESSAGE)
            word_count = len(str(raw_msg).split())
            speech_duration = 3 if self._is_dry_run else max(5.0, word_count * 0.45 + 2.5)
            await asyncio.sleep(speech_duration)

            if self._status != STATUS_RINGING and not self._is_dry_run:
                return

            # F. Explicitly restore original music volume on alarm media players
            for mp_ent in media_players:
                restore_vol = saved_volumes.get(mp_ent, target_vol)
                try:
                    await self.hass.services.async_call(
                        "media_player",
                        "volume_set",
                        {"entity_id": mp_ent, "volume_level": restore_vol},
                        blocking=False,
                    )
                except Exception as err:
                    _LOGGER.debug("Could not restore volume on %s: %s", mp_ent, err)

            # G. Wait briefly (0.5s) as requested before resuming playback
            await asyncio.sleep(0.5)

            if self._status != STATUS_RINGING and not self._is_dry_run:
                return

            # H. Resume music playback reliably:
            content_id = self._config.get(CONF_MAIN_AUDIO_CONTENT_ID)
            content_type = self._config.get(CONF_MAIN_AUDIO_CONTENT_TYPE, "music")

            for mp_ent in media_players:
                try:
                    if content_id:
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
                    else:
                        await self.hass.services.async_call(
                            "media_player",
                            "media_play",
                            {"entity_id": mp_ent},
                            blocking=False,
                        )
                except Exception as err:
                    _LOGGER.debug("Could not resume media playback on %s: %s", mp_ent, err)
        except asyncio.CancelledError:
            pass
        except Exception as err:
            _LOGGER.error("TTS sequence error for Smart Wake [%s]: %s", self._name, err)

    async def _speak_greeting(self, media_player_entity: str) -> None:
        """Compose and speak morning briefing via TTS (modern tts.speak and legacy fallback)."""
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
            str(raw_msg)
            .replace("{time}", time_text)
            .replace("{temp}", outdoor_temp)
            .replace("{name}", self._name)
        )

        tts_engine = self._config.get(CONF_MAIN_TTS_ENGINE) or ""
        if not tts_engine and hasattr(self.hass, "states") and hasattr(self.hass.states, "async_entity_ids"):
            try:
                for ent_id in self.hass.states.async_entity_ids("tts"):
                    tts_engine = ent_id
                    break
            except Exception:
                pass

        spoken = False

        # 1. Modern HA: tts.speak service
        if hasattr(self.hass, "services") and self.hass.services.has_service("tts", "speak"):
            try:
                service_data: dict[str, Any] = {
                    "media_player_entity_id": media_player_entity,
                    "message": formatted,
                }
                target_dict = (
                    {"entity_id": tts_engine}
                    if (tts_engine and tts_engine.startswith("tts."))
                    else None
                )
                await self.hass.services.async_call(
                    "tts",
                    "speak",
                    service_data,
                    target=target_dict,
                    blocking=False,
                )
                spoken = True
                _LOGGER.info(
                    "Smart Wake [%s] TTS spoken via tts.speak (engine: %s, target: %s)",
                    self._name,
                    tts_engine or "default",
                    media_player_entity,
                )
            except Exception as err:
                _LOGGER.warning("tts.speak attempt failed: %s; trying legacy fallback", err)

        # 2. Legacy HA fallback (e.g. tts.google_translate_say, tts.cloud_say, or custom engine)
        if not spoken and hasattr(self.hass, "services"):
            legacy_service = None
            if tts_engine and "." in tts_engine:
                domain, sname = tts_engine.split(".", 1)
                if self.hass.services.has_service(domain, sname):
                    legacy_service = (domain, sname)
                elif self.hass.services.has_service("tts", f"{sname}_say"):
                    legacy_service = ("tts", f"{sname}_say")

            if not legacy_service and hasattr(self.hass.services, "async_services"):
                try:
                    tts_srvs = self.hass.services.async_services().get("tts", {})
                    for s_key in tts_srvs:
                        if s_key.endswith("_say"):
                            legacy_service = ("tts", s_key)
                            break
                except Exception:
                    pass

            if not legacy_service:
                for candidate in ("google_translate_say", "cloud_say", "piper_say"):
                    if self.hass.services.has_service("tts", candidate):
                        legacy_service = ("tts", candidate)
                        break

            if legacy_service:
                try:
                    await self.hass.services.async_call(
                        legacy_service[0],
                        legacy_service[1],
                        {
                            "entity_id": media_player_entity,
                            "message": formatted,
                        },
                        blocking=False,
                    )
                    spoken = True
                    _LOGGER.info(
                        "Smart Wake [%s] TTS spoken via legacy service %s.%s on %s",
                        self._name,
                        legacy_service[0],
                        legacy_service[1],
                        media_player_entity,
                    )
                except Exception as err:
                    _LOGGER.warning("Legacy TTS service %s failed: %s", legacy_service, err)

        if not spoken:
            _LOGGER.warning(
                "Smart Wake [%s] Could not speak TTS greeting: no compatible TTS service found",
                self._name,
            )

    async def _stop_media_players(self) -> None:
        """Stop all media players configured for this alarm (alarm players and dedicated TTS player)."""
        media_players = self._config.get(CONF_MAIN_MEDIA_PLAYER_ENTITIES, [])
        if isinstance(media_players, str):
            media_players = [media_players]
        else:
            media_players = list(media_players)

        tts_mp = self._config.get(CONF_MAIN_TTS_MEDIA_PLAYER)
        if tts_mp and tts_mp not in media_players:
            media_players.append(tts_mp)

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
        self._setup_active_alarm_listeners()

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
        self._cleanup_listeners()
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
        if self._unsub_dynamic_sensors is not None:
            try:
                self._unsub_dynamic_sensors()
            except Exception:
                pass
            self._unsub_dynamic_sensors = None
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
        if self._tts_task and not self._tts_task.done():
            self._tts_task.cancel()
            self._tts_task = None

    def _notify_update(self) -> None:
        """Broadcast state updates to entities and websocket subscribers."""
        async_dispatcher_send(self.hass, SIGNAL_SMART_WAKE_UPDATED.format(self.entry_id))
        async_dispatcher_send(self.hass, SIGNAL_SMART_WAKE_ALL_UPDATED)
        if hasattr(self.hass, "bus") and not self._is_dry_run:
            try:
                self.hass.bus.async_fire(
                    EVENT_SMART_WAKE_STATUS_CHANGED,
                    {
                        "entry_id": self.entry_id,
                        "name": self._name,
                        "status": self._status,
                        "active_phase": self._active_phase,
                        "time": self._time_str,
                    },
                )
            except Exception as err:
                _LOGGER.debug("Could not fire status changed event: %s", err)

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
