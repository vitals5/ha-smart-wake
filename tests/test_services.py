"""Unit tests for Smart Wake services."""
from __future__ import annotations

import unittest
from unittest.mock import AsyncMock, MagicMock

from tests.mock_ha import MockHomeAssistant

from custom_components.smart_wake.const import DOMAIN, STATUS_RINGING
from custom_components.smart_wake.coordinator import SmartWakeAlarm
from custom_components.smart_wake.services import (
    _get_target_alarms,
    async_register_services,
    async_unregister_services,
)


class TestSmartWakeServices(unittest.IsolatedAsyncioTestCase):
    """Test Smart Wake services."""

    async def asyncSetUp(self) -> None:
        """Set up test environment."""
        self.hass = MockHomeAssistant()
        self.alarm = SmartWakeAlarm(self.hass, "entry_1", {"name": "Wecker Schlafzimmer", "time": "06:30"})
        self.hass.data[DOMAIN] = {"entry_1": self.alarm}

    async def test_get_target_alarms(self) -> None:
        """Test target alarm resolution."""
        # By entry ID
        res1 = _get_target_alarms(self.hass, "entry_1")
        self.assertEqual(len(res1), 1)
        self.assertEqual(res1[0].name, "Wecker Schlafzimmer")

        # By name
        res2 = _get_target_alarms(self.hass, "Schlafzimmer")
        self.assertEqual(len(res2), 1)

        # None provided -> returns all
        res3 = _get_target_alarms(self.hass, None)
        self.assertEqual(len(res3), 1)

    async def test_services_registration_and_calls(self) -> None:
        """Test service registration and execution."""
        registered_handlers = {}

        def mock_register(domain, service, handler, schema=None):
            registered_handlers[service] = handler

        self.hass.services.async_register = mock_register

        async_register_services(self.hass)
        self.assertIn("snooze", registered_handlers)
        self.assertIn("dismiss", registered_handlers)
        self.assertIn("set_time", registered_handlers)
        self.assertIn("test_alarm", registered_handlers)
        self.assertIn("start_full_test", registered_handlers)
        self.assertIn("stop_test", registered_handlers)

        # Call snooze service
        self.alarm._status = STATUS_RINGING
        call_mock = MagicMock()
        call_mock.data = {"alarm_id": "entry_1", "duration": 5}
        await registered_handlers["snooze"](call_mock)
        self.assertEqual(self.alarm.snooze_count, 1)

        # Call set_time service
        call_mock.data = {"alarm_id": "entry_1", "time": "07:45"}
        await registered_handlers["set_time"](call_mock)
        self.assertEqual(self.alarm.time_str, "07:45")

        # Call start_full_test service
        call_mock.data = {"alarm_id": "entry_1", "start_from_pre_alarm": False}
        await registered_handlers["start_full_test"](call_mock)
        self.assertTrue(self.alarm.is_full_test)
        self.assertTrue(self.alarm.is_testing)

        # Call stop_test service
        call_mock.data = {"alarm_id": "entry_1"}
        await registered_handlers["stop_test"](call_mock)
        self.assertFalse(self.alarm.is_full_test)
        self.assertFalse(self.alarm.is_testing)

        # Call test_alarm with mode="full"
        call_mock.data = {"alarm_id": "entry_1", "mode": "full", "start_from_pre_alarm": False}
        await registered_handlers["test_alarm"](call_mock)
        self.assertTrue(self.alarm.is_full_test)
        self.assertTrue(self.alarm.is_testing)

        # Unregister
        async_unregister_services(self.hass)


if __name__ == "__main__":
    unittest.main()
