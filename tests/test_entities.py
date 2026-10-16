"""Unit tests for Smart Wake entity platforms."""
from __future__ import annotations

from datetime import time as dt_time
import unittest
from unittest.mock import AsyncMock, MagicMock

from tests.mock_ha import MockHomeAssistant

from custom_components.smart_wake.button import (
    SmartWakeDismissButton,
    SmartWakeFullTestButton,
    SmartWakeSkipNextButton,
    SmartWakeSnoozeButton,
    SmartWakeTestButton,
)
from custom_components.smart_wake.const import (
    CONF_MAX_SNOOZE_COUNT,
    CONF_PRE_ALARM_DURATION,
    CONF_SNOOZE_DURATION,
    STATUS_IDLE,
    STATUS_RINGING,
)
from custom_components.smart_wake.coordinator import SmartWakeAlarm
from custom_components.smart_wake.number import (
    SmartWakeMaxSnoozeCountNumber,
    SmartWakePreAlarmDurationNumber,
    SmartWakeSnoozeDurationNumber,
)
from custom_components.smart_wake.sensor import (
    SmartWakeActivePhaseSensor,
    SmartWakeDynamicOffsetSensor,
    SmartWakeNextAlarmSensor,
    SmartWakeSnoozeCountSensor,
    SmartWakeStatusSensor,
)
from custom_components.smart_wake.switch import SmartWakeSwitchEntity
from custom_components.smart_wake.time import SmartWakeTimeEntity


class TestSmartWakeEntities(unittest.IsolatedAsyncioTestCase):
    """Test all entity platforms."""

    async def asyncSetUp(self) -> None:
        """Set up test environment."""
        self.hass = MockHomeAssistant()
        self.entry = MagicMock()
        self.entry.entry_id = "test_entry_ent"
        self.config = {
            "name": "Wecker Test",
            "time": "07:15",
            "enabled": True,
            "days": ["mon", "tue"],
            CONF_SNOOZE_DURATION: 8,
            CONF_MAX_SNOOZE_COUNT: 4,
            CONF_PRE_ALARM_DURATION: 12,
        }
        self.alarm = SmartWakeAlarm(self.hass, "test_entry_ent", self.config)

    async def test_time_entity(self) -> None:
        """Test SmartWakeTimeEntity."""
        ent = SmartWakeTimeEntity(self.alarm, self.entry)
        self.assertEqual(ent.native_value, dt_time(7, 15))

        await ent.async_set_value(dt_time(8, 30))
        self.assertEqual(self.alarm.time_str, "08:30")

    async def test_switch_entity(self) -> None:
        """Test SmartWakeSwitchEntity."""
        ent = SmartWakeSwitchEntity(self.alarm, self.entry)
        self.assertTrue(ent.is_on)

        await ent.async_turn_off()
        self.assertFalse(self.alarm.enabled)

        await ent.async_turn_on()
        self.assertTrue(self.alarm.enabled)

    async def test_sensor_entities(self) -> None:
        """Test all Smart Wake sensors."""
        status_sensor = SmartWakeStatusSensor(self.alarm, self.entry)
        self.assertEqual(status_sensor.native_value, STATUS_IDLE)
        self.assertEqual(status_sensor.icon, "mdi:alarm")

        next_alarm_sensor = SmartWakeNextAlarmSensor(self.alarm, self.entry)
        self.assertIsNone(next_alarm_sensor.native_value)
        attrs = next_alarm_sensor.extra_state_attributes
        self.assertIn("alarm_source", attrs)
        self.assertEqual(attrs["alarm_source"], "fixed")
        self.assertIn("alarm_source_mode", attrs)
        self.assertIn("mobile_alarm_entity", attrs)
        self.assertIn("mobile_alarm_time", attrs)

        phase_sensor = SmartWakeActivePhaseSensor(self.alarm, self.entry)
        self.assertEqual(phase_sensor.native_value, "none")

        snooze_sensor = SmartWakeSnoozeCountSensor(self.alarm, self.entry)
        self.assertEqual(snooze_sensor.native_value, 0)

        offset_sensor = SmartWakeDynamicOffsetSensor(self.alarm, self.entry)
        self.assertEqual(offset_sensor.native_value, 0)

    async def test_button_entities(self) -> None:
        """Test button entities: snooze, dismiss, test, skip_next."""
        btn_snooze = SmartWakeSnoozeButton(self.alarm, self.entry)
        btn_dismiss = SmartWakeDismissButton(self.alarm, self.entry)
        btn_test = SmartWakeTestButton(self.alarm, self.entry)
        btn_skip = SmartWakeSkipNextButton(self.alarm, self.entry)
        btn_full_test = SmartWakeFullTestButton(self.alarm, self.entry)

        self.alarm._status = STATUS_RINGING
        await btn_snooze.async_press()
        self.assertEqual(self.alarm.snooze_count, 1)

        await btn_dismiss.async_press()
        self.assertEqual(self.alarm.status, STATUS_IDLE)

        await btn_skip.async_press()
        self.assertTrue(self.alarm.skip_next)

        await btn_test.async_press()
        self.assertTrue(self.alarm.is_dry_run)

        # Full test button
        await self.alarm.async_stop_test()
        await btn_full_test.async_press()
        self.assertTrue(self.alarm.is_full_test)
        self.assertTrue(self.alarm.is_testing)

    async def test_number_entities(self) -> None:
        """Test number entities: snooze duration, max snooze, pre-alarm duration."""
        snooze_num = SmartWakeSnoozeDurationNumber(self.alarm, self.entry)
        self.assertEqual(snooze_num.native_value, 8.0)
        await snooze_num.async_set_native_value(10.0)
        self.assertEqual(self.alarm.snooze_duration, 10)

        max_num = SmartWakeMaxSnoozeCountNumber(self.alarm, self.entry)
        self.assertEqual(max_num.native_value, 4.0)
        await max_num.async_set_native_value(5.0)
        self.assertEqual(self.alarm.max_snooze_count, 5)

        pre_num = SmartWakePreAlarmDurationNumber(self.alarm, self.entry)
        self.assertEqual(pre_num.native_value, 12.0)
        await pre_num.async_set_native_value(20.0)
        self.assertEqual(self.alarm.pre_alarm_duration, 20)


if __name__ == "__main__":
    unittest.main()
