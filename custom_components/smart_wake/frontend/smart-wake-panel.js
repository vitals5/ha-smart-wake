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

const PANEL_STYLES = `
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
          flex-wrap: wrap;
          margin-top: 4px;
          padding-top: 12px;
          border-top: 1px solid rgba(255, 255, 255, 0.08);
          gap: 10px;
        }

        .btn-group {
          display: flex;
          flex-wrap: wrap;
          gap: 8px;
        }

        @media (max-width: 600px) {
          .actions-bar {
            flex-direction: column;
            align-items: stretch;
            gap: 10px;
          }

          .btn-group {
            width: 100%;
            display: flex;
            flex-wrap: wrap;
            gap: 8px;
          }

          button.btn-action {
            flex: 1 1 auto;
            min-height: 42px;
            justify-content: center;
            text-align: center;
          }
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

        .full-test-banner {
          background: rgba(229, 57, 53, 0.12);
          border: 1px solid rgba(229, 57, 53, 0.4);
          border-radius: 8px;
          padding: 10px 14px;
          margin-top: 10px;
          animation: modalFadeIn 0.3s ease-out;
        }

        .snooze-anti-cheat-banner {
          background: rgba(255, 152, 0, 0.12);
          border: 1px solid rgba(255, 152, 0, 0.4);
          border-left: 4px solid #ff9800;
          border-radius: 8px;
          padding: 10px 14px;
          margin-top: 10px;
          font-size: 12px;
          color: #ffe0b2;
          line-height: 1.4;
        }

        .sw-toast {
          position: fixed;
          bottom: 24px;
          right: 24px;
          background: #1e293b;
          color: #f1f5f9;
          border: 1px solid #3b82f6;
          border-left: 4px solid #3b82f6;
          box-shadow: 0 10px 25px -5px rgba(0, 0, 0, 0.5);
          border-radius: 8px;
          padding: 12px 18px;
          font-size: 13px;
          font-weight: 500;
          max-width: 440px;
          z-index: 99999;
          opacity: 0;
          transform: translateY(12px);
          transition: opacity 0.25s ease, transform 0.25s ease;
          pointer-events: none;
        }

        .sw-toast.visible {
          opacity: 1;
          transform: translateY(0);
        }

        .sw-toast.snoozing {
          border: 1px solid #fb8c00;
          border-left: 4px solid #fb8c00;
          background: rgba(30, 41, 59, 0.96);
          box-shadow: 0 10px 25px -5px rgba(251, 140, 0, 0.35);
        }

        button.btn-full-test {
          background: rgba(229, 57, 53, 0.18) !important;
          color: #ff8a80 !important;
          border-color: rgba(229, 57, 53, 0.4) !important;
        }

        button.btn-full-test:hover {
          background: rgba(229, 57, 53, 0.3) !important;
        }

        button.btn-stop-test {
          background: #d32f2f !important;
          color: white !important;
          border-color: #f44336 !important;
          font-weight: 600 !important;
        }

        button.btn-stop-test:hover {
          background: #b71c1c !important;
        }

        .test-choice-card {
          background: rgba(255, 255, 255, 0.04);
          border: 1px solid var(--divider-color, rgba(255, 255, 255, 0.12));
          border-radius: 12px;
          padding: 16px;
          display: flex;
          align-items: center;
          gap: 16px;
          cursor: pointer;
          transition: all 0.2s ease;
        }

        .test-choice-card:hover {
          background: rgba(255, 255, 255, 0.08);
          border-color: var(--primary-color, #03a9f4);
          transform: translateY(-2px);
        }

        .test-choice-icon {
          font-size: 32px;
          flex-shrink: 0;
        }

        .test-choice-content {
          flex: 1;
        }

        .test-choice-title {
          font-weight: 600;
          font-size: 15px;
          color: var(--primary-text-color, #fff);
          margin-bottom: 4px;
        }

        .test-choice-desc {
          font-size: 12px;
          color: var(--secondary-text-color, #aaa);
          line-height: 1.4;
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

        .radio-options-group {
          display: flex;
          flex-direction: column;
          gap: 8px;
          margin-top: 6px;
        }

        .radio-option {
          display: flex;
          align-items: flex-start;
          gap: 12px;
          padding: 10px 14px;
          border-radius: 8px;
          background: rgba(255, 255, 255, 0.03);
          border: 1px solid rgba(255, 255, 255, 0.08);
          cursor: pointer;
          transition: all 0.2s ease;
        }

        .radio-option:hover {
          background: rgba(255, 255, 255, 0.06);
          border-color: rgba(3, 169, 244, 0.4);
        }

        .radio-option input[type="radio"] {
          margin-top: 2px;
          accent-color: var(--primary-color, #03a9f4);
          cursor: pointer;
          width: 16px;
          height: 16px;
          flex-shrink: 0;
        }

        .radio-option:has(input:checked) {
          background: rgba(3, 169, 244, 0.08);
          border-color: var(--primary-color, #03a9f4);
        }

        .radio-label {
          display: flex;
          flex-direction: column;
          gap: 2px;
        }

        .radio-title {
          font-size: 13px;
          font-weight: 600;
          color: var(--primary-text-color, #eceff1);
        }

        .radio-desc {
          font-size: 11px;
          color: var(--secondary-text-color, #90a4ae);
          line-height: 1.35;
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

        /* -------------------------------------------------------------
           Entity Autocomplete & Live Preview Styling
           ------------------------------------------------------------- */
        .entity-input-wrapper {
          position: relative;
          width: 100%;
        }

        .entity-autocomplete-input {
          width: 100%;
        }

        .entity-preview-chips {
          display: flex;
          flex-wrap: wrap;
          gap: 6px;
          margin-top: 6px;
        }

        .entity-chip {
          display: inline-flex;
          align-items: center;
          gap: 6px;
          background: rgba(3, 169, 244, 0.14);
          border: 1px solid rgba(3, 169, 244, 0.35);
          border-radius: 6px;
          padding: 3px 8px;
          font-size: 11px;
          color: #e1f5fe;
          user-select: none;
        }

        .entity-chip.unverified {
          background: rgba(255, 152, 0, 0.14);
          border-color: rgba(255, 152, 0, 0.4);
          color: #ffe0b2;
        }

        .entity-chip-icon {
          font-size: 13px;
          line-height: 1;
        }

        .entity-chip-name {
          font-weight: 600;
          max-width: 170px;
          overflow: hidden;
          text-overflow: ellipsis;
          white-space: nowrap;
        }

        .entity-chip-state {
          font-size: 10px;
          background: rgba(0, 0, 0, 0.35);
          padding: 1px 6px;
          border-radius: 4px;
          color: #81d4fa;
          font-weight: 500;
        }

        .entity-chip.unverified .entity-chip-state {
          color: #ffcc80;
        }

        .entity-chip-remove {
          background: transparent;
          border: none;
          color: rgba(255, 255, 255, 0.6);
          font-size: 13px;
          line-height: 1;
          cursor: pointer;
          padding: 0 3px;
          border-radius: 3px;
          transition: background 0.15s, color 0.15s;
        }

        .entity-chip-remove:hover {
          color: #ff5252;
          background: rgba(255, 255, 255, 0.2);
        }

        .entity-autocomplete-dropdown {
          position: absolute;
          top: calc(100% + 4px);
          left: 0;
          right: 0;
          background: #182029;
          border: 1px solid rgba(3, 169, 244, 0.35);
          border-radius: 8px;
          box-shadow: 0 12px 32px rgba(0, 0, 0, 0.75);
          max-height: 240px;
          overflow-y: auto;
          z-index: 1000;
          scrollbar-width: thin;
        }

        .autocomplete-item {
          display: flex;
          align-items: center;
          justify-content: space-between;
          padding: 9px 12px;
          cursor: pointer;
          border-bottom: 1px solid rgba(255, 255, 255, 0.05);
          transition: background 0.15s;
          user-select: none;
        }

        .autocomplete-item:last-child {
          border-bottom: none;
        }

        .autocomplete-item:hover, .autocomplete-item.highlighted {
          background: rgba(3, 169, 244, 0.22);
        }

        .autocomplete-item-left {
          display: flex;
          align-items: center;
          gap: 10px;
          overflow: hidden;
          min-width: 0;
        }

        .autocomplete-item-icon {
          font-size: 17px;
          flex-shrink: 0;
          line-height: 1;
        }

        .autocomplete-item-info {
          display: flex;
          flex-direction: column;
          overflow: hidden;
          min-width: 0;
        }

        .autocomplete-item-name {
          font-size: 12px;
          font-weight: 600;
          color: #fff;
          white-space: nowrap;
          overflow: hidden;
          text-overflow: ellipsis;
        }

        .autocomplete-item-id {
          font-size: 10px;
          color: #90a4ae;
          font-family: monospace;
          white-space: nowrap;
          overflow: hidden;
          text-overflow: ellipsis;
        }

        .autocomplete-item-right {
          flex-shrink: 0;
          margin-left: 8px;
        }

        .autocomplete-item-state {
          font-size: 11px;
          background: rgba(255, 255, 255, 0.08);
          padding: 2px 7px;
          border-radius: 10px;
          color: #81d4fa;
          font-weight: 500;
          white-space: nowrap;
        }

        .autocomplete-no-results {
          padding: 12px;
          font-size: 12px;
          color: #78909c;
          text-align: center;
          font-style: italic;
        }
`;

class SmartWakePanel extends HTMLElement {
  constructor() {
    super();
    this.attachShadow({ mode: "open" });
    this._hass = null;
    this._alarms = [];
    this._loading = true;
    this._testInterval = null;
    this._timer = null;
    this._toastTimeout = null;

    // Modal state for in-panel settings
    this._editingAlarmId = null; // null = closed, "__new__" = creating new, or alarmId
    this._editConfig = null;
    this._activeTab = "general";
    this._saving = false;

    // Test selection modal state
    this._testModalAlarmId = null;

    // Permanent shadow DOM flags & RAF debounce
    this._shadowInitialized = false;
    this._dashboardRendered = false;
    this._chipRaf = null;
  }

