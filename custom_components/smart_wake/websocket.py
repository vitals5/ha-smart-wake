"""WebSocket API handlers for Smart Wake dashboard."""
from __future__ import annotations

from datetime import datetime
import logging
from typing import Any

try:
    import voluptuous as vol
except ImportError:
    class vol:  # type: ignore
        @staticmethod
        def Schema(s: Any) -> Any:
            return s
        @staticmethod
        def Required(k: Any, **kwargs: Any) -> Any:
            return k
        @staticmethod
        def Optional(k: Any, **kwargs: Any) -> Any:
            return k
        @staticmethod
        def Coerce(t: Any) -> Any:
            return t

try:
    from homeassistant.components import websocket_api
    from homeassistant.core import HomeAssistant, callback
    from homeassistant.util import dt as dt_util
except Exception:
    class websocket_api:
        ActiveConnection = Any
        @staticmethod
        def websocket_command(schema: Any) -> Any:
            def decorator(func: Any) -> Any:
                return func
            return decorator
        @staticmethod
        def async_response(func: Any) -> Any:
            return func
    HomeAssistant = Any
    def callback(func: Any) -> Any:
        return func
    class MockDtUtil:
        @staticmethod
        def now() -> datetime:
            return datetime.now().astimezone()
    dt_util = MockDtUtil()

from .const import (
    CONF_DAYS,
    CONF_DISMISS_BUTTON_ENTITY,
    CONF_DISMISS_MOTION_ENTITIES,
    CONF_DISMISS_NFC_TAGS,
    CONF_DISMISS_POWER_SENSOR,
    CONF_ENABLED,
    CONF_ESCALATION_DELAY,
    CONF_ESCALATION_VOLUME,
    CONF_MAIN_AUDIO_CONTENT_ID,
    CONF_MAIN_MEDIA_PLAYER_ENTITIES,
    CONF_MAIN_TTS_ENABLED,
    CONF_NAME,
    CONF_PERSON_ENTITIES,
    CONF_PERSON_HOME_REQUIRED,
    CONF_PRE_ALARM_CLIMATE_ENTITIES,
    CONF_PRE_ALARM_COVER_ENTITIES,
    CONF_PRE_ALARM_DURATION,
    CONF_PRE_ALARM_LIGHT_ENTITIES,
    CONF_TIME,
    CONF_WEATHER_TEMP_ENTITY,
    CONF_WORKDAY_ENTITY,
    CONF_WORKDAY_ONLY,
    DOMAIN,
)
from .coordinator import SmartWakeAlarm

_LOGGER = logging.getLogger(__name__)


def _format_countdown(seconds: float) -> str:
    """Format seconds into human-readable German countdown text."""
    if seconds <= 0:
        return "Fällig / Klingelt jetzt"
    total_seconds = int(seconds)
    days = total_seconds // 86400
    hours = (total_seconds % 86400) // 3600
    minutes = (total_seconds % 3600) // 60

    parts: list[str] = []
    if days > 0:
        parts.append(f"{days} T.")
    if hours > 0:
        parts.append(f"{hours} Std.")
    parts.append(f"{minutes} Min.")
    return "in " + " ".join(parts)


