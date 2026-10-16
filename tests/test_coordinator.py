"""Unit tests for Smart Wake Coordinator and Alarm Engine."""
from __future__ import annotations

import asyncio
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch
import unittest

from tests.mock_ha import MockHomeAssistant

from custom_components.smart_wake.const import (
    ALARM_SOURCE_EARLIEST,
    ALARM_SOURCE_FIXED_ONLY,
    ALARM_SOURCE_MOBILE_ONLY,
    ALARM_SOURCE_MOBILE_PRIORITY,
    CONF_ALARM_SOURCE_MODE,
    CONF_CALENDAR_BEHAVIOR,
    CONF_CALENDAR_ENTITY,
    CONF_DAYS,
    CONF_DISMISS_BUTTON_ENTITY,
    CONF_DISMISS_BUTTON_EVENT,
    CONF_DISMISS_INPUT_BOOLEAN,
    CONF_DISMISS_MOTION_ENTITIES,
    CONF_DISMISS_NFC_TAGS,
    CONF_DISMISS_POWER_SENSOR,
    CONF_DISMISS_POWER_THRESHOLD,
    CONF_ENABLED,
    CONF_ESCALATION_DELAY,
    CONF_ESCALATION_ENABLED,
    CONF_ESCALATION_LIGHT_ENTITIES,
    CONF_MAIN_AUDIO_CONTENT_ID,
    CONF_MAIN_MEDIA_PLAYER_ENTITIES,
    CONF_MAIN_TTS_DELAY,
    CONF_MAIN_TTS_ENABLED,
    CONF_MAIN_TTS_MEDIA_PLAYER,
    CONF_MAIN_TTS_VOLUME,
    CONF_MAX_SNOOZE_COUNT,
    CONF_MOBILE_ALARM_ENTITY,
    CONF_MOBILE_DISMISS_SYNC,
    CONF_NAME,
    CONF_PERSON_ENTITIES,
    CONF_PERSON_HOME_REQUIRED,
    CONF_ESCALATION_VOLUME_FADE_DURATION,
    CONF_PRE_ALARM_COVER_ENTITIES,
    CONF_PRE_ALARM_DURATION,
    CONF_PRE_ALARM_ENABLED,
    CONF_PRE_ALARM_LIGHT_ENTITIES,
    CONF_SLEEP_STAGE_ENTITY,
    CONF_SLEEP_STAGE_VALUES,
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
    PHASE_ESCALATION,
    PHASE_MAIN_ALARM,
    PHASE_NONE,
    PHASE_PRE_ALARM,
    STATUS_DISMISSED,
    STATUS_IDLE,
    STATUS_PRE_ALARM,
    STATUS_RINGING,
    STATUS_SKIPPED,
    STATUS_SNOOZED,
)
from custom_components.smart_wake.coordinator import SmartWakeAlarm


