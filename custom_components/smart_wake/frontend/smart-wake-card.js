/**
 * Smart Wake Lovelace Card
 * Card for Home Assistant Lovelace Dashboards
 * Author: VitalS5
 */
class SmartWakeCard extends HTMLElement {
  constructor() {
    super();
    this.attachShadow({ mode: "open" });
    this._config = {};
    this._hass = null;
  }

  setConfig(config) {
    this._config = config || {};
    this._render();
  }

  set hass(hass) {
    this._hass = hass;
    this._render();
  }

  getCardSize() {
    return 3;
  }

  _render() {
    if (!this.shadowRoot || !this._hass) return;

    // Find smart_wake entities in hass
    const alarmEntityId = this._config.entity;
    let alarmName = this._config.title || "Smart Wake";
    let status = "idle";
    let targetTime = "06:30";
    let isEnabled = true;

    if (alarmEntityId && this._hass.states[alarmEntityId]) {
      const stateObj = this._hass.states[alarmEntityId];
      status = stateObj.state;
      alarmName = stateObj.attributes.friendly_name || alarmName;
    }

    this.shadowRoot.innerHTML = `
      <style>
        ha-card {
          padding: 16px;
          border-radius: 12px;
          background: var(--ha-card-background, var(--card-background-color, #1c2229));
          color: var(--primary-text-color, #fff);
          font-family: var(--ha-font-family, sans-serif);
        }
        .header {
          display: flex;
          justify-content: space-between;
          align-items: center;
          margin-bottom: 12px;
        }
        .title {
          font-size: 16px;
          font-weight: 600;
          display: flex;
          align-items: center;
          gap: 8px;
        }
        .time-display {
          font-size: 32px;
          font-weight: 700;
          color: var(--primary-color, #4fc3f7);
          margin-bottom: 8px;
        }
        .status-badge {
          display: inline-block;
          padding: 4px 8px;
          border-radius: 6px;
          font-size: 11px;
          font-weight: 700;
          background: #2e7d32;
          color: #fff;
          text-transform: uppercase;
        }
        .btn-row {
          display: flex;
          gap: 8px;
          margin-top: 14px;
        }
        button {
          flex: 1;
          padding: 8px 12px;
          border-radius: 6px;
          border: 1px solid rgba(255,255,255,0.12);
          background: rgba(255,255,255,0.06);
          color: #fff;
          cursor: pointer;
          font-weight: 600;
        }
        button:hover {
          background: rgba(255,255,255,0.12);
        }
      </style>
      <ha-card>
        <div class="header">
          <div class="title">
            <span>⏰</span> ${alarmName}
          </div>
          <span class="status-badge">${status.toUpperCase()}</span>
        </div>
        <div class="time-display">${targetTime} Uhr</div>
        <div class="btn-row">
          <button id="btnSnooze">💤 Snooze</button>
          <button id="btnDismiss" style="background: #d32f2f; border: none;">🛑 Dismiss</button>
        </div>
      </ha-card>
    `;

    const btnSnooze = this.shadowRoot.getElementById("btnSnooze");
    if (btnSnooze) {
      btnSnooze.onclick = () => {
        this._hass.callService("smart_wake", "snooze", { alarm_id: alarmEntityId });
      };
    }

    const btnDismiss = this.shadowRoot.getElementById("btnDismiss");
    if (btnDismiss) {
      btnDismiss.onclick = () => {
        this._hass.callService("smart_wake", "dismiss", { alarm_id: alarmEntityId });
      };
    }
  }
}

customElements.define("smart-wake-card", SmartWakeCard);
window.customCards = window.customCards || [];
window.customCards.push({
  type: "smart-wake-card",
  name: "Smart Wake Card",
  description: "Dashboard card for Smart Wake alarm clocks",
});
