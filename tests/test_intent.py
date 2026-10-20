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

    async def test_multilingual_intents_all_languages(self) -> None:
        """Test intent handlers across French, Spanish, Italian, Dutch, Polish, Portuguese."""
        time_handler = SmartWakeSetTimeHandler()
        status_handler = SmartWakeSetStatusHandler()
        snooze_handler = SmartWakeSnoozeHandler()
        dismiss_handler = SmartWakeDismissHandler()

        # French: "chambre" -> "Schlafzimmer"
        res_fr = await time_handler.async_handle(
            MockIntentObj(self.hass, {"time": {"value": "huit heures"}, "alarm": {"value": "chambre"}}, language="fr")
        )
        self.assertEqual(self.alarm.time_str, "08:00")
        self.assertIn("a été réglé à 08:00", res_fr.speech)

        # Spanish: "dormitorio" -> "Schlafzimmer"
        res_es = await status_handler.async_handle(
            MockIntentObj(self.hass, {"status": {"value": "desactivar"}, "alarm": {"value": "dormitorio"}}, language="es")
        )
        self.assertFalse(self.alarm.enabled)
        self.assertIn("desactivado", res_es.speech)

        # Italian: "camera da letto" -> "Schlafzimmer"
        self.alarm._status = STATUS_RINGING
        res_it = await snooze_handler.async_handle(
            MockIntentObj(self.hass, {"alarm": {"value": "camera da letto"}, "duration": {"value": 8}}, language="it")
        )
        self.assertIn("altri 8 minuti", res_it.speech)

        # Dutch: "slaapkamer" -> "Schlafzimmer"
        self.alarm._status = STATUS_RINGING
        res_nl = await dismiss_handler.async_handle(
            MockIntentObj(self.hass, {"alarm": {"value": "slaapkamer"}}, language="nl")
        )
        self.assertIn("Goedemorgen", res_nl.speech)

        # Polish: "sypialnia" -> "Schlafzimmer"
        res_pl = await time_handler.async_handle(
            MockIntentObj(self.hass, {"time": {"value": "siódma"}, "alarm": {"value": "sypialnia"}}, language="pl")
        )
        self.assertEqual(self.alarm.time_str, "07:00")
        self.assertIn("ustawiony na 07:00", res_pl.speech)

        # Portuguese: "quarto" -> "Schlafzimmer"
        res_pt = await status_handler.async_handle(
            MockIntentObj(self.hass, {"status": {"value": "desligar"}, "alarm": {"value": "quarto"}}, language="pt")
        )
        self.assertFalse(self.alarm.enabled)
        self.assertIn("desativado", res_pt.speech)

    async def test_unknown_alarm_name_does_not_fall_back_to_unrelated_alarm(self) -> None:
        """Test that unknown device or room names (e.g. 'Lampe', 'Küche') do not touch unrelated alarms."""
        status_handler = SmartWakeSetStatusHandler()
        self.alarm._enabled = True

        # Non-matching name like 'Lampe'
        intent_lampe = MockIntentObj(
            self.hass,
            {"status": {"value": "aus"}, "alarm": {"value": "Lampe"}},
        )
        res_lampe = await status_handler.async_handle(intent_lampe)
        self.assertTrue(self.alarm.enabled, "Alarm must NOT be disabled when target was 'Lampe'")
        self.assertIn("Es wurde kein passender Smart Wake Wecker gefunden", res_lampe.speech)

        # Non-matching room like 'Küche' when only 'Schlafzimmer' exists
        intent_kueche = MockIntentObj(
            self.hass,
            {"status": {"value": "aus"}, "alarm": {"value": "Küche"}},
        )
        res_kueche = await status_handler.async_handle(intent_kueche)
        self.assertTrue(self.alarm.enabled, "Alarm must NOT be disabled when target was 'Küche'")
        self.assertIn("Es wurde kein passender Smart Wake Wecker gefunden", res_kueche.speech)

    async def test_no_alarm_slot_falls_back_to_single_alarm(self) -> None:
        """Test that generic voice commands without alarm slot toggle the only configured alarm."""
        status_handler = SmartWakeSetStatusHandler()
        self.alarm._enabled = True

        intent_general = MockIntentObj(
            self.hass,
            {"status": {"value": "aus"}},
        )
        res = await status_handler.async_handle(intent_general)
        self.assertFalse(self.alarm.enabled)
        self.assertIn("ausgeschaltet", res.speech)

    async def test_preposition_stripping_in_alarm_name(self) -> None:
        """Test that German and other prepositions ('im Schlafzimmer') resolve correctly."""
        time_handler = SmartWakeSetTimeHandler()
        intent_time = MockIntentObj(
            self.hass,
            {"time": {"value": "08:15"}, "alarm": {"value": "im Schlafzimmer"}},
        )
        res = await time_handler.async_handle(intent_time)
        self.assertEqual(self.alarm.time_str, "08:15")
        self.assertIn("08:15 Uhr", res.speech)

    def test_custom_sentences_do_not_have_optional_alarm_nouns(self) -> None:
        """Ensure that sentence YAMLs do not mark alarm nouns as optional, which would hijack regular device commands."""
        import glob
        import yaml

        for yaml_file in glob.glob("custom_components/smart_wake/custom_sentences/*/*.yaml"):
            with open(yaml_file, "r", encoding="utf-8") as f:
                data = yaml.safe_load(f)

            for intent_name, intent_data in data.get("intents", {}).items():
                for group in intent_data.get("data", []):
                    for sentence in group.get("sentences", []):
                        # Ensure no optional alarm words like [wecker], [alarm], [despertador], [réveil], [sveglia], [budzik]
                        for optional_noun in (
                            "[wecker]", "[alarm]", "[despertador]", "[réveil]", "[sveglia]", "[budzik]", "[wekker]"
                        ):
                            self.assertNotIn(
                                optional_noun,
                                sentence.lower(),
                                f"File {yaml_file} contains optional alarm noun '{optional_noun}' in sentence: '{sentence}'! "
                                "This causes Assist to hijack regular device commands like 'Lampe an'."
                            )


if __name__ == "__main__":
    unittest.main()
