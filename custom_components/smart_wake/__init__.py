"""The Smart Wake custom integration for Home Assistant."""
from __future__ import annotations

import logging
import os
from typing import Any

try:
    from homeassistant.components import panel_custom
    from homeassistant.config_entries import ConfigEntry
    from homeassistant.const import EVENT_HOMEASSISTANT_STARTED
    from homeassistant.core import HomeAssistant
    from homeassistant.helpers.typing import ConfigType
except Exception:
    panel_custom = None
    ConfigEntry = Any
    EVENT_HOMEASSISTANT_STARTED = "homeassistant_started"
    HomeAssistant = Any
    ConfigType = dict

from .const import (
    BRAND_DIR,
    DOMAIN,
    FRONTEND_DIR,
    PLATFORMS,
    URL_BASE,
    URL_BRAND,
    VERSION,
)
from .coordinator import SmartWakeAlarm
from .intent import async_setup_intents
from .services import async_register_services, async_unregister_services
from .websocket import async_register_websocket_api

_LOGGER = logging.getLogger(__name__)


async def async_setup(hass: HomeAssistant, config: ConfigType) -> bool:
    """Set up the Smart Wake integration component."""
    hass.data.setdefault(DOMAIN, {})

    # Register WebSocket API & Services
    async_register_websocket_api(hass)
    async_register_services(hass)

    # Register Voice Assist Intents & sync custom sentences to /config/custom_sentences/
    async_setup_intents(hass)
    _sync_custom_sentences(hass)

    # Register Static HTTP assets & custom sidebar panel
    await _async_setup_frontend(hass)

    return True


def _sync_custom_sentences(hass: HomeAssistant) -> None:
    """Ensure custom sentence files are copied to /config/custom_sentences/<lang>/ so Assist loads them."""
    try:
        if not hasattr(hass, "config") or not hasattr(hass.config, "path"):
            return
        import shutil
        src_base = os.path.join(os.path.dirname(__file__), "custom_sentences")
        if not os.path.isdir(src_base):
            return
        for lang in ("de", "en", "ru"):
            src_file = os.path.join(src_base, lang, "smart_wake.yaml")
            if not os.path.isfile(src_file):
                continue
            dest_dir = hass.config.path("custom_sentences", lang)
            dest_file = os.path.join(dest_dir, "smart_wake.yaml")
            os.makedirs(dest_dir, exist_ok=True)
            shutil.copy2(src_file, dest_file)
            _LOGGER.debug("Synchronized Smart Wake custom sentences to %s", dest_file)
    except Exception as err:
        _LOGGER.debug("Could not auto-sync custom sentences: %s", err)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Smart Wake from a config entry."""
    hass.data.setdefault(DOMAIN, {})

    # Combine entry.data and entry.options
    initial_config = dict(entry.data)
    if entry.options:
        initial_config.update(entry.options)

    alarm = SmartWakeAlarm(hass, entry.entry_id, initial_config)
    await alarm.async_setup()
    hass.data[DOMAIN][entry.entry_id] = alarm

    # Forward setup to all platforms (time, switch, sensor, button, number)
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    # Listen for configuration/options changes
    entry.async_on_unload(entry.add_update_listener(async_reload_entry))

    _LOGGER.info("Smart Wake [%s] set up successfully", alarm.name)
    return True


async def async_reload_entry(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Handle options update by applying new config to the alarm instance."""
    alarm: SmartWakeAlarm | None = hass.data.get(DOMAIN, {}).get(entry.entry_id)
    if alarm:
        new_config = dict(entry.data)
        if entry.options:
            new_config.update(entry.options)
        alarm.update_config(new_config)
        _LOGGER.debug("Updated configuration for Smart Wake [%s]", alarm.name)


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a Smart Wake config entry."""
    alarm: SmartWakeAlarm | None = hass.data.get(DOMAIN, {}).pop(entry.entry_id, None)
    if alarm:
        await alarm.async_unload()

    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)

    # If no more instances exist, unregister services
    if not hass.data[DOMAIN]:
        async_unregister_services(hass)

    return unload_ok


async def _async_setup_frontend(hass: HomeAssistant) -> None:
    """Register HTTP static path and custom sidebar panel."""
    # 1. Register static path for frontend assets and brand files
    if hasattr(hass, "http"):
        if hasattr(hass.http, "async_register_static_paths"):
            try:
                from homeassistant.components.http import StaticPathConfig
                static_configs = [
                    StaticPathConfig(URL_BASE, FRONTEND_DIR, cache_headers=False)
                ]
                if os.path.exists(BRAND_DIR):
                    static_configs.append(StaticPathConfig(URL_BRAND, BRAND_DIR, cache_headers=False))
                await hass.http.async_register_static_paths(static_configs)
            except Exception as err:
                _LOGGER.debug("StaticPathConfig registration error: %s", err)
        elif hasattr(hass.http, "register_static_path"):
            try:
                hass.http.register_static_path(URL_BASE, FRONTEND_DIR, cache_headers=False)
                if os.path.exists(BRAND_DIR):
                    hass.http.register_static_path(URL_BRAND, BRAND_DIR, cache_headers=False)
            except Exception as err:
                _LOGGER.debug("register_static_path error: %s", err)

    version_str = VERSION
    try:
        panel_file = os.path.join(FRONTEND_DIR, "smart-wake-panel.js")
        if os.path.exists(panel_file):
            version_str = f"{version_str}.{int(os.path.getmtime(panel_file))}"
    except Exception:
        pass

    panel_url = f"{URL_BASE}/smart-wake-panel.js?v={version_str}"

    # Clean up any legacy Lovelace card resources if registered
    async def _async_cleanup_legacy_card_resource() -> None:
        try:
            lovelace = hass.data.get("lovelace")
            if not lovelace:
                return
            resources = getattr(lovelace, "resources", None)
            if not resources:
                return
            if not getattr(resources, "loaded", True) and hasattr(resources, "async_load"):
                try:
                    await resources.async_load()
                except Exception:
                    pass
            for item in resources.async_items():
                url = item.get("url", "")
                if url.startswith(f"{URL_BASE}/smart-wake-card.js") and hasattr(resources, "async_delete_item"):
                    await resources.async_delete_item(item["id"])
                    _LOGGER.info("Removed legacy Smart Wake Lovelace card resource: %s", url)
        except Exception as err:
            _LOGGER.debug("Could not clean up legacy Lovelace card resource: %s", err)

    if getattr(hass, "is_running", True):
        hass.async_create_task(_async_cleanup_legacy_card_resource())
    elif hasattr(hass, "bus"):
        async def _on_ha_started(_event: Any) -> None:
            await _async_cleanup_legacy_card_resource()
        hass.bus.async_listen_once(EVENT_HOMEASSISTANT_STARTED, _on_ha_started)

    # 3. Register custom sidebar panel
    if not hass.data.get(f"{DOMAIN}_panel_registered"):
        hass.data[f"{DOMAIN}_panel_registered"] = True
        try:
            if panel_custom and hasattr(panel_custom, "async_register_panel"):
                await panel_custom.async_register_panel(
                    hass=hass,
                    frontend_url_path="smart-wake",
                    webcomponent_name="smart-wake-panel",
                    sidebar_title="Smart Wake",
                    sidebar_icon="mdi:alarm-multiple",
                    module_url=panel_url,
                    embed_iframe=False,
                    require_admin=False,
                )
                _LOGGER.info("Registered Smart Wake sidebar panel at /smart-wake (v=%s)", version_str)
        except Exception as err:
            _LOGGER.error("Failed to register Smart Wake sidebar panel: %s", err)
