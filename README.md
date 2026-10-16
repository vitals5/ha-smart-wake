<p align="center">
  <img src="images/logo.png" alt="Smart Wake Logo" width="220">
</p>

<h1 align="center">Smart Wake</h1>
<p align="center"><b>Smart Alarm Clock for Home Assistant with Dynamic Conditions, Multi-Phase Wakeup, Anti-Cheat Dismissal & Custom Side Panel Dashboard</b></p>

<p align="center">
  <a href="https://my.home-assistant.io/redirect/hacs_repository/?owner=vitals5&repository=ha-smart-wake&category=integration"><img src="https://my.home-assistant.io/badges/hacs_repository.svg" alt="Open your Home Assistant instance and open a repository inside the Home Assistant Community Store."></a>
</p>

<p align="center">
  <a href="https://hacs.xyz"><img src="https://img.shields.io/badge/HACS-Custom-orange.svg" alt="HACS Custom"></a>
  <a href="https://www.home-assistant.io/"><img src="https://img.shields.io/badge/Home%20Assistant-2024.1.0%2B-blue.svg" alt="Home Assistant"></a>
  <a href="https://github.com/vitals5/ha-smart-wake/actions/workflows/validate.yml"><img src="https://github.com/vitals5/ha-smart-wake/actions/workflows/validate.yml/badge.svg" alt="Validate CI"></a>
  <a href="LICENSE"><img src="https://img.shields.io/badge/License-MIT-yellow.svg" alt="License: MIT"></a>
</p>

---

**Smart Wake** is a powerful, highly customizable custom integration for Home Assistant designed to revolutionize how you wake up. It combines native Home Assistant entities, intelligent sensor gating, dynamic weather and sleep-stage offsets, a gentle three-phase wakeup sequence (Pre-Alarm sunrise, Main Alarm with soft fade-in & delayed TTS briefing, Escalation), bulletproof Anti-Cheat proof-of-wakeup mechanisms, and an intuitive standalone Side Panel Dashboard.

---

## Table of Contents