  _ensureShadowStructure() {
    if (this._shadowInitialized) return;
    this._shadowInitialized = true;

    const styleEl = document.createElement("style");
    styleEl.textContent = PANEL_STYLES;

    const appEl = document.createElement("div");
    appEl.id = "panelApp";
    appEl.className = "smart-wake-app";

    const modalHostEl = document.createElement("div");
    modalHostEl.id = "modalHost";

    const toastEl = document.createElement("div");
    toastEl.id = "smartWakeToast";
    toastEl.className = "sw-toast";

    this.shadowRoot.appendChild(styleEl);
    this.shadowRoot.appendChild(appEl);
    this.shadowRoot.appendChild(modalHostEl);
    this.shadowRoot.appendChild(toastEl);
  }

  set hass(hass) {
    const oldHass = this._hass;
    this._hass = hass;
    if (!oldHass) {
      this._fetchAlarms();
      this._subscribeUpdates();
    }
    if (!this._timer) {
      this._timer = setInterval(() => {
        this._updateLiveElements();
      }, 1000);
    }
    if (this._editingAlarmId) {
      this._scheduleChipRefresh();
    }
  }

  _scheduleChipRefresh() {
    if (this._chipRaf) return;
    this._chipRaf = requestAnimationFrame(() => {
      this._chipRaf = null;
      this._refreshAllPreviewChips();
    });
  }

  connectedCallback() {
    this._ensureShadowStructure();
    this._renderDashboard();
    if (this._hass) {
      this._fetchAlarms();
    }
    if (this._timer) clearInterval(this._timer);
    this._timer = setInterval(() => {
      this._updateLiveElements();
    }, 1000);
  }

  disconnectedCallback() {
    if (this._timer) clearInterval(this._timer);
    if (this._testInterval) clearInterval(this._testInterval);
    if (this._chipRaf) cancelAnimationFrame(this._chipRaf);
    if (this._unsubEvents) {
      this._unsubEvents();
      this._unsubEvents = null;
    }
  }

  async _fetchAlarms() {
    if (!this._hass) return;
    try {
      const res = await this._hass.callWS({ type: "smart_wake/get_alarms" });
      this._loading = false;
      this._updateAlarmsData(res.alarms || []);
    } catch (err) {
      console.error("Failed to fetch Smart Wake alarms:", err);
      this._loading = false;
      this._renderDashboard();
    }
  }

  _getAlarmSignature(a) {
    if (!a) return "";
    const cfg = a.config_summary || {};
    return [
      a.id,
      a.name,
      a.time,
      a.enabled,
      a.status,
      a.active_phase,
      (a.days || []).join(","),
      a.snooze_count,
      a.snooze_duration,
      a.max_snooze_count,
      a.pre_alarm_duration,
      a.pre_alarm_time,
      a.next_alarm,
      a.dynamic_offset_minutes,
      a.is_testing,
      a.is_full_test,
      a.is_dry_run,
      cfg.workday_only,
      cfg.person_home_required,
      cfg.mobile_alarm_entity,
      a.alarm_source,
      a.alarm_source_mode,
      cfg.escalation_delay,
      cfg.escalation_volume,
    ].join(":");
  }

  _updateAlarmsData(newAlarms) {
    const oldAlarms = this._alarms || [];
    const oldSig = oldAlarms.map((a) => this._getAlarmSignature(a)).join("###");
    const newSig = (newAlarms || []).map((a) => this._getAlarmSignature(a)).join("###");

    this._alarms = newAlarms;

    if (oldSig !== newSig || !this._dashboardRendered) {
      this._renderDashboard();
    } else {
      this._updateLiveElements();
    }
  }

  _updateLiveElements() {
    if (!this.shadowRoot) return;
    try {
      this._updateCountdowns();
      this._alarms.forEach((alarm) => {
        // Dynamic time updates
        const isMobile = alarm.alarm_source === "mobile" && alarm.next_alarm;
        const displayTime = isMobile ? this._formatTime(alarm.next_alarm) : alarm.time;
        const timeEl = this.shadowRoot.getElementById(`time-${alarm.id}`);
        if (timeEl) {
          const text = isMobile ? `${displayTime} Uhr 📱` : `${displayTime} Uhr`;
          if (timeEl.textContent !== text) timeEl.textContent = text;
        }
        const tlP2 = this.shadowRoot.getElementById(`timeline-p2-${alarm.id}`);
        if (tlP2 && tlP2.textContent !== displayTime) {
          tlP2.textContent = displayTime;
        }
        const tlP1 = this.shadowRoot.getElementById(`timeline-p1-${alarm.id}`);
        if (tlP1) {
          const p1Time = this._formatTime(alarm.pre_alarm_time);
          if (tlP1.textContent !== p1Time) tlP1.textContent = p1Time;
        }

        if (alarm.is_dry_run) {
          const textEl = this.shadowRoot.getElementById(`dryrun-text-${alarm.id}`);
          const barEl = this.shadowRoot.getElementById(`dryrun-bar-${alarm.id}`);
          const phaseEl = this.shadowRoot.getElementById(`dryrun-phase-${alarm.id}`);
          const pct = Math.min(100, (((alarm.dry_run_progress ?? 0) / 30) * 100));
          if (textEl) textEl.textContent = `⏱️ Testlauf Zeitraffer: ${alarm.dry_run_progress ?? 0}s / 30s`;
          if (barEl) barEl.style.width = `${pct}%`;
          if (phaseEl) phaseEl.textContent = (alarm.active_phase || "").toUpperCase();
        }
      });
      this._updateSnoozeToast();
    } catch (err) {
      console.debug("Live elements update error:", err);
    }
  }

  _updateSnoozeToast() {
    if (!this.shadowRoot) return;
    const toast = this.shadowRoot.getElementById("smartWakeToast");
    if (!toast) return;

    const snoozedAlarm = (this._alarms || []).find((a) => a.status === "snoozed");

    if (snoozedAlarm) {
      this._isSnoozeActive = true;
      const now = new Date();
      let remaining = "";
      if (snoozedAlarm.snooze_until) {
        const snoozeDate = new Date(snoozedAlarm.snooze_until);
        const diffSecs = Math.max(0, Math.floor((snoozeDate - now) / 1000));
        const mins = Math.floor(diffSecs / 60);
        const secs = diffSecs % 60;
        remaining = mins > 0 ? `noch ${mins}m ${secs}s` : `noch ${secs}s`;
      } else if (snoozedAlarm.countdown_text) {
        remaining = snoozedAlarm.countdown_text;
      } else {
        remaining = "aktiv";
      }

      const isTest = Boolean(snoozedAlarm.is_testing || snoozedAlarm.is_full_test || snoozedAlarm.is_dry_run);
      const testTag = isTest ? " [Testlauf]" : "";
      const text = `💤 Schlummermodus läuft${testTag} (${remaining}) – Wecker pausiert`;

      // Always update toast text and keep it visible while snoozed!
      toast.textContent = text;
      toast.classList.add("visible");
      toast.classList.add("snoozing");
    } else if (this._isSnoozeActive) {
      this._isSnoozeActive = false;
      toast.classList.remove("snoozing");
      this._showToast("🔔 Schlummern beendet – Wecker wird fortgesetzt!", 3500);
    }
  }

  _updateCountdowns() {
    if (!this.shadowRoot) return;
    const now = new Date();
    this._alarms.forEach((alarm) => {
      const chip = this.shadowRoot.getElementById(`countdown-${alarm.id}`);
      const snoozeBanner = this.shadowRoot.getElementById(`snooze-banner-text-${alarm.id}`);

      let text = "Deaktiviert";
      let snoozeBannerRemaining = "";
      if (!alarm.enabled) {
        text = "Deaktiviert";
      } else if (alarm.status === "snoozed" && alarm.snooze_until) {
        const snoozeDate = new Date(alarm.snooze_until);
        const diffSecs = Math.max(0, Math.floor((snoozeDate - now) / 1000));
        const mins = Math.floor(diffSecs / 60);
        const secs = diffSecs % 60;
        text = mins > 0 ? `Schlummert (noch ${mins}m ${secs}s)` : `Schlummert (noch ${secs}s)`;
        snoozeBannerRemaining = mins > 0 ? `noch ${mins}m ${secs}s` : `noch ${secs}s`;
      } else if (alarm.next_alarm) {
        const nextDate = new Date(alarm.next_alarm);
        const diffSecs = Math.max(0, Math.floor((nextDate - now) / 1000));
        text = this._formatCountdown(diffSecs);
      } else if (alarm.countdown_text) {
        text = alarm.countdown_text;
      }

      if (chip) {
        const formatted = `⏳ ${text}`;
        if (chip.textContent.trim() !== formatted) {
          chip.textContent = formatted;
        }
      }

      if (snoozeBanner && snoozeBannerRemaining) {
        const bannerFormatted = `💤 Schlummermodus aktiv (${snoozeBannerRemaining})`;
        if (snoozeBanner.textContent.trim() !== bannerFormatted) {
          snoozeBanner.textContent = bannerFormatted;
        }
      }
    });
  }

