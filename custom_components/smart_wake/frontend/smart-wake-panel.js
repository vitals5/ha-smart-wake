/**
 * Smart Wake Dashboard - Custom Sidebar Panel for Home Assistant
 * Author: VitalS5
 */
const WEEKDAYS = [
  { id: "mon", label: "Mo" },
  { id: "tue", label: "Di" },
  { id: "wed", label: "Mi" },
  { id: "thu", label: "Do" },
  { id: "fri", label: "Fr" },
  { id: "sat", label: "Sa" },
  { id: "sun", label: "So" },
];

class SmartWakePanel extends HTMLElement {
  constructor() {
    super();
    this.attachShadow({ mode: "open" });
    this._hass = null;
    this._alarms = [];
    this._loading = true;
    this._testInterval = null;

    // Modal state for in-panel settings
    this._editingAlarmId = null; // null = closed, "__new__" = creating new, or alarmId
    this._editConfig = null;
    this._activeTab = "general";
    this._saving = false;
  }

  set hass(hass) {
    const oldHass = this._hass;
    this._hass = hass;
    if (!oldHass) {
      this._fetchAlarms();
      this._subscribeUpdates();
    }
  }

  connectedCallback() {
    this._render();
    if (this._hass) {
      this._fetchAlarms();
    }
    // Update countdown timers every 10 seconds (only when modal is not open)
    this._timer = setInterval(() => {
      if (!this._editingAlarmId) {
        this._render();
      }
    }, 10000);
  }

  disconnectedCallback() {
    if (this._timer) clearInterval(this._timer);
    if (this._testInterval) clearInterval(this._testInterval);
    if (this._unsubEvents) {
      this._unsubEvents();
      this._unsubEvents = null;
    }
  }

  async _fetchAlarms() {
    if (!this._hass) return;
    try {
      const res = await this._hass.callWS({ type: "smart_wake/get_alarms" });
      this._alarms = res.alarms || [];
      this._loading = false;
      this._render();
    } catch (err) {
      console.error("Failed to fetch Smart Wake alarms:", err);
      this._loading = false;
      this._render();
    }
  }

  async _subscribeUpdates() {
    if (!this._hass || this._unsubEvents) return;
    try {
      this._unsubEvents = await this._hass.connection.subscribeEvents((event) => {
        if (event.event_type && event.event_type.startsWith("smart_wake_")) {
          this._fetchAlarms();
        }
      }, "smart_wake_status_changed");
    } catch (err) {
      console.debug("Could not subscribe to smart_wake events:", err);
    }
  }

  async _toggleAlarm(alarmId, enabled) {
    if (!this._hass) return;
    try {
      await this._hass.callWS({
        type: "smart_wake/toggle",
        alarm_id: alarmId,
        enabled: enabled,
      });
      await this._fetchAlarms();
    } catch (err) {
      console.error("Toggle alarm failed:", err);
    }
  }

  async _snoozeAlarm(alarmId) {
    if (!this._hass) return;
    try {
      await this._hass.callWS({
        type: "smart_wake/snooze",
        alarm_id: alarmId,
      });
      await this._fetchAlarms();
    } catch (err) {
      alert("Schlummern nicht möglich oder Limit erreicht!");
    }
  }

  async _dismissAlarm(alarmId) {
    if (!this._hass) return;
    try {
      await this._hass.callWS({
        type: "smart_wake/dismiss",
        alarm_id: alarmId,
      });
      await this._fetchAlarms();
    } catch (err) {
      console.error("Dismiss failed:", err);
    }
  }

  async _startDryRun(alarmId) {
    if (!this._hass) return;
    try {
      await this._hass.callWS({
        type: "smart_wake/test_alarm",
        alarm_id: alarmId,
      });
      await this._fetchAlarms();

      // Poll progress during test
      if (this._testInterval) clearInterval(this._testInterval);
      this._testInterval = setInterval(async () => {
        await this._fetchAlarms();
        const a = this._alarms.find((x) => x.id === alarmId);
        if (!a || !a.is_dry_run) {
          clearInterval(this._testInterval);
        }
      }, 1000);
    } catch (err) {
      console.error("Dry run test failed:", err);
    }
  }

  async _stopDryRun(alarmId) {
    if (!this._hass) return;
    try {
      await this._hass.callWS({
        type: "smart_wake/stop_test",
        alarm_id: alarmId,
      });
      if (this._testInterval) clearInterval(this._testInterval);
      await this._fetchAlarms();
    } catch (err) {
      console.error("Stop test failed:", err);
    }
  }

  _toggleSidebar() {
    // 1. Dispatch standard Home Assistant event (bubbles across shadow DOM)
    const ev = new CustomEvent("hass-toggle-menu", {
      bubbles: true,
      composed: true,
      cancelable: false,
      detail: {},
    });
    this.dispatchEvent(ev);
    window.dispatchEvent(ev);

    // 2. Direct DOM dispatch to Home Assistant main elements if accessible
    try {
      const ha = document.querySelector("home-assistant");
      if (ha) {
        ha.dispatchEvent(new CustomEvent("hass-toggle-menu", { bubbles: true, composed: true }));
        if (ha.shadowRoot) {
          const haMain = ha.shadowRoot.querySelector("home-assistant-main");
          if (haMain) {
            haMain.dispatchEvent(new CustomEvent("hass-toggle-menu", { bubbles: true, composed: true }));
            const drawer =
              haMain.shadowRoot?.querySelector("ha-drawer") ||
              haMain.shadowRoot?.querySelector("ha-sidebar");
            if (drawer && typeof drawer.toggle === "function") {
              drawer.toggle();
            } else if (drawer && "open" in drawer) {
              drawer.open = !drawer.open;
            }
          }
        }
      }
    } catch (e) {
      console.debug("Direct DOM sidebar toggle notice:", e);
    }

    // 3. Parent window dispatch if embedded in an iframe
    try {
      if (window.parent && window.parent !== window) {
        window.parent.dispatchEvent(new CustomEvent("hass-toggle-menu", { bubbles: true, composed: true }));
        const parentHa = window.parent.document?.querySelector("home-assistant");
        if (parentHa) {
          parentHa.dispatchEvent(new CustomEvent("hass-toggle-menu", { bubbles: true, composed: true }));
        }
      }
    } catch (e) {
      // Cross-origin iframe fallback
    }
  }

