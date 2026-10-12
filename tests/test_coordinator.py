"""Unit tests for Smart Wake Coordinator and Alarm Engine."""
from __future__ import annotations

import asyncio
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch
import unittest

from tests.mock_ha import MockHomeAssistant

from custom_components.smart_wake.const import (
    CONF_CALENDAR_BEHAVIOR,
    CONF_CALENDAR_ENTITY,
    CONF_DAYS,
    CONF_DISMISS_BUTTON_ENTITY,
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
    CONF_MAX_SNOOZE_COUNT,
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

        # Setup listeners
        alarm._setup_active_alarm_listeners()

        from homeassistant.helpers.event import async_track_state_change_event

        # Find the registered state change listener callback
        track_call = None
        for call in async_track_state_change_event.call_args_list:
            if "event.bedside_btn" in call[0][1]:
                track_call = call[0][2]
                break

        self.assertIsNotNone(track_call, "button state change listener should be registered")

        # 1. Single click on button -> Snoozes alarm
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

        # 3. Double click on button -> Dismisses alarm
        event_double = MagicMock()
        event_double.data = {
            "entity_id": "event.bedside_btn",
            "new_state": MagicMock(state="double", attributes={"event_type": "double"}),
        }
        track_call(event_double)
        await asyncio.sleep(0.01)
        self.assertEqual(alarm.status, STATUS_IDLE)


if __name__ == "__main__":
    unittest.main()