def _serialize_alarm(alarm: SmartWakeAlarm) -> dict[str, Any]:
    """Serialize an alarm instance for the web dashboard."""
    now = dt_util.now()
    countdown_secs: float = 0.0
    countdown_text = "Deaktiviert"

    if alarm.enabled and alarm.next_alarm:
        countdown_secs = max(0.0, (alarm.next_alarm - now).total_seconds())
        countdown_text = _format_countdown(countdown_secs)

    cfg = alarm.config
    return {
        "id": alarm.entry_id,
        "name": alarm.name,
        "enabled": alarm.enabled,
        "time": alarm.time_str,
        "days": alarm.days,
        "status": alarm.status,
        "active_phase": alarm.active_phase,
        "next_alarm": alarm.next_alarm.isoformat() if alarm.next_alarm else None,
        "pre_alarm_time": alarm.pre_alarm_time.isoformat() if alarm.pre_alarm_time else None,
        "countdown_seconds": countdown_secs,
        "countdown_text": countdown_text,
        "snooze_count": alarm.snooze_count,
        "snooze_duration": alarm.snooze_duration,
        "max_snooze_count": alarm.max_snooze_count,
        "pre_alarm_duration": alarm.pre_alarm_duration,
        "dynamic_offset_minutes": alarm.dynamic_offset_minutes,
        "offset_reasons": alarm.offset_reasons,
        "is_dry_run": alarm.is_dry_run,
        "dry_run_progress": alarm.dry_run_progress,
        "skip_next": alarm.skip_next,
        "config": dict(cfg),
        "config_summary": {
            "workday_only": cfg.get(CONF_WORKDAY_ONLY, False),
            "workday_entity": cfg.get(CONF_WORKDAY_ENTITY),
            "person_entities": cfg.get(CONF_PERSON_ENTITIES, []),
            "person_home_required": cfg.get(CONF_PERSON_HOME_REQUIRED, False),
            "weather_temp_entity": cfg.get(CONF_WEATHER_TEMP_ENTITY),
            "pre_alarm_lights": cfg.get(CONF_PRE_ALARM_LIGHT_ENTITIES, []),
            "pre_alarm_covers": cfg.get(CONF_PRE_ALARM_COVER_ENTITIES, []),
            "pre_alarm_climates": cfg.get(CONF_PRE_ALARM_CLIMATE_ENTITIES, []),
            "main_media_players": cfg.get(CONF_MAIN_MEDIA_PLAYER_ENTITIES, []),
            "main_audio_content": cfg.get(CONF_MAIN_AUDIO_CONTENT_ID),
            "main_tts_enabled": cfg.get(CONF_MAIN_TTS_ENABLED, False),
            "escalation_delay": cfg.get(CONF_ESCALATION_DELAY, 10),
            "escalation_volume": cfg.get(CONF_ESCALATION_VOLUME, 0.9),
            "dismiss_button": cfg.get(CONF_DISMISS_BUTTON_ENTITY),
            "dismiss_motion": cfg.get(CONF_DISMISS_MOTION_ENTITIES, []),
            "dismiss_nfc": cfg.get(CONF_DISMISS_NFC_TAGS, []),
            "dismiss_power": cfg.get(CONF_DISMISS_POWER_SENSOR),
        },
    }


