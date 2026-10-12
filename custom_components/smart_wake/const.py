"""Constants for the Smart Wake integration."""
from __future__ import annotations

import os

DOMAIN = "smart_wake"
NAME = "Smart Wake"
VERSION = "1.0.11"

# Static assets and frontend paths
URL_BASE = "/smart_wake_frontend"
FRONTEND_DIR = os.path.join(os.path.dirname(__file__), "frontend")
URL_BRAND = "/smart_wake_brand"
BRAND_DIR = os.path.join(os.path.dirname(__file__), "brand")

# Supported platforms
PLATFORMS: list[str] = ["time", "switch", "sensor", "button", "number"]

# Statuses
STATUS_IDLE = "idle"
STATUS_PRE_ALARM = "pre_alarm"
STATUS_RINGING = "ringing"
STATUS_SNOOZED = "snoozed"
STATUS_DISMISSED = "dismissed"
STATUS_SKIPPED = "skipped"

ALL_STATUSES = [
    STATUS_IDLE,
    STATUS_PRE_ALARM,
    STATUS_RINGING,
    STATUS_SNOOZED,
    STATUS_DISMISSED,
    STATUS_SKIPPED,
]

# Phases
PHASE_NONE = "none"
PHASE_PRE_ALARM = "pre_alarm"
PHASE_MAIN_ALARM = "main_alarm"
PHASE_ESCALATION = "escalation"

ALL_PHASES = [
    PHASE_NONE,
    PHASE_PRE_ALARM,
    PHASE_MAIN_ALARM,
    PHASE_ESCALATION,
]

# Days of week
WEEKDAYS = ["mon", "tue", "wed", "thu", "fri", "sat", "sun"]
WEEKDAY_NAMES_DE = {
    "mon": "Mo",
    "tue": "Di",
    "wed": "Mi",
    "thu": "Do",
    "fri": "Fr",
    "sat": "Sa",
    "sun": "So",
}
WEEKDAY_NAMES_EN = {
    "mon": "Mon",
    "tue": "Tue",
    "wed": "Wed",
    "thu": "Thu",
    "fri": "Fri",
    "sat": "Sat",
    "sun": "Sun",
}

# General configuration keys
CONF_NAME = "name"
CONF_TIME = "time"
CONF_ENABLED = "enabled"
CONF_DAYS = "days"
CONF_WORKDAY_ENTITY = "workday_entity"
CONF_WORKDAY_ONLY = "workday_only"
CONF_CALENDAR_ENTITY = "calendar_entity"
CONF_CALENDAR_BEHAVIOR = "calendar_behavior"

CALENDAR_BEHAVIOR_NONE = "none"
CALENDAR_BEHAVIOR_ONLY_IF_EVENT = "only_if_event"
CALENDAR_BEHAVIOR_SKIP_IF_EVENT = "skip_if_event"

# Person tracking & dynamic gating
CONF_PERSON_ENTITIES = "person_entities"
CONF_PERSON_HOME_REQUIRED = "person_home_required"
CONF_WEATHER_TEMP_ENTITY = "weather_temp_entity"
CONF_WEATHER_TEMP_THRESHOLD = "weather_temp_threshold"
CONF_WEATHER_TEMP_OFFSET = "weather_temp_offset"  # minutes earlier
CONF_WEATHER_RAIN_ENTITY = "weather_rain_entity"
CONF_WEATHER_RAIN_OFFSET = "weather_rain_offset"  # minutes earlier
CONF_SLEEP_STAGE_ENTITY = "sleep_stage_entity"
CONF_SLEEP_STAGE_VALUES = "sleep_stage_values"
CONF_SLEEP_STAGE_WINDOW = "sleep_stage_window"  # minutes window before alarm

# Phase 1: Pre-Alarm (Sanftes Wecken)
CONF_PRE_ALARM_ENABLED = "pre_alarm_enabled"
CONF_PRE_ALARM_DURATION = "pre_alarm_duration"  # minutes
CONF_PRE_ALARM_LIGHT_ENTITIES = "pre_alarm_light_entities"
CONF_PRE_ALARM_LIGHT_START_BRIGHTNESS = "pre_alarm_light_start_brightness"
CONF_PRE_ALARM_LIGHT_END_BRIGHTNESS = "pre_alarm_light_end_brightness"
CONF_PRE_ALARM_COVER_ENTITIES = "pre_alarm_cover_entities"
CONF_PRE_ALARM_COVER_POSITION = "pre_alarm_cover_position"
CONF_PRE_ALARM_SCRIPT_ENTITY = "pre_alarm_script_entity"

# Phase 2: Main Alarm (Weckzeitpunkt)
CONF_MAIN_MEDIA_PLAYER_ENTITIES = "main_media_player_entities"
CONF_MAIN_AUDIO_CONTENT_ID = "main_audio_content_id"
CONF_MAIN_AUDIO_CONTENT_TYPE = "main_audio_content_type"
CONF_MAIN_AUDIO_FADE_IN = "main_audio_fade_in"
CONF_MAIN_AUDIO_FADE_DURATION = "main_audio_fade_duration"  # seconds
CONF_MAIN_AUDIO_TARGET_VOLUME = "main_audio_target_volume"  # 0.0 - 1.0
CONF_MAIN_TTS_ENABLED = "main_tts_enabled"
CONF_MAIN_TTS_MESSAGE = "main_tts_message"
CONF_MAIN_TTS_ENGINE = "main_tts_engine"
CONF_MAIN_TTS_DELAY = "main_tts_delay"  # seconds after main alarm start
CONF_MAIN_SCRIPT_ENTITY = "main_script_entity"