  // ---------------------------------------------------------------------------
  // In-Panel Settings Modal Logic
  // ---------------------------------------------------------------------------
  _openSettingsModal(alarmId = null) {
    this._editingAlarmId = alarmId || "__new__";
    this._activeTab = "general";
    this._saving = false;

    if (alarmId) {
      const alarm = this._alarms.find((a) => a.id === alarmId);
      const rawCfg = (alarm && alarm.config) || {};
      const sumCfg = (alarm && alarm.config_summary) || {};

      this._editConfig = {
        name: alarm ? alarm.name : "Wecker",
        time: alarm ? alarm.time : "06:30",
        enabled: alarm ? Boolean(alarm.enabled) : true,
        days: alarm && alarm.days ? [...alarm.days] : ["mon", "tue", "wed", "thu", "fri"],

        // Conditions
        workday_only: Boolean(rawCfg.workday_only ?? sumCfg.workday_only ?? false),
        workday_entity: rawCfg.workday_entity ?? sumCfg.workday_entity ?? "",
        person_home_required: Boolean(rawCfg.person_home_required ?? sumCfg.person_home_required ?? false),
        person_entities: Array.isArray(rawCfg.person_entities)
          ? rawCfg.person_entities.join(", ")
          : (sumCfg.person_entities ? sumCfg.person_entities.join(", ") : ""),
        calendar_entity: rawCfg.calendar_entity ?? "",
        calendar_behavior: rawCfg.calendar_behavior ?? "none",
        weather_temp_entity: rawCfg.weather_temp_entity ?? sumCfg.weather_temp_entity ?? "",
        weather_temp_threshold: rawCfg.weather_temp_threshold ?? 0.0,
        weather_temp_offset: rawCfg.weather_temp_offset ?? 15,
        weather_rain_entity: rawCfg.weather_rain_entity ?? "",
        weather_rain_offset: rawCfg.weather_rain_offset ?? 10,
        sleep_stage_entity: rawCfg.sleep_stage_entity ?? "",
        sleep_stage_window: rawCfg.sleep_stage_window ?? 30,

        // Phase 1: Pre-Alarm
        pre_alarm_enabled: Boolean(rawCfg.pre_alarm_enabled ?? true),
        pre_alarm_duration: rawCfg.pre_alarm_duration ?? alarm?.pre_alarm_duration ?? 15,
        pre_alarm_light_entities: Array.isArray(rawCfg.pre_alarm_light_entities)
          ? rawCfg.pre_alarm_light_entities.join(", ")
          : (sumCfg.pre_alarm_lights ? sumCfg.pre_alarm_lights.join(", ") : ""),
        pre_alarm_light_start_brightness: rawCfg.pre_alarm_light_start_brightness ?? 1,
        pre_alarm_light_end_brightness: rawCfg.pre_alarm_light_end_brightness ?? 80,
        pre_alarm_climate_entities: Array.isArray(rawCfg.pre_alarm_climate_entities)
          ? rawCfg.pre_alarm_climate_entities.join(", ")
          : (sumCfg.pre_alarm_climates ? sumCfg.pre_alarm_climates.join(", ") : ""),
        pre_alarm_climate_temp_delta: rawCfg.pre_alarm_climate_temp_delta ?? 2.0,
        pre_alarm_cover_entities: Array.isArray(rawCfg.pre_alarm_cover_entities)
          ? rawCfg.pre_alarm_cover_entities.join(", ")
          : (sumCfg.pre_alarm_covers ? sumCfg.pre_alarm_covers.join(", ") : ""),
        pre_alarm_cover_position: rawCfg.pre_alarm_cover_position ?? 20,
        pre_alarm_script_entity: rawCfg.pre_alarm_script_entity ?? "",

        // Phase 2: Main Alarm
        main_media_player_entities: Array.isArray(rawCfg.main_media_player_entities)
          ? rawCfg.main_media_player_entities.join(", ")
          : (sumCfg.main_media_players ? sumCfg.main_media_players.join(", ") : ""),
        main_audio_content_id: rawCfg.main_audio_content_id ?? sumCfg.main_audio_content ?? "",
        main_audio_content_type: rawCfg.main_audio_content_type ?? "music",
        main_audio_fade_in: Boolean(rawCfg.main_audio_fade_in ?? true),
        main_audio_fade_duration: rawCfg.main_audio_fade_duration ?? 30,
        main_audio_target_volume: Math.round((rawCfg.main_audio_target_volume ?? 0.5) * 100),
        main_tts_enabled: Boolean(rawCfg.main_tts_enabled ?? sumCfg.main_tts_enabled ?? false),
        main_tts_message: rawCfg.main_tts_message ?? "Guten Morgen! Es ist {time} Uhr, draußen sind es {temp}°C.",
        main_tts_engine: rawCfg.main_tts_engine ?? "",
        main_script_entity: rawCfg.main_script_entity ?? "",

        // Phase 3: Escalation
        escalation_enabled: Boolean(rawCfg.escalation_enabled ?? true),
        escalation_delay: rawCfg.escalation_delay ?? sumCfg.escalation_delay ?? 10,
        escalation_volume: Math.round((rawCfg.escalation_volume ?? sumCfg.escalation_volume ?? 0.9) * 100),
        escalation_light_entities: Array.isArray(rawCfg.escalation_light_entities)
          ? rawCfg.escalation_light_entities.join(", ")
          : "",
        escalation_light_brightness: rawCfg.escalation_light_brightness ?? 100,
        escalation_light_cold_white: Boolean(rawCfg.escalation_light_cold_white ?? true),
        escalation_cover_entities: Array.isArray(rawCfg.escalation_cover_entities)
          ? rawCfg.escalation_cover_entities.join(", ")
          : "",
        escalation_cover_position: rawCfg.escalation_cover_position ?? 100,
        escalation_script_entity: rawCfg.escalation_script_entity ?? "",

        // Snooze & Anti-Cheat
        snooze_duration: rawCfg.snooze_duration ?? alarm?.snooze_duration ?? 8,
        max_snooze_count: rawCfg.max_snooze_count ?? alarm?.max_snooze_count ?? 2,
        snooze_button_entity: rawCfg.snooze_button_entity ?? "",
        dismiss_button_entity: rawCfg.dismiss_button_entity ?? sumCfg.dismiss_button ?? "",
        dismiss_motion_entities: Array.isArray(rawCfg.dismiss_motion_entities)
          ? rawCfg.dismiss_motion_entities.join(", ")
          : (sumCfg.dismiss_motion ? sumCfg.dismiss_motion.join(", ") : ""),
        dismiss_nfc_tags: Array.isArray(rawCfg.dismiss_nfc_tags)
          ? rawCfg.dismiss_nfc_tags.join(", ")
          : (sumCfg.dismiss_nfc ? sumCfg.dismiss_nfc.join(", ") : ""),
        dismiss_power_sensor: rawCfg.dismiss_power_sensor ?? sumCfg.dismiss_power ?? "",
        dismiss_power_threshold: rawCfg.dismiss_power_threshold ?? 10.0,
      };
    } else {
      this._editConfig = {
        name: "Neuer Wecker",
        time: "06:30",
        enabled: true,
        days: ["mon", "tue", "wed", "thu", "fri"],

        workday_only: false,
        workday_entity: "binary_sensor.workday_sensor",
        person_home_required: false,
        person_entities: "",
        calendar_entity: "",
        calendar_behavior: "none",
        weather_temp_entity: "",
        weather_temp_threshold: 0.0,
        weather_temp_offset: 15,
        weather_rain_entity: "",
        weather_rain_offset: 10,
        sleep_stage_entity: "",
        sleep_stage_window: 30,

        pre_alarm_enabled: true,
        pre_alarm_duration: 15,
        pre_alarm_light_entities: "",
        pre_alarm_light_start_brightness: 1,
        pre_alarm_light_end_brightness: 80,
        pre_alarm_climate_entities: "",
        pre_alarm_climate_temp_delta: 2.0,
        pre_alarm_cover_entities: "",
        pre_alarm_cover_position: 20,
        pre_alarm_script_entity: "",

        main_media_player_entities: "",
        main_audio_content_id: "",
        main_audio_content_type: "music",
        main_audio_fade_in: true,
        main_audio_fade_duration: 30,
        main_audio_target_volume: 50,
        main_tts_enabled: false,
        main_tts_message: "Guten Morgen! Es ist {time} Uhr, draußen sind es {temp}°C.",
        main_tts_engine: "",
        main_script_entity: "",

        escalation_enabled: true,
        escalation_delay: 10,
        escalation_volume: 90,
        escalation_light_entities: "",
        escalation_light_brightness: 100,
        escalation_light_cold_white: true,
        escalation_cover_entities: "",
        escalation_cover_position: 100,
        escalation_script_entity: "",

        snooze_duration: 8,
        max_snooze_count: 2,
        snooze_button_entity: "",
        dismiss_button_entity: "",
        dismiss_motion_entities: "",
        dismiss_nfc_tags: "",
        dismiss_power_sensor: "",
        dismiss_power_threshold: 10.0,
      };
    }
    this._render();
  }

  _closeSettingsModal() {
    this._editingAlarmId = null;
    this._editConfig = null;
    this._saving = false;
    this._render();
  }

  _collectFormValues() {
    if (!this._editConfig || !this.shadowRoot) return;
    const root = this.shadowRoot;

    const getVal = (id) => {
      const el = root.getElementById(id);
      return el !== null ? el.value : undefined;
    };
    const getChecked = (id) => {
      const el = root.getElementById(id);
      return el !== null ? el.checked : undefined;
    };

    // General Tab
    if (getVal("f_name") !== undefined) this._editConfig.name = getVal("f_name");
    if (getVal("f_time") !== undefined) this._editConfig.time = getVal("f_time");
    if (getChecked("f_enabled") !== undefined) this._editConfig.enabled = getChecked("f_enabled");

    // Conditions Tab
    if (getChecked("f_workday_only") !== undefined) this._editConfig.workday_only = getChecked("f_workday_only");
    if (getVal("f_workday_entity") !== undefined) this._editConfig.workday_entity = getVal("f_workday_entity");
    if (getChecked("f_person_home_required") !== undefined) this._editConfig.person_home_required = getChecked("f_person_home_required");
    if (getVal("f_person_entities") !== undefined) this._editConfig.person_entities = getVal("f_person_entities");
    if (getVal("f_calendar_entity") !== undefined) this._editConfig.calendar_entity = getVal("f_calendar_entity");
    if (getVal("f_calendar_behavior") !== undefined) this._editConfig.calendar_behavior = getVal("f_calendar_behavior");
    if (getVal("f_weather_temp_entity") !== undefined) this._editConfig.weather_temp_entity = getVal("f_weather_temp_entity");
    if (getVal("f_weather_temp_threshold") !== undefined) this._editConfig.weather_temp_threshold = getVal("f_weather_temp_threshold");
    if (getVal("f_weather_temp_offset") !== undefined) this._editConfig.weather_temp_offset = getVal("f_weather_temp_offset");
    if (getVal("f_weather_rain_entity") !== undefined) this._editConfig.weather_rain_entity = getVal("f_weather_rain_entity");
    if (getVal("f_weather_rain_offset") !== undefined) this._editConfig.weather_rain_offset = getVal("f_weather_rain_offset");
    if (getVal("f_sleep_stage_entity") !== undefined) this._editConfig.sleep_stage_entity = getVal("f_sleep_stage_entity");
    if (getVal("f_sleep_stage_window") !== undefined) this._editConfig.sleep_stage_window = getVal("f_sleep_stage_window");

    // Phase 1 Tab
    if (getChecked("f_pre_alarm_enabled") !== undefined) this._editConfig.pre_alarm_enabled = getChecked("f_pre_alarm_enabled");
    if (getVal("f_pre_alarm_duration") !== undefined) this._editConfig.pre_alarm_duration = getVal("f_pre_alarm_duration");
    if (getVal("f_pre_alarm_light_entities") !== undefined) this._editConfig.pre_alarm_light_entities = getVal("f_pre_alarm_light_entities");
    if (getVal("f_pre_alarm_light_start_brightness") !== undefined) this._editConfig.pre_alarm_light_start_brightness = getVal("f_pre_alarm_light_start_brightness");
    if (getVal("f_pre_alarm_light_end_brightness") !== undefined) this._editConfig.pre_alarm_light_end_brightness = getVal("f_pre_alarm_light_end_brightness");
    if (getVal("f_pre_alarm_climate_entities") !== undefined) this._editConfig.pre_alarm_climate_entities = getVal("f_pre_alarm_climate_entities");
    if (getVal("f_pre_alarm_climate_temp_delta") !== undefined) this._editConfig.pre_alarm_climate_temp_delta = getVal("f_pre_alarm_climate_temp_delta");
    if (getVal("f_pre_alarm_cover_entities") !== undefined) this._editConfig.pre_alarm_cover_entities = getVal("f_pre_alarm_cover_entities");
    if (getVal("f_pre_alarm_cover_position") !== undefined) this._editConfig.pre_alarm_cover_position = getVal("f_pre_alarm_cover_position");
    if (getVal("f_pre_alarm_script_entity") !== undefined) this._editConfig.pre_alarm_script_entity = getVal("f_pre_alarm_script_entity");

    // Phase 2 Tab
    if (getVal("f_main_media_player_entities") !== undefined) this._editConfig.main_media_player_entities = getVal("f_main_media_player_entities");
    if (getVal("f_main_audio_content_id") !== undefined) this._editConfig.main_audio_content_id = getVal("f_main_audio_content_id");
    if (getVal("f_main_audio_content_type") !== undefined) this._editConfig.main_audio_content_type = getVal("f_main_audio_content_type");
    if (getChecked("f_main_audio_fade_in") !== undefined) this._editConfig.main_audio_fade_in = getChecked("f_main_audio_fade_in");
    if (getVal("f_main_audio_fade_duration") !== undefined) this._editConfig.main_audio_fade_duration = getVal("f_main_audio_fade_duration");
    if (getVal("f_main_audio_target_volume") !== undefined) this._editConfig.main_audio_target_volume = getVal("f_main_audio_target_volume");
    if (getChecked("f_main_tts_enabled") !== undefined) this._editConfig.main_tts_enabled = getChecked("f_main_tts_enabled");
    if (getVal("f_main_tts_message") !== undefined) this._editConfig.main_tts_message = getVal("f_main_tts_message");
    if (getVal("f_main_tts_engine") !== undefined) this._editConfig.main_tts_engine = getVal("f_main_tts_engine");
    if (getVal("f_main_script_entity") !== undefined) this._editConfig.main_script_entity = getVal("f_main_script_entity");

    // Phase 3 Tab
    if (getChecked("f_escalation_enabled") !== undefined) this._editConfig.escalation_enabled = getChecked("f_escalation_enabled");
    if (getVal("f_escalation_delay") !== undefined) this._editConfig.escalation_delay = getVal("f_escalation_delay");
    if (getVal("f_escalation_volume") !== undefined) this._editConfig.escalation_volume = getVal("f_escalation_volume");
    if (getChecked("f_escalation_light_cold_white") !== undefined) this._editConfig.escalation_light_cold_white = getChecked("f_escalation_light_cold_white");
    if (getVal("f_escalation_light_entities") !== undefined) this._editConfig.escalation_light_entities = getVal("f_escalation_light_entities");
    if (getVal("f_escalation_cover_position") !== undefined) this._editConfig.escalation_cover_position = getVal("f_escalation_cover_position");
    if (getVal("f_escalation_cover_entities") !== undefined) this._editConfig.escalation_cover_entities = getVal("f_escalation_cover_entities");
    if (getVal("f_escalation_script_entity") !== undefined) this._editConfig.escalation_script_entity = getVal("f_escalation_script_entity");

    // Snooze & Anti-Cheat Tab
    if (getVal("f_snooze_duration") !== undefined) this._editConfig.snooze_duration = getVal("f_snooze_duration");
    if (getVal("f_max_snooze_count") !== undefined) this._editConfig.max_snooze_count = getVal("f_max_snooze_count");
    if (getVal("f_snooze_button_entity") !== undefined) this._editConfig.snooze_button_entity = getVal("f_snooze_button_entity");
    if (getVal("f_dismiss_button_entity") !== undefined) this._editConfig.dismiss_button_entity = getVal("f_dismiss_button_entity");
    if (getVal("f_dismiss_motion_entities") !== undefined) this._editConfig.dismiss_motion_entities = getVal("f_dismiss_motion_entities");
    if (getVal("f_dismiss_nfc_tags") !== undefined) this._editConfig.dismiss_nfc_tags = getVal("f_dismiss_nfc_tags");
    if (getVal("f_dismiss_power_sensor") !== undefined) this._editConfig.dismiss_power_sensor = getVal("f_dismiss_power_sensor");
    if (getVal("f_dismiss_power_threshold") !== undefined) this._editConfig.dismiss_power_threshold = getVal("f_dismiss_power_threshold");
  }