  _formatCountdown(totalSecs) {
    if (totalSecs <= 0) return "Jetzt fällig";
    const hours = Math.floor(totalSecs / 3600);
    const mins = Math.floor((totalSecs % 3600) / 60);
    const parts = [];
    if (hours > 0) parts.push(`${hours} Std.`);
    if (mins > 0 || hours === 0) parts.push(`${mins} Min.`);
    return "in " + parts.join(" ");
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

  _showToast(msg, duration = 4000) {
    if (!this.shadowRoot) return;
    let toast = this.shadowRoot.getElementById("smartWakeToast");
    if (!toast) return;
    this._customToastUntil = Date.now() + duration;
    toast.textContent = msg;
    toast.classList.add("visible");
    toast.classList.remove("snoozing");
    if (this._toastTimeout) clearTimeout(this._toastTimeout);
    this._toastTimeout = setTimeout(() => {
      this._customToastUntil = 0;
      const snoozedAlarm = (this._alarms || []).find((a) => a.status === "snoozed");
      if (snoozedAlarm) {
        this._updateSnoozeToast();
      } else {
        toast.classList.remove("visible");
      }
    }, duration);
  }
  async _snoozeAlarm(alarmId) {
    if (!this._hass) return;
    try {
      const res = await this._hass.callWS({
        type: "smart_wake/snooze",
        alarm_id: alarmId,
      });
      await this._fetchAlarms();
      if (res && res.snoozed) {
        this._showToast("💤 Wecker pausiert und schlummert...");
      } else {
        this._showToast("⚠️ Schlummern nicht möglich oder Maximum erreicht!", 4000);
      }
    } catch (err) {
      this._showToast("⚠️ Schlummern nicht möglich oder Maximum erreicht!", 4000);
    }
  }

  async _dismissAlarm(alarmId) {
    if (!this._hass) return;
    try {
      const res = await this._hass.callWS({
        type: "smart_wake/dismiss",
        alarm_id: alarmId,
      });
      await this._fetchAlarms();
      if (res && res.snoozed) {
        this._showToast("🛡️ Anti-Cheat aktiv: Quittierung wirkt als Schlummern, bis Aufsteh-Beweis (Bewegungsmelder, Leistungsmesser oder NFC) erbracht ist!", 5000);
      } else if (res && res.dismissed) {
        this._showToast("🛑 Wecker erfolgreich beendet und quittiert!", 3000);
      }
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
        mode: "dry_run",
      });
      await this._fetchAlarms();

      // Poll progress during test
      if (this._testInterval) clearInterval(this._testInterval);
      this._testInterval = setInterval(async () => {
        await this._fetchAlarms();
        const a = this._alarms.find((x) => x.id === alarmId);
        if (!a || !a.is_testing) {
          clearInterval(this._testInterval);
        }
      }, 1000);
    } catch (err) {
      console.error("Dry run test failed:", err);
      alert("Fehler beim Starten des Zeitraffer-Tests: " + (err.message || err));
    }
  }

  async _startFullTest(alarmId, startFromPreAlarm = false) {
    if (!this._hass) return;
    try {
      await this._hass.callWS({
        type: "smart_wake/start_full_test",
        alarm_id: alarmId,
        start_from_pre_alarm: startFromPreAlarm,
      });
      await this._fetchAlarms();

      // Poll updates during full test
      if (this._testInterval) clearInterval(this._testInterval);
      this._testInterval = setInterval(async () => {
        await this._fetchAlarms();
        const a = this._alarms.find((x) => x.id === alarmId);
        if (!a || !a.is_testing) {
          clearInterval(this._testInterval);
        }
      }, 2000);
    } catch (err) {
      console.error("Full test failed:", err);
      alert("Fehler beim Starten des vollen Testlaufs: " + (err.message || err));
    }
  }

  async _stopTest(alarmId) {
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

  _openTestModal(alarmId) {
    this._testModalAlarmId = alarmId;
    this._renderModals();
  }

  _closeTestModal() {
    this._testModalAlarmId = null;
    this._renderModals();
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
        mobile_alarm_entity: rawCfg.mobile_alarm_entity ?? sumCfg.mobile_alarm_entity ?? "",
        alarm_source_mode: rawCfg.alarm_source_mode ?? sumCfg.alarm_source_mode ?? "mobile_priority",
        mobile_dismiss_sync: Boolean(rawCfg.mobile_dismiss_sync ?? sumCfg.mobile_dismiss_sync ?? true),

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
        pre_alarm_cover_entities: Array.isArray(rawCfg.pre_alarm_cover_entities)
          ? rawCfg.pre_alarm_cover_entities.join(", ")
          : (sumCfg.pre_alarm_covers ? sumCfg.pre_alarm_covers.join(", ") : ""),
        pre_alarm_cover_position: rawCfg.pre_alarm_cover_position ?? 20,
        pre_alarm_script_entity: rawCfg.pre_alarm_script_entity ?? "",

        // Phase 2: Main Alarm
        main_media_player_entities: Array.isArray(rawCfg.main_media_player_entities)
          ? rawCfg.main_media_player_entities.join(", ")
          : (sumCfg.main_media_players ? sumCfg.main_media_players.join(", ") : ""),
        main_tts_media_player: rawCfg.main_tts_media_player ?? sumCfg.main_tts_media_player ?? "",
        main_audio_content_id: rawCfg.main_audio_content_id ?? sumCfg.main_audio_content ?? "",
        main_audio_content_type: rawCfg.main_audio_content_type ?? "music",
        main_audio_fade_in: Boolean(rawCfg.main_audio_fade_in ?? true),
        main_audio_fade_duration: rawCfg.main_audio_fade_duration ?? 30,
        main_audio_target_volume: Math.round((rawCfg.main_audio_target_volume ?? 0.5) * 100),
        main_tts_enabled: Boolean(rawCfg.main_tts_enabled ?? sumCfg.main_tts_enabled ?? false),
        main_tts_delay: rawCfg.main_tts_delay ?? sumCfg.main_tts_delay ?? 15,
        main_tts_volume: Math.round((rawCfg.main_tts_volume ?? sumCfg.main_tts_volume ?? 0.6) * 100),
        main_tts_message: rawCfg.main_tts_message ?? "Guten Morgen! Es ist {time} Uhr, draußen sind es {temp}°C.",
        main_tts_engine: rawCfg.main_tts_engine ?? "",
        main_script_entity: rawCfg.main_script_entity ?? "",

        // Phase 3: Escalation
        escalation_enabled: Boolean(rawCfg.escalation_enabled ?? true),
        escalation_delay: rawCfg.escalation_delay ?? sumCfg.escalation_delay ?? 10,
        escalation_volume: Math.round((rawCfg.escalation_volume ?? sumCfg.escalation_volume ?? 0.9) * 100),
        escalation_volume_fade_duration: rawCfg.escalation_volume_fade_duration ?? sumCfg.escalation_volume_fade_duration ?? 30,
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
        snooze_button_entity: rawCfg.snooze_button_entity ?? sumCfg.snooze_button ?? "",
        snooze_button_event: rawCfg.snooze_button_event ?? sumCfg.snooze_button_event ?? "",
        dismiss_button_entity: rawCfg.dismiss_button_entity ?? sumCfg.dismiss_button ?? "",
        dismiss_button_event: rawCfg.dismiss_button_event ?? sumCfg.dismiss_button_event ?? "",
        dismiss_motion_entities: Array.isArray(rawCfg.dismiss_motion_entities)
          ? rawCfg.dismiss_motion_entities.join(", ")
          : (sumCfg.dismiss_motion ? sumCfg.dismiss_motion.join(", ") : ""),
        dismiss_nfc_tags: Array.isArray(rawCfg.dismiss_nfc_tags)
          ? rawCfg.dismiss_nfc_tags.join(", ")
          : (sumCfg.dismiss_nfc ? sumCfg.dismiss_nfc.join(", ") : ""),
        dismiss_power_sensor: rawCfg.dismiss_power_sensor ?? sumCfg.dismiss_power ?? "",
        dismiss_power_threshold: rawCfg.dismiss_power_threshold ?? 10.0,
        dismiss_input_boolean: rawCfg.dismiss_input_boolean ?? sumCfg.dismiss_input_boolean ?? "",
      };
    } else {
      this._editConfig = {
        name: "Neuer Wecker",
        time: "06:30",
        enabled: true,
        days: ["mon", "tue", "wed", "thu", "fri"],
        mobile_alarm_entity: "",
        alarm_source_mode: "mobile_priority",
        mobile_dismiss_sync: true,

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
        pre_alarm_cover_entities: "",
        pre_alarm_cover_position: 20,
        pre_alarm_script_entity: "",

        main_media_player_entities: "",
        main_tts_media_player: "",
        main_audio_content_id: "",
        main_audio_content_type: "music",
        main_audio_fade_in: true,
        main_audio_fade_duration: 30,
        main_audio_target_volume: 50,
        main_tts_enabled: false,
        main_tts_delay: 15,
        main_tts_volume: 60,
        main_tts_message: "Guten Morgen! Es ist {time} Uhr, draußen sind es {temp}°C.",
        main_tts_engine: "",
        main_script_entity: "",

        escalation_enabled: true,
        escalation_delay: 10,
        escalation_volume: 90,
        escalation_volume_fade_duration: 30,
        escalation_light_entities: "",
        escalation_light_brightness: 100,
        escalation_light_cold_white: true,
        escalation_cover_entities: "",
        escalation_cover_position: 100,
        escalation_script_entity: "",

        snooze_duration: 8,
        max_snooze_count: 2,
        snooze_button_entity: "",
        snooze_button_event: "",
        dismiss_button_entity: "",
        dismiss_button_event: "",
        dismiss_motion_entities: "",
        dismiss_nfc_tags: "",
        dismiss_power_sensor: "",
        dismiss_power_threshold: 10.0,
        dismiss_input_boolean: "",
      };
    }
    this._renderModals();
  }

  _closeSettingsModal() {
    this._editingAlarmId = null;
    this._editConfig = null;
    this._saving = false;
    this._renderModals();
  }

  _switchModalTab(targetTab) {
    if (this._activeTab === targetTab) return;
    this._collectFormValues();
    this._activeTab = targetTab;

    const root = this.shadowRoot;
    if (!root) return;

    root.querySelectorAll(".tab-btn").forEach((btn) => {
      const tab = btn.getAttribute("data-tab");
      if (tab === targetTab) {
        btn.classList.add("active");
      } else {
        btn.classList.remove("active");
      }
    });

    const modalBody = root.getElementById("modalBody");
    if (modalBody) {
      modalBody.innerHTML = this._renderTabContent();
      this._initEntityAutocompletes();
      if (targetTab === "general") {
        this._attachDayChipsListeners();
      }
    }
  }

  _attachDayChipsListeners() {
    const root = this.shadowRoot;
    if (!root) return;
    root.querySelectorAll(".day-chip").forEach((chip) => {
      chip.onclick = () => {
        const day = chip.getAttribute("data-day");
        if (day && this._editConfig) {
          const currentDays = this._editConfig.days || [];
          if (currentDays.includes(day)) {
            this._editConfig.days = currentDays.filter((d) => d !== day);
            chip.classList.remove("active");
          } else {
            this._editConfig.days = [...currentDays, day];
            chip.classList.add("active");
          }
        }
      };
    });
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
    if (getVal("f_mobile_alarm_entity") !== undefined) this._editConfig.mobile_alarm_entity = getVal("f_mobile_alarm_entity");
    const sourceRadio = root.querySelector("input[name='f_alarm_source_mode']:checked");
    if (sourceRadio) this._editConfig.alarm_source_mode = sourceRadio.value;
    if (getChecked("f_mobile_dismiss_sync") !== undefined) this._editConfig.mobile_dismiss_sync = getChecked("f_mobile_dismiss_sync");

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
    if (getVal("f_pre_alarm_cover_entities") !== undefined) this._editConfig.pre_alarm_cover_entities = getVal("f_pre_alarm_cover_entities");
    if (getVal("f_pre_alarm_cover_position") !== undefined) this._editConfig.pre_alarm_cover_position = getVal("f_pre_alarm_cover_position");
    if (getVal("f_pre_alarm_script_entity") !== undefined) this._editConfig.pre_alarm_script_entity = getVal("f_pre_alarm_script_entity");

    // Phase 2 Tab
    if (getVal("f_main_media_player_entities") !== undefined) this._editConfig.main_media_player_entities = getVal("f_main_media_player_entities");
    if (getVal("f_main_tts_media_player") !== undefined) this._editConfig.main_tts_media_player = getVal("f_main_tts_media_player");
    if (getVal("f_main_audio_content_id") !== undefined) this._editConfig.main_audio_content_id = getVal("f_main_audio_content_id");
    if (getVal("f_main_audio_content_type") !== undefined) this._editConfig.main_audio_content_type = getVal("f_main_audio_content_type");
    if (getChecked("f_main_audio_fade_in") !== undefined) this._editConfig.main_audio_fade_in = getChecked("f_main_audio_fade_in");
    if (getVal("f_main_audio_fade_duration") !== undefined) this._editConfig.main_audio_fade_duration = getVal("f_main_audio_fade_duration");
    if (getVal("f_main_audio_target_volume") !== undefined) this._editConfig.main_audio_target_volume = getVal("f_main_audio_target_volume");
    if (getChecked("f_main_tts_enabled") !== undefined) this._editConfig.main_tts_enabled = getChecked("f_main_tts_enabled");
    if (getVal("f_main_tts_delay") !== undefined) this._editConfig.main_tts_delay = getVal("f_main_tts_delay");
    if (getVal("f_main_tts_volume") !== undefined) this._editConfig.main_tts_volume = getVal("f_main_tts_volume");
    if (getVal("f_main_tts_message") !== undefined) this._editConfig.main_tts_message = getVal("f_main_tts_message");
    if (getVal("f_main_tts_engine") !== undefined) this._editConfig.main_tts_engine = getVal("f_main_tts_engine");
    if (getVal("f_main_script_entity") !== undefined) this._editConfig.main_script_entity = getVal("f_main_script_entity");

    // Phase 3 Tab
    if (getChecked("f_escalation_enabled") !== undefined) this._editConfig.escalation_enabled = getChecked("f_escalation_enabled");
    if (getVal("f_escalation_delay") !== undefined) this._editConfig.escalation_delay = getVal("f_escalation_delay");
    if (getVal("f_escalation_volume") !== undefined) this._editConfig.escalation_volume = getVal("f_escalation_volume");
    if (getVal("f_escalation_volume_fade_duration") !== undefined) this._editConfig.escalation_volume_fade_duration = getVal("f_escalation_volume_fade_duration");
    if (getChecked("f_escalation_light_cold_white") !== undefined) this._editConfig.escalation_light_cold_white = getChecked("f_escalation_light_cold_white");
    if (getVal("f_escalation_light_entities") !== undefined) this._editConfig.escalation_light_entities = getVal("f_escalation_light_entities");
    if (getVal("f_escalation_cover_position") !== undefined) this._editConfig.escalation_cover_position = getVal("f_escalation_cover_position");
    if (getVal("f_escalation_cover_entities") !== undefined) this._editConfig.escalation_cover_entities = getVal("f_escalation_cover_entities");
    if (getVal("f_escalation_script_entity") !== undefined) this._editConfig.escalation_script_entity = getVal("f_escalation_script_entity");

    // Snooze & Anti-Cheat Tab
    if (getVal("f_snooze_duration") !== undefined) this._editConfig.snooze_duration = getVal("f_snooze_duration");
    if (getVal("f_max_snooze_count") !== undefined) this._editConfig.max_snooze_count = getVal("f_max_snooze_count");
    if (getVal("f_snooze_button_entity") !== undefined) this._editConfig.snooze_button_entity = getVal("f_snooze_button_entity");
    if (getVal("f_snooze_button_event") !== undefined) this._editConfig.snooze_button_event = getVal("f_snooze_button_event");
    if (getVal("f_dismiss_button_entity") !== undefined) this._editConfig.dismiss_button_entity = getVal("f_dismiss_button_entity");
    if (getVal("f_dismiss_button_event") !== undefined) this._editConfig.dismiss_button_event = getVal("f_dismiss_button_event");
    if (getVal("f_dismiss_motion_entities") !== undefined) this._editConfig.dismiss_motion_entities = getVal("f_dismiss_motion_entities");
    if (getVal("f_dismiss_nfc_tags") !== undefined) this._editConfig.dismiss_nfc_tags = getVal("f_dismiss_nfc_tags");
    if (getVal("f_dismiss_power_sensor") !== undefined) this._editConfig.dismiss_power_sensor = getVal("f_dismiss_power_sensor");
    if (getVal("f_dismiss_power_threshold") !== undefined) this._editConfig.dismiss_power_threshold = getVal("f_dismiss_power_threshold");
    if (getVal("f_dismiss_input_boolean") !== undefined) this._editConfig.dismiss_input_boolean = getVal("f_dismiss_input_boolean");
  }

  async _saveSettings() {
    if (!this._hass || !this._editConfig) return;
    this._collectFormValues();
    this._saving = true;

    const btnSave = this.shadowRoot ? this.shadowRoot.getElementById("btnSaveModal") : null;
    if (btnSave) {
      btnSave.disabled = true;
      btnSave.textContent = "💾 Speichern...";
    }

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
        mobile_alarm_entity: this._editConfig.mobile_alarm_entity || null,
        alarm_source_mode: this._editConfig.alarm_source_mode || "mobile_priority",
        mobile_dismiss_sync: Boolean(this._editConfig.mobile_dismiss_sync),

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
        pre_alarm_cover_entities: toList(this._editConfig.pre_alarm_cover_entities),
        pre_alarm_cover_position: parseInt(this._editConfig.pre_alarm_cover_position, 10) || 20,
        pre_alarm_script_entity: this._editConfig.pre_alarm_script_entity || null,

        main_media_player_entities: toList(this._editConfig.main_media_player_entities),
        main_tts_media_player: this._editConfig.main_tts_media_player || null,
        main_audio_content_id: this._editConfig.main_audio_content_id || null,
        main_audio_content_type: this._editConfig.main_audio_content_type || "music",
        main_audio_fade_in: Boolean(this._editConfig.main_audio_fade_in),
        main_audio_fade_duration: parseInt(this._editConfig.main_audio_fade_duration, 10) || 30,
        main_audio_target_volume: (parseInt(this._editConfig.main_audio_target_volume, 10) || 50) / 100,
        main_tts_enabled: Boolean(this._editConfig.main_tts_enabled),
        main_tts_delay: parseInt(this._editConfig.main_tts_delay, 10) ?? 15,
        main_tts_volume: (parseInt(this._editConfig.main_tts_volume, 10) || 60) / 100,
        main_tts_message: this._editConfig.main_tts_message || "",
        main_tts_engine: this._editConfig.main_tts_engine || null,
        main_script_entity: this._editConfig.main_script_entity || null,

        escalation_enabled: Boolean(this._editConfig.escalation_enabled),
        escalation_delay: parseInt(this._editConfig.escalation_delay, 10) || 10,
        escalation_volume: (parseInt(this._editConfig.escalation_volume, 10) || 90) / 100,
        escalation_volume_fade_duration: parseInt(this._editConfig.escalation_volume_fade_duration, 10) ?? 30,
        escalation_light_entities: toList(this._editConfig.escalation_light_entities),
        escalation_light_brightness: parseInt(this._editConfig.escalation_light_brightness, 10) || 100,
        escalation_light_cold_white: Boolean(this._editConfig.escalation_light_cold_white),
        escalation_cover_entities: toList(this._editConfig.escalation_cover_entities),
        escalation_cover_position: parseInt(this._editConfig.escalation_cover_position, 10) || 100,
        escalation_script_entity: this._editConfig.escalation_script_entity || null,

        snooze_duration: parseInt(this._editConfig.snooze_duration, 10) || 8,
        max_snooze_count: parseInt(this._editConfig.max_snooze_count, 10) || 2,
        snooze_button_entity: this._editConfig.snooze_button_entity || null,
        snooze_button_event: this._editConfig.snooze_button_event || "",
        dismiss_button_entity: this._editConfig.dismiss_button_entity || null,
        dismiss_button_event: this._editConfig.dismiss_button_event || "",
        dismiss_motion_entities: toList(this._editConfig.dismiss_motion_entities),
        dismiss_nfc_tags: toList(this._editConfig.dismiss_nfc_tags),
        dismiss_power_sensor: this._editConfig.dismiss_power_sensor || null,
        dismiss_power_threshold: parseFloat(this._editConfig.dismiss_power_threshold) || 10.0,
        dismiss_input_boolean: this._editConfig.dismiss_input_boolean || null,
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
      this._renderDashboard();
      this._showToast("💾 Einstellungen erfolgreich gespeichert!", 3000);
    } catch (err) {
      console.error("Failed to save alarm settings:", err);
      alert("Fehler beim Speichern: " + (err.message || err));
      this._saving = false;
      const btnSave = this.shadowRoot ? this.shadowRoot.getElementById("btnSaveModal") : null;
      if (btnSave) {
        btnSave.disabled = false;
        btnSave.textContent = "💾 Einstellungen speichern";
      }
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
      this._renderDashboard();
      this._showToast("🗑️ Wecker erfolgreich gelöscht!", 3000);
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

  _getStatusBadge(status, phase, isFullTest = false) {
    let color = "#78909c";
    let text = status.toUpperCase();
    let pulse = false;

    if (isFullTest) {
      if (status === "ringing") {
        color = "#e53935";
        text = phase === "escalation" ? "🔔 TEST: ESKALATION!" : "🔔 TEST: KLINGELT";
        pulse = true;
      } else if (status === "pre_alarm") {
        color = "#fb8c00";
        text = "🌅 TEST: PRE-ALARM";
        pulse = true;
      } else if (status === "snoozed") {
        color = "#8e24aa";
        text = "💤 TEST: SCHLUMMERT";
        pulse = true;
      } else {
        color = "#e53935";
        text = "🔔 TESTLAUF AKTIV";
        pulse = true;
      }
    } else {
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
    }

    return `<span class="badge ${pulse ? "pulse" : ""}" style="background-color: ${color};">${text}</span>`;
  }

  // ---------------------------------------------------------------------------
  // Entity Autocomplete & Live Preview Helpers
  // ---------------------------------------------------------------------------
  _getEntityDomainIcon(entityId, attributes = {}) {
    if (!entityId) return "🔹";
    const domain = entityId.split(".")[0];
    switch (domain) {
      case "light":
        return "💡";
      case "switch":
        return "🔌";
      case "person":
        return "👤";
      case "media_player":
        return "🔊";
      case "climate":
        return "🌡️";
      case "cover":
        return "🪟";
      case "calendar":
        return "📅";
      case "binary_sensor": {
        const dc = attributes.device_class;
        if (dc === "motion" || dc === "occupancy" || dc === "presence") return "🏃";
        if (dc === "door" || dc === "window" || dc === "opening") return "🚪";
        if (dc === "moisture") return "💧";
        if (dc === "sound") return "🔊";
        if (dc === "vibration") return "📳";
        return "🔘";
      }
      case "sensor": {
        const dc = attributes.device_class;
        if (dc === "temperature") return "🌡️";
        if (dc === "power" || dc === "energy") return "⚡";
        if (dc === "battery") return "🔋";
        if (dc === "humidity") return "💧";
        if (dc === "illuminance") return "☀️";
        return "📊";
      }
      case "script":
        return "📜";
      case "button":
        return "🔘";
      case "event":
        return "⚡";
      case "tts":
        return "🗣️";
      case "weather":
        return "⛅";
      case "automation":
        return "⚙️";
      default:
        return "🔹";
    }
  }

  _formatEntityState(stateObj) {
    if (!stateObj) return "";
    let val = stateObj.state;
    const unit = stateObj.attributes?.unit_of_measurement;
    if (val === "on") val = "an";
    else if (val === "off") val = "aus";
    else if (val === "home") val = "zuhause";
    else if (val === "not_home") val = "abwesend";
    else if (val === "unavailable") val = "nicht verfügbar";
    else if (val === "unknown") val = "unbekannt";
    else if (val === "playing") val = "spielt";
    else if (val === "paused") val = "pausiert";
    else if (val === "idle") val = "standby";

    if (unit) return `${val} ${unit}`;
    return val;
  }

  _searchEntities(query = "", domainsStr = "") {
    if (!this._hass || !this._hass.states) return [];
    const allowedDomains = domainsStr
      ? domainsStr.split(",").map((d) => d.trim().toLowerCase()).filter(Boolean)
      : [];
    const q = (query || "").trim().toLowerCase();

    const allStates = Object.values(this._hass.states);
    const results = [];

    for (const s of allStates) {
      const eid = s.entity_id.toLowerCase();
      const domain = eid.split(".")[0];
      const fname = (s.attributes?.friendly_name || "").toLowerCase();

      const inDomain = allowedDomains.length === 0 || allowedDomains.includes(domain);

      let score = 0;
      if (!q) {
        if (!inDomain) continue;
        score = 1;
      } else {
        if (eid === q) score = 100;
        else if (fname === q) score = 90;
        else if (eid.startsWith(q)) score = 80;
        else if (fname.startsWith(q)) score = 70;
        else if (eid.includes(q)) score = 60;
        else if (fname.includes(q)) score = 50;
        else continue;

        if (inDomain) score += 25;
      }

      results.push({
        state: s,
        score,
        name: s.attributes?.friendly_name || s.entity_id,
      });
    }

    results.sort((a, b) => {
      if (b.score !== a.score) return b.score - a.score;
      return a.name.localeCompare(b.name);
    });

    return results.slice(0, 10).map((r) => r.state);
  }

  _renderEntityField(id, label, value, placeholder, hint, domain, isMultiple = false) {
    return `
      <div class="form-group">
        <label class="form-label" for="${id}">${label}</label>
        <div class="entity-input-wrapper">
          <input
            class="form-input entity-autocomplete-input"
            id="${id}"
            type="text"
            value="${value || ""}"
            placeholder="${placeholder || ""}"
            data-domain="${domain || ""}"
            data-multiple="${isMultiple ? "true" : "false"}"
            autocomplete="off"
            spellcheck="false"
          />
          <div class="entity-autocomplete-dropdown" id="dropdown-${id}" style="display: none;"></div>
        </div>
        <div class="entity-preview-chips" id="preview-${id}"></div>
        ${hint ? `<span class="form-hint">${hint}</span>` : ""}
      </div>
    `;
  }

  _updatePreviewChips(input, chipsContainer) {
    if (!input || !chipsContainer) return;
    const rawVal = input.value || "";
    const isMultiple = input.getAttribute("data-multiple") === "true";
    const parts = rawVal
      .split(",")
      .map((p) => p.trim())
      .filter(Boolean);

    if (parts.length === 0) {
      if (chipsContainer.children.length > 0) {
        chipsContainer.innerHTML = "";
      }
      return;
    }

    // Check if same entities are already rendered to avoid rebuilding DOM & flickering
    const existingChips = Array.from(chipsContainer.querySelectorAll(".entity-chip"));
    const existingIds = existingChips.map((c) => c.getAttribute("data-entity-id"));
    const sameList =
      existingIds.length === parts.length &&
      existingIds.every((id, idx) => id === parts[idx]);

    if (sameList) {
      // Update text and verification state in-place without touching DOM tree or listeners
      parts.forEach((entId, idx) => {
        const chip = existingChips[idx];
        const stateObj = this._hass && this._hass.states ? this._hass.states[entId] : null;
        const stateSpan = chip.querySelector(".entity-chip-state");
        if (stateObj) {
          const newState = this._formatEntityState(stateObj);
          if (stateSpan && stateSpan.textContent !== newState) {
            stateSpan.textContent = newState;
          }
          if (chip.classList.contains("unverified")) {
            chip.classList.remove("unverified");
            const iconSpan = chip.querySelector(".entity-chip-icon");
            if (iconSpan) iconSpan.textContent = this._getEntityDomainIcon(entId, stateObj.attributes);
            const nameSpan = chip.querySelector(".entity-chip-name");
            if (nameSpan) nameSpan.textContent = stateObj.attributes?.friendly_name || entId;
          }
        } else {
          if (!chip.classList.contains("unverified")) {
            chip.classList.add("unverified");
            const iconSpan = chip.querySelector(".entity-chip-icon");
            if (iconSpan) iconSpan.textContent = "⚠️";
          }
          if (stateSpan && stateSpan.textContent !== "Nicht in HA gefunden") {
            stateSpan.textContent = "Nicht in HA gefunden";
          }
        }
      });
      return;
    }

    const html = parts.map((entId) => {
      const stateObj = this._hass && this._hass.states ? this._hass.states[entId] : null;
      if (stateObj) {
        const icon = this._getEntityDomainIcon(entId, stateObj.attributes);
        const name = stateObj.attributes?.friendly_name || entId;
        const stateStr = this._formatEntityState(stateObj);
        return `
          <div class="entity-chip" data-entity-id="${entId}" title="${entId}">
            <span class="entity-chip-icon">${icon}</span>
            <span class="entity-chip-name">${name}</span>
            <span class="entity-chip-state">${stateStr}</span>
            <button type="button" class="entity-chip-remove" data-remove="${entId}" title="${entId} entfernen">&times;</button>
          </div>
        `;
      } else {
        return `
          <div class="entity-chip unverified" data-entity-id="${entId}" title="Nicht in Home Assistant gefunden">
            <span class="entity-chip-icon">⚠️</span>
            <span class="entity-chip-name">${entId}</span>
            <span class="entity-chip-state">Nicht in HA gefunden</span>
            <button type="button" class="entity-chip-remove" data-remove="${entId}" title="${entId} entfernen">&times;</button>
          </div>
        `;
      }
    }).join("");

    chipsContainer.innerHTML = html;

    chipsContainer.querySelectorAll(".entity-chip-remove").forEach((btn) => {
      btn.onclick = (e) => {
        e.stopPropagation();
        const toRemove = btn.getAttribute("data-remove");
        if (!toRemove) return;

        if (isMultiple) {
          const currentList = input.value
            .split(",")
            .map((p) => p.trim())
            .filter((p) => p && p !== toRemove);
          input.value = currentList.join(", ");
        } else {
          input.value = "";
        }

        this._updatePreviewChips(input, chipsContainer);
        this._collectFormValues();
      };
    });
  }

  _refreshAllPreviewChips() {
    if (!this.shadowRoot) return;
    this.shadowRoot.querySelectorAll(".entity-autocomplete-input").forEach((input) => {
      const preview = this.shadowRoot.getElementById(`preview-${input.id}`);
      if (preview) {
        this._updatePreviewChips(input, preview);
      }
    });
  }

  _initEntityAutocompletes() {
    const root = this.shadowRoot;
    if (!root) return;

    const inputs = root.querySelectorAll(".entity-autocomplete-input");
    inputs.forEach((input) => {
      const id = input.id;
      const dropdown = root.getElementById(`dropdown-${id}`);
      const preview = root.getElementById(`preview-${id}`);
      const domain = input.getAttribute("data-domain") || "";
      const isMulti = input.getAttribute("data-multiple") === "true";

      if (!dropdown || !preview) return;

      this._updatePreviewChips(input, preview);

      let currentResults = [];
      let activeIdx = -1;

      const getActiveToken = () => {
        if (!isMulti) return input.value.trim();
        const pos = input.selectionStart ?? input.value.length;
        const textBefore = input.value.slice(0, pos);
        const lastComma = textBefore.lastIndexOf(",");
        return (lastComma >= 0 ? textBefore.slice(lastComma + 1) : textBefore).trim();
      };

      const selectEntity = (eid) => {
        if (!isMulti) {
          input.value = eid;
        } else {
          const pos = input.selectionStart ?? input.value.length;
          const textBefore = input.value.slice(0, pos);
          const textAfter = input.value.slice(pos);
          const lastComma = textBefore.lastIndexOf(",");
          const prefix = lastComma >= 0 ? textBefore.slice(0, lastComma + 1) + " " : "";
          input.value = (prefix + eid + ", " + textAfter.replace(/^[\s,]+/, "")).trim();
        }
        dropdown.style.display = "none";
        activeIdx = -1;
        this._updatePreviewChips(input, preview);
        this._collectFormValues();
        input.focus();
      };

      const renderDropdown = () => {
        if (currentResults.length === 0) {
          dropdown.innerHTML = `<div class="autocomplete-no-results">Keine passenden Entities gefunden</div>`;
        } else {
          dropdown.innerHTML = currentResults.map((s, idx) => {
            const icon = this._getEntityDomainIcon(s.entity_id, s.attributes);
            const name = s.attributes?.friendly_name || s.entity_id;
            const stateStr = this._formatEntityState(s);
            return `
              <div class="autocomplete-item ${idx === activeIdx ? "highlighted" : ""}" data-index="${idx}" data-eid="${s.entity_id}">
                <div class="autocomplete-item-left">
                  <span class="autocomplete-item-icon">${icon}</span>
                  <div class="autocomplete-item-info">
                    <span class="autocomplete-item-name">${name}</span>
                    <span class="autocomplete-item-id">${s.entity_id}</span>
                  </div>
                </div>
                <div class="autocomplete-item-right">
                  <span class="autocomplete-item-state">${stateStr}</span>
                </div>
              </div>
            `;
          }).join("");

          dropdown.querySelectorAll(".autocomplete-item").forEach((item) => {
            item.onmousedown = (e) => {
              e.preventDefault();
              const eid = item.getAttribute("data-eid");
              if (eid) selectEntity(eid);
            };
          });
        }
        dropdown.style.display = "block";
      };

      const openAutocomplete = () => {
        root.querySelectorAll(".entity-autocomplete-dropdown").forEach((dd) => {
          if (dd !== dropdown) dd.style.display = "none";
        });
        const query = getActiveToken();
        currentResults = this._searchEntities(query, domain);
        activeIdx = -1;
        renderDropdown();
      };

      input.onfocus = () => {
        openAutocomplete();
      };

      input.oninput = () => {
        openAutocomplete();
        this._updatePreviewChips(input, preview);
        this._collectFormValues();
      };

      input.onkeydown = (e) => {
        if (dropdown.style.display === "none") {
          if (e.key === "ArrowDown") {
            openAutocomplete();
            e.preventDefault();
          }
          return;
        }

        if (e.key === "ArrowDown") {
          e.preventDefault();
          if (currentResults.length > 0) {
            activeIdx = (activeIdx + 1) % currentResults.length;
            renderDropdown();
            const highlighted = dropdown.querySelector(".autocomplete-item.highlighted");
            if (highlighted) highlighted.scrollIntoView({ block: "nearest" });
          }
        } else if (e.key === "ArrowUp") {
          e.preventDefault();
          if (currentResults.length > 0) {
            activeIdx = (activeIdx - 1 + currentResults.length) % currentResults.length;
            renderDropdown();
            const highlighted = dropdown.querySelector(".autocomplete-item.highlighted");
            if (highlighted) highlighted.scrollIntoView({ block: "nearest" });
          }
        } else if (e.key === "Enter") {
          if (activeIdx >= 0 && currentResults[activeIdx]) {
            e.preventDefault();
            selectEntity(currentResults[activeIdx].entity_id);
          }
        } else if (e.key === "Escape") {
          dropdown.style.display = "none";
          activeIdx = -1;
        }
      };

      input.onblur = () => {
        setTimeout(() => {
          dropdown.style.display = "none";
        }, 150);
      };
    });
  }

  _renderDashboard() {
    this._ensureShadowStructure();
    const appEl = this.shadowRoot.getElementById("panelApp");
    if (!appEl) return;

    appEl.innerHTML = `
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

    this._dashboardRendered = true;

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

      const timeEl = this.shadowRoot.getElementById(`time-${alarm.id}`);
      if (timeEl) {
        timeEl.onclick = () => this._openSettingsModal(alarm.id);
      }

      const btnFullTest = this.shadowRoot.getElementById(`full-test-${alarm.id}`);
      if (btnFullTest) {
        btnFullTest.onclick = () => {
          if (alarm.pre_alarm_duration > 0) {
            this._openTestModal(alarm.id);
          } else {
            this._startFullTest(alarm.id, false);
          }
        };
      }

      const btnDryRun = this.shadowRoot.getElementById(`dry-run-${alarm.id}`);
      if (btnDryRun) {
        btnDryRun.onclick = () => this._startDryRun(alarm.id);
      }

      const btnStopTest = this.shadowRoot.getElementById(`stop-test-${alarm.id}`);
      if (btnStopTest) {
        btnStopTest.onclick = () => this._stopTest(alarm.id);
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

    this._updateLiveElements();
  }

  _renderModals() {
    this._ensureShadowStructure();
    const modalHost = this.shadowRoot.getElementById("modalHost");
    if (!modalHost) return;

    if (this._editingAlarmId) {
      modalHost.innerHTML = this._renderSettingsModal();
      this._attachModalListeners();
    } else if (this._testModalAlarmId) {
      modalHost.innerHTML = this._renderTestModal();
      this._attachTestModalListeners();
    } else {
      modalHost.innerHTML = "";
    }
  }

  _render() {
    this._ensureShadowStructure();
    this._renderDashboard();
    this._renderModals();
  }
  _renderTestModal() {
    const alarm = this._alarms.find((a) => a.id === this._testModalAlarmId);
    if (!alarm) return "";

    return `
      <div class="modal-backdrop" id="testModalBackdrop">
        <div class="modal-container" style="max-width: 540px;">
          <div class="modal-header">
            <div class="modal-title-group">
              <span class="modal-icon">🔔</span>
              <div>
                <h2 class="modal-title">Voller Testlauf: ${alarm.name}</h2>
                <div class="modal-subtitle">Wähle die Startphase für den Echtzeit-Testlauf</div>
              </div>
            </div>
            <button class="btn-close" id="btnCloseTestModal" title="Schließen">&times;</button>
          </div>

          <div class="modal-body" style="padding: 20px; display: flex; flex-direction: column; gap: 14px;">
            <div class="test-choice-card" id="btnChoicePreAlarm">
              <div class="test-choice-icon">🌅</div>
              <div class="test-choice-content">
                <div class="test-choice-title">Phase 1: Pre-Alarm starten</div>
                <div class="test-choice-desc">
                  Startet sanftes Licht & Jalousien (${alarm.pre_alarm_duration} Min.) und wechselt danach automatisch zum Hauptalarm.
                </div>
              </div>
              <button class="btn-primary" style="align-self: center; white-space: nowrap; pointer-events: none;">Starten</button>
            </div>

            <div class="test-choice-card" id="btnChoiceMainAlarm">
              <div class="test-choice-icon">🔔</div>
              <div class="test-choice-content">
                <div class="test-choice-title">Phase 2: Hauptalarm direkt starten</div>
                <div class="test-choice-desc">
                  Startet direkt Audio/TTS, aktiviert Anti-Cheat Quittierungs-Sensoren (Taster, Bewegung, Leistung, NFC) und den Eskalationstimer.
                </div>
              </div>
              <button class="btn-primary" style="align-self: center; white-space: nowrap; background: #e53935; pointer-events: none;">Direkt starten</button>
            </div>
          </div>

          <div class="modal-footer" style="justify-content: flex-end;">
            <button class="btn-cancel" id="btnCancelTestModal">Abbrechen</button>
          </div>
        </div>
      </div>
    `;
  }

  _attachTestModalListeners() {
    const root = this.shadowRoot;
    const backdrop = root.getElementById("testModalBackdrop");
    if (backdrop) {
      backdrop.onclick = (e) => {
        if (e.target === backdrop) this._closeTestModal();
      };
    }

    const btnClose = root.getElementById("btnCloseTestModal");
    if (btnClose) btnClose.onclick = () => this._closeTestModal();

    const btnCancel = root.getElementById("btnCancelTestModal");
    if (btnCancel) btnCancel.onclick = () => this._closeTestModal();

    const alarmId = this._testModalAlarmId;
    const btnChoicePre = root.getElementById("btnChoicePreAlarm");
    if (btnChoicePre) {
      btnChoicePre.onclick = () => {
        this._closeTestModal();
        this._startFullTest(alarmId, true);
      };
    }

    const btnChoiceMain = root.getElementById("btnChoiceMainAlarm");
    if (btnChoiceMain) {
      btnChoiceMain.onclick = () => {
        this._closeTestModal();
        this._startFullTest(alarmId, false);
      };
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
        if (targetTab) {
          this._switchModalTab(targetTab);
        }
      };
    });

    // Day chips in general tab
    this._attachDayChipsListeners();

    // Close open autocomplete dropdowns when clicking outside
    const container = root.querySelector(".modal-container");
    if (container) {
      container.addEventListener("click", (e) => {
        if (!e.target.closest(".entity-input-wrapper")) {
          root.querySelectorAll(".entity-autocomplete-dropdown").forEach((dd) => {
            dd.style.display = "none";
          });
        }
      });
    }

    // Initialize Entity Autocomplete & Live Previews for all entity inputs
    this._initEntityAutocompletes();
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
    const isTesting = Boolean(alarm.is_testing);
    const isFullTest = Boolean(alarm.is_full_test);
    const isDryRun = Boolean(alarm.is_dry_run);
    const isRinging =
      alarm.status === "ringing" ||
      alarm.status === "pre_alarm" ||
      alarm.status === "snoozed" ||
      isFullTest;
    const dryRunPct = Math.min(100, (alarm.dry_run_progress / 30) * 100);

    const cfg = alarm.config_summary || {};
    const daysStr = (alarm.days || []).map((d) => d.toUpperCase()).join(", ");
    const isMobile = alarm.alarm_source === "mobile" && alarm.next_alarm;
    const displayTime = isMobile ? this._formatTime(alarm.next_alarm) : alarm.time;

    return `
      <div class="alarm-card">
        <div class="card-header">
          <div>
            <h2 class="alarm-title">
              <span>⏰</span> ${alarm.name}
            </h2>
            <div style="margin-top: 6px;">
              ${this._getStatusBadge(alarm.status, alarm.active_phase, isFullTest)}
            </div>
          </div>
          <label class="switch-toggle">
            <input type="checkbox" id="toggle-${alarm.id}" ${alarm.enabled ? "checked" : ""}>
            <span class="slider"></span>
          </label>
        </div>

        <div class="time-row">
          <div class="big-time" id="time-${alarm.id}" style="cursor: pointer;" title="Weckzeit ändern (Klicken öffnet Einstellungen)">${isMobile ? `${displayTime} Uhr 📱` : `${alarm.time} Uhr`}</div>
          <div class="countdown-chip" id="countdown-${alarm.id}">
            ⏳ ${alarm.countdown_text}
          </div>
        </div>

        <div class="meta-tags">
          <div class="tag">📅 Tage: ${daysStr}</div>
          ${cfg.workday_only ? `<div class="tag workday">💼 Nur Werktage: AN</div>` : ""}
          ${cfg.person_home_required ? `<div class="tag">👤 Anwesenheit: Erforderlich</div>` : ""}
          ${
            alarm.alarm_source === "mobile" && alarm.next_alarm
              ? `<div class="tag highlight">📱 Handy-Wecker aktiv (${this._formatTime(alarm.next_alarm)} Uhr)</div>`
              : (alarm.alarm_source_mode === "mobile_only" || cfg.alarm_source_mode === "mobile_only")
              ? `<div class="tag">📱 Handy-Wecker: Wartet auf Alarm</div>`
              : (cfg.mobile_alarm_entity && (alarm.alarm_source_mode === "mobile_priority" || cfg.alarm_source_mode === "mobile_priority"))
              ? `<div class="tag">📱 Handy-Wecker: Nicht aktiv (Fallback: ${alarm.time} Uhr)</div>`
              : ""
          }
          ${
            alarm.dynamic_offset_minutes > 0
              ? `<div class="tag highlight">❄️ Wetter-Offset: -${alarm.dynamic_offset_minutes} Min (${alarm.offset_reasons.join(", ")})</div>`
              : ""
          }
        </div>

        <div class="timeline">
          <div class="timeline-title">Ablauf & Phasen</div>
          <div class="timeline-item">
            <div class="timeline-time" id="timeline-p1-${alarm.id}">${this._formatTime(alarm.pre_alarm_time)}</div>
            <div class="timeline-dot p1"></div>
            <div class="timeline-desc">Phase 1: Pre-Alarm (${alarm.pre_alarm_duration} Min sanftes Erwachen)</div>
          </div>
          <div class="timeline-item">
            <div class="timeline-time" id="timeline-p2-${alarm.id}">${displayTime}</div>
            <div class="timeline-dot p2"></div>
            <div class="timeline-desc">Phase 2: Hauptalarm (Audio Fade-in + TTS Morgenbriefing)</div>
          </div>
          <div class="timeline-item">
            <div class="timeline-time">+${cfg.escalation_delay || 10}m</div>
            <div class="timeline-dot p3"></div>
            <div class="timeline-desc">Phase 3: Eskalation (Volles Licht 100%, sanfter Audio-Anstieg auf ${Math.round((cfg.escalation_volume || 0.9) * 100)}%)</div>
          </div>
        </div>

        <div class="anti-cheat-box">
          <div>🛡️ <b>Quittierung:</b> Taster, Bad-Bewegungsmelder, Kaffeemaschine oder Schalter/Helfer</div>
          <div>💤 <b>Schlummern:</b> ${alarm.snooze_duration} Min (Max: ${alarm.max_snooze_count}x | Aktuell: ${alarm.snooze_count})</div>
        </div>

        ${
          alarm.status === "snoozed"
            ? `
            <div class="snooze-anti-cheat-banner">
              <div style="font-weight: 600; font-size: 13px; color: #ffb74d; display: flex; align-items: center; justify-content: space-between;">
                <span id="snooze-banner-text-${alarm.id}">💤 Schlummermodus aktiv (${alarm.countdown_text})</span>
                <span class="badge" style="background: #fb8c00; font-size: 10px; padding: 2px 7px;">SNOOZE ${alarm.snooze_count}/${alarm.max_snooze_count}</span>
              </div>
              <div style="font-size: 12px; margin-top: 5px; color: #ffe0b2;">
                ${
                  alarm.has_anti_cheat
                    ? "🛡️ <b>Anti-Cheat aktiv:</b> Quittierung wirkt als Schlummern. Endgültiges Beenden erfolgt automatisch bei Aufsteh-Beweis (Bad-Bewegungsmelder, Kaffeemaschine, Schalter/Helfer oder NFC-Tag)."
                    : "Der Wecker pausiert vorübergehend und weckt nach Ablauf der Schlummerzeit erneut."
                }
              </div>
            </div>
            `
            : ""
        }

        ${
          isFullTest
            ? `
            <div class="full-test-banner">
              <div style="font-weight: 600; font-size: 13px; color: #ff8a80; display: flex; align-items: center; justify-content: space-between;">
                <span>🔔 Echter Testlauf in Echtzeit aktiv!</span>
                <span class="badge" style="background: #e53935; font-size: 10px; padding: 2px 7px;">LIVE TEST</span>
              </div>
              <div style="font-size: 12px; color: #cfd8dc; margin-top: 5px; line-height: 1.4;">
                Aktiver Zustand: <b>${alarm.status === "snoozed" ? "💤 Schlummert (Snooze)" : alarm.active_phase === "pre_alarm" ? "Phase 1 (Pre-Alarm)" : alarm.active_phase === "escalation" ? "Phase 3 (Eskalation)" : "Phase 2 (Hauptalarm)"}</b><br>
                <span>💡 Alle Audio- & Licht-Trigger laufen in Echtzeit. Teste Schlummern oder Quittierung per Button, Bewegungsmelder, Leistungsmesser oder NFC!</span>
              </div>
            </div>
            `
            : ""
        }

        ${
          isDryRun
            ? `
            <div>
              <div style="font-size: 12px; color: #ffb74d; display: flex; justify-content: space-between;">
                <span id="dryrun-text-${alarm.id}">⏱️ Testlauf Zeitraffer: ${alarm.dry_run_progress}s / 30s</span>
                <span id="dryrun-phase-${alarm.id}">${alarm.active_phase.toUpperCase()}</span>
              </div>
              <div class="dry-run-progress">
                <div class="progress-bar" id="dryrun-bar-${alarm.id}" style="width: ${dryRunPct}%"></div>
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
            ${
              isTesting
                ? `
                <button class="btn-action btn-stop-test" id="stop-test-${alarm.id}">
                  ⏹️ Testlauf beenden
                </button>
                `
                : `
                <button class="btn-action btn-full-test" id="full-test-${alarm.id}" title="Startet einen echten Echtzeit-Testlauf mit allen Sensoren, Audio & Quittierung">
                  🔔 Voller Testlauf
                </button>
                <button class="btn-action" id="dry-run-${alarm.id}" title="Simuliert alle 3 Phasen beschleunigt in 30 Sekunden">
                  ⚡ 30s Zeitraffer
                </button>
                `
            }
          </div>

          <div class="btn-group">
            ${
              isRinging
                ? `
                <button class="btn-action btn-snooze" id="snooze-${alarm.id}" ${alarm.status === "snoozed" ? "disabled style='opacity: 0.6; cursor: not-allowed;'" : ""}>
                  💤 ${alarm.status === "snoozed" ? "Schlummert..." : "Schlummern"}
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

          <div class="modal-body" id="modalBody">
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

          <div class="form-section-title" style="margin-top: 18px;">📱 Handy-Wecker Synchronisation (Companion App)</div>
          ${this._renderEntityField(
            "f_mobile_alarm_entity",
            "Next Alarm Sensor (Mobiltelefon)",
            cfg.mobile_alarm_entity,
            "sensor.pixel_7_next_alarm",
            "Optional: Wähle den 'Next Alarm'-Sensor deines Smartphones oder ein input_datetime",
            "sensor,input_datetime",
            false
          )}
          <div class="form-group" style="margin-top: 12px;">
            <label class="form-label">Weckquellen-Priorität</label>
            <div class="radio-options-group">
              <label class="radio-option">
                <input type="radio" name="f_alarm_source_mode" value="mobile_priority" ${(!cfg.alarm_source_mode || cfg.alarm_source_mode === "mobile_priority") ? "checked" : ""}>
                <div class="radio-label">
                  <span class="radio-title">Handy-Wecker hat Vorrang, feste Zeit nur als Fallback (empfohlen)</span>
                  <span class="radio-desc">Wenn ein Wecker auf dem Handy gestellt ist, wird diese Zeit verwendet. Ist kein Handy-Wecker aktiv, gilt die oben eingestellte feste Zeit.</span>
                </div>
              </label>
              <label class="radio-option">
                <input type="radio" name="f_alarm_source_mode" value="earliest" ${cfg.alarm_source_mode === "earliest" ? "checked" : ""}>
                <div class="radio-label">
                  <span class="radio-title">Beide aktiv – wer zuerst kommt, gewinnt</span>
                  <span class="radio-desc">Vergleicht Handy-Wecker und feste Zeit und löst zum früheren Zeitpunkt aus.</span>
                </div>
              </label>
              <label class="radio-option">
                <input type="radio" name="f_alarm_source_mode" value="mobile_only" ${cfg.alarm_source_mode === "mobile_only" ? "checked" : ""}>
                <div class="radio-label">
                  <span class="radio-title">Nur Handy-Wecker</span>
                  <span class="radio-desc">Löst nur aus, wenn auf dem Handy ein Wecker aktiv ist. Ohne Handy-Wecker bleibt der Alarm inaktiv.</span>
                </div>
              </label>
              <label class="radio-option">
                <input type="radio" name="f_alarm_source_mode" value="fixed_only" ${cfg.alarm_source_mode === "fixed_only" ? "checked" : ""}>
                <div class="radio-label">
                  <span class="radio-title">Nur feste Weckzeit</span>
                  <span class="radio-desc">Ignoriert den Handy-Wecker und weckt ausschließlich zur oben eingestellten festen Uhrzeit.</span>
                </div>
              </label>
            </div>
          </div>

          <div class="form-checkbox-row" style="margin-top: 14px;">
            <div class="form-checkbox-label">
              <span>Handy-Quittierung synchronisieren (Bidirektional)</span>
              <span class="form-hint">Ausschalten oder Schlummern auf dem Smartphone beendet bzw. pausiert auch Smart Wake</span>
            </div>
            <label class="switch-toggle">
              <input type="checkbox" id="f_mobile_dismiss_sync" ${cfg.mobile_dismiss_sync !== false ? "checked" : ""}>
              <span class="slider"></span>
            </label>
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

          ${this._renderEntityField("f_workday_entity", "Workday Sensor Entity", cfg.workday_entity, "binary_sensor.workday_sensor", "Optional: Eigener Workday Sensor (Standard: binary_sensor.workday_sensor)", "binary_sensor", false)}

          <div class="form-row">
            ${this._renderEntityField("f_calendar_entity", "Home Assistant Kalender Entity", cfg.calendar_entity, "calendar.privat", "Optional: Kalender für Schichtpläne, Urlaub oder Schulferien", "calendar", false)}
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

          ${this._renderEntityField("f_person_entities", "Zugewiesene Personen (Kommagetrennt)", cfg.person_entities, "person.vitali, person.anna", "Mindestens eine dieser Personen muss zu Hause sein", "person", true)}

          <div class="form-section-title">Dynamische Weckzeitverschiebung (Wetter & Schlaf)</div>
          <div class="form-row">
            ${this._renderEntityField("f_weather_temp_entity", "Außentemperatur-Sensor", cfg.weather_temp_entity, "sensor.aussentemperatur", "Sensor für Frost-Erkennung", "sensor,weather", false)}
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
            ${this._renderEntityField("f_weather_rain_entity", "Regensensor Entity", cfg.weather_rain_entity, "binary_sensor.regen", "Sensor für Regen-Offset", "binary_sensor,sensor,weather", false)}
          </div>

          <div class="form-row">
            <div class="form-group">
              <label class="form-label" for="f_weather_rain_offset">Regen-Offset (Minuten)</label>
              <input class="form-input" id="f_weather_rain_offset" type="number" value="${cfg.weather_rain_offset ?? 10}" />
            </div>
            ${this._renderEntityField("f_sleep_stage_entity", "Sleep-Tracker Sensor", cfg.sleep_stage_entity, "sensor.withings_sleep_stage", "Löst in Leichtschlafphase innerhalb von " + (cfg.sleep_stage_window || 30) + " Min vor Weckzeit aus", "sensor,binary_sensor", false)}
          </div>
        `;

      case "phase1":
        return `
          <div class="form-checkbox-row">
            <div class="form-checkbox-label">
              <span>Phase 1 (Pre-Alarm / Sanftes Wecken) aktivieren</span>
              <span class="form-hint">Startet sanft vor der Weckzeit mit Licht und Rollos</span>
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
          ${this._renderEntityField("f_pre_alarm_light_entities", "Dimmbare Licht-Entities (Kommagetrennt)", cfg.pre_alarm_light_entities, "light.nachttisch_links, light.nachttisch_rechts", "Leuchten für sanften Sonnenaufgang-Fade-in", "light", true)}

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

          <div class="form-section-title">Rollos & Jalousien</div>
          <div class="form-row">
            ${this._renderEntityField("f_pre_alarm_cover_entities", "Rollos / Jalousien Entities", cfg.pre_alarm_cover_entities, "cover.schlafzimmer", "Z. B. 20% für sanftes Kippen der Lamellen", "cover", true)}
            <div class="form-group">
              <label class="form-label" for="f_pre_alarm_cover_position">Zielposition (% geöffnet)</label>
              <input class="form-input" id="f_pre_alarm_cover_position" type="number" min="0" max="100" value="${cfg.pre_alarm_cover_position ?? 20}" />
              <span class="form-hint">Z. B. 20% für sanftes Kippen der Lamellen</span>
            </div>
          </div>

          ${this._renderEntityField("f_pre_alarm_script_entity", "Optionales Pre-Alarm Skript", cfg.pre_alarm_script_entity, "script.pre_alarm_custom", "HA-Skript, das zu Beginn von Phase 1 ausgeführt wird", "script", false)}
        `;

      case "phase2":
        return `
          <div class="form-section-title">Media Player & Audio</div>
          ${this._renderEntityField("f_main_media_player_entities", "Media Player Entities (Kommagetrennt)", cfg.main_media_player_entities, "media_player.schlafzimmer_speaker", "Lautsprecher, auf denen der Wecker ertönen soll", "media_player", true)}

          ${this._renderEntityField("f_main_tts_media_player", "Eigener TTS Media Player (Optional)", cfg.main_tts_media_player, "media_player.google_nest_mini", "Separater Lautsprecher nur für Sprachausgabe. Musik-Player wird während der Ansage pausiert.", "media_player", false)}

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

          <div class="form-row">
            <div class="form-group">
              <label class="form-label" for="f_main_tts_delay">TTS Verzögerung (Sekunden)</label>
              <input class="form-input" id="f_main_tts_delay" type="number" min="0" max="300" value="${cfg.main_tts_delay ?? 15}" />
              <span class="form-hint">Pausiert Musik nach N Sek., spricht TTS und setzt fort</span>
            </div>
            <div class="form-group">
              <label class="form-label" for="f_main_tts_volume">TTS Lautstärke (%)</label>
              <input class="form-input" id="f_main_tts_volume" type="number" min="5" max="100" value="${cfg.main_tts_volume ?? 60}" />
              <span class="form-hint">Eigene Lautstärke für die Sprachansage</span>
            </div>
          </div>

          <div class="form-group">
            <label class="form-label" for="f_main_tts_message">TTS Nachrichtentext</label>
            <textarea class="form-textarea" id="f_main_tts_message" rows="3">${cfg.main_tts_message || "Guten Morgen! Es ist {time} Uhr, draußen sind es {temp}°C."}</textarea>
            <span class="form-hint">Verfügbare Platzhalter: {name}, {time}, {temp}</span>
          </div>

          <div class="form-row">
            ${this._renderEntityField("f_main_tts_engine", "TTS Engine Entity (Optional)", cfg.main_tts_engine, "tts.google_en_com oder tts.piper", "Text-to-Speech Engine für Sprachansage", "tts", false)}
            ${this._renderEntityField("f_main_script_entity", "Optionales Hauptalarm Skript", cfg.main_script_entity, "script.guten_morgen", "HA-Skript für den Hauptweckruf", "script", false)}
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
            <div class="form-group">
              <label class="form-label" for="f_escalation_volume_fade_duration">Sanfter Lautstärkeanstieg (Sekunden)</label>
              <input class="form-input" id="f_escalation_volume_fade_duration" type="number" min="0" max="120" value="${cfg.escalation_volume_fade_duration ?? 30}" />
              <span class="form-hint">Dauer für sanftes Hochfahren (z. B. 30s)</span>
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

          ${this._renderEntityField("f_escalation_light_entities", "Licht-Entities für Eskalation", cfg.escalation_light_entities, "light.schlafzimmer_hauptlicht", "Hauptbeleuchtung, die bei Eskalation eingeschaltet wird", "light", true)}

          <div class="form-row">
            ${this._renderEntityField("f_escalation_cover_entities", "Rollos für Eskalation", cfg.escalation_cover_entities, "cover.schlafzimmer_rollo", "Rollos, die bei Eskalation komplett hochfahren", "cover", true)}
            <div class="form-group">
              <label class="form-label" for="f_escalation_cover_position">Zielposition (% geöffnet)</label>
              <input class="form-input" id="f_escalation_cover_position" type="number" min="0" max="100" value="${cfg.escalation_cover_position ?? 100}" />
            </div>
          </div>

          ${this._renderEntityField("f_escalation_script_entity", "Optionales Eskalations-Skript", cfg.escalation_script_entity, "script.alarm_escalation", "HA-Skript für Eskalations-Aktionen", "script", false)}
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
            ${this._renderEntityField("f_snooze_button_entity", "Snooze-Taster Entity", cfg.snooze_button_entity, "event.nachttisch_taster", "Hardware-Taster für Schlummern (Event, Button oder Sensor)", "event,button,sensor,binary_sensor", false)}
            <div class="form-group">
              <label class="form-label" for="f_snooze_button_event">Snooze Event-Typ / Aktion</label>
              <input class="form-input" id="f_snooze_button_event" type="text" value="${cfg.snooze_button_event || ""}" placeholder="z. B. press, single, click" />
              <span class="form-hint">Optional: Spezifischer Event-Typ oder Action-String (leer lassen für Standard)</span>
            </div>
          </div>
          <div class="form-row">
            ${this._renderEntityField("f_dismiss_button_entity", "Dismiss-Taster Entity", cfg.dismiss_button_entity, "event.nachttisch_taster_double", "Hardware-Taster für Quittieren (Event, Button oder Sensor)", "event,button,sensor,binary_sensor", false)}
            <div class="form-group">
              <label class="form-label" for="f_dismiss_button_event">Dismiss Event-Typ / Aktion</label>
              <input class="form-input" id="f_dismiss_button_event" type="text" value="${cfg.dismiss_button_event || ""}" placeholder="z. B. double, double_press, hold" />
              <span class="form-hint">Optional: Spezifischer Event-Typ oder Action-String (leer lassen für Standard)</span>
            </div>
          </div>

          <div class="form-section-title">Anti-Cheat Aufsteh-Beweis</div>
          ${this._renderEntityField("f_dismiss_motion_entities", "Bewegungsmelder Badezimmer / Küche", cfg.dismiss_motion_entities, "binary_sensor.bad_motion, binary_sensor.kueche_motion", "Quittiert automatisch bei Bewegung im Bad oder in der Küche", "binary_sensor,sensor", true)}

          <div class="form-group">
            <label class="form-label" for="f_dismiss_nfc_tags">NFC Tag IDs (Spiegel / Kaffeemaschine)</label>
            <input class="form-input" id="f_dismiss_nfc_tags" type="text" value="${cfg.dismiss_nfc_tags || ""}" placeholder="tag_badspiegel, tag_kaffee" />
            <span class="form-hint">Wecker stoppt erst nach Scannen des physischen NFC-Tags</span>
          </div>

          <div class="form-row">
            ${this._renderEntityField("f_dismiss_power_sensor", "Leistungssensor (Kaffeemaschine / Bad)", cfg.dismiss_power_sensor, "sensor.kaffeemaschine_leistung", "Quittiert bei Stromverbrauch über Schwellenwert", "sensor", false)}
            <div class="form-group">
              <label class="form-label" for="f_dismiss_power_threshold">Leistungsschwelle (Watt)</label>
              <input class="form-input" id="f_dismiss_power_threshold" type="number" step="1" value="${cfg.dismiss_power_threshold ?? 10.0}" />
              <span class="form-hint">Quittiert, wenn z. B. Kaffeemaschine eingeschaltet wird (> 10W)</span>
            </div>
          </div>

          ${this._renderEntityField("f_dismiss_input_boolean", "Anti-Cheat Schalter / Helfer (input_boolean)", cfg.dismiss_input_boolean, "input_boolean.aufgestanden", "Quittiert automatisch, wenn dieser Schalter auf 'on' geschaltet wird (wird danach automatisch zurückgesetzt)", "input_boolean", false)}
        `;

      default:
        return `<div>Ungültiger Tab</div>`;
    }
  }
}

customElements.define("smart-wake-panel", SmartWakePanel);