def async_register_websocket_api(hass: HomeAssistant) -> None:
    """Register all Smart Wake WebSocket commands."""

    def _get_alarm(alarm_id: str) -> SmartWakeAlarm | None:
        domain_data: dict[str, SmartWakeAlarm] = hass.data.get(DOMAIN, {})
        if alarm_id in domain_data:
            return domain_data[alarm_id]
        for a in domain_data.values():
            if a.name.lower() == alarm_id.lower():
                return a
        return None

    # 1. smart_wake/get_alarms
    @websocket_api.websocket_command({vol.Required("type"): "smart_wake/get_alarms"})
    @websocket_api.async_response
    async def ws_get_alarms(
        hass: HomeAssistant, connection: websocket_api.ActiveConnection, msg: dict[str, Any]
    ) -> None:
        """Handle request for all Smart Wake alarms."""
        domain_data: dict[str, SmartWakeAlarm] = hass.data.get(DOMAIN, {})
        alarms = [_serialize_alarm(a) for a in domain_data.values()]
        connection.send_result(msg["id"], {"alarms": alarms})

    # 2. smart_wake/test_alarm
    @websocket_api.websocket_command({
        vol.Required("type"): "smart_wake/test_alarm",
        vol.Required("alarm_id"): str,
    })
    @websocket_api.async_response
    async def ws_test_alarm(
        hass: HomeAssistant, connection: websocket_api.ActiveConnection, msg: dict[str, Any]
    ) -> None:
        """Handle start 30s dry run test."""
        alarm = _get_alarm(msg["alarm_id"])
        if not alarm:
            connection.send_error(msg["id"], "alarm_not_found", "Alarm instance not found")
            return
        await alarm.async_start_dry_run()
        connection.send_result(msg["id"], {"success": True, "alarm": _serialize_alarm(alarm)})

    # 3. smart_wake/stop_test
    @websocket_api.websocket_command({
        vol.Required("type"): "smart_wake/stop_test",
        vol.Required("alarm_id"): str,
    })
    @websocket_api.async_response
    async def ws_stop_test(
        hass: HomeAssistant, connection: websocket_api.ActiveConnection, msg: dict[str, Any]
    ) -> None:
        """Handle stop dry run test."""
        alarm = _get_alarm(msg["alarm_id"])
        if not alarm:
            connection.send_error(msg["id"], "alarm_not_found", "Alarm instance not found")
            return
        await alarm.async_stop_dry_run()
        connection.send_result(msg["id"], {"success": True, "alarm": _serialize_alarm(alarm)})

    # 4. smart_wake/snooze
    @websocket_api.websocket_command({
        vol.Required("type"): "smart_wake/snooze",
        vol.Required("alarm_id"): str,
        vol.Optional("duration"): vol.Coerce(int),
    })
    @websocket_api.async_response
    async def ws_snooze(
        hass: HomeAssistant, connection: websocket_api.ActiveConnection, msg: dict[str, Any]
    ) -> None:
        """Handle snooze command from dashboard."""
        alarm = _get_alarm(msg["alarm_id"])
        if not alarm:
            connection.send_error(msg["id"], "alarm_not_found", "Alarm instance not found")
            return
        res = await alarm.async_snooze(custom_duration=msg.get("duration"))
        connection.send_result(
            msg["id"],
            {"success": res, "snoozed": res, "alarm": _serialize_alarm(alarm)},
        )

    # 5. smart_wake/dismiss
    @websocket_api.websocket_command({
        vol.Required("type"): "smart_wake/dismiss",
        vol.Required("alarm_id"): str,
    })
    @websocket_api.async_response
    async def ws_dismiss(
        hass: HomeAssistant, connection: websocket_api.ActiveConnection, msg: dict[str, Any]
    ) -> None:
        """Handle dismiss command from dashboard."""
        alarm = _get_alarm(msg["alarm_id"])
        if not alarm:
            connection.send_error(msg["id"], "alarm_not_found", "Alarm instance not found")
            return
        await alarm.async_dismiss()
        connection.send_result(msg["id"], {"success": True, "alarm": _serialize_alarm(alarm)})

    # 6. smart_wake/toggle
    @websocket_api.websocket_command({
        vol.Required("type"): "smart_wake/toggle",
        vol.Required("alarm_id"): str,
        vol.Optional("enabled"): bool,
    })
    @websocket_api.async_response
    async def ws_toggle(
        hass: HomeAssistant, connection: websocket_api.ActiveConnection, msg: dict[str, Any]
    ) -> None:
        """Handle toggle enabled/disabled command."""
        alarm = _get_alarm(msg["alarm_id"])
        if not alarm:
            connection.send_error(msg["id"], "alarm_not_found", "Alarm instance not found")
            return
        new_state = msg.get("enabled", not alarm.enabled)
        await alarm.async_set_enabled(new_state)
        connection.send_result(msg["id"], {"success": True, "alarm": _serialize_alarm(alarm)})

    # 7. smart_wake/set_time
    @websocket_api.websocket_command({
        vol.Required("type"): "smart_wake/set_time",
        vol.Required("alarm_id"): str,
        vol.Required("time"): str,
    })
    @websocket_api.async_response
    async def ws_set_time(
        hass: HomeAssistant, connection: websocket_api.ActiveConnection, msg: dict[str, Any]
    ) -> None:
        """Handle setting alarm time from dashboard."""
        alarm = _get_alarm(msg["alarm_id"])
        if not alarm:
            connection.send_error(msg["id"], "alarm_not_found", "Alarm instance not found")
            return
        await alarm.async_set_time(msg["time"])
        connection.send_result(msg["id"], {"success": True, "alarm": _serialize_alarm(alarm)})

    # 8. smart_wake/skip_next
    @websocket_api.websocket_command({
        vol.Required("type"): "smart_wake/skip_next",
        vol.Required("alarm_id"): str,
        vol.Optional("skip"): bool,
    })
    @websocket_api.async_response
    async def ws_skip_next(
        hass: HomeAssistant, connection: websocket_api.ActiveConnection, msg: dict[str, Any]
    ) -> None:
        """Handle skip next alarm."""
        alarm = _get_alarm(msg["alarm_id"])
        if not alarm:
            connection.send_error(msg["id"], "alarm_not_found", "Alarm instance not found")
            return
        skip_val = msg.get("skip", not alarm.skip_next)
        alarm.set_skip_next(skip_val)
        connection.send_result(msg["id"], {"success": True, "alarm": _serialize_alarm(alarm)})

    # 9. smart_wake/update_config
    @websocket_api.websocket_command({
        vol.Required("type"): "smart_wake/update_config",
        vol.Required("alarm_id"): str,
        vol.Required("config"): dict,
    })
    @websocket_api.async_response
    async def ws_update_config(
        hass: HomeAssistant, connection: websocket_api.ActiveConnection, msg: dict[str, Any]
    ) -> None:
        """Handle updating full alarm configuration from side-panel dashboard."""
        alarm = _get_alarm(msg["alarm_id"])
        if not alarm:
            connection.send_error(msg["id"], "alarm_not_found", "Alarm instance not found")
            return

        new_config_data = dict(msg["config"])
        entry = None
        if hasattr(hass, "config_entries") and hasattr(hass.config_entries, "async_get_entry"):
            entry = hass.config_entries.async_get_entry(alarm.entry_id)

        if entry:
            new_options = dict(getattr(entry, "options", {}))
            new_options.update(new_config_data)
            hass.config_entries.async_update_entry(entry, options=new_options)

        alarm.update_config(new_config_data)
        if hasattr(hass, "bus"):
            hass.bus.async_fire("smart_wake_status_changed", {"alarm_id": alarm.entry_id})

        connection.send_result(msg["id"], {"success": True, "alarm": _serialize_alarm(alarm)})

    # 10. smart_wake/create_alarm
    @websocket_api.websocket_command({
        vol.Required("type"): "smart_wake/create_alarm",
        vol.Required("name"): str,
        vol.Optional("time", default="06:30"): str,
        vol.Optional("days", default=["mon", "tue", "wed", "thu", "fri"]): list,
        vol.Optional("enabled", default=True): bool,
        vol.Optional("config", default={}): dict,
    })
    @websocket_api.async_response
    async def ws_create_alarm(
        hass: HomeAssistant, connection: websocket_api.ActiveConnection, msg: dict[str, Any]
    ) -> None:
        """Handle creating a new alarm instance directly from side-panel."""
        name = msg["name"].strip()
        if not name:
            connection.send_error(msg["id"], "invalid_name", "Alarm name cannot be empty")
            return

        domain_data: dict[str, SmartWakeAlarm] = hass.data.get(DOMAIN, {})
        for existing in domain_data.values():
            if existing.name.lower() == name.lower():
                connection.send_error(msg["id"], "already_exists", f"Alarm with name '{name}' already exists")
                return

        initial_data = {
            CONF_NAME: name,
            CONF_TIME: msg.get("time", "06:30"),
            CONF_DAYS: msg.get("days", ["mon", "tue", "wed", "thu", "fri"]),
            CONF_ENABLED: msg.get("enabled", True),
        }
        if msg.get("config"):
            initial_data.update(msg["config"])

        if hasattr(hass, "config_entries") and hasattr(hass.config_entries, "flow"):
            await hass.config_entries.flow.async_init(
                DOMAIN,
                context={"source": "user"},
                data=initial_data,
            )

        # Retrieve the newly created alarm coordinator
        created_alarm = None
        for a in hass.data.get(DOMAIN, {}).values():
            if a.name.lower() == name.lower():
                created_alarm = a
                break

        if hasattr(hass, "bus"):
            hass.bus.async_fire("smart_wake_status_changed", {})

        connection.send_result(
            msg["id"],
            {
                "success": True,
                "alarm": _serialize_alarm(created_alarm) if created_alarm else None,
            },
        )

    # 11. smart_wake/delete_alarm
    @websocket_api.websocket_command({
        vol.Required("type"): "smart_wake/delete_alarm",
        vol.Required("alarm_id"): str,
    })
    @websocket_api.async_response
    async def ws_delete_alarm(
        hass: HomeAssistant, connection: websocket_api.ActiveConnection, msg: dict[str, Any]
    ) -> None:
        """Handle deleting an alarm instance from side-panel."""
        alarm = _get_alarm(msg["alarm_id"])
        if not alarm:
            connection.send_error(msg["id"], "alarm_not_found", "Alarm instance not found")
            return

        entry_id = alarm.entry_id
        if hasattr(hass, "config_entries") and hasattr(hass.config_entries, "async_remove"):
            await hass.config_entries.async_remove(entry_id)

        if hasattr(hass, "bus"):
            hass.bus.async_fire("smart_wake_status_changed", {})

        connection.send_result(msg["id"], {"success": True, "deleted_id": entry_id})

    if hasattr(websocket_api, "async_register_command"):
        websocket_api.async_register_command(hass, ws_get_alarms)
        websocket_api.async_register_command(hass, ws_test_alarm)
        websocket_api.async_register_command(hass, ws_stop_test)
        websocket_api.async_register_command(hass, ws_snooze)
        websocket_api.async_register_command(hass, ws_dismiss)
        websocket_api.async_register_command(hass, ws_toggle)
        websocket_api.async_register_command(hass, ws_set_time)
        websocket_api.async_register_command(hass, ws_skip_next)
        websocket_api.async_register_command(hass, ws_update_config)
        websocket_api.async_register_command(hass, ws_create_alarm)
        websocket_api.async_register_command(hass, ws_delete_alarm)