  async _saveSettings() {
    if (!this._hass || !this._editConfig) return;
    this._collectFormValues();
    this._saving = true;
    this._render();

    try {
      const toList = (val) => {
        if (!val) return [];
        if (Array.isArray(val)) return val;
        return val.split(",").map((s) => s.trim()).filter((s) => s.length > 0);
      };

      const payloadConfig = {
        name: this._editConfig.name,
        time: this._editConfig.time,
        enabled: Boolean(this._editConfig.enabled),
        days: this._editConfig.days,

        workday_only: Boolean(this._editConfig.workday_only),
        workday_entity: this._editConfig.workday_entity || null,
        person_home_required: Boolean(this._editConfig.person_home_required),
        person_entities: toList(this._editConfig.person_entities),
        calendar_entity: this._editConfig.calendar_entity || null,
        calendar_behavior: this._editConfig.calendar_behavior || "none",
        weather_temp_entity: this._editConfig.weather_temp_entity || null,
        weather_temp_threshold: parseFloat(this._editConfig.weather_temp_threshold) || 0.0,
        weather_temp_offset: parseInt(this._editConfig.weather_temp_offset, 10) || 15,
        weather_rain_entity: this._editConfig.weather_rain_entity || null,
        weather_rain_offset: parseInt(this._editConfig.weather_rain_offset, 10) || 10,
        sleep_stage_entity: this._editConfig.sleep_stage_entity || null,
        sleep_stage_window: parseInt(this._editConfig.sleep_stage_window, 10) || 30,

        pre_alarm_enabled: Boolean(this._editConfig.pre_alarm_enabled),
        pre_alarm_duration: parseInt(this._editConfig.pre_alarm_duration, 10) || 15,
        pre_alarm_light_entities: toList(this._editConfig.pre_alarm_light_entities),
        pre_alarm_light_start_brightness: parseInt(this._editConfig.pre_alarm_light_start_brightness, 10) || 1,
        pre_alarm_light_end_brightness: parseInt(this._editConfig.pre_alarm_light_end_brightness, 10) || 80,
        pre_alarm_climate_entities: toList(this._editConfig.pre_alarm_climate_entities),
        pre_alarm_climate_temp_delta: parseFloat(this._editConfig.pre_alarm_climate_temp_delta) || 2.0,
        pre_alarm_cover_entities: toList(this._editConfig.pre_alarm_cover_entities),
        pre_alarm_cover_position: parseInt(this._editConfig.pre_alarm_cover_position, 10) || 20,
        pre_alarm_script_entity: this._editConfig.pre_alarm_script_entity || null,

        main_media_player_entities: toList(this._editConfig.main_media_player_entities),
        main_audio_content_id: this._editConfig.main_audio_content_id || null,
        main_audio_content_type: this._editConfig.main_audio_content_type || "music",
        main_audio_fade_in: Boolean(this._editConfig.main_audio_fade_in),
        main_audio_fade_duration: parseInt(this._editConfig.main_audio_fade_duration, 10) || 30,
        main_audio_target_volume: (parseInt(this._editConfig.main_audio_target_volume, 10) || 50) / 100,
        main_tts_enabled: Boolean(this._editConfig.main_tts_enabled),
        main_tts_message: this._editConfig.main_tts_message || "",
        main_tts_engine: this._editConfig.main_tts_engine || null,
        main_script_entity: this._editConfig.main_script_entity || null,

        escalation_enabled: Boolean(this._editConfig.escalation_enabled),
        escalation_delay: parseInt(this._editConfig.escalation_delay, 10) || 10,
        escalation_volume: (parseInt(this._editConfig.escalation_volume, 10) || 90) / 100,
        escalation_light_entities: toList(this._editConfig.escalation_light_entities),
        escalation_light_brightness: parseInt(this._editConfig.escalation_light_brightness, 10) || 100,
        escalation_light_cold_white: Boolean(this._editConfig.escalation_light_cold_white),
        escalation_cover_entities: toList(this._editConfig.escalation_cover_entities),
        escalation_cover_position: parseInt(this._editConfig.escalation_cover_position, 10) || 100,
        escalation_script_entity: this._editConfig.escalation_script_entity || null,

        snooze_duration: parseInt(this._editConfig.snooze_duration, 10) || 8,
        max_snooze_count: parseInt(this._editConfig.max_snooze_count, 10) || 2,
        snooze_button_entity: this._editConfig.snooze_button_entity || null,
        dismiss_button_entity: this._editConfig.dismiss_button_entity || null,
        dismiss_motion_entities: toList(this._editConfig.dismiss_motion_entities),
        dismiss_nfc_tags: toList(this._editConfig.dismiss_nfc_tags),
        dismiss_power_sensor: this._editConfig.dismiss_power_sensor || null,
        dismiss_power_threshold: parseFloat(this._editConfig.dismiss_power_threshold) || 10.0,
      };

      if (this._editingAlarmId === "__new__") {
        await this._hass.callWS({
          type: "smart_wake/create_alarm",
          name: this._editConfig.name,
          time: this._editConfig.time,
          days: this._editConfig.days,
          enabled: this._editConfig.enabled,
          config: payloadConfig,
        });
      } else {
        await this._hass.callWS({
          type: "smart_wake/update_config",
          alarm_id: this._editingAlarmId,
          config: payloadConfig,
        });
      }

      this._closeSettingsModal();
      await this._fetchAlarms();
    } catch (err) {
      console.error("Failed to save alarm settings:", err);
      alert("Fehler beim Speichern: " + (err.message || err));
      this._saving = false;
      this._render();
    }
  }

  async _deleteAlarm(alarmId) {
    if (!this._hass) return;
    if (!confirm("Möchtest du diesen Smart Wake Wecker wirklich löschen?")) return;
    try {
      await this._hass.callWS({
        type: "smart_wake/delete_alarm",
        alarm_id: alarmId,
      });
      this._closeSettingsModal();
      await this._fetchAlarms();
    } catch (err) {
      console.error("Failed to delete alarm:", err);
      alert("Fehler beim Löschen: " + (err.message || err));
    }
  }

