"""Unit tests for Smart Wake Voice Assist intents."""
from __future__ import annotations

import unittest
from unittest.mock import MagicMock

from tests.mock_ha import MockHomeAssistant, MockIntentObj

from custom_components.smart_wake.const import DOMAIN, STATUS_RINGING
from custom_components.smart_wake.coordinator import SmartWakeAlarm
from custom_components.smart_wake.intent import (
    SmartWakeDismissHandler,
    SmartWakeSetStatusHandler,
    SmartWakeSetTimeHandler,
    SmartWakeSnoozeHandler,
    async_setup_intents,
)


class TestSmartWakeIntents(unittest.IsolatedAsyncioTestCase):
    """Test Voice Assist custom intents."""

    async def asyncSetUp(self) -> None:
        """Set up test environment."""
        self.hass = MockHomeAssistant()
        self.alarm = SmartWakeAlarm(
            self.hass,
            "entry_intent",
            {"name": "Schlafzimmer", "time": "06:30", "enabled": True},
        )
        self.hass.data[DOMAIN] = {"entry_intent": self.alarm}

    async def test_set_time_intent(self) -> None:
        """Test SmartWakeSetTime intent."""
        handler = SmartWakeSetTimeHandler()
        intent_obj = MockIntentObj(
            self.hass,
            {"time": {"value": "06:45"}, "alarm": {"value": "Schlafzimmer"}},
        )
        res = await handler.async_handle(intent_obj)
        self.assertEqual(self.alarm.time_str, "06:45")
        self.assertIn("06:45 Uhr", res.speech)

    async def test_set_status_intent(self) -> None:
        """Test SmartWakeSetStatus intent."""
        handler = SmartWakeSetStatusHandler()

        # Turn off
        intent_off = MockIntentObj(
            self.hass,
            {"status": {"value": "aus"}, "alarm": {"value": "Schlafzimmer"}},
        )
        res_off = await handler.async_handle(intent_off)
        self.assertFalse(self.alarm.enabled)
        self.assertIn("ausgeschaltet", res_off.speech)

        # Turn on
        intent_on = MockIntentObj(
            self.hass,
            {"status": {"value": "ein"}, "alarm": {"value": "Schlafzimmer"}},
        )
        res_on = await handler.async_handle(intent_on)
        self.assertTrue(self.alarm.enabled)
        self.assertIn("aktiviert", res_on.speech)

    async def test_snooze_intent(self) -> None:
        """Test SmartWakeSnooze intent."""
        handler = SmartWakeSnoozeHandler()
        self.alarm._status = STATUS_RINGING

        intent_obj = MockIntentObj(
            self.hass,
            {"alarm": {"value": "Schlafzimmer"}, "duration": {"value": 5}},
        )
        res = await handler.async_handle(intent_obj)
        self.assertEqual(self.alarm.snooze_count, 1)
        self.assertIn("5 Minuten weiterschlafen", res.speech)

    async def test_dismiss_intent(self) -> None:
        """Test SmartWakeDismiss intent."""
        handler = SmartWakeDismissHandler()
        self.alarm._status = STATUS_RINGING

        intent_obj = MockIntentObj(
            self.hass,
            {"alarm": {"value": "Schlafzimmer"}},
        )
        res = await handler.async_handle(intent_obj)
        self.assertIn("beendet", res.speech)


if __name__ == "__main__":
    unittest.main()
