/**
 * Smart Wake Dashboard - Custom Sidebar Panel for Home Assistant
 * Author: VitalS5
 */
class SmartWakePanel extends HTMLElement {
  constructor() {
    super();
    this.attachShadow({ mode: "open" });
    this._hass = null;
    this._alarms = [];
    this._loading = true;
    this._testInterval = null;
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
    // Update countdown timers every 10 seconds
    this._timer = setInterval(() => {
      this._render();
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

  _openNewAlarmFlow() {
    window.location.href = "/config/integrations/dashboard/add?domain=smart_wake";
  }

  _openEditOptions(alarmId) {
    window.location.href = "/config/integrations/integration/smart_wake";
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
          gap: 12px;
        }

        .big-time {
          font-size: 38px;
          font-weight: 700;
          letter-spacing: -0.5px;
          color: var(--primary-color, #4fc3f7);
        }

        .countdown-chip {
          background: rgba(255, 255, 255, 0.06);
          padding: 4px 10px;
          border-radius: 6px;
          font-size: 13px;
          color: var(--secondary-text-color, #b0bec5);
        }

        .badge {
          display: inline-block;
          padding: 4px 8px;
          border-radius: 6px;
          font-size: 11px;
          font-weight: 700;
          color: #fff;
          text-transform: uppercase;
        }

        .pulse {
          animation: pulse-anim 1.5s infinite;
        }

        @keyframes pulse-anim {
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
          color: var(--primary-text-color, #fff);
          border: 1px solid rgba(255, 255, 255, 0.12);
          border-radius: 6px;
          padding: 7px 12px;
          font-size: 12px;
          font-weight: 600;
          cursor: pointer;
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
    `;

    // Attach listeners
    const btnToggleMenu = this.shadowRoot.getElementById("btnToggleMenu");
    if (btnToggleMenu) btnToggleMenu.onclick = () => this._toggleSidebar();

    const btnAdd = this.shadowRoot.getElementById("btnAdd");
    if (btnAdd) btnAdd.onclick = () => this._openNewAlarmFlow();

    // Attach alarm specific actions
    this._alarms.forEach((alarm) => {
      const toggle = this.shadowRoot.getElementById(`toggle-${alarm.id}`);
      if (toggle) {
        toggle.onchange = (e) => this._toggleAlarm(alarm.id, e.target.checked);
      }

      const btnEdit = this.shadowRoot.getElementById(`edit-${alarm.id}`);
      if (btnEdit) {
        btnEdit.onclick = () => this._openEditOptions(alarm.id);
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
            <div class="timeline-desc">Phase 1: Pre-Alarm (Sanftes Licht Fade-in, Rollos 20%)</div>
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
              ⚙️ Bearbeiten
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
}

customElements.define("smart-wake-panel", SmartWakePanel);