  _formatTime(isoStr) {
    if (!isoStr) return "--:--";
    try {
      const d = new Date(isoStr);
      return d.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });
    } catch {
      return "--:--";
    }
  }

  _getStatusBadge(status, phase) {
    let color = "#78909c";
    let text = status.toUpperCase();
    let pulse = false;

    switch (status) {
      case "ringing":
        color = "#e53935";
        text = phase === "escalation" ? "🔔 ESKALATION!" : "🔔 KLINGELT";
        pulse = true;
        break;
      case "pre_alarm":
        color = "#fb8c00";
        text = "🌅 PRE-ALARM";
        pulse = true;
        break;
      case "snoozed":
        color = "#8e24aa";
        text = "💤 SCHLUMMERT";
        break;
      case "skipped":
        color = "#546e7a";
        text = "⏭️ ÜBERSPRUNGEN";
        break;
      case "dismissed":
        color = "#43a047";
        text = "✅ QUITTIERT";
        break;
      case "idle":
        color = "#2e7d32";
        text = "AKTIV (IDLE)";
        break;
    }

    return `<span class="badge ${pulse ? "pulse" : ""}" style="background-color: ${color};">${text}</span>`;
  }

  _render() {
    if (!this.shadowRoot) return;

    this.shadowRoot.innerHTML = `
      <style>
        :host {
          display: block;
          font-family: var(--ha-font-family, -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif);
          background-color: var(--primary-background-color, #111417);
          color: var(--primary-text-color, #e1e2e5);
          min-height: 100vh;
          padding: 24px;
          box-sizing: border-box;
        }

        .header {
          display: flex;
          justify-content: space-between;
          align-items: center;
          margin-bottom: 24px;
          padding-bottom: 16px;
          border-bottom: 1px solid var(--divider-color, rgba(255, 255, 255, 0.12));
        }

        .title-group {
          display: flex;
          align-items: center;
          gap: 14px;
        }

        .logo-menu-btn {
          background: rgba(255, 255, 255, 0.04);
          border: 1px solid var(--divider-color, rgba(255, 255, 255, 0.15));
          border-radius: 12px;
          padding: 3px;
          cursor: pointer;
          display: flex;
          align-items: center;
          justify-content: center;
          position: relative;
          color: var(--primary-text-color, #e1e2e5);
          transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
          outline: none;
        }

        .logo-menu-btn:hover {
          background: rgba(255, 255, 255, 0.1);
          border-color: var(--primary-color, #03a9f4);
          transform: translateY(-1px) scale(1.04);
          box-shadow: 0 4px 14px rgba(3, 169, 244, 0.35);
        }

        .logo-menu-btn:active {
          transform: translateY(0) scale(0.96);
        }

        .logo-wrapper {
          position: relative;
          width: 44px;
          height: 44px;
          display: flex;
          align-items: center;
          justify-content: center;
        }

        .logo-img {
          width: 44px;
          height: 44px;
          border-radius: 9px;
          object-fit: cover;
          display: block;
        }

        .logo-fallback {
          font-size: 32px;
          line-height: 1;
        }

        .menu-icon-badge {
          position: absolute;
          bottom: -4px;
          right: -4px;
          background: var(--primary-color, #03a9f4);
          color: #ffffff;
          border-radius: 50%;
          width: 18px;
          height: 18px;
          display: flex;
          align-items: center;
          justify-content: center;
          box-shadow: 0 2px 5px rgba(0, 0, 0, 0.5);
          border: 1.5px solid var(--primary-background-color, #111417);
          transition: transform 0.2s;
        }

        .logo-menu-btn:hover .menu-icon-badge {
          transform: scale(1.1);
        }

        h1 {
          font-size: 24px;
          margin: 0;
          font-weight: 600;
          letter-spacing: 0.5px;
        }

        .subtitle {
          font-size: 13px;
          color: var(--secondary-text-color, #9e9e9e);
          margin-top: 4px;
        }

        .btn-add {
          background-color: var(--primary-color, #03a9f4);
          color: var(--text-primary-color, #fff);
          border: none;
          padding: 10px 18px;
          border-radius: 8px;
          font-weight: 600;
          cursor: pointer;
          font-size: 14px;
          display: flex;
          align-items: center;
          gap: 8px;
          transition: background-color 0.2s, transform 0.1s;
        }

        .btn-add:hover {
          background-color: var(--accent-color, #0288d1);
          transform: translateY(-1px);
        }

        .alarms-grid {
          display: grid;
          grid-template-columns: repeat(auto-fill, minmax(460px, 1fr));
          gap: 20px;
        }

        @media (max-width: 600px) {
          .header {
            flex-direction: column;
            align-items: flex-start;
            gap: 16px;
          }
          .title-group {
            width: 100%;
          }
          .btn-add {
            width: 100%;
            justify-content: center;
          }
          .alarms-grid {
            grid-template-columns: 1fr;
          }
        }

        .alarm-card {
          background: var(--card-background-color, #1c2229);
          border-radius: 12px;
          border: 1px solid var(--divider-color, rgba(255, 255, 255, 0.08));
          box-shadow: 0 4px 12px rgba(0, 0, 0, 0.2);
          padding: 20px;
          display: flex;
          flex-direction: column;
          gap: 16px;
          position: relative;
          overflow: hidden;
        }

        .card-header {
          display: flex;
          justify-content: space-between;
          align-items: flex-start;
        }

        .alarm-title {
          font-size: 18px;
          font-weight: 600;
          display: flex;
          align-items: center;
          gap: 8px;
          margin: 0;
        }

        .switch-toggle {
          position: relative;
          display: inline-block;
          width: 44px;
          height: 24px;
        }

        .switch-toggle input {
          opacity: 0;
          width: 0;
          height: 0;
        }

        .slider {
          position: absolute;
          cursor: pointer;
          top: 0; left: 0; right: 0; bottom: 0;
          background-color: #555;
          transition: .3s;
          border-radius: 24px;
        }

        .slider:before {
          position: absolute;
          content: "";
          height: 18px; width: 18px;
          left: 3px; bottom: 3px;
          background-color: white;
          transition: .3s;
          border-radius: 50%;
        }

        input:checked + .slider {
          background-color: var(--primary-color, #03a9f4);
        }

        input:checked + .slider:before {
          transform: translateX(20px);
        }

        .time-row {
          display: flex;
          align-items: baseline;
          justify-content: space-between;
          border-bottom: 1px solid rgba(255, 255, 255, 0.06);
          padding-bottom: 12px;
        }

        .big-time {
          font-size: 38px;
          font-weight: 700;
          letter-spacing: 1px;
          color: var(--primary-color, #4fc3f7);
          font-variant-numeric: tabular-nums;
        }

        .countdown-chip {
          background: rgba(255, 255, 255, 0.08);
          padding: 6px 12px;
          border-radius: 16px;
          font-size: 13px;
          font-weight: 500;
        }

        .badge {
          display: inline-block;
          padding: 3px 8px;
          border-radius: 4px;
          font-size: 11px;
          font-weight: 700;
          letter-spacing: 0.5px;
          color: #fff;
        }

        .pulse {
          animation: pulseAnim 1.5s infinite;
        }

        @keyframes pulseAnim {
          0% { opacity: 1; transform: scale(1); }
          50% { opacity: 0.8; transform: scale(1.03); }
          100% { opacity: 1; transform: scale(1); }
        }

        .meta-tags {
          display: flex;
          flex-wrap: wrap;
          gap: 8px;
          font-size: 12px;
        }

        .tag {
          background: rgba(255, 255, 255, 0.05);
          border: 1px solid rgba(255, 255, 255, 0.08);
          border-radius: 6px;
          padding: 4px 8px;
          display: flex;
          align-items: center;
          gap: 5px;
        }

        .tag.highlight {
          border-color: #ffa726;
          color: #ffb74d;
        }

        .tag.workday {
          border-color: #42a5f5;
          color: #90caf9;
        }

        .timeline {
          background: rgba(0, 0, 0, 0.25);
          border-radius: 8px;
          padding: 12px 14px;
          display: flex;
          flex-direction: column;
          gap: 8px;
        }

        .timeline-title {
          font-size: 12px;
          font-weight: 600;
          text-transform: uppercase;
          letter-spacing: 0.5px;
          color: var(--secondary-text-color, #78909c);
          margin-bottom: 2px;
        }

        .timeline-item {
          display: flex;
          align-items: center;
          gap: 10px;
          font-size: 13px;
        }

        .timeline-time {
          font-weight: 600;
          min-width: 48px;
          color: #90caf9;
        }

        .timeline-dot {
          width: 8px;
          height: 8px;
          border-radius: 50%;
          background: #555;
        }

        .timeline-dot.p1 { background: #ff9800; }
        .timeline-dot.p2 { background: #4caf50; }
        .timeline-dot.p3 { background: #f44336; }

        .timeline-desc {
          color: #cfd8dc;
        }

        .anti-cheat-box {
          font-size: 12px;
          color: #90a4ae;
          background: rgba(255, 255, 255, 0.03);
          border-radius: 6px;
          padding: 8px 10px;
          display: flex;
          flex-direction: column;
          gap: 4px;
        }

        .actions-bar {
          display: flex;
          justify-content: space-between;
          align-items: center;
          margin-top: 4px;
          padding-top: 12px;
          border-top: 1px solid rgba(255, 255, 255, 0.08);
          gap: 8px;
        }

        .btn-group {
          display: flex;
          gap: 8px;
        }

        button.btn-action {
          background: rgba(255, 255, 255, 0.08);
          border: 1px solid rgba(255, 255, 255, 0.12);
          color: var(--primary-text-color, #fff);
          padding: 8px 14px;
          border-radius: 6px;
          cursor: pointer;
          font-size: 13px;
          font-weight: 600;
          display: flex;
          align-items: center;
          gap: 6px;
          transition: background-color 0.2s;
        }

        button.btn-action:hover {
          background: rgba(255, 255, 255, 0.16);
        }

        button.btn-snooze {
          background: #8e24aa;
          color: white;
          border: none;
        }

        button.btn-snooze:hover {
          background: #ab47bc;
        }

        button.btn-dismiss {
          background: #d32f2f;
          color: white;
          border: none;
        }

        button.btn-dismiss:hover {
          background: #f44336;
        }

        .dry-run-progress {
          margin-top: 8px;
          background: #263238;
          border-radius: 6px;
          overflow: hidden;
          height: 10px;
          position: relative;
        }

        .progress-bar {
          height: 100%;
          background: linear-gradient(90deg, #ff9800 0%, #4caf50 50%, #f44336 100%);
          transition: width 0.3s;
        }

        .empty-state {
          text-align: center;
          padding: 60px 20px;
          background: var(--card-background-color, #1c2229);
          border-radius: 12px;
          border: 1px dashed rgba(255, 255, 255, 0.2);
          max-width: 500px;
          margin: 40px auto;
        }

        .empty-icon {
          font-size: 48px;
          margin-bottom: 12px;
        }

        /* -------------------------------------------------------------
           Settings Modal Styling
           ------------------------------------------------------------- */
        .modal-backdrop {
          position: fixed;
          top: 0; left: 0; right: 0; bottom: 0;
          background: rgba(0, 0, 0, 0.75);
          backdrop-filter: blur(8px);
          display: flex;
          align-items: center;
          justify-content: center;
          z-index: 9999;
          padding: 16px;
          box-sizing: border-box;
          animation: modalFadeIn 0.2s ease-out;
        }

        @keyframes modalFadeIn {
          from { opacity: 0; }
          to { opacity: 1; }
        }

        .modal-container {
          background: var(--card-background-color, #1a2028);
          border: 1px solid var(--divider-color, rgba(255, 255, 255, 0.15));
          border-radius: 16px;
          width: 100%;
          max-width: 820px;
          max-height: 90vh;
          display: flex;
          flex-direction: column;
          box-shadow: 0 24px 60px rgba(0, 0, 0, 0.6);
          overflow: hidden;
          animation: modalSlideIn 0.25s cubic-bezier(0.16, 1, 0.3, 1);
        }

        @keyframes modalSlideIn {
          from { transform: translateY(20px) scale(0.97); }
          to { transform: translateY(0) scale(1); }
        }

        .modal-header {
          display: flex;
          justify-content: space-between;
          align-items: center;
          padding: 18px 24px;
          border-bottom: 1px solid var(--divider-color, rgba(255, 255, 255, 0.1));
          background: rgba(255, 255, 255, 0.03);
        }

        .modal-title-group {
          display: flex;
          align-items: center;
          gap: 12px;
        }

        .modal-icon {
          font-size: 26px;
        }

        .modal-title {
          font-size: 19px;
          font-weight: 600;
          margin: 0;
        }

        .modal-subtitle {
          font-size: 12px;
          color: var(--secondary-text-color, #90a4ae);
          margin-top: 2px;
        }

        .btn-close {
          background: transparent;
          border: none;
          color: var(--secondary-text-color, #9e9e9e);
          font-size: 24px;
          cursor: pointer;
          padding: 4px 8px;
          border-radius: 6px;
          line-height: 1;
          transition: background 0.2s, color 0.2s;
        }

        .btn-close:hover {
          background: rgba(255, 255, 255, 0.1);
          color: #fff;
        }

        .modal-tabs {
          display: flex;
          background: rgba(0, 0, 0, 0.35);
          border-bottom: 1px solid var(--divider-color, rgba(255, 255, 255, 0.08));
          padding: 6px 16px;
          gap: 6px;
          overflow-x: auto;
          scrollbar-width: thin;
        }

        .tab-btn {
          background: transparent;
          border: none;
          border-radius: 8px;
          padding: 8px 14px;
          color: var(--secondary-text-color, #90a4ae);
          font-size: 13px;
          font-weight: 600;
          cursor: pointer;
          white-space: nowrap;
          display: flex;
          align-items: center;
          gap: 6px;
          transition: all 0.2s ease;
        }

        .tab-btn:hover {
          color: #fff;
          background: rgba(255, 255, 255, 0.06);
        }

        .tab-btn.active {
          background: var(--primary-color, #03a9f4);
          color: #fff;
          box-shadow: 0 2px 8px rgba(3, 169, 244, 0.4);
        }

        .modal-body {
          padding: 22px 24px;
          overflow-y: auto;
          flex: 1;
          display: flex;
          flex-direction: column;
          gap: 18px;
        }

        .form-section-title {
          font-size: 13px;
          font-weight: 700;
          color: #90caf9;
          text-transform: uppercase;
          letter-spacing: 0.5px;
          margin-bottom: 4px;
          border-bottom: 1px solid rgba(144, 202, 249, 0.2);
          padding-bottom: 4px;
        }

        .form-group {
          display: flex;
          flex-direction: column;
          gap: 6px;
        }

        .form-row {
          display: grid;
          grid-template-columns: 1fr 1fr;
          gap: 16px;
        }

        @media (max-width: 650px) {
          .form-row {
            grid-template-columns: 1fr;
          }
        }

        .form-label {
          font-size: 13px;
          font-weight: 600;
          color: #cfd8dc;
          display: flex;
          justify-content: space-between;
          align-items: center;
        }

        .form-hint {
          font-size: 11px;
          color: var(--secondary-text-color, #78909c);
          margin-top: 2px;
          line-height: 1.4;
        }

        .form-input, .form-select, .form-textarea {
          background: rgba(255, 255, 255, 0.05);
          border: 1px solid var(--divider-color, rgba(255, 255, 255, 0.15));
          border-radius: 8px;
          padding: 10px 12px;
          color: var(--primary-text-color, #fff);
          font-size: 14px;
          outline: none;
          box-sizing: border-box;
          font-family: inherit;
          transition: border-color 0.2s, background 0.2s;
        }

        .form-input:focus, .form-select:focus, .form-textarea:focus {
          border-color: var(--primary-color, #03a9f4);
          background: rgba(255, 255, 255, 0.08);
        }

        .form-checkbox-row {
          display: flex;
          align-items: center;
          justify-content: space-between;
          padding: 10px 14px;
          background: rgba(255, 255, 255, 0.03);
          border: 1px solid rgba(255, 255, 255, 0.08);
          border-radius: 8px;
          gap: 12px;
        }

        .form-checkbox-label {
          display: flex;
          flex-direction: column;
          gap: 2px;
          font-size: 13px;
          font-weight: 600;
          color: #cfd8dc;
        }

        .days-selector {
          display: flex;
          gap: 6px;
          flex-wrap: wrap;
        }

        .day-chip {
          padding: 8px 14px;
          border-radius: 8px;
          border: 1px solid rgba(255, 255, 255, 0.15);
          background: rgba(255, 255, 255, 0.04);
          color: var(--secondary-text-color, #90a4ae);
          cursor: pointer;
          font-weight: 600;
          font-size: 13px;
          transition: all 0.2s;
          user-select: none;
        }

        .day-chip:hover {
          background: rgba(255, 255, 255, 0.1);
          color: #fff;
        }

        .day-chip.active {
          background: var(--primary-color, #03a9f4);
          border-color: var(--primary-color, #03a9f4);
          color: #fff;
          box-shadow: 0 2px 6px rgba(3, 169, 244, 0.35);
        }

        .modal-footer {
          display: flex;
          justify-content: space-between;
          align-items: center;
          padding: 16px 24px;
          border-top: 1px solid var(--divider-color, rgba(255, 255, 255, 0.1));
          background: rgba(0, 0, 0, 0.25);
        }

        .modal-footer-right {
          display: flex;
          gap: 10px;
        }

        .btn-cancel {
          background: transparent;
          border: 1px solid rgba(255, 255, 255, 0.2);
          color: var(--primary-text-color, #fff);
          padding: 10px 18px;
          border-radius: 8px;
          font-weight: 600;
          cursor: pointer;
          transition: background 0.2s;
        }

        .btn-cancel:hover {
          background: rgba(255, 255, 255, 0.08);
        }

        .btn-save {
          background: var(--primary-color, #03a9f4);
          color: #fff;
          border: none;
          padding: 10px 22px;
          border-radius: 8px;
          font-weight: 600;
          cursor: pointer;
          display: flex;
          align-items: center;
          gap: 8px;
          transition: background 0.2s, transform 0.1s;
        }

        .btn-save:hover {
          background: #0288d1;
          transform: translateY(-1px);
        }

        .btn-delete {
          background: transparent;
          border: 1px solid rgba(244, 67, 54, 0.4);
          color: #ef5350;
          padding: 10px 16px;
          border-radius: 8px;
          font-weight: 600;
          cursor: pointer;
          transition: background 0.2s, border-color 0.2s;
        }

        .btn-delete:hover {
          background: rgba(244, 67, 54, 0.15);
          border-color: #f44336;
        }
      </style>

      <div class="header">
        <div class="title-group">
          <button
            class="logo-menu-btn"
            id="btnToggleMenu"
            title="Seitenmenü öffnen (Sidebar)"
            aria-label="Seitenmenü öffnen"
          >
            <div class="logo-wrapper">
              <img
                src="/smart_wake_frontend/icon.png"
                alt="Smart Wake Logo"
                class="logo-img"
                onerror="this.style.display='none'; this.nextElementSibling.style.display='block';"
              />
              <span class="logo-fallback" style="display: none;">⏰</span>
              <div class="menu-icon-badge" title="Seitenmenü öffnen">
                <svg viewBox="0 0 24 24" width="11" height="11" fill="currentColor">
                  <path d="M3 18h18v-2H3v2zm0-5h18v-2H3v2zm0-7v2h18V6H3z"/>
                </svg>
              </div>
            </div>
          </button>
          <div>
            <h1>SMART WAKE DASHBOARD</h1>
            <div class="subtitle">Smarter Wecker mit dynamischen Bedingungen, Phasen-Aktionen & Eskalation</div>
          </div>
        </div>
        <button class="btn-add" id="btnAdd">
          <span>+</span> Neuer Wecker
        </button>
      </div>

      ${this._renderBody()}

      ${this._editingAlarmId ? this._renderSettingsModal() : ""}
    `;

    // Attach header listeners
    const btnToggleMenu = this.shadowRoot.getElementById("btnToggleMenu");
    if (btnToggleMenu) btnToggleMenu.onclick = () => this._toggleSidebar();

    const btnAdd = this.shadowRoot.getElementById("btnAdd");
    if (btnAdd) btnAdd.onclick = () => this._openSettingsModal(null);

    const btnAddEmpty = this.shadowRoot.getElementById("btnAddEmpty");
    if (btnAddEmpty) btnAddEmpty.onclick = () => this._openSettingsModal(null);

    // Attach alarm card specific actions
    this._alarms.forEach((alarm) => {
      const toggle = this.shadowRoot.getElementById(`toggle-${alarm.id}`);
      if (toggle) {
        toggle.onchange = (e) => this._toggleAlarm(alarm.id, e.target.checked);
      }

      const btnEdit = this.shadowRoot.getElementById(`edit-${alarm.id}`);
      if (btnEdit) {
        btnEdit.onclick = () => this._openSettingsModal(alarm.id);
      }

      const btnTest = this.shadowRoot.getElementById(`test-${alarm.id}`);
      if (btnTest) {
        btnTest.onclick = () => {
          if (alarm.is_dry_run) this._stopDryRun(alarm.id);
          else this._startDryRun(alarm.id);
        };
      }

      const btnSnooze = this.shadowRoot.getElementById(`snooze-${alarm.id}`);
      if (btnSnooze) {
        btnSnooze.onclick = () => this._snoozeAlarm(alarm.id);
      }

      const btnDismiss = this.shadowRoot.getElementById(`dismiss-${alarm.id}`);
      if (btnDismiss) {
        btnDismiss.onclick = () => this._dismissAlarm(alarm.id);
      }
    });

    // Attach Modal listeners if modal is open
    if (this._editingAlarmId) {
      this._attachModalListeners();
    }
  }

  _attachModalListeners() {
    const root = this.shadowRoot;

    // Close on backdrop click
    const backdrop = root.getElementById("modalBackdrop");
    if (backdrop) {
      backdrop.onclick = (e) => {
        if (e.target === backdrop) this._closeSettingsModal();
      };
    }

    const btnClose = root.getElementById("btnCloseModal");
    if (btnClose) btnClose.onclick = () => this._closeSettingsModal();

    const btnCancel = root.getElementById("btnCancelModal");
    if (btnCancel) btnCancel.onclick = () => this._closeSettingsModal();

    const btnSave = root.getElementById("btnSaveModal");
    if (btnSave) btnSave.onclick = () => this._saveSettings();

    const btnDelete = root.getElementById("btnDeleteModal");
    if (btnDelete) {
      btnDelete.onclick = () => this._deleteAlarm(this._editingAlarmId);
    }

    // Tab buttons
    root.querySelectorAll(".tab-btn").forEach((btn) => {
      btn.onclick = () => {
        const targetTab = btn.getAttribute("data-tab");
        if (targetTab && targetTab !== this._activeTab) {
          this._collectFormValues();
          this._activeTab = targetTab;
          this._render();
        }
      };
    });

    // Day chips in general tab
    root.querySelectorAll(".day-chip").forEach((chip) => {
      chip.onclick = () => {
        const day = chip.getAttribute("data-day");
        if (day && this._editConfig) {
          const currentDays = this._editConfig.days || [];
          if (currentDays.includes(day)) {
            this._editConfig.days = currentDays.filter((d) => d !== day);
          } else {
            this._editConfig.days = [...currentDays, day];
          }
          this._collectFormValues();
          this._render();
        }
      };
    });
  }

  _renderBody() {
    if (this._loading) {
      return `<div style="text-align: center; padding: 40px;">Lade Smart Wake Wecker...</div>`;
    }

    if (this._alarms.length === 0) {
      return `
        <div class="empty-state">
          <div class="empty-icon">⏰</div>
          <h3>Keine Smart Wake Wecker eingerichtet</h3>
          <p class="subtitle" style="margin-bottom: 20px;">
            Erstelle deinen ersten smarten Wecker mit Licht-Fade, Audio-Begrüßung und Anti-Verschlaf-Schutz.
          </p>
          <button class="btn-add" style="margin: 0 auto;" id="btnAddEmpty">
            <span>+</span> Jetzt Wecker hinzufügen
          </button>
        </div>
      `;
    }

    return `
      <div class="alarms-grid">
        ${this._alarms.map((alarm) => this._renderAlarmCard(alarm)).join("")}
      </div>
    `;
  }

  _renderAlarmCard(alarm) {
    const isRinging = alarm.status === "ringing" || alarm.status === "pre_alarm";
    const dryRunPct = Math.min(100, (alarm.dry_run_progress / 30) * 100);

    const cfg = alarm.config_summary || {};
    const daysStr = (alarm.days || []).map((d) => d.toUpperCase()).join(", ");

    return `
      <div class="alarm-card">
        <div class="card-header">
          <div>
            <h2 class="alarm-title">
              <span>⏰</span> ${alarm.name}
            </h2>
            <div style="margin-top: 6px;">
              ${this._getStatusBadge(alarm.status, alarm.active_phase)}
            </div>
          </div>
          <label class="switch-toggle">
            <input type="checkbox" id="toggle-${alarm.id}" ${alarm.enabled ? "checked" : ""}>
            <span class="slider"></span>
          </label>
        </div>

        <div class="time-row">
          <div class="big-time">${alarm.time} Uhr</div>
          <div class="countdown-chip">
            ⏳ ${alarm.countdown_text}
          </div>
        </div>

        <div class="meta-tags">
          <div class="tag">📅 Tage: ${daysStr}</div>
          ${cfg.workday_only ? `<div class="tag workday">💼 Nur Werktage: AN</div>` : ""}
          ${cfg.person_home_required ? `<div class="tag">👤 Anwesenheit: Erforderlich</div>` : ""}
          ${
            alarm.dynamic_offset_minutes > 0
              ? `<div class="tag highlight">❄️ Wetter-Offset: -${alarm.dynamic_offset_minutes} Min (${alarm.offset_reasons.join(", ")})</div>`
              : ""
          }
        </div>

        <div class="timeline">
          <div class="timeline-title">Ablauf & Phasen</div>
          <div class="timeline-item">
            <div class="timeline-time">${this._formatTime(alarm.pre_alarm_time)}</div>
            <div class="timeline-dot p1"></div>
            <div class="timeline-desc">Phase 1: Pre-Alarm (${alarm.pre_alarm_duration} Min sanftes Erwachen)</div>
          </div>
          <div class="timeline-item">
            <div class="timeline-time">${alarm.time}</div>
            <div class="timeline-dot p2"></div>
            <div class="timeline-desc">Phase 2: Hauptalarm (Audio Fade-in + TTS Morgenbriefing)</div>
          </div>
          <div class="timeline-item">
            <div class="timeline-time">+${cfg.escalation_delay || 10}m</div>
            <div class="timeline-dot p3"></div>
            <div class="timeline-desc">Phase 3: Eskalation (Volles Licht 100%, Audio ${Math.round((cfg.escalation_volume || 0.9) * 100)}%)</div>
          </div>
        </div>

        <div class="anti-cheat-box">
          <div>🛡️ <b>Quittierung:</b> Taster, Bad-Bewegungsmelder oder Kaffeemaschine</div>
          <div>💤 <b>Schlummern:</b> ${alarm.snooze_duration} Min (Max: ${alarm.max_snooze_count}x | Aktuell: ${alarm.snooze_count})</div>
        </div>

        ${
          alarm.is_dry_run
            ? `
            <div>
              <div style="font-size: 12px; color: #ffb74d; display: flex; justify-content: space-between;">
                <span>⏱️ Testlauf Zeitraffer: ${alarm.dry_run_progress}s / 30s</span>
                <span>${alarm.active_phase.toUpperCase()}</span>
              </div>
              <div class="dry-run-progress">
                <div class="progress-bar" style="width: ${dryRunPct}%"></div>
              </div>
            </div>
            `
            : ""
        }

        <div class="actions-bar">
          <div class="btn-group">
            <button class="btn-action" id="edit-${alarm.id}">
              ⚙️ Einstellungen
            </button>
            <button class="btn-action" id="test-${alarm.id}" style="${alarm.is_dry_run ? "background: #f44336; color: white;" : ""}">
              ${alarm.is_dry_run ? "⏹️ Test stoppen" : "▶️ 30s Testlauf"}
            </button>
          </div>

          <div class="btn-group">
            ${
              isRinging
                ? `
                <button class="btn-action btn-snooze" id="snooze-${alarm.id}">
                  💤 Schlummern
                </button>
                <button class="btn-action btn-dismiss" id="dismiss-${alarm.id}">
                  🛑 Quittieren
                </button>
                `
                : ""
            }
          </div>
        </div>
      </div>
    `;
  }

  // ---------------------------------------------------------------------------
  // Modal Rendering
  // ---------------------------------------------------------------------------
  _renderSettingsModal() {
    const isNew = this._editingAlarmId === "__new__";
    const cfg = this._editConfig || {};

    return `
      <div class="modal-backdrop" id="modalBackdrop">
        <div class="modal-container">
          <div class="modal-header">
            <div class="modal-title-group">
              <span class="modal-icon">⚙️</span>
              <div>
                <h2 class="modal-title">${isNew ? "Neuen Wecker einrichten" : "Wecker konfigurieren: " + (cfg.name || "")}</h2>
                <div class="modal-subtitle">Bequem alle Parameter direkt im Smart Wake Side-Panel anpassen</div>
              </div>
            </div>
            <button class="btn-close" id="btnCloseModal" title="Schließen">&times;</button>
          </div>

          <div class="modal-tabs">
            <button class="tab-btn ${this._activeTab === "general" ? "active" : ""}" data-tab="general">⏰ Allgemein</button>
            <button class="tab-btn ${this._activeTab === "conditions" ? "active" : ""}" data-tab="conditions">🛡️ Bedingungen</button>
            <button class="tab-btn ${this._activeTab === "phase1" ? "active" : ""}" data-tab="phase1">🌅 Pre-Alarm</button>
            <button class="tab-btn ${this._activeTab === "phase2" ? "active" : ""}" data-tab="phase2">🔔 Hauptalarm</button>
            <button class="tab-btn ${this._activeTab === "phase3" ? "active" : ""}" data-tab="phase3">⚡ Eskalation</button>
            <button class="tab-btn ${this._activeTab === "anti_cheat" ? "active" : ""}" data-tab="anti_cheat">🛑 Quittierung</button>
          </div>

          <div class="modal-body">
            ${this._renderTabContent()}
          </div>

          <div class="modal-footer">
            <div>
              ${!isNew ? `<button class="btn-delete" id="btnDeleteModal">🗑️ Wecker löschen</button>` : ""}
            </div>
            <div class="modal-footer-right">
              <button class="btn-cancel" id="btnCancelModal">Abbrechen</button>
              <button class="btn-save" id="btnSaveModal" ${this._saving ? "disabled" : ""}>
                ${this._saving ? "💾 Speichern..." : "💾 Einstellungen speichern"}
              </button>
            </div>
          </div>
        </div>
      </div>
    `;
  }

  _renderTabContent() {
    const cfg = this._editConfig || {};

    switch (this._activeTab) {
      case "general":
        return `
          <div class="form-row">
            <div class="form-group">
              <label class="form-label" for="f_name">Wecker-Name</label>
              <input class="form-input" id="f_name" type="text" value="${cfg.name || ""}" placeholder="z. B. Wecker Schlafzimmer" required />
              <span class="form-hint">Eindeutige Bezeichnung dieses Weckers</span>
            </div>
            <div class="form-group">
              <label class="form-label" for="f_time">Weckzeit</label>
              <input class="form-input" id="f_time" type="time" value="${cfg.time || "06:30"}" required />
              <span class="form-hint">Uhrzeit des Hauptalarms (HH:MM)</span>
            </div>
          </div>

          <div class="form-checkbox-row">
            <div class="form-checkbox-label">
              <span>Wecker Aktivieren</span>
              <span class="form-hint">Legt fest, ob der Wecker aktiv scharfgeschaltet ist</span>
            </div>
            <label class="switch-toggle">
              <input type="checkbox" id="f_enabled" ${cfg.enabled ? "checked" : ""}>
              <span class="slider"></span>
            </label>
          </div>

          <div class="form-group">
            <label class="form-label">Aktive Wochentage</label>
            <div class="days-selector">
              ${WEEKDAYS.map(
                (d) => `
                <div class="day-chip ${(cfg.days || []).includes(d.id) ? "active" : ""}" data-day="${d.id}">
                  ${d.label}
                </div>
              `
              ).join("")}
            </div>
            <span class="form-hint">Klicke auf die Tage, an denen der Wecker klingeln soll</span>
          </div>
        `;

      case "conditions":
        return `
          <div class="form-section-title">Werktage & Kalender</div>
          <div class="form-checkbox-row">
            <div class="form-checkbox-label">
              <span>Nur an Werktagen klingeln (Workday Filter)</span>
              <span class="form-hint">Überspringt Wochenenden und Feiertage automatisch</span>
            </div>
            <label class="switch-toggle">
              <input type="checkbox" id="f_workday_only" ${cfg.workday_only ? "checked" : ""}>
              <span class="slider"></span>
            </label>
          </div>

          <div class="form-group">
            <label class="form-label" for="f_workday_entity">Workday Sensor Entity</label>
            <input class="form-input" id="f_workday_entity" type="text" value="${cfg.workday_entity || ""}" placeholder="binary_sensor.workday_sensor" />
            <span class="form-hint">Optional: Eigener Workday Sensor (Standard: binary_sensor.workday_sensor)</span>
          </div>

          <div class="form-row">
            <div class="form-group">
              <label class="form-label" for="f_calendar_entity">Home Assistant Kalender Entity</label>
              <input class="form-input" id="f_calendar_entity" type="text" value="${cfg.calendar_entity || ""}" placeholder="calendar.privat" />
              <span class="form-hint">Optional: Kalender für Schichtpläne, Urlaub oder Schulferien</span>
            </div>
            <div class="form-group">
              <label class="form-label" for="f_calendar_behavior">Kalender-Verhalten</label>
              <select class="form-select" id="f_calendar_behavior">
                <option value="none" ${cfg.calendar_behavior === "none" ? "selected" : ""}>Keine Kalender-Bindung</option>
                <option value="only_if_event" ${cfg.calendar_behavior === "only_if_event" ? "selected" : ""}>Nur wecken wenn Ganztagstermin vorliegt</option>
                <option value="skip_if_event" ${cfg.calendar_behavior === "skip_if_event" ? "selected" : ""}>Überspringen wenn Termin vorliegt (z. B. Urlaub)</option>
              </select>
            </div>
          </div>

          <div class="form-section-title">Anwesenheitstracking</div>
          <div class="form-checkbox-row">
            <div class="form-checkbox-label">
              <span>Personen-Anwesenheit erforderlich</span>
              <span class="form-hint">Wecker wird automatisch übersprungen (status: skipped), wenn Person nicht zu Hause ist</span>
            </div>
            <label class="switch-toggle">
              <input type="checkbox" id="f_person_home_required" ${cfg.person_home_required ? "checked" : ""}>
              <span class="slider"></span>
            </label>
          </div>

          <div class="form-group">
            <label class="form-label" for="f_person_entities">Zugewiesene Personen (Kommagetrennt)</label>
            <input class="form-input" id="f_person_entities" type="text" value="${cfg.person_entities || ""}" placeholder="person.vitali, person.anna" />
            <span class="form-hint">Mindestens eine dieser Personen muss zu Hause sein</span>
          </div>

          <div class="form-section-title">Dynamische Weckzeitverschiebung (Wetter & Schlaf)</div>
          <div class="form-row">
            <div class="form-group">
              <label class="form-label" for="f_weather_temp_entity">Außentemperatur-Sensor</label>
              <input class="form-input" id="f_weather_temp_entity" type="text" value="${cfg.weather_temp_entity || ""}" placeholder="sensor.aussentemperatur" />
            </div>
            <div class="form-group">
              <label class="form-label" for="f_weather_temp_threshold">Frost-Schwelle (°C)</label>
              <input class="form-input" id="f_weather_temp_threshold" type="number" step="0.5" value="${cfg.weather_temp_threshold ?? 0.0}" />
            </div>
          </div>

          <div class="form-row">
            <div class="form-group">
              <label class="form-label" for="f_weather_temp_offset">Frost-Frühwecker Offset (Minuten)</label>
              <input class="form-input" id="f_weather_temp_offset" type="number" value="${cfg.weather_temp_offset ?? 15}" />
              <span class="form-hint">Weckt X Minuten früher zum Scheiben kratzen</span>
            </div>
            <div class="form-group">
              <label class="form-label" for="f_weather_rain_entity">Regensensor Entity</label>
              <input class="form-input" id="f_weather_rain_entity" type="text" value="${cfg.weather_rain_entity || ""}" placeholder="binary_sensor.regen" />
            </div>
          </div>

          <div class="form-row">
            <div class="form-group">
              <label class="form-label" for="f_weather_rain_offset">Regen-Offset (Minuten)</label>
              <input class="form-input" id="f_weather_rain_offset" type="number" value="${cfg.weather_rain_offset ?? 10}" />
            </div>
            <div class="form-group">
              <label class="form-label" for="f_sleep_stage_entity">Sleep-Tracker Sensor</label>
              <input class="form-input" id="f_sleep_stage_entity" type="text" value="${cfg.sleep_stage_entity || ""}" placeholder="sensor.withings_sleep_stage" />
              <span class="form-hint">Löst in Leichtschlafphase innerhalb von ${cfg.sleep_stage_window || 30} Min vor Weckzeit aus</span>
            </div>
          </div>
        `;

      case "phase1":
        return `
          <div class="form-checkbox-row">
            <div class="form-checkbox-label">
              <span>Phase 1 (Pre-Alarm / Sanftes Wecken) aktivieren</span>
              <span class="form-hint">Startet sanft vor der Weckzeit mit Licht und Heizung</span>
            </div>
            <label class="switch-toggle">
              <input type="checkbox" id="f_pre_alarm_enabled" ${cfg.pre_alarm_enabled ? "checked" : ""}>
              <span class="slider"></span>
            </label>
          </div>

          <div class="form-group">
            <label class="form-label" for="f_pre_alarm_duration">Vorlaufzeit (Minuten vor Weckzeit)</label>
            <input class="form-input" id="f_pre_alarm_duration" type="number" min="1" max="60" value="${cfg.pre_alarm_duration ?? 15}" />
            <span class="form-hint">Z. B. 15 Minuten vor dem Hauptalarm beginnen</span>
          </div>

          <div class="form-section-title">Licht-Transition</div>
          <div class="form-group">
            <label class="form-label" for="f_pre_alarm_light_entities">Dimmbare Licht-Entities (Kommagetrennt)</label>
            <input class="form-input" id="f_pre_alarm_light_entities" type="text" value="${cfg.pre_alarm_light_entities || ""}" placeholder="light.nachttisch_links, light.nachttisch_rechts" />
          </div>

          <div class="form-row">
            <div class="form-group">
              <label class="form-label" for="f_pre_alarm_light_start_brightness">Start-Helligkeit (%)</label>
              <input class="form-input" id="f_pre_alarm_light_start_brightness" type="number" min="1" max="100" value="${cfg.pre_alarm_light_start_brightness ?? 1}" />
            </div>
            <div class="form-group">
              <label class="form-label" for="f_pre_alarm_light_end_brightness">Ziel-Helligkeit (%)</label>
              <input class="form-input" id="f_pre_alarm_light_end_brightness" type="number" min="1" max="100" value="${cfg.pre_alarm_light_end_brightness ?? 80}" />
            </div>
          </div>

          <div class="form-section-title">Heizung & Rollos</div>
          <div class="form-row">
            <div class="form-group">
              <label class="form-label" for="f_pre_alarm_climate_entities">Klima / Thermostat-Entities</label>
              <input class="form-input" id="f_pre_alarm_climate_entities" type="text" value="${cfg.pre_alarm_climate_entities || ""}" placeholder="climate.schlafzimmer" />
            </div>
            <div class="form-group">
              <label class="form-label" for="f_pre_alarm_climate_temp_delta">Temperaturanhebung (°C)</label>
              <input class="form-input" id="f_pre_alarm_climate_temp_delta" type="number" step="0.5" value="${cfg.pre_alarm_climate_temp_delta ?? 2.0}" />
            </div>
          </div>

          <div class="form-row">
            <div class="form-group">
              <label class="form-label" for="f_pre_alarm_cover_entities">Rollos / Jalousien Entities</label>
              <input class="form-input" id="f_pre_alarm_cover_entities" type="text" value="${cfg.pre_alarm_cover_entities || ""}" placeholder="cover.schlafzimmer" />
            </div>
            <div class="form-group">
              <label class="form-label" for="f_pre_alarm_cover_position">Zielposition (% geöffnet)</label>
              <input class="form-input" id="f_pre_alarm_cover_position" type="number" min="0" max="100" value="${cfg.pre_alarm_cover_position ?? 20}" />
              <span class="form-hint">Z. B. 20% für sanftes Kippen der Lamellen</span>
            </div>
          </div>

          <div class="form-group">
            <label class="form-label" for="f_pre_alarm_script_entity">Optionales Pre-Alarm Skript</label>
            <input class="form-input" id="f_pre_alarm_script_entity" type="text" value="${cfg.pre_alarm_script_entity || ""}" placeholder="script.pre_alarm_custom" />
          </div>
        `;

      case "phase2":
        return `
          <div class="form-section-title">Media Player & Audio</div>
          <div class="form-group">
            <label class="form-label" for="f_main_media_player_entities">Media Player Entities (Kommagetrennt)</label>
            <input class="form-input" id="f_main_media_player_entities" type="text" value="${cfg.main_media_player_entities || ""}" placeholder="media_player.schlafzimmer_speaker" />
            <span class="form-hint">Lautsprecher, auf denen der Wecker ertönen soll</span>
          </div>

          <div class="form-row">
            <div class="form-group">
              <label class="form-label" for="f_main_audio_content_id">Audio Content ID / Radio URL</label>
              <input class="form-input" id="f_main_audio_content_id" type="text" value="${cfg.main_audio_content_id || ""}" placeholder="http://stream.radioparadise.com/mp3-128" />
              <span class="form-hint">Web-Radio Stream URL, Spotify URI oder Chime</span>
            </div>
            <div class="form-group">
              <label class="form-label" for="f_main_audio_content_type">Audio Content Type</label>
              <input class="form-input" id="f_main_audio_content_type" type="text" value="${cfg.main_audio_content_type || "music"}" placeholder="music" />
            </div>
          </div>

          <div class="form-checkbox-row">
            <div class="form-checkbox-label">
              <span>Sanfter Audio-Fade-in</span>
              <span class="form-hint">Lautstärke schrittweise von 1% auf Ziellautstärke anheben</span>
            </div>
            <label class="switch-toggle">
              <input type="checkbox" id="f_main_audio_fade_in" ${cfg.main_audio_fade_in ? "checked" : ""}>
              <span class="slider"></span>
            </label>
          </div>

          <div class="form-row">
            <div class="form-group">
              <label class="form-label" for="f_main_audio_fade_duration">Fade-in Dauer (Sekunden)</label>
              <input class="form-input" id="f_main_audio_fade_duration" type="number" min="5" max="300" value="${cfg.main_audio_fade_duration ?? 30}" />
            </div>
            <div class="form-group">
              <label class="form-label" for="f_main_audio_target_volume">Ziellautstärke (%)</label>
              <input class="form-input" id="f_main_audio_target_volume" type="number" min="1" max="100" value="${cfg.main_audio_target_volume ?? 50}" />
            </div>
          </div>

          <div class="form-section-title">TTS Morgenbriefing</div>
          <div class="form-checkbox-row">
            <div class="form-checkbox-label">
              <span>Sprachausgabe (TTS Begrüßung) aktivieren</span>
              <span class="form-hint">Sagt z. B. die Uhrzeit und das aktuelle Wetter an</span>
            </div>
            <label class="switch-toggle">
              <input type="checkbox" id="f_main_tts_enabled" ${cfg.main_tts_enabled ? "checked" : ""}>
              <span class="slider"></span>
            </label>
          </div>

          <div class="form-group">
            <label class="form-label" for="f_main_tts_message">TTS Nachrichtentext</label>
            <textarea class="form-textarea" id="f_main_tts_message" rows="3">${cfg.main_tts_message || "Guten Morgen! Es ist {time} Uhr, draußen sind es {temp}°C."}</textarea>
            <span class="form-hint">Verfügbare Platzhalter: {name}, {time}, {temp}</span>
          </div>

          <div class="form-row">
            <div class="form-group">
              <label class="form-label" for="f_main_tts_engine">TTS Engine Entity (Optional)</label>
              <input class="form-input" id="f_main_tts_engine" type="text" value="${cfg.main_tts_engine || ""}" placeholder="tts.google_en_com oder tts.piper" />
            </div>
            <div class="form-group">
              <label class="form-label" for="f_main_script_entity">Optionales Hauptalarm Skript</label>
              <input class="form-input" id="f_main_script_entity" type="text" value="${cfg.main_script_entity || ""}" placeholder="script.guten_morgen" />
            </div>
          </div>
        `;

      case "phase3":
        return `
          <div class="form-checkbox-row">
            <div class="form-checkbox-label">
              <span>Phase 3 (Eskalations-Modus) aktivieren</span>
              <span class="form-hint">Anti-Verschlaf-Schutz: Maximale Beleuchtung & Lautstärke nach Wartezeit</span>
            </div>
            <label class="switch-toggle">
              <input type="checkbox" id="f_escalation_enabled" ${cfg.escalation_enabled ? "checked" : ""}>
              <span class="slider"></span>
            </label>
          </div>

          <div class="form-row">
            <div class="form-group">
              <label class="form-label" for="f_escalation_delay">Verzögerung bis Eskalation (Minuten)</label>
              <input class="form-input" id="f_escalation_delay" type="number" min="1" max="60" value="${cfg.escalation_delay ?? 10}" />
              <span class="form-hint">Minuten nach Hauptalarm ohne Snooze/Dismiss</span>
            </div>
            <div class="form-group">
              <label class="form-label" for="f_escalation_volume">Eskalations-Lautstärke (%)</label>
              <input class="form-input" id="f_escalation_volume" type="number" min="50" max="100" value="${cfg.escalation_volume ?? 90}" />
            </div>
          </div>

          <div class="form-section-title">Eskalations-Licht & Rollos</div>
          <div class="form-checkbox-row">
            <div class="form-checkbox-label">
              <span>100% Kaltweiß einschalten</span>
              <span class="form-hint">Schaltet den Raum schlagartig hell gegen Verschlafen</span>
            </div>
            <label class="switch-toggle">
              <input type="checkbox" id="f_escalation_light_cold_white" ${cfg.escalation_light_cold_white ? "checked" : ""}>
              <span class="slider"></span>
            </label>
          </div>

          <div class="form-group">
            <label class="form-label" for="f_escalation_light_entities">Licht-Entities für Eskalation</label>
            <input class="form-input" id="f_escalation_light_entities" type="text" value="${cfg.escalation_light_entities || ""}" placeholder="light.schlafzimmer_hauptlicht" />
          </div>

          <div class="form-row">
            <div class="form-group">
              <label class="form-label" for="f_escalation_cover_entities">Rollos für Eskalation</label>
              <input class="form-input" id="f_escalation_cover_entities" type="text" value="${cfg.escalation_cover_entities || ""}" placeholder="cover.schlafzimmer_rollo" />
            </div>
            <div class="form-group">
              <label class="form-label" for="f_escalation_cover_position">Zielposition (% geöffnet)</label>
              <input class="form-input" id="f_escalation_cover_position" type="number" min="0" max="100" value="${cfg.escalation_cover_position ?? 100}" />
            </div>
          </div>

          <div class="form-group">
            <label class="form-label" for="f_escalation_script_entity">Optionales Eskalations-Skript</label>
            <input class="form-input" id="f_escalation_script_entity" type="text" value="${cfg.escalation_script_entity || ""}" placeholder="script.alarm_escalation" />
          </div>
        `;

      case "anti_cheat":
        return `
          <div class="form-section-title">Schlummer-Einstellungen</div>
          <div class="form-row">
            <div class="form-group">
              <label class="form-label" for="f_snooze_duration">Schlummerdauer (Minuten)</label>
              <input class="form-input" id="f_snooze_duration" type="number" min="1" max="60" value="${cfg.snooze_duration ?? 8}" />
              <span class="form-hint">Dauer eines Schlummervorgangs (z. B. 8 Min)</span>
            </div>
            <div class="form-group">
              <label class="form-label" for="f_max_snooze_count">Max. Anzahl Schlummern (Snooze-Limit)</label>
              <input class="form-input" id="f_max_snooze_count" type="number" min="0" max="10" value="${cfg.max_snooze_count ?? 2}" />
              <span class="form-hint">Nach N Malen wird Snooze gesperrt – Quittier-Zwang!</span>
            </div>
          </div>

          <div class="form-section-title">Hardware-Taster (Zigbee / Z-Wave)</div>
          <div class="form-row">
            <div class="form-group">
              <label class="form-label" for="f_snooze_button_entity">Snooze-Taster Entity (1x Klick)</label>
              <input class="form-input" id="f_snooze_button_entity" type="text" value="${cfg.snooze_button_entity || ""}" placeholder="event.nachttisch_taster" />
            </div>
            <div class="form-group">
              <label class="form-label" for="f_dismiss_button_entity">Dismiss-Taster Entity (2x Klick)</label>
              <input class="form-input" id="f_dismiss_button_entity" type="text" value="${cfg.dismiss_button_entity || ""}" placeholder="event.nachttisch_taster_double" />
            </div>
          </div>

          <div class="form-section-title">Anti-Cheat Aufsteh-Beweis</div>
          <div class="form-group">
            <label class="form-label" for="f_dismiss_motion_entities">Bewegungsmelder Badezimmer / Küche</label>
            <input class="form-input" id="f_dismiss_motion_entities" type="text" value="${cfg.dismiss_motion_entities || ""}" placeholder="binary_sensor.bad_motion, binary_sensor.kueche_motion" />
            <span class="form-hint">Quittiert den Wecker automatisch bei Bewegung im Bad/Küche</span>
          </div>

          <div class="form-group">
            <label class="form-label" for="f_dismiss_nfc_tags">NFC Tag IDs (Spiegel / Kaffeemaschine)</label>
            <input class="form-input" id="f_dismiss_nfc_tags" type="text" value="${cfg.dismiss_nfc_tags || ""}" placeholder="tag_badspiegel, tag_kaffee" />
            <span class="form-hint">Wecker stoppt erst nach Scannen des physischen NFC-Tags</span>
          </div>

          <div class="form-row">
            <div class="form-group">
              <label class="form-label" for="f_dismiss_power_sensor">Leistungssensor (Kaffeemaschine / Bad)</label>
              <input class="form-input" id="f_dismiss_power_sensor" type="text" value="${cfg.dismiss_power_sensor || ""}" placeholder="sensor.kaffeemaschine_leistung" />
            </div>
            <div class="form-group">
              <label class="form-label" for="f_dismiss_power_threshold">Leistungsschwelle (Watt)</label>
              <input class="form-input" id="f_dismiss_power_threshold" type="number" step="1" value="${cfg.dismiss_power_threshold ?? 10.0}" />
              <span class="form-hint">Quittiert, wenn z. B. Kaffeemaschine eingeschaltet wird (> 10W)</span>
            </div>
          </div>
        `;

      default:
        return `<div>Ungültiger Tab</div>`;
    }
  }
}

customElements.define("smart-wake-panel", SmartWakePanel);
