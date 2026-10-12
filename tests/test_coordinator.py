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
    CONF_ENABLED,
    CONF_ESCALATION_DELAY,
    CONF_ESCALATION_ENABLED,
    CONF_ESCALATION_LIGHT_ENTITIES,
    CONF_MAIN_AUDIO_CONTENT_ID,
    CONF_MAIN_MEDIA_PLAYER_ENTITIES,
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



if __name__ == "__main__":
    unittest.main()