- [Integration Architecture & Entity Model](#1-integration-architecture--entity-model)
- [Intelligent Conditions & Dynamic Triggers](#2-intelligent-conditions--dynamic-triggers)
- [3-Phase Wakeup Sequence](#3-3-phase-wakeup-sequence)
- [Dismissal, Snooze & Anti-Cheat System](#4-dismissal-snooze--anti-cheat-system)
- [Comprehensive Testing Modes](#5-comprehensive-testing-modes)
- [Custom Side Panel Dashboard](#6-custom-side-panel-dashboard)
- [Multilingual Support & Voice Assist Integration](#7-multilingual-support--voice-assist-integration)
- [Installation](#installation)
- [Services](#services)
- [License](#license)

---

## 1. Integration Architecture & Entity Model

Smart Wake is built on Home Assistant's modern `config_flow` architecture:
* **Independent Alarm Instances:** Each instance represents an individual alarm (e.g., *"Master Bedroom"*, *"Kids Room"*, or *"Gentle Sunrise"*).
* **Dedicated Config Entry per Alarm:** Easily configured and edited via the Home Assistant UI (*Settings → Devices & Services*) or directly through the Smart Wake Side Panel.
* **Entities Created per Alarm Instance:**
  | Entity | Type | Description |
  |---|---|---|
  | `time.<alarm_name>_time` | Native Time Entity | Direct alarm time adjustment via UI, Lovelace, or Voice Assist (`time.set_value`). |
  | `switch.<alarm_name>_enabled` | Switch | Enables or disables the alarm clock. |
  | `sensor.<alarm_name>_status` | Sensor | Real-time status: `idle`, `pre_alarm`, `ringing`, `snoozed`, `dismissed`, `skipped`. |
  | `sensor.<alarm_name>_next_alarm` | Timestamp Sensor | Next scheduled trigger time including dynamic weather offsets, with countdown attributes. |
  | `sensor.<alarm_name>_active_phase` | Sensor | Current active phase: `none`, `pre_alarm`, `main_alarm`, `escalation`. |
  | `sensor.<alarm_name>_snooze_count` | Sensor | Number of snooze cycles used in the active wakeup sequence. |
  | `sensor.<alarm_name>_dynamic_offset` | Sensor | Calculated early wake offset in minutes (frost or rain). |
  | `button.<alarm_name>_snooze` | Button | Triggers manual snooze. |
  | `button.<alarm_name>_dismiss` | Button | Triggers manual dismissal / stop. |
  | `button.<alarm_name>_full_test` | Button | Launches an interactive real-time test run (lights, audio fade-in, TTS, Anti-Cheat, escalation). |
  | `button.<alarm_name>_test` | Button | Runs a fast 30-second time-lapse simulation. |
  | `button.<alarm_name>_skip_next` | Button | Skips the next scheduled alarm trigger once without disabling the schedule. |
  | `number.<alarm_name>_snooze_duration` | Number (min) | Configurable snooze length (1 to 60 minutes, default: 9). |
  | `number.<alarm_name>_max_snooze_count` | Number | Maximum allowed snoozes before snooze is blocked (0 to 10, default: 3). |
  | `number.<alarm_name>_pre_alarm_duration` | Number (min) | Duration of the gentle sunrise pre-alarm phase (0 to 60 minutes, default: 15). |

---

## 2. Intelligent Conditions & Dynamic Triggers

Before triggering, each alarm evaluates a smart condition and offset pipeline:

* **Mobile Phone Alarm Trigger & Bidirectional Synchronization:**
  * Seamlessly syncs with your Android or iOS smartphone alarm via the Home Assistant Companion App (`sensor.<phone>_next_alarm`).
  * Live state-tracking listens for changes in real-time, automatically recalculating pre-alarm and main alarm schedules.
  * Robust parsing supports ISO-8601 strings and UNIX timestamps, and gracefully handles `unavailable`, `unknown`, `not available`, or `none` when no phone alarm is set.
  * **4 Configurable Alarm Source Priority Modes:**
    1. **Phone Priority (`mobile_priority`, Recommended):** Phone alarm takes priority when active; the fixed schedule automatically serves as a reliable fallback.
    2. **Earliest Alarm Wins (`earliest`):** Compares both phone alarm and fixed schedule and triggers whichever is earlier.
    3. **Phone Only (`mobile_only`):** Strictly wakes according to your phone. Remains idle (`Wartet auf Handy-Wecker`) when no phone alarm is set.
    4. **Fixed Schedule Only (`fixed_only`):** Ignores phone alarms and triggers exclusively on the configured fixed schedule.
  * **Bidirectional Dismissal & Snooze Synchronization (`mobile_dismiss_sync`, Default: Enabled):**
    * When both your smartphone and Smart Wake are ringing, dismissing the alarm on your phone automatically stops and dismisses Smart Wake in Home Assistant—no need to dismiss twice!
    * Tapping "Snooze" (Schlummern) on your smartphone automatically puts Smart Wake into Snooze as well, keeping both devices synchronized.
    * Turning off or deleting an upcoming alarm on your phone while Smart Wake is running its gentle pre-alarm phase immediately cancels the pre-alarm and turns off the sunrise lights.
    * Fully compatible with Anti-Cheat: if physical proof-of-wakeup is configured, dismissing the phone alarm diverts to Snooze until the physical condition (e.g., bathroom motion or NFC) is fulfilled.
* **Workday & Calendar Filters:**
  * Direct integration with `binary_sensor.workday_sensor` (only ring on business days).
  * HA Calendar integration (`calendar.*`): Trigger only when calendar events match, or skip on holidays/vacation days.
* **Presence & Person Tracking:**
  * Tied to `person.*` entities. If the assigned person is not home (`not_home`), the alarm automatically skips (`status: skipped`).
* **Dynamic Weather & Winter Offsets:**
  * **Frost Detection:** If outside temperature falls below a set threshold (e.g., `sensor.outdoor_temperature` < 0 °C), the alarm triggers $X$ minutes early to allow time for de-icing car windows.
  * **Rain Detection:** If rain is detected by rain sensors, wake time shifts earlier by $Y$ minutes to compensate for traffic delays.
* **Sleep Tracker Integration (Smart Wake Window):**
  * Monitors sleep stage sensors (e.g., Withings Sleep, Sleep As Android, Apple Watch, Garmin).
  * If a transition to light sleep (`light`, `awake`) occurs within a configurable window (e.g., 30 minutes before alarm time), Smart Wake triggers immediately to wake you at the ideal point in your sleep cycle.

---

## 3. 3-Phase Wakeup Sequence

Each alarm sequence progresses through up to three distinct phases:

### Phase 1: Pre-Alarm (Gentle Sunrise Wakeup)
* Starts $X$ minutes before the alarm time (default: 15 minutes).
* **Light Transition:** Dimmable lights (`light.*`) gradually brighten from warm deep red (1%) up to daylight yellow/white (up to 100%).
* **Cover / Blind Control:** Tilts or raises blinds/shutters to a gentle position (e.g., 20%).
* **Scripts:** Executes an optional Home Assistant pre-alarm script (`script.*`).

### Phase 2: Main Alarm (Wakeup Time)
* **Soft Audio Fade-In:**
  * Sets the starting volume first, waits 0.5s to prevent loud initial audio bursts, and then smoothly ramps the volume up over a configurable duration (e.g., 30s) to the target volume (e.g., 50%).
  * Plays internet radio streams, Spotify playlists, chimes, or local audio files on any `media_player.*`.
* **Intelligent Delayed TTS Morning Briefing:**
  * Configurable delay (e.g., 15s after audio starts) allowing you to gently wake up before speaking.
  * Pauses music playback and records the current music volume.
  * Dedicated **TTS Media Player** support (`main_tts_media_player`): Use a separate speaker for speech (e.g., Google Nest or Alexa) while another plays music.
  * Dedicated **TTS Volume** setting (`main_tts_volume`, e.g., 60%): Guarantees crisp, clear voice announcements regardless of background music volume.
  * Dynamic template placeholders: `{name}`, `{time}`, `{temp}`.
  * After the announcement finishes, original music player volume is explicitly restored, followed by a 0.5s pause, and playback is seamlessly resumed (`play_media` / `media_play`).
* **Scripts:** Executes an optional main alarm script (`script.*`).

### Phase 3: Escalation Mode (Anti-Oversleep Protection)
* Activated if no snooze or dismissal occurs after $Y$ minutes (default: 10 minutes):
  * **Volume Escalation:** Smooth, continuous fade-in up to escalation volume (e.g., 90–100%).
  * **Full Lighting:** Switches room lights to 100% brightness and crisp cold white (6500 K).
  * **Covers:** Opens blinds and shutters completely (100%).
  * **Scripts:** Executes an optional escalation script.

---

## 4. Dismissal, Snooze & Anti-Cheat System

### Anti-Cheat Proof-of-Wakeup Dismissal
* **Snooze-Diverted Dismissal:** When Anti-Cheat conditions are configured, any attempt to dismiss the alarm (via UI, Side Panel, button entity, Voice Assist, or hardware buttons) automatically acts as **Snooze** until the physical proof-of-wakeup is satisfied.
* **Immediate Dismissal:** If no Anti-Cheat conditions are defined, dismissal takes effect immediately.
* **Bypass-Proof Max Snooze Enforcement:** Even if the maximum snooze limit is reached, dismissal remains diverted to snooze if Anti-Cheat conditions are active—preventing you from turning off the alarm while still in bed.
* **Supported Anti-Cheat Conditions (Any can fulfill):**
  * **Motion / Presence Sensors:** Detects movement in the bathroom or kitchen (`binary_sensor.*`).
  * **NFC Tag:** Scanning a physical NFC tag located at the coffee maker or bathroom mirror (`tag_scanned`).
  * **Power Consumption Threshold:** Smart plug power draw exceeds threshold (e.g., coffee machine or electric kettle > 10 W).
  * **Input Boolean Helper:** Any custom `input_boolean.*` helper (toggled by external automations, tasks, or smart devices). Automatically resets back to `off` upon successful dismissal!

### Snooze (Schlummern)
* Configurable duration (e.g., 5, 8, 9, 10 minutes).
* **Max Snooze Limit:** Once the maximum allowed snoozes are exhausted, manual snooze is blocked.
* In full test mode, snooze can be safely tested using an accelerated 30-second window.

### Hardware Button Control with Strict Event Routing
* Connect any Zigbee, Z-Wave, or Matter button / remote (`sensor.*` or `event.*`).
* **Configurable Event Types:** Assign explicit event types for Snooze (e.g., `single` or `1_single`) and Dismiss (e.g., `hold`, `double`, or `2_single`).
* **Strict Event Isolation:** If a dismiss event is configured (e.g., `hold`), single clicks strictly trigger Snooze and can never accidentally dismiss the alarm—even on remotes sending complex attribute dictionaries.

---

## 5. Comprehensive Testing Modes

Smart Wake provides two built-in testing mechanisms to verify your setup without waiting for tomorrow morning:

1. **Full Real-Time Test Run (`button.<name>_full_test`):**
   * Executes the real-time wakeup sequence with live lights, audio fade-in, TTS greeting, and escalation timer.
   * Can be launched from Phase 1 (Pre-Alarm) or directly from Phase 2 (Main Alarm).
   * Supports live testing of Snooze, Dismiss, and Anti-Cheat sensors (hardware buttons, motion, NFC tags, power sensors, input_booleans) with an accelerated 30-second snooze countdown.
   * Prominent test banner in the Side Panel with live phase indicator and one-click "Stop Test" button.
2. **30-Second Fast Simulation / Dry-Run (`button.<name>_test`):**
   * A rapid 30-second time-lapse simulation cycling through all phases with a live progress bar to quickly verify light transitions and entity actions.

---

## 6. Custom Side Panel Dashboard

Smart Wake automatically registers a dedicated entry in the Home Assistant sidebar (`/smart-wake`):

* **Live Status & Countdown:** Displays active status, live countdown to the next alarm, and current dynamic offsets.
* **Full In-Panel Management:** Create, configure, clone, test, and delete alarms directly from the Side Panel—no need to navigate through Home Assistant's integration menus.
* **Live Search Autocomplete:** Entity input fields provide interactive autocomplete with domain icons, friendly names, and live state previews.
* **Direct Actions:** One-click toggling, manual snooze, dismissal, and full test controls directly in the browser with responsive mobile layouts.

---

## 7. Multilingual Support & Voice Assist Integration

Smart Wake features **full native localization and multilingual Voice Assist integration** for the 9 most widely used languages in Home Assistant:

| Language | Code | UI / Config Flow | Voice Assist Sentences | Cross-Lingual Room Matching |
|---|:---:|:---:|:---:|:---:|
| **English** | `en` |  |  |  |
| **German** (Deutsch) | `de` |  |  |  |
| **Russian** (Русский) | `ru` |  |  |  |
| **French** (Français) | `fr` |  |  |  |
| **Spanish** (Español) | `es` |  |  |  |
| **Italian** (Italiano) | `it` |  |  |  |
| **Dutch** (Nederlands) | `nl` |  |  |  |
| **Polish** (Polski) | `pl` |  |  |  |
| **Portuguese** (Português) | `pt` |  |  |  |

### Automatic Sentence Syncing
Home Assistant requires custom voice sentences to reside in `/config/custom_sentences/<lang>/`. Smart Wake **automatically synchronizes** its sentence models to your configuration folder on startup—zero manual YAML copying needed.

### Cross-Lingual Room & Intent Matching
Even if your Home Assistant instance and entity names are in one language (e.g., German *"Wecker Schlafzimmer"*), you can talk to Assist in any of the supported languages. Smart Wake automatically resolves room names across languages:
* **English:** *"Set bedroom alarm to 7:00 AM."* / *"Turn off the alarm."* / *"Snooze for 5 minutes."* / *"I am awake."*
* **German:** *"Stelle den Wecker Schlafzimmer auf 7:00 Uhr."* / *"Schalte den Wecker aus."* / *"10 Minuten weiterschlafen."* / *"Ich bin wach."*
* **Russian:** *"Поставь будильник в спальне на 7 утра."* / *"Выключи будильник."* / *"Дай поспать ещё 10 минут."* / *"Я проснулся."*
* **French:** *"Règle le réveil dans la chambre à 7h."* / *"Désactive le réveil."* / *"Encore 5 minutes de sommeil."* / *"Je suis réveillé."*
* **Spanish:** *"Pon el despertador en el dormitorio a las 7."* / *"Desactiva el despertador."* / *"Déjame dormir 5 minutos más."* / *"Ya me desperté."*
* **Italian:** *"Imposta la sveglia in camera da letto alle 7."* / *"Spegni la sveglia."* / *"Fammi dormire ancora 5 minuti."* / *"Sono sveglio."*
* **Dutch:** *"Zet de wekker in de slaapkamer op 7 uur."* / *"Zet de wekker uit."* / *"Nog 5 minuten slapen."* / *"Ik ben wakker."*
* **Polish:** *"Ustaw budzik w sypialni na siódmą."* / *"Wyłącz budzik."* / *"Daj mi pospać jeszcze 5 minut."* / *"Wstałem."*
* **Portuguese:** *"Define o despertador no quarto para as 7."* / *"Desliga o despertador."* / *"Deixa-me dormir mais 5 minutos."* / *"Já acordei."*


---

## Installation

### Option 1: HACS 1-Click Installation (Recommended)

Click the button below to open Smart Wake directly in your Home Assistant Community Store (HACS):

[![Open your Home Assistant instance and open a repository inside the Home Assistant Community Store.](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=vitals5&repository=ha-smart-wake&category=integration)

1. Click **Download** in HACS.
2. Restart Home Assistant.
3. Click the button below or navigate to **Settings → Devices & Services → Add Integration** and select **Smart Wake**:

[![Add Integration](https://my.home-assistant.io/badges/config_flow_start.svg)](https://my.home-assistant.io/redirect/config_flow_start/?domain=smart_wake)

---

### Option 2: Manual HACS Setup
1. Open **HACS** in Home Assistant.
2. Click the top-right menu `⋮` → **Custom repositories**.
3. Enter the repository URL:
   ```text
   https://github.com/vitals5/ha-smart-wake
   ```
4. Select category **Integration**.
5. Click **Add**, then **Download**.
6. Restart Home Assistant.

---

### Option 3: Manual File Installation
1. Download the latest release from GitHub.
2. Copy the folder `custom_components/smart_wake` into your Home Assistant directory `config/custom_components/smart_wake`.
3. Restart Home Assistant.
4. Add your first alarm under **Settings → Devices & Services → Add Integration → Smart Wake** or via the sidebar panel.

---

## Services

| Service | Parameters | Description |
|---|---|---|
| `smart_wake.start_full_test` | `alarm_id`, `start_from_pre_alarm`, `pre_alarm_seconds` | Starts an interactive real-time test run (lights, audio/TTS, Anti-Cheat, escalation). |
| `smart_wake.test_alarm` | `alarm_id`, `mode`, `start_from_pre_alarm` | Starts a test run (`dry_run` for 30s simulation, or `full` for real-time testing). |
| `smart_wake.stop_test` | `alarm_id` | Immediately cancels any running test run (dry-run or full test). |
| `smart_wake.snooze` | `alarm_id`, `duration` | Snoozes an active alarm for the configured or custom duration in minutes. |
| `smart_wake.dismiss` | `alarm_id` | Dismisses and ends an active alarm or pre-alarm. |
| `smart_wake.set_time` | `alarm_id`, `time` | Sets a new alarm time (e.g., `"06:45"`). |
| `smart_wake.skip_next` | `alarm_id`, `skip` | Skips the next scheduled alarm cycle once without altering the recurring schedule. |

---

## License

This project is licensed under the [MIT License](LICENSE). Copyright (c) 2026 VitalS5.