# Phase 3: Escalation (Anti-Verschlaf-Schutz)
CONF_ESCALATION_ENABLED = "escalation_enabled"
CONF_ESCALATION_DELAY = "escalation_delay"  # minutes after main alarm
CONF_ESCALATION_VOLUME = "escalation_volume"  # 0.0 - 1.0
CONF_ESCALATION_VOLUME_FADE_DURATION = "escalation_volume_fade_duration"  # seconds for smooth volume rise
CONF_ESCALATION_LIGHT_ENTITIES = "escalation_light_entities"
CONF_ESCALATION_LIGHT_BRIGHTNESS = "escalation_light_brightness"
CONF_ESCALATION_LIGHT_COLD_WHITE = "escalation_light_cold_white"
CONF_ESCALATION_COVER_ENTITIES = "escalation_cover_entities"
CONF_ESCALATION_COVER_POSITION = "escalation_cover_position"
CONF_ESCALATION_SCRIPT_ENTITY = "escalation_script_entity"

# Quittierung & Snooze & Anti-Cheat
CONF_SNOOZE_DURATION = "snooze_duration"  # minutes
CONF_MAX_SNOOZE_COUNT = "max_snooze_count"
CONF_DISMISS_BUTTON_ENTITY = "dismiss_button_entity"
CONF_DISMISS_BUTTON_EVENT = "dismiss_button_event"
CONF_SNOOZE_BUTTON_ENTITY = "snooze_button_entity"
CONF_SNOOZE_BUTTON_EVENT = "snooze_button_event"
CONF_DISMISS_MOTION_ENTITIES = "dismiss_motion_entities"
CONF_DISMISS_NFC_TAGS = "dismiss_nfc_tags"
CONF_DISMISS_POWER_SENSOR = "dismiss_power_sensor"
CONF_DISMISS_POWER_THRESHOLD = "dismiss_power_threshold"  # Watts
CONF_DISMISS_INPUT_BOOLEAN = "dismiss_input_boolean"  # Input boolean entity

# Default values
DEFAULT_NAME = "Smart Wake"
DEFAULT_TIME = "06:30"
DEFAULT_DAYS = ["mon", "tue", "wed", "thu", "fri"]
DEFAULT_WORKDAY_ONLY = False
DEFAULT_CALENDAR_BEHAVIOR = CALENDAR_BEHAVIOR_NONE
DEFAULT_PERSON_HOME_REQUIRED = False
DEFAULT_WEATHER_TEMP_THRESHOLD = 0.0
DEFAULT_WEATHER_TEMP_OFFSET = 15  # 15 minutes earlier
DEFAULT_WEATHER_RAIN_OFFSET = 10  # 10 minutes earlier
DEFAULT_SLEEP_STAGE_WINDOW = 30   # 30 minutes window
DEFAULT_SLEEP_STAGE_VALUES = ["light", "light_sleep", "awake"]

DEFAULT_PRE_ALARM_ENABLED = True
DEFAULT_PRE_ALARM_DURATION = 15
DEFAULT_PRE_ALARM_LIGHT_START_BRIGHTNESS = 1
DEFAULT_PRE_ALARM_LIGHT_END_BRIGHTNESS = 80
DEFAULT_PRE_ALARM_COVER_POSITION = 20

DEFAULT_MAIN_AUDIO_FADE_IN = True
DEFAULT_MAIN_AUDIO_FADE_DURATION = 30
DEFAULT_MAIN_AUDIO_TARGET_VOLUME = 0.5
DEFAULT_MAIN_AUDIO_CONTENT_TYPE = "music"
DEFAULT_MAIN_TTS_ENABLED = False
DEFAULT_MAIN_TTS_MESSAGE = "Guten Morgen! Es ist {time} Uhr."
DEFAULT_MAIN_TTS_DELAY = 15

DEFAULT_ESCALATION_ENABLED = True
DEFAULT_ESCALATION_DELAY = 10
DEFAULT_ESCALATION_VOLUME = 0.9
DEFAULT_ESCALATION_VOLUME_FADE_DURATION = 30
DEFAULT_ESCALATION_LIGHT_BRIGHTNESS = 100
DEFAULT_ESCALATION_LIGHT_COLD_WHITE = True
DEFAULT_ESCALATION_COVER_POSITION = 100

DEFAULT_SNOOZE_DURATION = 9
DEFAULT_MAX_SNOOZE_COUNT = 3
DEFAULT_DISMISS_POWER_THRESHOLD = 10.0
DEFAULT_FULL_TEST_SNOOZE_SECONDS = 30

# Event and Signal definitions
SIGNAL_SMART_WAKE_UPDATED = "smart_wake_updated_{}"
SIGNAL_SMART_WAKE_ALL_UPDATED = "smart_wake_all_updated"

EVENT_SMART_WAKE_STATUS_CHANGED = "smart_wake_status_changed"
EVENT_SMART_WAKE_ALARM_TRIGGERED = "smart_wake_alarm_triggered"
EVENT_SMART_WAKE_PRE_ALARM_STARTED = "smart_wake_pre_alarm_started"
EVENT_SMART_WAKE_ESCALATION_STARTED = "smart_wake_escalation_started"
EVENT_SMART_WAKE_SNOOZED = "smart_wake_snoozed"
EVENT_SMART_WAKE_DISMISSED = "smart_wake_dismissed"
EVENT_SMART_WAKE_SKIPPED = "smart_wake_skipped"
EVENT_SMART_WAKE_ANTI_CHEAT_BLOCKED = "smart_wake_anti_cheat_blocked"

# Dry run test duration
TEST_DRY_RUN_TOTAL_SECONDS = 30
TEST_DRY_RUN_PRE_ALARM_SECONDS = 10
TEST_DRY_RUN_MAIN_SECONDS = 10
TEST_DRY_RUN_ESCALATION_SECONDS = 10
