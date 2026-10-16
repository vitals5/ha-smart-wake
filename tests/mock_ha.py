"""Mock setup for Home Assistant testing without full HA installation."""
from __future__ import annotations

from datetime import datetime, timezone
import sys
from unittest.mock import AsyncMock, MagicMock

# Mock voluptuous
vol_mock = MagicMock()
vol_mock.Schema = lambda s: s
vol_mock.Required = lambda k, **kw: k
vol_mock.Optional = lambda k, **kw: k
vol_mock.Coerce = lambda t: t
vol_mock.All = lambda *a: a[0]
vol_mock.Range = lambda **kw: lambda x: x
vol_mock.In = lambda l: lambda x: x
sys.modules["voluptuous"] = vol_mock
sys.modules.setdefault("voluptuous", vol_mock)

# Base mock objects
ha_mock = MagicMock()
ha_mock.__path__ = []
core_mock = MagicMock()

def dummy_callback(func):
    return func

ha_mock.callback = dummy_callback
core_mock.callback = dummy_callback

class MockHomeAssistant:
    def __init__(self):
        self.data = {}
        self.services = MagicMock()
        self.services.async_call = AsyncMock()
        self.services.async_register = MagicMock()
        self.services.async_remove = MagicMock()
        self.services.has_service = MagicMock(return_value=True)
        self._states_map = {}
        self.states = MagicMock()
        def _get_state(entity_id):
            if entity_id in self._states_map:
                return self._states_map[entity_id]
            mock_s = MagicMock()
            mock_s.entity_id = entity_id
            mock_s.state = "unknown"
            mock_s.attributes = {}
            return mock_s
        self.states.get = MagicMock(side_effect=_get_state)
        def _set_state(entity_id, state, attributes=None):
            st = MagicMock()
            st.entity_id = entity_id
            st.state = str(state)
            st.attributes = attributes or {}
            self._states_map[entity_id] = st
            return st
        self.states.set = _set_state
        self.bus = MagicMock()
        self.bus.async_fire = MagicMock()
        self.bus.async_listen = MagicMock(return_value=lambda: None)
        self.bus.async_listen_once = MagicMock(return_value=lambda: None)
        self.http = MagicMock()
        self.http.async_register_static_paths = AsyncMock()
        self.http.register_static_path = MagicMock()
        self.config_entries = MagicMock()
        self.config_entries.async_forward_entry_setups = AsyncMock()
        self.config_entries.async_unload_platforms = AsyncMock(return_value=True)
        self.config_entries.async_get_entry = MagicMock(return_value=None)
        self.config_entries.async_update_entry = MagicMock()
        self.config_entries.async_remove = AsyncMock(return_value={"require_restart": False})
        self.config_entries.flow = MagicMock()
        self.config_entries.flow.async_init = AsyncMock(return_value={"type": "create_entry"})
        self.loop = MagicMock()
        self.is_running = True

    def async_create_task(self, coro):
        import asyncio
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                return loop.create_task(coro)
        except RuntimeError:
            pass
        return AsyncMock()

core_mock.HomeAssistant = MockHomeAssistant
ha_mock.core = core_mock

ha_const_mock = MagicMock()
ha_const_mock.EVENT_HOMEASSISTANT_STARTED = "homeassistant_started"
ha_const_mock.STATE_ON = "on"
ha_const_mock.STATE_OFF = "off"
ha_const_mock.STATE_HOME = "home"
ha_const_mock.STATE_NOT_HOME = "not_home"
ha_const_mock.STATE_UNKNOWN = "unknown"
ha_const_mock.STATE_UNAVAILABLE = "unavailable"
ha_mock.const = ha_const_mock

# Entity base mocks
class MockEntity:
    def __init__(self):
        self.hass = None
        self._on_remove_callbacks = []

    def async_write_ha_state(self):
        pass

    def async_on_remove(self, cb):
        self._on_remove_callbacks.append(cb)

class MockTimeEntity(MockEntity):
    _attr_has_entity_name = True

class MockSwitchEntity(MockEntity):
    _attr_has_entity_name = True

class MockSensorEntity(MockEntity):
    _attr_has_entity_name = True

class MockButtonEntity(MockEntity):
    _attr_has_entity_name = True

class MockNumberEntity(MockEntity):
    _attr_has_entity_name = True

time_mock = MagicMock()
time_mock.TimeEntity = MockTimeEntity

switch_mock = MagicMock()
switch_mock.SwitchEntity = MockSwitchEntity

sensor_mock = MagicMock()
sensor_mock.SensorEntity = MockSensorEntity
sensor_mock.SensorDeviceClass = MagicMock()
sensor_mock.SensorDeviceClass.TIMESTAMP = "timestamp"

button_mock = MagicMock()
button_mock.ButtonEntity = MockButtonEntity

number_mock = MagicMock()
number_mock.NumberEntity = MockNumberEntity
number_mock.NumberMode = MagicMock()

panel_custom_mock = MagicMock()
panel_custom_mock.async_register_panel = AsyncMock()

websocket_api_mock = MagicMock()
def dummy_ws_cmd(schema):
    def decorator(fn):
        return fn
    return decorator
websocket_api_mock.websocket_command = dummy_ws_cmd
websocket_api_mock.async_response = lambda f: f
websocket_api_mock.async_register_command = MagicMock()

intent_mock = MagicMock()
class MockIntentHandler:
    intent_type = ""
    def async_validate_slots(self, slots):
        return slots or {}
intent_mock.IntentHandler = MockIntentHandler
intent_mock.async_register = MagicMock()

class MockIntentResponse:
    def __init__(self, *args, **kwargs):
        self.speech = ""
    def async_set_speech(self, text):
        self.speech = text