class TestSmartWakeCoordinator(unittest.IsolatedAsyncioTestCase):
    """Test SmartWakeAlarm coordinator."""

    async def asyncSetUp(self) -> None:
        """Set up test environment."""
        self.hass = MockHomeAssistant()
        self.config = {
            CONF_NAME: "Wecker Schlafzimmer",
            CONF_TIME: "06:30",
            CONF_ENABLED: True,
            CONF_DAYS: ["mon", "tue", "wed", "thu", "fri", "sat", "sun"],
            CONF_PRE_ALARM_ENABLED: True,
            CONF_PRE_ALARM_DURATION: 15,
            CONF_SNOOZE_DURATION: 9,
            CONF_MAX_SNOOZE_COUNT: 2,
        }
        self.alarm = SmartWakeAlarm(self.hass, "test_1", self.config)

    async def test_initial_state_and_properties(self) -> None:
        """Test properties after setup."""
        self.assertEqual(self.alarm.name, "Wecker Schlafzimmer")
        self.assertTrue(self.alarm.enabled)
        self.assertEqual(self.alarm.time_str, "06:30")
        self.assertEqual(self.alarm.status, STATUS_IDLE)
        self.assertEqual(self.alarm.active_phase, PHASE_NONE)
        self.assertEqual(self.alarm.snooze_count, 0)
        self.assertEqual(self.alarm.snooze_duration, 9)
        self.assertEqual(self.alarm.max_snooze_count, 2)
        self.assertEqual(self.alarm.pre_alarm_duration, 15)

    async def test_schedule_calculation(self) -> None:
        """Test schedule calculation produces next alarm in future."""
        await self.alarm.async_recalculate_schedule()
        self.assertIsNotNone(self.alarm.next_alarm)
        self.assertIsNotNone(self.alarm.pre_alarm_time)
        self.assertGreaterEqual(self.alarm.next_alarm, self.alarm.pre_alarm_time)

    async def test_dynamic_weather_offset(self) -> None:
        """Test early wake offset when freezing or raining."""
        # Set up cold temperature state: -2.5 °C
        temp_state = MagicMock()
        temp_state.state = "-2.5"
        rain_state = MagicMock()
        rain_state.state = "on"

        def get_state(entity_id):
            if entity_id == "sensor.outdoor_temp":
                return temp_state
            if entity_id == "binary_sensor.rain":
                return rain_state
            return None

        self.hass.states.get = get_state

        cfg = dict(self.config)
        cfg[CONF_WEATHER_TEMP_ENTITY] = "sensor.outdoor_temp"
        cfg[CONF_WEATHER_TEMP_THRESHOLD] = 0.0
        cfg[CONF_WEATHER_TEMP_OFFSET] = 15
        cfg[CONF_WEATHER_RAIN_ENTITY] = "binary_sensor.rain"
        cfg[CONF_WEATHER_RAIN_OFFSET] = 10

        alarm = SmartWakeAlarm(self.hass, "test_weather", cfg)
        offset, reasons = alarm._calculate_dynamic_offset()

        self.assertEqual(offset, 25)  # 15m (Frost) + 10m (Regen)
        self.assertEqual(len(reasons), 2)

    async def test_condition_pipeline_workday_only(self) -> None:
        """Test skipping alarm when workday sensor is off."""
        wd_state = MagicMock()
        wd_state.state = "off"
        self.hass.states.get = MagicMock(return_value=wd_state)

        cfg = dict(self.config)
        cfg[CONF_WORKDAY_ONLY] = True
        cfg[CONF_WORKDAY_ENTITY] = "binary_sensor.workday_sensor"

        alarm = SmartWakeAlarm(self.hass, "test_wd", cfg)
        allowed, reason = await alarm.async_evaluate_conditions()
        self.assertFalse(allowed)
        self.assertIn("Kein Werktag", reason)

    async def test_condition_pipeline_person_home(self) -> None:
        """Test skipping alarm when assigned person is not home."""
        person_state = MagicMock()
        person_state.state = "not_home"
        self.hass.states.get = MagicMock(return_value=person_state)

        cfg = dict(self.config)
        cfg[CONF_PERSON_HOME_REQUIRED] = True
        cfg[CONF_PERSON_ENTITIES] = ["person.vitali"]

        alarm = SmartWakeAlarm(self.hass, "test_person", cfg)
        allowed, reason = await alarm.async_evaluate_conditions()
        self.assertFalse(allowed)
        self.assertIn("nicht zu Hause", reason)

    async def test_phase_actions_execution(self) -> None:
        """Test 3-phase execution: Pre-Alarm, Main Alarm, Escalation."""
        cfg = dict(self.config)
        cfg[CONF_PRE_ALARM_LIGHT_ENTITIES] = ["light.bedside"]
        cfg[CONF_PRE_ALARM_COVER_ENTITIES] = ["cover.bedroom"]
        cfg[CONF_MAIN_MEDIA_PLAYER_ENTITIES] = ["media_player.bedroom"]
        cfg[CONF_MAIN_AUDIO_CONTENT_ID] = "http://stream.radio.de"
        cfg[CONF_MAIN_TTS_ENABLED] = True
        cfg[CONF_ESCALATION_LIGHT_ENTITIES] = ["light.bedroom_main"]
        cfg[CONF_ESCALATION_VOLUME_FADE_DURATION] = 10

        alarm = SmartWakeAlarm(self.hass, "test_phases", cfg)

        # 1. Start Pre-Alarm
        await alarm.async_start_pre_alarm()
        self.assertEqual(alarm.status, STATUS_PRE_ALARM)
        self.assertEqual(alarm.active_phase, PHASE_PRE_ALARM)
        self.hass.services.async_call.assert_any_call(
            "light", "turn_on", {"entity_id": "light.bedside", "brightness_pct": 1, "rgb_color": [255, 60, 20]}, blocking=False
        )

        # 2. Start Main Alarm
        await alarm.async_start_main_alarm()
        self.assertEqual(alarm.status, STATUS_RINGING)
        self.assertEqual(alarm.active_phase, PHASE_MAIN_ALARM)

        # 3. Start Escalation (gentle volume rise)
        await alarm.async_start_escalation()
        self.assertEqual(alarm.status, STATUS_RINGING)
        self.assertEqual(alarm.active_phase, PHASE_ESCALATION)
        # Verify light turned on cold white
        self.hass.services.async_call.assert_any_call(
            "light", "turn_on", {"entity_id": "light.bedroom_main", "brightness_pct": 100, "color_temp_kelvin": 6500}, blocking=False
        )

    async def test_snooze_and_max_snooze_limit(self) -> None:
        """Test snooze logic and enforcement of max snooze count limit."""
        alarm = SmartWakeAlarm(self.hass, "test_snooze", self.config)
        alarm._status = STATUS_RINGING
        alarm._active_phase = PHASE_MAIN_ALARM

        # 1st Snooze (allowed, count becomes 1)
        res1 = await alarm.async_snooze()
        self.assertTrue(res1)
        self.assertEqual(alarm.status, STATUS_SNOOZED)
        self.assertEqual(alarm.snooze_count, 1)

        # Simulate ring resume
        alarm._status = STATUS_RINGING

        # 2nd Snooze (allowed, count becomes 2, max reached)
        res2 = await alarm.async_snooze()
        self.assertTrue(res2)
        self.assertEqual(alarm.snooze_count, 2)

        # Simulate ring resume
        alarm._status = STATUS_RINGING

        # 3rd Snooze (blocked!)
        res3 = await alarm.async_snooze()
        self.assertFalse(res3)
        self.assertEqual(alarm.status, STATUS_RINGING)
        self.assertEqual(alarm.snooze_count, 2)

    async def test_dismiss_action(self) -> None:
        """Test dismissing active alarm."""
        alarm = SmartWakeAlarm(self.hass, "test_dismiss", self.config)
        alarm._status = STATUS_RINGING
        alarm._snooze_count = 2

        await alarm.async_dismiss()
        self.assertEqual(alarm.status, STATUS_IDLE)
        self.assertEqual(alarm.active_phase, PHASE_NONE)
        self.assertEqual(alarm.snooze_count, 0)

    async def test_set_time_updates_schedule_and_fires_event(self) -> None:
        """Test changing alarm time recalculates schedule and fires status changed event."""
        mock_entry = MagicMock()
        mock_entry.options = {"time": "06:30"}
        self.hass.config_entries.async_get_entry = MagicMock(return_value=mock_entry)

        alarm = SmartWakeAlarm(self.hass, "test_set_time_entry", self.config)
        self.assertEqual(alarm.time_str, "06:30")

        self.hass.bus.async_fire.reset_mock()
        await alarm.async_set_time("08:15")

        self.assertEqual(alarm.time_str, "08:15")
        self.assertEqual(alarm.config[CONF_TIME], "08:15")
        self.hass.config_entries.async_update_entry.assert_called_with(
            mock_entry, options={"time": "08:15"}
        )

        # Verify event was fired to bus so frontends receive real-time update
        status_event_calls = [
            c for c in self.hass.bus.async_fire.call_args_list
            if c[0][0] == "smart_wake_status_changed"
        ]
        self.assertTrue(len(status_event_calls) >= 1)
        self.assertEqual(status_event_calls[-1][0][1]["time"], "08:15")

    async def test_dry_run_test_mode(self) -> None:
        """Test 30s dry run mode."""
        alarm = SmartWakeAlarm(self.hass, "test_dry_run", self.config)
        await alarm.async_start_dry_run()
        self.assertTrue(alarm.is_dry_run)
        self.assertTrue(alarm.is_testing)
        self.assertEqual(alarm.status, STATUS_PRE_ALARM)

        # Stop dry run
        await alarm.async_stop_dry_run()
        self.assertFalse(alarm.is_dry_run)
        self.assertFalse(alarm.is_testing)
        self.assertEqual(alarm.status, STATUS_IDLE)

    async def test_full_test_mode(self) -> None:
        """Test full test mode (real-time test execution)."""
        alarm = SmartWakeAlarm(self.hass, "test_full_test", self.config)
        self.assertFalse(alarm.is_full_test)
        self.assertFalse(alarm.is_testing)

        # 1. Start full test directly from main alarm
        await alarm.async_start_full_test(start_from_pre_alarm=False)
        self.assertTrue(alarm.is_full_test)
        self.assertTrue(alarm.is_testing)
        self.assertEqual(alarm.status, STATUS_RINGING)
        self.assertEqual(alarm.active_phase, PHASE_MAIN_ALARM)

        # Stop test
        await alarm.async_stop_test()
        self.assertFalse(alarm.is_full_test)
        self.assertFalse(alarm.is_testing)
        self.assertEqual(alarm.status, STATUS_IDLE)

        # 2. Start full test from pre-alarm
        await alarm.async_start_full_test(start_from_pre_alarm=True, pre_alarm_seconds=60)
        self.assertTrue(alarm.is_full_test)
        self.assertTrue(alarm.is_testing)
        self.assertEqual(alarm.status, STATUS_PRE_ALARM)
        self.assertEqual(alarm.active_phase, PHASE_PRE_ALARM)

        # Dismiss during test also ends full test mode
        await alarm.async_dismiss()
        self.assertFalse(alarm.is_full_test)
        self.assertFalse(alarm.is_testing)

    async def test_anti_cheat_dismiss_diverts_to_snooze_when_unfulfilled(self) -> None:
        """Test dismiss diverts to snooze when Anti-Cheat motion condition is not met."""
        motion_state = MagicMock()
        motion_state.state = "off"
        self.hass.states.get = MagicMock(return_value=motion_state)

        cfg = dict(self.config)
        cfg[CONF_DISMISS_MOTION_ENTITIES] = ["binary_sensor.bath_motion"]
        alarm = SmartWakeAlarm(self.hass, "test_ac_divert", cfg)
        alarm._status = STATUS_RINGING

        # Dismiss attempt while still in bed (motion is off)
        dismissed = await alarm.async_dismiss()
        self.assertFalse(dismissed)
        self.assertEqual(alarm.status, STATUS_SNOOZED)
        self.assertEqual(alarm.snooze_count, 1)

        # Another dismiss attempt while still in bed and already snoozed
        dismissed2 = await alarm.async_dismiss()
        self.assertFalse(dismissed2)
        self.assertEqual(alarm.status, STATUS_SNOOZED)
        self.assertEqual(alarm.snooze_count, 1)

    async def test_anti_cheat_dismiss_when_fulfilled(self) -> None:
        """Test dismiss finally succeeds when Anti-Cheat motion condition is fulfilled."""
        motion_state = MagicMock()
        motion_state.state = "on"
        self.hass.states.get = MagicMock(return_value=motion_state)

        cfg = dict(self.config)
        cfg[CONF_DISMISS_MOTION_ENTITIES] = ["binary_sensor.bath_motion"]
        alarm = SmartWakeAlarm(self.hass, "test_ac_fulfill", cfg)
        alarm._status = STATUS_RINGING

        # Motion is already ON (user got out of bed to bathroom)
        dismissed = await alarm.async_dismiss()
        self.assertTrue(dismissed)
        self.assertEqual(alarm.status, STATUS_IDLE)
        self.assertEqual(alarm.snooze_count, 0)

    async def test_anti_cheat_power_sensor_gating(self) -> None:
        """Test dismiss with power sensor below and above threshold."""
        power_state = MagicMock()
        power_state.state = "4.2"  # Below threshold
        self.hass.states.get = MagicMock(return_value=power_state)

        cfg = dict(self.config)
        cfg[CONF_DISMISS_POWER_SENSOR] = "sensor.coffee_power"
        cfg[CONF_DISMISS_POWER_THRESHOLD] = 10.0
        alarm = SmartWakeAlarm(self.hass, "test_ac_power", cfg)
        alarm._status = STATUS_RINGING

        # Below 10W -> Diverts to snooze
        dismissed = await alarm.async_dismiss()
        self.assertFalse(dismissed)
        self.assertEqual(alarm.status, STATUS_SNOOZED)

        # Coffee machine turned on: 45.0W -> Now dismiss succeeds!
        power_state.state = "45.0"
        dismissed2 = await alarm.async_dismiss()
        self.assertTrue(dismissed2)
        self.assertEqual(alarm.status, STATUS_IDLE)

    async def test_full_test_snooze_and_quittieren_with_anti_cheat(self) -> None:
        """Test testing Snooze and Quittieren (incl. Anti-Cheat) in full test mode."""
        motion_state = MagicMock()
        motion_state.state = "off"
        self.hass.states.get = MagicMock(return_value=motion_state)

        cfg = dict(self.config)
        cfg[CONF_DISMISS_MOTION_ENTITIES] = ["binary_sensor.bath_motion"]
        alarm = SmartWakeAlarm(self.hass, "test_full_ac", cfg)

        # 1. Start full test directly into Main Alarm
        await alarm.async_start_full_test(start_from_pre_alarm=False, snooze_seconds=30)
        self.assertTrue(alarm.is_full_test)
        self.assertEqual(alarm.status, STATUS_RINGING)

        # 2. Test manual Snooze in full test mode
        snooze_res = await alarm.async_snooze()
        self.assertTrue(snooze_res)
        self.assertEqual(alarm.status, STATUS_SNOOZED)
        self.assertTrue(alarm.is_full_test)
        self.assertIsNotNone(alarm.snooze_until)

        # 3. Test Quittieren while Anti-Cheat is not met -> must stay snoozed
        dismiss_res = await alarm.async_dismiss()
        self.assertFalse(dismiss_res)
        self.assertEqual(alarm.status, STATUS_SNOOZED)
        self.assertTrue(alarm.is_full_test)

        # 4. Anti-cheat sensor fulfills (motion detected in bathroom)
        motion_state.state = "on"
        dismiss_res2 = await alarm.async_dismiss()
        self.assertTrue(dismiss_res2)
        self.assertEqual(alarm.status, STATUS_IDLE)
        self.assertFalse(alarm.is_full_test)

    async def test_anti_cheat_dismiss_bypasses_max_snooze_count(self) -> None:
        """Test dismiss diverts to snooze even if max snooze limit is reached when anti-cheat conditions are not met."""
        motion_state = MagicMock()
        motion_state.state = "off"
        self.hass.states.get = MagicMock(return_value=motion_state)

        cfg = dict(self.config)
        cfg[CONF_DISMISS_MOTION_ENTITIES] = ["binary_sensor.bath_motion"]
        cfg[CONF_MAX_SNOOZE_COUNT] = 1
        alarm = SmartWakeAlarm(self.hass, "test_ac_bypass_max", cfg)
        alarm._status = STATUS_RINGING

        # 1. Normal snooze consumes the single available snooze
        snooze_res = await alarm.async_snooze()
        self.assertTrue(snooze_res)
        self.assertEqual(alarm.snooze_count, 1)

        # Alarm rings again after snooze
        alarm._status = STATUS_RINGING

        # Normal snooze is now blocked because max snooze limit (1) is reached
        snooze_res2 = await alarm.async_snooze()
        self.assertFalse(snooze_res2)

        # User presses dismiss button in bed (motion still off):
        # Anti-cheat must NOT leave alarm blaring continuously in bed, but divert to snooze with bypass_max_limit=True!
        dismissed = await alarm.async_dismiss()
        self.assertFalse(dismissed)
        self.assertEqual(alarm.status, STATUS_SNOOZED)
        self.assertIsNotNone(alarm.snooze_until)

    async def test_anti_cheat_dismiss_input_boolean(self) -> None:
        """Test input_boolean helper gating for anti-cheat and automatic reset on final dismiss."""
        helper_state = MagicMock()
        helper_state.state = "off"
        self.hass.states.get = MagicMock(return_value=helper_state)

        cfg = dict(self.config)
        cfg[CONF_DISMISS_INPUT_BOOLEAN] = "input_boolean.up_and_awake"
        alarm = SmartWakeAlarm(self.hass, "test_ac_helper", cfg)
        alarm._status = STATUS_RINGING

        # 1. Helper is off -> Anti-cheat unfulfilled -> diverts to snooze
        dismissed = await alarm.async_dismiss()
        self.assertFalse(dismissed)
        self.assertEqual(alarm.status, STATUS_SNOOZED)

        # 2. Helper is switched to 'on' -> Anti-cheat fulfilled -> dismiss succeeds and resets helper to off
        helper_state.state = "on"
        dismissed2 = await alarm.async_dismiss()
        self.assertTrue(dismissed2)
        self.assertEqual(alarm.status, STATUS_IDLE)

        # Verify helper was turned back off
        self.hass.services.async_call.assert_any_call(
            "input_boolean",
            "turn_off",
            {"entity_id": "input_boolean.up_and_awake"},
            blocking=False,
        )

    async def test_hardware_button_single_and_double_click(self) -> None:
        """Test hardware button listener distinguishes single click (snooze) and double click (dismiss)."""
        cfg = dict(self.config)
        cfg[CONF_SNOOZE_BUTTON_ENTITY] = "event.bedside_btn"
        cfg[CONF_DISMISS_BUTTON_ENTITY] = "event.bedside_btn"  # Shared button entity
        alarm = SmartWakeAlarm(self.hass, "test_btn_events", cfg)
        alarm._status = STATUS_RINGING

        from homeassistant.helpers.event import async_track_state_change_event
        async_track_state_change_event.reset_mock()

        # Setup listeners
        alarm._setup_active_alarm_listeners()

        # Find the registered state change listener callback
        track_call = None
        for call in async_track_state_change_event.call_args_list:
            if "event.bedside_btn" in call[0][1]:
                track_call = call[0][2]
                break

        self.assertIsNotNone(track_call, "button state change listener should be registered")

        # 1. Single click on button (keyword state) -> Snoozes alarm
        event_single = MagicMock()
        event_single.data = {
            "entity_id": "event.bedside_btn",
            "new_state": MagicMock(state="single", attributes={"event_type": "single"}),
        }
        track_call(event_single)
        await asyncio.sleep(0.01)
        self.assertEqual(alarm.status, STATUS_SNOOZED)

        # 2. Re-trigger ringing
        alarm._status = STATUS_RINGING

        # 3. Single click on button with HA ISO timestamp state containing '2026' -> MUST Snooze, NOT Dismiss!
        event_timestamp_single = MagicMock()
        event_timestamp_single.data = {
            "entity_id": "event.bedside_btn",
            "new_state": MagicMock(
                state="2026-10-12T20:14:00.123456+00:00",
                attributes={"event_type": "press"},
            ),
        }
        track_call(event_timestamp_single)
        await asyncio.sleep(0.01)
        self.assertEqual(alarm.status, STATUS_SNOOZED, "Timestamp with '2026' must NOT falsely trigger double-click dismiss")

        # 4. Release / empty state transition (e.g. Zigbee clear after 500ms) -> Ignored, stays snoozed
        event_reset = MagicMock()
        event_reset.data = {
            "entity_id": "event.bedside_btn",
            "new_state": MagicMock(state="", attributes={}),
        }
        track_call(event_reset)
        await asyncio.sleep(0.01)
        self.assertEqual(alarm.status, STATUS_SNOOZED)

        # 5. Re-trigger ringing
        alarm._status = STATUS_RINGING

        # 6. Double click on button -> Dismisses alarm
        event_double = MagicMock()
        event_double.data = {
            "entity_id": "event.bedside_btn",
            "new_state": MagicMock(
                state="2026-10-12T20:14:05.123456+00:00",
                attributes={"event_type": "double_press"},
            ),
        }
        track_call(event_double)
        await asyncio.sleep(0.01)
        self.assertEqual(alarm.status, STATUS_IDLE)

    async def test_hardware_button_during_test_run(self) -> None:
        """Test hardware button single click activates snooze during full test run and dry run."""
        from homeassistant.helpers.event import async_track_state_change_event
        async_track_state_change_event.reset_mock()

        cfg = dict(self.config)
        cfg[CONF_DISMISS_BUTTON_ENTITY] = "event.bedside_btn"
        alarm = SmartWakeAlarm(self.hass, "test_btn_in_test_run", cfg)

        # 1. Full test run
        await alarm.async_start_full_test(start_from_pre_alarm=False, snooze_seconds=30)
        self.assertEqual(alarm.status, STATUS_RINGING)
        self.assertTrue(alarm.is_full_test)

        # Find registered listener
        track_call = None
        for call in async_track_state_change_event.call_args_list:
            if "event.bedside_btn" in call[0][1]:
                track_call = call[0][2]
                break
        self.assertIsNotNone(track_call)

        # Button 1x click with ISO timestamp -> Snooze!
        event_click = MagicMock()
        event_click.data = {
            "entity_id": "event.bedside_btn",
            "new_state": MagicMock(state="2026-10-12T20:15:00+00:00", attributes={"event_type": "press"}),
        }
        track_call(event_click)
        await asyncio.sleep(0.01)
        self.assertEqual(alarm.status, STATUS_SNOOZED)
        self.assertTrue(alarm.is_full_test)
        self.assertIsNotNone(alarm.snooze_until)

        # 2. Dry run test
        alarm._status = STATUS_IDLE
        alarm._is_full_test = False
        await alarm.async_start_dry_run()
        alarm._status = STATUS_RINGING  # In dry run Phase 2

        track_call(event_click)
        await asyncio.sleep(0.01)
        self.assertEqual(alarm.status, STATUS_SNOOZED)
        self.assertIsNone(alarm._unsub_dry_run)  # Dry run loop cancelled on snooze

    async def test_dedicated_tts_media_player(self) -> None:
        """Test dedicated TTS media player pauses music player, speaks on TTS player with dedicated volume, and resumes music player."""
        cfg = dict(self.config)
        cfg[CONF_MAIN_MEDIA_PLAYER_ENTITIES] = ["media_player.music_box"]
        cfg[CONF_MAIN_TTS_MEDIA_PLAYER] = "media_player.tts_speaker"
        cfg[CONF_MAIN_TTS_VOLUME] = 0.75
        cfg[CONF_MAIN_AUDIO_CONTENT_ID] = "http://stream.radio/live.mp3"
        cfg[CONF_MAIN_TTS_ENABLED] = True
        cfg[CONF_MAIN_TTS_DELAY] = 0

        alarm = SmartWakeAlarm(self.hass, "test_tts_player", cfg)
        alarm._status = STATUS_RINGING

        # Mock current state of music player with volume_level 0.4
        music_state = MagicMock()
        music_state.attributes = {"volume_level": 0.4}
        self.hass.states.get = MagicMock(side_effect=lambda entity_id: music_state if entity_id == "media_player.music_box" else None)

        # Mock tts engine discovery in hass.states
        tts_state = MagicMock()
        tts_state.entity_id = "tts.piper"
        self.hass.states.async_entity_ids = MagicMock(return_value=["tts.piper"])
        self.hass.services.has_service = MagicMock(return_value=True)

        with patch("asyncio.sleep", new_callable=AsyncMock):
            await alarm._run_tts_sequence(["media_player.music_box"], 0)

        # 1. Verify music player was paused
        self.hass.services.async_call.assert_any_call(
            "media_player",
            "media_pause",
            {"entity_id": "media_player.music_box"},
            blocking=False,
        )

        # 2. Verify TTS player volume was explicitly set to CONF_MAIN_TTS_VOLUME
        self.hass.services.async_call.assert_any_call(
            "media_player",
            "volume_set",
            {"entity_id": "media_player.tts_speaker", "volume_level": 0.75},
            blocking=False,
        )

        # 3. Verify TTS was spoken on dedicated TTS player
        tts_call_found = False
        for call in self.hass.services.async_call.call_args_list:
            if call[0][0] == "tts" and call[0][2].get("media_player_entity_id") == "media_player.tts_speaker":
                tts_call_found = True
                break
        self.assertTrue(tts_call_found, "TTS must be targeted at dedicated TTS player media_player.tts_speaker")

        # 4. Verify music player original volume was restored
        self.hass.services.async_call.assert_any_call(
            "media_player",
            "volume_set",
            {"entity_id": "media_player.music_box", "volume_level": 0.4},
            blocking=False,
        )

        # 5. Verify music player playback was resumed with content_id via play_media
        self.hass.services.async_call.assert_any_call(
            "media_player",
            "play_media",
            {
                "entity_id": "media_player.music_box",
                "media_content_id": "http://stream.radio/live.mp3",
                "media_content_type": "music",
            },
            blocking=False,
        )

    async def test_button_event_type_configuration_and_multi_button_remote(self) -> None:
        """Test explicit button event configuration and multi-button remote buttons."""
        from homeassistant.helpers.event import async_track_state_change_event
        async_track_state_change_event.reset_mock()

        cfg = dict(self.config)
        cfg[CONF_SNOOZE_BUTTON_ENTITY] = "event.bedside_remote"
        cfg[CONF_SNOOZE_BUTTON_EVENT] = "1_single"
        cfg[CONF_DISMISS_BUTTON_ENTITY] = "event.bedside_remote"
        cfg[CONF_DISMISS_BUTTON_EVENT] = "2_single"

        alarm = SmartWakeAlarm(self.hass, "test_custom_btn_events", cfg)
        alarm._status = STATUS_RINGING
        alarm._setup_active_alarm_listeners()

        track_call = None
        for call in async_track_state_change_event.call_args_list:
            if "event.bedside_remote" in call[0][1]:
                track_call = call[0][2]
                break
        self.assertIsNotNone(track_call)

        # 1. Configured snooze event "1_single" triggers Snooze
        event_snooze = MagicMock()
        event_snooze.data = {
            "entity_id": "event.bedside_remote",
            "new_state": MagicMock(state="press", attributes={"event_type": "1_single"}),
        }
        track_call(event_snooze)
        await asyncio.sleep(0.01)
        self.assertEqual(alarm.status, STATUS_SNOOZED)

        # 2. Reset to ringing
        alarm._status = STATUS_RINGING

        # 3. Remote with button 2 single press on unconfigured button must default to Snooze, NOT Dismiss
        cfg2 = dict(self.config)
        cfg2[CONF_SNOOZE_BUTTON_ENTITY] = "event.ikea_remote"
        alarm2 = SmartWakeAlarm(self.hass, "test_ikea_remote", cfg2)
        alarm2._status = STATUS_RINGING
        alarm2._setup_active_alarm_listeners()

        track_call2 = None
        for call in async_track_state_change_event.call_args_list:
            if "event.ikea_remote" in call[0][1]:
                track_call2 = call[0][2]
                break
        self.assertIsNotNone(track_call2)

        event_ikea_btn2 = MagicMock()
        event_ikea_btn2.data = {
            "entity_id": "event.ikea_remote",
            "new_state": MagicMock(state="press", attributes={"event_type": "button_2_single"}),
        }
        track_call2(event_ikea_btn2)
        await asyncio.sleep(0.01)
        self.assertEqual(alarm2.status, STATUS_SNOOZED, "button_2_single must snooze and not be misclassified as double click")

        # 4. Configured dismiss event "2_single" on alarm 1 triggers Dismiss
        alarm._status = STATUS_RINGING
        event_dismiss = MagicMock()
        event_dismiss.data = {
            "entity_id": "event.bedside_remote",
            "new_state": MagicMock(state="press", attributes={"event_type": "2_single"}),
        }
        track_call(event_dismiss)
        await asyncio.sleep(0.01)
        self.assertEqual(alarm.status, STATUS_IDLE)

    async def test_button_snooze_single_and_dismiss_hold_strict_routing(self) -> None:
        """Test single click strictly snoozes and does NOT dismiss when snooze='single' and dismiss='hold'."""
        from homeassistant.helpers.event import async_track_state_change_event
        async_track_state_change_event.reset_mock()

        cfg = dict(self.config)
        cfg[CONF_SNOOZE_BUTTON_ENTITY] = "sensor.zigbee_switch"
        cfg[CONF_SNOOZE_BUTTON_EVENT] = "single"
        cfg[CONF_DISMISS_BUTTON_ENTITY] = "sensor.zigbee_switch"
        cfg[CONF_DISMISS_BUTTON_EVENT] = "hold"

        alarm = SmartWakeAlarm(self.hass, "test_single_hold", cfg)
        alarm._status = STATUS_RINGING
        alarm._setup_active_alarm_listeners()

        track_call = None
        for call in async_track_state_change_event.call_args_list:
            if "sensor.zigbee_switch" in call[0][1]:
                track_call = call[0][2]
                break
        self.assertIsNotNone(track_call)

        # Case 1: Single click with zigbee attributes containing supported event types ['single', 'hold']
        # Must strictly SNOOZE and NOT dismiss due to 'hold' being in the supported types array!
        event_single = MagicMock()
        event_single.data = {
            "entity_id": "sensor.zigbee_switch",
            "new_state": MagicMock(
                state="single",
                attributes={"action": "single", "event_types": ["single", "hold", "double"]},
            ),
        }
        track_call(event_single)
        await asyncio.sleep(0.01)
        self.assertEqual(alarm.status, STATUS_SNOOZED, "Single click must strictly snooze!")

        # Reset alarm to ringing
        alarm._status = STATUS_RINGING

        # Case 2: Hold event must trigger dismiss
        event_hold = MagicMock()
        event_hold.data = {
            "entity_id": "sensor.zigbee_switch",
            "new_state": MagicMock(
                state="hold",
                attributes={"action": "hold", "event_types": ["single", "hold", "double"]},
            ),
        }
        track_call(event_hold)
        await asyncio.sleep(0.01)
        self.assertEqual(alarm.status, STATUS_IDLE, "Hold click must dismiss the alarm!")

    async def test_mobile_alarm_priority_mode_with_phone_alarm(self) -> None:
        """Test mobile_priority mode uses phone alarm when available."""
        from homeassistant.util import dt as dt_util

        now = dt_util.now()
        phone_alarm_time = now + timedelta(hours=2)
        self.hass.states.set("sensor.phone_next_alarm", phone_alarm_time.isoformat())

        cfg = {
            CONF_NAME: "Mobile Test Wecker",
            CONF_TIME: "08:00",
            CONF_ENABLED: True,
            CONF_DAYS: ["mon", "tue", "wed", "thu", "fri", "sat", "sun"],
            CONF_MOBILE_ALARM_ENTITY: "sensor.phone_next_alarm",
            CONF_ALARM_SOURCE_MODE: ALARM_SOURCE_MOBILE_PRIORITY,
            CONF_PRE_ALARM_ENABLED: True,
            CONF_PRE_ALARM_DURATION: 15,
        }
        alarm = SmartWakeAlarm(self.hass, "test_mob_1", cfg)
        await alarm.async_recalculate_schedule()

        self.assertEqual(alarm.active_alarm_source, "mobile")
        self.assertIsNotNone(alarm.next_alarm)
        self.assertEqual(int(alarm.next_alarm.timestamp()), int(phone_alarm_time.timestamp()))
        self.assertEqual(alarm.pre_alarm_time, alarm.next_alarm - timedelta(minutes=15))

    async def test_mobile_alarm_priority_mode_fallback_when_unavailable(self) -> None:
        """Test mobile_priority mode falls back to fixed time when phone alarm is unavailable."""
        self.hass.states.set("sensor.phone_next_alarm", "unavailable")

        cfg = {
            CONF_NAME: "Mobile Test Wecker",
            CONF_TIME: "08:00",
            CONF_ENABLED: True,
            CONF_DAYS: ["mon", "tue", "wed", "thu", "fri", "sat", "sun"],
            CONF_MOBILE_ALARM_ENTITY: "sensor.phone_next_alarm",
            CONF_ALARM_SOURCE_MODE: ALARM_SOURCE_MOBILE_PRIORITY,
            CONF_PRE_ALARM_ENABLED: False,
        }
        alarm = SmartWakeAlarm(self.hass, "test_mob_2", cfg)
        await alarm.async_recalculate_schedule()

        self.assertEqual(alarm.active_alarm_source, "fixed_fallback")
        self.assertIsNotNone(alarm.next_alarm)
        self.assertEqual(alarm.next_alarm.strftime("%H:%M"), "08:00")

    async def test_mobile_alarm_earliest_mode(self) -> None:
        """Test earliest mode picks whichever alarm comes first."""
        from homeassistant.util import dt as dt_util

        now = dt_util.now()
        # Case A: Phone alarm is in 1 hour (earlier than fixed)
        earlier_phone = now + timedelta(hours=1)
        self.hass.states.set("sensor.phone_next_alarm", earlier_phone.isoformat())

        cfg = {
            CONF_NAME: "Earliest Test Wecker",
            CONF_TIME: (now + timedelta(hours=3)).strftime("%H:%M"),
            CONF_ENABLED: True,
            CONF_DAYS: ["mon", "tue", "wed", "thu", "fri", "sat", "sun"],
            CONF_MOBILE_ALARM_ENTITY: "sensor.phone_next_alarm",
            CONF_ALARM_SOURCE_MODE: ALARM_SOURCE_EARLIEST,
            CONF_PRE_ALARM_ENABLED: False,
        }
        alarm = SmartWakeAlarm(self.hass, "test_mob_earliest", cfg)
        await alarm.async_recalculate_schedule()

        self.assertEqual(alarm.active_alarm_source, "mobile")
        self.assertEqual(int(alarm.next_alarm.timestamp()), int(earlier_phone.timestamp()))

        # Case B: Phone alarm is in 5 hours (later than fixed 3 hours)
        later_phone = now + timedelta(hours=5)
        self.hass.states.set("sensor.phone_next_alarm", later_phone.isoformat())
        await alarm.async_recalculate_schedule()

        self.assertEqual(alarm.active_alarm_source, "fixed")

    async def test_mobile_alarm_mobile_only_mode(self) -> None:
        """Test mobile_only mode only rings when mobile alarm is present."""
        from homeassistant.util import dt as dt_util

        now = dt_util.now()
        phone_alarm_time = now + timedelta(hours=4)
        self.hass.states.set("sensor.phone_next_alarm", phone_alarm_time.isoformat())

        cfg = {
            CONF_NAME: "Mobile Only Wecker",
            CONF_TIME: "07:00",
            CONF_ENABLED: True,
            CONF_DAYS: ["mon", "tue", "wed", "thu", "fri", "sat", "sun"],
            CONF_MOBILE_ALARM_ENTITY: "sensor.phone_next_alarm",
            CONF_ALARM_SOURCE_MODE: ALARM_SOURCE_MOBILE_ONLY,
            CONF_PRE_ALARM_ENABLED: False,
        }
        alarm = SmartWakeAlarm(self.hass, "test_mob_only", cfg)
        await alarm.async_recalculate_schedule()

        self.assertEqual(alarm.active_alarm_source, "mobile")
        self.assertIsNotNone(alarm.next_alarm)

        # When phone alarm is disabled / unavailable
        self.hass.states.set("sensor.phone_next_alarm", "none")
        await alarm.async_recalculate_schedule()

        self.assertEqual(alarm.active_alarm_source, "none")
        self.assertIsNone(alarm.next_alarm)
        self.assertIsNone(alarm.pre_alarm_time)

    async def test_mobile_alarm_fixed_only_mode(self) -> None:
        """Test fixed_only mode ignores mobile alarm."""
        from homeassistant.util import dt as dt_util

        now = dt_util.now()
        phone_alarm_time = now + timedelta(hours=1)
        self.hass.states.set("sensor.phone_next_alarm", phone_alarm_time.isoformat())

        cfg = {
            CONF_NAME: "Fixed Only Wecker",
            CONF_TIME: "09:15",
            CONF_ENABLED: True,
            CONF_DAYS: ["mon", "tue", "wed", "thu", "fri", "sat", "sun"],
            CONF_MOBILE_ALARM_ENTITY: "sensor.phone_next_alarm",
            CONF_ALARM_SOURCE_MODE: ALARM_SOURCE_FIXED_ONLY,
            CONF_PRE_ALARM_ENABLED: False,
        }
        alarm = SmartWakeAlarm(self.hass, "test_fixed_only", cfg)
        await alarm.async_recalculate_schedule()

        self.assertEqual(alarm.active_alarm_source, "fixed")
        self.assertEqual(alarm.next_alarm.strftime("%H:%M"), "09:15")

    async def test_mobile_alarm_sensor_state_change_listener(self) -> None:
        """Test that updating mobile alarm sensor recalculates schedule."""
        from homeassistant.helpers.event import async_track_state_change_event
        from homeassistant.util import dt as dt_util

        now = dt_util.now()
        self.hass.states.set("sensor.phone_next_alarm", "unavailable")

        cfg = {
            CONF_NAME: "Listener Test Wecker",
            CONF_TIME: "07:00",
            CONF_ENABLED: True,
            CONF_DAYS: ["mon", "tue", "wed", "thu", "fri", "sat", "sun"],
            CONF_MOBILE_ALARM_ENTITY: "sensor.phone_next_alarm",
            CONF_ALARM_SOURCE_MODE: ALARM_SOURCE_MOBILE_PRIORITY,
            CONF_PRE_ALARM_ENABLED: False,
        }
        alarm = SmartWakeAlarm(self.hass, "test_listener", cfg)
        await alarm.async_setup()

        self.assertEqual(alarm.active_alarm_source, "fixed_fallback")

        # Find registered listener for sensor.phone_next_alarm
        track_call = None
        for call in async_track_state_change_event.call_args_list:
            if "sensor.phone_next_alarm" in call[0][1]:
                track_call = call[0][2]
                break
        self.assertIsNotNone(track_call, "mobile alarm state change listener should be registered")

        # Now simulate companion app updating the sensor
        new_phone_time = now + timedelta(hours=2)
        self.hass.states.set("sensor.phone_next_alarm", new_phone_time.isoformat())
        event = MagicMock()
        event.data = {"entity_id": "sensor.phone_next_alarm"}
        track_call(event)

        # Give async tasks a moment to run
        await asyncio.sleep(0.01)
        self.assertEqual(alarm.active_alarm_source, "mobile")
        self.assertEqual(int(alarm.next_alarm.timestamp()), int(new_phone_time.timestamp()))

    async def test_mobile_dismiss_sync_ringing_dismiss(self) -> None:
        """Test dismissing mobile phone alarm while Smart Wake is ringing dismisses Smart Wake."""
        from homeassistant.util import dt as dt_util

        now = dt_util.now()
        target_time = now + timedelta(seconds=10)
        self.hass.states.set("sensor.phone_next_alarm", target_time.isoformat())

        cfg = {
            CONF_NAME: "Sync Dismiss Wecker",
            CONF_TIME: "07:00",
            CONF_ENABLED: True,
            CONF_DAYS: ["mon", "tue", "wed", "thu", "fri", "sat", "sun"],
            CONF_MOBILE_ALARM_ENTITY: "sensor.phone_next_alarm",
            CONF_MOBILE_DISMISS_SYNC: True,
            CONF_PRE_ALARM_ENABLED: False,
        }
        alarm = SmartWakeAlarm(self.hass, "test_sync_dismiss", cfg)
        await alarm.async_setup()

        # Simulate alarm ringing
        alarm._status = STATUS_RINGING
        alarm._active_phase = PHASE_MAIN_ALARM
        alarm._active_alarm_target = target_time

        # User dismisses alarm on phone -> phone sensor becomes unavailable
        self.hass.states.set("sensor.phone_next_alarm", "unavailable")
        await alarm._handle_mobile_alarm_state_change()

        self.assertEqual(alarm.status, STATUS_IDLE)
        self.assertEqual(alarm.active_phase, PHASE_NONE)
        self.assertIsNone(alarm._active_alarm_target)

    async def test_mobile_dismiss_sync_ringing_snooze(self) -> None:
        """Test snoozing mobile phone alarm while Smart Wake is ringing snoozes Smart Wake."""
        from homeassistant.util import dt as dt_util

        now = dt_util.now()
        target_time = now + timedelta(seconds=10)
        self.hass.states.set("sensor.phone_next_alarm", target_time.isoformat())

        cfg = {
            CONF_NAME: "Sync Snooze Wecker",
            CONF_TIME: "07:00",
            CONF_ENABLED: True,
            CONF_DAYS: ["mon", "tue", "wed", "thu", "fri", "sat", "sun"],
            CONF_MOBILE_ALARM_ENTITY: "sensor.phone_next_alarm",
            CONF_MOBILE_DISMISS_SYNC: True,
            CONF_SNOOZE_DURATION: 9,
            CONF_PRE_ALARM_ENABLED: False,
        }
        alarm = SmartWakeAlarm(self.hass, "test_sync_snooze", cfg)
        await alarm.async_setup()

        # Simulate alarm ringing
        alarm._status = STATUS_RINGING
        alarm._active_phase = PHASE_MAIN_ALARM
        alarm._active_alarm_target = target_time

        # User snoozes alarm on phone -> phone sensor updates to now + 9 minutes
        snooze_time = now + timedelta(minutes=9)
        self.hass.states.set("sensor.phone_next_alarm", snooze_time.isoformat())
        await alarm._handle_mobile_alarm_state_change()

        self.assertEqual(alarm.status, STATUS_SNOOZED)
        self.assertEqual(alarm.snooze_count, 1)

    async def test_mobile_dismiss_sync_pre_alarm_dismiss(self) -> None:
        """Test turning off mobile phone alarm during pre-alarm cancels pre-alarm."""
        from homeassistant.util import dt as dt_util

        now = dt_util.now()
        target_time = now + timedelta(minutes=30)
        self.hass.states.set("sensor.phone_next_alarm", target_time.isoformat())

        cfg = {
            CONF_NAME: "Sync PreAlarm Wecker",
            CONF_TIME: "07:00",
            CONF_ENABLED: True,
            CONF_DAYS: ["mon", "tue", "wed", "thu", "fri", "sat", "sun"],
            CONF_MOBILE_ALARM_ENTITY: "sensor.phone_next_alarm",
            CONF_MOBILE_DISMISS_SYNC: True,
            CONF_PRE_ALARM_ENABLED: True,
            CONF_PRE_ALARM_DURATION: 30,
        }
        alarm = SmartWakeAlarm(self.hass, "test_sync_pre_alarm", cfg)
        await alarm.async_setup()

        # Simulate pre-alarm running
        alarm._status = STATUS_PRE_ALARM
        alarm._active_phase = PHASE_PRE_ALARM
        alarm._active_alarm_target = target_time

        # User cancels tomorrow's / morning alarm on phone (sensor changes or becomes unavailable)
        self.hass.states.set("sensor.phone_next_alarm", "none")
        await alarm._handle_mobile_alarm_state_change()

        self.assertEqual(alarm.status, STATUS_IDLE)
        self.assertEqual(alarm.active_phase, PHASE_NONE)

    async def test_mobile_dismiss_sync_disabled(self) -> None:
        """Test that phone alarm change does not dismiss Smart Wake when mobile_dismiss_sync is False."""
        from homeassistant.util import dt as dt_util

        now = dt_util.now()
        target_time = now + timedelta(seconds=10)
        self.hass.states.set("sensor.phone_next_alarm", target_time.isoformat())

        cfg = {
            CONF_NAME: "Sync Disabled Wecker",
            CONF_TIME: "07:00",
            CONF_ENABLED: True,
            CONF_DAYS: ["mon", "tue", "wed", "thu", "fri", "sat", "sun"],
            CONF_MOBILE_ALARM_ENTITY: "sensor.phone_next_alarm",
            CONF_MOBILE_DISMISS_SYNC: False,
            CONF_PRE_ALARM_ENABLED: False,
        }
        alarm = SmartWakeAlarm(self.hass, "test_sync_disabled", cfg)
        await alarm.async_setup()

        # Simulate alarm ringing
        alarm._status = STATUS_RINGING
        alarm._active_phase = PHASE_MAIN_ALARM
        alarm._active_alarm_target = target_time

        # Phone sensor changes to unavailable
        self.hass.states.set("sensor.phone_next_alarm", "unavailable")
        await alarm._handle_mobile_alarm_state_change()

        # Smart Wake should still be ringing!
        self.assertEqual(alarm.status, STATUS_RINGING)
        self.assertEqual(alarm.active_phase, PHASE_MAIN_ALARM)

    async def test_dynamic_sensor_listener_persists_after_dismiss_and_test(self) -> None:
        """Test that standing dynamic sensor listener is NOT destroyed by dismiss or test stop."""
        from homeassistant.util import dt as dt_util

        now = dt_util.now()
        target_time = now + timedelta(hours=1)
        self.hass.states.set("sensor.phone_next_alarm", target_time.isoformat())

        cfg = {
            CONF_NAME: "Persistence Test Wecker",
            CONF_TIME: "07:00",
            CONF_ENABLED: True,
            CONF_DAYS: ["mon", "tue", "wed", "thu", "fri", "sat", "sun"],
            CONF_MOBILE_ALARM_ENTITY: "sensor.phone_next_alarm",
            CONF_PRE_ALARM_ENABLED: True,
        }
        alarm = SmartWakeAlarm(self.hass, "test_listener_persistence", cfg)
        await alarm.async_setup()
        self.assertIsNotNone(alarm._unsub_dynamic_sensors)

        # 1. Start pre-alarm -> listener must still be alive!
        await alarm.async_start_pre_alarm()
        self.assertIsNotNone(alarm._unsub_dynamic_sensors, "listener must not be killed on pre_alarm start")

        # 2. Start main alarm -> listener must still be alive!
        await alarm.async_start_main_alarm()
        self.assertIsNotNone(alarm._unsub_dynamic_sensors, "listener must not be killed on main_alarm start")

        # 3. Dismiss alarm -> listener must still be alive!
        await alarm.async_dismiss(forced=True)
        self.assertIsNotNone(alarm._unsub_dynamic_sensors, "listener must not be killed on dismiss")

        # 4. Stop dry run test -> listener must still be alive!
        await alarm.async_start_dry_run()
        await alarm.async_stop_dry_run()
        self.assertIsNotNone(alarm._unsub_dynamic_sensors, "listener must not be killed on stop_dry_run")

        # 5. Verify that updating the phone sensor now STILL updates the schedule
        new_phone_time = now + timedelta(hours=3)
        self.hass.states.set("sensor.phone_next_alarm", new_phone_time.isoformat())
        await alarm._handle_mobile_alarm_state_change()
        self.assertEqual(int(alarm.next_alarm.timestamp()), int(new_phone_time.timestamp()))

    async def test_parse_mobile_alarm_time_with_milliseconds_attribute(self) -> None:
        """Test parsing Companion App 'Time in Milliseconds' attribute when state is a formatted string."""
        from homeassistant.util import dt as dt_util

        now = dt_util.now()
        future_time = now + timedelta(hours=4)
        epoch_ms = int(future_time.timestamp() * 1000)

        # Companion App state is sometimes formatted text or local string, while milliseconds is epoch ms
        self.hass.states.set(
            "sensor.phone_next_alarm",
            "Morgen 08:30",
            attributes={"Time in Milliseconds": epoch_ms},
        )

        cfg = {
            CONF_NAME: "Milliseconds Test Wecker",
            CONF_TIME: "07:00",
            CONF_ENABLED: True,
            CONF_DAYS: ["mon", "tue", "wed", "thu", "fri", "sat", "sun"],
            CONF_MOBILE_ALARM_ENTITY: "sensor.phone_next_alarm",
            CONF_PRE_ALARM_ENABLED: False,
        }
        alarm = SmartWakeAlarm(self.hass, "test_ms_attr", cfg)
        await alarm.async_setup()

        self.assertEqual(alarm.active_alarm_source, "mobile")
        self.assertEqual(int(alarm.next_alarm.timestamp()), int(future_time.timestamp()))

    async def test_parse_mobile_alarm_time_with_time_only_format(self) -> None:
        """Test parsing time-only format e.g. from input_datetime helper (e.g. '08:45')."""
        from homeassistant.util import dt as dt_util

        now = dt_util.now()
        # Set phone sensor to 08:45
        self.hass.states.set("sensor.phone_next_alarm", "08:45")

        cfg = {
            CONF_NAME: "Time Only Test Wecker",
            CONF_TIME: "06:00",
            CONF_ENABLED: True,
            CONF_DAYS: ["mon", "tue", "wed", "thu", "fri", "sat", "sun"],
            CONF_MOBILE_ALARM_ENTITY: "sensor.phone_next_alarm",
            CONF_PRE_ALARM_ENABLED: False,
        }
        alarm = SmartWakeAlarm(self.hass, "test_time_only", cfg)
        await alarm.async_setup()

        self.assertEqual(alarm.active_alarm_source, "mobile")
        self.assertEqual(alarm.next_alarm.strftime("%H:%M"), "08:45")

    async def test_parse_mobile_alarm_entity_with_whitespace_and_mixed_case(self) -> None:
        """Test configuring mobile alarm entity with leading/trailing whitespace and mixed case."""
        from homeassistant.util import dt as dt_util

        now = dt_util.now()
        target_time = now + timedelta(hours=2)
        self.hass.states.set("sensor.pixel_7_next_alarm", target_time.isoformat())

        cfg = {
            CONF_NAME: "Casing Test Wecker",
            CONF_TIME: "07:00",
            CONF_ENABLED: True,
            CONF_DAYS: ["mon", "tue", "wed", "thu", "fri", "sat", "sun"],
            CONF_MOBILE_ALARM_ENTITY: "  Sensor.Pixel_7_Next_Alarm  ",
            CONF_PRE_ALARM_ENABLED: False,
        }
        alarm = SmartWakeAlarm(self.hass, "test_casing", cfg)
        await alarm.async_setup()

        self.assertEqual(alarm.active_alarm_source, "mobile")
        self.assertEqual(int(alarm.next_alarm.timestamp()), int(target_time.timestamp()))


if __name__ == "__main__":
    unittest.main()

