"""Unit tests for Smart Wake __init__.py lifecycle."""
from __future__ import annotations

import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
import unittest

from tests.mock_ha import MockHomeAssistant

from custom_components.smart_wake import (
    async_reload_entry,
    async_setup,
    async_setup_entry,
    async_unload_entry,
)
from custom_components.smart_wake.const import DOMAIN, PLATFORMS


class TestSmartWakeInit(unittest.IsolatedAsyncioTestCase):
    """Test Smart Wake setup and lifecycle."""

    async def asyncSetUp(self) -> None:
        """Set up test environment."""
        self.hass = MockHomeAssistant()

    async def test_async_setup(self) -> None:
        """Test integration root setup."""
        res = await async_setup(self.hass, {})
        self.assertTrue(res)
        self.assertIn(DOMAIN, self.hass.data)

    async def test_async_setup_and_unload_entry(self) -> None:
        """Test setup and unload of a config entry."""
        entry = MagicMock()
        entry.entry_id = "test_entry_123"
        entry.data = {
            "name": "Wecker Schlafzimmer",
            "time": "06:30",
            "enabled": True,
            "days": ["mon", "tue", "wed", "thu", "fri"],
        }
        entry.options = {}
        entry.async_on_unload = MagicMock()
        entry.add_update_listener = MagicMock()

        # Setup entry
        res = await async_setup_entry(self.hass, entry)
        self.assertTrue(res)
        self.assertIn("test_entry_123", self.hass.data[DOMAIN])
        alarm = self.hass.data[DOMAIN]["test_entry_123"]
        self.assertEqual(alarm.name, "Wecker Schlafzimmer")
        self.assertEqual(alarm.time_str, "06:30")

        # Test reload listener
        entry.options = {"time": "07:15"}
        await async_reload_entry(self.hass, entry)
        self.assertEqual(alarm.time_str, "07:15")

        # Unload entry
        unload_res = await async_unload_entry(self.hass, entry)
        self.assertTrue(unload_res)
        self.assertNotIn("test_entry_123", self.hass.data[DOMAIN])


if __name__ == "__main__":
    unittest.main()