class MockIntentObj:
    def __init__(self, hass, slots=None, language="de"):
        self.hass = hass
        self.slots = slots or {}
        self.language = language
    def create_response(self):
        return MockIntentResponse()

intent_mock.IntentResponse = MockIntentResponse
intent_mock.MockIntentObj = MockIntentObj

helpers_mock = MagicMock()
helpers_mock.intent = intent_mock

# Utilities
dt_util_mock = MagicMock()
dt_util_mock.now = lambda: datetime.now().astimezone()
dt_util_mock.utcnow = lambda: datetime.now(timezone.utc)
dt_util_mock.as_utc = lambda d: d
dt_util_mock.as_local = lambda d: d
dt_util_mock.DEFAULT_TIME_ZONE = timezone.utc

def _mock_parse_datetime(dt_str):
    if not isinstance(dt_str, str):
        return None
    try:
        clean_str = dt_str.replace("Z", "+00:00")
        return datetime.fromisoformat(clean_str)
    except Exception:
        return None

dt_util_mock.parse_datetime = _mock_parse_datetime
dt_util_mock.utc_from_timestamp = lambda ts: datetime.fromtimestamp(ts, tz=timezone.utc)

dispatcher_mock = MagicMock()
dispatcher_mock.async_dispatcher_send = MagicMock()
dispatcher_mock.async_dispatcher_connect = MagicMock(return_value=lambda: None)

event_mock = MagicMock()
event_mock.async_call_later = MagicMock(return_value=lambda: None)
event_mock.async_track_point_in_utc_time = MagicMock(return_value=lambda: None)
event_mock.async_track_state_change_event = MagicMock(return_value=lambda: None)
event_mock.async_track_time_interval = MagicMock(return_value=lambda: None)

config_entries_mock = MagicMock()
class MockConfigFlow:
    VERSION = 1

    def __init_subclass__(cls, domain=None, **kwargs):
        super().__init_subclass__()
        cls.domain = domain

    def _async_current_entries(self):
        return []
    def async_create_entry(self, title, data):
        return {"type": "create_entry", "title": title, "data": data}
    def async_show_form(self, step_id, data_schema, errors=None):
        return {"type": "form", "step_id": step_id, "data_schema": data_schema, "errors": errors or {}}
    def async_show_menu(self, step_id, menu_options):
        return {"type": "menu", "step_id": step_id, "menu_options": menu_options}

class MockOptionsFlow:
    def __init__(self, entry=None):
        self._config_entry = entry

    @property
    def config_entry(self):
        return getattr(self, "_config_entry", None)
    def async_create_entry(self, title, data):
        return {"type": "create_entry", "title": title, "data": data}
    def async_show_form(self, step_id, data_schema, errors=None):
        return {"type": "form", "step_id": step_id, "data_schema": data_schema, "errors": errors or {}}
    def async_show_menu(self, step_id, menu_options):
        return {"type": "menu", "step_id": step_id, "menu_options": menu_options}

config_entries_mock.ConfigFlow = MockConfigFlow
config_entries_mock.OptionsFlow = MockOptionsFlow
config_entries_mock.ConfigEntry = MagicMock

# Create parent containers
components_mock = MagicMock()
components_mock.__path__ = []
components_mock.time = time_mock
components_mock.switch = switch_mock
components_mock.sensor = sensor_mock
components_mock.button = button_mock
components_mock.number = number_mock
components_mock.panel_custom = panel_custom_mock
components_mock.websocket_api = websocket_api_mock

util_mock = MagicMock()
util_mock.__path__ = []
util_mock.dt = dt_util_mock

entity_mock = MagicMock()
entity_mock.DeviceInfo = dict

selector_mock = MagicMock()
cv_mock = MagicMock()

helpers_mock.__path__ = []
helpers_mock.dispatcher = dispatcher_mock
helpers_mock.event = event_mock
helpers_mock.intent = intent_mock
helpers_mock.entity = entity_mock
helpers_mock.selector = selector_mock
helpers_mock.config_validation = cv_mock

ha_mock.core = core_mock
ha_mock.const = ha_const_mock
ha_mock.config_entries = config_entries_mock
ha_mock.components = components_mock
ha_mock.helpers = helpers_mock
ha_mock.util = util_mock

# Register modules in sys.modules
sys.modules["homeassistant"] = ha_mock
sys.modules["homeassistant.core"] = core_mock
sys.modules["homeassistant.const"] = ha_const_mock
sys.modules["homeassistant.config_entries"] = config_entries_mock
sys.modules["homeassistant.components"] = components_mock
sys.modules["homeassistant.components.time"] = time_mock
sys.modules["homeassistant.components.switch"] = switch_mock
sys.modules["homeassistant.components.sensor"] = sensor_mock
sys.modules["homeassistant.components.button"] = button_mock
sys.modules["homeassistant.components.number"] = number_mock
sys.modules["homeassistant.components.panel_custom"] = panel_custom_mock
sys.modules["homeassistant.components.websocket_api"] = websocket_api_mock
sys.modules["homeassistant.helpers"] = helpers_mock
sys.modules["homeassistant.helpers.dispatcher"] = dispatcher_mock
sys.modules["homeassistant.helpers.event"] = event_mock
sys.modules["homeassistant.helpers.intent"] = intent_mock
sys.modules["homeassistant.helpers.entity"] = entity_mock
sys.modules["homeassistant.helpers.selector"] = selector_mock
sys.modules["homeassistant.helpers.config_validation"] = cv_mock
sys.modules["homeassistant.util"] = util_mock
sys.modules["homeassistant.util.dt"] = dt_util_mock
