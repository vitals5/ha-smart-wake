"""Unit tests for Smart Wake Config Flow and Options Flow."""
from __future__ import annotations

import unittest
from unittest.mock import MagicMock

from tests.mock_ha import MockHomeAssistant

from custom_components.smart_wake.config_flow import (
    SmartWakeConfigFlow,
    SmartWakeOptionsFlowHandler,
)
from custom_components.smart_wake.const import (
    CONF_DAYS,
    CONF_ENABLED,
    CONF_NAME,
    CONF_PRE_ALARM_ENABLED,
    CONF_TIME,
    DOMAIN,
)


class TestSmartWakeConfigFlow(unittest.IsolatedAsyncioTestCase):
    """Test Smart Wake configuration flows."""

    async def asyncSetUp(self) -> None:
        """Set up test environment."""
        self.hass = MockHomeAssistant()

    async def test_config_flow_user_step_init(self) -> None:
        """Test initial form rendering."""
        flow = SmartWakeConfigFlow()
        flow.hass = self.hass

        result = await flow.async_step_user()
        self.assertEqual(result["type"], "form")
        self.assertEqual(result["step_id"], "user")

    async def test_config_flow_user_step_success(self) -> None:
        """Test successful entry creation."""
        flow = SmartWakeConfigFlow()
        flow.hass = self.hass

        user_input = {
            CONF_NAME: "Wecker Schlafzimmer",
            CONF_TIME: "06:30",
            CONF_ENABLED: True,
            CONF_DAYS: ["mon", "tue", "wed", "thu", "fri"],
        }
        result = await flow.async_step_user(user_input)
        self.assertEqual(result["type"], "create_entry")
        self.assertEqual(result["title"], "Wecker Schlafzimmer")
        self.assertEqual(result["data"][CONF_TIME], "06:30")

    async def test_config_flow_duplicate_name_error(self) -> None:
        """Test error when alarm with same name exists."""
        flow = SmartWakeConfigFlow()
        flow.hass = self.hass

        existing = MagicMock()
        existing.data = {CONF_NAME: "Wecker Schlafzimmer"}
        flow._async_current_entries = MagicMock(return_value=[existing])

        user_input = {
            CONF_NAME: "Wecker Schlafzimmer",
            CONF_TIME: "07:00",
            CONF_ENABLED: True,
            CONF_DAYS: ["mon"],
        }
        result = await flow.async_step_user(user_input)
        self.assertEqual(result["type"], "form")
        self.assertIn("already_configured", result["errors"]["base"])

    async def test_options_flow_navigation(self) -> None:
        """Test options flow menu and steps."""
        entry = MagicMock()
        entry.data = {
            CONF_NAME: "Wecker Büro",
            CONF_TIME: "08:00",
            CONF_DAYS: ["mon", "wed"],
        }
        entry.options = {}

        flow = SmartWakeOptionsFlowHandler(entry)
        flow.hass = self.hass

        # Menu step
        menu_res = await flow.async_step_init()
        self.assertEqual(menu_res["type"], "menu")
        self.assertIn("schedule", menu_res["menu_options"])
        self.assertIn("phase1_pre_alarm", menu_res["menu_options"])

        # Schedule step form
        sched_res = await flow.async_step_schedule()
        self.assertEqual(sched_res["type"], "form")

        # Phase 1 step form
        p1_res = await flow.async_step_phase1_pre_alarm()
        self.assertEqual(p1_res["type"], "form")

        # Save phase 1
        p1_save = await flow.async_step_phase1_pre_alarm({CONF_PRE_ALARM_ENABLED: False})
        self.assertEqual(p1_save["type"], "create_entry")
        self.assertFalse(flow._options[CONF_PRE_ALARM_ENABLED])


if __name__ == "__main__":
    unittest.main()
