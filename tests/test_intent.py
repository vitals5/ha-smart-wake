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

    async def test_russian_intents_and_room_aliases(self) -> None:
        """Test Russian language intents and Russian-to-German room alias resolution."""
        # 1. Russian set time using Russian room name "в спальне" for German alarm "Schlafzimmer"
        time_handler = SmartWakeSetTimeHandler()
        intent_time = MockIntentObj(
            self.hass,
            {"time": {"value": "семь часов"}, "alarm": {"value": "в спальне"}},
            language="ru",
        )
        res_time = await time_handler.async_handle(intent_time)
        self.assertEqual(self.alarm.time_str, "07:00")
        self.assertIn("установлен на 07:00", res_time.speech)

        # 2. Russian turn off command
        status_handler = SmartWakeSetStatusHandler()
        intent_status = MockIntentObj(
            self.hass,
            {"status": {"value": "выключить"}, "alarm": {"value": "спальня"}},
            language="ru",
        )
        res_status = await status_handler.async_handle(intent_status)
        self.assertFalse(self.alarm.enabled)
        self.assertIn("выключен", res_status.speech)

        # 3. Russian snooze command
        snooze_handler = SmartWakeSnoozeHandler()
        self.alarm._status = STATUS_RINGING
        intent_snooze = MockIntentObj(
            self.hass,
            {"alarm": {"value": "спальне"}, "duration": {"value": 10}},
            language="ru",
        )
        res_snooze = await snooze_handler.async_handle(intent_snooze)
        self.assertIn("Хорошо, ещё 10 минут сна.", res_snooze.speech)

        # 4. Russian dismiss command
        dismiss_handler = SmartWakeDismissHandler()
        intent_dismiss = MockIntentObj(
            self.hass,
            {"alarm": {"value": "спальне"}},
            language="ru",
        )
        res_dismiss = await dismiss_handler.async_handle(intent_dismiss)
        self.assertIn("Доброе утро!", res_dismiss.speech)


if __name__ == "__main__":
    unittest.main()
