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
        registered_cmds = {}

        def mock_register(hass, func):
            registered_cmds[func.__name__] = func

        with unittest.mock.patch("custom_components.smart_wake.websocket.websocket_api.async_register_command", side_effect=mock_register):
            async_register_websocket_api(self.hass)
            self.assertGreaterEqual(len(registered_cmds), 11)
            self.assertIn("ws_update_config", registered_cmds)
            self.assertIn("ws_create_alarm", registered_cmds)
            self.assertIn("ws_delete_alarm", registered_cmds)

            # Test update_config
            conn = MagicMock()
            msg = {"id": 1, "alarm_id": "entry_ws", "config": {"time": "07:15", "workday_only": True}}
            await registered_cmds["ws_update_config"](self.hass, conn, msg)
            conn.send_result.assert_called_once()
            res = conn.send_result.call_args[0][1]
            self.assertTrue(res["success"])
            self.assertEqual(res["alarm"]["time"], "07:15")

            # Test create_alarm
            conn_create = MagicMock()
            msg_create = {"id": 2, "name": "Neuer Wecker", "time": "08:00"}
            await registered_cmds["ws_create_alarm"](self.hass, conn_create, msg_create)
            conn_create.send_result.assert_called_once()
            res_create = conn_create.send_result.call_args[0][1]
            self.assertTrue(res_create["success"])

            # Test delete_alarm
            conn_del = MagicMock()
            msg_del = {"id": 3, "alarm_id": "entry_ws"}
            await registered_cmds["ws_delete_alarm"](self.hass, conn_del, msg_del)
            conn_del.send_result.assert_called_once()
            res_del = conn_del.send_result.call_args[0][1]
            self.assertTrue(res_del["success"])
            self.assertEqual(res_del["deleted_id"], "entry_ws")


if __name__ == "__main__":
    unittest.main()
