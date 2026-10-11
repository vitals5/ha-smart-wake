"""Unit tests for Smart Wake WebSocket API."""
from __future__ import annotations

import unittest
from unittest.mock import AsyncMock, MagicMock

from tests.mock_ha import MockHomeAssistant

from custom_components.smart_wake.const import DOMAIN, STATUS_RINGING
from custom_components.smart_wake.coordinator import SmartWakeAlarm
from custom_components.smart_wake.websocket import (
    _format_countdown,
    _serialize_alarm,
    async_register_websocket_api,
)


class TestSmartWakeWebSocket(unittest.IsolatedAsyncioTestCase):
    """Test WebSocket handlers."""

    async def asyncSetUp(self) -> None:
        """Set up test environment."""
        self.hass = MockHomeAssistant()
        self.alarm = SmartWakeAlarm(
            self.hass,
            "entry_ws",
            {"name": "Wecker WS", "time": "06:30", "enabled": True},
        )
        self.hass.data[DOMAIN] = {"entry_ws": self.alarm}

    def test_format_countdown(self) -> None:
        """Test countdown formatter."""
        self.assertIn("in ", _format_countdown(3600))
        self.assertIn("Fällig", _format_countdown(0))

    def test_serialize_alarm(self) -> None:
        """Test alarm serialization for web dashboard."""
        data = _serialize_alarm(self.alarm)
        self.assertEqual(data["id"], "entry_ws")
        self.assertEqual(data["name"], "Wecker WS")
        self.assertEqual(data["time"], "06:30")
        self.assertTrue(data["enabled"])
        self.assertIn("config_summary", data)

    async def test_websocket_commands_registration(self) -> None:
        """Test registration of all websocket commands."""
        registered_cmds = []

        with unittest.mock.patch("custom_components.smart_wake.websocket.websocket_api.async_register_command") as mock_reg:
            async_register_websocket_api(self.hass)
            self.assertGreaterEqual(mock_reg.call_count, 5)


if __name__ == "__main__":
    unittest.main()
