## 2026-10-16T22:49:10Z
Identity: You are Worker M2 (UX/UI, Design System & WCAG 2.1 AA Accessibility Worker).
Working directory: D:\Proyectos\observatorio-ti-municipal\.agents\teamwork\worker_m2
Project Root: D:\Proyectos\observatorio-ti-municipal
Authoritative Request: Read D:\Proyectos\observatorio-ti-municipal\.agents\teamwork\ORIGINAL_REQUEST.md first!
Project Plan: Read D:\Proyectos\observatorio-ti-municipal\PROJECT.md
Survey & Reviewer Findings to Address:
- Read D:\Proyectos\observatorio-ti-municipal\.agents\teamwork\explorer_survey_ux\handoff.md (Detailed CSS proposals and contrast mathematics)
- Read D:\Proyectos\observatorio-ti-municipal\.agents\teamwork\reviewer_m1_1\handoff.md (Notes on scrollytelling ARIA and styling)

MANDATORY INTEGRITY WARNING:
DO NOT CHEAT. All implementations must be genuine. DO NOT hardcode test results, create dummy/facade implementations, or circumvent the intended task. A teamwork_preview_auditor will independently verify your work. Integrity violations WILL be detected and your work WILL be rejected.

Scope of Milestone 2:
You own style.css, and necessary UX/A11y markup and script adjustments in index.html and app.js.

Tasks:
1. Implement all 48 missing CSS classes in style.css:
   - Follow Proposal A from explorer_survey_ux/handoff.md.
   - Include .a11y-topbar, .a11y-container, .a11y-ecosystem, .a11y-eco-home, .a11y-eco-link, .a11y-divider, .a11y-controls, .a11y-label, .a11y-btn, .a11y-group, .a11y-hide-sm, .a11y-hide-md.
   - Include .skip-link with accessible top transition and focus state.
   - Include .hero-top-row, .hero-status-pill, .status-dot, .hero-actions-bar, .btn-hero-primary, .btn-hero-secondary, .hero-share-group, .btn-hero-share.
   - Include .guia-banner, .guia-banner-header, .guia-banner-title, .btn-guia-detail, .guia-steps-grid, .guia-step-card, .guia-step-num.
   - Include .site-footer, .footer-grid, .footer-col, .footer-brand, .footer-heading, .footer-bio, .footer-links-row, .footer-cta-row, .btn-footer-cta, .btn-footer-download, .footer-downloads, .footer-legal-trigger, .footer-bottom.
   - Include .ranking-actions, .ranking-header-row, .filter-select, .btn-export-csv, .form-checkbox-row, .legal-block.
2. Calibrate WCAG 2.1 AA Contrast Ratios in style.css:
   - Adjust --muted to #556265 (ratio 5.96:1 on #faf8f5, passes AA).
   - Add --gold-text: #875f00; and apply it to textual gold accents on light surfaces (ratio 5.40:1).
   - Implement accessible focus ring with :focus-visible: outline 3px solid var(--focus-outline-color) !important; outline-offset: 2px !important; with --focus-outline-color defined per theme (#002b49 light, #38bdf8 dark, #ffff00 contrast).
3. Dark Theme & High Contrast Corrections in style.css:
   - Fix inputs (.search-input, .region-select, .compare-select) in dark mode: background #071f43, color #f8fafc, border #1f5091.
   - Fix table th in dark mode: background #071f43, color #38bdf8, border #153b70.
   - Fix table tr:hover td in dark mode: background #0d3166, color #f8fafc.
   - Fix #chile-map in dark mode: background #04142b (eliminates white flicker during tile loading).
   - Fix .map-legend-overlay in dark mode: background rgba(7, 31, 67, 0.95), color #f8fafc.
   - Fix Leaflet popups in dark mode: .leaflet-popup-content-wrapper, .leaflet-popup-tip background #071f43, color #f8fafc, border 1px solid #1f5091.
   - Ensure contrast theme (data-theme="contrast") provides pitch black background with vivid yellow/white outlines and text.
4. Markup Updates in index.html:
   - Add `<a href="#main-content" class="skip-link">Saltar al contenido principal</a>` right after `<body>`.
   - Add `<main id="main-content" tabindex="-1">` wrapping the main content sections.
   - Add `tabindex="0"`, `role="button"`, and `aria-sort="none"` to sortable `<th>` elements.
5. Interactive & Accessibility Logic in app.js:
   - Modal Focus Trap and Return: In openModal/closeModal, preserve previous activeElement. Focus modal close button or first interactive input on open. Trap Tab/Shift+Tab inside modal card. On close/Esc, restore focus to previous activeElement.
   - Theme Sync with Map: In updateMapTheme(theme), if theme === "contrast", use state.esriDarkGroup instead of light canvas.
   - Dynamic SVG Gauge: In renderGaugeSvg, set score text `fill="currentColor"` or `fill="var(--ink)"` so it's readable across all themes.
   - Table Keyboard Sorting: Add keydown listener (Enter/Space) to `<th>` for accessible sorting, and Enter on `<tr>` to open commune drawer.
   - Scrollytelling Tabs: Dynamically update `aria-selected="true"` on active chapter button and `"false"` on others.

Verification:
- Run `python .agents\teamwork\explorer_survey_ux\audit_classes.py` to verify 0 missing classes.
- Run `node -c app.js` to ensure 0 syntax errors.
- Run `powershell -ExecutionPolicy Bypass -File .myworld-harness\harness.ps1 quality`.
- Run `python .agents\teamwork\explorer_survey_sim_jev\eval_jev.py` to verify all sections PASS.
